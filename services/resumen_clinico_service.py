"""
HomeCare Enterprise - Resumen Clínico del Paciente

Junta, en un solo vistazo desde la ficha del paciente, la
informacion diagnosticada y registrada por cada tipo de
profesional (medico, enfermeria, curaciones/aplicador,
terapias, etc.): diagnosticos activos, equipo de atencion
asignado, y el ultimo informe que dejo cada tipo de
profesional -- para no tener que entrar a la Historia
Clinica completa solo para ver "que dijo el enfermero" o
"que dijo el de curaciones" la ultima vez.
"""

from database.database import consultar_todos


def equipo_de_atencion(paciente_id: int) -> list:
    """Profesionales con un servicio ACTIVO asignado a este paciente."""
    filas = consultar_todos(
        """
        SELECT DISTINCT pr.id, pr.nombre_completo, pr.especialidad_principal
        FROM servicios_paciente sp
        JOIN profesionales pr ON pr.id = sp.profesional_id
        WHERE sp.paciente_id=? AND sp.estado='Activo'
        ORDER BY pr.nombre_completo
        """,
        (paciente_id,),
    )
    return [dict(f) for f in filas]


def ultimo_informe_por_tipo_profesional(paciente_id: int) -> list:
    """
    El informe (nota de visita) mas reciente que dejo CADA
    tipo de profesional distinto (Enfermero, Medico, Cuidador,
    Aplicador, Terapeuta, etc.), para ver de un vistazo el
    ultimo reporte de cada disciplina.
    """
    filas = consultar_todos(
        """
        SELECT e.tipo_profesional, e.nota, e.fecha, e.consecutivo,
               pr.nombre_completo AS profesional
        FROM evoluciones e
        LEFT JOIN profesionales pr ON pr.id = e.profesional_id
        WHERE e.paciente_id=?
          AND e.tipo_registro='INFORME'
        ORDER BY e.consecutivo DESC
        """,
        (paciente_id,),
    )

    vistos = set()
    ultimos = []

    for f in filas:
        f = dict(f)
        tipo = f["tipo_profesional"] or "Sin especificar"
        if tipo in vistos:
            continue
        vistos.add(tipo)
        ultimos.append(f)

    return ultimos


def resumen_completo(paciente_id: int) -> dict:
    from services.diagnosticos_service import DiagnosticosService
    from services.programas_atencion_service import programa_actual

    return {
        "diagnosticos_activos": DiagnosticosService.listar_activos_por_paciente(paciente_id),
        "equipo_atencion": equipo_de_atencion(paciente_id),
        "ultimos_informes": ultimo_informe_por_tipo_profesional(paciente_id),
        "programa_actual": programa_actual(paciente_id),
    }
