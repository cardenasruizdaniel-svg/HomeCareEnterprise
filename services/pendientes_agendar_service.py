"""
HomeCare Enterprise - Pacientes Pendientes de Agendar

Dos listados separados:
1. Pacientes a los que aún no se les ha programado la
   PRIMERA visita (la de valoración médica inicial).
2. Pacientes que ya tienen servicios activos, pero con
   sesiones sin programar aparte de esa primera visita
   (ej. una terapia semanal que no se ha ido agendando).
"""

from database.database import consultar_todos


def pacientes_sin_primera_visita() -> list:
    filas = consultar_todos(
        """
        SELECT p.id AS paciente_id, p.primer_nombre, p.primer_apellido, p.documento,
               p.celular, p.zona_ciudad, sp.id AS servicio_id, sp.fecha_inicio, sp.tipo_servicio
        FROM servicios_paciente sp
        JOIN pacientes p ON p.id = sp.paciente_id
        WHERE sp.tipo_servicio LIKE 'Visita de valoración médica inicial%'
          AND sp.estado = 'Activo'
          AND NOT EXISTS (
              SELECT 1 FROM planilla_visitas pv
              WHERE pv.servicio_paciente_id = sp.id AND pv.programacion_id IS NOT NULL
          )
        ORDER BY sp.fecha_inicio
        """
    )
    return [dict(f) for f in filas]


def pacientes_con_visitas_pendientes() -> list:
    """
    Servicios (que NO son la primera valoración) con al menos
    una sesión sin programar todavía.
    """
    filas = consultar_todos(
        """
        SELECT p.id AS paciente_id, p.primer_nombre, p.primer_apellido, p.documento, p.celular,
               p.zona_ciudad, sp.id AS servicio_id, sp.tipo_servicio, sp.frecuencia, sp.fecha_inicio, sp.fecha_fin,
               COUNT(pv.id) AS sesiones_totales,
               SUM(CASE WHEN pv.programacion_id IS NULL THEN 1 ELSE 0 END) AS sesiones_pendientes
        FROM servicios_paciente sp
        JOIN pacientes p ON p.id = sp.paciente_id
        JOIN planilla_visitas pv ON pv.servicio_paciente_id = sp.id
        WHERE sp.estado = 'Activo'
          AND sp.tipo_servicio NOT LIKE 'Visita de valoración médica inicial%'
        GROUP BY sp.id
        HAVING sesiones_pendientes > 0
        ORDER BY sp.fecha_inicio
        """
    )
    return [dict(f) for f in filas]


def resumen_pendientes() -> dict:
    sin_primera = pacientes_sin_primera_visita()
    con_pendientes = pacientes_con_visitas_pendientes()
    return {
        "sin_primera_visita": sin_primera,
        "total_sin_primera_visita": len(sin_primera),
        "con_visitas_pendientes": con_pendientes,
        "total_con_visitas_pendientes": len(con_pendientes),
        "por_zona": agrupar_pendientes_por_zona(sin_primera, con_pendientes),
    }


def agrupar_pendientes_por_zona(sin_primera: list, con_pendientes: list) -> list:
    """
    Junta ambos listados de pendientes y los agrupa por zona
    de la ciudad -- para que la oficina pueda ver de un vistazo
    qué pacientes de una misma zona hace falta agendar, y así
    programarlos juntos el mismo día con el mismo profesional.
    """
    from core.zonas import ZONAS_CIUDAD

    zonas = {z: [] for z in ZONAS_CIUDAD}
    zonas["Sin zona asignada"] = []

    for p in sin_primera:
        zona = p.get("zona_ciudad") or "Sin zona asignada"
        zonas.setdefault(zona, []).append({**p, "motivo": "Primera visita (valoración)"})

    for p in con_pendientes:
        zona = p.get("zona_ciudad") or "Sin zona asignada"
        zonas.setdefault(zona, []).append({**p, "motivo": p["tipo_servicio"]})

    return [{"zona": zona, "pacientes": pacientes} for zona, pacientes in zonas.items() if pacientes]
