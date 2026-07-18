"""
=========================================================
HomeCare Enterprise
Router de Asignación Inteligente
Sprint 3.4
=========================================================
"""

from fastapi import APIRouter
from fastapi import Request
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from services.asignacion_service import AsignacionService

router = APIRouter(
    prefix="/asignacion",
    tags=["Asignación Inteligente"]
)

templates = Jinja2Templates(directory="templates")


# =====================================================
# DASHBOARD
# =====================================================

@router.get("")

@router.get("/")

def dashboard(request: Request):

    datos = AsignacionService.dashboard()

    return templates.TemplateResponse(

        "asignacion/dashboard.html",

        {

            "request": request,

            **datos

        }

    )


# =====================================================
# INDICADORES
# =====================================================

@router.get("/indicadores")

def indicadores():

    return JSONResponse(

        AsignacionService.indicadores()

    )


# =====================================================
# PROFESIONALES DISPONIBLES
# =====================================================

@router.get("/profesionales")

def profesionales():

    return JSONResponse(

        AsignacionService.profesionales()

    )


# =====================================================
# VISITAS PENDIENTES
# =====================================================

@router.get("/pendientes")

def pendientes():

    return JSONResponse(

        AsignacionService.visitas_pendientes()

    )


# =====================================================
# ASIGNACIÓN AUTOMÁTICA
# =====================================================

@router.post("/ejecutar")

def ejecutar():

    resultado = AsignacionService.asignacion_automatica()

    return JSONResponse(

        {

            "ok": True,

            "total": len(resultado),

            "resultado": resultado

        }

    )


# =====================================================
# ASIGNAR UNA VISITA
# =====================================================

@router.post("/{programacion_id}")

def asignar(programacion_id: int):

    visita = None

    for item in AsignacionService.visitas_pendientes():

        if item["id"] == programacion_id:

            visita = item

            break

    if visita is None:

        raise HTTPException(

            status_code=404,

            detail="Programación no encontrada"

        )

    resultado = AsignacionService.asignar_visita(

        visita

    )

    return JSONResponse(

        resultado

    )


# =====================================================
# HEALTH
# =====================================================

@router.get("/health")

def health():

    return {

        "modulo": "Asignación Inteligente",

        "estado": "OK",

        "version": "3.4"

    }