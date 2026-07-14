"""HomeCare Enterprise - Router: Panel de Agente WhatsApp (chat en vivo)"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos

from services import whatsapp_agente_service as agente_service

router = APIRouter(prefix="/agente-whatsapp", tags=["Agente WhatsApp"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel(request: Request, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    return templates.TemplateResponse(
        request=request, name="agente_whatsapp/panel.html",
        context={"usuario": usuario},
    )


@router.get("/hilos")
async def api_listar_hilos(usuario=Depends(requiere_permiso("agente_whatsapp"))):
    return agente_service.listar_hilos(usuario.get("rol") if isinstance(usuario, dict) else None)


@router.get("/hilos/{hilo_id}")
async def api_hilo(hilo_id: int, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    hilo = agente_service.obtener_hilo(hilo_id)
    if not hilo:
        raise HTTPException(status_code=404, detail="La conversación no existe.")
    agente_service.marcar_leido(hilo_id)
    return {"hilo": hilo, "mensajes": agente_service.obtener_mensajes(hilo_id)}


@router.post("/hilos/{hilo_id}/tomar")
async def api_tomar(hilo_id: int, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    agente_service.tomar_conversacion(hilo_id, usuario.get("id") if isinstance(usuario, dict) else None)
    return {"ok": True}


@router.post("/hilos/{hilo_id}/devolver-a-bot")
async def api_devolver(hilo_id: int, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    agente_service.devolver_a_bot(hilo_id)
    return {"ok": True}


@router.post("/hilos/{hilo_id}/cerrar")
async def api_cerrar(hilo_id: int, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    agente_service.cerrar_conversacion(hilo_id)
    return {"ok": True}


@router.post("/hilos/{hilo_id}/enviar")
async def api_enviar(hilo_id: int, datos: dict, usuario=Depends(requiere_permiso("agente_whatsapp"))):
    try:
        resultado = agente_service.enviar_mensaje_agente(
            hilo_id, datos.get("texto", ""), usuario.get("id") if isinstance(usuario, dict) else None
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
