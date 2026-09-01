"""
HomeCare Enterprise - Turnero HomeCare (motor de turnos)

Fila de espera con numerador para consultorios, ventanillas y
salas de atención -- con prioridad automática por edad, cola
justa (N turnos normales por cada 1 prioritario, configurable),
y trazabilidad completa de cada llamado.

IMPORTANTE: se usa el prefijo "turnero_" en todas las tablas a
propósito -- ya existía un módulo distinto llamado "turnos"
(horarios de trabajo del personal), y este es un concepto
totalmente diferente (fila de espera física de pacientes), para
no confundirlos ni chocar con ese módulo existente.
"""

from datetime import date, datetime

from database.database import consultar_todos, consultar_uno, ejecutar, transaction

CANALES = ("Presencial", "Web", "QR", "Programado")
ESTADOS = ("Creado", "En espera", "Llamado", "En atención", "Finalizado", "No presentado", "Transferido", "Cancelado")


def _hoy() -> str:
    return date.today().isoformat()


def calcular_edad(fecha_nacimiento: str) -> int:
    """Calcula la edad real a partir de la fecha de nacimiento -- nunca se confía en una edad digitada a mano si hay fecha de nacimiento disponible."""
    nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
    hoy = date.today()
    edad = hoy.year - nacimiento.year
    if (hoy.month, hoy.day) < (nacimiento.month, nacimiento.day):
        edad -= 1
    return edad


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

def obtener_configuracion() -> dict:
    fila = consultar_uno("SELECT * FROM turnero_configuracion WHERE id=1")
    if fila:
        return dict(fila)
    ejecutar("INSERT INTO turnero_configuracion(id) VALUES (1)")
    return dict(consultar_uno("SELECT * FROM turnero_configuracion WHERE id=1"))


def guardar_configuracion(datos: dict):
    obtener_configuracion()  # asegura que exista la fila
    ejecutar(
        """
        UPDATE turnero_configuracion SET
            nombre=?, normales_por_prioritario=?, edad_prioridad=?, reinicio_numeracion=?,
            mensaje_voz=?, volumen=?, timbre_activo=?
        WHERE id=1
        """,
        (
            datos.get("nombre", "Turnero HomeCare"), int(datos.get("normales_por_prioritario") or 2),
            int(datos.get("edad_prioridad") or 60), datos.get("reinicio_numeracion", "Diario"),
            datos.get("mensaje_voz") or "Turno {TURNO}, {PACIENTE}, diríjase a {MODULO}.",
            int(datos.get("volumen") or 80), 1 if datos.get("timbre_activo") else 0,
        ),
    )


# ==========================================================
# SERVICIOS DEL TURNERO
# ==========================================================

def listar_servicios(solo_activos=False):
    sql = "SELECT * FROM turnero_servicios"
    if solo_activos:
        sql += " WHERE activo=1"
    sql += " ORDER BY orden, nombre"
    return [dict(f) for f in consultar_todos(sql)]


def obtener_servicio(servicio_id: int):
    fila = consultar_uno("SELECT * FROM turnero_servicios WHERE id=?", (servicio_id,))
    return dict(fila) if fila else None


def crear_servicio(datos: dict, usuario_id=None) -> int:
    if not datos.get("nombre"):
        raise ValueError("Debe indicar el nombre del servicio.")
    if not datos.get("prefijo"):
        raise ValueError("Debe indicar el prefijo del turno (ej: C, V, L).")
    return ejecutar(
        """
        INSERT INTO turnero_servicios(nombre, codigo, descripcion, color, icono, prefijo,
            tiempo_promedio_minutos, permite_prioridad, orden, usuario_creacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos["nombre"], datos.get("codigo"), datos.get("descripcion"),
            datos.get("color") or "#00A19B", datos.get("icono") or "fa-solid fa-user-doctor",
            datos["prefijo"].strip().upper(), int(datos.get("tiempo_promedio_minutos") or 15),
            1 if datos.get("permite_prioridad") else 0, int(datos.get("orden") or 0), usuario_id,
        ),
    )


def desactivar_servicio(servicio_id: int):
    ejecutar("UPDATE turnero_servicios SET activo=0 WHERE id=?", (servicio_id,))


def reactivar_servicio(servicio_id: int):
    ejecutar("UPDATE turnero_servicios SET activo=1 WHERE id=?", (servicio_id,))


# ==========================================================
# MÓDULOS DE ATENCIÓN
# ==========================================================

TIPOS_MODULO = ("Consultorio", "Ventanilla", "Salón", "Recepción", "Caja", "Laboratorio", "Otro")


def listar_modulos(solo_activos=False):
    sql = """
        SELECT m.*, s.nombre AS servicio_nombre, s.prefijo AS servicio_prefijo,
               u.nombre AS usuario_nombre
        FROM turnero_modulos m
        LEFT JOIN turnero_servicios s ON s.id = m.servicio_id
        LEFT JOIN usuarios u ON u.id = m.usuario_asignado_id
    """
    if solo_activos:
        sql += " WHERE m.activo=1"
    sql += " ORDER BY m.nombre"
    return [dict(f) for f in consultar_todos(sql)]


def obtener_modulo(modulo_id: int):
    fila = consultar_uno(
        """
        SELECT m.*, s.nombre AS servicio_nombre
        FROM turnero_modulos m
        LEFT JOIN turnero_servicios s ON s.id = m.servicio_id
        WHERE m.id=?
        """,
        (modulo_id,),
    )
    return dict(fila) if fila else None


def crear_modulo(datos: dict) -> int:
    if not datos.get("nombre"):
        raise ValueError("Debe indicar el nombre del módulo.")
    if datos.get("tipo") not in TIPOS_MODULO:
        raise ValueError(f"Tipo no válido. Use uno de: {', '.join(TIPOS_MODULO)}")
    return ejecutar(
        "INSERT INTO turnero_modulos(nombre, codigo, tipo, servicio_id, usuario_asignado_id, descripcion) VALUES (?, ?, ?, ?, ?, ?)",
        (datos["nombre"], datos.get("codigo"), datos["tipo"], datos.get("servicio_id") or None,
         datos.get("usuario_asignado_id") or None, datos.get("descripcion")),
    )


def desactivar_modulo(modulo_id: int):
    ejecutar("UPDATE turnero_modulos SET activo=0 WHERE id=?", (modulo_id,))


def reactivar_modulo(modulo_id: int):
    ejecutar("UPDATE turnero_modulos SET activo=1 WHERE id=?", (modulo_id,))


# ==========================================================
# CREACIÓN DE TURNOS -- sin duplicar pacientes
# ==========================================================

def _registrar_evento(turno_id: int, tipo_evento: str, detalle: str = None, usuario_id=None, modulo_id=None):
    ejecutar(
        "INSERT INTO turnero_eventos(turno_id, tipo_evento, detalle, usuario_id, modulo_id) VALUES (?, ?, ?, ?, ?)",
        (turno_id, tipo_evento, detalle, usuario_id, modulo_id),
    )


def _siguiente_numero(servicio_id: int, fecha: str) -> int:
    config = obtener_configuracion()
    if config["reinicio_numeracion"] == "Diario":
        fila = consultar_uno(
            "SELECT COUNT(*) AS total FROM turnero_turnos WHERE servicio_id=? AND fecha=?",
            (servicio_id, fecha),
        )
    else:
        fila = consultar_uno("SELECT COUNT(*) AS total FROM turnero_turnos WHERE servicio_id=?", (servicio_id,))
    return (dict(fila)["total"] if fila else 0) + 1


def crear_turno(datos: dict, usuario_id=None, canal="Presencial") -> dict:
    """
    Busca al paciente por documento antes que nada -- si existe,
    lo reutiliza (nunca crea uno nuevo). Si no existe, guarda
    solo lo mínimo (documento, nombre, fecha de nacimiento) como
    visitante, sin crear una ficha clínica completa.

    La prioridad SIEMPRE se calcula en el backend a partir de la
    fecha de nacimiento cuando está disponible -- nunca se
    confía en un valor de prioridad que venga ya marcado desde
    el frontend.
    """
    servicio = obtener_servicio(datos.get("servicio_id"))
    if not servicio or not servicio["activo"]:
        raise ValueError("El servicio seleccionado no existe o no está activo.")
    if not datos.get("documento"):
        raise ValueError("Debe indicar el número de documento.")
    if canal not in CANALES:
        raise ValueError(f"Canal no válido. Use uno de: {', '.join(CANALES)}")

    from services.pacientes_service import PacientesService

    paciente_id = None
    nombre_visitante = datos.get("nombre_visitante")
    fecha_nacimiento = datos.get("fecha_nacimiento")

    paciente_existente = PacientesService.obtener_por_documento(datos["documento"])
    if paciente_existente:
        paciente = dict(paciente_existente)
        paciente_id = paciente["id"]
        nombre_visitante = f"{paciente.get('primer_nombre', '')} {paciente.get('primer_apellido', '')}".strip()
        fecha_nacimiento = paciente.get("fecha_nacimiento") or fecha_nacimiento
    else:
        if not nombre_visitante:
            raise ValueError("El documento no está registrado -- debe indicar el nombre completo.")

    # La prioridad SOLO se calcula en el backend, nunca se recibe ya decidida.
    config = obtener_configuracion()
    es_prioritario = False
    motivo_prioridad = None
    if servicio["permite_prioridad"] and fecha_nacimiento:
        try:
            edad = calcular_edad(fecha_nacimiento)
            if edad >= config["edad_prioridad"]:
                es_prioritario = True
                motivo_prioridad = f"Adulto mayor ({edad} años)"
        except (ValueError, TypeError):
            pass

    fecha = _hoy()
    numero = _siguiente_numero(servicio["id"], fecha)
    numero_completo = f"{servicio['prefijo']}{numero:03d}"
    momento_creacion = datetime.now().isoformat(sep=" ", timespec="microseconds")

    turno_id = ejecutar(
        """
        INSERT INTO turnero_turnos(
            numero_completo, numero, servicio_id, paciente_id, documento, nombre_visitante,
            fecha_nacimiento, prioridad, motivo_prioridad, canal, estado, fecha, hora_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'En espera', ?, ?)
        """,
        (
            numero_completo, numero, servicio["id"], paciente_id, datos["documento"], nombre_visitante,
            fecha_nacimiento, 1 if es_prioritario else 0, motivo_prioridad, canal, fecha, momento_creacion,
        ),
    )
    _registrar_evento(turno_id, "Creado", detalle=f"Canal: {canal}", usuario_id=usuario_id)

    return obtener_turno(turno_id)


def obtener_turno(turno_id: int):
    fila = consultar_uno(
        """
        SELECT t.*, s.nombre AS servicio_nombre, s.prefijo AS servicio_prefijo, s.color AS servicio_color,
               m.nombre AS modulo_nombre
        FROM turnero_turnos t
        JOIN turnero_servicios s ON s.id = t.servicio_id
        LEFT JOIN turnero_modulos m ON m.id = t.modulo_id
        WHERE t.id=?
        """,
        (turno_id,),
    )
    return dict(fila) if fila else None


# ==========================================================
# ALGORITMO DE COLA -- lo más importante del módulo
# ==========================================================

def siguiente_turno_a_llamar(servicio_id: int):
    """
    Decide cuál turno debe llamarse a continuación para un
    servicio, aplicando la regla configurable de "N turnos
    normales por cada 1 prioritario" -- sin que un prioritario
    pierda su lugar sin importar cuándo llegó, y sin saltarse
    injustificadamente a los normales que ya esperaban.
    """
    fecha = _hoy()
    normales = consultar_todos(
        "SELECT * FROM turnero_turnos WHERE servicio_id=? AND fecha=? AND estado='En espera' AND prioridad=0 ORDER BY hora_creacion ASC",
        (servicio_id, fecha),
    )
    prioritarios = consultar_todos(
        "SELECT * FROM turnero_turnos WHERE servicio_id=? AND fecha=? AND estado='En espera' AND prioridad=1 ORDER BY hora_creacion ASC",
        (servicio_id, fecha),
    )
    normales = [dict(f) for f in normales]
    prioritarios = [dict(f) for f in prioritarios]

    if not prioritarios:
        return normales[0] if normales else None
    if not normales:
        return prioritarios[0]

    config = obtener_configuracion()
    ya_llamados_hoy = consultar_todos(
        "SELECT prioridad FROM turnero_turnos WHERE servicio_id=? AND fecha=? AND hora_llamado IS NOT NULL ORDER BY hora_llamado DESC",
        (servicio_id, fecha),
    )
    normales_seguidos = 0
    for fila in ya_llamados_hoy:
        if dict(fila)["prioridad"]:
            break
        normales_seguidos += 1

    if normales_seguidos >= config["normales_por_prioritario"]:
        return prioritarios[0]
    return normales[0]


def llamar_siguiente(servicio_id: int, modulo_id: int, usuario_id=None):
    """
    Llama al siguiente turno de la cola y lo asigna a este
    módulo -- con control de concurrencia real: si otro operador
    ya se adelantó a llamar ese mismo turno, este intento no lo
    toca (evita que dos módulos llamen el mismo turno a la vez).
    """
    turno = siguiente_turno_a_llamar(servicio_id)
    if not turno:
        return None

    # CURRENT_TIMESTAMP de SQLite solo tiene resolucion de 1
    # segundo -- si dos llamados ocurren en el mismo segundo
    # (perfectamente normal si un operador hace clic rapido),
    # quedarian con la MISMA hora_llamado, y el algoritmo de cola
    # (que depende de leer el orden real de los ultimos llamados)
    # dejaria de ser confiable. Se usa un timestamp de Python con
    # microsegundos en su lugar.
    momento_llamado = datetime.now().isoformat(sep=" ", timespec="microseconds")

    with transaction() as cn:
        cursor = cn.cursor()
        cursor.execute(
            "UPDATE turnero_turnos SET estado='Llamado', modulo_id=?, usuario_operador_id=?, hora_llamado=?, veces_llamado=veces_llamado+1 WHERE id=? AND estado='En espera'",
            (modulo_id, usuario_id, momento_llamado, turno["id"]),
        )
        gano_la_carrera = cursor.rowcount > 0

    if not gano_la_carrera:
        return llamar_siguiente(servicio_id, modulo_id, usuario_id)

    _registrar_evento(turno["id"], "Llamado", usuario_id=usuario_id, modulo_id=modulo_id)
    return obtener_turno(turno["id"])


def rellamar(turno_id: int, usuario_id=None):
    ejecutar("UPDATE turnero_turnos SET veces_llamado=veces_llamado+1 WHERE id=?", (turno_id,))
    turno = obtener_turno(turno_id)
    _registrar_evento(turno_id, "Re-llamado", usuario_id=usuario_id, modulo_id=turno.get("modulo_id"))
    return turno


def iniciar_atencion(turno_id: int, usuario_id=None):
    ejecutar("UPDATE turnero_turnos SET estado='En atención', hora_inicio_atencion=CURRENT_TIMESTAMP WHERE id=?", (turno_id,))
    _registrar_evento(turno_id, "Inicio de atención", usuario_id=usuario_id)
    return obtener_turno(turno_id)


def finalizar_turno(turno_id: int, usuario_id=None):
    ejecutar("UPDATE turnero_turnos SET estado='Finalizado', hora_fin=CURRENT_TIMESTAMP WHERE id=?", (turno_id,))
    _registrar_evento(turno_id, "Finalizado", usuario_id=usuario_id)
    return obtener_turno(turno_id)


def marcar_no_presentado(turno_id: int, usuario_id=None):
    ejecutar("UPDATE turnero_turnos SET estado='No presentado', hora_fin=CURRENT_TIMESTAMP WHERE id=?", (turno_id,))
    _registrar_evento(turno_id, "No presentado", usuario_id=usuario_id)
    return obtener_turno(turno_id)


def transferir_turno(turno_id: int, nuevo_servicio_id: int, usuario_id=None) -> dict:
    """Cierra el turno actual y crea uno nuevo en el servicio destino, dejando trazabilidad del origen."""
    turno_original = obtener_turno(turno_id)
    if not turno_original:
        raise ValueError("El turno no existe.")

    ejecutar("UPDATE turnero_turnos SET estado='Transferido', hora_fin=CURRENT_TIMESTAMP WHERE id=?", (turno_id,))
    _registrar_evento(turno_id, "Transferido", detalle=f"Hacia servicio #{nuevo_servicio_id}", usuario_id=usuario_id)

    nuevo_turno = crear_turno(
        {
            "servicio_id": nuevo_servicio_id, "documento": turno_original["documento"],
            "nombre_visitante": turno_original["nombre_visitante"], "fecha_nacimiento": turno_original.get("fecha_nacimiento"),
        },
        usuario_id=usuario_id, canal=turno_original["canal"],
    )
    ejecutar("UPDATE turnero_turnos SET transferido_de_turno_id=? WHERE id=?", (turno_id, nuevo_turno["id"]))
    return nuevo_turno


# ==========================================================
# CONSULTAS PARA PANTALLA / DASHBOARD / PORTAL
# ==========================================================

def cola_en_espera(servicio_id=None):
    sql = """
        SELECT t.*, s.nombre AS servicio_nombre, s.color AS servicio_color
        FROM turnero_turnos t JOIN turnero_servicios s ON s.id = t.servicio_id
        WHERE t.fecha=? AND t.estado='En espera'
    """
    parametros = [_hoy()]
    if servicio_id:
        sql += " AND t.servicio_id=?"
        parametros.append(servicio_id)
    sql += " ORDER BY t.hora_creacion ASC"
    return [dict(f) for f in consultar_todos(sql, tuple(parametros))]


def ultimos_llamados(limite=10):
    filas = consultar_todos(
        """
        SELECT t.*, m.nombre AS modulo_nombre
        FROM turnero_turnos t LEFT JOIN turnero_modulos m ON m.id = t.modulo_id
        WHERE t.fecha=? AND t.hora_llamado IS NOT NULL
        ORDER BY t.hora_llamado DESC LIMIT ?
        """,
        (_hoy(), limite),
    )
    return [dict(f) for f in filas]


def posicion_en_cola(turno_id: int) -> int:
    """Cuántos turnos hay antes de este en su servicio (aproximado, para mostrarle al paciente)."""
    turno = obtener_turno(turno_id)
    if not turno or turno["estado"] != "En espera":
        return 0
    fila = consultar_uno(
        "SELECT COUNT(*) AS total FROM turnero_turnos WHERE servicio_id=? AND fecha=? AND estado='En espera' AND hora_creacion < ?",
        (turno["servicio_id"], turno["fecha"], turno["hora_creacion"]),
    )
    return dict(fila)["total"] if fila else 0


def resumen_dashboard():
    fecha = _hoy()
    fila = consultar_uno(
        """
        SELECT
            COUNT(*) AS total_hoy,
            SUM(CASE WHEN estado='En espera' THEN 1 ELSE 0 END) AS en_espera,
            SUM(CASE WHEN estado='En atención' THEN 1 ELSE 0 END) AS en_atencion,
            SUM(CASE WHEN estado='Finalizado' THEN 1 ELSE 0 END) AS atendidos,
            SUM(CASE WHEN estado='No presentado' THEN 1 ELSE 0 END) AS no_presentados,
            SUM(CASE WHEN prioridad=1 THEN 1 ELSE 0 END) AS prioritarios,
            SUM(CASE WHEN prioridad=0 THEN 1 ELSE 0 END) AS normales
        FROM turnero_turnos WHERE fecha=?
        """,
        (fecha,),
    )
    r = dict(fila) if fila else {}
    return {k: (r.get(k) or 0) for k in ("total_hoy", "en_espera", "en_atencion", "atendidos", "no_presentados", "prioritarios", "normales")}


def consultar_estado_publico(numero_completo: str, documento: str):
    """
    Para la página pública "Consulta tu turno" -- el paciente
    ingresa el número de turno y su documento (los dos, para no
    permitir que cualquiera consulte cualquier turno solo
    adivinando el número). No expone datos clínicos, solo el
    estado administrativo del turno.
    """
    fila = consultar_uno(
        """
        SELECT t.*, s.nombre AS servicio_nombre, s.color AS servicio_color, m.nombre AS modulo_nombre
        FROM turnero_turnos t
        JOIN turnero_servicios s ON s.id = t.servicio_id
        LEFT JOIN turnero_modulos m ON m.id = t.modulo_id
        WHERE t.numero_completo=? AND t.documento=? AND t.fecha=?
        """,
        (numero_completo.strip().upper(), documento.strip(), _hoy()),
    )
    if not fila:
        return None

    turno = dict(fila)
    return {
        "numero_completo": turno["numero_completo"],
        "servicio_nombre": turno["servicio_nombre"],
        "servicio_color": turno["servicio_color"],
        "estado": turno["estado"],
        "prioridad": bool(turno["prioridad"]),
        "modulo_nombre": turno["modulo_nombre"],
        "posicion": posicion_en_cola(turno["id"]) if turno["estado"] == "En espera" else None,
    }


def sembrar_ejemplo(usuario_id=None) -> dict:
    """
    Servicios y módulos de ejemplo, para poder probar el
    Turnero de inmediato sin tener que configurar nada primero
    -- solo se siembra si todavía no existe ningún servicio
    (para no duplicar si ya se configuró algo real).
    """
    if listar_servicios():
        return {"servicios": [], "modulos": []}

    servicios_ejemplo = [
        ("Medicina General", "C", "fa-solid fa-stethoscope", "#00A19B"),
        ("Enfermería", "E", "fa-solid fa-user-nurse", "#8bbd00"),
        ("Atención al Usuario", "V", "fa-solid fa-headset", "#e6006e"),
        ("Toma de Muestras", "L", "fa-solid fa-vial", "#6b5b95"),
        ("Terapias", "T", "fa-solid fa-hand-holding-medical", "#00807b"),
    ]
    ids_servicios = {}
    for nombre, prefijo, icono, color in servicios_ejemplo:
        sid = crear_servicio({"nombre": nombre, "prefijo": prefijo, "icono": icono, "color": color, "permite_prioridad": True}, usuario_id=usuario_id)
        ids_servicios[nombre] = sid

    modulos_ejemplo = [
        ("Consultorio 1", "Consultorio", "Medicina General"),
        ("Consultorio 2", "Consultorio", "Enfermería"),
        ("Ventanilla 1", "Ventanilla", "Atención al Usuario"),
        ("Laboratorio", "Laboratorio", "Toma de Muestras"),
    ]
    ids_modulos = []
    for nombre, tipo, servicio_nombre in modulos_ejemplo:
        mid = crear_modulo({"nombre": nombre, "tipo": tipo, "servicio_id": ids_servicios[servicio_nombre]})
        ids_modulos.append(mid)

    return {"servicios": list(ids_servicios.values()), "modulos": ids_modulos}
