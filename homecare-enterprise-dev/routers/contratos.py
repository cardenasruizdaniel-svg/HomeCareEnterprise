"""HomeCare Enterprise - Router: Contratos"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos

from services import cargos_service, contratos_service

router = APIRouter(prefix="/contratos", tags=["Contratos"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def listado(request: Request, usuario=Depends(requiere_permiso("nomina"))):
    return templates.TemplateResponse(
        request=request, name="contratos/lista.html",
        context={"usuario": usuario, "contratos": contratos_service.listar()},
    )


@router.get("/nuevo", response_class=HTMLResponse)
async def nuevo(request: Request, usuario=Depends(requiere_permiso("nomina"))):
    profesionales = consultar_todos("SELECT * FROM profesionales WHERE estado='ACTIVO' ORDER BY primer_apellido")
    return templates.TemplateResponse(
        request=request, name="contratos/form.html",
        context={
            "usuario": usuario, "profesionales": profesionales,
            "cargos": cargos_service.listar(), "tipos_contrato": contratos_service.TIPOS_CONTRATO,
        },
    )


@router.post("/guardar")
async def guardar(
    profesional_id: int = Form(...),
    cargo_id: int = Form(...),
    tipo_contrato: str = Form(...),
    modalidad_pago: str = Form("POR_HORAS"),
    salario_mensual: float = Form(0),
    valor_hora: float = Form(0),
    periodicidad_pago: str = Form("MENSUAL"),
    fecha_inicio: str = Form(...),
    nivel_riesgo_arl: str = Form("I"),
    eps: str = Form(""),
    fondo_pension: str = Form(""),
    fondo_cesantias: str = Form(""),
    caja_compensacion: str = Form(""),
    observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("nomina")),
):
    contratos_service.crear({
        "profesional_id": profesional_id, "cargo_id": cargo_id, "tipo_contrato": tipo_contrato,
        "modalidad_pago": modalidad_pago, "salario_mensual": salario_mensual, "valor_hora": valor_hora,
        "periodicidad_pago": periodicidad_pago, "fecha_inicio": fecha_inicio,
        "nivel_riesgo_arl": nivel_riesgo_arl, "eps": eps, "fondo_pension": fondo_pension,
        "fondo_cesantias": fondo_cesantias, "caja_compensacion": caja_compensacion,
        "observaciones": observaciones,
    }, usuario=usuario.get("id") if isinstance(usuario, dict) else None)
    return RedirectResponse(url="/contratos", status_code=303)


@router.get("/detalle/{id}", response_class=HTMLResponse)
async def detalle(request: Request, id: int, usuario=Depends(requiere_permiso("nomina"))):
    contrato = dict(contratos_service.obtener(id))
    liquidacion = None
    if contrato["tipo_contrato"] != "Prestación de servicios" and contrato.get("salario_mensual"):
        liquidacion = contratos_service.liquidacion_prestacional(
            contrato["salario_mensual"], contrato.get("nivel_riesgo_arl", "I")
        )
    return templates.TemplateResponse(
        request=request, name="contratos/detalle.html",
        context={"usuario": usuario, "contrato": contrato, "liquidacion": liquidacion},
    )


@router.get("/finalizar/{id}")
async def finalizar(id: int, _actor=Depends(requiere_permiso("nomina"))):
    from datetime import date
    contratos_service.finalizar(id, date.today().isoformat())
    return RedirectResponse(url="/contratos", status_code=303)
