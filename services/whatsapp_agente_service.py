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


def listar_hilos():
    """
    Bandeja de entrada, ordenada por actividad más reciente
    primero -- igual que la lista de chats de WhatsApp.
    """
    filas = consultar_todos(
        """
        SELECT wh.*, p.primer_nombre, p.primer_apellido, u.nombre AS agente_nombre
        FROM whatsapp_hilos wh
        LEFT JOIN pacientes p ON p.id = wh.paciente_id
        LEFT JOIN usuarios u ON u.id = wh.agente_asignado_id
        ORDER BY wh.ultima_actividad DESC
        """
    )
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
    """El agente humano toma el control: el chatbot automático deja de responder en este hilo."""
    ejecutar(
        "UPDATE whatsapp_hilos SET atendido_por_humano=1, agente_asignado_id=?, estado='Abierto' WHERE id=?",
        (usuario_id, hilo_id),
    )


def devolver_a_bot(hilo_id: int):
    ejecutar(
        "UPDATE whatsapp_hilos SET atendido_por_humano=0, agente_asignado_id=NULL WHERE id=?",
        (hilo_id,),
    )


def cerrar_conversacion(hilo_id: int):
    ejecutar("UPDATE whatsapp_hilos SET estado='Cerrado' WHERE id=?", (hilo_id,))


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
