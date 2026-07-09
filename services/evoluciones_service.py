"""
HomeCare Enterprise - Registro de evoluciones (nota de la visita)

Funcion compartida entre la web y la app movil para guardar
la nota clinica de una visita, usada tanto por cuidadores y
enfermeros como por profesionales de la salud.

Cada nota queda con:
- Un CONSECUTIVO propio del paciente (Informe N.° 1, 2, 3...),
  para que la historia clinica sea trazable.
- La FIRMA del profesional que la hizo, tomada de la que
  quedo guardada al crear su perfil (se copia/"snapshotea" en
  cada nota, para que quede fija tal como era en ese momento,
  aunque despues el profesional actualice su firma).
- Si es una NOTA ACLARATORIA (para corregir un informe
  anterior), el numero de consecutivo del informe que corrige.
"""

from database.database import consultar_escalar, consultar_uno, ejecutar


def _siguiente_consecutivo(paciente_id: int) -> int:
    maximo = consultar_escalar(
        "SELECT MAX(consecutivo) FROM evoluciones WHERE paciente_id=?",
        (paciente_id,),
    )
    return (maximo or 0) + 1


def registrar_evolucion(paciente_id, programacion_id, profesional_id, tipo_profesional, nota,
                          origen="WEB", latitud=None, longitud=None, usuario_id=None,
                          tipo_registro="INFORME", nota_aclaratoria_de=None) -> dict:

    if not nota or not nota.strip():
        raise ValueError("La nota de la visita no puede estar vacía.")

    if tipo_registro not in ("INFORME", "NOTA_ACLARATORIA"):
        raise ValueError("Tipo de registro no válido.")

    if tipo_registro == "NOTA_ACLARATORIA" and not nota_aclaratoria_de:
        raise ValueError("Debe indicar a qué informe corresponde la nota aclaratoria.")

    firma_profesional = None
    if profesional_id:
        fila_profesional = consultar_uno(
            "SELECT firma_base64 FROM profesionales WHERE id=?", (profesional_id,)
        )
        if fila_profesional:
            firma_profesional = dict(fila_profesional).get("firma_base64")

    consecutivo = _siguiente_consecutivo(paciente_id)

    ejecutar(
        """
        INSERT INTO evoluciones(
            paciente_id, programacion_id, profesional_id, tipo_profesional,
            nota, latitud, longitud, origen, usuario_creacion,
            consecutivo, tipo_registro, nota_aclaratoria_de, firma_profesional_base64
        ) VALUES (
            :paciente_id, :programacion_id, :profesional_id, :tipo_profesional,
            :nota, :latitud, :longitud, :origen, :usuario_creacion,
            :consecutivo, :tipo_registro, :nota_aclaratoria_de, :firma_profesional_base64
        )
        """,
        {
            "paciente_id": paciente_id,
            "programacion_id": programacion_id,
            "profesional_id": profesional_id,
            "tipo_profesional": tipo_profesional,
            "nota": nota,
            "latitud": latitud,
            "longitud": longitud,
            "origen": origen,
            "usuario_creacion": usuario_id,
            "consecutivo": consecutivo,
            "tipo_registro": tipo_registro,
            "nota_aclaratoria_de": nota_aclaratoria_de,
            "firma_profesional_base64": firma_profesional,
        },
    )

    return {"ok": True, "consecutivo": consecutivo}


def listar_informes_para_aclarar(paciente_id: int):
    """
    Lista los informes (no las notas aclaratorias) de un
    paciente, para elegir a cual se le va a hacer una nota
    aclaratoria.
    """
    from database.database import consultar_todos
    return [
        dict(f) for f in consultar_todos(
            """
            SELECT consecutivo, fecha, tipo_profesional, nota
            FROM evoluciones
            WHERE paciente_id=? AND tipo_registro='INFORME'
            ORDER BY consecutivo DESC
            """,
            (paciente_id,),
        )
    ]
