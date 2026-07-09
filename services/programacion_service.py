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

from database.database import consultar_todos, consultar_escalar, consultar_uno
from repositories.programacion_repository import ProgramacionRepository

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
    return ProgramacionRepository.agenda_profesional(profesional_id, fecha)


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

    Las horas contabilizadas para nomina siguen siendo las
    que el profesional marque realmente (ingreso/salida) en
    cada uno de estos turnos, exactamente igual que con una
    visita programada individualmente.
    """

    if not turnos:
        raise ValueError("Debe agregar al menos un turno.")

    creados = []
    errores = []

    for indice, turno in enumerate(turnos, start=1):

        try:
            if not turno.get("paciente_id"):
                raise ValueError("falta seleccionar el paciente")
            if not turno.get("fecha"):
                raise ValueError("falta la fecha")
            if not turno.get("hora_inicio") or not turno.get("hora_fin"):
                raise ValueError("falta la hora de inicio o fin")

            paciente = consultar_uno(
                "SELECT direccion, barrio, municipio, departamento FROM pacientes WHERE id=?",
                (turno["paciente_id"],),
            )
            paciente = dict(paciente) if paciente else {}

            hora_inicio_dt = datetime.strptime(turno["hora_inicio"], "%H:%M")
            hora_fin_dt = datetime.strptime(turno["hora_fin"], "%H:%M")
            duracion = int((hora_fin_dt - hora_inicio_dt).total_seconds() / 60)

            if duracion <= 0:
                raise ValueError("la hora de fin debe ser posterior a la de inicio")

            nuevo_id = crear_visita(
                paciente_id=turno["paciente_id"],
                profesional_id=profesional_id,
                diagnostico_id=None,
                fecha=turno["fecha"],
                hora_inicio=turno["hora_inicio"],
                hora_fin=turno["hora_fin"],
                duracion=duracion,
                servicio=turno.get("servicio") or "Cuidado domiciliario",
                procedimiento=turno.get("procedimiento", ""),
                codigo_cups=turno.get("codigo_cups", ""),
                valor_servicio=turno.get("valor_servicio") or 0,
                prioridad="Normal",
                direccion=paciente.get("direccion", ""),
                barrio=paciente.get("barrio", ""),
                ciudad=paciente.get("municipio", ""),
                departamento=paciente.get("departamento", ""),
                telefono_contacto="",
                nombre_contacto="",
                observaciones=turno.get("observaciones", ""),
                usuario=usuario,
            )
            creados.append(nuevo_id)

        except Exception as error:
            errores.append({"turno": indice, "fecha": turno.get("fecha", ""), "error": str(error)})

    return {"creados": len(creados), "errores": errores, "total": len(creados) + len(errores)}


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
