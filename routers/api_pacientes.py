from datetime import date

from fastapi import APIRouter
from services.pacientes_busqueda_service import buscar

router = APIRouter(
    prefix="/api",
    tags=["API Pacientes"]
)


def _calcular_edad(fecha_nacimiento):
    if not fecha_nacimiento:
        return None
    try:
        nacimiento = date.fromisoformat(str(fecha_nacimiento)[:10])
    except ValueError:
        return None
    hoy = date.today()
    return hoy.year - nacimiento.year - (
        (hoy.month, hoy.day) < (nacimiento.month, nacimiento.day)
    )


@router.get("/pacientes")
async def api_pacientes(buscar_texto: str = ""):

    pacientes = buscar(buscar_texto)

    respuesta = []

    for p in pacientes:

        respuesta.append({

            "id": p["id"],

            "documento": p["documento"],

            "nombre": p["nombre"],

            "telefono": p["telefono"],

            "direccion": p["direccion"],

            "ciudad": p["ciudad"],

            "eps": p["eps"],

            "sexo": p["sexo"],

            "edad": _calcular_edad(p["fecha_nacimiento"]),

        })

    return respuesta