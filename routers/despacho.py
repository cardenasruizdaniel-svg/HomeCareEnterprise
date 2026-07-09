"""
==========================================================
HomeCare Enterprise
Centro de Despacho Inteligente
Router de Despacho
==========================================================
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from services.despacho_service import DespachoService


router = APIRouter(
    prefix="/despacho",
    tags=["Centro de Despacho"]
)


# ==========================================================
# DASHBOARD
# ==========================================================

@router.get("/")
async def dashboard():

    return DespachoService.generar_despacho_diario()


@router.get("/indicadores")
async def indicadores():

    return DespachoService.indicadores()


# ==========================================================
# CONSULTAS
# ==========================================================

@router.get("/listar")
async def listar():

    return DespachoService.listar()


@router.get("/{despacho_id}")
async def obtener(despacho_id: int):

    despacho = DespachoService.obtener(despacho_id)

    if not despacho:
        raise HTTPException(
            status_code=404,
            detail="Despacho no encontrado."
        )

    return despacho


@router.get("/profesional/{profesional_id}")
async def profesional(
    profesional_id: int,
    fecha: str = Query(...)
):

    return DespachoService.por_profesional(
        profesional_id,
        fecha,
    )


@router.get("/pendientes")
async def pendientes():

    return DespachoService.pendientes()


@router.get("/en-ruta")
async def en_ruta():

    return DespachoService.en_ruta()


# ==========================================================
# CREACIÓN
# ==========================================================

@router.post("/crear")
async def crear(datos: dict):

    return DespachoService.crear(datos)


# ==========================================================
# ASIGNACIÓN
# ==========================================================

@router.put("/{despacho_id}/asignar/{profesional_id}")
async def asignar(
    despacho_id: int,
    profesional_id: int,
):

    return DespachoService.asignar_profesional(
        despacho_id,
        profesional_id,
    )


# ==========================================================
# ESTADOS
# ==========================================================

@router.put("/{despacho_id}/en-ruta")
async def iniciar_ruta(
    despacho_id: int,
):

    return DespachoService.iniciar_ruta(
        despacho_id
    )


@router.put("/{despacho_id}/en-atencion")
async def iniciar_atencion(
    despacho_id: int,
):

    return DespachoService.iniciar_atencion(
        despacho_id
    )


@router.put("/{despacho_id}/finalizar")
async def finalizar(
    despacho_id: int,
):

    return DespachoService.finalizar(
        despacho_id
    )


@router.put("/{despacho_id}/cancelar")
async def cancelar(
    despacho_id: int,
):

    return DespachoService.cancelar(
        despacho_id
    )


@router.put("/{despacho_id}/reprogramar")
async def reprogramar(
    despacho_id: int,
):

    return DespachoService.reprogramar(
        despacho_id
    )


# ==========================================================
# MOTOR DE DESPACHO
# ==========================================================

@router.post("/generar")
async def generar():

    """
    Genera el despacho operativo del día.

    Próximos Sprint:

    • Balanceo de carga.
    • IA de asignación.
    • Optimización de rutas.
    • Georreferenciación.
    """

    return DespachoService.generar_despacho_diario()