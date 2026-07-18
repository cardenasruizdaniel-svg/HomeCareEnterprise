"""
HomeCare Enterprise - Panel de Agente WhatsApp

Bandeja de entrada profesional para que el equipo Asistencial
atienda las conversaciones de WhatsApp en vivo, como un chat
de atención al cliente real -- con lista de conversaciones,
historial completo, y la posibilidad de "tomar" una
conversación (pausando el chatbot automático mientras un
humano la atiende) y devolverla al bot cuando termine.

También permite reenviar rápidamente la última orden médica o
recomendación del paciente, sin salir del chat.
"""

from database.database import consultar_todos, consultar_uno, ejecutar
from services.notificaciones_service import enviar_whatsapp, normalizar_celular


def _obtener_o_crear_hilo(numero_celular: str, paciente_id=None):
    numero_normalizado = normalizar_celular(numero_celular)
    hilo = consultar_uno("SELECT * FROM whatsapp_hilos WHERE numero_celular=?", (numero_normalizado,))
    if hilo:
        return dict(hilo)

    hilo_id = ejecutar(
        "INSERT INTO whatsapp_hilos(numero_celular, paciente_id) VALUES (?, ?)",
        (numero_normalizado, paciente_id),
    )
    return dict(consultar_uno("SELECT * FROM whatsapp_hilos WHERE id=?", (hilo_id,)))


def registrar_actividad_entrante(numero_celular: str, paciente_id, mensaje: str):
    """Se llama desde el webhook cada vez que llega un mensaje -- actualiza el hilo para la bandeja de entrada."""
    hilo = _obtener_o_crear_hilo(numero_celular, paciente_id)
    ejecutar(
        """
        UPDATE whatsapp_hilos
        SET ultimo_mensaje=?, ultima_actividad=CURRENT_TIMESTAMP, no_leidos=no_leidos+1,
            paciente_id=COALESCE(paciente_id, ?)
        WHERE id=?
        """,
        (mensaje, paciente_id, hilo["id"]),
    )
    return hilo


def esta_atendido_por_humano(numero_celular: str) -> bool:
    numero_normalizado = normalizar_celular(numero_celular)
    hilo = consultar_uno("SELECT atendido_por_humano FROM whatsapp_hilos WHERE numero_celular=?", (numero_normalizado,))
    return bool(dict(hilo)["atendido_por_humano"]) if hilo else False


ROLES_CON_DEPARTAMENTO_ASIGNADO = {
    "Asistencial Procedimientos": "Procedimientos",
    "Asistencial Terapias": "Terapias",
}


def listar_hilos_en_espera(rol_usuario=None):
    """
    Chats "en espera": los que TODAVÍA no ha aceptado ningún
    agente -- pueden estar siendo atendidos por el bot en ese
    momento, o ya haber terminado con el bot y estar esperando
    a que alguien los tome. Un agente puede aceptar o
    transferir cualquiera de estos, así el bot todavía no haya
    terminado la conversación.

    Se filtran por el departamento del rol del agente (si
    aplica) -- así cada quien solo ve lo que le corresponde.
    """
    filtro_departamento = ROLES_CON_DEPARTAMENTO_ASIGNADO.get(rol_usuario)

    sql = """
        SELECT wh.*, p.primer_nombre, p.primer_apellido, u.nombre AS agente_nombre
        FROM whatsapp_hilos wh
        LEFT JOIN pacientes p ON p.id = wh.paciente_id
        LEFT JOIN usuarios u ON u.id = wh.agente_asignado_id
        WHERE wh.agente_asignado_id IS NULL AND wh.estado != 'Cerrado'
    """
    parametros = []
    if filtro_departamento:
        sql += " AND wh.departamento LIKE ?"
        parametros.append(f"%{filtro_departamento}%")
    sql += " ORDER BY wh.ultima_actividad DESC"

    filas = consultar_todos(sql, tuple(parametros))
    return [dict(f) for f in filas]


def listar_mis_conversaciones(usuario_id):
    """Las conversaciones que ESTE agente ya aceptó y está atendiendo."""
    filas = consultar_todos(
        """
        SELECT wh.*, p.primer_nombre, p.primer_apellido, u.nombre AS agente_nombre
        FROM whatsapp_hilos wh
        LEFT JOIN pacientes p ON p.id = wh.paciente_id
        LEFT JOIN usuarios u ON u.id = wh.agente_asignado_id
        WHERE wh.agente_asignado_id=? AND wh.estado != 'Cerrado'
        ORDER BY wh.ultima_actividad DESC
        """,
        (usuario_id,),
    )
    return [dict(f) for f in filas]


def listar_hilos(rol_usuario=None):
    """Se conserva por compatibilidad -- todas las conversaciones abiertas, sin separar en espera/mías."""
    filtro_departamento = ROLES_CON_DEPARTAMENTO_ASIGNADO.get(rol_usuario)

    sql = """
        SELECT wh.*, p.primer_nombre, p.primer_apellido, u.nombre AS agente_nombre
        FROM whatsapp_hilos wh
        LEFT JOIN pacientes p ON p.id = wh.paciente_id
        LEFT JOIN usuarios u ON u.id = wh.agente_asignado_id
    """
    parametros = ()
    if filtro_departamento:
        sql += " WHERE wh.departamento LIKE ?"
        parametros = (f"%{filtro_departamento}%",)
    sql += " ORDER BY wh.ultima_actividad DESC"

    filas = consultar_todos(sql, parametros)
    return [dict(f) for f in filas]


def obtener_hilo(hilo_id: int):
    fila = consultar_uno(
        """
        SELECT wh.*, p.primer_nombre, p.primer_apellido, p.documento, p.celular AS celular_ficha
        FROM whatsapp_hilos wh
        LEFT JOIN pacientes p ON p.id = wh.paciente_id
        WHERE wh.id=?
        """,
        (hilo_id,),
    )
    return dict(fila) if fila else None


def obtener_mensajes(hilo_id: int):
    hilo = obtener_hilo(hilo_id)
    if not hilo:
        return []
    filas = consultar_todos(
        "SELECT * FROM whatsapp_conversaciones WHERE numero_celular=? ORDER BY fecha ASC",
        (hilo["numero_celular"],),
    )
    return [dict(f) for f in filas]


def marcar_leido(hilo_id: int):
    ejecutar("UPDATE whatsapp_hilos SET no_leidos=0 WHERE id=?", (hilo_id,))


def tomar_conversacion(hilo_id: int, usuario_id: int):
    """
    El agente ACEPTA la conversación (desde "en espera" o
    reasignándosela) -- el chatbot automático deja de responder
    en este hilo, y pasa a la bandeja de "Mis conversaciones"
    de este agente. Funciona sin importar si el bot ya había
    terminado con ella o todavía la estaba atendiendo.
    """
    ejecutar(
        "UPDATE whatsapp_hilos SET atendido_por_humano=1, agente_asignado_id=?, estado='Abierto' WHERE id=?",
        (usuario_id, hilo_id),
    )


def transferir_conversacion(hilo_id: int, de_agente_id, a_agente_id: int, motivo: str):
    """Pasa la conversación a otro agente conectado, dejando registro de quién la transfirió y por qué."""
    if not a_agente_id:
        raise ValueError("Debe indicar a qué agente se transfiere.")
    if not motivo or not motivo.strip():
        raise ValueError("Debe indicar el motivo de la transferencia.")

    ejecutar(
        "UPDATE whatsapp_hilos SET agente_asignado_id=?, atendido_por_humano=1, estado='Abierto' WHERE id=?",
        (a_agente_id, hilo_id),
    )
    ejecutar(
        "INSERT INTO whatsapp_transferencias(hilo_id, de_agente_id, a_agente_id, motivo) VALUES (?, ?, ?, ?)",
        (hilo_id, de_agente_id, a_agente_id, motivo.strip()),
    )


def historial_transferencias(hilo_id: int):
    filas = consultar_todos(
        """
        SELECT t.*, ua.nombre AS de_nombre, ub.nombre AS a_nombre
        FROM whatsapp_transferencias t
        LEFT JOIN usuarios ua ON ua.id = t.de_agente_id
        LEFT JOIN usuarios ub ON ub.id = t.a_agente_id
        WHERE t.hilo_id=? ORDER BY t.fecha ASC
        """,
        (hilo_id,),
    )
    return [dict(f) for f in filas]


def devolver_a_bot(hilo_id: int):
    ejecutar(
        "UPDATE whatsapp_hilos SET atendido_por_humano=0, agente_asignado_id=NULL WHERE id=?",
        (hilo_id,),
    )


def finalizar_conversacion(hilo_id: int, con_respuesta: bool):
    """
    Termina la conversación. Si es "con respuesta", se envía el
    mensaje de despedida configurado (con el enlace a la
    encuesta de satisfacción si está configurado) antes de
    cerrarla -- si es "sin respuesta", solo se cierra.
    """
    hilo = obtener_hilo(hilo_id)
    if not hilo:
        raise ValueError("La conversación no existe.")

    if con_respuesta:
        config = consultar_uno("SELECT mensaje_despedida, url_encuesta_satisfaccion FROM configuracion_whatsapp WHERE id=1")
        config = dict(config) if config else {}
        texto = config.get("mensaje_despedida") or "✨ Gracias por confiar en nosotros."
        if config.get("url_encuesta_satisfaccion"):
            texto += f"\n\n📋 Nos encantaría conocer su opinión, por favor responda esta breve encuesta:\n{config['url_encuesta_satisfaccion']}"

        enviar_whatsapp(hilo["numero_celular"], texto)
        ejecutar(
            "INSERT INTO whatsapp_conversaciones(numero_celular, paciente_id, direccion, mensaje) VALUES (?, ?, 'saliente', ?)",
            (hilo["numero_celular"], hilo.get("paciente_id"), texto),
        )

    ejecutar("UPDATE whatsapp_hilos SET estado='Cerrado' WHERE id=?", (hilo_id,))


def cerrar_conversacion(hilo_id: int):
    """Se conserva por compatibilidad -- equivale a finalizar sin respuesta."""
    finalizar_conversacion(hilo_id, con_respuesta=False)


def actualizar_etiquetas(hilo_id: int, etiquetas: list):
    texto_etiquetas = ",".join(e.strip() for e in etiquetas if e.strip())
    ejecutar("UPDATE whatsapp_hilos SET etiquetas=? WHERE id=?", (texto_etiquetas, hilo_id))


def enviar_archivo_agente(hilo_id: int, archivo_base64: str, nombre_archivo: str, usuario_id: int) -> dict:
    """Envía una foto o documento al paciente desde el chat del agente."""
    hilo = obtener_hilo(hilo_id)
    if not hilo:
        raise ValueError("La conversación no existe.")
    if not archivo_base64:
        raise ValueError("Debe adjuntar un archivo.")

    es_imagen = nombre_archivo.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
    resultado = enviar_whatsapp(hilo["numero_celular"], f"📎 {nombre_archivo}", adjunto_url=archivo_base64)

    ejecutar(
        "INSERT INTO whatsapp_conversaciones(numero_celular, paciente_id, direccion, mensaje, tipo_mensaje, url_adjunto) "
        "VALUES (?, ?, 'saliente', ?, ?, ?)",
        (hilo["numero_celular"], hilo.get("paciente_id"), nombre_archivo, "imagen" if es_imagen else "documento", archivo_base64),
    )
    ejecutar("UPDATE whatsapp_hilos SET ultimo_mensaje=?, ultima_actividad=CURRENT_TIMESTAMP WHERE id=?", (f"📎 {nombre_archivo}", hilo_id))
    return resultado


# ==========================================================
# PRESENCIA DE AGENTES (quién está conectado ahora mismo)
# ==========================================================

def marcar_presencia(usuario_id: int):
    ejecutar(
        "INSERT INTO whatsapp_agentes_presencia(usuario_id, ultima_actividad) VALUES (?, CURRENT_TIMESTAMP) "
        "ON CONFLICT(usuario_id) DO UPDATE SET ultima_actividad=CURRENT_TIMESTAMP",
        (usuario_id,),
    )


def listar_agentes_conectados(minutos=3):
    """Agentes que han estado activos en el panel en los últimos N minutos -- para poder transferirles una conversación."""
    filas = consultar_todos(
        """
        SELECT u.id, u.nombre, u.rol
        FROM whatsapp_agentes_presencia p
        JOIN usuarios u ON u.id = p.usuario_id
        WHERE p.ultima_actividad >= datetime('now', ?)
        ORDER BY u.nombre
        """,
        (f"-{minutos} minutes",),
    )
    return [dict(f) for f in filas]


# ==========================================================
# CONTACTOS INTERNOS (números de la propia empresa)
# ==========================================================

def listar_contactos_internos():
    filas = consultar_todos("SELECT * FROM whatsapp_contactos_internos ORDER BY nombre")
    return [dict(f) for f in filas]


def crear_contacto_interno(nombre: str, numero_celular: str, area: str, usuario_id=None) -> int:
    if not nombre or not numero_celular:
        raise ValueError("Debe indicar el nombre y el número de celular.")
    numero_normalizado = normalizar_celular(numero_celular)
    return ejecutar(
        "INSERT INTO whatsapp_contactos_internos(nombre, numero_celular, area, usuario_creacion) VALUES (?, ?, ?, ?)",
        (nombre.strip(), numero_normalizado, area or "", usuario_id),
    )


def desactivar_contacto_interno(contacto_id: int):
    ejecutar("UPDATE whatsapp_contactos_internos SET activo=0 WHERE id=?", (contacto_id,))


def es_contacto_interno(numero_celular: str) -> bool:
    numero_normalizado = normalizar_celular(numero_celular)
    fila = consultar_uno(
        "SELECT id FROM whatsapp_contactos_internos WHERE numero_celular=? AND activo=1", (numero_normalizado,)
    )
    return bool(fila)


# ==========================================================
# RESPUESTAS RÁPIDAS (mensajes predefinidos para el agente)
# ==========================================================

def listar_respuestas_rapidas():
    filas = consultar_todos(
        "SELECT * FROM whatsapp_respuestas_rapidas WHERE activo=1 ORDER BY categoria, orden, titulo"
    )
    return [dict(f) for f in filas]


def listar_todas_respuestas_rapidas():
    """Incluye las inactivas también -- para la pantalla de administración."""
    filas = consultar_todos("SELECT * FROM whatsapp_respuestas_rapidas ORDER BY categoria, orden, titulo")
    return [dict(f) for f in filas]


def crear_respuesta_rapida(titulo: str, texto: str, categoria: str, orden: int, usuario_id=None) -> int:
    if not titulo or not titulo.strip():
        raise ValueError("Debe indicar un título corto para identificar la respuesta.")
    if not texto or not texto.strip():
        raise ValueError("El texto de la respuesta no puede estar vacío.")
    return ejecutar(
        "INSERT INTO whatsapp_respuestas_rapidas(titulo, texto, categoria, orden, usuario_creacion) VALUES (?, ?, ?, ?, ?)",
        (titulo.strip(), texto.strip(), categoria or "General", orden or 0, usuario_id),
    )


def actualizar_respuesta_rapida(respuesta_id: int, titulo: str, texto: str, categoria: str, orden: int):
    if not titulo or not titulo.strip():
        raise ValueError("Debe indicar un título corto para identificar la respuesta.")
    if not texto or not texto.strip():
        raise ValueError("El texto de la respuesta no puede estar vacío.")
    ejecutar(
        "UPDATE whatsapp_respuestas_rapidas SET titulo=?, texto=?, categoria=?, orden=? WHERE id=?",
        (titulo.strip(), texto.strip(), categoria or "General", orden or 0, respuesta_id),
    )


def desactivar_respuesta_rapida(respuesta_id: int):
    ejecutar("UPDATE whatsapp_respuestas_rapidas SET activo=0 WHERE id=?", (respuesta_id,))


def activar_respuesta_rapida(respuesta_id: int):
    ejecutar("UPDATE whatsapp_respuestas_rapidas SET activo=1 WHERE id=?", (respuesta_id,))


def enviar_mensaje_agente(hilo_id: int, texto: str, usuario_id: int) -> dict:
    hilo = obtener_hilo(hilo_id)
    if not hilo:
        raise ValueError("La conversación no existe.")
    if not texto or not texto.strip():
        raise ValueError("El mensaje no puede estar vacío.")

    resultado = enviar_whatsapp(hilo["numero_celular"], texto)

    ejecutar(
        "INSERT INTO whatsapp_conversaciones(numero_celular, paciente_id, direccion, mensaje) VALUES (?, ?, 'saliente', ?)",
        (hilo["numero_celular"], hilo.get("paciente_id"), texto),
    )
    ejecutar(
        "UPDATE whatsapp_hilos SET ultimo_mensaje=?, ultima_actividad=CURRENT_TIMESTAMP WHERE id=?",
        (texto, hilo_id),
    )

    return resultado


def enviar_ultima_orden(hilo_id: int) -> dict:
    hilo = obtener_hilo(hilo_id)
    if not hilo or not hilo.get("paciente_id"):
        raise ValueError("Esta conversación no está asociada a un paciente registrado.")

    orden = consultar_uno(
        "SELECT * FROM ordenes_medicas WHERE paciente_id=? ORDER BY fecha_creacion DESC LIMIT 1",
        (hilo["paciente_id"],),
    )
    if not orden:
        raise ValueError("Este paciente no tiene ninguna orden médica registrada.")
    orden = dict(orden)

    from core.config import PUBLIC_BASE_URL
    adjunto_url = None
    if PUBLIC_BASE_URL and orden.get("token_pdf"):
        adjunto_url = f"{PUBLIC_BASE_URL.rstrip('/')}/ordenes-medicas/pdf-publico/{orden['id']}/{orden['token_pdf']}"

    texto = f"📋 Le reenviamos su orden médica más reciente ({orden.get('tipo_orden', 'Orden')}, {orden.get('fecha_creacion','')})."
    resultado = enviar_whatsapp(hilo["numero_celular"], texto, adjunto_url=adjunto_url)

    ejecutar(
        "INSERT INTO whatsapp_conversaciones(numero_celular, paciente_id, direccion, mensaje) VALUES (?, ?, 'saliente', ?)",
        (hilo["numero_celular"], hilo["paciente_id"], texto),
    )
    ejecutar("UPDATE whatsapp_hilos SET ultimo_mensaje=?, ultima_actividad=CURRENT_TIMESTAMP WHERE id=?", (texto, hilo_id))
    return resultado


def enviar_ultima_recomendacion(hilo_id: int) -> dict:
    hilo = obtener_hilo(hilo_id)
    if not hilo or not hilo.get("paciente_id"):
        raise ValueError("Esta conversación no está asociada a un paciente registrado.")

    reco = consultar_uno(
        "SELECT * FROM recomendaciones_medicas WHERE paciente_id=? ORDER BY fecha_creacion DESC LIMIT 1",
        (hilo["paciente_id"],),
    )
    if not reco:
        raise ValueError("Este paciente no tiene ninguna recomendación registrada.")
    reco = dict(reco)

    texto = (
        f"📝 Su última recomendación médica ({reco.get('fecha_creacion','')}):\n\n"
        f"Diagnóstico: {reco.get('diagnostico_ppal_nombre','')}\n"
    )
    if reco.get("recomendaciones_texto"):
        texto += f"\n{reco['recomendaciones_texto']}"

    resultado = enviar_whatsapp(hilo["numero_celular"], texto)

    ejecutar(
        "INSERT INTO whatsapp_conversaciones(numero_celular, paciente_id, direccion, mensaje) VALUES (?, ?, 'saliente', ?)",
        (hilo["numero_celular"], hilo["paciente_id"], texto),
    )
    ejecutar("UPDATE whatsapp_hilos SET ultimo_mensaje=?, ultima_actividad=CURRENT_TIMESTAMP WHERE id=?", (texto, hilo_id))
    return resultado


def vincular_paciente(hilo_id: int, paciente_id: int):
    """Por si un número escribe y todavía no está asociado a ningún paciente (ej. un acudiente con otro número)."""
    ejecutar("UPDATE whatsapp_hilos SET paciente_id=? WHERE id=?", (paciente_id, hilo_id))
