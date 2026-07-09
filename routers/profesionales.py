"""
=========================================================
HomeCare Enterprise
Router: Profesionales (equipo interdisciplinario)
Reconstruido: el archivo original estaba corrupto
(sin router, sin imports, llamaba funciones inexistentes).
=========================================================
"""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import PlainTextResponse

from services import profesionales_import_service
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.roles import ROLES
from core.templates import templates
from database.database import consultar_todos, consultar_uno

from services import profesionales_service

router = APIRouter(prefix="/profesionales", tags=["Profesionales"])


# ==========================================
# LISTADO
# ==========================================

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def listado(
    request: Request,
    usuario=Depends(requiere_permiso("profesionales")),
):
    profesionales = profesionales_service.listar()

    return templates.TemplateResponse(
        request=request,
        name="profesionales/lista.html",
        context={
            "usuario": usuario,
            "profesionales": profesionales,
        },
    )


# ==========================================
# NUEVO
# ==========================================

@router.get("/nuevo", response_class=HTMLResponse)
async def nuevo(
    request: Request,
    usuario=Depends(requiere_permiso("profesionales")),
):
    from repositories.catalogo_bancos_repository import CatalogoBancosRepository

    return templates.TemplateResponse(
        request=request,
        name="profesionales/nuevo.html",
        context={
            "usuario": usuario,
            "roles": ROLES,
            "lista_bancos": [dict(b) for b in CatalogoBancosRepository.listar_activos()],
        },
    )


# ==========================================
# GUARDAR
# ==========================================

@router.post("/guardar")
async def guardar(
    request: Request,
    tipo_documento: str = Form(""),
    documento: str = Form(...),
    registro_profesional: str = Form(""),
    especialidad_principal: str = Form(...),
    primer_nombre: str = Form(...),
    segundo_nombre: str = Form(""),
    primer_apellido: str = Form(...),
    segundo_apellido: str = Form(""),
    telefono: str = Form(""),
    celular: str = Form(""),
    correo: str = Form(""),
    direccion: str = Form(""),
    municipio: str = Form(""),
    departamento: str = Form(""),
    capacidad_diaria: int = Form(20),
    acepta_urgencias: int = Form(0),
    radio_cobertura_km: float = Form(10),
    tiempo_promedio_visita: int = Form(45),
    observaciones: str = Form(""),
    tipo_contrato: str = Form("POR_HORAS"),
    valor_hora: float = Form(0),
    salario_fijo: float = Form(0),
    banco: str = Form(""),
    tipo_cuenta: str = Form(""),
    numero_cuenta: str = Form(""),
    firma_base64: str = Form(""),
    nombre_usuario: str = Form(""),
    password: str = Form(""),
    rol_sistema: str = Form(""),
    _actor=Depends(requiere_permiso("profesionales")),
):
    datos_profesional = {
        "tipo_documento": tipo_documento,
        "documento": documento,
        "registro_profesional": registro_profesional,
        "profesion": especialidad_principal,
        "especialidad_principal": especialidad_principal,
        "primer_nombre": primer_nombre,
        "segundo_nombre": segundo_nombre,
        "primer_apellido": primer_apellido,
        "segundo_apellido": segundo_apellido,
        "telefono": telefono,
        "celular": celular,
        "correo": correo,
        "direccion": direccion,
        "municipio": municipio,
        "departamento": departamento,
        "capacidad_diaria": capacidad_diaria,
        "acepta_urgencias": acepta_urgencias,
        "radio_cobertura_km": radio_cobertura_km,
        "tiempo_promedio_visita": tiempo_promedio_visita,
        "observaciones": observaciones,
        "tipo_contrato": tipo_contrato,
        "valor_hora": valor_hora,
        "salario_fijo": salario_fijo,
        "banco": banco,
        "tipo_cuenta": tipo_cuenta,
        "numero_cuenta": numero_cuenta,
        "firma_base64": firma_base64 or None,
    }

    try:
        profesionales_service.crear_con_cuenta_acceso(
            datos_profesional, nombre_usuario or None, password or None,
            rol_sistema or especialidad_principal,
            usuario_creacion=_actor.get("id") if isinstance(_actor, dict) else None,
        )
    except ValueError as error:
        from repositories.catalogo_bancos_repository import CatalogoBancosRepository
        return templates.TemplateResponse(
            request=request, name="profesionales/nuevo.html",
            context={
                "usuario": _actor, "roles": ROLES,
                "lista_bancos": [dict(b) for b in CatalogoBancosRepository.listar_activos()],
                "error": str(error), "datos_previos": {**datos_profesional, "nombre_usuario": nombre_usuario, "rol_sistema": rol_sistema},
            },
        )

    return RedirectResponse(url="/profesionales", status_code=303)


# ==========================================
# EDITAR
# ==========================================

@router.get("/editar/{id}", response_class=HTMLResponse)
async def editar(
    request: Request,
    id: int,
    usuario=Depends(requiere_permiso("profesionales")),
):
    profesional = profesionales_service.obtener(id)

    from repositories.catalogo_bancos_repository import CatalogoBancosRepository

    cuenta_vinculada = None
    if profesional and dict(profesional).get("usuario_id"):
        cuenta_vinculada = consultar_uno(
            "SELECT * FROM usuarios WHERE id=?", (dict(profesional)["usuario_id"],)
        )
        cuenta_vinculada = dict(cuenta_vinculada) if cuenta_vinculada else None

    return templates.TemplateResponse(
        request=request,
        name="profesionales/editar.html",
        context={
            "usuario": usuario,
            "profesional": profesional,
            "roles": ROLES,
            "cuenta_vinculada": cuenta_vinculada,
            "lista_bancos": [dict(b) for b in CatalogoBancosRepository.listar_activos()],
        },
    )


# ==========================================
# ACTUALIZAR
# ==========================================

@router.post("/actualizar/{id}")
async def actualizar(
    request: Request,
    id: int,
    especialidad_principal: str = Form(...),
    registro_profesional: str = Form(""),
    estado: str = Form("ACTIVO"),
    telefono: str = Form(""),
    celular: str = Form(""),
    correo: str = Form(""),
    direccion: str = Form(""),
    municipio: str = Form(""),
    departamento: str = Form(""),
    capacidad_diaria: int = Form(20),
    radio_cobertura_km: float = Form(10),
    tiempo_promedio_visita: int = Form(45),
    observaciones: str = Form(""),
    tipo_contrato: str = Form("POR_HORAS"),
    valor_hora: float = Form(0),
    salario_fijo: float = Form(0),
    banco: str = Form(""),
    tipo_cuenta: str = Form(""),
    numero_cuenta: str = Form(""),
    nombre_usuario: str = Form(""),
    password: str = Form(""),
    rol_sistema: str = Form(""),
    _actor=Depends(requiere_permiso("profesionales")),
):
    try:
        nuevo_usuario_id = profesionales_service.gestionar_cuenta_acceso(
            id, nombre_usuario, password, rol_sistema
        )
    except ValueError as error:
        profesional = profesionales_service.obtener(id)
        from repositories.catalogo_bancos_repository import CatalogoBancosRepository
        cuenta_vinculada = None
        if profesional and dict(profesional).get("usuario_id"):
            cuenta_vinculada = consultar_uno("SELECT * FROM usuarios WHERE id=?", (dict(profesional)["usuario_id"],))
            cuenta_vinculada = dict(cuenta_vinculada) if cuenta_vinculada else None
        return templates.TemplateResponse(
            request=request, name="profesionales/editar.html",
            context={
                "usuario": _actor, "profesional": profesional, "roles": ROLES,
                "cuenta_vinculada": cuenta_vinculada,
                "lista_bancos": [dict(b) for b in CatalogoBancosRepository.listar_activos()],
                "error": str(error),
            },
        )

    profesionales_service.actualizar(
        id,
        {
            "profesion": especialidad_principal,
            "especialidad_principal": especialidad_principal,
            "registro_profesional": registro_profesional,
            "telefono": telefono,
            "celular": celular,
            "correo": correo,
            "direccion": direccion,
            "municipio": municipio,
            "departamento": departamento,
            "capacidad_diaria": capacidad_diaria,
            "radio_cobertura_km": radio_cobertura_km,
            "tiempo_promedio_visita": tiempo_promedio_visita,
            "observaciones": observaciones,
            "tipo_contrato": tipo_contrato,
            "valor_hora": valor_hora,
            "salario_fijo": salario_fijo,
            "banco": banco,
            "tipo_cuenta": tipo_cuenta,
            "numero_cuenta": numero_cuenta,
            "usuario_id": nuevo_usuario_id,
        },
        usuario_id=_actor.get("id") if isinstance(_actor, dict) else None,
    )

    profesionales_service.cambiar_estado(id, estado)

    return RedirectResponse(url="/profesionales", status_code=303)


# ==========================================
# ELIMINAR
# ==========================================

@router.get("/eliminar/{id}")
async def eliminar(
    id: int,
    _actor=Depends(requiere_permiso("profesionales")),
):
    profesionales_service.cambiar_estado(id, "INACTIVO")

    return RedirectResponse(url="/profesionales", status_code=303)

# ==========================================
# IMPORTACIÓN MASIVA DE PROFESIONALES (CSV)
# ==========================================

@router.get("/importar/formulario")
async def importar_formulario(request: Request, usuario=Depends(requiere_permiso("profesionales"))):
    return templates.TemplateResponse(
        request=request, name="profesionales/importar.html",
        context={"usuario": usuario},
    )


@router.get("/importar/plantilla")
async def importar_plantilla(_actor=Depends(requiere_permiso("profesionales"))):
    from fastapi.responses import Response
    return Response(
        content=profesionales_import_service.plantilla_excel(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_profesionales.xlsx"},
    )


@router.post("/importar")
async def importar(
    request: Request,
    archivo: UploadFile = File(...),
    usuario=Depends(requiere_permiso("profesionales")),
):
    contenido = await archivo.read()

    try:
        resultado = profesionales_import_service.importar_profesionales_excel(
            contenido, usuario.get("id") if isinstance(usuario, dict) else None
        )
    except ValueError as error:
        return templates.TemplateResponse(
            request=request, name="profesionales/importar.html",
            context={"usuario": usuario, "error": str(error)},
        )

    return templates.TemplateResponse(
        request=request, name="profesionales/importar.html",
        context={"usuario": usuario, "resultado": resultado},
    )

# ==========================================
# FIRMA DIGITAL DEL PROFESIONAL
# ==========================================

@router.post("/actualizar-firma/{profesional_id}")
async def actualizar_firma_endpoint(
    profesional_id: int,
    datos: dict,
    usuario=Depends(requiere_permiso("profesionales")),
):
    try:
        profesionales_service.actualizar_firma(profesional_id, datos.get("firma_base64"))
        return {"ok": True}
    except ValueError as error:
        return {"ok": False, "error": str(error)}
