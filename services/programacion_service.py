"""
=========================================================
HomeCare Enterprise
Servicio: Programacion de visitas

Reescrito: el archivo original importaba funciones sueltas
(listar, obtener, crear, ...) de repositories.programacion_repository,
pero ese modulo solo expone la clase ProgramacionRepository
(no funciones planas), por lo que el import fallaba siempre.
=========================================================
"""

import uuid as uuid_lib
from datetime import datetime

from database.database import consultar_todos, consultar_escalar, consultar_uno, ejecutar
from repositories.programacion_repository import ProgramacionRepository
from repositories.servicios_paciente_repository import ServiciosPacienteRepository

_repo = ProgramacionRepository()


# ==========================================
# DASHBOARD
# ==========================================

def listar_programacion():
    return _repo.listar()


def obtener_visita(id):
    return _repo.obtener(id)


def obtener_agenda_dia(fecha):
    return ProgramacionRepository.agenda_dia(fecha)


def obtener_agenda_semana(fecha_referencia: str):
    from datetime import datetime, timedelta

    fecha_obj = datetime.strptime(fecha_referencia, "%Y-%m-%d")
    inicio_semana = fecha_obj - timedelta(days=fecha_obj.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    visitas = ProgramacionRepository.agenda_rango(
        inicio_semana.strftime("%Y-%m-%d"), fin_semana.strftime("%Y-%m-%d")
    )

    return {
        "visitas": visitas,
        "inicio_semana": inicio_semana.strftime("%Y-%m-%d"),
        "fin_semana": fin_semana.strftime("%Y-%m-%d"),
    }


def obtener_agenda_mes(anio: int, mes: int):
    import calendar

    MESES_ES = [
        "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ]

    ultimo_dia = calendar.monthrange(anio, mes)[1]
    fecha_inicio = f"{anio:04d}-{mes:02d}-01"
    fecha_fin = f"{anio:04d}-{mes:02d}-{ultimo_dia:02d}"

    visitas = ProgramacionRepository.agenda_rango(fecha_inicio, fecha_fin)

    return {
        "visitas": visitas,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "anio": anio,
        "mes": mes,
        "nombre_mes": MESES_ES[mes],
    }


def obtener_agenda_profesional(profesional_id, fecha):
    # Aqui SI se incluyen las canceladas (para que se vean
    # tachadas en el calendario, por transparencia); la que NO
    # las incluye es la verificacion de conflictos de horario
    # al crear una visita nueva, mas abajo en este archivo.
    return ProgramacionRepository.agenda_profesional(profesional_id, fecha, incluir_canceladas=True)


def obtener_agenda_paciente(paciente_id):
    return ProgramacionRepository.agenda_paciente(paciente_id)


def visitas_pendientes():
    return ProgramacionRepository.programaciones_pendientes()


def indicadores_dashboard(fecha: str) -> dict:

    visitas_hoy = consultar_escalar(
        "SELECT COUNT(*) FROM programaciones WHERE fecha=? AND eliminado=0",
        (fecha,),
    ) or 0

    pendientes = consultar_escalar(
        "SELECT COUNT(*) FROM programaciones "
        "WHERE eliminado=0 AND estado IN ('Programada','Confirmada')",
    ) or 0

    canceladas = consultar_escalar(
        "SELECT COUNT(*) FROM programaciones WHERE eliminado=0 AND estado='Cancelada'",
    ) or 0

    profesionales_disponibles = consultar_escalar(
        "SELECT COUNT(*) FROM profesionales WHERE estado='ACTIVO' AND disponible=1",
    ) or 0

    return {
        "visitas_hoy": visitas_hoy,
        "pendientes": pendientes,
        "canceladas": canceladas,
        "profesionales_disponibles": profesionales_disponibles,
    }


def proximas_visitas(limite: int = 20):
    return consultar_todos(
        """
        SELECT
            pr.id,
            pr.hora_inicio AS hora,
            pr.estado,
            (p.primer_nombre || ' ' || p.primer_apellido) AS paciente,
            pf.nombre_completo AS profesional,
            pr.servicio,
            pr.municipio AS ciudad
        FROM programaciones pr
        JOIN pacientes p ON p.id = pr.paciente_id
        JOIN profesionales pf ON pf.id = pr.profesional_id
        WHERE pr.eliminado = 0
        ORDER BY pr.fecha DESC, pr.hora_inicio DESC
        LIMIT ?
        """,
        (limite,),
    )


# ==========================================
# CREAR VISITA
# ==========================================

def crear_visita(
    paciente_id,
    profesional_id,
    diagnostico_id,
    fecha,
    hora_inicio,
    hora_fin,
    duracion,
    servicio,
    procedimiento,
    codigo_cups,
    valor_servicio,
    prioridad,
    direccion,
    barrio,
    ciudad,
    departamento,
    telefono_contacto,
    nombre_contacto,
    observaciones,
    usuario,
    notificar=True,
):
    # -----------------------------
    # VALIDACIONES
    # -----------------------------

    if not paciente_id:
        raise ValueError("Debe seleccionar un paciente.")

    if not profesional_id:
        raise ValueError("Debe seleccionar un profesional.")

    if not fecha:
        raise ValueError("Debe seleccionar una fecha.")

    if not hora_inicio:
        raise ValueError("Debe seleccionar una hora.")

    if not servicio:
        raise ValueError("Debe indicar el servicio.")

    # -----------------------------
    # VALIDAR AGENDA DEL PROFESIONAL
    # -----------------------------

    agenda = ProgramacionRepository.agenda_profesional(profesional_id, fecha)

    for visita in agenda:
        if visita["hora_inicio"] == hora_inicio:
            raise ValueError(
                "El profesional ya tiene una visita programada en esa hora."
            )

    # -----------------------------
    # CREAR
    # -----------------------------

    nueva_visita_id = _repo.crear({
        "uuid": str(uuid_lib.uuid4()),
        "paciente_id": paciente_id,
        "profesional_id": profesional_id,
        "diagnostico_id": diagnostico_id or None,
        "servicio": servicio,
        "procedimiento": procedimiento,
        "codigo_cups": codigo_cups or None,
        "valor_servicio": valor_servicio or 0,
        "prioridad": prioridad or "Normal",
        "estado": "Programada",
        "fecha": fecha,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "duracion": duracion,
        "direccion": direccion,
        "barrio": barrio,
        "municipio": ciudad,
        "departamento": departamento,
        "latitud": None,
        "longitud": None,
        "telefono_contacto": telefono_contacto,
        "nombre_contacto": nombre_contacto,
        "observaciones": observaciones,
        "usuario_creacion": usuario,
    })

    try:
        if notificar:
            _notificar_visita_programada(nueva_visita_id)
    except Exception:
        pass  # la notificacion nunca debe impedir que la visita quede programada

    return nueva_visita_id


def _notificar_visita_programada(visita_id):
    """
    Envia un WhatsApp al paciente y otro al profesional
    avisando que se programo una visita, y les adjunta por
    correo un archivo de calendario (.ics) que pueden abrir
    para agregar la cita a su Google Calendar, Outlook o
    Apple Calendar con un clic. Si WhatsApp/correo no estan
    configurados en el .env, queda en modo simulado (no falla).
    """

    from core.calendario_ics import generar_ics_visita
    from services.notificaciones_service import enviar_email, enviar_whatsapp

    visita = dict(_repo.obtener(visita_id))

    paciente = consultar_uno(
        "SELECT primer_nombre, primer_apellido, celular, correo FROM pacientes WHERE id=?",
        (visita["paciente_id"],),
    )
    profesional = consultar_uno(
        "SELECT nombre_completo, celular, correo FROM profesionales WHERE id=?",
        (visita["profesional_id"],),
    )

    paciente = dict(paciente) if paciente else {}
    profesional = dict(profesional) if profesional else {}

    nombre_paciente = f"{paciente.get('primer_nombre', '')} {paciente.get('primer_apellido', '')}".strip()
    nombre_profesional = profesional.get("nombre_completo", "")

    ics_contenido = generar_ics_visita(visita, nombre_paciente, nombre_profesional)

    ruta_ics = None
    try:
        import tempfile
        archivo_temporal = tempfile.NamedTemporaryFile(
            mode="w", suffix=".ics", delete=False, encoding="utf-8"
        )
        archivo_temporal.write(ics_contenido)
        archivo_temporal.close()
        ruta_ics = archivo_temporal.name
    except Exception:
        ruta_ics = None

    if paciente:
        mensaje_paciente = (
            f"Hola {nombre_paciente}, HomeCare le informa que tiene una visita domiciliaria "
            f"programada el {visita['fecha']} a las {visita['hora_inicio']} "
            f"({visita['servicio']}). Si tiene alguna duda, comuníquese con nosotros."
        )
        enviar_whatsapp(paciente.get("celular"), mensaje_paciente)

        if paciente.get("correo"):
            enviar_email(
                paciente["correo"],
                "HomeCare - Confirmación de visita domiciliaria",
                f"<p>{mensaje_paciente}</p>"
                "<p>Adjunto encontrará el evento para agregarlo a su calendario (Google, Outlook o Apple).</p>",
                ruta_ics,
            )

    if profesional:
        mensaje_profesional = (
            f"Hola {nombre_profesional}, se le asignó una nueva visita el "
            f"{visita['fecha']} a las {visita['hora_inicio']}, en {visita['direccion']}, "
            f"{visita['barrio']} ({visita['municipio']}). Servicio: {visita['servicio']}."
        )
        enviar_whatsapp(profesional.get("celular"), mensaje_profesional)

        if profesional.get("correo"):
            enviar_email(
                profesional["correo"],
                "HomeCare - Nueva visita asignada",
                f"<p>{mensaje_profesional}</p>"
                "<p>Adjunto encontrará el evento para agregarlo a su calendario (Google, Outlook o Apple).</p>",
                ruta_ics,
            )


def crear_programacion_mensual(profesional_id: int, turnos: list, usuario) -> dict:
    """
    Crea de una sola vez todos los turnos de un mes para un
    profesional (tipicamente un cuidador con horario fijo
    variable: puede trabajar distintas horas del dia, con
    distintos pacientes, incluso el mismo dia).

    `turnos` es una lista de diccionarios, cada uno con:
    fecha, hora_inicio, hora_fin, paciente_id, servicio,
    codigo_cups (opcional), procedimiento (opcional).

    IMPORTANTE: cada paciente distinto de la lista queda con su
    propio registro en "Servicios Asignados" (agrupando todos
    sus turnos del mes en un solo servicio), y cada turno queda
    programado en la agenda real -- exactamente como si se
    hubiera hecho paso a paso desde Servicios Asignados, para
    que todo se vea reflejado alli, en el calendario web, y en
    la app de campo del cuidador.

    Las horas contabilizadas para nomina siguen siendo las
    que el profesional marque realmente (ingreso/salida) en
    cada uno de estos turnos, exactamente igual que con una
    visita programada individualmente.
    """

    if not turnos:
        raise ValueError("Debe agregar al menos un turno.")

    from services.gestion_visitas_service import programar_visita

    # Agrupar los turnos por (paciente, nombre del servicio),
    # para crear UN SOLO servicio_paciente por combinacion,
    # en vez de uno por cada turno individual.
    grupos = {}
    for indice, turno in enumerate(turnos, start=1):
        if not turno.get("paciente_id") or not turno.get("fecha"):
            continue
        clave = (turno["paciente_id"], turno.get("servicio") or "Cuidado domiciliario")
        grupos.setdefault(clave, []).append(turno)

    creados = []
    errores = []
    indice_global = 0

    for (paciente_id, nombre_servicio), turnos_grupo in grupos.items():

        fechas_grupo = sorted(t["fecha"] for t in turnos_grupo if t.get("fecha"))
        if not fechas_grupo:
            continue

        servicio_id = ServiciosPacienteRepository.crear({
            "paciente_id": paciente_id,
            "tipo_servicio": nombre_servicio,
            "subtipo": None,
            "profesional_id": profesional_id,
            "frecuencia": "Mensual (variable)",
            "fecha_inicio": fechas_grupo[0],
            "fecha_fin": fechas_grupo[-1],
            "hora_inicio": turnos_grupo[0].get("hora_inicio") or "08:00",
            "hora_fin": turnos_grupo[0].get("hora_fin") or "09:00",
            "indicaciones": "",
            "usuario_creacion": usuario,
        })
        ejecutar(
            "UPDATE servicios_paciente SET numero_sesiones=? WHERE id=?",
            (len(turnos_grupo), servicio_id),
        )

        for turno in turnos_grupo:
            indice_global += 1
            try:
                if not turno.get("hora_inicio") or not turno.get("hora_fin"):
                    raise ValueError("falta la hora de inicio o fin")

                hora_inicio_dt = datetime.strptime(turno["hora_inicio"], "%H:%M")
                hora_fin_dt = datetime.strptime(turno["hora_fin"], "%H:%M")
                if (hora_fin_dt - hora_inicio_dt).total_seconds() <= 0:
                    raise ValueError("la hora de fin debe ser posterior a la de inicio")

                planilla_id = ejecutar(
                    """
                    INSERT INTO planilla_visitas(
                        servicio_paciente_id, paciente_id, fecha, hora_inicio, hora_fin,
                        profesional_id, estado
                    ) VALUES (?, ?, ?, ?, ?, ?, 'Pendiente')
                    """,
                    (servicio_id, paciente_id, turno["fecha"], turno["hora_inicio"], turno["hora_fin"], profesional_id),
                )

                resultado_programar = programar_visita(
                    planilla_id, turno["fecha"], turno["hora_inicio"], turno["hora_fin"],
                    profesional_id, usuario,
                )
                creados.append(resultado_programar)

            except Exception as error:
                errores.append({"turno": indice_global, "fecha": turno.get("fecha", ""), "error": str(error)})

    return {"creados": len(creados), "errores": errores, "total": len(creados) + len(errores)}


def historial_programacion_profesional(profesional_id: int) -> list:
    """
    Resumen mes a mes de todo lo que se le ha programado a un
    profesional (agrupado por mes), para que la oficina vea de
    un vistazo qué tanto se le ha programado antes de armar un
    mes nuevo.
    """
    filas = consultar_todos(
        """
        SELECT strftime('%Y-%m', fecha) AS mes,
               COUNT(*) AS total_visitas,
               COUNT(DISTINCT paciente_id) AS total_pacientes,
               SUM(CASE WHEN estado='Cancelada' THEN 1 ELSE 0 END) AS canceladas
        FROM programaciones
        WHERE profesional_id=?
        GROUP BY mes
        ORDER BY mes DESC
        """,
        (profesional_id,),
    )
    return [dict(f) for f in filas]


def cronograma_mensual(profesional_id: int, anio: int, mes: int) -> dict:
    """
    Cronograma de un profesional para un mes especifico, dia a
    dia, listo para mostrar en pantalla o imprimir -- un
    calendario de actividades por cuidador/profesional.
    """
    mes_texto = f"{anio:04d}-{mes:02d}"

    filas = consultar_todos(
        """
        SELECT pr.fecha, pr.hora_inicio, pr.hora_fin, pr.servicio, pr.estado,
               p.primer_nombre, p.primer_apellido, p.direccion, p.zona_ciudad
        FROM programaciones pr
        JOIN pacientes p ON p.id = pr.paciente_id
        WHERE pr.profesional_id=? AND strftime('%Y-%m', pr.fecha) = ?
        ORDER BY pr.fecha, pr.hora_inicio
        """,
        (profesional_id, mes_texto),
    )

    por_dia = {}
    for f in filas:
        f = dict(f)
        por_dia.setdefault(f["fecha"], []).append(f)

    profesional = consultar_uno("SELECT nombre_completo, especialidad_principal FROM profesionales WHERE id=?", (profesional_id,))

    return {
        "profesional": dict(profesional) if profesional else {},
        "anio": anio, "mes": mes,
        "por_dia": por_dia,
        "total_visitas": len(filas),
    }


# ==========================================
# CAMBIOS DE ESTADO
# ==========================================

def confirmar_visita(id):
    return ProgramacionRepository.cambiar_estado(id, "Confirmada")


def registrar_ingreso(id, latitud=None, longitud=None, foto_base64=None):
    """
    Marca la hora REAL de inicio de labores del profesional
    en el domicilio del paciente. Esta hora (no la
    programada) es la que alimenta la nómina. Tambien verifica,
    por geocerca, que el profesional realmente estaba en el
    domicilio del paciente, y guarda la foto tomada en ese
    momento como corroboracion adicional.
    """

    from core.geolocalizacion import verificar_geocerca

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    visita = dict(_repo.obtener(id))

    # Verificación facial: compara la foto tomada contra la
    # foto de enrolamiento del profesional, para confirmar que
    # quien está marcando el ingreso es de verdad esa persona.
    if foto_base64 and visita.get("profesional_id"):
        try:
            from services.reconocimiento_facial_service import comparar_rostros
            profesional = consultar_uno(
                "SELECT foto_enrolamiento_base64 FROM profesionales WHERE id=?", (visita["profesional_id"],)
            )
            foto_enrolamiento = dict(profesional).get("foto_enrolamiento_base64") if profesional else None
            resultado_facial = comparar_rostros(foto_enrolamiento, foto_base64)
            if not resultado_facial["verificado"]:
                raise ValueError(
                    "No se puede registrar el ingreso: " + resultado_facial["motivo"]
                )
        except ImportError as error:
            print(f"[ADVERTENCIA] Verificación facial OMITIDA (falta instalar OpenCV): {error}")  # se ve en la consola del servidor

    paciente = consultar_uno(
        "SELECT latitud, longitud, radio_geocerca_metros FROM pacientes WHERE id=?",
        (visita["paciente_id"],),
    )
    paciente = dict(paciente) if paciente else {}

    verificacion = verificar_geocerca(
        latitud, longitud,
        paciente.get("latitud"), paciente.get("longitud"),
        paciente.get("radio_geocerca_metros") or 150,
    )

    ProgramacionRepository.registrar_ingreso(
        id, ahora, latitud, longitud,
        verificacion["dentro_del_rango"], verificacion["distancia_metros"],
        foto_base64,
    )

    return verificacion


def registrar_salida(id, latitud=None, longitud=None, foto_base64=None):
    """
    Marca la hora REAL de finalizacion de labores, calcula las
    horas efectivamente trabajadas para la nómina, y verifica
    por geocerca que el profesional estaba en el domicilio del
    paciente al finalizar.
    """

    from core.geolocalizacion import verificar_geocerca

    visita = dict(_repo.obtener(id))

    if foto_base64 and visita.get("profesional_id"):
        try:
            from services.reconocimiento_facial_service import comparar_rostros
            profesional = consultar_uno(
                "SELECT foto_enrolamiento_base64 FROM profesionales WHERE id=?", (visita["profesional_id"],)
            )
            foto_enrolamiento = dict(profesional).get("foto_enrolamiento_base64") if profesional else None
            resultado_facial = comparar_rostros(foto_enrolamiento, foto_base64)
            if not resultado_facial["verificado"]:
                raise ValueError(
                    "No se puede registrar la salida: " + resultado_facial["motivo"]
                )
        except ImportError as error:
            print(f"[ADVERTENCIA] Verificación facial OMITIDA (falta instalar OpenCV): {error}")  # se ve en la consola del servidor

    ahora_dt = datetime.now()
    ahora = ahora_dt.strftime("%Y-%m-%d %H:%M:%S")

    horas_trabajadas = None

    if visita.get("hora_real_inicio"):
        try:
            inicio_dt = datetime.strptime(visita["hora_real_inicio"], "%Y-%m-%d %H:%M:%S")
            horas_trabajadas = round((ahora_dt - inicio_dt).total_seconds() / 3600, 2)
        except ValueError:
            horas_trabajadas = None

    paciente = consultar_uno(
        "SELECT latitud, longitud, radio_geocerca_metros FROM pacientes WHERE id=?",
        (visita["paciente_id"],),
    )
    paciente = dict(paciente) if paciente else {}

    verificacion = verificar_geocerca(
        latitud, longitud,
        paciente.get("latitud"), paciente.get("longitud"),
        paciente.get("radio_geocerca_metros") or 150,
    )

    ProgramacionRepository.registrar_salida(
        id, ahora, horas_trabajadas, latitud, longitud,
        verificacion["dentro_del_rango"], verificacion["distancia_metros"],
        foto_base64,
    )

    return verificacion


def iniciar_visita(id):
    return ProgramacionRepository.cambiar_estado(id, "En Curso")


def finalizar_visita(id):
    return ProgramacionRepository.cambiar_estado(id, "Completada")


def cancelar_visita(id):
    return ProgramacionRepository.cambiar_estado(id, "Cancelada")


def reprogramar_visita(id):
    return ProgramacionRepository.cambiar_estado(id, "Reprogramada")


def eliminar_visita(id):
    return ProgramacionRepository.eliminar(id)
