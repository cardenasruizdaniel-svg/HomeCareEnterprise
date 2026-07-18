"""
HomeCare Enterprise - Gestión de visitas (Programar / Cancelar / Reprogramar)

Cada fila de la planilla de visitas nace como una fecha
TENTATIVA (generada al asignar una actividad del programa).
Este servicio maneja el paso siguiente: confirmarla en la
agenda real (Programar), cambiar su fecha/hora si ya estaba
programada (Reprogramar), o cancelarla. En los dos primeros
casos se envian alertas de WhatsApp al paciente y al
profesional, igual que con cualquier otra visita.
"""

from database.database import consultar_uno, ejecutar
from repositories.planilla_visitas_repository import PlanillaVisitasRepository


def listar_visitas_de_servicio(servicio_paciente_id: int):
    from database.database import consultar_todos
    filas = consultar_todos(
        """
        SELECT pv.*, pr.nombre_completo AS profesional
        FROM planilla_visitas pv
        LEFT JOIN profesionales pr ON pr.id = pv.profesional_id
        WHERE pv.servicio_paciente_id=?
        ORDER BY pv.fecha
        """,
        (servicio_paciente_id,),
    )
    return [dict(f) for f in filas]


def programar_visita(planilla_id: int, fecha: str, hora_inicio: str, hora_fin: str,
                       profesional_id: int, usuario_id=None) -> dict:
    """
    Confirma una visita tentativa: la lleva a la agenda real
    (crea la programacion), y avisa por WhatsApp al paciente
    y al profesional. La FECHA es obligatoria; la HORA es
    tentativa (no obligatoria) -- si no se indica, queda como
    "por confirmar" y se puede precisar despues.
    """

    if not profesional_id:
        raise ValueError("Debe indicar qué profesional atenderá la visita.")

    if not fecha:
        raise ValueError("Debe indicar la fecha de la visita.")

    hora_inicio = hora_inicio or "08:00"
    hora_fin = hora_fin or "09:00"

    fila = PlanillaVisitasRepository.obtener(planilla_id)
    if not fila:
        raise ValueError("La visita no existe.")
    fila = dict(fila)

    if fila["estado"] == "Cancelada":
        raise ValueError("Esta visita está cancelada; no se puede programar.")

    if fila.get("programacion_id"):
        raise ValueError("Esta visita ya está programada. Use 'Reprogramar' para cambiar la fecha.")

    servicio = consultar_uno("SELECT * FROM servicios_paciente WHERE id=?", (fila["servicio_paciente_id"],))
    servicio = dict(servicio) if servicio else {}

    paciente = consultar_uno(
        "SELECT direccion, barrio, municipio, departamento FROM pacientes WHERE id=?",
        (fila["paciente_id"],),
    )
    paciente = dict(paciente) if paciente else {}

    from services.programacion_service import crear_visita

    nombre_servicio = servicio.get("tipo_servicio", "Visita domiciliaria")
    if servicio.get("subtipo"):
        nombre_servicio += f" - {servicio['subtipo']}"

    programacion_id = crear_visita(
        paciente_id=fila["paciente_id"], profesional_id=profesional_id, diagnostico_id=None,
        fecha=fecha, hora_inicio=hora_inicio, hora_fin=hora_fin, duracion=60,
        servicio=nombre_servicio, procedimiento="", codigo_cups="", valor_servicio=0,
        prioridad="Normal",
        direccion=paciente.get("direccion", ""), barrio=paciente.get("barrio", ""),
        ciudad=paciente.get("municipio", ""), departamento=paciente.get("departamento", ""),
        telefono_contacto="", nombre_contacto="", observaciones=servicio.get("indicaciones", ""),
        usuario=usuario_id,
    )
    # crear_visita ya envia las alertas de WhatsApp/calendario
    # al paciente y al profesional.

    ejecutar(
        """
        UPDATE planilla_visitas
        SET programacion_id=?, profesional_id=?, fecha=?, hora_inicio=?, hora_fin=?, estado='Programada'
        WHERE id=?
        """,
        (programacion_id, profesional_id, fecha, hora_inicio, hora_fin, planilla_id),
    )

    return {"ok": True, "programacion_id": programacion_id}


def reprogramar_visita(planilla_id: int, nueva_fecha: str, nueva_hora_inicio: str,
                         nueva_hora_fin: str, nuevo_profesional_id=None, usuario_id=None) -> dict:
    """
    Cambia la fecha/hora (y opcionalmente el profesional) de
    una visita YA programada, actualiza la agenda real, y
    vuelve a avisar por WhatsApp del nuevo horario. La hora
    sigue siendo tentativa (no obligatoria).
    """

    if not nueva_fecha:
        raise ValueError("Debe indicar la nueva fecha de la visita.")

    nueva_hora_inicio = nueva_hora_inicio or "08:00"
    nueva_hora_fin = nueva_hora_fin or "09:00"

    fila = PlanillaVisitasRepository.obtener(planilla_id)
    if not fila:
        raise ValueError("La visita no existe.")
    fila = dict(fila)

    if not fila.get("programacion_id"):
        raise ValueError("Esta visita todavía no está programada; use 'Programar' primero.")

    profesional_id = nuevo_profesional_id or fila["profesional_id"]

    ejecutar(
        "UPDATE programaciones SET fecha=?, hora_inicio=?, hora_fin=?, profesional_id=?, estado='Programada' WHERE id=?",
        (nueva_fecha, nueva_hora_inicio, nueva_hora_fin, profesional_id, fila["programacion_id"]),
    )

    ejecutar(
        "UPDATE planilla_visitas SET fecha=?, hora_inicio=?, hora_fin=?, profesional_id=? WHERE id=?",
        (nueva_fecha, nueva_hora_inicio, nueva_hora_fin, profesional_id, planilla_id),
    )

    try:
        from services.programacion_service import _notificar_visita_programada
        _notificar_visita_programada(fila["programacion_id"])
    except Exception:
        pass

    return {"ok": True}


def cancelar_visita(planilla_id: int, motivo: str = "", usuario_id=None) -> dict:

    fila = PlanillaVisitasRepository.obtener(planilla_id)
    if not fila:
        raise ValueError("La visita no existe.")
    fila = dict(fila)

    if fila.get("programacion_id"):
        ejecutar(
            "UPDATE programaciones SET estado='Cancelada' WHERE id=?",
            (fila["programacion_id"],),
        )

    ejecutar(
        "UPDATE planilla_visitas SET estado='Cancelada', motivo_cancelacion=? WHERE id=?",
        (motivo or "Cancelada por el usuario", planilla_id),
    )

    try:
        from services.servicios_paciente_service import renovar_si_corresponde
        renovar_si_corresponde(fila["servicio_paciente_id"])
    except Exception:
        pass

    return {"ok": True}
