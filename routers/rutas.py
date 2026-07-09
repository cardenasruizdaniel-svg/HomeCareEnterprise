from fastapi import APIRouter
from services.rutas_service import RutasService
router=APIRouter(prefix="/rutas",tags=["Rutas"])
@router.get("/{profesional_id}/{fecha}")
async def ruta(profesional_id:int,fecha:str):
    return RutasService.generar_ruta(profesional_id,fecha)
