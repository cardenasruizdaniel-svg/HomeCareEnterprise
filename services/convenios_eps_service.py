"""
HomeCare Enterprise - Convenios con EPS

Jerarquía del módulo (desde la reestructuración):

    EPS
     └── Convenio  (contrato marco: vigencia, número, NIT)
          └── Programa  (Crónicos, Paliativos, Materno...) -- cada uno con su propio valor mensual
               └── Servicios parametrizados  (cuántas sesiones incluye cada tipo de servicio,
                                               cada cuántos días se reinicia el tope, y el valor
                                               normal / adicional de cada uno)

Un paciente se asigna a un PROGRAMA específico (no al convenio en
general), con su fecha de ingreso, fecha de autorización, y
opcionalmente el profesional/médico tratante.

Varios tipos de servicio pueden compartir un mismo tope dentro de
un programa (por ejemplo, las 4 terapias -- física, ocupacional,
respiratoria, fonoaudiología -- comparten el tope de 12 sesiones
al mes, aunque cada una tenga su propio valor). La cantidad de
cada tipo específico la decide el médico al ordenarlas; lo único
que controla el sistema es que la SUMA no se pase de lo
autorizado para ese programa.
"""

from database.database import consultar_todos, consultar_uno, ejecutar

# Nombre del grupo que comparte un mismo tope -- las 4 terapias
# van agrupadas bajo este mismo nombre dentro de un programa.
GRUPO_TERAPIAS = "Terapias"


# ==========================================
# CONVENIOS (el contrato marco con la EPS)
# ==========================================

def programas_disponibles_para_eps(eps: str):
    """
    Todos los programas activos, de convenios vigentes, que
    correspondan a una EPS específica -- se usa para que, al
    momento de la primera visita, el médico pueda elegir a cuál
    programa corresponde el paciente, sin tener que buscarlo
    manualmente en Convenios EPS. Se valida contra la EPS que ya
    tiene registrada el paciente desde que se creó.
    """
    if not eps:
        return []
    filas = consultar_todos(
        """
        SELECT pc.id, pc.nombre, pc.valor_mensual, ce.id AS convenio_id, ce.eps, ce.numero_convenio
        FROM programas_convenio pc
        JOIN convenios_eps ce ON ce.id = pc.convenio_id
        WHERE pc.estado='Activo' AND ce.estado='Vigente' AND LOWER(ce.eps) = LOWER(?)
        ORDER BY pc.nombre
        """,
        (eps.strip(),),
    )
    return [dict(f) for f in filas]


def programas_generales_activos():
    """
    Programas de servicios que NO dependen de ningún convenio de
    EPS -- sirven para poder asignarle a un paciente un plan de
    servicios con sus topes, aunque todavía no exista (o no
    aplique) un convenio formal con su EPS. Nunca son
    obligatorios: un paciente puede seguir recibiendo servicios
    sin estar en ningún programa.
    """
    filas = consultar_todos(
        "SELECT id, nombre, valor_mensual, NULL AS convenio_id, NULL AS eps, NULL AS numero_convenio "
        "FROM programas_convenio WHERE convenio_id IS NULL AND estado='Activo' ORDER BY nombre"
    )
    return [dict(f) for f in filas]


def opciones_de_programa_para_paciente(eps: str) -> dict:
    """
    Junta las dos fuentes de programas que se le pueden ofrecer
    a un paciente al momento de asignarlo: primero los que
    vienen de un convenio con SU EPS (si existe alguno vigente
    -- estos tienen prioridad), y también los programas
    generales, que aplican sin importar la EPS. Ninguno de los
    dos es obligatorio -- el paciente puede quedar sin programa
    y de todas formas se le pueden asignar servicios con
    normalidad.
    """
    return {
        "con_convenio": programas_disponibles_para_eps(eps),
        "generales": programas_generales_activos(),
    }


def listar_convenios(solo_vigentes=False):
    sql = "SELECT * FROM convenios_eps"
    if solo_vigentes:
        sql += " WHERE estado='Vigente'"
    sql += " ORDER BY eps, nombre_plan"
    convenios = [dict(c) for c in consultar_todos(sql)]
    for c in convenios:
        c["total_programas"] = contar_programas_convenio(c["id"])
    return convenios


def obtener_convenio(convenio_id: int):
    fila = consultar_uno("SELECT * FROM convenios_eps WHERE id=?", (convenio_id,))
    if not fila:
        return None
    convenio = dict(fila)
    convenio["programas"] = listar_programas_convenio(convenio_id)
    return convenio


def crear_convenio(eps, nit_eps, nombre_plan, numero_convenio, fecha_inicio, fecha_fin, observaciones, usuario_id) -> int:
    if not eps:
        raise ValueError("Debe indicar la EPS.")
    return ejecutar(
        "INSERT INTO convenios_eps(eps, nit_eps, nombre_plan, numero_convenio, fecha_inicio, fecha_fin, observaciones, usuario_creacion) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (eps.strip(), nit_eps or "", (nombre_plan or "").strip(), numero_convenio or "", fecha_inicio or None, fecha_fin or None, observaciones or "", usuario_id),
    )


def actualizar_convenio(convenio_id, eps, nit_eps, nombre_plan, numero_convenio, fecha_inicio, fecha_fin, estado, observaciones):
    ejecutar(
        "UPDATE convenios_eps SET eps=?, nit_eps=?, nombre_plan=?, numero_convenio=?, fecha_inicio=?, fecha_fin=?, estado=?, observaciones=? WHERE id=?",
        (eps.strip(), nit_eps or "", (nombre_plan or "").strip(), numero_convenio or "", fecha_inicio or None, fecha_fin or None, estado, observaciones or "", convenio_id),
    )


def finalizar_convenio(convenio_id: int):
    ejecutar("UPDATE convenios_eps SET estado='Finalizado' WHERE id=?", (convenio_id,))


# ==========================================
# PROGRAMAS DENTRO DE UN CONVENIO
# ==========================================

def contar_programas_convenio(convenio_id: int) -> int:
    fila = consultar_uno("SELECT COUNT(*) AS total FROM programas_convenio WHERE convenio_id=? AND estado='Activo'", (convenio_id,))
    return dict(fila)["total"] if fila else 0


def listar_programas_convenio(convenio_id: int):
    """Todos los programas de un convenio, cada uno con su lista de servicios ya resuelta."""
    filas = consultar_todos(
        "SELECT * FROM programas_convenio WHERE convenio_id=? AND estado='Activo' ORDER BY nombre", (convenio_id,)
    )
    programas = [dict(f) for f in filas]
    for p in programas:
        p["servicios"] = listar_servicios_programa(p["id"])
    return programas


def obtener_programa(programa_convenio_id: int):
    fila = consultar_uno(
        """
        SELECT pc.*, ce.eps, ce.nombre_plan AS referencia_convenio
        FROM programas_convenio pc
        JOIN convenios_eps ce ON ce.id = pc.convenio_id
        WHERE pc.id=?
        """,
        (programa_convenio_id,),
    )
    if not fila:
        return None
    programa = dict(fila)
    programa["servicios"] = listar_servicios_programa(programa_convenio_id)
    return programa


def crear_programa_convenio(convenio_id, nombre, valor_mensual, observaciones, usuario_id) -> int:
    """
    'convenio_id' puede ser None -- un programa no necesita
    estar atado a ningún convenio de EPS para poder usarse. Esto
    permite seguir asignando programas y servicios a los
    pacientes con total normalidad mientras no exista (o no
    aplique) un convenio formal con una EPS. Si más adelante se
    crea el convenio correspondiente, ese es el que se prioriza
    para los pacientes de esa EPS -- pero nunca es obligatorio.
    """
    if not nombre or not nombre.strip():
        raise ValueError("Debe indicar el nombre del programa.")
    return ejecutar(
        "INSERT INTO programas_convenio(convenio_id, nombre, valor_mensual, observaciones, usuario_creacion) VALUES (?, ?, ?, ?, ?)",
        (convenio_id or None, nombre.strip(), float(valor_mensual or 0), observaciones or "", usuario_id),
    )


def listar_programas_independientes():
    """Programas de servicios que NO están atados a ningún convenio EPS -- se pueden asignar a cualquier paciente, tenga o no EPS con convenio."""
    filas = consultar_todos("SELECT * FROM programas_convenio WHERE convenio_id IS NULL AND estado='Activo' ORDER BY nombre")
    programas = [dict(f) for f in filas]
    for p in programas:
        p["servicios"] = listar_servicios_programa(p["id"])
    return programas


def actualizar_programa_convenio(programa_convenio_id, nombre, valor_mensual, observaciones):
    if not nombre or not nombre.strip():
        raise ValueError("Debe indicar el nombre del programa.")
    ejecutar(
        "UPDATE programas_convenio SET nombre=?, valor_mensual=?, observaciones=? WHERE id=?",
        (nombre.strip(), float(valor_mensual or 0), observaciones or "", programa_convenio_id),
    )


def desactivar_programa_convenio(programa_convenio_id: int):
    ejecutar("UPDATE programas_convenio SET estado='Inactivo' WHERE id=?", (programa_convenio_id,))


# ==========================================
# PLAN DE SERVICIOS DE UN PROGRAMA
# ==========================================

def listar_actividades_catalogo():
    """El mismo catálogo de servicios que se usa al asignarle actividades a un paciente -- para que el nombre siempre coincida exactamente."""
    from repositories.catalogo_actividades_repository import CatalogoActividadesRepository
    return [dict(a) for a in CatalogoActividadesRepository.listar_activas()]


def listar_servicios_programa(programa_convenio_id: int):
    filas = consultar_todos(
        "SELECT * FROM convenios_eps_servicios WHERE programa_convenio_id=? AND activo=1 ORDER BY tipo_servicio",
        (programa_convenio_id,),
    )
    return [dict(f) for f in filas]


def agregar_servicio_programa(programa_convenio_id, actividad_id, grupo_tope, limite_cantidad, dias_ciclo,
                                valor_normal, valor_adicional) -> int:
    if not actividad_id:
        raise ValueError("Debe seleccionar el servicio del catálogo.")
    if not limite_cantidad or int(limite_cantidad) <= 0:
        raise ValueError("El límite de cantidad debe ser mayor a cero.")
    if not dias_ciclo or int(dias_ciclo) <= 0:
        raise ValueError("Los días del ciclo deben ser mayores a cero.")

    programa = consultar_uno("SELECT convenio_id FROM programas_convenio WHERE id=?", (programa_convenio_id,))
    if not programa:
        raise ValueError("El programa indicado no existe.")
    convenio_id = dict(programa)["convenio_id"]

    actividad = consultar_uno("SELECT nombre FROM catalogo_actividades WHERE id=?", (actividad_id,))
    if not actividad:
        raise ValueError("La actividad seleccionada no existe en el catálogo.")
    tipo_servicio = dict(actividad)["nombre"]

    return ejecutar(
        "INSERT INTO convenios_eps_servicios(convenio_id, programa_convenio_id, actividad_id, tipo_servicio, grupo_tope, limite_cantidad, dias_ciclo, valor_normal, valor_adicional) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (convenio_id, programa_convenio_id, int(actividad_id), tipo_servicio, (grupo_tope or "").strip() or None,
         int(limite_cantidad), int(dias_ciclo), float(valor_normal or 0), float(valor_adicional or 0)),
    )


def actualizar_servicio_convenio(servicio_id, actividad_id, grupo_tope, limite_cantidad, dias_ciclo,
                                    valor_normal, valor_adicional):
    actividad = consultar_uno("SELECT nombre FROM catalogo_actividades WHERE id=?", (actividad_id,))
    if not actividad:
        raise ValueError("La actividad seleccionada no existe en el catálogo.")
    tipo_servicio = dict(actividad)["nombre"]

    ejecutar(
        "UPDATE convenios_eps_servicios SET actividad_id=?, tipo_servicio=?, grupo_tope=?, limite_cantidad=?, dias_ciclo=?, valor_normal=?, valor_adicional=? WHERE id=?",
        (int(actividad_id), tipo_servicio, (grupo_tope or "").strip() or None, int(limite_cantidad), int(dias_ciclo),
         float(valor_normal or 0), float(valor_adicional or 0), servicio_id),
    )


def quitar_servicio_convenio(servicio_id: int):
    ejecutar("UPDATE convenios_eps_servicios SET activo=0 WHERE id=?", (servicio_id,))


# ==========================================
# ASIGNACIÓN DEL PROGRAMA AL PACIENTE
# ==========================================

def convenio_actual_paciente(paciente_id: int):
    """
    El programa (dentro de un convenio de EPS) que tiene
    actualmente asignado el paciente -- con los datos del
    convenio y la EPS ya resueltos, para no tener que hacer
    joins adicionales en cada validación.
    """
    fila = consultar_uno(
        """
        SELECT pc.*, ce.eps, ce.nombre_plan, ce.estado AS convenio_estado,
               prog.nombre AS nombre_programa, prog.id AS programa_convenio_id
        FROM paciente_convenio pc
        LEFT JOIN convenios_eps ce ON ce.id = pc.convenio_id
        LEFT JOIN programas_convenio prog ON prog.id = pc.programa_convenio_id
        WHERE pc.paciente_id=? AND pc.es_actual=1
        """,
        (paciente_id,),
    )
    return dict(fila) if fila else None


def asignar_convenio_paciente(paciente_id, programa_convenio_id, fecha_ingreso, usuario_id, fecha_fin=None,
                                autorizacion=None, profesional_tratante_id=None, medico_tratante_id=None) -> int:
    if not programa_convenio_id:
        raise ValueError("Debe indicar el programa del convenio de la EPS.")
    if not fecha_ingreso:
        from datetime import date
        fecha_ingreso = date.today().isoformat()

    programa = consultar_uno("SELECT convenio_id FROM programas_convenio WHERE id=?", (programa_convenio_id,))
    if not programa:
        raise ValueError("El programa indicado no existe.")
    convenio_id = dict(programa)["convenio_id"]

    # Si no se indica hasta cuándo queda autorizado este programa
    # para el paciente, se sugiere automáticamente 3 meses desde
    # el ingreso -- que es lo usual en las autorizaciones de las
    # EPS -- pero queda como un valor de referencia: se puede
    # cambiar en cualquier momento si la autorización real es
    # distinta.
    if not fecha_fin:
        from datetime import date, timedelta
        inicio = date.fromisoformat(fecha_ingreso[:10])
        fecha_fin = (inicio + timedelta(days=90)).isoformat()

    # Si ya tenía un programa activo, se cierra (queda en el historial) antes de abrir el nuevo --
    # igual que se hace con los programas de atención clínicos.
    ejecutar(
        "UPDATE paciente_convenio SET es_actual=0, fecha_fin=? WHERE paciente_id=? AND es_actual=1",
        (fecha_ingreso, paciente_id),
    )

    return ejecutar(
        """
        INSERT INTO paciente_convenio(
            paciente_id, convenio_id, programa_convenio_id, fecha_ingreso, fecha_fin,
            autorizacion, profesional_tratante_id, medico_tratante_id, usuario_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (paciente_id, convenio_id, programa_convenio_id, fecha_ingreso, fecha_fin,
         autorizacion or None, profesional_tratante_id or None, medico_tratante_id or None, usuario_id),
    )


def historial_convenios_paciente(paciente_id: int):
    filas = consultar_todos(
        """
        SELECT pc.*, ce.eps, ce.nombre_plan, prog.nombre AS nombre_programa
        FROM paciente_convenio pc
        LEFT JOIN convenios_eps ce ON ce.id = pc.convenio_id
        LEFT JOIN programas_convenio prog ON prog.id = pc.programa_convenio_id
        WHERE pc.paciente_id=?
        ORDER BY pc.fecha_ingreso DESC
        """,
        (paciente_id,),
    )
    return [dict(f) for f in filas]


# ==========================================
# GENERACIÓN AUTOMÁTICA DE CUENTAS POR COBRAR
# ==========================================

def verificar_disponibilidad_convenio(paciente_id: int, nombre_servicio: str, cantidad_nueva: int, fecha_referencia=None):
    """
    Se llama ANTES de asignarle sesiones nuevas a un paciente
    (no cuando se completan, sino cuando el médico las manda) --
    revisa cuántas sesiones de ese servicio (o de todo su grupo,
    si comparte tope -- como las 4 terapias) ya tiene asignadas
    en el ciclo actual, y si la cantidad nueva que se quiere
    agregar se pasaría del tope autorizado por el programa.

    No bloquea nada por sí sola -- devuelve la información para
    que quien esté asignando decida, con una alerta clara si ya
    no hay cupo. (El bloqueo real de la programación, cuando no
    hay autorización de la EPS para el excedente, se maneja en
    el módulo de autorizaciones.)
    """
    from datetime import date

    resultado = {
        "aplica": False, "disponible": True, "ya_asignadas": 0, "limite": 0,
        "cantidad_nueva": cantidad_nueva, "exceden": 0, "mensaje": "",
    }

    convenio_actual = convenio_actual_paciente(paciente_id)
    if not convenio_actual or not convenio_actual.get("programa_convenio_id"):
        return resultado  # paciente sin programa de EPS asignado -- no aplica ningún tope

    plan_servicio = _buscar_servicio_programa(convenio_actual["programa_convenio_id"], nombre_servicio)
    if not plan_servicio:
        return resultado  # este servicio no está contemplado en su programa -- no aplica tope

    resultado["aplica"] = True
    resultado["limite"] = plan_servicio["limite_cantidad"]

    fecha_referencia = fecha_referencia or date.today().isoformat()
    ciclo = _numero_ciclo(convenio_actual["fecha_ingreso"], fecha_referencia, plan_servicio["dias_ciclo"])

    # Se calcula el rango de fechas exacto de este ciclo, para
    # poder contar cuántas visitas YA ASIGNADAS (aunque todavía
    # no se hayan completado) caen dentro de él.
    from datetime import timedelta
    inicio_convenio = date.fromisoformat(convenio_actual["fecha_ingreso"][:10])
    inicio_ciclo = inicio_convenio + timedelta(days=ciclo * plan_servicio["dias_ciclo"])
    fin_ciclo = inicio_ciclo + timedelta(days=plan_servicio["dias_ciclo"] - 1)

    if plan_servicio.get("grupo_tope"):
        # Se cuentan TODOS los servicios que compartan el mismo grupo (ej. las 4 terapias juntas)
        filas_grupo = consultar_todos(
            "SELECT tipo_servicio FROM convenios_eps_servicios WHERE programa_convenio_id=? AND grupo_tope=? AND activo=1",
            (convenio_actual["programa_convenio_id"], plan_servicio["grupo_tope"]),
        )
        nombres_grupo = [dict(f)["tipo_servicio"] for f in filas_grupo]
        marcadores = ",".join("?" * len(nombres_grupo))
        fila_conteo = consultar_uno(
            f"""
            SELECT COALESCE(SUM(sp.numero_sesiones), 0) AS total
            FROM servicios_paciente sp
            WHERE sp.paciente_id=? AND sp.tipo_servicio IN ({marcadores}) AND sp.estado='Activo'
              AND date(sp.fecha_inicio) >= date(?) AND date(sp.fecha_inicio) <= date(?)
            """,
            (paciente_id, *nombres_grupo, inicio_ciclo.isoformat(), fin_ciclo.isoformat()),
        )
        etiqueta_servicio = plan_servicio["grupo_tope"]
    else:
        fila_conteo = consultar_uno(
            """
            SELECT COALESCE(SUM(numero_sesiones), 0) AS total
            FROM servicios_paciente
            WHERE paciente_id=? AND tipo_servicio=? AND estado='Activo'
              AND date(fecha_inicio) >= date(?) AND date(fecha_inicio) <= date(?)
            """,
            (paciente_id, nombre_servicio, inicio_ciclo.isoformat(), fin_ciclo.isoformat()),
        )
        etiqueta_servicio = nombre_servicio

    ya_asignadas = dict(fila_conteo)["total"] if fila_conteo else 0
    resultado["ya_asignadas"] = ya_asignadas

    # Si la EPS ya autorizó sesiones adicionales para este
    # paciente y este servicio (o grupo), esa cantidad se suma
    # al límite normal del programa -- es lo que hace que, una
    # vez autorizado, sí se pueda programar el excedente.
    from services.autorizaciones_eps_service import cantidad_autorizada_disponible
    autorizado_adicional = cantidad_autorizada_disponible(paciente_id, nombre_servicio, plan_servicio.get("grupo_tope"))
    limite_efectivo = plan_servicio["limite_cantidad"] + autorizado_adicional
    resultado["autorizado_adicional"] = autorizado_adicional
    resultado["limite_efectivo"] = limite_efectivo

    total_con_nueva = ya_asignadas + cantidad_nueva
    if total_con_nueva > limite_efectivo:
        resultado["disponible"] = False
        resultado["exceden"] = total_con_nueva - limite_efectivo
        # Cuántas de las que se están pidiendo SÍ caben dentro de lo
        # ya autorizado (normal + adicional aprobado) -- el resto es
        # lo que queda bloqueado, pendiente de una nueva autorización.
        resultado["cantidad_permitida"] = max(0, limite_efectivo - ya_asignadas)
        texto_adicional = f" (de las cuales {autorizado_adicional} son de un excedente ya autorizado por la EPS)" if autorizado_adicional else ""
        resultado["mensaje"] = (
            f"El programa '{convenio_actual.get('nombre_programa') or convenio_actual['nombre_plan']}' de {convenio_actual['eps']} autoriza "
            f"{limite_efectivo} sesión(es) de {etiqueta_servicio} cada {plan_servicio['dias_ciclo']} días{texto_adicional}, y este paciente ya "
            f"tiene {ya_asignadas} asignada(s) en el periodo actual. De las {cantidad_nueva} que se están pidiendo, solo "
            f"{resultado['cantidad_permitida']} se pueden programar ahora -- las {resultado['exceden']} restantes quedan como una "
            f"solicitud pendiente de autorización de la EPS, y no se podrán programar hasta que se autoricen."
        )
    else:
        resultado["cantidad_permitida"] = cantidad_nueva
        resultado["mensaje"] = f"Dentro del tope autorizado: {ya_asignadas + cantidad_nueva} de {limite_efectivo} en el periodo actual."

    return resultado


def _buscar_servicio_programa(programa_convenio_id: int, tipo_servicio: str):
    """Encuentra la fila del plan que aplica a este tipo de servicio (comparación sin importar mayúsculas/acentos exactos)."""
    fila = consultar_uno(
        "SELECT * FROM convenios_eps_servicios WHERE programa_convenio_id=? AND activo=1 AND LOWER(tipo_servicio)=LOWER(?)",
        (programa_convenio_id, tipo_servicio),
    )
    return dict(fila) if fila else None


def _numero_ciclo(fecha_ingreso: str, fecha_servicio: str, dias_ciclo: int) -> int:
    from datetime import date

    ingreso = date.fromisoformat(fecha_ingreso[:10])
    servicio = date.fromisoformat(fecha_servicio[:10])
    dias_transcurridos = (servicio - ingreso).days
    if dias_transcurridos < 0:
        dias_transcurridos = 0
    return dias_transcurridos // dias_ciclo


def registrar_consumo_servicio(paciente_id: int, tipo_servicio: str, fecha_servicio: str, programacion_id=None):
    """
    Se llama cada vez que se COMPLETA una visita (no cuando
    solo se programa, ni cuando se cancela) -- revisa si el
    paciente tiene un programa de EPS asignado, y si ese
    servicio está contemplado en su plan. Si es así, cuenta
    cuántas veces se ha usado ese mismo servicio (o el grupo
    que comparte tope, como las terapias) en el ciclo actual
    (los N días desde que el paciente ingresó al programa), y
    genera la cuenta por cobrar con el valor que corresponda:
    el normal si todavía está dentro del tope, o el adicional
    si ya se pasó.

    Si el paciente no tiene programa asignado, o el servicio no
    está contemplado en su plan, simplemente no genera nada --
    no es un error, solo significa que ese servicio no se
    factura a ninguna EPS por este medio.
    """
    convenio_actual = convenio_actual_paciente(paciente_id)
    if not convenio_actual or not convenio_actual.get("programa_convenio_id"):
        return None

    # Si el programa del paciente no está atado a ningún
    # convenio de EPS (un programa "general"/independiente), no
    # hay ninguna EPS a la que facturarle -- se sigue llevando
    # el control del tope con normalidad, solo que sin generar
    # ninguna cuenta por cobrar (no hay a quién cobrarle).
    if convenio_actual.get("convenio_id") is None:
        return None

    plan_servicio = _buscar_servicio_programa(convenio_actual["programa_convenio_id"], tipo_servicio)
    if not plan_servicio:
        return None

    ciclo = _numero_ciclo(convenio_actual["fecha_ingreso"], fecha_servicio, plan_servicio["dias_ciclo"])

    # Cuenta lo ya consumido en este mismo ciclo -- si el servicio
    # pertenece a un grupo (como "Terapias"), se cuentan TODOS los
    # servicios de ese grupo juntos, no solo el mismo tipo exacto.
    if plan_servicio.get("grupo_tope"):
        fila_conteo = consultar_uno(
            """
            SELECT COUNT(*) AS total FROM cuentas_por_cobrar_eps
            WHERE paciente_id=? AND programa_convenio_id=? AND grupo_tope=? AND numero_ciclo=?
            """,
            (paciente_id, convenio_actual["programa_convenio_id"], plan_servicio["grupo_tope"], ciclo),
        )
    else:
        fila_conteo = consultar_uno(
            """
            SELECT COUNT(*) AS total FROM cuentas_por_cobrar_eps
            WHERE paciente_id=? AND programa_convenio_id=? AND tipo_servicio=? AND numero_ciclo=? AND grupo_tope IS NULL
            """,
            (paciente_id, convenio_actual["programa_convenio_id"], tipo_servicio, ciclo),
        )
    ya_consumidos = dict(fila_conteo)["total"] if fila_conteo else 0

    es_adicional = ya_consumidos >= plan_servicio["limite_cantidad"]
    valor = plan_servicio["valor_adicional"] if es_adicional else plan_servicio["valor_normal"]

    return ejecutar(
        """
        INSERT INTO cuentas_por_cobrar_eps(
            paciente_id, convenio_id, programa_convenio_id, convenio_servicio_id, programacion_id, tipo_servicio, grupo_tope,
            fecha_servicio, numero_ciclo, es_adicional, valor
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (paciente_id, convenio_actual["convenio_id"], convenio_actual["programa_convenio_id"], plan_servicio["id"], programacion_id, tipo_servicio,
         plan_servicio.get("grupo_tope"), fecha_servicio, ciclo, 1 if es_adicional else 0, valor),
    )


def resumen_consumo_ciclo_actual(paciente_id: int):
    """Para mostrarle al usuario, de un vistazo, cuánto le queda disponible de cada servicio en el ciclo actual."""
    convenio_actual = convenio_actual_paciente(paciente_id)
    if not convenio_actual or not convenio_actual.get("programa_convenio_id"):
        return None

    from datetime import date
    hoy = date.today().isoformat()
    plan = listar_servicios_programa(convenio_actual["programa_convenio_id"])

    resumen = []
    vistos_grupos = set()
    for item in plan:
        clave_grupo = item.get("grupo_tope")
        if clave_grupo:
            if clave_grupo in vistos_grupos:
                continue
            vistos_grupos.add(clave_grupo)

        ciclo = _numero_ciclo(convenio_actual["fecha_ingreso"], hoy, item["dias_ciclo"])
        if clave_grupo:
            fila = consultar_uno(
                "SELECT COUNT(*) AS total FROM cuentas_por_cobrar_eps WHERE paciente_id=? AND programa_convenio_id=? AND grupo_tope=? AND numero_ciclo=?",
                (paciente_id, convenio_actual["programa_convenio_id"], clave_grupo, ciclo),
            )
            etiqueta = clave_grupo
        else:
            fila = consultar_uno(
                "SELECT COUNT(*) AS total FROM cuentas_por_cobrar_eps WHERE paciente_id=? AND programa_convenio_id=? AND tipo_servicio=? AND numero_ciclo=? AND grupo_tope IS NULL",
                (paciente_id, convenio_actual["programa_convenio_id"], item["tipo_servicio"], ciclo),
            )
            etiqueta = item["tipo_servicio"]

        usados = dict(fila)["total"] if fila else 0
        resumen.append({
            "etiqueta": etiqueta, "usados": usados, "limite": item["limite_cantidad"],
            "disponibles": max(0, item["limite_cantidad"] - usados), "ciclo_numero": ciclo,
        })

    return {"convenio": convenio_actual, "servicios": resumen}


# ==========================================
# FACTURACIÓN A LA EPS (con los tres modos de agrupación)
# ==========================================

def listar_cuentas_pendientes(fecha_desde=None, fecha_hasta=None, eps=None, paciente_id=None):
    sql = """
        SELECT cc.*, p.primer_nombre, p.primer_apellido, p.documento, p.tipo_documento, ce.eps, ce.nombre_plan,
               prog.nombre AS nombre_programa
        FROM cuentas_por_cobrar_eps cc
        JOIN pacientes p ON p.id = cc.paciente_id
        JOIN convenios_eps ce ON ce.id = cc.convenio_id
        LEFT JOIN programas_convenio prog ON prog.id = cc.programa_convenio_id
        WHERE cc.estado='Pendiente'
    """
    parametros = []
    if fecha_desde:
        sql += " AND date(cc.fecha_servicio) >= date(?)"
        parametros.append(fecha_desde)
    if fecha_hasta:
        sql += " AND date(cc.fecha_servicio) <= date(?)"
        parametros.append(fecha_hasta)
    if eps:
        sql += " AND ce.eps = ?"
        parametros.append(eps)
    if paciente_id:
        sql += " AND cc.paciente_id = ?"
        parametros.append(paciente_id)
    sql += " ORDER BY ce.eps, p.primer_apellido, cc.fecha_servicio"

    filas = consultar_todos(sql, tuple(parametros))
    return [dict(f) for f in filas]


def resumen_pendientes_por_eps(fecha_desde=None, fecha_hasta=None):
    """Para la pantalla de facturación: cuánto hay pendiente de cobrar, agrupado por EPS."""
    cuentas = listar_cuentas_pendientes(fecha_desde, fecha_hasta)
    por_eps = {}
    for c in cuentas:
        por_eps.setdefault(c["eps"], {"eps": c["eps"], "cantidad": 0, "valor_total": 0})
        por_eps[c["eps"]]["cantidad"] += 1
        por_eps[c["eps"]]["valor_total"] += c["valor"]
    return list(por_eps.values())


def _agrupar_cuentas(cuentas: list, modo: str) -> dict:
    """
    modo:
      - "por_eps": una sola factura con TODOS los pacientes y servicios de esa EPS.
      - "por_paciente": una factura por paciente, con todos sus servicios juntos.
      - "por_paciente_servicio": una factura por cada combinación paciente + tipo de servicio.
      - "por_programa": una factura por cada programa (EPS + programa), con todos los pacientes de ese programa juntos.
    """
    grupos = {}
    for c in cuentas:
        if modo == "por_eps":
            clave = c["eps"]
        elif modo == "por_programa":
            clave = (c["eps"], c.get("programa_convenio_id"))
        elif modo == "por_paciente":
            clave = (c["eps"], c["paciente_id"])
        else:  # por_paciente_servicio
            clave = (c["eps"], c["paciente_id"], c["tipo_servicio"])
        grupos.setdefault(clave, []).append(c)
    return grupos


def generar_facturacion_eps(fecha_desde, fecha_hasta, modo, eps=None, usuario_id=None) -> dict:
    """
    Genera las facturas de las cuentas por cobrar pendientes en
    el rango de fechas indicado, agrupadas según el modo
    elegido. Cada factura generada queda con el detalle completo
    de qué se está cobrando (paciente, servicio, fecha, si era
    normal o adicional), y las cuentas por cobrar usadas quedan
    marcadas como "Facturado" para no volver a cobrarlas dos
    veces.
    """
    if modo not in ("por_eps", "por_programa", "por_paciente", "por_paciente_servicio"):
        raise ValueError("Modo de facturación no válido.")

    cuentas = listar_cuentas_pendientes(fecha_desde, fecha_hasta, eps)
    if not cuentas:
        return {"facturas_generadas": [], "mensaje": "No hay cuentas pendientes en ese rango de fechas."}

    grupos = _agrupar_cuentas(cuentas, modo)

    from services.facturacion_service import _generar_factura_desde_items

    facturas_generadas = []
    for clave, items in grupos.items():
        resultado = _generar_factura_desde_items(items, usuario_id)
        facturas_generadas.append(resultado)

        ids_cuentas = [str(item["id"]) for item in items]
        ejecutar(
            f"UPDATE cuentas_por_cobrar_eps SET estado='Facturado', factura_id=? WHERE id IN ({','.join(ids_cuentas)})",
            (resultado["factura_id"],),
        )

    return {"facturas_generadas": facturas_generadas, "total_facturas": len(facturas_generadas)}
