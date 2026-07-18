from fastapi import APIRouter
router=APIRouter(prefix="/historia-clinica",tags=["Historia Clínica"])

@router.get("/")
async def listado():
    return {"modulo":"Historia Clínica Enterprise"}
