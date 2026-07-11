"""
HomeCare Enterprise - Examen Físico por Sistemas

Un registro por visita/consulta, con cada sistema por
separado (cabeza, cara, boca, cuello, torax, abdomen,
extremidades, vascular, neurológico, columna) -- tal como en
el formato de historia clínica de medicina general de la IPS.
"""

from database.database import consultar_todos, consultar_uno, ejecutar

SISTEMAS = [
    "cabeza", "cara", "boca", "cuello", "torax",
    "abdomen", "extremidades", "vascular", "neurologico", "columna",
]


def crear(paciente_id, programacion_id, profesional_id, tipo_profesional, valores: dict, usuario) -> int:
    if not paciente_id:
        raise ValueError("Debe indicar el paciente.")

    datos = {"paciente_id": paciente_id, "programacion_id": programacion_id or None,
              "profesional_id": profesional_id or None, "tipo_profesional": tipo_profesional or "",
              "usuario_creacion": usuario}
    for sistema in SISTEMAS:
        datos[sistema] = valores.get(sistema, "")

    return ejecutar(
        f"""
        INSERT INTO examen_fisico(
            paciente_id, programacion_id, profesional_id, tipo_profesional,
            {', '.join(SISTEMAS)}, usuario_creacion
        ) VALUES (
            :paciente_id, :programacion_id, :profesional_id, :tipo_profesional,
            {', '.join(':' + s for s in SISTEMAS)}, :usuario_creacion
        )
        """,
        datos,
    )


def listar_por_paciente(paciente_id: int):
    filas = consultar_todos(
        """
        SELECT e.*, pr.nombre_completo AS profesional
        FROM examen_fisico e
        LEFT JOIN profesionales pr ON pr.id = e.profesional_id
        WHERE e.paciente_id=?
        ORDER BY e.fecha_creacion DESC
        """,
        (paciente_id,),
    )
    return [dict(f) for f in filas]


def ultimo_por_paciente(paciente_id: int):
    fila = consultar_uno(
        """
        SELECT e.*, pr.nombre_completo AS profesional
        FROM examen_fisico e
        LEFT JOIN profesionales pr ON pr.id = e.profesional_id
        WHERE e.paciente_id=?
        ORDER BY e.fecha_creacion DESC LIMIT 1
        """,
        (paciente_id,),
    )
    return dict(fila) if fila else None
