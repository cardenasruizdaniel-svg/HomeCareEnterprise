"""
HomeCare Enterprise - Sugerencia de reparto de visitas médicas

Cuando se va a programar una visita médica (la de valoración
inicial, o cualquier visita médica posterior), esto sugiere a
qué médico asignarla -- repartiendo la carga entre todos los
médicos activos, en vez de que siempre le toque al mismo. Es
solo una SUGERENCIA: la persona que programa puede elegir a
cualquier otro médico si el caso lo amerita, y las visitas ya
asignadas se pueden pasar de un médico a otro después
(reprogramando con un profesional distinto).
"""

from database.database import consultar_todos


def sugerir_medicos(fecha_desde=None, fecha_hasta=None) -> list:
    """
    Lista de médicos activos, cada uno con la cantidad de
    visitas médicas que tiene actualmente asignadas (Pendientes
    + Programadas, en el rango de fechas indicado o en general
    si no se indica rango) -- ordenados de MENOS a MÁS carga,
    para que el primero de la lista sea la sugerencia principal.
    """

    condicion_fecha = ""
    parametros = []
    if fecha_desde and fecha_hasta:
        condicion_fecha = "AND (pv.fecha IS NULL OR pv.fecha BETWEEN ? AND ?)"
        parametros = [fecha_desde, fecha_hasta]

    filas = consultar_todos(
        f"""
        SELECT pf.id AS profesional_id, pf.nombre_completo, pf.especialidad_principal,
               COUNT(pv.id) AS visitas_asignadas
        FROM profesionales pf
        LEFT JOIN servicios_paciente sp ON sp.profesional_id = pf.id AND sp.estado='Activo'
        LEFT JOIN planilla_visitas pv ON pv.servicio_paciente_id = sp.id
            AND pv.estado IN ('Pendiente', 'Programada') {condicion_fecha}
        WHERE pf.estado='ACTIVO' AND pf.especialidad_principal LIKE '%édic%'
        GROUP BY pf.id
        ORDER BY visitas_asignadas ASC, pf.nombre_completo
        """,
        tuple(parametros),
    )

    resultado = [dict(f) for f in filas]
    for i, medico in enumerate(resultado):
        medico["es_sugerido"] = (i == 0)

    return resultado


def medico_sugerido(fecha_desde=None, fecha_hasta=None) -> dict | None:
    medicos = sugerir_medicos(fecha_desde, fecha_hasta)
    return medicos[0] if medicos else None
