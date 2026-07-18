"""HomeCare Enterprise - Router: Plantillas de visita"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from core.dependencies import requiere_permiso, usuario_actual
from core.templates import templates
from database.database import consultar_todos, consultar_uno

from services import plantillas_visita_service

router = APIRouter(prefix="/plantillas-visita", tags=["Plantillas de Visita"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def listado(request: Request, usuario=Depends(requiere_permiso("programacion"))):
    profesionales = consultar_todos(
        "SELECT id, nombre_completo, especialidad_principal FROM profesionales WHERE estado='ACTIVO' ORDER BY nombre_completo"
    )
    from repositories.catalogo_actividades_repository import CatalogoActividadesRepository
    tipos_servicio = ["General"] + [
        dict(a)["nombre"] for a in CatalogoActividadesRepository.listar_activas()
    ]

    return templates.TemplateResponse(
        request=request, name="plantillas_visita/lista.html",
        context={
            "usuario": usuario,
            "plantillas": plantillas_visita_service.listar_todas(),
            "profesionales": profesionales,
            "tipos_servicio": tipos_servicio,
            "roles": plantillas_visita_service.ROLES_DESTINATARIO,
        },
    )


@router.post("/guardar")
async def guardar(
    nombre: str = Form(...),
    tipo_servicio: str = Form("General"),
    subtipo: str = Form(""),
    rol_destinatario: str = Form("Todos"),
    contenido: str = Form(...),
    profesional_id: str = Form(""),
    origen: str = Form("administracion"),
    usuario=Depends(requiere_permiso("programacion")),
):
    plantillas_visita_service.crear_plantilla(
        nombre, tipo_servicio, subtipo, rol_destinatario, contenido,
        int(profesional_id) if profesional_id else None,
        origen == "administracion",
        usuario.get("id") if isinstance(usuario, dict) else None,
    )
    return RedirectResponse(url="/plantillas-visita", status_code=303)


@router.get("/desactivar/{plantilla_id}")
async def desactivar(plantilla_id: int, _actor=Depends(requiere_permiso("programacion"))):
    plantillas_visita_service.desactivar(plantilla_id)
    return RedirectResponse(url="/plantillas-visita", status_code=303)


@router.get("/editar/{plantilla_id}", response_class=HTMLResponse)
async def editar_formulario(request: Request, plantilla_id: int, usuario=Depends(requiere_permiso("programacion"))):
    plantilla = plantillas_visita_service.obtener(plantilla_id)
    if not plantilla:
        return RedirectResponse(url="/plantillas-visita", status_code=303)

    from repositories.catalogo_actividades_repository import CatalogoActividadesRepository
    tipos_servicio = ["General"] + [
        dict(a)["nombre"] for a in CatalogoActividadesRepository.listar_activas()
    ]

    return templates.TemplateResponse(
        request=request, name="plantillas_visita/editar.html",
        context={
            "usuario": usuario, "plantilla": dict(plantilla),
            "tipos_servicio": tipos_servicio, "roles": plantillas_visita_service.ROLES_DESTINATARIO,
        },
    )


@router.post("/editar/{plantilla_id}")
async def editar_guardar(
    request: Request,
    plantilla_id: int,
    nombre: str = Form(...),
    tipo_servicio: str = Form("General"),
    subtipo: str = Form(""),
    rol_destinatario: str = Form("Todos"),
    contenido: str = Form(...),
    usuario=Depends(requiere_permiso("programacion")),
):
    try:
        plantillas_visita_service.actualizar_plantilla(
            plantilla_id, nombre, tipo_servicio, subtipo, rol_destinatario, contenido
        )
    except ValueError as error:
        plantilla = plantillas_visita_service.obtener(plantilla_id)
        from repositories.catalogo_actividades_repository import CatalogoActividadesRepository
        tipos_servicio = ["General"] + [
            dict(a)["nombre"] for a in CatalogoActividadesRepository.listar_activas()
        ]
        return templates.TemplateResponse(
            request=request, name="plantillas_visita/editar.html",
            context={
                "usuario": usuario, "plantilla": dict(plantilla),
                "tipos_servicio": tipos_servicio, "roles": plantillas_visita_service.ROLES_DESTINATARIO,
                "error": str(error),
            },
        )
    return RedirectResponse(url="/plantillas-visita", status_code=303)


# ==========================================
# API: plantillas disponibles para EL PROFESIONAL
# que esta conectado (segun su rol/perfil), usada
# por el formulario de nota de la visita en la web
# y en la app movil.
# ==========================================

@router.get("/api/mis-plantillas", response_class=JSONResponse)
async def api_mis_plantillas(rol: str = None, usuario: dict = Depends(usuario_actual)):

    profesional = consultar_uno(
        "SELECT id, especialidad_principal FROM profesionales WHERE usuario_id=?",
        (usuario["id"],),
    )

    profesional_id = dict(profesional)["id"] if profesional else None

    if rol:
        # El usuario ya eligió explícitamente el tipo de nota
        # (Enfermería, Cuidador, Curaciones, etc.) desde el
        # selector de formato.
        return plantillas_visita_service.listar_disponibles_por_rol(rol, profesional_id)

    if not profesional:
        return []

    return plantillas_visita_service.listar_disponibles_para_profesional(
        dict(profesional)["especialidad_principal"], profesional_id
    )


@router.get("/api/tipos-nota", response_class=JSONResponse)
async def api_tipos_nota(_actor=Depends(usuario_actual)):
    return plantillas_visita_service.TIPOS_NOTA


@router.post("/api/crear-rapida", response_class=JSONResponse)
async def api_crear_rapida(datos: dict, usuario: dict = Depends(usuario_actual)):
    """
    Permite que un profesional de la salud cree su propia
    plantilla desde el mismo cuadro de la nota de visita, sin
    pasar por la pantalla de administración.
    """

    profesional = consultar_uno(
        "SELECT id FROM profesionales WHERE usuario_id=?", (usuario["id"],)
    )

    if not profesional:
        return {"error": "Su usuario no está vinculado a un profesional."}

    profesional = dict(profesional)

    try:
        nuevo_id = plantillas_visita_service.crear_plantilla(
            datos.get("nombre", "Mi plantilla"), "General", "",
            "Todos", datos.get("contenido", ""),
            profesional["id"], False, usuario["id"],
        )
        return {"ok": True, "id": nuevo_id}
    except ValueError as error:
        return {"error": str(error)}
