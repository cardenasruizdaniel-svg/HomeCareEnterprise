"""HomeCare Enterprise - Router: Recomendaciones / Plan Médico"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_uno

from services import recomendaciones_service as reco_service

router = APIRouter(prefix="/recomendaciones", tags=["Recomendaciones"])


@router.get("/{paciente_id}", response_class=HTMLResponse)
async def ver(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("programacion"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    return templates.TemplateResponse(
        request=request, name="recomendaciones/lista.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "registros": reco_service.listar_por_paciente(paciente_id),
            "tipos_consulta": reco_service.TIPOS_CONSULTA,
        },
    )


@router.post("/{paciente_id}/guardar")
async def guardar(
    request: Request,
    paciente_id: int,
    programacion_id: str = Form(""),
    profesional_id: str = Form(""),
    diagnostico_ppal_codigo: str = Form(""),
    diagnostico_ppal_nombre: str = Form(""),
    diagnostico_rel1_codigo: str = Form(""),
    diagnostico_rel1_nombre: str = Form(""),
    diagnostico_rel2_codigo: str = Form(""),
    diagnostico_rel2_nombre: str = Form(""),
    diagnostico_rel3_codigo: str = Form(""),
    diagnostico_rel3_nombre: str = Form(""),
    tipo_consulta: str = Form("PRIMERA VEZ"),
    incapacidad: str = Form(""),
    nota_aclaratoria: str = Form(""),
    orden_medicamentos: str = Form(""),
    orden_procedimientos: str = Form(""),
    recomendaciones_texto: str = Form(""),
    usuario=Depends(requiere_permiso("programacion")),
):
    try:
        reco_service.crear(
            paciente_id, int(programacion_id) if programacion_id else None,
            int(profesional_id) if profesional_id else None,
            {
                "diagnostico_ppal_codigo": diagnostico_ppal_codigo,
                "diagnostico_ppal_nombre": diagnostico_ppal_nombre,
                "diagnostico_rel1_codigo": diagnostico_rel1_codigo,
                "diagnostico_rel1_nombre": diagnostico_rel1_nombre,
                "diagnostico_rel2_codigo": diagnostico_rel2_codigo,
                "diagnostico_rel2_nombre": diagnostico_rel2_nombre,
                "diagnostico_rel3_codigo": diagnostico_rel3_codigo,
                "diagnostico_rel3_nombre": diagnostico_rel3_nombre,
                "tipo_consulta": tipo_consulta,
                "incapacidad": bool(incapacidad), "nota_aclaratoria": bool(nota_aclaratoria),
                "orden_medicamentos": bool(orden_medicamentos), "orden_procedimientos": bool(orden_procedimientos),
                "recomendaciones_texto": recomendaciones_texto,
            },
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
        return templates.TemplateResponse(
            request=request, name="recomendaciones/lista.html",
            context={
                "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
                "registros": reco_service.listar_por_paciente(paciente_id),
                "tipos_consulta": reco_service.TIPOS_CONSULTA, "error": str(error),
            },
        )
    return RedirectResponse(url=f"/recomendaciones/{paciente_id}", status_code=303)
