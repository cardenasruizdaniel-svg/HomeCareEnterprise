from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import PlainTextResponse, RedirectResponse
from core.dependencies import requiere_permiso
from core.templates import templates
from services.pacientes_service import PacientesService
from services.alertas_service import obtener_alertas, obtener_resumen_seguridad
from services import pacientes_import_service

router=APIRouter(prefix="/pacientes",tags=["Pacientes"])

@router.get("/")
async def listado(request:Request,q:str=Query(""),pagina:int=1,usuario=Depends(requiere_permiso("pacientes"))):
    pacientes=PacientesService.buscar(q) if q.strip() else PacientesService.listar()

    # Los roles administrativos/de coordinación ven TODOS los
    # pacientes (los necesitan para crearlos, asignarlos, etc.).
    # Los roles clinicos (medico, enfermero, cuidador, terapeuta...)
    # solo ven los pacientes que tienen agendados/asignados a
    # su propio usuario, para no mezclarse con los de otros
    # profesionales.
    from core.permissions import tiene_permiso
    rol_actual = usuario.get("rol") if isinstance(usuario, dict) else None
    roles_acceso_total = ("Administrador", "Director Médico", "Coordinador", "Administrativo")

    if rol_actual and rol_actual not in roles_acceso_total and not tiene_permiso(rol_actual, "usuarios"):
        from database.database import consultar_escalar, consultar_todos
        profesional = consultar_escalar(
            "SELECT id FROM profesionales WHERE usuario_id=?", (usuario.get("id"),)
        )
        if profesional:
            ids_asignados = {
                dict(f)["paciente_id"] for f in consultar_todos(
                    """
                    SELECT DISTINCT paciente_id FROM servicios_paciente WHERE profesional_id=?
                    UNION
                    SELECT DISTINCT paciente_id FROM programaciones WHERE profesional_id=?
                    """,
                    (profesional, profesional),
                )
            }
            pacientes = [p for p in pacientes if dict(p)["id"] in ids_asignados]
        else:
            pacientes = []

    dashboard=getattr(PacientesService,"dashboard_enterprise",lambda:{"total":len(pacientes)})()
    estadisticas=getattr(PacientesService,"estadisticas",lambda:{})()
    return templates.TemplateResponse(request=request,name="pacientes/listado.html",context={
        "request":request,"usuario":usuario,"titulo":"Gestión Integral de Pacientes",
        "pacientes":pacientes,"texto_busqueda":q,"pagina":pagina,
        "dashboard":dashboard,"estadisticas":estadisticas,
        "total_pacientes":dashboard.get("total",0),
        "pacientes_activos":dashboard.get("total",0),
        "pacientes_inactivos":0,"nuevos_mes":0})

@router.get("/buscar")
async def buscar(q:str="",usuario=Depends(requiere_permiso("pacientes"))):
    return RedirectResponse(url=f"/pacientes/?q={q}",status_code=302)


# ==========================================
# NUEVO PACIENTE
# ==========================================

@router.get("/nuevo")
async def nuevo(
    request: Request,
    usuario=Depends(requiere_permiso("pacientes")),
):
    from repositories.catalogo_eps_repository import CatalogoEPSRepository
    from core.zonas import ZONAS_CIUDAD

    return templates.TemplateResponse(
        request=request,
        name="pacientes/nuevo.html",
        context={
            "usuario": usuario,
            "lista_eps": [dict(e) for e in CatalogoEPSRepository.listar_activas()],
            "zonas_ciudad": ZONAS_CIUDAD,
        },
    )


@router.post("/guardar")
async def guardar(
    request: Request,
    tipo_documento: str = Form("CC"),
    documento: str = Form(...),
    primer_nombre: str = Form(...),
    segundo_nombre: str = Form(""),
    primer_apellido: str = Form(...),
    segundo_apellido: str = Form(""),
    fecha_nacimiento: str = Form(""),
    sexo: str = Form(""),
    eps: str = Form(""),
    regimen: str = Form(""),
    tipo_cuidado: str = Form("No Ventilado"),
    zona_ciudad: str = Form(""),
    telefono: str = Form(""),
    celular: str = Form(""),
    correo: str = Form(""),
    direccion: str = Form(""),
    barrio: str = Form(""),
    municipio: str = Form(""),
    departamento: str = Form(""),
    codigo_municipio_divipola: str = Form(""),
    latitud: str = Form(""),
    longitud: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    datos = {
        "tipo_documento": tipo_documento,
        "documento": documento,
        "primer_nombre": primer_nombre,
        "segundo_nombre": segundo_nombre,
        "primer_apellido": primer_apellido,
        "segundo_apellido": segundo_apellido,
        "fecha_nacimiento": fecha_nacimiento,
        "sexo": sexo,
        "eps": eps,
        "regimen": regimen,
        "tipo_cuidado": tipo_cuidado,
        "zona_ciudad": zona_ciudad,
        "telefono": telefono,
        "celular": celular,
        "correo": correo,
        "direccion": direccion,
        "barrio": barrio,
        "municipio": municipio,
        "departamento": departamento,
        "codigo_municipio_divipola": codigo_municipio_divipola or None,
        "latitud": float(latitud) if latitud else None,
        "longitud": float(longitud) if longitud else None,
    }

    try:
        nuevo_id = PacientesService.guardar(datos)
    except ValueError as error:
        return templates.TemplateResponse(
            request=request,
            name="pacientes/nuevo.html",
            context={"usuario": usuario, "error": str(error)},
        )
    except Exception as error:
        return templates.TemplateResponse(
            request=request,
            name="pacientes/nuevo.html",
            context={"usuario": usuario, "error": f"No se pudo guardar el paciente: {error}"},
        )

    return RedirectResponse(url=f"/pacientes/{nuevo_id}", status_code=303)


# ==========================================
# EDITAR PACIENTE
# ==========================================

@router.get("/editar/{paciente_id}")
async def editar(
    request: Request,
    paciente_id: int,
    usuario=Depends(requiere_permiso("pacientes")),
):
    paciente = PacientesService.obtener(paciente_id)

    if not paciente:
        return RedirectResponse(url="/pacientes/", status_code=303)

    from repositories.catalogo_eps_repository import CatalogoEPSRepository
    from core.zonas import ZONAS_CIUDAD

    return templates.TemplateResponse(
        request=request,
        name="pacientes/editar.html",
        context={
            "usuario": usuario, "paciente": paciente,
            "lista_eps": [dict(e) for e in CatalogoEPSRepository.listar_activas()],
            "zonas_ciudad": ZONAS_CIUDAD,
        },
    )


@router.post("/actualizar/{paciente_id}")
async def actualizar(
    request: Request,
    paciente_id: int,
    tipo_documento: str = Form("CC"),
    documento: str = Form(...),
    primer_nombre: str = Form(...),
    segundo_nombre: str = Form(""),
    primer_apellido: str = Form(...),
    segundo_apellido: str = Form(""),
    fecha_nacimiento: str = Form(""),
    sexo: str = Form(""),
    eps: str = Form(""),
    regimen: str = Form(""),
    tipo_cuidado: str = Form("No Ventilado"),
    zona_ciudad: str = Form(""),
    telefono: str = Form(""),
    celular: str = Form(""),
    correo: str = Form(""),
    direccion: str = Form(""),
    barrio: str = Form(""),
    municipio: str = Form(""),
    departamento: str = Form(""),
    codigo_municipio_divipola: str = Form(""),
    latitud: str = Form(""),
    longitud: str = Form(""),
    estado: str = Form("ACTIVO"),
    estado_vital: str = Form("Vivo"),
    fecha_fallecimiento: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    datos = {
        "tipo_documento": tipo_documento,
        "documento": documento,
        "primer_nombre": primer_nombre,
        "segundo_nombre": segundo_nombre,
        "primer_apellido": primer_apellido,
        "segundo_apellido": segundo_apellido,
        "fecha_nacimiento": fecha_nacimiento,
        "sexo": sexo,
        "eps": eps,
        "regimen": regimen,
        "tipo_cuidado": tipo_cuidado,
        "zona_ciudad": zona_ciudad,
        "telefono": telefono,
        "celular": celular,
        "correo": correo,
        "direccion": direccion,
        "barrio": barrio,
        "municipio": municipio,
        "departamento": departamento,
        "latitud": float(latitud) if latitud else None,
        "longitud": float(longitud) if longitud else None,
        # Se sincroniza con el estado real de las coordenadas: si
        # se borran desde aquí, se resetea (para que la app vuelva
        # a pedirle al profesional que la registre); si se
        # diligencian, queda marcada como confirmada.
        "ubicacion_confirmada": 1 if (latitud and longitud) else 0,
        "codigo_municipio_divipola": codigo_municipio_divipola or None,
        "estado": estado,
        "estado_vital": estado_vital,
        "fecha_fallecimiento": fecha_fallecimiento if estado_vital == "Fallecido" else None,
    }

    try:
        PacientesService.actualizar(paciente_id, datos)
    except Exception as error:
        paciente = PacientesService.obtener(paciente_id)
        return templates.TemplateResponse(
            request=request,
            name="pacientes/editar.html",
            context={"usuario": usuario, "paciente": paciente, "error": str(error)},
        )

    return RedirectResponse(url=f"/pacientes/{paciente_id}", status_code=303)


# ==========================================
# FICHA DEL PACIENTE
# (al entrar, se muestran de inmediato las alertas de
# seguridad: alergias activas y medicamentos que el
# paciente esta tomando)
# ==========================================

@router.get("/{paciente_id}")
async def ficha(
    request: Request,
    paciente_id: int,
    usuario=Depends(requiere_permiso("pacientes")),
):
    paciente = PacientesService.obtener(paciente_id)

    if not paciente:
        return RedirectResponse(url="/pacientes/", status_code=303)

    resumen_seguridad = obtener_resumen_seguridad(paciente_id)
    alertas = obtener_alertas(paciente_id)

    from services.programas_atencion_service import programa_actual
    programa_paciente = programa_actual(paciente_id)

    from services.resumen_clinico_service import resumen_completo
    resumen_clinico = resumen_completo(paciente_id)

    return templates.TemplateResponse(
        request=request,
        name="pacientes/ficha.html",
        context={
            "usuario": usuario,
            "paciente": paciente,
            "paciente_id": paciente_id,
            "resumen_seguridad": resumen_seguridad,
            "alertas": alertas,
            "programa_paciente": programa_paciente,
            "resumen_clinico": resumen_clinico,
        },
    )

# ==========================================
# IMPORTACIÓN MASIVA DE PACIENTES (CSV)
# ==========================================

@router.get("/importar/formulario")
async def importar_formulario(request: Request, usuario=Depends(requiere_permiso("pacientes"))):
    return templates.TemplateResponse(
        request=request, name="pacientes/importar.html",
        context={"usuario": usuario},
    )


@router.get("/importar/plantilla")
async def importar_plantilla(_actor=Depends(requiere_permiso("pacientes"))):
    from fastapi.responses import Response
    return Response(
        content=pacientes_import_service.plantilla_excel(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_pacientes.xlsx"},
    )


@router.post("/importar")
async def importar(
    request: Request,
    archivo: UploadFile = File(...),
    usuario=Depends(requiere_permiso("pacientes")),
):
    contenido = await archivo.read()

    try:
        resultado = pacientes_import_service.importar_pacientes_excel(
            contenido, usuario.get("id") if isinstance(usuario, dict) else None
        )
    except ValueError as error:
        return templates.TemplateResponse(
            request=request, name="pacientes/importar.html",
            context={"usuario": usuario, "error": str(error)},
        )

    return templates.TemplateResponse(
        request=request, name="pacientes/importar.html",
        context={"usuario": usuario, "resultado": resultado},
    )
