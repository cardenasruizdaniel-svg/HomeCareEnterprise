"""HomeCare Enterprise - Router: Cargos"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services import cargos_service

router = APIRouter(prefix="/cargos", tags=["Cargos"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def listado(request: Request, usuario=Depends(requiere_permiso("nomina"))):
    return templates.TemplateResponse(
        request=request, name="cargos/lista.html",
        context={"usuario": usuario, "cargos": cargos_service.listar()},
    )


@router.get("/nuevo", response_class=HTMLResponse)
async def nuevo(request: Request, usuario=Depends(requiere_permiso("nomina"))):
    return templates.TemplateResponse(
        request=request, name="cargos/form.html",
        context={
            "usuario": usuario, "cargo": None,
            "sugeridos": cargos_service.CARGOS_SUGERIDOS_IPS_DOMICILIARIA,
        },
    )


@router.post("/guardar")
async def guardar(
    nombre: str = Form(...),
    descripcion: str = Form(""),
    tipo_contrato_sugerido: str = Form("POR_HORAS"),
    salario_base: float = Form(0),
    valor_hora_base: float = Form(0),
    periodicidad_pago: str = Form("MENSUAL"),
    nivel_riesgo_arl: str = Form("I"),
    documentos_requeridos: str = Form(""),
    _actor=Depends(requiere_permiso("nomina")),
):
    cargos_service.crear({
        "nombre": nombre, "descripcion": descripcion,
        "tipo_contrato_sugerido": tipo_contrato_sugerido,
        "salario_base": salario_base, "valor_hora_base": valor_hora_base,
        "periodicidad_pago": periodicidad_pago, "nivel_riesgo_arl": nivel_riesgo_arl,
        "documentos_requeridos": documentos_requeridos,
    })
    return RedirectResponse(url="/cargos", status_code=303)


@router.get("/editar/{id}", response_class=HTMLResponse)
async def editar(request: Request, id: int, usuario=Depends(requiere_permiso("nomina"))):
    return templates.TemplateResponse(
        request=request, name="cargos/form.html",
        context={
            "usuario": usuario, "cargo": cargos_service.obtener(id),
            "sugeridos": cargos_service.CARGOS_SUGERIDOS_IPS_DOMICILIARIA,
        },
    )


@router.post("/editar/{id}")
async def actualizar(
    id: int,
    nombre: str = Form(...),
    descripcion: str = Form(""),
    tipo_contrato_sugerido: str = Form("POR_HORAS"),
    salario_base: float = Form(0),
    valor_hora_base: float = Form(0),
    periodicidad_pago: str = Form("MENSUAL"),
    nivel_riesgo_arl: str = Form("I"),
    documentos_requeridos: str = Form(""),
    _actor=Depends(requiere_permiso("nomina")),
):
    cargos_service.actualizar(id, {
        "nombre": nombre, "descripcion": descripcion,
        "tipo_contrato_sugerido": tipo_contrato_sugerido,
        "salario_base": salario_base, "valor_hora_base": valor_hora_base,
        "periodicidad_pago": periodicidad_pago, "nivel_riesgo_arl": nivel_riesgo_arl,
        "documentos_requeridos": documentos_requeridos,
    })
    return RedirectResponse(url="/cargos", status_code=303)


@router.get("/desactivar/{id}")
async def desactivar(id: int, _actor=Depends(requiere_permiso("nomina"))):
    cargos_service.desactivar(id)
    return RedirectResponse(url="/cargos", status_code=303)
