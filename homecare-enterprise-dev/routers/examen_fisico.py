"""HomeCare Enterprise - Router: Examen Físico por Sistemas"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_uno

from services import examen_fisico_service as ef_service

router = APIRouter(prefix="/examen-fisico", tags=["Examen Físico"])


@router.get("/{paciente_id}", response_class=HTMLResponse)
async def ver(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("programacion"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    return templates.TemplateResponse(
        request=request, name="examen_fisico/lista.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "registros": ef_service.listar_por_paciente(paciente_id),
            "sistemas": ef_service.SISTEMAS,
        },
    )


@router.post("/{paciente_id}/guardar")
async def guardar(
    request: Request,
    paciente_id: int,
    programacion_id: str = Form(""),
    profesional_id: str = Form(""),
    tipo_profesional: str = Form(""),
    cabeza: str = Form(""), cara: str = Form(""), boca: str = Form(""), cuello: str = Form(""),
    torax: str = Form(""), abdomen: str = Form(""), extremidades: str = Form(""),
    vascular: str = Form(""), neurologico: str = Form(""), columna: str = Form(""),
    usuario=Depends(requiere_permiso("programacion")),
):
    ef_service.crear(
        paciente_id, int(programacion_id) if programacion_id else None,
        int(profesional_id) if profesional_id else None, tipo_profesional,
        {
            "cabeza": cabeza, "cara": cara, "boca": boca, "cuello": cuello, "torax": torax,
            "abdomen": abdomen, "extremidades": extremidades, "vascular": vascular,
            "neurologico": neurologico, "columna": columna,
        },
        usuario.get("id") if isinstance(usuario, dict) else None,
    )
    return RedirectResponse(url=f"/examen-fisico/{paciente_id}", status_code=303)
