"""HomeCare Enterprise - Administración del Flujo del Chatbot de WhatsApp"""

from database.database import consultar_todos, consultar_uno, ejecutar

TIPOS_ACCION = [
    ("respuesta_automatica", "Responder automáticamente (puede usar datos del paciente)"),
    ("submenu", "Abrir un submenú con más opciones"),
    ("recoleccion_datos", "Pedirle datos al paciente (nombre, documento, etc.) y derivar a un departamento"),
    ("derivar_departamento", "Derivar directamente a un agente humano de un departamento"),
]

MARCADORES_DISPONIBLES = [
    ("{nombre_formal}", "Nombre del paciente en formato formal (Sr.(a) Nombre Apellido)"),
    ("{proxima_visita}", "Próxima visita programada del paciente"),
    ("{ultima_orden}", "Última orden médica del paciente"),
    ("{ultimas_recomendaciones}", "Últimas recomendaciones médicas del paciente"),
]


def arbol_completo():
    """Todas las opciones, organizadas como árbol (raíz + hijos anidados), para mostrar en la pantalla de administración."""
    todas = [dict(f) for f in consultar_todos("SELECT * FROM whatsapp_flujo_opciones ORDER BY padre_id, orden")]
    por_padre = {}
    for opcion in todas:
        por_padre.setdefault(opcion["padre_id"], []).append(opcion)

    def construir(padre_id):
        hijos = por_padre.get(padre_id, [])
        for hijo in hijos:
            hijo["hijos"] = construir(hijo["id"])
        return hijos

    return construir(None)


def opciones_planas_para_padre():
    """Lista simple de todas las opciones (para el desplegable de 'a cuál pertenece'), con su ruta completa."""
    todas = [dict(f) for f in consultar_todos("SELECT * FROM whatsapp_flujo_opciones WHERE activo=1 ORDER BY padre_id, orden")]
    por_id = {o["id"]: o for o in todas}

    def ruta(opcion):
        if opcion["padre_id"] and opcion["padre_id"] in por_id:
            return ruta(por_id[opcion["padre_id"]]) + " → " + opcion["texto_boton"]
        return opcion["texto_boton"]

    return [{"id": o["id"], "ruta": ruta(o)} for o in todas]


def crear_opcion(padre_id, texto_boton, tipo_accion, contenido_respuesta, departamento, orden, campos_solicitados=None) -> int:
    if not texto_boton or not texto_boton.strip():
        raise ValueError("Debe indicar el texto del botón/opción.")
    if tipo_accion not in dict(TIPOS_ACCION):
        raise ValueError("Tipo de acción no válido.")
    if tipo_accion == "derivar_departamento" and not departamento:
        raise ValueError("Debe indicar a qué departamento se deriva.")
    if tipo_accion == "recoleccion_datos" and not (departamento and campos_solicitados):
        raise ValueError("Para recolección de datos debe indicar el departamento y los campos a solicitar.")

    return ejecutar(
        "INSERT INTO whatsapp_flujo_opciones(padre_id, orden, texto_boton, tipo_accion, contenido_respuesta, departamento, campos_solicitados) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (padre_id or None, orden or 0, texto_boton.strip(), tipo_accion, contenido_respuesta or None, departamento or None, campos_solicitados or None),
    )


def actualizar_opcion(opcion_id, texto_boton, tipo_accion, contenido_respuesta, departamento, orden, campos_solicitados=None):
    if not texto_boton or not texto_boton.strip():
        raise ValueError("Debe indicar el texto del botón/opción.")
    if tipo_accion == "derivar_departamento" and not departamento:
        raise ValueError("Debe indicar a qué departamento se deriva.")
    if tipo_accion == "recoleccion_datos" and not (departamento and campos_solicitados):
        raise ValueError("Para recolección de datos debe indicar el departamento y los campos a solicitar.")

    ejecutar(
        "UPDATE whatsapp_flujo_opciones SET texto_boton=?, tipo_accion=?, contenido_respuesta=?, departamento=?, orden=?, campos_solicitados=? WHERE id=?",
        (texto_boton.strip(), tipo_accion, contenido_respuesta or None, departamento or None, orden or 0, campos_solicitados or None, opcion_id),
    )


def eliminar_opcion(opcion_id):
    # Al borrar una opcion, tambien se borran sus hijas (si era un submenu) -- para no dejar opciones huerfanas.
    hijas = consultar_todos("SELECT id FROM whatsapp_flujo_opciones WHERE padre_id=?", (opcion_id,))
    for hija in hijas:
        eliminar_opcion(dict(hija)["id"])
    ejecutar("DELETE FROM whatsapp_flujo_opciones WHERE id=?", (opcion_id,))


def desactivar_opcion(opcion_id):
    ejecutar("UPDATE whatsapp_flujo_opciones SET activo=0 WHERE id=?", (opcion_id,))


def diagrama_mermaid():
    """
    Arma la definición del flujo completo en formato Mermaid
    (una librería que dibuja diagramas de flujo interactivos en
    el navegador), para poder VER de un vistazo cómo corre el
    bot: qué responde cada opción, y a dónde sigue después de
    que el paciente elige un número.
    """
    todas = [dict(f) for f in consultar_todos("SELECT * FROM whatsapp_flujo_opciones ORDER BY padre_id, orden")]

    lineas = ["flowchart TD"]
    lineas.append('    inicio(["👋 Bienvenida + Nota Legal"])')

    detalles = {"inicio": {"titulo": "Mensaje de bienvenida", "tipo": "Inicio", "texto": "Se envía una sola vez, la primera vez que el paciente escribe."}}

    raiz = [o for o in todas if o["padre_id"] is None]
    for opcion in raiz:
        nodo_id = f"op{opcion['id']}"
        lineas.append(f'    inicio --> {nodo_id}')
        _agregar_nodo_mermaid(lineas, detalles, opcion, todas)

    lineas.append("")
    lineas.append('    classDef submenu fill:#dbeafe,stroke:#2563eb,color:#1e3a8a;')
    lineas.append('    classDef respuesta fill:#e5fbf9,stroke:#0a8f86,color:#0a8f86;')
    lineas.append('    classDef recoleccion fill:#fff7e0,stroke:#dd9d00,color:#7a5600;')
    lineas.append('    classDef derivar fill:#ffe3f2,stroke:#c2185b,color:#7a0e3d;')
    lineas.append('    classDef inicio fill:#0a8f86,stroke:#0a8f86,color:#fff;')
    lineas.append('    class inicio inicio;')

    for opcion in todas:
        nodo_id = f"op{opcion['id']}"
        clase = {"submenu": "submenu", "respuesta_automatica": "respuesta", "recoleccion_datos": "recoleccion", "derivar_departamento": "derivar"}.get(opcion["tipo_accion"], "respuesta")
        lineas.append(f'    class {nodo_id} {clase};')

    return {"definicion": "\n".join(lineas), "detalles": detalles}


def _agregar_nodo_mermaid(lineas, detalles, opcion, todas):
    nodo_id = f"op{opcion['id']}"

    def texto_seguro(texto, largo=28):
        texto = (texto or "").replace('"', "'").replace("\n", " ").replace("{", "(").replace("}", ")")
        return (texto[:largo] + "…") if len(texto) > largo else texto

    etiqueta = texto_seguro(f"{opcion['orden']}. {opcion['texto_boton']}")

    if opcion["tipo_accion"] == "submenu":
        lineas.append(f'    {nodo_id}{{{{"{etiqueta}"}}}}')
    elif opcion["tipo_accion"] == "derivar_departamento":
        lineas.append(f'    {nodo_id}[/"{etiqueta}<br/>→ {texto_seguro(opcion.get("departamento") or "", 20)}"/]')
    elif opcion["tipo_accion"] == "recoleccion_datos":
        lineas.append(f'    {nodo_id}[["{etiqueta}<br/>📋 pide datos"]]')
    else:
        lineas.append(f'    {nodo_id}("{etiqueta}")')

    detalles[nodo_id] = {
        "titulo": opcion["texto_boton"],
        "tipo": {
            "submenu": "Abre un submenú",
            "respuesta_automatica": "Responde automáticamente",
            "recoleccion_datos": "Pide datos y deriva a un departamento",
            "derivar_departamento": "Deriva directamente a un agente humano",
        }.get(opcion["tipo_accion"], opcion["tipo_accion"]),
        "texto": opcion.get("contenido_respuesta") or "",
        "departamento": opcion.get("departamento") or "",
        "campos": opcion.get("campos_solicitados") or "",
    }

    hijas = [o for o in todas if o["padre_id"] == opcion["id"]]
    for hija in hijas:
        hijo_id = f"op{hija['id']}"
        lineas.append(f'    {nodo_id} --> {hijo_id}')
        _agregar_nodo_mermaid(lineas, detalles, hija, todas)


def activar_opcion(opcion_id):
    ejecutar("UPDATE whatsapp_flujo_opciones SET activo=1 WHERE id=?", (opcion_id,))


def restaurar_plantilla_homecare(usuario_id=None):
    """
    Borra el árbol de opciones actual y lo reemplaza por la
    plantilla profesional de HomeCare del Quindío: selección de
    ciudad -> menú de servicios -> submenús -> recolección de
    datos -> derivación al departamento correspondiente. Úsela
    cuando quiera empezar de cero con una base ya armada, y
    luego ajústela a su gusto.
    """
    ejecutar("DELETE FROM whatsapp_flujo_opciones")

    # Se asegura que exista la fila de configuración antes de
    # actualizarla -- si nunca se había guardado nada desde la
    # pantalla de Configuración Chatbot, un UPDATE por sí solo
    # no crea la fila, y los mensajes personalizados no
    # quedarían aplicados.
    if not consultar_uno("SELECT id FROM configuracion_whatsapp WHERE id=1"):
        ejecutar("INSERT INTO configuracion_whatsapp(id) VALUES (1)")

    ejecutar(
        "UPDATE configuracion_whatsapp SET "
        "mensaje_bienvenida=?, mensaje_despedida=? WHERE id=1",
        (
            "IPS HOMECARE DEL QUINDÍO.\n\n"
            "💙 Nos alegra atenderte. Tu bienestar y el de tu familia son nuestra prioridad.\n\n"
            "Estoy aquí para ayudarte de forma rápida y sencilla con información sobre nuestros servicios, "
            "programación de citas, autorizaciones, atención domiciliaria y cualquier inquietud que tengas.\n\n"
            "✨ Gracias por confiar en nosotros. Trabajamos cada día para brindarte una atención humana, "
            "oportuna y de calidad.\n\n"
            "📝 Nota legal: Al interactuar con este canal, aceptas los términos de nuestra Política de "
            "Tratamiento de Datos Personales y nos autorizas a utilizarlos para gestionar tu solicitud.",

            "✨ Gracias por confiar en HomeCare del Quindío I.P.S. Estamos comprometidos con brindarte "
            "una atención oportuna y de calidad.",
        ),
    )

    # Nivel 0: selección de ciudad
    ciudades = ["Armenia", "Calarcá", "La Tebaida", "Montenegro"]
    ids_ciudad = []
    for orden, ciudad in enumerate(ciudades, start=1):
        id_ciudad = crear_opcion(None, ciudad, "submenu", None, None, orden)
        ids_ciudad.append(id_ciudad)

    # Nivel 1: menú de servicios (igual bajo cada ciudad)
    servicios = [
        (1, "🩺 Procedimientos", "recoleccion_datos", "Procedimientos",
         "Nombre completo del paciente\nNúmero de documento de identidad\nNúmero de contacto\nProcedimiento que requiere"),
        (2, "📁 Solicitudes", "submenu", None, None),
        (3, "🏥 Consultas Esp. y Terapias", "recoleccion_datos", "Consultas y Terapias",
         "Nombre completo del paciente\nNúmero de documento de identidad\nNúmero de contacto\nEspecialidad o terapia que requiere"),
        (4, "💳 Pagos", "recoleccion_datos", "Pagos y Cartera",
         "Nombre completo del paciente\nNúmero de documento de identidad\nNúmero de contacto\nConcepto del pago"),
        (5, "📝 Actualización de Datos", "recoleccion_datos", "Actualización de Datos",
         "Nombre completo del paciente\nNúmero de documento de identidad\nDato que desea actualizar y nuevo valor"),
        (6, "ℹ️ PQR", "recoleccion_datos", "PQR",
         "Nombre completo\nNúmero de documento de identidad\nNúmero de contacto\nDescripción de su petición, queja o reclamo"),
    ]

    for id_ciudad in ids_ciudad:
        ids_servicio = {}
        for orden, texto, tipo, depto, campos in servicios:
            id_servicio = crear_opcion(id_ciudad, texto, tipo, None, depto, orden, campos)
            ids_servicio[orden] = id_servicio

        # Nivel 2: submenú de "Solicitudes"
        solicitudes = [
            (1, "🗓️ Asignación de servicios", "Asignación de Servicios",
             "Nombre completo del paciente\nNúmero de documento de identidad\nNúmero de contacto\nServicio que requiere"),
            (2, "📋 Historias Clínicas", "Historias Clínicas",
             "Nombre completo del paciente\nNúmero de documento de identidad\nNúmero de contacto\nMotivo de la solicitud"),
            (3, "📝 Órdenes Médicas", "Órdenes Médicas",
             "Nombre completo del paciente\nNúmero de documento de identidad\nNúmero de contacto\nServicio o especialidad para la cual requiere la orden médica"),
        ]
        for orden, texto, depto, campos in solicitudes:
            crear_opcion(ids_servicio[2], texto, "recoleccion_datos", None, depto, orden, campos)
