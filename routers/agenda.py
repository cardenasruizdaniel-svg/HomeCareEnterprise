from fastapi import APIRouter
from services.agenda_service import AgendaService

router=APIRouter(prefix="/agenda",tags=["Agenda"])

@router.get("/semanal/{profesional_id}/{inicio}")
async def semanal(profesional_id:int,inicio:str):
    return AgendaService.agenda_semanal(profesional_id,inicio)

@router.post("/reprogramar/{cita_id}")
async def reprogramar(cita_id:int,fecha:str,hora:str):
    return AgendaService.reprogramar(cita_id,fecha,hora)
