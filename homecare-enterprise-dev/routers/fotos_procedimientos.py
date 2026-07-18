"""HomeCare Enterprise - Router: Fotos de Procedimientos"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos, consultar_uno

from services import fotos_procedimientos_service

router = APIRouter(prefix="/fotos-procedimientos", tags=["Fotos de Procedimientos"])


@router.get("/{paciente_id}", response_class=HTMLResponse)
async def listado(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    profesionales = consultar_todos(
        "SELECT id, nombre_completo FROM profesionales WHERE estado='ACTIVO' ORDER BY nombre_completo"
    )

    return templates.TemplateResponse(
        request=request, name="fotos_procedimientos/lista.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "profesionales": profesionales,
            "fotos": fotos_procedimientos_service.listar_por_paciente(paciente_id),
        },
    )


@router.post("/subir")
async def subir(
    request: Request,
    paciente_id: int = Form(...),
    descripcion: str = Form(""),
    foto_base64: str = Form(...),
    profesional_id: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    try:
        fotos_procedimientos_service.subir_foto(
            paciente_id, descripcion, foto_base64,
            int(profesional_id) if profesional_id else None,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError:
        pass

    return RedirectResponse(url=f"/fotos-procedimientos/{paciente_id}", status_code=303)


@router.get("/eliminar/{foto_id}/{paciente_id}")
async def eliminar(foto_id: int, paciente_id: int, _actor=Depends(requiere_permiso("pacientes"))):
    fotos_procedimientos_service.eliminar_foto(foto_id)
    return RedirectResponse(url=f"/fotos-procedimientos/{paciente_id}", status_code=303)
