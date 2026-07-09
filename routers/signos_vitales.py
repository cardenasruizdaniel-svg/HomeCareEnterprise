"""
HomeCare Enterprise - Router: Signos Vitales del Paciente

Reconstruido: el router original era un stub que no hacia
nada real. El servicio y repositorio ya estaban completos
(incluyen calculo de IMC y alertas clinicas), solo faltaba
exponerlos para verlos desde la ficha del paciente.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_uno

from services.signos_vitales_service import crear_signos_vitales, listar_signos_vitales

router = APIRouter(prefix="/signos-vitales", tags=["Signos Vitales"])


@router.get("/paciente/{paciente_id}", response_class=HTMLResponse)
async def ver_signos_vitales(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))

    registros = [dict(r) for r in listar_signos_vitales(paciente_id)]

    return templates.TemplateResponse(
        request=request, name="signos_vitales/historial.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "registros": registros,
        },
    )


@router.post("/registrar")
async def registrar(
    request: Request,
    paciente_id: int = Form(...),
    profesional: str = Form(""),
    temperatura: float = Form(...),
    presion_sistolica: int = Form(...),
    presion_diastolica: int = Form(...),
    frecuencia_cardiaca: int = Form(...),
    frecuencia_respiratoria: int = Form(...),
    saturacion_oxigeno: int = Form(...),
    glucemia: float = Form(0),
    peso: float = Form(...),
    talla: float = Form(...),
    dolor: int = Form(0),
    observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    hoy = datetime.now()

    try:
        crear_signos_vitales(
            paciente_id, profesional, hoy.strftime("%Y-%m-%d"), hoy.strftime("%H:%M:%S"),
            temperatura, presion_sistolica, presion_diastolica, frecuencia_cardiaca,
            frecuencia_respiratoria, saturacion_oxigeno, glucemia, peso, talla, dolor,
            observaciones, usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except Exception as error:
        paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
        registros = [dict(r) for r in listar_signos_vitales(paciente_id)]
        return templates.TemplateResponse(
            request=request, name="signos_vitales/historial.html",
            context={
                "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
                "registros": registros, "error": str(error),
            },
        )

    return RedirectResponse(url=f"/signos-vitales/paciente/{paciente_id}", status_code=303)
