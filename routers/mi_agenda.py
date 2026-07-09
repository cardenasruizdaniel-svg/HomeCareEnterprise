"""
HomeCare Enterprise - Router: Mi Agenda

Vista para que un profesional, al iniciar sesion, vea
UNICAMENTE su propia programacion y sus propios pacientes
(no las de todo el equipo). Requiere que su usuario este
vinculado a su registro de profesional (usuario_id).
"""

from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from core.dependencies import usuario_actual
from core.templates import templates
from database.database import consultar_todos, consultar_uno

router = APIRouter(prefix="/mi-agenda", tags=["Mi Agenda"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def mi_agenda(request: Request, fecha: str = "", usuario: dict = Depends(usuario_actual)):

    if not usuario or not usuario.get("id"):
        return templates.TemplateResponse(
            request=request, name="mi_agenda/no_vinculado.html", context={"usuario": usuario},
        )

    profesional = consultar_uno(
        "SELECT * FROM profesionales WHERE usuario_id=?", (usuario["id"],)
    )

    if not profesional:
        return templates.TemplateResponse(
            request=request, name="mi_agenda/no_vinculado.html", context={"usuario": usuario},
        )

    profesional = dict(profesional)
    fecha = fecha or date.today().isoformat()

    visitas = consultar_todos(
        """
        SELECT p.*, (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente
        FROM programaciones p
        JOIN pacientes pa ON pa.id = p.paciente_id
        WHERE p.profesional_id=? AND p.fecha=? AND p.eliminado=0
        ORDER BY p.hora_inicio
        """,
        (profesional["id"], fecha),
    )

    pacientes_activos = consultar_todos(
        """
        SELECT DISTINCT pa.id, pa.primer_nombre, pa.primer_apellido, pa.documento, pa.celular
        FROM servicios_paciente sp
        JOIN pacientes pa ON pa.id = sp.paciente_id
        WHERE sp.profesional_id=? AND sp.estado='Activo'
        ORDER BY pa.primer_nombre
        """,
        (profesional["id"],),
    )

    return templates.TemplateResponse(
        request=request, name="mi_agenda/lista.html",
        context={
            "usuario": usuario,
            "profesional": profesional,
            "fecha": fecha,
            "visitas": [dict(v) for v in visitas],
            "pacientes_activos": [dict(p) for p in pacientes_activos],
        },
    )
