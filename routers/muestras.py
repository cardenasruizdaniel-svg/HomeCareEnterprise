"""HomeCare Enterprise - Router: Trazabilidad de Toma de Muestras"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso, usuario_actual
from core.templates import templates

from services import trazabilidad_muestras_service as muestras
from services.pacientes_service import PacientesService

router = APIRouter(prefix="/muestras", tags=["Trazabilidad de Muestras"])


def _id_usuario(usuario):
    return usuario.get("id") if isinstance(usuario, dict) else None


@router.get("/pendientes", response_class=HTMLResponse)
async def pendientes(request: Request, usuario=Depends(requiere_permiso("pacientes"))):
    return templates.TemplateResponse(
        request=request, name="muestras/pendientes.html",
        context={"usuario": usuario, "pendientes": muestras.listar_pendientes_entrega(), "resumen": muestras.resumen_dashboard()},
    )


@router.get("/paciente/{paciente_id}", response_class=HTMLResponse)
async def listar_paciente(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = PacientesService.obtener(paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="El paciente no existe.")
    return templates.TemplateResponse(
        request=request, name="muestras/lista_paciente.html",
        context={"usuario": usuario, "paciente": paciente, "muestras": muestras.listar_por_paciente(paciente_id)},
    )


@router.get("/paciente/{paciente_id}/registrar", response_class=HTMLResponse)
async def ver_registrar(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    from database.database import consultar_uno
    from datetime import datetime

    paciente = PacientesService.obtener(paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="El paciente no existe.")

    profesional = consultar_uno("SELECT id FROM profesionales WHERE usuario_id=?", (usuario.get("id"),))
    profesional_id = dict(profesional)["id"] if profesional else None

    return templates.TemplateResponse(
        request=request, name="muestras/registrar.html",
        context={
            "usuario": usuario, "paciente": paciente, "profesional_id": profesional_id,
            "tipos_muestra": muestras.TIPOS_MUESTRA, "tipos_recipiente": muestras.TIPOS_RECIPIENTE,
            "condiciones_transporte": muestras.CONDICIONES_TRANSPORTE,
            "fecha_hora_actual": datetime.now().strftime("%Y-%m-%dT%H:%M"),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/paciente/{paciente_id}/registrar")
async def registrar(
    paciente_id: int,
    tipo_muestra: str = Form(...), tipo_recipiente: str = Form(...), fecha_hora_recoleccion: str = Form(...),
    cantidad_recipientes: int = Form(1), examenes_solicitados: str = Form(""), condiciones_transporte: str = Form(""),
    laboratorio_destino: str = Form(""), observaciones: str = Form(""),
    foto_muestra_base64: str = Form(""), firma_recoleccion_base64: str = Form(""),
    profesional_id: str = Form(""), programacion_id: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    try:
        muestra_id = muestras.registrar_recoleccion(
            paciente_id, int(profesional_id) if profesional_id else None, tipo_muestra, tipo_recipiente,
            fecha_hora_recoleccion.replace("T", " ") + (":00" if len(fecha_hora_recoleccion) == 16 else ""),
            cantidad_recipientes=cantidad_recipientes, examenes_solicitados=examenes_solicitados,
            condiciones_transporte=condiciones_transporte, laboratorio_destino=laboratorio_destino,
            observaciones=observaciones, foto_muestra_base64=foto_muestra_base64 or None,
            firma_recoleccion_base64=firma_recoleccion_base64 or None,
            programacion_id=int(programacion_id) if programacion_id else None,
            usuario_id=_id_usuario(usuario), usuario_nombre=usuario.get("nombre"),
        )
    except ValueError as error:
        return RedirectResponse(url=f"/muestras/paciente/{paciente_id}/registrar?error={error}", status_code=303)

    return RedirectResponse(url=f"/muestras/{muestra_id}", status_code=303)


# ==========================================================
# LISTA DE SUPERVISIÓN -- TOMA DE MUESTRAS (auditoría en sitio)
# Estas rutas van ANTES de "/{muestra_id}" a propósito -- si
# quedaran después, FastAPI trataría "supervision" como si
# fuera un muestra_id numérico y fallaría con error 422.
# ==========================================================

from services import supervision_muestras_service as supervision


@router.get("/supervision", response_class=HTMLResponse)
async def supervision_lista(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    from services import profesionales_service
    return templates.TemplateResponse(
        request=request, name="muestras/supervision_lista.html",
        context={
            "usuario": usuario, "supervisiones": supervision.listar_supervisiones(),
            "promedio": supervision.promedio_cumplimiento_general(),
            "profesionales": profesionales_service.activos(),
        },
    )


@router.get("/supervision/nueva", response_class=HTMLResponse)
async def supervision_nueva(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    from services import profesionales_service
    return templates.TemplateResponse(
        request=request, name="muestras/supervision_formulario.html",
        context={
            "usuario": usuario, "secciones": supervision.SECCIONES_CHECKLIST,
            "profesionales": profesionales_service.activos(),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/supervision/crear")
async def supervision_crear(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    formulario = await request.form()
    datos = {
        "fecha": formulario.get("fecha"), "punto_toma": formulario.get("punto_toma"),
        "auxiliar_supervisado_id": formulario.get("auxiliar_supervisado_id") or None,
        "auxiliar_supervisado_nombre": formulario.get("auxiliar_supervisado_nombre"),
        "responsable_auditoria_id": _id_profesional_responsable(formulario),
        "cargo_responsable": formulario.get("cargo_responsable"),
        "hora_inicio": formulario.get("hora_inicio"), "hora_fin": formulario.get("hora_fin"),
        "observaciones_generales": formulario.get("observaciones_generales"),
    }
    respuestas = {}
    for bloque in supervision.SECCIONES_CHECKLIST:
        for codigo, _texto in bloque["items"]:
            respuestas[codigo] = {
                "respuesta": formulario.get(f"respuesta_{codigo}", "N/A"),
                "observaciones": formulario.get(f"observaciones_{codigo}", ""),
            }
    try:
        supervision_id = supervision.crear_supervision(datos, respuestas, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/muestras/supervision/nueva?error={error}", status_code=303)
    return RedirectResponse(url=f"/muestras/supervision/{supervision_id}?guardado=1", status_code=303)


def _id_profesional_responsable(formulario):
    valor = formulario.get("responsable_auditoria_id")
    return int(valor) if valor else None


@router.get("/supervision/{supervision_id}", response_class=HTMLResponse)
async def supervision_detalle(request: Request, supervision_id: int, usuario=Depends(requiere_permiso("calidad"))):
    registro = supervision.obtener_supervision(supervision_id)
    if not registro:
        raise HTTPException(status_code=404, detail="La supervisión no existe.")
    return templates.TemplateResponse(
        request=request, name="muestras/supervision_detalle.html",
        context={"usuario": usuario, "supervision": registro, "guardado": request.query_params.get("guardado")},
    )


@router.get("/{muestra_id}", response_class=HTMLResponse)
async def ver_muestra(request: Request, muestra_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    muestra = muestras.obtener(muestra_id)
    if not muestra:
        raise HTTPException(status_code=404, detail="La muestra no existe.")
    return templates.TemplateResponse(
        request=request, name="muestras/ver.html",
        context={"usuario": usuario, "muestra": muestra, "estados": muestras.ESTADOS, "guardado": request.query_params.get("guardado")},
    )


@router.post("/{muestra_id}/cambiar-estado")
async def cambiar_estado(
    muestra_id: int,
    nuevo_estado: str = Form(...), observaciones: str = Form(""), incidencia: str = Form(""),
    responsable_entrega: str = Form(""), responsable_recibe: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    try:
        muestras.cambiar_estado(
            muestra_id, nuevo_estado, _id_usuario(usuario), usuario.get("nombre"),
            observaciones=observaciones, incidencia=incidencia or None,
            responsable_entrega=responsable_entrega or None, responsable_recibe=responsable_recibe or None,
        )
    except ValueError as error:
        return RedirectResponse(url=f"/muestras/{muestra_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/muestras/{muestra_id}?guardado=1", status_code=303)
