"""
=========================================================
HomeCare Enterprise
Plantillas Router
=========================================================
"""

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from services.plantilla_service import PlantillaService

router = APIRouter(
    prefix="/plantillas",
    tags=["Plantillas"]
)

templates = Jinja2Templates(
    directory="templates"
)

service = PlantillaService()


# =====================================================
# LISTADO
# =====================================================

@router.get(
    "/",
    response_class=HTMLResponse
)
async def listar_plantillas(
    request: Request
):

    plantillas = service.listar()

    return templates.TemplateResponse(

        request=request,

        name="configuracion/plantillas.html",

        context={

            "plantillas": plantillas

        }

    )

# =====================================================
# NUEVA PLANTILLA
# =====================================================

@router.get(

    "/nueva",

    response_class=HTMLResponse

)

async def nueva_plantilla(

    request: Request

):

    return templates.TemplateResponse(

        request=request,

        name="configuracion/nueva_plantilla.html",

        context={}

    )

from fastapi import Form
from fastapi.responses import RedirectResponse


# =====================================================
# GUARDAR PLANTILLA
# =====================================================

@router.post("/")

async def guardar_plantilla(

    nombre: str = Form(...),

    categoria: str = Form(...),

    especialidad: str = Form(...),

    tipo_profesional: str = Form(...),

    servicio: str = Form(...)

):

    # Usuario temporal
    usuario = 1

    service.crear(

        nombre,

        categoria,

        especialidad,

        tipo_profesional,

        servicio,

        usuario

    )

    return RedirectResponse(

        url="/plantillas",

        status_code=303

    )

# =====================================================
# EDITOR VISUAL
# =====================================================

@router.get(

    "/{plantilla_id}/editor",

    response_class=HTMLResponse

)

async def editor_plantilla(

    request: Request,

    plantilla_id: int

):

    return templates.TemplateResponse(

        request=request,

        name="configuracion/editor_plantilla.html",

        context={

            "plantilla_id": plantilla_id

        }

    )

# =====================================================
# API COMPONENTES
# =====================================================

@router.get(

    "/api/componentes",

    response_class=JSONResponse

)

async def api_componentes():

    datos = service.componentes()

    return [

        dict(x)

        for x in datos

    ]