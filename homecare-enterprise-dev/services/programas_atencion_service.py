"""
HomeCare Enterprise - Programas de Atención del Paciente

Cuando un paciente ingresa, el medico que hace la primera
visita de valoracion lo asigna a un programa de atencion
(ej. Paciente Cronico Complejidad Alta - Con Traqueostomia).
El catalogo de programas NO es una lista cerrada: se pueden
crear programas nuevos cuando se necesiten.

Si el programa del paciente cambia mas adelante, se cierra
la asignacion anterior y se abre una nueva, quedando todo el
historial disponible, y se deja una nota en la historia
clinica (evoluciones) para que el cambio quede trazado.
"""

from datetime import date

from database.database import ejecutar
from repositories.programas_atencion_repository import ProgramasAtencionRepository


def listar_programas_activos():
    return [dict(p) for p in ProgramasAtencionRepository.listar_activos()]


def crear_programa(nombre, tipo, subtipo, descripcion, usuario_id) -> int:
    if not nombre or not tipo:
        raise ValueError("El nombre y el tipo del programa son obligatorios.")
    return ProgramasAtencionRepository.crear(nombre, tipo, subtipo, descripcion, usuario_id)


def desactivar_programa(programa_id: int):
    ProgramasAtencionRepository.desactivar(programa_id)


def conteo_pacientes_por_programa():
    return [dict(c) for c in ProgramasAtencionRepository.conteo_pacientes_por_programa()]


def programa_actual(paciente_id: int):
    from database.database import consultar_uno
    fila = consultar_uno(
        """
        SELECT pp.*, pa.nombre AS programa_nombre, pa.tipo, pa.subtipo, pr.nombre_completo AS profesional
        FROM paciente_programas pp
        JOIN programas_atencion pa ON pa.id = pp.programa_id
        LEFT JOIN profesionales pr ON pr.id = pp.profesional_id
        WHERE pp.paciente_id=? AND pp.es_actual=1
        """,
        (paciente_id,),
    )
    return dict(fila) if fila else None


def historial_programas(paciente_id: int):
    from database.database import consultar_todos
    filas = consultar_todos(
        """
        SELECT pp.*, pa.nombre AS programa_nombre, pa.tipo, pa.subtipo, pr.nombre_completo AS profesional
        FROM paciente_programas pp
        JOIN programas_atencion pa ON pa.id = pp.programa_id
        LEFT JOIN profesionales pr ON pr.id = pp.profesional_id
        WHERE pp.paciente_id=?
        ORDER BY pp.fecha_asignacion DESC
        """,
        (paciente_id,),
    )
    return [dict(f) for f in filas]


def asignar_programa(paciente_id: int, programa_id: int, profesional_id, motivo: str, usuario_id) -> int:

    if not programa_id:
        raise ValueError("Debe seleccionar el programa de atención.")

    programa = ProgramasAtencionRepository.obtener(programa_id)
    if not programa:
        raise ValueError("El programa seleccionado no existe.")
    programa = dict(programa)

    fecha_hoy = date.today().isoformat()

    # Cerrar la asignacion anterior, si existia
    anterior = programa_actual(paciente_id)
    if anterior:
        ejecutar(
            "UPDATE paciente_programas SET es_actual=0, fecha_fin=? WHERE id=?",
            (fecha_hoy, anterior["id"]),
        )

    nuevo_id = ejecutar(
        """
        INSERT INTO paciente_programas(
            paciente_id, programa_id, profesional_id, fecha_asignacion, motivo, usuario_creacion
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (paciente_id, programa_id, profesional_id, fecha_hoy, motivo or "", usuario_id),
    )

    # Dejar constancia en la historia clinica (linea de tiempo
    # de evoluciones), para que el cambio de programa quede
    # trazado igual que cualquier otra nota clinica.
    nota = (
        f"Asignación de programa de atención: {programa['nombre']}."
        + (f" Motivo: {motivo}." if motivo else "")
        + (f" (Cambio desde: {anterior['programa_nombre']})" if anterior else " (Primera asignación)")
    )

    try:
        from services.evoluciones_service import registrar_evolucion
        registrar_evolucion(
            paciente_id=paciente_id,
            programacion_id=None,
            profesional_id=profesional_id,
            tipo_profesional="Médico",
            nota=nota,
            origen="ASIGNACION_PROGRAMA",
            usuario_id=usuario_id,
        )
    except Exception:
        pass  # la asignacion del programa no debe fallar por esto

    return nuevo_id


def asignar_programa_con_actividades(paciente_id: int, programa_id: int, profesional_id,
                                        motivo: str, actividades: list, usuario_id) -> dict:
    """
    Hace en un solo paso lo que el medico necesita en la
    valoracion inicial: asigna el programa Y las actividades
    que se le van a realizar al paciente dentro de ese
    programa (cada una con sus sesiones, fechas y, si ya se
    sabe, el profesional que las hará).
    """

    from services.servicios_paciente_service import asignar_servicio

    paciente_programa_id = asignar_programa(paciente_id, programa_id, profesional_id, motivo, usuario_id)

    resultados = []

    for actividad in actividades:

        try:
            resultado = asignar_servicio(
                paciente_id=paciente_id,
                tipo_servicio=actividad.get("nombre_actividad", "Actividad"),
                subtipo="",
                profesional_id=actividad.get("profesional_id") or None,
                frecuencia=actividad.get("frecuencia", "Diaria"),
                fecha_inicio=actividad["fecha_inicio"],
                fecha_fin=actividad.get("fecha_fin") or None,
                hora_inicio=actividad.get("hora_inicio", "08:00"),
                hora_fin=actividad.get("hora_fin", "09:00"),
                indicaciones=actividad.get("indicaciones", ""),
                usuario=usuario_id,
                actividad_id=actividad.get("actividad_id"),
                numero_sesiones=actividad.get("numero_sesiones"),
                paciente_programa_id=paciente_programa_id,
                renovacion_automatica=bool(actividad.get("renovacion_automatica")),
            )
            resultados.append({"actividad": actividad.get("nombre_actividad"), **resultado})
        except Exception as error:
            resultados.append({"actividad": actividad.get("nombre_actividad"), "error": str(error)})

    return {"paciente_programa_id": paciente_programa_id, "actividades": resultados}
