"""
=========================================================
HomeCare Enterprise
Dashboard Router
Sprint 3.4C
=========================================================
"""

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from services.dashboard_service import DashboardService
from core.dependencies import usuario_actual
from core.dependencies import requiere_permiso
from core.templates import templates


router = APIRouter()

dashboard_service = DashboardService()

# =====================================================
# DASHBOARD
# =====================================================

@router.get(
    "/",
    response_class=HTMLResponse,
)
async def dashboard(
    request: Request,
    fecha_desde_ordenes: str = None,
    fecha_hasta_ordenes: str = None,
):

    # ==========================================
    # REQUIERE SESIÓN INICIADA
    # ==========================================

    if not request.session.get("usuario_id"):
        return RedirectResponse(url="/login", status_code=303)

    usuario = usuario_actual(request)

    contexto = dashboard_service.dashboard_context()

    from services.dashboard_operativo_service import panel_operativo_completo
    contexto["panel_operativo"] = panel_operativo_completo()

    contexto["gerencial"] = dashboard_service.resumen_gerencial()

    contexto["produccion_detallada"] = dashboard_service.grafico_produccion_detallado()
    contexto["cumplimiento_historico"] = dashboard_service.grafico_cumplimiento_historico(6)
    contexto["altas_bajas"] = dashboard_service.grafico_altas_bajas(6)

    from datetime import date
    from services.ordenes_service import OrdenesService
    hoy = date.today().isoformat()
    contexto["ordenes_fecha_desde"] = fecha_desde_ordenes or hoy
    contexto["ordenes_fecha_hasta"] = fecha_hasta_ordenes or hoy
    contexto["ordenes_medicas_dashboard"] = OrdenesService.listar_por_rango_fechas(
        contexto["ordenes_fecha_desde"], contexto["ordenes_fecha_hasta"]
    )

    contexto["request"] = request

    contexto["usuario"] = usuario

    return templates.TemplateResponse(
    request=request,
    name="dashboard/index.html",
    context=contexto,
)

# =====================================================
# DASHBOARD DATA
# =====================================================

@router.get(
    "/dashboard",
)

async def dashboard_data():

    return dashboard_service.dashboard_context()

# =====================================================
# DASHBOARD KPIs
# =====================================================

@router.get(
    "/dashboard/kpis",
)

async def dashboard_kpis():

    return dashboard_service.indicadores_dashboard()

# =====================================================
# DASHBOARD AGENDA
# =====================================================

@router.get(
    "/dashboard/agenda",
)

async def dashboard_agenda():

    return dashboard_service.agenda_dashboard()

# =====================================================
# DASHBOARD ALERTAS
# =====================================================

@router.get(
    "/dashboard/alertas",
)

async def dashboard_alertas():

    return dashboard_service.alertas_dashboard()

# =====================================================
# PRODUCCIÓN MENSUAL
# =====================================================

@router.get(
    "/dashboard/produccion",
)

async def dashboard_produccion():

    return dashboard_service.grafico_produccion()

# =====================================================
# RESUMEN EJECUTIVO
# =====================================================

@router.get(
    "/dashboard/resumen",
)

async def dashboard_resumen():

    return dashboard_service.resumen_ejecutivo()

# =====================================================
# CONTEXTO
# =====================================================

@router.get(
    "/dashboard/contexto",
)

async def dashboard_contexto():

    return dashboard_service.dashboard_context()

# =====================================================
# ESTADO DEL DASHBOARD
# =====================================================

@router.get(
    "/dashboard/status",
)

async def dashboard_status():

    return {

        "status": "online",

        "version": "10.0.0",

        "modulo": "Dashboard Enterprise",

    }