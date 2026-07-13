"""
HomeCare Enterprise - Chatbot de WhatsApp para pacientes

El menú y las respuestas del bot ahora son CONFIGURABLES desde
la web (Configuración Chatbot → Flujo de Conversación), en vez
de estar escritos fijos en este archivo -- un administrador
puede armar menús con submenús, cambiar los textos, y decidir
a qué departamento se deriva cada opción, sin tocar código.

Cómo funciona la conversación:
1. El paciente escribe -- si dice "menu"/"hola" o es su primer
   mensaje, se le muestra el menú principal.
2. Si responde con un número, se interpreta contra las
   opciones del nivel de menú en el que esté en ese momento
   (se guarda en whatsapp_hilos.opcion_actual_id).
3. Cada opción puede ser: un SUBMENÚ (abre más opciones), una
   RESPUESTA AUTOMÁTICA (contesta con datos reales del
   paciente), o DERIVAR A UN DEPARTAMENTO (pasa la conversación
   a un agente humano, etiquetada con el departamento, y el bot
   deja de responder ahí -- ver whatsapp_agente_service).

SEGURIDAD Y PRIVACIDAD: antes de responder CUALQUIER cosa, se
verifica que el número de celular que escribe corresponda a un
paciente registrado en el sistema -- si no coincide con nadie,
no se revela ninguna información.
"""

from database.database import consultar_todos, consultar_uno, ejecutar
from services.notificaciones_service import enviar_whatsapp, normalizar_celular

PALABRAS_REINICIO = ("menu", "menú", "hola", "buenas", "inicio", "hi", "")


def _buscar_paciente_por_celular(numero: str):
    numero_normalizado = normalizar_celular(numero)
    if not numero_normalizado:
        return None

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


def _obtener_mensaje_bienvenida() -> str:
    config = consultar_uno("SELECT mensaje_bienvenida FROM configuracion_whatsapp WHERE id=1")
    if config and dict(config).get("mensaje_bienvenida"):
        return dict(config)["mensaje_bienvenida"]
    return "Hola, soy el asistente virtual de HomeCare del Quindío I.P.S. 👋"


def _listar_opciones(padre_id):
    if padre_id is None:
        filas = consultar_todos(
            "SELECT * FROM whatsapp_flujo_opciones WHERE padre_id IS NULL AND activo=1 ORDER BY orden"
        )
    else:
        filas = consultar_todos(
            "SELECT * FROM whatsapp_flujo_opciones WHERE padre_id=? AND activo=1 ORDER BY orden", (padre_id,)
        )
    return [dict(f) for f in filas]


def _texto_menu(nombre_paciente: str, padre_id, es_inicio: bool) -> str:
    opciones = _listar_opciones(padre_id)

    if es_inicio:
        encabezado = f"{_obtener_mensaje_bienvenida()}\n\nHola {nombre_paciente}, ¿en qué le puedo ayudar? Responda con el número:\n\n"
    else:
        encabezado = "¿Algo más? Responda con el número:\n\n"

    lineas = [f"{indice}️⃣ {op['texto_boton']}" for indice, op in enumerate(opciones, start=1)]
    pie = "\n\nEn cualquier momento escriba *menu* para volver al inicio."
    return encabezado + "\n".join(lineas) + pie


def _reemplazar_marcadores(texto: str, paciente: dict) -> str:
    if "{proxima_visita}" in texto:
        texto = texto.replace("{proxima_visita}", _dato_proxima_visita(paciente))
    if "{ultima_orden}" in texto:
        texto = texto.replace("{ultima_orden}", _dato_ultima_orden(paciente))
    if "{ultimas_recomendaciones}" in texto:
        texto = texto.replace("{ultimas_recomendaciones}", _dato_ultimas_recomendaciones(paciente))
    return texto


def _dato_proxima_visita(paciente: dict) -> str:
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
        return "No tiene ninguna visita programada por ahora."
    fila = dict(fila)
    return (
        f"📅 *Fecha:* {fila['fecha']}\n*Hora:* {fila['hora_inicio']}\n"
        f"*Servicio:* {fila['servicio']}\n*Profesional:* {fila['profesional'] or 'Por asignar'}"
    )


def _dato_ultima_orden(paciente: dict) -> str:
    fila = consultar_uno(
        "SELECT * FROM ordenes_medicas WHERE paciente_id=? ORDER BY fecha_creacion DESC LIMIT 1", (paciente["id"],)
    )
    if not fila:
        return "Todavía no tiene ninguna orden médica registrada."
    fila = dict(fila)
    return f"📋 Su última orden médica ({fila.get('tipo_orden', 'Orden')}) fue generada el {fila.get('fecha_creacion', '')}."


def _dato_ultimas_recomendaciones(paciente: dict) -> str:
    filas = consultar_todos(
        "SELECT * FROM recomendaciones_medicas WHERE paciente_id=? ORDER BY fecha_creacion DESC LIMIT 1",
        (paciente["id"],),
    )
    if not filas:
        return "Todavía no hay recomendaciones médicas registradas."
    r = dict(filas[0])
    texto = f"📝 ({r.get('fecha_creacion','')}) *Diagnóstico principal:* {r.get('diagnostico_ppal_nombre','')}"
    if r.get("recomendaciones_texto"):
        texto += f"\n{r['recomendaciones_texto']}"
    texto += "\n\nPor su seguridad, no enviamos el detalle clínico completo por aquí."
    return texto


def procesar_mensaje_entrante(numero_celular: str, texto_mensaje: str) -> dict:
    texto_normalizado = (texto_mensaje or "").strip().lower()

    _registrar_mensaje(numero_celular, None, "entrante", texto_mensaje)

    paciente = _buscar_paciente_por_celular(numero_celular)

    if paciente:
        try:
            from services.whatsapp_agente_service import vincular_paciente
            hilo_fila = consultar_uno("SELECT id FROM whatsapp_hilos WHERE numero_celular=?", (normalizar_celular(numero_celular),))
            if hilo_fila:
                vincular_paciente(dict(hilo_fila)["id"], paciente["id"])
        except Exception:
            pass

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
    numero_normalizado = normalizar_celular(numero_celular)
    hilo = consultar_uno("SELECT * FROM whatsapp_hilos WHERE numero_celular=?", (numero_normalizado,))
    hilo = dict(hilo) if hilo else {"id": None, "opcion_actual_id": None}

    # "menu"/"hola"/mensaje vacío -> se reinicia al menú principal
    if texto_normalizado in PALABRAS_REINICIO:
        if hilo.get("id"):
            ejecutar("UPDATE whatsapp_hilos SET opcion_actual_id=NULL WHERE id=?", (hilo["id"],))
        respuesta = _texto_menu(nombre_paciente, None, es_inicio=True)
        enviar_whatsapp(numero_celular, respuesta)
        _registrar_mensaje(numero_celular, paciente["id"], "saliente", respuesta)
        return {"ok": True, "reconocido": True}

    # Interpretar el mensaje como el numero de una opcion del nivel actual
    opciones_nivel = _listar_opciones(hilo.get("opcion_actual_id"))
    opcion_elegida = None
    if texto_normalizado.isdigit():
        indice = int(texto_normalizado)
        if 1 <= indice <= len(opciones_nivel):
            opcion_elegida = opciones_nivel[indice - 1]

    if opcion_elegida is None:
        respuesta = "No entendí su respuesta. 🤔\n\n" + _texto_menu(nombre_paciente, hilo.get("opcion_actual_id"), es_inicio=False)
        enviar_whatsapp(numero_celular, respuesta)
        _registrar_mensaje(numero_celular, paciente["id"], "saliente", respuesta)
        return {"ok": True, "reconocido": True}

    if opcion_elegida["tipo_accion"] == "submenu":
        if hilo.get("id"):
            ejecutar("UPDATE whatsapp_hilos SET opcion_actual_id=? WHERE id=?", (opcion_elegida["id"], hilo["id"]))
        respuesta = _texto_menu(nombre_paciente, opcion_elegida["id"], es_inicio=False)

    elif opcion_elegida["tipo_accion"] == "derivar_departamento":
        if hilo.get("id"):
            ejecutar(
                "UPDATE whatsapp_hilos SET atendido_por_humano=1, departamento=?, opcion_actual_id=NULL WHERE id=?",
                (opcion_elegida.get("departamento") or "General", hilo["id"]),
            )
        respuesta = opcion_elegida.get("contenido_respuesta") or "Ya lo comunicamos con uno de nuestros asesores."

    else:  # respuesta_automatica
        respuesta = _reemplazar_marcadores(opcion_elegida.get("contenido_respuesta") or "", paciente)
        respuesta += "\n\n" + _texto_menu(nombre_paciente, hilo.get("opcion_actual_id"), es_inicio=False)

    enviar_whatsapp(numero_celular, respuesta)
    _registrar_mensaje(numero_celular, paciente["id"], "saliente", respuesta)
    return {"ok": True, "reconocido": True, "paciente_id": paciente["id"]}
