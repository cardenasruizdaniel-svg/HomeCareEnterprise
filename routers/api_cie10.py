from fastapi import APIRouter

from services.cie10_service import buscar_cie10

router = APIRouter(

    prefix="/api",

    tags=["API CIE10"]

)


# ==========================================
# BUSCAR CIE10
# ==========================================

@router.get("/cie10")

async def api_buscar_cie10(

    buscar: str = ""

):

    datos = buscar_cie10(buscar)

    resultado = []

    for d in datos:

        resultado.append({

            "codigo": d["codigo"],

            "descripcion": d["descripcion"],

            "categoria": d["categoria"],

            "capitulo": d["capitulo"]

        })

    return resultado