"""
HomeCare Enterprise - Chatbot de WhatsApp para pacientes

Un chatbot sencillo, basado en menú numérico (sin necesitar
guardar el "estado" de la conversación entre mensajes -- cada
mensaje que llega se interpreta solo, buscando un número de
opción; si no coincide con nada, se le vuelve a mostrar el
menú). Así de simple es más fácil de mantener y de auditar
que uno con inteligencia artificial libre, y evita que el
bot "invente" información clínica.

SEGURIDAD Y PRIVACIDAD: antes de responder CUALQUIER cosa, se
verifica que el número de celular que escribe corresponda a un
paciente registrado en el sistema -- si no coincide con nadie,
no se revela ninguna información, solo se informa que el
número no está registrado. Esto es clave porque los datos de
salud son datos sensibles (Ley 1581 de 2012).

El envío de las respuestas usa la misma función
`enviar_whatsapp` que ya usa el resto del sistema (órdenes
médicas, confirmación de citas, etc.) -- no se duplica la
integración con la API de Meta.
"""

from database.database import consultar_todos, consultar_uno, ejecutar
from services.notificaciones_service import enviar_whatsapp, normalizar_celular

OPCIONES_MENU = {
    "1": "proxima_visita",
    "2": "ultima_orden",
    "3": "ultimas_recomendaciones",
    "4": "resumen_historia",
    "5": "hablar_asesor",
}


def _buscar_paciente_por_celular(numero: str):
    numero_normalizado = normalizar_celular(numero)
    if not numero_normalizado:
        return None

    # El celular guardado en la ficha del paciente puede estar
    # con o sin indicativo de país (según cómo se haya
    # diligenciado) -- por eso se comparan ambos ya
    # normalizados de la misma forma, en vez de compararlos tal
    # cual están guardados en la base de datos.
    candidatos = consultar_todos("SELECT * FROM pacientes WHERE celular IS NOT NULL AND celular != ''")
    for candidato in candidatos:
        candidato = dict(candidato)
        if normalizar_celular(candidato.get("celular")) == numero_normalizado:
            return candidato

    candidatos_tel = consultar_todos("SELECT * FROM pacientes WHERE telefono IS NOT NULL AND telefono != ''")
    for candidato in candidatos_tel:
        candidato = dict(candidato)
        if normalizar_celular(candidato.get("telefono")) == numero_normalizado:
            return candidato

    return None


def _registrar_mensaje(numero: str, paciente_id, direccion: str, mensaje: str):
    numero_normalizado = normalizar_celular(numero)
    ejecutar(
        "INSERT INTO whatsapp_conversaciones(numero_celular, paciente_id, direccion, mensaje) VALUES (?, ?, ?, ?)",
        (numero_normalizado, paciente_id, direccion, mensaje),
    )


def _texto_menu(nombre_paciente: str) -> str:
    return (
        f"Hola {nombre_paciente} 👋, soy el asistente virtual de *HomeCare del Quindío I.P.S.*\n\n"
        "¿En qué le puedo ayudar? Responda con el número:\n\n"
        "1️⃣ Mi próxima visita programada\n"
        "2️⃣ Mi última orden médica\n"
        "3️⃣ Últimas recomendaciones del médico\n"
        "4️⃣ Resumen de mi historia clínica reciente\n"
        "5️⃣ Hablar con un asesor de la IPS\n\n"
        "En cualquier momento escriba *menu* para volver a ver estas opciones."
    )


def _responder_proxima_visita(paciente: dict) -> str:
    fila = consultar_uno(
        """
        SELECT fecha, hora_inicio, servicio, pr.nombre_completo AS profesional
        FROM programaciones p
        LEFT JOIN profesionales pr ON pr.id = p.profesional_id
        WHERE p.paciente_id=? AND p.estado NOT IN ('Cancelada', 'Completada') AND date(p.fecha) >= date('now')
        ORDER BY p.fecha, p.hora_inicio LIMIT 1
        """,
        (paciente["id"],),
    )
    if not fila:
        return "No tiene ninguna visita programada por ahora. Si necesita agendar una, escriba la opción 5 para hablar con un asesor."
    fila = dict(fila)
    return (
        f"📅 Su próxima visita programada es:\n\n"
        f"*Fecha:* {fila['fecha']}\n*Hora:* {fila['hora_inicio']}\n"
        f"*Servicio:* {fila['servicio']}\n"
        f"*Profesional:* {fila['profesional'] or 'Por asignar'}"
    )


def _responder_ultima_orden(paciente: dict) -> str:
    fila = consultar_uno(
        "SELECT * FROM ordenes_medicas WHERE paciente_id=? ORDER BY fecha_creacion DESC LIMIT 1",
        (paciente["id"],),
    )
    if not fila:
        return "Todavía no tiene ninguna orden médica registrada."
    fila = dict(fila)
    return (
        f"📋 Su última orden médica ({fila.get('tipo_orden', 'Orden')}) fue generada el {fila.get('fecha_creacion', '')}.\n\n"
        "Se la enviamos por este mismo medio en su momento — si necesita que se la reenviemos, escriba la opción 5."
    )


def _responder_ultimas_recomendaciones(paciente: dict) -> str:
    filas = consultar_todos(
        "SELECT * FROM recomendaciones_medicas WHERE paciente_id=? ORDER BY fecha_creacion DESC LIMIT 1",
        (paciente["id"],),
    )
    if not filas:
        return "Todavía no hay recomendaciones médicas registradas."
    r = dict(filas[0])
    texto = (
        f"📝 Su última recomendación médica ({r.get('fecha_creacion','')}):\n\n"
        f"*Diagnóstico principal:* {r.get('diagnostico_ppal_nombre','')}\n"
    )
    if r.get("recomendaciones_texto"):
        texto += f"\n{r['recomendaciones_texto']}"
    texto += "\n\nPor su seguridad, no enviamos aquí el detalle clínico completo — para verlo completo, comuníquese con la IPS (opción 5)."
    return texto


def _responder_resumen_historia(paciente: dict) -> str:
    total_visitas = consultar_uno(
        "SELECT COUNT(*) AS total FROM programaciones WHERE paciente_id=? AND estado='Completada'",
        (paciente["id"],),
    )
    total = dict(total_visitas)["total"] if total_visitas else 0
    return (
        f"📖 Usted tiene {total} visita(s) completada(s) registradas en su historia clínica con nosotros.\n\n"
        "Por tratarse de información clínica sensible, el detalle completo de su historia no se envía por WhatsApp — "
        "puede solicitarla formalmente comunicándose con la IPS (opción 5), o a través de su acudiente autorizado."
    )


def _responder_hablar_asesor() -> str:
    return (
        "🙋 Un asesor de HomeCare del Quindío I.P.S. se comunicará con usted en el horario de atención.\n\n"
        "Si es urgente, por favor llámenos directamente a la línea de la IPS."
    )


def procesar_mensaje_entrante(numero_celular: str, texto_mensaje: str) -> dict:
    """
    Punto de entrada del chatbot: recibe el número y el texto
    de un mensaje entrante, decide qué responder, envía la
    respuesta por WhatsApp, y deja registro de la conversación.
    """
    texto_normalizado = (texto_mensaje or "").strip().lower()

    _registrar_mensaje(numero_celular, None, "entrante", texto_mensaje)

    paciente = _buscar_paciente_por_celular(numero_celular)

    if paciente:
        try:
            from services.whatsapp_agente_service import vincular_paciente
            from database.database import consultar_uno as _consultar_uno
            from services.notificaciones_service import normalizar_celular as _normalizar
            hilo = _consultar_uno("SELECT id FROM whatsapp_hilos WHERE numero_celular=?", (_normalizar(numero_celular),))
            if hilo:
                vincular_paciente(dict(hilo)["id"], paciente["id"])
        except Exception:
            pass  # esto es solo para que el panel de agentes muestre el nombre -- si falla, no debe romper la respuesta del bot

    if not paciente:
        respuesta = (
            "Este número no está registrado en nuestro sistema. "
            "Si usted es paciente de HomeCare del Quindío I.P.S., por favor comuníquese con la IPS "
            "para verificar el número de contacto registrado."
        )
        enviar_whatsapp(numero_celular, respuesta)
        _registrar_mensaje(numero_celular, None, "saliente", respuesta)
        return {"ok": True, "reconocido": False}

    nombre_paciente = paciente.get("primer_nombre", "")

    if texto_normalizado in ("menu", "menú", "hola", "buenas", "inicio", ""):
        respuesta = _texto_menu(nombre_paciente)
    elif texto_normalizado in OPCIONES_MENU:
        opcion = OPCIONES_MENU[texto_normalizado]
        if opcion == "proxima_visita":
            respuesta = _responder_proxima_visita(paciente)
        elif opcion == "ultima_orden":
            respuesta = _responder_ultima_orden(paciente)
        elif opcion == "ultimas_recomendaciones":
            respuesta = _responder_ultimas_recomendaciones(paciente)
        elif opcion == "resumen_historia":
            respuesta = _responder_resumen_historia(paciente)
        else:
            respuesta = _responder_hablar_asesor()
    else:
        respuesta = "No entendí su mensaje. 🤔\n\n" + _texto_menu(nombre_paciente)

    resultado_envio = enviar_whatsapp(numero_celular, respuesta)
    _registrar_mensaje(numero_celular, paciente["id"], "saliente", respuesta)

    return {"ok": True, "reconocido": True, "paciente_id": paciente["id"], "envio": resultado_envio}
