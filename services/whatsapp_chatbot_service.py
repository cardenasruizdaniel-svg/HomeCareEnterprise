"""
HomeCare Enterprise - Chatbot de WhatsApp para pacientes

Flujo profesional configurable, tipo Whaticket:

1. Primer contacto -> mensaje de bienvenida + nota legal de
   tratamiento de datos. Cualquier mensaje que el paciente
   escriba después de esto se toma como que acepta continuar
   (igual que en el ejemplo de las capturas: no hace falta que
   escriba "acepto", basta con que siga escribiendo).
2. Menú principal (configurable en el árbol de opciones) --
   típicamente empieza con la selección de ciudad, y de ahí
   se abre el menú de servicios.
3. Cada opción puede ser: SUBMENÚ (abre más opciones),
   RESPUESTA AUTOMÁTICA (contesta con datos reales del
   paciente), RECOLECCIÓN DE DATOS (le pide al paciente que
   escriba varios datos en un solo mensaje -- nombre,
   documento, etc. -- y cuando responde, se guarda todo y se
   deriva a un agente humano), o DERIVAR A UN DEPARTAMENTO
   directamente.
4. Al terminar una recolección de datos o una derivación, se
   envía el mensaje de despedida configurado, con el enlace a
   la encuesta de satisfacción si está configurada.

Todo el árbol de opciones, los mensajes, y los campos que se
piden en cada recolección de datos son configurables desde
Configuración Chatbot → Flujo de Conversación.
"""

from database.database import consultar_todos, consultar_uno, ejecutar
from services.notificaciones_service import enviar_whatsapp, normalizar_celular

PALABRAS_REINICIO = ("menu", "menú", "#", "hola", "buenas", "inicio", "hi")


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


def _config() -> dict:
    fila = consultar_uno("SELECT * FROM configuracion_whatsapp WHERE id=1")
    return dict(fila) if fila else {}


def _obtener_o_crear_hilo(numero_celular: str):
    numero_normalizado = normalizar_celular(numero_celular)
    hilo = consultar_uno("SELECT * FROM whatsapp_hilos WHERE numero_celular=?", (numero_normalizado,))
    if hilo:
        return dict(hilo)
    hilo_id = ejecutar("INSERT INTO whatsapp_hilos(numero_celular) VALUES (?)", (numero_normalizado,))
    return dict(consultar_uno("SELECT * FROM whatsapp_hilos WHERE id=?", (hilo_id,)))


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


def _texto_menu(padre_id) -> str:
    opciones = _listar_opciones(padre_id)
    lineas = [f"{indice} - {op['texto_boton']}" for indice, op in enumerate(opciones, start=1)]
    pie = "\n\n# - Volver al menú principal"
    return "Seleccione la opción que necesita:\n\n" + "\n".join(lineas) + pie


def _reemplazar_marcadores(texto: str, paciente: dict) -> str:
    nombre_formal = f"Sr.(a) {paciente.get('primer_nombre','')} {paciente.get('primer_apellido','')}".strip()
    if "{nombre_formal}" in texto:
        texto = texto.replace("{nombre_formal}", nombre_formal)
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


def _enviar_despedida(numero_celular: str, paciente_id):
    config = _config()
    texto = config.get("mensaje_despedida") or "✨ Gracias por confiar en nosotros."
    if config.get("url_encuesta_satisfaccion"):
        texto += f"\n\n📋 Nos encantaría conocer su opinión, por favor responda esta breve encuesta:\n{config['url_encuesta_satisfaccion']}"
    enviar_whatsapp(numero_celular, texto)
    _registrar_mensaje(numero_celular, paciente_id, "saliente", texto)


def procesar_mensaje_entrante(numero_celular: str, texto_mensaje: str) -> dict:
    texto_original = (texto_mensaje or "").strip()
    texto_normalizado = texto_original.lower()

    _registrar_mensaje(numero_celular, None, "entrante", texto_mensaje)

    paciente = _buscar_paciente_por_celular(numero_celular)

    hilo = _obtener_o_crear_hilo(numero_celular)

    if paciente:
        ejecutar("UPDATE whatsapp_hilos SET paciente_id=COALESCE(paciente_id, ?) WHERE id=?", (paciente["id"], hilo["id"]))

    if not paciente:
        respuesta = (
            "Este número no está registrado en nuestro sistema. "
            "Si usted es paciente de HomeCare del Quindío I.P.S., por favor comuníquese con la IPS "
            "para verificar el número de contacto registrado."
        )
        enviar_whatsapp(numero_celular, respuesta)
        _registrar_mensaje(numero_celular, None, "saliente", respuesta)
        return {"ok": True, "reconocido": False}

    # ---------- Paso 1: bienvenida + nota legal (una sola vez) ----------
    if not hilo.get("politica_aceptada"):
        ejecutar("UPDATE whatsapp_hilos SET politica_aceptada=1 WHERE id=?", (hilo["id"],))
        config = _config()
        bienvenida = config.get("mensaje_bienvenida") or "Hola, soy el asistente virtual de HomeCare del Quindío I.P.S. 👋"
        respuesta = bienvenida + "\n\n" + _texto_menu(None)
        enviar_whatsapp(numero_celular, respuesta)
        _registrar_mensaje(numero_celular, paciente["id"], "saliente", respuesta)
        return {"ok": True, "reconocido": True}

    # ---------- Paso 2: esperando la respuesta de una recolección de datos ----------
    if hilo.get("esperando_datos_libres"):
        opcion = consultar_uno("SELECT * FROM whatsapp_flujo_opciones WHERE id=?", (hilo.get("opcion_actual_id"),))
        opcion = dict(opcion) if opcion else {}

        ejecutar(
            "INSERT INTO whatsapp_datos_recolectados(hilo_id, opcion_id, texto_solicitado, respuesta_paciente) VALUES (?, ?, ?, ?)",
            (hilo["id"], opcion.get("id"), opcion.get("campos_solicitados"), texto_original),
        )
        ejecutar(
            "UPDATE whatsapp_hilos SET esperando_datos_libres=0, atendido_por_humano=1, departamento=?, opcion_actual_id=NULL WHERE id=?",
            (opcion.get("departamento") or "General", hilo["id"]),
        )

        agradecimiento = "Una vez recibamos la información, nuestro equipo realizará la validación correspondiente y gestionará su solicitud en el menor tiempo posible."
        enviar_whatsapp(numero_celular, agradecimiento)
        _registrar_mensaje(numero_celular, paciente["id"], "saliente", agradecimiento)
        _enviar_despedida(numero_celular, paciente["id"])
        return {"ok": True, "reconocido": True}

    # ---------- Paso 3: "#"/"menu" -> volver al menú principal ----------
    if texto_normalizado in PALABRAS_REINICIO:
        ejecutar("UPDATE whatsapp_hilos SET opcion_actual_id=NULL WHERE id=?", (hilo["id"],))
        respuesta = _texto_menu(None)
        enviar_whatsapp(numero_celular, respuesta)
        _registrar_mensaje(numero_celular, paciente["id"], "saliente", respuesta)
        return {"ok": True, "reconocido": True}

    # ---------- Paso 4: navegación normal del árbol ----------
    opciones_nivel = _listar_opciones(hilo.get("opcion_actual_id"))
    opcion_elegida = None
    if texto_normalizado.isdigit():
        indice = int(texto_normalizado)
        if 1 <= indice <= len(opciones_nivel):
            opcion_elegida = opciones_nivel[indice - 1]

    if opcion_elegida is None:
        respuesta = "No entendí su respuesta. 🤔\n\n" + _texto_menu(hilo.get("opcion_actual_id"))
        enviar_whatsapp(numero_celular, respuesta)
        _registrar_mensaje(numero_celular, paciente["id"], "saliente", respuesta)
        return {"ok": True, "reconocido": True}

    tipo = opcion_elegida["tipo_accion"]

    if tipo == "submenu":
        ejecutar("UPDATE whatsapp_hilos SET opcion_actual_id=? WHERE id=?", (opcion_elegida["id"], hilo["id"]))
        nombre_formal = f"Sr.(a) {paciente.get('primer_nombre','')} {paciente.get('primer_apellido','')}".strip()
        respuesta = f"{nombre_formal} gracias por continuar con HomeCare del Quindío I.P.S. 💙\n\n" + _texto_menu(opcion_elegida["id"])

    elif tipo == "recoleccion_datos":
        ejecutar(
            "UPDATE whatsapp_hilos SET esperando_datos_libres=1, opcion_actual_id=? WHERE id=?",
            (opcion_elegida["id"], hilo["id"]),
        )
        # Si se configuró un texto personalizado para esta
        # opción, se usa tal cual (respetando exactamente lo
        # que se haya redactado) -- si no, se arma uno genérico
        # a partir de la lista de campos solicitados.
        if opcion_elegida.get("contenido_respuesta"):
            respuesta = opcion_elegida["contenido_respuesta"]
        else:
            campos = (opcion_elegida.get("campos_solicitados") or "").strip()
            lista_campos = "\n".join(f"• {c.strip()}" for c in campos.split("\n") if c.strip())
            respuesta = (
                "Gracias por comunicarse con HomeCare del Quindío I.P.S. 💙\n\n"
                "Con gusto le ayudaremos a gestionar su solicitud.\n\n"
                "Para continuar, por favor compártanos la siguiente información en un solo mensaje:\n\n"
                f"{lista_campos}\n\n"
                "Una vez recibamos la información, nuestro equipo la validará y gestionará su solicitud."
            )

    elif tipo == "derivar_departamento":
        ejecutar(
            "UPDATE whatsapp_hilos SET atendido_por_humano=1, departamento=?, opcion_actual_id=NULL WHERE id=?",
            (opcion_elegida.get("departamento") or "General", hilo["id"]),
        )
        respuesta = opcion_elegida.get("contenido_respuesta") or "Ya lo comunicamos con uno de nuestros asesores."
        enviar_whatsapp(numero_celular, respuesta)
        _registrar_mensaje(numero_celular, paciente["id"], "saliente", respuesta)
        _enviar_despedida(numero_celular, paciente["id"])
        return {"ok": True, "reconocido": True, "paciente_id": paciente["id"]}

    else:  # respuesta_automatica
        respuesta = _reemplazar_marcadores(opcion_elegida.get("contenido_respuesta") or "", paciente)
        respuesta += "\n\n" + _texto_menu(hilo.get("opcion_actual_id"))

    enviar_whatsapp(numero_celular, respuesta)
    _registrar_mensaje(numero_celular, paciente["id"], "saliente", respuesta)
    return {"ok": True, "reconocido": True, "paciente_id": paciente["id"]}
