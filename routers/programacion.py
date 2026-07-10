"""
=========================================================
HomeCare Enterprise
Router: Programacion de visitas domiciliarias
Reconstruido: el archivo original estaba corrupto
(sin router, sin imports, llamaba funciones inexistentes).
=========================================================
"""

from datetime import date

from fastapi import APIRouter, Body, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from database.database import consultar_todos

from services import programacion_service

router = APIRouter(prefix="/programacion", tags=["Programación"])


# ==========================================
# DASHBOARD
# ==========================================

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    usuario=Depends(requiere_permiso("programacion")),
):
    hoy = date.today().isoformat()

    indicadores = programacion_service.indicadores_dashboard(hoy)
    visitas = programacion_service.proximas_visitas(20)

    return templates.TemplateResponse(
        request=request,
        name="programacion/dashboard.html",
        context={
            "usuario": usuario,
            "visitas": visitas,
            **indicadores,
        },
    )


# ==========================================
# AGENDA DEL DÍA
# ==========================================

@router.get("/dia", response_class=HTMLResponse)
async def agenda_dia(
    request: Request,
    fecha: str = "",
    usuario=Depends(requiere_permiso("programacion")),
):
    fecha = fecha or date.today().isoformat()
    visitas = programacion_service.obtener_agenda_dia(fecha)

    return templates.TemplateResponse(
        request=request,
        name="programacion/dashboard.html",
        context={
            "usuario": usuario,
            "visitas": visitas,
            **programacion_service.indicadores_dashboard(fecha),
        },
    )


# ==========================================
# AGENDA SEMANAL
# ==========================================

@router.get("/semana", response_class=HTMLResponse)
async def agenda_semana(
    request: Request,
    fecha: str = "",
    usuario=Depends(requiere_permiso("programacion")),
):
    fecha = fecha or date.today().isoformat()
    datos = programacion_service.obtener_agenda_semana(fecha)

    return templates.TemplateResponse(
        request=request,
        name="programacion/semana.html",
        context={"usuario": usuario, "fecha_referencia": fecha, **datos},
    )


# ==========================================
# AGENDA MENSUAL
# ==========================================

@router.get("/mes", response_class=HTMLResponse)
async def agenda_mes(
    request: Request,
    anio: int = 0,
    mes: int = 0,
    usuario=Depends(requiere_permiso("programacion")),
):
    hoy = date.today()
    anio = anio or hoy.year
    mes = mes or hoy.month

    datos = programacion_service.obtener_agenda_mes(anio, mes)

    return templates.TemplateResponse(
        request=request,
        name="programacion/mes.html",
        context={"usuario": usuario, **datos},
    )


# ==========================================
# CALENDARIO (vista de cuadrícula mensual)
# ==========================================

@router.get("/calendario", response_class=HTMLResponse)
async def calendario(
    request: Request,
    anio: int = 0,
    mes: int = 0,
    usuario=Depends(requiere_permiso("programacion")),
):
    import calendar as calendar_mod

    hoy = date.today()
    anio = anio or hoy.year
    mes = mes or hoy.month

    datos = programacion_service.obtener_agenda_mes(anio, mes)

    visitas_por_dia = {}
    for v in datos["visitas"]:
        visitas_por_dia.setdefault(v["fecha"], []).append(dict(v))

    cal = calendar_mod.Calendar(firstweekday=0)
    semanas = cal.monthdayscalendar(anio, mes)

    return templates.TemplateResponse(
        request=request,
        name="programacion/calendario.html",
        context={
            "usuario": usuario,
            "anio": anio,
            "mes": mes,
            "nombre_mes": datos["nombre_mes"],
            "semanas": semanas,
            "visitas_por_dia": visitas_por_dia,
            "hoy": hoy.isoformat(),
        },
    )


# ==========================================
# NUEVA VISITA
# ==========================================

@router.get("/mensual", response_class=HTMLResponse)
async def programacion_mensual_formulario(
    request: Request,
    usuario=Depends(requiere_permiso("programacion")),
):
    profesionales = consultar_todos(
        "SELECT id, nombre_completo, especialidad_principal FROM profesionales "
        "WHERE estado='ACTIVO' ORDER BY nombre_completo"
    )
    pacientes = consultar_todos(
        "SELECT id, documento, primer_nombre, primer_apellido FROM pacientes "
        "WHERE UPPER(estado)='ACTIVO' ORDER BY primer_nombre"
    )

    return templates.TemplateResponse(
        request=request,
        name="programacion/mensual.html",
        context={
            "usuario": usuario,
            "profesionales": profesionales,
            "pacientes": pacientes,
        },
    )


@router.get("/mensual/historial/{profesional_id}")
async def historial_profesional(profesional_id: int, usuario=Depends(requiere_permiso("programacion"))):
    return programacion_service.historial_programacion_profesional(profesional_id)


@router.get("/mensual/cronograma/{profesional_id}/{anio}/{mes}", response_class=HTMLResponse)
async def ver_cronograma(
    request: Request, profesional_id: int, anio: int, mes: int,
    usuario=Depends(requiere_permiso("programacion")),
):
    datos = programacion_service.cronograma_mensual(profesional_id, anio, mes)
    return templates.TemplateResponse(
        request=request, name="programacion/cronograma_mensual.html",
        context={"usuario": usuario, **datos},
    )


@router.post("/mensual/crear")
async def programacion_mensual_crear(
    request: Request,
    datos: dict = Body(...),
    usuario=Depends(requiere_permiso("programacion")),
):
    try:
        resultado = programacion_service.crear_programacion_mensual(
            int(datos["profesional_id"]), datos["turnos"],
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
        return resultado
    except Exception as error:
        return {"error": str(error)}


@router.get("/nueva", response_class=HTMLResponse)
async def nueva(
    request: Request,
    usuario=Depends(requiere_permiso("programacion")),
):
    profesionales = consultar_todos(
        "SELECT * FROM profesionales WHERE estado='ACTIVO' "
        "ORDER BY primer_apellido, primer_nombre"
    )

    return templates.TemplateResponse(
        request=request,
        name="programacion/nueva_visita.html",
        context={
            "usuario": usuario,
            "profesionales": profesionales,
        },
    )


# ==========================================
# GUARDAR
# ==========================================

@router.post("/guardar")
async def guardar(
    request: Request,
    paciente_id: int = Form(...),
    profesional_id: int = Form(...),
    diagnostico_id: int = Form(None),
    fecha: str = Form(...),
    hora_inicio: str = Form(...),
    hora_fin: str = Form(""),
    duracion: int = Form(60),
    servicio: str = Form(...),
    procedimiento: str = Form(""),
    codigo_cups: str = Form(""),
    valor_servicio: float = Form(0),
    prioridad: str = Form("Normal"),
    direccion: str = Form(""),
    barrio: str = Form(""),
    ciudad: str = Form(""),
    departamento: str = Form(""),
    telefono_contacto: str = Form(""),
    nombre_contacto: str = Form(""),
    observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("programacion")),
):
    try:
        programacion_service.crear_visita(
            paciente_id,
            profesional_id,
            diagnostico_id,
            fecha,
            hora_inicio,
            hora_fin,
            duracion,
            servicio,
            procedimiento,
            codigo_cups,
            valor_servicio,
            prioridad,
            direccion,
            barrio,
            ciudad,
            departamento,
            telefono_contacto,
            nombre_contacto,
            observaciones,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        profesionales = consultar_todos(
            "SELECT * FROM profesionales WHERE estado='ACTIVO' "
            "ORDER BY primer_apellido, primer_nombre"
        )
        return templates.TemplateResponse(
            request=request,
            name="programacion/nueva_visita.html",
            context={
                "usuario": usuario,
                "profesionales": profesionales,
                "error": str(error),
            },
        )

    return RedirectResponse(url="/programacion", status_code=303)


# ==========================================
# DETALLE
# ==========================================

@router.get("/detalle/{id}", response_class=HTMLResponse)
async def detalle(
    request: Request,
    id: int,
    geocerca_ok: str = None,
    geocerca_distancia: str = None,
    geocerca_verificable: str = None,
    geocerca_evento: str = None,
    usuario=Depends(requiere_permiso("programacion")),
):
    visita = programacion_service.obtener_visita(id)

    profesional_conectado = None
    if isinstance(usuario, dict) and usuario.get("id"):
        from database.database import consultar_uno
        profesional_conectado = consultar_uno(
            "SELECT id, especialidad_principal FROM profesionales WHERE usuario_id=?",
            (usuario["id"],),
        )
        profesional_conectado = dict(profesional_conectado) if profesional_conectado else None

    return templates.TemplateResponse(
        request=request,
        name="programacion/detalle.html",
        context={
            "usuario": usuario,
            "visita": visita,
            "geocerca_ok": geocerca_ok,
            "geocerca_distancia": geocerca_distancia,
            "geocerca_verificable": geocerca_verificable,
            "geocerca_evento": geocerca_evento,
            "profesional_conectado": profesional_conectado,
        },
    )


@router.post("/registrar-evolucion/{id}")
async def registrar_evolucion_web(
    id: int,
    nota: str = Form(...),
    tipo_registro: str = Form("INFORME"),
    tipo_profesional: str = Form(""),
    nota_aclaratoria_de: str = Form(""),
    usuario=Depends(requiere_permiso("programacion")),
):
    from database.database import consultar_uno
    from services.evoluciones_service import registrar_evolucion

    visita = programacion_service.obtener_visita(id)
    visita = dict(visita) if visita else {}

    profesional = consultar_uno(
        "SELECT id, especialidad_principal FROM profesionales WHERE usuario_id=?",
        (usuario.get("id"),),
    )
    profesional = dict(profesional) if profesional else {}

    try:
        registrar_evolucion(
            paciente_id=visita.get("paciente_id"),
            programacion_id=id,
            profesional_id=profesional.get("id"),
            tipo_profesional=tipo_profesional or profesional.get("especialidad_principal", ""),
            nota=nota,
            origen="WEB",
            usuario_id=usuario.get("id"),
            tipo_registro=tipo_registro,
            nota_aclaratoria_de=int(nota_aclaratoria_de) if nota_aclaratoria_de else None,
        )
    except ValueError:
        pass  # se ignora una nota vacia en vez de romper la pantalla

    return RedirectResponse(url=f"/programacion/detalle/{id}", status_code=303)


# ==========================================
# CAMBIOS DE ESTADO
# ==========================================

@router.get("/confirmar/{id}")
async def confirmar(id: int, _actor=Depends(requiere_permiso("programacion"))):
    programacion_service.confirmar_visita(id)
    return RedirectResponse(url="/programacion", status_code=303)


@router.get("/iniciar/{id}")
async def iniciar(
    id: int,
    lat: float = None,
    lon: float = None,
    _actor=Depends(requiere_permiso("programacion")),
):
    verificacion = programacion_service.registrar_ingreso(id, lat, lon)
    return RedirectResponse(
        url=f"/programacion/detalle/{id}?geocerca_ok={verificacion['dentro_del_rango']}"
            f"&geocerca_distancia={verificacion['distancia_metros']}"
            f"&geocerca_verificable={verificacion['verificable']}&geocerca_evento=ingreso",
        status_code=303,
    )


@router.post("/iniciar-con-foto/{id}")
async def iniciar_con_foto(id: int, datos: dict, _actor=Depends(requiere_permiso("programacion"))):
    verificacion = programacion_service.registrar_ingreso(
        id, datos.get("lat"), datos.get("lon"), datos.get("foto_base64"),
    )
    return verificacion


@router.get("/finalizar/{id}")
async def finalizar(
    id: int,
    lat: float = None,
    lon: float = None,
    _actor=Depends(requiere_permiso("programacion")),
):
    verificacion = programacion_service.registrar_salida(id, lat, lon)
    return RedirectResponse(
        url=f"/programacion/detalle/{id}?geocerca_ok={verificacion['dentro_del_rango']}"
            f"&geocerca_distancia={verificacion['distancia_metros']}"
            f"&geocerca_verificable={verificacion['verificable']}&geocerca_evento=salida",
        status_code=303,
    )


@router.post("/finalizar-con-foto/{id}")
async def finalizar_con_foto(id: int, datos: dict, _actor=Depends(requiere_permiso("programacion"))):
    verificacion = programacion_service.registrar_salida(
        id, datos.get("lat"), datos.get("lon"), datos.get("foto_base64"),
    )
    return verificacion


@router.get("/cancelar/{id}")
async def cancelar(id: int, _actor=Depends(requiere_permiso("programacion"))):
    programacion_service.cancelar_visita(id)
    return RedirectResponse(url="/programacion", status_code=303)


@router.get("/eliminar/{id}")
async def eliminar(id: int, _actor=Depends(requiere_permiso("programacion"))):
    programacion_service.eliminar_visita(id)
    return RedirectResponse(url="/programacion", status_code=303)
