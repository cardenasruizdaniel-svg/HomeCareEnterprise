from fastapi import APIRouter
from services.georreferenciacion_service import GeorreferenciacionService
router=APIRouter(prefix="/mapa",tags=["Mapa"])
@router.get("/marcador")
async def marcador(lat:float,lon:float,titulo:str="Paciente"):
    return GeorreferenciacionService.marcador(lat,lon,titulo)
