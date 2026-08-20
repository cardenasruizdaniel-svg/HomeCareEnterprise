from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from core.audit import registrar_auditoria

from core.templates import templates
from services.auth_service import AuthService

router = APIRouter(tags=["Autenticación"])


@router.get("/login")
async def login(request: Request):

    mensaje_inactividad = (
        "Su sesión se cerró automáticamente por 20 minutos de inactividad. Ingrese de nuevo para continuar."
        if request.query_params.get("motivo") == "inactividad" else None
    )

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "error": None,
            "aviso": mensaje_inactividad,
        },
    )


@router.post("/login")
async def login_post(
    request: Request,
    usuario: str = Form(...),
    password: str = Form(...),
):

    datos = AuthService.autenticar(
        usuario,
        password,
    )

    if datos is None:

        registrar_auditoria(
            usuario=usuario, modulo="Autenticación", accion="Login fallido",
            descripcion=f"Intento de inicio de sesión con credenciales incorrectas para el usuario '{usuario}'.",
            ip=request.client.host if request.client else "", navegador=request.headers.get("user-agent", ""),
            resultado="Advertencia",
        )

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "error": "Usuario o contraseña incorrectos.",
            },
        )

    # El rol Cuidador solo puede ingresar desde la app móvil de
    # campo -- no tiene acceso a la plataforma web, por
    # seguridad y porque todas sus tareas (informes de cuidado,
    # registro de ingreso/salida) ya están cubiertas ahí.
    if datos["rol"] == "Cuidador":
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "error": "Este usuario es de tipo Cuidador y solo puede ingresar desde la aplicación móvil, no desde esta página web.",
            },
        )

    request.session["usuario_id"] = datos["id"]
    request.session["usuario"] = datos["usuario"]
    request.session["nombre"] = datos["nombre"]
    request.session["rol"] = datos["rol"]

    registrar_auditoria(

    usuario_id=datos["id"],

    usuario=datos["usuario"],

    rol=datos["rol"],

    modulo="Autenticación",

    accion="Login",

    descripcion="Inicio de sesión",

    ip=request.client.host if request.client else "",

    navegador=request.headers.get("user-agent", "")

)

    return RedirectResponse(
        url="/",
        status_code=302,
    )


@router.get("/logout")
async def logout(request: Request, motivo: str = None):

    es_por_inactividad = motivo == "inactividad"

    registrar_auditoria(

    usuario_id=request.session.get("usuario_id"),

    usuario=request.session.get("usuario"),

    rol=request.session.get("rol"),

    modulo="Autenticación",

    accion="Logout por inactividad" if es_por_inactividad else "Logout",

    descripcion="Cierre de sesión automático por 20 minutos de inactividad" if es_por_inactividad else "Cierre de sesión",

    ip=request.client.host if request.client else "",

    navegador=request.headers.get("user-agent", "")

)

    request.session.clear()

    return RedirectResponse(
        url="/login?motivo=inactividad" if es_por_inactividad else "/login",
        status_code=302,
    )