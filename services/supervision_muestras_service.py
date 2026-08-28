"""
HomeCare Enterprise - Lista de Supervisión: Toma de Muestras

Versión digital de la lista de chequeo en papel que usa el
equipo de calidad para auditar, en el sitio, cómo un auxiliar
realiza la toma de muestras -- mismos 3 bloques y 23 puntos
exactos del formato original, para no perder ni cambiar nada
de lo que ya se venía verificando, solo pasarlo a digital con
historial y porcentaje de cumplimiento calculado solo.
"""

from database.database import consultar_todos, consultar_uno, ejecutar

RESPUESTAS_VALIDAS = ("Cumple", "No cumple", "N/A")

# Mismos 3 bloques y 23 puntos EXACTOS del documento original en
# papel -- el "codigo_item" es estable (no cambia aunque se
# retoque el texto más adelante), para que las respuestas ya
# guardadas de supervisiones anteriores no se desalineen si el
# texto de un punto se ajusta con el tiempo.
SECCIONES_CHECKLIST = [
    {
        "seccion": "Identificación del paciente",
        "items": [
            ("id_1", "Solicita al paciente y/o acudiente que indique su nombre completo (identificación activa, no inducida)."),
            ("id_2", "Solicita documento de identidad."),
            ("id_3", "Verifica coincidencia entre el nombre referido por el paciente y la solicitud de examen."),
            ("id_4", "Confirma identidad con un segundo identificador (fecha de nacimiento, historia clínica, etc.)."),
            ("id_5", "En caso de paciente inconsciente, menor de edad o con barrera de comunicación, verifica identidad con acompañante."),
        ],
    },
    {
        "seccion": "Verificación de datos demográficos",
        "items": [
            ("demo_1", "Confirma sexo del paciente."),
            ("demo_2", "Confirma procedencia (servicio, EPS/asegurador, ubicación)."),
            ("demo_3", "Los datos demográficos registrados en el rótulo/etiqueta coinciden con la orden médica y el sistema."),
        ],
    },
    {
        "seccion": "Supervisión de la toma de muestras",
        "items": [
            ("tec_1", "Realiza higiene de manos antes del procedimiento."),
            ("tec_2", "Utiliza los elementos de protección personal adecuados (guantes, tapabocas, etc.)."),
            ("tec_3", "Verifica fecha de vencimiento e integridad de los tubos, agujas y demás insumos."),
            ("tec_4", "Selecciona el tubo/recipiente correcto según el examen solicitado."),
            ("tec_5", "Realiza antisepsia adecuada del sitio de punción."),
            ("tec_6", "Aplica técnica correcta de punción venosa/capilar según protocolo institucional."),
            ("tec_7", "Rotula los tubos inmediatamente después de la toma, en presencia del paciente."),
            ("tec_8", "El rótulo incluye nombre completo, documento de identidad, fecha, hora y tipo de muestra."),
            ("tec_9", "Respeta el orden de llenado de tubos (orden de extracción) cuando aplica."),
            ("tec_10", "Homogeniza las muestras según corresponda (inversión suave, número de veces indicado)."),
            ("tec_11", "Realiza descarte adecuado de elementos cortopunzantes en guardián."),
            ("tec_12", "Aplica presión/apósito en el sitio de punción y verifica ausencia de sangrado."),
            ("tec_13", "Registra el procedimiento en el sistema de información / planilla correspondiente."),
            ("tec_14", "Transporta y almacena la muestra en condiciones adecuadas (temperatura, tiempo, protección de la luz, etc.)."),
            ("tec_15", "Trata al paciente con respeto, amabilidad y privacidad durante todo el procedimiento."),
        ],
    },
]

_TEXTOS_POR_CODIGO = {codigo: texto for bloque in SECCIONES_CHECKLIST for codigo, texto in bloque["items"]}


def crear_supervision(datos: dict, respuestas: dict, usuario_id=None) -> int:
    """
    respuestas: {codigo_item: {"respuesta": "Cumple"/"No cumple"/"N/A", "observaciones": "..."}}
    El porcentaje de cumplimiento se calcula solo, sobre los
    puntos marcados Cumple o No cumple (los N/A no cuentan ni a
    favor ni en contra, porque simplemente no aplicaron ese día).
    """
    if not datos.get("fecha"):
        raise ValueError("Debe indicar la fecha de la supervisión.")
    if not datos.get("punto_toma"):
        raise ValueError("Debe indicar la dirección / IPS / punto de toma.")
    if not datos.get("auxiliar_supervisado_nombre"):
        raise ValueError("Debe indicar el nombre del auxiliar que toma las muestras.")

    total_aplicables = 0
    total_cumple = 0
    for codigo in _TEXTOS_POR_CODIGO:
        resp = (respuestas.get(codigo) or {}).get("respuesta", "N/A")
        if resp not in RESPUESTAS_VALIDAS:
            resp = "N/A"
        if resp in ("Cumple", "No cumple"):
            total_aplicables += 1
            if resp == "Cumple":
                total_cumple += 1
    porcentaje = round((total_cumple / total_aplicables) * 100, 1) if total_aplicables else None

    supervision_id = ejecutar(
        """
        INSERT INTO supervision_muestras(
            fecha, punto_toma, auxiliar_supervisado_id, auxiliar_supervisado_nombre,
            responsable_auditoria_id, cargo_responsable, hora_inicio, hora_fin, muestra_id,
            porcentaje_cumplimiento, observaciones_generales, usuario_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos["fecha"], datos["punto_toma"], datos.get("auxiliar_supervisado_id") or None,
            datos["auxiliar_supervisado_nombre"], datos.get("responsable_auditoria_id") or None,
            datos.get("cargo_responsable"), datos.get("hora_inicio"), datos.get("hora_fin"),
            datos.get("muestra_id") or None, porcentaje, datos.get("observaciones_generales"), usuario_id,
        ),
    )

    for bloque in SECCIONES_CHECKLIST:
        for codigo, _texto in bloque["items"]:
            item_respuesta = respuestas.get(codigo) or {}
            resp = item_respuesta.get("respuesta", "N/A")
            if resp not in RESPUESTAS_VALIDAS:
                resp = "N/A"
            ejecutar(
                "INSERT INTO supervision_muestras_items(supervision_id, seccion, codigo_item, respuesta, observaciones) VALUES (?, ?, ?, ?, ?)",
                (supervision_id, bloque["seccion"], codigo, resp, item_respuesta.get("observaciones") or None),
            )

    return supervision_id


def listar_supervisiones():
    return [dict(f) for f in consultar_todos(
        """
        SELECT s.*, pa.primer_nombre AS aux_nombre_real, pa.primer_apellido AS aux_apellido_real,
               pr.primer_nombre AS resp_nombre, pr.primer_apellido AS resp_apellido
        FROM supervision_muestras s
        LEFT JOIN profesionales pa ON pa.id = s.auxiliar_supervisado_id
        LEFT JOIN profesionales pr ON pr.id = s.responsable_auditoria_id
        ORDER BY s.fecha DESC, s.id DESC
        """
    )]


def obtener_supervision(supervision_id: int):
    fila = consultar_uno(
        """
        SELECT s.*, pa.primer_nombre AS aux_nombre_real, pa.primer_apellido AS aux_apellido_real,
               pr.primer_nombre AS resp_nombre, pr.primer_apellido AS resp_apellido
        FROM supervision_muestras s
        LEFT JOIN profesionales pa ON pa.id = s.auxiliar_supervisado_id
        LEFT JOIN profesionales pr ON pr.id = s.responsable_auditoria_id
        WHERE s.id=?
        """,
        (supervision_id,),
    )
    if not fila:
        return None
    supervision = dict(fila)

    items_guardados = {
        dict(f)["codigo_item"]: dict(f)
        for f in consultar_todos("SELECT * FROM supervision_muestras_items WHERE supervision_id=?", (supervision_id,))
    }

    secciones_con_respuestas = []
    for bloque in SECCIONES_CHECKLIST:
        items = []
        for codigo, texto in bloque["items"]:
            guardado = items_guardados.get(codigo, {})
            items.append({
                "codigo": codigo, "texto": texto,
                "respuesta": guardado.get("respuesta", "N/A"),
                "observaciones": guardado.get("observaciones", ""),
            })
        secciones_con_respuestas.append({"seccion": bloque["seccion"], "items": items})

    supervision["secciones"] = secciones_con_respuestas
    return supervision


def promedio_cumplimiento_general():
    fila = consultar_uno("SELECT AVG(porcentaje_cumplimiento) AS promedio FROM supervision_muestras WHERE porcentaje_cumplimiento IS NOT NULL")
    valor = dict(fila)["promedio"] if fila else None
    return round(valor, 1) if valor is not None else None
