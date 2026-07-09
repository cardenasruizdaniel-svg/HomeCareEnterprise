"""HomeCare Enterprise - Router: Servicios asignados al paciente"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos, consultar_uno

from services import servicios_paciente_service

router = APIRouter(prefix="/servicios-paciente", tags=["Servicios del Paciente"])


@router.get("/{paciente_id}", response_class=HTMLResponse)
async def listado(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    profesionales = consultar_todos(
        "SELECT id, nombre_completo, especialidad_principal FROM profesionales "
        "WHERE estado='ACTIVO' ORDER BY nombre_completo"
    )

    return templates.TemplateResponse(
        request=request, name="servicios_paciente/lista.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "servicios": servicios_paciente_service.listar_por_paciente(paciente_id),
            "profesionales": profesionales,
            "frecuencias": servicios_paciente_service.FRECUENCIAS_VALIDAS,
        },
    )


@router.post("/asignar")
async def asignar(
    request: Request,
    paciente_id: int = Form(...),
    actividad_id: str = Form(...),
    profesional_id: str = Form(""),
    frecuencia: str = Form("Diaria"),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(""),
    numero_sesiones: str = Form(""),
    hora_inicio: str = Form("08:00"),
    hora_fin: str = Form("09:00"),
    indicaciones: str = Form(""),
    renovacion_automatica: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    try:
        resultado = servicios_paciente_service.asignar_servicio(
            paciente_id, None, None,
            int(profesional_id) if profesional_id else None,
            frecuencia, fecha_inicio, fecha_fin or None, hora_inicio, hora_fin, indicaciones,
            usuario.get("id") if isinstance(usuario, dict) else None,
            actividad_id=int(actividad_id),
            numero_sesiones=int(numero_sesiones) if numero_sesiones else None,
            renovacion_automatica=bool(renovacion_automatica),
        )
    except ValueError as error:
        paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
        profesionales = consultar_todos(
            "SELECT id, nombre_completo, especialidad_principal FROM profesionales WHERE estado='ACTIVO' ORDER BY nombre_completo"
        )
        return templates.TemplateResponse(
            request=request, name="servicios_paciente/lista.html",
            context={
                "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
                "servicios": servicios_paciente_service.listar_por_paciente(paciente_id),
                "profesionales": profesionales,
                "frecuencias": servicios_paciente_service.FRECUENCIAS_VALIDAS,
                "error": str(error),
            },
        )

    return RedirectResponse(
        url=f"/servicios-paciente/{paciente_id}?creado={resultado['visitas_creadas']}",
        status_code=303,
    )


@router.get("/cancelar/{servicio_id}/{paciente_id}")
async def cancelar(servicio_id: int, paciente_id: int, _actor=Depends(requiere_permiso("pacientes"))):
    servicios_paciente_service.cancelar_servicio(servicio_id)
    return RedirectResponse(url=f"/servicios-paciente/{paciente_id}", status_code=303)
