"""HomeCare Enterprise - Router: Historia Clínica Consolidada"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_uno

from services.historia_clinica_service import (
    obtener_informe_para_imprimir,
    obtener_informes_cuidador,
    obtener_linea_tiempo,
)

router = APIRouter(prefix="/historia-clinica", tags=["Historia Clínica"])


@router.get("/cuidador/{paciente_id}", response_class=HTMLResponse)
async def ver_informes_cuidador(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))

    return templates.TemplateResponse(
        request=request, name="historia_clinica_consolidada/informes_cuidador.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "informes": obtener_informes_cuidador(paciente_id),
        },
    )


@router.get("/informe/{evolucion_id}/imprimir", response_class=HTMLResponse)
async def imprimir_informe(request: Request, evolucion_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    from services.configuracion_empresa_service import obtener as obtener_config_empresa

    try:
        datos = obtener_informe_para_imprimir(evolucion_id)
    except ValueError as error:
        return HTMLResponse(f"<h3>{error}</h3>", status_code=404)

    return templates.TemplateResponse(
        request=request, name="historia_clinica_consolidada/imprimir_informe.html",
        context={
            "usuario": usuario, **datos,
            "empresa": obtener_config_empresa(),
        },
    )


@router.get("/{paciente_id}", response_class=HTMLResponse)
async def ver_historia(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))

    return templates.TemplateResponse(
        request=request, name="historia_clinica_consolidada/lista.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "eventos": obtener_linea_tiempo(paciente_id),
        },
    )


@router.post("/nota-aclaratoria")
async def crear_nota_aclaratoria(
    request: Request,
    paciente_id: int = Form(...),
    nota_aclaratoria_de: int = Form(...),
    nota: str = Form(...),
    usuario=Depends(requiere_permiso("pacientes")),
):
    from services.evoluciones_service import registrar_evolucion

    profesional = consultar_uno(
        "SELECT id, especialidad_principal FROM profesionales WHERE usuario_id=?",
        (usuario.get("id") if isinstance(usuario, dict) else None,),
    )
    profesional = dict(profesional) if profesional else {}

    try:
        registrar_evolucion(
            paciente_id=paciente_id,
            programacion_id=None,
            profesional_id=profesional.get("id"),
            tipo_profesional=profesional.get("especialidad_principal", ""),
            nota=nota,
            origen="WEB",
            usuario_id=usuario.get("id") if isinstance(usuario, dict) else None,
            tipo_registro="NOTA_ACLARATORIA",
            nota_aclaratoria_de=nota_aclaratoria_de,
        )
    except ValueError as error:
        paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
        return templates.TemplateResponse(
            request=request, name="historia_clinica_consolidada/lista.html",
            context={
                "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
                "eventos": obtener_linea_tiempo(paciente_id),
                "error": str(error),
            },
        )

    return RedirectResponse(url=f"/historia-clinica/{paciente_id}", status_code=303)
