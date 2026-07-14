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


def construir_flujo_personalizado_homecare(usuario_id=None):
    """
    Arma el árbol de conversación EXACTO que se definió mensaje
    a mensaje con la IPS: bienvenida -> menú de 6 servicios ->
    submenús de Procedimientos y Terapias con las 4 opciones de
    cita (Consultar/Programar/Reprogramar/Cancelar) -> Solicitudes
    con sus 3 sub-secciones -> Pagos -> Actualización de Datos ->
    PQR. Reemplaza el árbol anterior por completo.

    Los textos marcados como "(texto de referencia, ajustar si
    se desea)" son los que no se definieron con una redacción
    exacta durante la conversación -- se armaron siguiendo el
    mismo estilo que sí se definió (como el de Órdenes Médicas),
    para que quede algo funcional desde ya, pero se pueden
    editar en cualquier momento desde el editor del flujo.
    """
    ejecutar("DELETE FROM whatsapp_flujo_opciones")

    if not consultar_uno("SELECT id FROM configuracion_whatsapp WHERE id=1"):
        ejecutar("INSERT INTO configuracion_whatsapp(id) VALUES (1)")

    ejecutar(
        "UPDATE configuracion_whatsapp SET mensaje_bienvenida=?, mensaje_despedida=? WHERE id=1",
        (
            "👋 ¡Hola! Bienvenido(a) a *HomeCare del Quindío I.P.S.*\n\n"
            "Es un gusto saludarte. Somos un equipo comprometido con brindarte a ti y a tu familia una atención "
            "domiciliaria cálida, oportuna y de la más alta calidad — como si estuviéramos ahí contigo, en tu "
            "propio hogar. 💙\n\n"
            "Este es nuestro canal de atención por WhatsApp. Aquí podrás consultar información sobre tus "
            "servicios, solicitar citas, resolver dudas y mucho más, de forma rápida y sencilla.\n\n"
            "📝 *Nota:* al continuar la conversación, aceptas nuestra Política de Tratamiento de Datos "
            "Personales, la cual usamos únicamente para gestionar tu solicitud de la mejor manera.\n\n"
            "¡Gracias por confiar en nosotros! Estamos aquí para ayudarte. ✨",

            "✨ Gracias por confiar en HomeCare del Quindío I.P.S. Estamos comprometidos con brindarte "
            "una atención oportuna y de calidad.",
        ),
    )

    TEXTO_CITA = (
        "Para ayudarte con la consulta de tu cita, por favor envíanos la siguiente información:\n"
        "👤 Nombre completo del paciente:\n"
        "🆔 Número de documento:\n"
        "📱 Número de contacto:\n"
        "📅 Fecha de la visita:\n\n"
        "Una vez recibamos la información, nuestro equipo verificará y te contactará para confirmar la fecha "
        "y hora de atención.\n\n"
        "⏳ Tu solicitud será gestionada en el menor tiempo posible. Gracias por confiar en IPS HOMECARE DEL QUINDÍO."
    )
    CAMPOS_CITA = "Nombre completo del paciente\nNúmero de documento\nNúmero de contacto\nFecha de la visita"

    def submenu_de_citas(id_padre, departamento):
        opciones = [
            (1, "🔍 Consultar visita programada"),
            (2, "📅 Programar visita"),
            (3, "🔄 Reprogramar visita"),
            (4, "❌ Cancelar visita"),
        ]
        for orden, texto in opciones:
            crear_opcion(id_padre, texto, "recoleccion_datos", TEXTO_CITA, departamento, orden, CAMPOS_CITA)

    # ---------------- Menú principal ----------------
    id_procedimientos = crear_opcion(None, "🩺 Procedimientos", "submenu", None, None, 1)
    id_solicitudes = crear_opcion(None, "📂 Solicitudes", "submenu", None, None, 2)
    id_terapias = crear_opcion(None, "🏥 Consultas Esp. y Terapias", "submenu", None, None, 3)
    id_pagos = crear_opcion(None, "💳 Pagos", "submenu", None, None, 4)

    crear_opcion(
        None, "📝 Actualización de Datos", "recoleccion_datos",
        None, "Asistencial General", 5,
        "Nombre completo\nNúmero de cédula\nDato(s) que deseas actualizar (dirección, teléfono, EPS, etc.)",
    )

    texto_pqr = (
        "Gracias por tomarse el tiempo de compartir sus comentarios, sugerencias o inquietudes. Cada mensaje "
        "nos ayuda a mejorar la calidad de nuestros servicios y fortalecer la atención que brindamos a nuestros "
        "pacientes.\n"
        "Por favor, comparte la siguiente información para atender tu consulta:\n"
        "👤 Nombre completo:\n"
        "🆔 Número de documento:\n"
        "📱 Número de contacto:\n"
        "📝 Describe tu consulta o solicitud:\n\n"
        "📌 Nuestro equipo revisará la información y te brindará una respuesta en el menor tiempo posible.\n"
        "💙 Gracias por confiar en IPS HOMECARE DEL QUINDÍO. Será un gusto ayudarte."
    )
    crear_opcion(
        None, "ℹ️ PQR", "recoleccion_datos", texto_pqr, "Asistencial General", 6,
        "Nombre completo\nNúmero de documento\nNúmero de contacto\nDescripción de la consulta o solicitud",
    )

    # ---------------- 1. Procedimientos ----------------
    id_curaciones = crear_opcion(id_procedimientos, "🩹 Curaciones", "submenu", None, None, 1)
    id_medicamentos = crear_opcion(id_procedimientos, "💉 Aplicación de medicamentos", "submenu", None, None, 2)
    id_muestras = crear_opcion(id_procedimientos, "🧪 Toma de muestras", "submenu", None, None, 3)
    for id_padre in (id_curaciones, id_medicamentos, id_muestras):
        submenu_de_citas(id_padre, "Procedimientos")

    # ---------------- 3. Consultas Esp. y Terapias ----------------
    id_terapia_fisica = crear_opcion(id_terapias, "🏃 Terapias", "submenu", None, None, 1)
    id_nutricion = crear_opcion(id_terapias, "🥗 Nutrición", "submenu", None, None, 2)
    id_psicologia = crear_opcion(id_terapias, "🧠 Psicología", "submenu", None, None, 3)
    id_trabajo_social = crear_opcion(id_terapias, "🤝 Trabajo social", "submenu", None, None, 4)
    for id_padre in (id_terapia_fisica, id_nutricion, id_psicologia, id_trabajo_social):
        submenu_de_citas(id_padre, "Terapias y Especialistas")

    # ---------------- 2. Solicitudes ----------------
    id_asignacion = crear_opcion(id_solicitudes, "📅 Asignación de servicios", "submenu", None, None, 1)
    id_historias = crear_opcion(id_solicitudes, "📄 Historias Clínicas", "submenu", None, None, 2)

    # (texto de referencia, ajustar si se desea -- no se definió una redacción exacta para estas 4)
    texto_solicitud_servicio = (
        "Gracias por comunicarse con HomeCare del Quindío. 💙 Con gusto le ayudaremos a gestionar su solicitud.\n\n"
        "Para continuar, por favor compártanos la siguiente información:\n"
        "👤 Nombre completo del paciente\n"
        "🪪 Número de documento de identidad\n"
        "📱 Número de contacto\n"
        "🏥 Servicio que requiere\n\n"
        "Una vez recibamos la información, nuestro equipo realizará la validación correspondiente y gestionará "
        "su solicitud en el menor tiempo posible.\n\n"
        "✨ Gracias por confiar en nosotros. Estamos comprometidos con brindarle una atención oportuna y de calidad."
    )
    campos_solicitud_servicio = "Nombre completo del paciente\nNúmero de documento de identidad\nNúmero de contacto\nServicio que requiere"
    crear_opcion(id_asignacion, "📥 Realizar solicitud de servicio", "recoleccion_datos", texto_solicitud_servicio, "Asistencial General", 1, campos_solicitud_servicio)

    texto_consultar_estado = (
        "Gracias por comunicarse con HomeCare del Quindío. 💙\n\n"
        "Para consultar el estado de su solicitud, por favor compártanos:\n"
        "👤 Nombre completo del paciente\n"
        "🪪 Número de documento de identidad\n"
        "📱 Número de contacto\n\n"
        "Nuestro equipo revisará el estado de su solicitud y le responderá en el menor tiempo posible."
    )
    campos_consultar_estado = "Nombre completo del paciente\nNúmero de documento de identidad\nNúmero de contacto"
    crear_opcion(id_asignacion, "🔍 Consultar estado de una solicitud existente", "recoleccion_datos", texto_consultar_estado, "Asistencial General", 2, campos_consultar_estado)
    crear_opcion(id_historias, "🔍 Consultar el estado de una solicitud realizada", "recoleccion_datos", texto_consultar_estado, "Asistencial General", 1, campos_consultar_estado)

    texto_historia_clinica = (
        "Gracias por comunicarse con HomeCare del Quindío. 💙\n\n"
        "Para tramitar la solicitud de la historia clínica, por favor compártanos:\n"
        "👤 Nombre completo del paciente\n"
        "🪪 Número de documento de identidad\n"
        "📱 Número de contacto\n\n"
        "Una vez recibamos la información, nuestro equipo realizará la validación correspondiente y gestionará "
        "su solicitud en el menor tiempo posible."
    )
    campos_historia_clinica = "Nombre completo del paciente\nNúmero de documento de identidad\nNúmero de contacto"
    crear_opcion(id_historias, "📥 Solicitar historia clínica", "recoleccion_datos", texto_historia_clinica, "Asistencial General", 2, campos_historia_clinica)

    texto_orden_medica = (
        "Gracias por comunicarse con HomeCare del Quindío. 💙 Con gusto le ayudaremos a gestionar su solicitud. "
        "Para continuar, por favor compártanos la siguiente información: "
        "👤 Nombre completo del paciente "
        "🪪 Número de documento de identidad "
        "📱 Número de contacto "
        "🏥 Servicio o especialidad para la cual requiere la orden médica "
        "Una vez recibamos la información, nuestro equipo realizará la validación correspondiente y gestionará "
        "su solicitud en el menor tiempo posible. "
        "✨ Gracias por confiar en nosotros. Estamos comprometidos con brindarle una atención oportuna y de calidad."
    )
    campos_orden_medica = "Nombre completo del paciente\nNúmero de documento de identidad\nNúmero de contacto\nServicio o especialidad para la cual requiere la orden médica"
    crear_opcion(id_solicitudes, "📋 Órdenes Médicas", "recoleccion_datos", texto_orden_medica, "Asistencial General", 3, campos_orden_medica)

    # ---------------- 4. Pagos ----------------
    # (texto de referencia, ajustar si se desea -- no se definió una redacción exacta para estas 2)
    for orden, texto_boton, nombre_banco in ((1, "NEQUI", "Nequi"), (2, "DAVIVIENDA", "Daviviendo")):
        texto_pago = (
            f"Gracias por comunicarte con HomeCare del Quindío. 💙\n\n"
            f"Para procesar tu pago por {nombre_banco}, por favor compártenos:\n"
            "👤 Nombre completo del paciente\n"
            "🪪 Número de documento\n"
            "💳 Comprobante o soporte de la transacción (puedes enviarlo como foto)\n"
            "📝 Concepto del pago\n\n"
            "Nuestro equipo de facturación confirmará tu pago en el menor tiempo posible."
        )
        campos_pago = "Nombre completo del paciente\nNúmero de documento\nConcepto del pago"
        crear_opcion(id_pagos, texto_boton, "recoleccion_datos", texto_pago, "Asistencial General", orden, campos_pago)


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
