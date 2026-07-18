from fastapi import APIRouter
router=APIRouter(prefix="/medicamentos",tags=["Medicamentos"])
@router.get("/{historia_id}")
async def listar(historia_id:int):
    return {"historia_id":historia_id}
