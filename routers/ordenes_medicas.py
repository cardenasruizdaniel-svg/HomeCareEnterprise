"""
=========================================================
HomeCare Enterprise
Router: Ordenes Medicas

Al guardar una orden, el sistema genera el PDF y lo envia
automaticamente al paciente por WhatsApp y correo.
=========================================================
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from database.database import consultar_todos

from services.ordenes_service import OrdenesService

router = APIRouter(prefix="/ordenes-medicas", tags=["Órdenes Médicas"])


# ==========================================
# LISTADO POR PACIENTE
# ==========================================

@router.get("/{paciente_id}", response_class=HTMLResponse)
async def listado(
    request: Request,
    paciente_id: int,
    usuario=Depends(requiere_permiso("ordenes")),
):
    ordenes = OrdenesService.listar_por_paciente(paciente_id)

    return templates.TemplateResponse(
        request=request,
        name="ordenes_medicas/lista.html",
        context={
            "usuario": usuario,
            "paciente_id": paciente_id,
            "ordenes": ordenes,
        },
    )


# ==========================================
# NUEVO
# ==========================================

@router.get("/nuevo/{paciente_id}", response_class=HTMLResponse)
async def nuevo(
    request: Request,
    paciente_id: int,
    usuario=Depends(requiere_permiso("ordenes")),
):
    profesionales = consultar_todos(
        "SELECT * FROM profesionales WHERE estado='ACTIVO' "
        "ORDER BY primer_apellido, primer_nombre"
    )

    return templates.TemplateResponse(
        request=request,
        name="ordenes_medicas/nuevo.html",
        context={
            "usuario": usuario,
            "paciente_id": paciente_id,
            "profesionales": profesionales,
        },
    )


# ==========================================
# GUARDAR (genera PDF + envía WhatsApp/correo)
# ==========================================

@router.post("/guardar")
async def guardar(
    request: Request,
    paciente_id: int = Form(...),
    profesional_id: int = Form(...),
    tipo: str = Form(...),
    descripcion: str = Form(...),
    codigo_cups: str = Form(""),
    usuario=Depends(requiere_permiso("ordenes")),
):
    profesionales = consultar_todos(
        "SELECT * FROM profesionales WHERE estado='ACTIVO' "
        "ORDER BY primer_apellido, primer_nombre"
    )

    try:
        resultado = OrdenesService.crear_y_enviar(
            paciente_id=paciente_id,
            profesional_id=profesional_id,
            tipo=tipo,
            descripcion=descripcion,
            codigo_cups=codigo_cups,
            usuario_creacion=usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        return templates.TemplateResponse(
            request=request,
            name="ordenes_medicas/nuevo.html",
            context={
                "usuario": usuario,
                "paciente_id": paciente_id,
                "profesionales": profesionales,
                "error": str(error),
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="ordenes_medicas/nuevo.html",
        context={
            "usuario": usuario,
            "paciente_id": paciente_id,
            "profesionales": profesionales,
            "resultado": resultado,
        },
    )


# ==========================================
# REENVIAR
# ==========================================

@router.get("/reenviar/{orden_id}")
async def reenviar(
    orden_id: int,
    usuario=Depends(requiere_permiso("ordenes")),
):
    orden = OrdenesService.obtener(orden_id)

    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")

    OrdenesService.reenviar(orden_id)

    return RedirectResponse(
        url=f"/ordenes-medicas/{orden['paciente_id']}",
        status_code=303,
    )


# ==========================================
# DESCARGA PÚBLICA (sin login) - solo para que la API de
# WhatsApp pueda descargar el adjunto. Protegida por un
# token aleatorio propio de cada orden, no por sesión.
# ==========================================

@router.get("/pdf-publico/{orden_id}/{token}")
async def pdf_publico(orden_id: int, token: str):
    from repositories.ordenes_repository import OrdenesRepository
    from services.orden_pdf_service import generar_pdf_orden
    from database.database import consultar_uno

    orden = OrdenesRepository.obtener_por_token(orden_id, token)

    if not orden:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    orden = dict(orden)
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (orden["paciente_id"],))
    paciente = dict(paciente) if paciente else {}

    profesional = None
    if orden.get("profesional_id"):
        profesional = consultar_uno(
            "SELECT * FROM profesionales WHERE id=?", (orden["profesional_id"],)
        )
        profesional = dict(profesional) if profesional else None

    ruta = generar_pdf_orden(orden, paciente, profesional)

    return FileResponse(ruta, media_type="application/pdf", filename=f"orden_{orden_id}.pdf")


# ==========================================
# DESCARGAR / SERVIR EL PDF (uso interno, con sesión)
# ==========================================

@router.get("/pdf/{orden_id}")
async def pdf(
    orden_id: int,
    usuario=Depends(requiere_permiso("ordenes")),
):
    orden = OrdenesService.obtener(orden_id)

    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")

    from services.orden_pdf_service import generar_pdf_orden
    from database.database import consultar_uno

    orden = dict(orden)
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (orden["paciente_id"],))
    paciente = dict(paciente) if paciente else {}

    profesional = None
    if orden.get("profesional_id"):
        profesional = consultar_uno(
            "SELECT * FROM profesionales WHERE id=?", (orden["profesional_id"],)
        )
        profesional = dict(profesional) if profesional else None

    ruta = generar_pdf_orden(orden, paciente, profesional)

    if not Path(ruta).exists():
        raise HTTPException(status_code=404, detail="No se pudo generar el PDF.")

    return FileResponse(
        ruta,
        media_type="application/pdf",
        filename=f"orden_{orden_id}.pdf",
    )
