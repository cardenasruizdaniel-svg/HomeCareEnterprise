"""HomeCare Enterprise - Router: Configuración de la Empresa"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso, usuario_actual
from core.templates import templates

from services import configuracion_empresa_service as config_service

router = APIRouter(prefix="/configuracion-empresa", tags=["Configuración de la Empresa"])


def _requiere_administrador_maestro(usuario=Depends(usuario_actual)):
    """
    El reinicio de la base de datos es una accion irreversible
    y destructiva -- por eso queda restringida al rol exacto
    "Administrador" (el administrador maestro), y no a
    cualquier otro rol que tambien tenga acceso total
    (Coordinador, Director Médico, etc.).
    """
    if not usuario or usuario.get("rol") != "Administrador":
        raise HTTPException(status_code=403, detail="Esta acción solo la puede hacer el Administrador maestro.")
    return usuario


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def ver(request: Request, usuario=Depends(requiere_permiso("usuarios"))):
    return templates.TemplateResponse(
        request=request, name="configuracion_empresa/formulario.html",
        context={
            "usuario": usuario, "config": config_service.obtener(),
            "es_administrador_maestro": isinstance(usuario, dict) and usuario.get("rol") == "Administrador",
        },
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
            context={
                "usuario": usuario, "config": config_service.obtener(), "error": str(error),
                "es_administrador_maestro": isinstance(usuario, dict) and usuario.get("rol") == "Administrador",
            },
        )

    return RedirectResponse(url="/configuracion-empresa?guardado=1", status_code=303)


@router.post("/reiniciar-base-datos")
async def reiniciar_base_datos(
    confirmacion: str = Form(""),
    usuario=Depends(_requiere_administrador_maestro),
):
    if confirmacion != "REINICIAR":
        return RedirectResponse(
            url="/configuracion-empresa?error_reinicio=Debe%20escribir%20REINICIAR%20para%20confirmar",
            status_code=303,
        )

    from services.reinicio_service import reiniciar_base_datos_en_blanco
    resultado = reiniciar_base_datos_en_blanco(usuario.get("id"))

    return RedirectResponse(
        url=f"/configuracion-empresa?reiniciado={resultado['tablas_vaciadas']}",
        status_code=303,
    )
