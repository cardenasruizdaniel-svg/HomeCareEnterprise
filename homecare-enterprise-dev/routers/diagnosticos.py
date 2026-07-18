"""
HomeCare Enterprise - Router: Diagnósticos del paciente

Reconstruido: antes solo existia un buscador del catalogo
CIE-10 (/diagnosticos/buscar), pero no habia forma real de
asignarle un diagnostico a un paciente ni de verlos en su
historia clinica.
"""

from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_uno

from services.diagnosticos_service import DiagnosticosService

router = APIRouter(prefix="/diagnosticos", tags=["Diagnósticos"])


@router.get("/buscar", response_class=JSONResponse)
async def buscar(q: str, _actor=Depends(requiere_permiso("pacientes"))):
    return [dict(r) for r in DiagnosticosService.buscar(q)]


@router.get("/paciente/{paciente_id}", response_class=HTMLResponse)
async def ver_diagnosticos(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))

    return templates.TemplateResponse(
        request=request, name="diagnosticos_paciente/lista.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "diagnosticos": DiagnosticosService.listar_por_paciente(paciente_id),
        },
    )


@router.post("/asignar")
async def asignar(
    paciente_id: int = Form(...),
    codigo_cie10: str = Form(""),
    diagnostico: str = Form(...),
    tipo: str = Form("IMPRESION DIAGNOSTICA"),
    fecha_diagnostico: str = Form(""),
    profesional: str = Form(""),
    especialidad: str = Form(""),
    observaciones: str = Form(""),
    codigo_cups: str = Form(""),
    descripcion_cups: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    DiagnosticosService.asignar(
        paciente_id, codigo_cie10, diagnostico, tipo,
        fecha_diagnostico or date.today().isoformat(),
        profesional, especialidad, observaciones,
        usuario.get("id") if isinstance(usuario, dict) else None,
        codigo_cups=codigo_cups, descripcion_cups=descripcion_cups,
    )
    return RedirectResponse(url=f"/diagnosticos/paciente/{paciente_id}", status_code=303)


@router.get("/resolver/{diagnostico_id}/{paciente_id}")
async def resolver(diagnostico_id: int, paciente_id: int, _actor=Depends(requiere_permiso("pacientes"))):
    DiagnosticosService.resolver(diagnostico_id)
    return RedirectResponse(url=f"/diagnosticos/paciente/{paciente_id}", status_code=303)


@router.get("/reactivar/{diagnostico_id}/{paciente_id}")
async def reactivar(diagnostico_id: int, paciente_id: int, _actor=Depends(requiere_permiso("pacientes"))):
    DiagnosticosService.reactivar(diagnostico_id)
    return RedirectResponse(url=f"/diagnosticos/paciente/{paciente_id}", status_code=303)
