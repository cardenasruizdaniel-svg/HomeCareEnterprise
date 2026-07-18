"""
HomeCare Enterprise - Resultados de Laboratorio Clínico

Registra los examenes de laboratorio que se le mandan al
paciente: cual examen, que laboratorio lo realizo, el
resultado, y una foto del resultado como constancia. Se puede
diligenciar desde la oficina, o desde la app de campo cuando
un profesional de la salud visita al paciente. Cada resultado
queda tambien reflejado en la Historia Clínica.
"""

from database.database import consultar_todos, consultar_uno, ejecutar


def listar_por_paciente(paciente_id: int):
    filas = consultar_todos(
        """
        SELECT lr.*, pr.nombre_completo AS profesional
        FROM laboratorios_resultados lr
        LEFT JOIN profesionales pr ON pr.id = lr.profesional_id
        WHERE lr.paciente_id=?
        ORDER BY lr.fecha_resultado DESC, lr.id DESC
        """,
        (paciente_id,),
    )
    resultados = [dict(f) for f in filas]
    for r in resultados:
        r["items"] = listar_items(r["id"])
    return resultados


def obtener(resultado_id: int):
    fila = consultar_uno(
        """
        SELECT lr.*, pr.nombre_completo AS profesional
        FROM laboratorios_resultados lr
        LEFT JOIN profesionales pr ON pr.id = lr.profesional_id
        WHERE lr.id=?
        """,
        (resultado_id,),
    )
    if not fila:
        return None
    resultado = dict(fila)
    resultado["items"] = listar_items(resultado_id)
    return resultado


def registrar_resultado(paciente_id, nombre_examen, laboratorio_realizo, fecha_orden, fecha_resultado,
                          resultado_texto, foto_resultado_base64, profesional_id, origen, usuario_id,
                          items=None) -> int:

    if not paciente_id or not nombre_examen:
        raise ValueError("Debe indicar el paciente y el nombre del examen.")

    resultado_id = ejecutar(
        """
        INSERT INTO laboratorios_resultados(
            paciente_id, nombre_examen, laboratorio_realizo, fecha_orden, fecha_resultado,
            resultado_texto, foto_resultado_base64, profesional_id, origen, usuario_registro
        ) VALUES (
            :paciente_id, :nombre_examen, :laboratorio_realizo, :fecha_orden, :fecha_resultado,
            :resultado_texto, :foto_resultado_base64, :profesional_id, :origen, :usuario_registro
        )
        """,
        {
            "paciente_id": paciente_id, "nombre_examen": nombre_examen,
            "laboratorio_realizo": laboratorio_realizo or "", "fecha_orden": fecha_orden or None,
            "fecha_resultado": fecha_resultado or None, "resultado_texto": resultado_texto or "",
            "foto_resultado_base64": foto_resultado_base64 or None, "profesional_id": profesional_id or None,
            "origen": origen or "WEB", "usuario_registro": usuario_id,
        },
    )

    for item in (items or []):
        if item.get("nombre_parametro"):
            agregar_item(
                resultado_id, item["nombre_parametro"], item.get("valor_obtenido", ""),
                item.get("unidad", ""), item.get("rango_min"), item.get("rango_max"),
            )

    return resultado_id


def _interpretar(valor_numerico, rango_min, rango_max):
    """
    Compara el valor obtenido contra el rango normal y dice si
    quedo Bajo, Alto, o Normal. Si el valor no es numerico (ej.
    "Positivo"/"Negativo") o no se indico un rango, no se
    interpreta -- queda en blanco, para que el profesional lo
    lea directamente en observaciones.
    """
    if valor_numerico is None or rango_min is None or rango_max is None:
        return None
    if valor_numerico < rango_min:
        return "Bajo"
    if valor_numerico > rango_max:
        return "Alto"
    return "Normal"


def agregar_item(resultado_id, nombre_parametro, valor_obtenido, unidad, rango_min, rango_max) -> int:

    if not nombre_parametro:
        raise ValueError("Debe indicar el nombre del parámetro (ej. Glóbulos rojos).")

    valor_numerico = None
    if valor_obtenido not in (None, ""):
        try:
            valor_numerico = float(str(valor_obtenido).replace(",", "."))
        except ValueError:
            valor_numerico = None  # valores no numericos (ej. "Positivo") se guardan tal cual, sin interpretar

    rango_min_f = float(rango_min) if rango_min not in (None, "") else None
    rango_max_f = float(rango_max) if rango_max not in (None, "") else None

    interpretacion = _interpretar(valor_numerico, rango_min_f, rango_max_f)

    return ejecutar(
        """
        INSERT INTO laboratorio_items(
            resultado_id, nombre_parametro, valor_obtenido, valor_numerico, unidad,
            rango_min, rango_max, interpretacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (resultado_id, nombre_parametro, str(valor_obtenido or ""), valor_numerico, unidad or "",
         rango_min_f, rango_max_f, interpretacion),
    )


def listar_items(resultado_id: int):
    filas = consultar_todos(
        "SELECT * FROM laboratorio_items WHERE resultado_id=? ORDER BY id", (resultado_id,)
    )
    return [dict(f) for f in filas]


def eliminar_item(item_id: int):
    ejecutar("DELETE FROM laboratorio_items WHERE id=?", (item_id,))


def eliminar(resultado_id: int):
    ejecutar("DELETE FROM laboratorios_resultados WHERE id=?", (resultado_id,))
