"""HomeCare Enterprise - Router: Panel de Agente WhatsApp (chat en vivo)"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos

from services import whatsapp_agente_service as agente_service

router = APIRouter(prefix="/agente-whatsapp", tags=["Agente WhatsApp"])


def _id_usuario(usuario):
    return usuario.get("id") if isinstance(usuario, dict) else None


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel(request: Request, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    return templates.TemplateResponse(
        request=request, name="agente_whatsapp/panel.html",
        context={"usuario": usuario},
    )


# ==========================================================
# LISTADOS: en espera / mis conversaciones
# ==========================================================

@router.get("/hilos/en-espera")
async def api_hilos_en_espera(usuario=Depends(requiere_permiso("agente_whatsapp"))):
    agente_service.marcar_presencia(_id_usuario(usuario))
    return agente_service.listar_hilos_en_espera(usuario.get("rol") if isinstance(usuario, dict) else None)


@router.get("/hilos/mias")
async def api_mis_hilos(usuario=Depends(requiere_permiso("agente_whatsapp"))):
    agente_service.marcar_presencia(_id_usuario(usuario))
    return agente_service.listar_mis_conversaciones(_id_usuario(usuario))


@router.get("/hilos")
async def api_listar_hilos(usuario=Depends(requiere_permiso("agente_whatsapp"))):
    """Se conserva por compatibilidad."""
    return agente_service.listar_hilos(usuario.get("rol") if isinstance(usuario, dict) else None)


@router.get("/agentes-conectados")
async def api_agentes_conectados(usuario=Depends(requiere_permiso("agente_whatsapp"))):
    return agente_service.listar_agentes_conectados()


# ==========================================================
# RESPUESTAS RÁPIDAS
# ==========================================================

@router.get("/respuestas-rapidas")
async def api_listar_respuestas_rapidas(usuario=Depends(requiere_permiso("agente_whatsapp"))):
    return agente_service.listar_respuestas_rapidas()


@router.get("/respuestas-rapidas/administrar", response_class=HTMLResponse)
async def ver_respuestas_rapidas(request: Request, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    return templates.TemplateResponse(
        request=request, name="agente_whatsapp/respuestas_rapidas.html",
        context={
            "usuario": usuario, "respuestas": agente_service.listar_todas_respuestas_rapidas(),
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/respuestas-rapidas/crear")
async def crear_respuesta_rapida(
    request: Request,
    titulo: str = Form(...),
    texto: str = Form(...),
    categoria: str = Form("General"),
    orden: str = Form("0"),
    usuario=Depends(requiere_permiso("chatbot_whatsapp")),
):
    try:
        agente_service.crear_respuesta_rapida(titulo, texto, categoria, int(orden or 0), _id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/agente-whatsapp/respuestas-rapidas/administrar?error={error}", status_code=303)
    return RedirectResponse(url="/agente-whatsapp/respuestas-rapidas/administrar?guardado=1", status_code=303)


@router.post("/respuestas-rapidas/{respuesta_id}/actualizar")
async def actualizar_respuesta_rapida(
    request: Request,
    respuesta_id: int,
    titulo: str = Form(...),
    texto: str = Form(...),
    categoria: str = Form("General"),
    orden: str = Form("0"),
    usuario=Depends(requiere_permiso("chatbot_whatsapp")),
):
    try:
        agente_service.actualizar_respuesta_rapida(respuesta_id, titulo, texto, categoria, int(orden or 0))
    except ValueError as error:
        return RedirectResponse(url=f"/agente-whatsapp/respuestas-rapidas/administrar?error={error}", status_code=303)
    return RedirectResponse(url="/agente-whatsapp/respuestas-rapidas/administrar?guardado=1", status_code=303)


@router.post("/respuestas-rapidas/{respuesta_id}/desactivar")
async def desactivar_respuesta_rapida(respuesta_id: int, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    agente_service.desactivar_respuesta_rapida(respuesta_id)
    return RedirectResponse(url="/agente-whatsapp/respuestas-rapidas/administrar?guardado=1", status_code=303)


@router.post("/respuestas-rapidas/{respuesta_id}/activar")
async def activar_respuesta_rapida(respuesta_id: int, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    agente_service.activar_respuesta_rapida(respuesta_id)
    return RedirectResponse(url="/agente-whatsapp/respuestas-rapidas/administrar?guardado=1", status_code=303)


@router.get("/hilos/{hilo_id}")
async def api_hilo(hilo_id: int, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    hilo = agente_service.obtener_hilo(hilo_id)
    if not hilo:
        raise HTTPException(status_code=404, detail="La conversación no existe.")
    agente_service.marcar_leido(hilo_id)
    return {
        "hilo": hilo,
        "mensajes": agente_service.obtener_mensajes(hilo_id),
        "transferencias": agente_service.historial_transferencias(hilo_id),
    }


# ==========================================================
# ACCIONES: aceptar / transferir / finalizar / devolver al bot
# ==========================================================

@router.post("/hilos/{hilo_id}/tomar")
async def api_tomar(hilo_id: int, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    agente_service.tomar_conversacion(hilo_id, _id_usuario(usuario))
    return {"ok": True}


@router.post("/hilos/{hilo_id}/transferir")
async def api_transferir(hilo_id: int, datos: dict, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    try:
        agente_service.transferir_conversacion(
            hilo_id, _id_usuario(usuario), datos.get("a_agente_id"), datos.get("motivo", "")
        )
        return {"ok": True}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/hilos/{hilo_id}/finalizar")
async def api_finalizar(hilo_id: int, datos: dict, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    try:
        agente_service.finalizar_conversacion(hilo_id, con_respuesta=bool(datos.get("con_respuesta")))
        return {"ok": True}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/hilos/{hilo_id}/devolver-a-bot")
async def api_devolver(hilo_id: int, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    agente_service.devolver_a_bot(hilo_id)
    return {"ok": True}


@router.post("/hilos/{hilo_id}/cerrar")
async def api_cerrar(hilo_id: int, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    """Se conserva por compatibilidad -- equivale a finalizar sin respuesta."""
    agente_service.cerrar_conversacion(hilo_id)
    return {"ok": True}


@router.post("/hilos/{hilo_id}/etiquetas")
async def api_etiquetas(hilo_id: int, datos: dict, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    agente_service.actualizar_etiquetas(hilo_id, datos.get("etiquetas", []))
    return {"ok": True}


# ==========================================================
# MENSAJES: texto, archivos, accesos rápidos
# ==========================================================

@router.post("/hilos/{hilo_id}/enviar")
async def api_enviar(hilo_id: int, datos: dict, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    try:
        resultado = agente_service.enviar_mensaje_agente(hilo_id, datos.get("texto", ""), _id_usuario(usuario))
        return {"ok": True, "envio": resultado}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/hilos/{hilo_id}/enviar-archivo")
async def api_enviar_archivo(hilo_id: int, datos: dict, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    try:
        resultado = agente_service.enviar_archivo_agente(
            hilo_id, datos.get("archivo_base64", ""), datos.get("nombre_archivo", "archivo"), _id_usuario(usuario)
        )
        return {"ok": True, "envio": resultado}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/hilos/{hilo_id}/enviar-orden")
async def api_enviar_orden(hilo_id: int, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    try:
        resultado = agente_service.enviar_ultima_orden(hilo_id)
        return {"ok": True, "envio": resultado}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/hilos/{hilo_id}/enviar-recomendacion")
async def api_enviar_recomendacion(hilo_id: int, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    try:
        resultado = agente_service.enviar_ultima_recomendacion(hilo_id)
        return {"ok": True, "envio": resultado}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/buscar-pacientes")
async def api_buscar_pacientes(q: str = "", usuario=Depends(requiere_permiso("agente_whatsapp"))):
    if not q or len(q) < 2:
        return []
    filas = consultar_todos(
        "SELECT id, documento, primer_nombre, primer_apellido FROM pacientes "
        "WHERE (primer_nombre LIKE ? OR primer_apellido LIKE ? OR documento LIKE ?) AND UPPER(estado)='ACTIVO' LIMIT 10",
        (f"%{q}%", f"%{q}%", f"%{q}%"),
    )
    return [dict(f) for f in filas]


@router.post("/hilos/{hilo_id}/vincular-paciente/{paciente_id}")
async def api_vincular_paciente(hilo_id: int, paciente_id: int, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    agente_service.vincular_paciente(hilo_id, paciente_id)
    return {"ok": True}


# ==========================================================
# CONFIGURACIÓN: contactos internos de la empresa
# ==========================================================

@router.get("/contactos-internos", response_class=HTMLResponse)
async def ver_contactos_internos(request: Request, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    return templates.TemplateResponse(
        request=request, name="agente_whatsapp/contactos_internos.html",
        context={
            "usuario": usuario, "contactos": agente_service.listar_contactos_internos(),
            "guardado": request.query_params.get("guardado"),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/contactos-internos/crear")
async def crear_contacto_interno(
    request: Request,
    nombre: str = Form(...),
    numero_celular: str = Form(...),
    area: str = Form(""),
    usuario=Depends(requiere_permiso("chatbot_whatsapp")),
):
    try:
        agente_service.crear_contacto_interno(nombre, numero_celular, area, _id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/agente-whatsapp/contactos-internos?error={error}", status_code=303)
    return RedirectResponse(url="/agente-whatsapp/contactos-internos?guardado=1", status_code=303)


@router.post("/contactos-internos/{contacto_id}/desactivar")
async def desactivar_contacto_interno(contacto_id: int, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    agente_service.desactivar_contacto_interno(contacto_id)
    return RedirectResponse(url="/agente-whatsapp/contactos-internos?guardado=1", status_code=303)
