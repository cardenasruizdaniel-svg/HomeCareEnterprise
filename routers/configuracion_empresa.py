"""HomeCare Enterprise - Router: Configuración de la Empresa"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services import configuracion_empresa_service as config_service

router = APIRouter(prefix="/configuracion-empresa", tags=["Configuración de la Empresa"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def ver(request: Request, usuario=Depends(requiere_permiso("usuarios"))):
    return templates.TemplateResponse(
        request=request, name="configuracion_empresa/formulario.html",
        context={"usuario": usuario, "config": config_service.obtener()},
    )


@router.post("/guardar")
async def guardar(
    request: Request,
    razon_social: str = Form(...),
    nit: str = Form(""),
    resolucion_habilitacion: str = Form(""),
    direccion: str = Form(""),
    telefono: str = Form(""),
    correo: str = Form(""),
    ciudad: str = Form(""),
    departamento: str = Form(""),
    representante_legal: str = Form(""),
    logo_base64: str = Form(""),
    usuario=Depends(requiere_permiso("usuarios")),
):
    try:
        config_service.guardar({
            "razon_social": razon_social, "nit": nit,
            "resolucion_habilitacion": resolucion_habilitacion,
            "direccion": direccion, "telefono": telefono, "correo": correo,
            "ciudad": ciudad, "departamento": departamento,
            "representante_legal": representante_legal,
            "logo_base64": logo_base64 or None,
        }, usuario.get("id") if isinstance(usuario, dict) else None)
    except ValueError as error:
        return templates.TemplateResponse(
            request=request, name="configuracion_empresa/formulario.html",
            context={"usuario": usuario, "config": config_service.obtener(), "error": str(error)},
        )

    return RedirectResponse(url="/configuracion-empresa?guardado=1", status_code=303)
