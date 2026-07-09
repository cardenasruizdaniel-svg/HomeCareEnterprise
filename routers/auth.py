from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from core.audit import registrar_auditoria

from core.templates import templates
from services.auth_service import AuthService

router = APIRouter(tags=["Autenticación"])


@router.get("/login")
async def login(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "error": None,
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

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "error": "Usuario o contraseña incorrectos.",
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
async def logout(request: Request):

    registrar_auditoria(

    usuario_id=request.session.get("usuario_id"),

    usuario=request.session.get("usuario"),

    rol=request.session.get("rol"),

    modulo="Autenticación",

    accion="Logout",

    descripcion="Cierre de sesión",

    ip=request.client.host if request.client else "",

    navegador=request.headers.get("user-agent", "")

)

    request.session.clear()

    return RedirectResponse(
        url="/login",
        status_code=302,
    )