"""HomeCare Enterprise - Router: Turnos programados (calendario)"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos

from services import turnos_service

router = APIRouter(prefix="/turnos", tags=["Turnos"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def calendario(
    request: Request,
    fecha_inicio: str = "",
    fecha_fin: str = "",
    usuario=Depends(requiere_permiso("programacion")),
):
    if not fecha_inicio:
        hoy = date.today()
        fecha_inicio = hoy.isoformat()
        fecha_fin = (hoy + timedelta(days=6)).isoformat()

    turnos = turnos_service.listar_calendario_con_paciente(fecha_inicio, fecha_fin)
    profesionales = consultar_todos(
        "SELECT * FROM profesionales WHERE estado='ACTIVO' ORDER BY primer_apellido"
    )

    return templates.TemplateResponse(
        request=request, name="turnos/calendario.html",
        context={
            "usuario": usuario, "turnos": turnos, "profesionales": profesionales,
            "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin,
        },
    )


# ==========================================================
# CATÁLOGO DE TURNOS (patrones de horario reutilizables)
# ==========================================================

@router.get("/catalogo", response_class=HTMLResponse)
async def catalogo(request: Request, usuario=Depends(requiere_permiso("programacion"))):
    return templates.TemplateResponse(
        request=request, name="turnos/catalogo.html",
        context={"usuario": usuario, "turnos": turnos_service.listar_catalogo_turnos()},
    )


@router.post("/catalogo/crear")
async def crear_catalogo(
    request: Request,
    nombre: str = Form(...),
    tramo1_inicio: str = Form(...),
    tramo1_fin: str = Form(...),
    tramo2_inicio: str = Form(""),
    tramo2_fin: str = Form(""),
    tipo_cuidado_aplica: str = Form("Ambos"),
    usuario=Depends(requiere_permiso("programacion")),
):
    try:
        turnos_service.crear_turno_catalogo(
            nombre, tramo1_inicio, tramo1_fin, tramo2_inicio, tramo2_fin, tipo_cuidado_aplica
        )
    except ValueError as error:
        return templates.TemplateResponse(
            request=request, name="turnos/catalogo.html",
            context={"usuario": usuario, "turnos": turnos_service.listar_catalogo_turnos(), "error": str(error)},
        )
    return RedirectResponse(url="/turnos/catalogo", status_code=303)


@router.get("/catalogo/desactivar/{turno_id}")
async def desactivar_catalogo(turno_id: int, _actor=Depends(requiere_permiso("programacion"))):
    turnos_service.desactivar_turno_catalogo(turno_id)
    return RedirectResponse(url="/turnos/catalogo", status_code=303)


# ==========================================================
# ASIGNAR TURNOS A UN PACIENTE (día a día, semana o mes)
# ==========================================================

@router.get("/asignar/{paciente_id}", response_class=HTMLResponse)
async def asignar_formulario(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("programacion"))):
    from database.database import consultar_uno
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    paciente = dict(paciente) if paciente else {}

    # Filtra los profesionales sugeridos segun el tipo de
    # cuidado del paciente: Ventilado -> Auxiliar de Enfermeria,
    # No Ventilado -> Cuidador. Igual se listan todos, para que
    # se pueda ajustar manualmente si hace falta.
    profesionales = [
        dict(p) for p in consultar_todos(
            "SELECT * FROM profesionales WHERE estado='ACTIVO' ORDER BY primer_apellido"
        )
    ]

    hoy = date.today()

    return templates.TemplateResponse(
        request=request, name="turnos/asignar_paciente.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "profesionales": profesionales, "catalogo": turnos_service.listar_catalogo_turnos(),
            "turnos_actuales": turnos_service.listar_turnos_de_paciente(
                paciente_id, hoy.isoformat(), (hoy + timedelta(days=30)).isoformat()
            ),
        },
    )


@router.post("/asignar/{paciente_id}")
async def asignar_guardar(
    request: Request,
    paciente_id: int,
    profesional_id: int = Form(...),
    catalogo_turno_id: int = Form(...),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    dias_semana: list = Form([]),
    zona: str = Form(""),
    observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("programacion")),
):
    from database.database import consultar_uno
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    paciente = dict(paciente) if paciente else {}
    profesionales = [
        dict(p) for p in consultar_todos(
            "SELECT * FROM profesionales WHERE estado='ACTIVO' ORDER BY primer_apellido"
        )
    ]

    try:
        resultado = turnos_service.asignar_turno_paciente(
            paciente_id, profesional_id, catalogo_turno_id, fecha_inicio, fecha_fin,
            dias_semana, zona, observaciones,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        hoy = date.today()
        return templates.TemplateResponse(
            request=request, name="turnos/asignar_paciente.html",
            context={
                "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
                "profesionales": profesionales, "catalogo": turnos_service.listar_catalogo_turnos(),
                "turnos_actuales": turnos_service.listar_turnos_de_paciente(
                    paciente_id, hoy.isoformat(), (hoy + timedelta(days=30)).isoformat()
                ),
                "error": str(error),
            },
        )

    return RedirectResponse(
        url=f"/turnos/asignar/{paciente_id}?creado={resultado['turnos_creados']}", status_code=303
    )


@router.post("/guardar")
async def guardar(
    profesional_id: int = Form(...),
    fecha: str = Form(...),
    turno: str = Form(...),
    hora_inicio: str = Form(...),
    hora_fin: str = Form(...),
    zona: str = Form(""),
    observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("programacion")),
):
    turnos_service.crear_turno(
        profesional_id, fecha, turno, hora_inicio, hora_fin, zona, observaciones,
        usuario.get("id") if isinstance(usuario, dict) else None,
    )
    return RedirectResponse(url=f"/turnos?fecha_inicio={fecha}&fecha_fin={fecha}", status_code=303)


@router.get("/eliminar/{id}")
async def eliminar(id: int, _actor=Depends(requiere_permiso("programacion"))):
    turnos_service.eliminar_turno(id)
    return RedirectResponse(url="/turnos", status_code=303)


@router.get("/validar/{profesional_id}", response_class=HTMLResponse)
async def validar(
    request: Request,
    profesional_id: int,
    fecha_inicio: str = "",
    fecha_fin: str = "",
    usuario=Depends(requiere_permiso("programacion")),
):
    if not fecha_inicio:
        hoy = date.today()
        fecha_inicio = (hoy - timedelta(days=7)).isoformat()
        fecha_fin = hoy.isoformat()

    reporte = turnos_service.validar_turnos_periodo(profesional_id, fecha_inicio, fecha_fin)

    return templates.TemplateResponse(
        request=request, name="turnos/validacion.html",
        context={
            "usuario": usuario, "reporte": reporte, "profesional_id": profesional_id,
            "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin,
        },
    )
