"""HomeCare Enterprise - Administración del Flujo del Chatbot de WhatsApp"""

from database.database import consultar_todos, consultar_uno, ejecutar

TIPOS_ACCION = [
    ("respuesta_automatica", "Responder automáticamente (puede usar datos del paciente)"),
    ("submenu", "Abrir un submenú con más opciones"),
    ("derivar_departamento", "Derivar a un agente humano de un departamento"),
]

MARCADORES_DISPONIBLES = [
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


def crear_opcion(padre_id, texto_boton, tipo_accion, contenido_respuesta, departamento, orden) -> int:
    if not texto_boton or not texto_boton.strip():
        raise ValueError("Debe indicar el texto del botón/opción.")
    if tipo_accion not in dict(TIPOS_ACCION):
        raise ValueError("Tipo de acción no válido.")
    if tipo_accion == "derivar_departamento" and not departamento:
        raise ValueError("Debe indicar a qué departamento se deriva.")

    return ejecutar(
        "INSERT INTO whatsapp_flujo_opciones(padre_id, orden, texto_boton, tipo_accion, contenido_respuesta, departamento) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (padre_id or None, orden or 0, texto_boton.strip(), tipo_accion, contenido_respuesta or None, departamento or None),
    )


def actualizar_opcion(opcion_id, texto_boton, tipo_accion, contenido_respuesta, departamento, orden):
    if not texto_boton or not texto_boton.strip():
        raise ValueError("Debe indicar el texto del botón/opción.")
    if tipo_accion == "derivar_departamento" and not departamento:
        raise ValueError("Debe indicar a qué departamento se deriva.")

    ejecutar(
        "UPDATE whatsapp_flujo_opciones SET texto_boton=?, tipo_accion=?, contenido_respuesta=?, departamento=?, orden=? WHERE id=?",
        (texto_boton.strip(), tipo_accion, contenido_respuesta or None, departamento or None, orden or 0, opcion_id),
    )


def eliminar_opcion(opcion_id):
    # Al borrar una opcion, tambien se borran sus hijas (si era un submenu) -- para no dejar opciones huerfanas.
    hijas = consultar_todos("SELECT id FROM whatsapp_flujo_opciones WHERE padre_id=?", (opcion_id,))
    for hija in hijas:
        eliminar_opcion(dict(hija)["id"])
    ejecutar("DELETE FROM whatsapp_flujo_opciones WHERE id=?", (opcion_id,))


def desactivar_opcion(opcion_id):
    ejecutar("UPDATE whatsapp_flujo_opciones SET activo=0 WHERE id=?", (opcion_id,))


def activar_opcion(opcion_id):
    ejecutar("UPDATE whatsapp_flujo_opciones SET activo=1 WHERE id=?", (opcion_id,))
