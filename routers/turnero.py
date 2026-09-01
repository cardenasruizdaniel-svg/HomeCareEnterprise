"""HomeCare Enterprise - Router: Turnero HomeCare (motor de turnos)"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services import turnero_service as t

router = APIRouter(prefix="/turnero", tags=["Turnero HomeCare"])


def _id_usuario(usuario):
    return usuario.get("id") if isinstance(usuario, dict) else None


# ==========================================================
# DASHBOARD
# ==========================================================

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, usuario=Depends(requiere_permiso("turnero"))):
    return templates.TemplateResponse(
        request=request, name="turnero/dashboard.html",
        context={
            "usuario": usuario, "resumen": t.resumen_dashboard(),
            "servicios": t.listar_servicios(solo_activos=True), "modulos": t.listar_modulos(solo_activos=True),
        },
    )


# ==========================================================
# ADMINISTRACIÓN -- SERVICIOS
# ==========================================================

@router.get("/servicios", response_class=HTMLResponse)
async def servicios_lista(request: Request, usuario=Depends(requiere_permiso("turnero"))):
    return templates.TemplateResponse(
        request=request, name="turnero/servicios_lista.html",
        context={"usuario": usuario, "servicios": t.listar_servicios(), "error": request.query_params.get("error")},
    )


@router.post("/servicios/crear")
async def servicios_crear(request: Request, usuario=Depends(requiere_permiso("turnero"))):
    datos = dict(await request.form())
    try:
        t.crear_servicio(datos, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/turnero/servicios?error={error}", status_code=303)
    return RedirectResponse(url="/turnero/servicios?guardado=1", status_code=303)


@router.post("/servicios/{servicio_id}/desactivar")
async def servicios_desactivar(servicio_id: int, usuario=Depends(requiere_permiso("turnero"))):
    t.desactivar_servicio(servicio_id)
    return RedirectResponse(url="/turnero/servicios?guardado=1", status_code=303)


@router.post("/servicios/{servicio_id}/reactivar")
async def servicios_reactivar(servicio_id: int, usuario=Depends(requiere_permiso("turnero"))):
    t.reactivar_servicio(servicio_id)
    return RedirectResponse(url="/turnero/servicios?guardado=1", status_code=303)


# ==========================================================
# ADMINISTRACIÓN -- MÓDULOS DE ATENCIÓN
# ==========================================================

@router.get("/modulos", response_class=HTMLResponse)
async def modulos_lista(request: Request, usuario=Depends(requiere_permiso("turnero"))):
    from services import usuarios_service
    return templates.TemplateResponse(
        request=request, name="turnero/modulos_lista.html",
        context={
            "usuario": usuario, "modulos": t.listar_modulos(), "servicios": t.listar_servicios(solo_activos=True),
            "tipos": t.TIPOS_MODULO, "usuarios_sistema": usuarios_service.listar_usuarios(),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/modulos/crear")
async def modulos_crear(request: Request, usuario=Depends(requiere_permiso("turnero"))):
    datos = dict(await request.form())
    try:
        t.crear_modulo(datos)
    except ValueError as error:
        return RedirectResponse(url=f"/turnero/modulos?error={error}", status_code=303)
    return RedirectResponse(url="/turnero/modulos?guardado=1", status_code=303)


@router.post("/modulos/{modulo_id}/desactivar")
async def modulos_desactivar(modulo_id: int, usuario=Depends(requiere_permiso("turnero"))):
    t.desactivar_modulo(modulo_id)
    return RedirectResponse(url="/turnero/modulos?guardado=1", status_code=303)


@router.post("/modulos/{modulo_id}/reactivar")
async def modulos_reactivar(modulo_id: int, usuario=Depends(requiere_permiso("turnero"))):
    t.reactivar_modulo(modulo_id)
    return RedirectResponse(url="/turnero/modulos?guardado=1", status_code=303)


# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

@router.get("/configuracion", response_class=HTMLResponse)
async def configuracion_ver(request: Request, usuario=Depends(requiere_permiso("turnero"))):
    return templates.TemplateResponse(
        request=request, name="turnero/configuracion.html",
        context={"usuario": usuario, "config": t.obtener_configuracion(), "guardado": request.query_params.get("guardado")},
    )


@router.post("/configuracion/guardar")
async def configuracion_guardar(request: Request, usuario=Depends(requiere_permiso("turnero"))):
    datos = dict(await request.form())
    t.guardar_configuracion(datos)
    return RedirectResponse(url="/turnero/configuracion?guardado=1", status_code=303)


# ==========================================================
# REGISTRAR TURNO (presencial, desde recepción)
# ==========================================================

@router.get("/registrar", response_class=HTMLResponse)
async def registrar_ver(request: Request, usuario=Depends(requiere_permiso("turnero"))):
    return templates.TemplateResponse(
        request=request, name="turnero/registrar.html",
        context={
            "usuario": usuario, "servicios": t.listar_servicios(solo_activos=True),
            "error": request.query_params.get("error"), "turno_creado": None,
        },
    )


@router.post("/registrar")
async def registrar_crear(request: Request, usuario=Depends(requiere_permiso("turnero"))):
    formulario = dict(await request.form())
    try:
        turno = t.crear_turno(formulario, usuario_id=_id_usuario(usuario), canal="Presencial")
    except ValueError as error:
        return RedirectResponse(url=f"/turnero/registrar?error={error}", status_code=303)
    return templates.TemplateResponse(
        request=request, name="turnero/registrar.html",
        context={"usuario": usuario, "servicios": t.listar_servicios(solo_activos=True), "error": None, "turno_creado": turno},
    )


# ==========================================================
# PANTALLA DEL OPERADOR (consultorio / ventanilla)
# ==========================================================

@router.get("/operador/{modulo_id}", response_class=HTMLResponse)
async def operador_ver(request: Request, modulo_id: int, usuario=Depends(requiere_permiso("turnero"))):
    modulo = t.obtener_modulo(modulo_id)
    if not modulo:
        raise HTTPException(status_code=404, detail="El módulo no existe.")

    from database.database import consultar_uno
    fila = consultar_uno(
        "SELECT id FROM turnero_turnos WHERE modulo_id=? AND estado IN ('Llamado','En atención') ORDER BY hora_llamado DESC LIMIT 1",
        (modulo_id,),
    )
    turno_actual = t.obtener_turno(dict(fila)["id"]) if fila else None

    return templates.TemplateResponse(
        request=request, name="turnero/operador.html",
        context={
            "usuario": usuario, "modulo": modulo, "turno_actual": turno_actual,
            "servicios": t.listar_servicios(solo_activos=True),
            "en_espera": len(t.cola_en_espera(modulo.get("servicio_id"))) if modulo.get("servicio_id") else 0,
        },
    )


@router.post("/operador/{modulo_id}/llamar-siguiente")
async def operador_llamar_siguiente(modulo_id: int, servicio_id: int = Form(...), usuario=Depends(requiere_permiso("turnero"))):
    t.llamar_siguiente(servicio_id, modulo_id, usuario_id=_id_usuario(usuario))
    return RedirectResponse(url=f"/turnero/operador/{modulo_id}", status_code=303)


@router.post("/operador/{modulo_id}/rellamar/{turno_id}")
async def operador_rellamar(modulo_id: int, turno_id: int, usuario=Depends(requiere_permiso("turnero"))):
    t.rellamar(turno_id, usuario_id=_id_usuario(usuario))
    return RedirectResponse(url=f"/turnero/operador/{modulo_id}", status_code=303)


@router.post("/operador/{modulo_id}/iniciar-atencion/{turno_id}")
async def operador_iniciar_atencion(modulo_id: int, turno_id: int, usuario=Depends(requiere_permiso("turnero"))):
    t.iniciar_atencion(turno_id, usuario_id=_id_usuario(usuario))
    return RedirectResponse(url=f"/turnero/operador/{modulo_id}", status_code=303)


@router.post("/operador/{modulo_id}/finalizar/{turno_id}")
async def operador_finalizar(modulo_id: int, turno_id: int, usuario=Depends(requiere_permiso("turnero"))):
    t.finalizar_turno(turno_id, usuario_id=_id_usuario(usuario))
    return RedirectResponse(url=f"/turnero/operador/{modulo_id}", status_code=303)


@router.post("/operador/{modulo_id}/no-presentado/{turno_id}")
async def operador_no_presentado(modulo_id: int, turno_id: int, usuario=Depends(requiere_permiso("turnero"))):
    t.marcar_no_presentado(turno_id, usuario_id=_id_usuario(usuario))
    return RedirectResponse(url=f"/turnero/operador/{modulo_id}", status_code=303)


@router.post("/operador/{modulo_id}/transferir/{turno_id}")
async def operador_transferir(modulo_id: int, turno_id: int, nuevo_servicio_id: int = Form(...), usuario=Depends(requiere_permiso("turnero"))):
    try:
        t.transferir_turno(turno_id, nuevo_servicio_id, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/turnero/operador/{modulo_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/turnero/operador/{modulo_id}", status_code=303)


# ==========================================================
# PANTALLA PÚBLICA (para TV / monitor) -- sin necesidad de
# sesión, pensada para dejarse abierta permanentemente.
# ==========================================================

@router.get("/pantalla", response_class=HTMLResponse)
async def pantalla_publica(request: Request):
    return templates.TemplateResponse(request=request, name="turnero/pantalla.html", context={})


@router.get("/pantalla/datos")
async def pantalla_datos(request: Request):
    """Los datos que la pantalla consulta periódicamente (polling) para actualizarse sola."""
    ultimos = t.ultimos_llamados(limite=8)
    actual = ultimos[0] if ultimos else None
    return {
        "actual": actual,
        "ultimos": ultimos[1:6] if len(ultimos) > 1 else [],
        "config": t.obtener_configuracion(),
    }
