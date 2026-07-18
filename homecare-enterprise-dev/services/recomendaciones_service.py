"""
HomeCare Enterprise - Recomendaciones / Plan Médico

Diagnóstico principal + hasta 3 diagnósticos relacionados
(cada uno buscado del catálogo CIE-10 oficial), tipo de
consulta, y las marcas de incapacidad / nota aclaratoria /
orden de medicamentos / orden de procedimientos -- tal como
en el formato de historia clínica de la IPS.
"""

from database.database import consultar_todos, consultar_uno, ejecutar

TIPOS_CONSULTA = [
    "PRIMERA VEZ",
    "CONTROL",
    "CONFIRMADO NUEVO",
    "CONFIRMADO REPETIDO",
    "PRESUNTIVO",
]


def crear(paciente_id, programacion_id, profesional_id, datos: dict, usuario) -> int:
    if not paciente_id:
        raise ValueError("Debe indicar el paciente.")
    if not datos.get("diagnostico_ppal_codigo"):
        raise ValueError("Debe indicar el diagnóstico principal.")

    _id = ejecutar(
        """
        INSERT INTO recomendaciones_medicas(
            paciente_id, programacion_id, profesional_id,
            diagnostico_ppal_codigo, diagnostico_ppal_nombre,
            diagnostico_rel1_codigo, diagnostico_rel1_nombre,
            diagnostico_rel2_codigo, diagnostico_rel2_nombre,
            diagnostico_rel3_codigo, diagnostico_rel3_nombre,
            tipo_consulta, incapacidad, nota_aclaratoria,
            orden_medicamentos, orden_procedimientos, recomendaciones_texto,
            usuario_creacion
        ) VALUES (
            :paciente_id, :programacion_id, :profesional_id,
            :diagnostico_ppal_codigo, :diagnostico_ppal_nombre,
            :diagnostico_rel1_codigo, :diagnostico_rel1_nombre,
            :diagnostico_rel2_codigo, :diagnostico_rel2_nombre,
            :diagnostico_rel3_codigo, :diagnostico_rel3_nombre,
            :tipo_consulta, :incapacidad, :nota_aclaratoria,
            :orden_medicamentos, :orden_procedimientos, :recomendaciones_texto,
            :usuario_creacion
        )
        """,
        {
            "paciente_id": paciente_id, "programacion_id": programacion_id or None,
            "profesional_id": profesional_id or None,
            "diagnostico_ppal_codigo": datos.get("diagnostico_ppal_codigo"),
            "diagnostico_ppal_nombre": datos.get("diagnostico_ppal_nombre"),
            "diagnostico_rel1_codigo": datos.get("diagnostico_rel1_codigo") or None,
            "diagnostico_rel1_nombre": datos.get("diagnostico_rel1_nombre") or None,
            "diagnostico_rel2_codigo": datos.get("diagnostico_rel2_codigo") or None,
            "diagnostico_rel2_nombre": datos.get("diagnostico_rel2_nombre") or None,
            "diagnostico_rel3_codigo": datos.get("diagnostico_rel3_codigo") or None,
            "diagnostico_rel3_nombre": datos.get("diagnostico_rel3_nombre") or None,
            "tipo_consulta": datos.get("tipo_consulta") or "PRIMERA VEZ",
            "incapacidad": 1 if datos.get("incapacidad") else 0,
            "nota_aclaratoria": 1 if datos.get("nota_aclaratoria") else 0,
            "orden_medicamentos": 1 if datos.get("orden_medicamentos") else 0,
            "orden_procedimientos": 1 if datos.get("orden_procedimientos") else 0,
            "recomendaciones_texto": datos.get("recomendaciones_texto") or "",
            "usuario_creacion": usuario,
        },
    )

    # Aviso corto y sin detalle clínico sensible -- si el
    # paciente/acudiente quiere el detalle completo, lo puede
    # pedir por el chatbot (que sí verifica primero que sea de
    # verdad su número registrado) o directamente con la IPS.
    try:
        from services.notificaciones_service import enviar_whatsapp
        paciente = consultar_uno("SELECT celular, primer_nombre FROM pacientes WHERE id=?", (paciente_id,))
        if paciente:
            paciente = dict(paciente)
            enviar_whatsapp(
                paciente.get("celular"),
                f"Hola {paciente.get('primer_nombre','')}, su médico acaba de registrar una nueva recomendación "
                "en su historia clínica. Escríbanos *menu* por este medio si desea más información.",
            )
    except Exception:
        pass  # un fallo al avisar por WhatsApp no debe impedir que la recomendacion quede guardada

    return _id


def listar_por_paciente(paciente_id: int):
    filas = consultar_todos(
        """
        SELECT r.*, pr.nombre_completo AS profesional
        FROM recomendaciones_medicas r
        LEFT JOIN profesionales pr ON pr.id = r.profesional_id
        WHERE r.paciente_id=?
        ORDER BY r.fecha_creacion DESC
        """,
        (paciente_id,),
    )
    return [dict(f) for f in filas]


def ultimo_por_paciente(paciente_id: int):
    fila = consultar_uno(
        """
        SELECT r.*, pr.nombre_completo AS profesional
        FROM recomendaciones_medicas r
        LEFT JOIN profesionales pr ON pr.id = r.profesional_id
        WHERE r.paciente_id=?
        ORDER BY r.fecha_creacion DESC LIMIT 1
        """,
        (paciente_id,),
    )
    return dict(fila) if fila else None
