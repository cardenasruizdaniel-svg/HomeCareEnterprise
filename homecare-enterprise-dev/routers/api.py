from fastapi import APIRouter
from database.database import get_connection

router = APIRouter()


@router.get("/api/calendario")
async def calendario():

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT

            id,

            paciente,

            fecha,

            hora,

            estado

        FROM programacion

    """)

    agenda = cursor.fetchall()

    conexion.close()

    eventos = []

    for visita in agenda:

        eventos.append({

            "id": visita["id"],

            "title": visita["paciente"],

            "start": f'{visita["fecha"]}T{visita["hora"]}',

            "color": "#0d6efd"

        })

    return eventos