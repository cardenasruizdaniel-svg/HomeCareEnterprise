from fastapi import APIRouter
router=APIRouter(prefix="/evoluciones",tags=["Evoluciones"])
@router.get("/{historia_id}")
async def listar(historia_id:int):
    return {"historia_id":historia_id}
