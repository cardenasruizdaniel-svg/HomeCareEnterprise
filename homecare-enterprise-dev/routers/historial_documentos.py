"""HomeCare Enterprise - Router: Historial de documentos del paciente"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_uno

from services import historial_documentos_service

router = APIRouter(prefix="/historial-documentos", tags=["Historial de Documentos"])


@router.get("/{paciente_id}", response_class=HTMLResponse)
async def listado(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    return templates.TemplateResponse(
        request=request, name="historial_documentos/lista.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "historial": historial_documentos_service.obtener_historial(paciente_id),
        },
    )


@router.post("/cambiar")
async def cambiar(
    request: Request,
    paciente_id: int = Form(...),
    tipo_documento_nuevo: str = Form(...),
    numero_documento_nuevo: str = Form(...),
    fecha_cambio: str = Form(...),
    motivo: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    try:
        historial_documentos_service.cambiar_documento(
            paciente_id, tipo_documento_nuevo, numero_documento_nuevo, fecha_cambio, motivo,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
        return templates.TemplateResponse(
            request=request, name="historial_documentos/lista.html",
            context={
                "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
                "historial": historial_documentos_service.obtener_historial(paciente_id),
                "error": str(error),
            },
        )

    return RedirectResponse(url=f"/historial-documentos/{paciente_id}", status_code=303)


@router.get("/marcar-principal/{historial_id}/{paciente_id}")
async def marcar_principal(
    historial_id: int,
    paciente_id: int,
    _actor=Depends(requiere_permiso("pacientes")),
):
    historial_documentos_service.marcar_como_principal(paciente_id, historial_id)
    return RedirectResponse(url=f"/historial-documentos/{paciente_id}", status_code=303)
