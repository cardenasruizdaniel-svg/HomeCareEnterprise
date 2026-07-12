"""HomeCare Enterprise - Router: Configuración Legal / Cumplimiento Normativo"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from core.config import BASE_DIR
from core.dependencies import requiere_permiso
from core.templates import templates

from services import configuracion_legal_service as legal_service

router = APIRouter(prefix="/configuracion-legal", tags=["Configuración Legal"])


@router.get("/manual-pdf")
async def descargar_manual_legal(usuario=Depends(requiere_permiso("usuarios"))):
    ruta = BASE_DIR / "docs" / "manuales" / "MANUAL_CONFIGURACION_LEGAL.pdf"
    return FileResponse(ruta, media_type="application/pdf", filename="Manual_Configuracion_Legal_HomeCare.pdf")


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def ver(request: Request, usuario=Depends(requiere_permiso("usuarios"))):
    config = legal_service.obtener()
    # Los campos sensibles nunca se muestran de vuelta en texto plano
    for campo in legal_service.CAMPOS_SENSIBLES:
        config[campo] = ""
    config["_dian_certificado_password_configurada"] = bool(legal_service.obtener().get("dian_certificado_password"))
    config["_pila_clave_configurada"] = bool(legal_service.obtener().get("pila_clave"))

    return templates.TemplateResponse(
        request=request, name="configuracion_legal/formulario.html",
        context={
            "usuario": usuario, "config": config,
            "resumen": legal_service.resumen_estado(),
            "guardado": request.query_params.get("guardado"),
        },
    )


@router.post("/guardar")
async def guardar(
    request: Request,
    reps_codigo_habilitacion: str = Form(""), reps_numero_habilitacion: str = Form(""),
    reps_fecha_habilitacion: str = Form(""), reps_vigencia_hasta: str = Form(""),
    rips_nit_prestador: str = Form(""), rips_codigo_prestador: str = Form(""), rips_razon_social: str = Form(""),
    dian_nit: str = Form(""), dian_digito_verificacion: str = Form(""),
    dian_resolucion_numero: str = Form(""), dian_resolucion_prefijo: str = Form(""),
    dian_resolucion_rango_desde: str = Form(""), dian_resolucion_rango_hasta: str = Form(""),
    dian_resolucion_fecha_desde: str = Form(""), dian_resolucion_fecha_hasta: str = Form(""),
    dian_software_id: str = Form(""), dian_software_pin: str = Form(""),
    dian_certificado_nombre_archivo: str = Form(""), dian_certificado_base64: str = Form(""),
    dian_certificado_password: str = Form(""),
    dian_ambiente: str = Form("Habilitación"), dian_test_set_id: str = Form(""),
    dian_nomina_software_id: str = Form(""), dian_nomina_software_pin: str = Form(""),
    dian_nomina_ambiente: str = Form("Habilitación"), dian_nomina_test_set_id: str = Form(""),
    pila_operador: str = Form(""), pila_usuario: str = Form(""), pila_clave: str = Form(""),
    sic_numero_registro_rnbd: str = Form(""), sic_fecha_registro: str = Form(""),
    arl_nit: str = Form(""), arl_nombre: str = Form(""),
    usuario=Depends(requiere_permiso("usuarios")),
):
    legal_service.guardar(
        {k: v for k, v in locals().items() if k not in ("request", "usuario") and not k.startswith("_")},
        usuario.get("id") if isinstance(usuario, dict) else None,
    )
    return RedirectResponse(url="/configuracion-legal?guardado=1", status_code=303)
