"""HomeCare Enterprise - Router: Consentimientos Informados"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_uno

from services import consentimientos_service
from services.programas_atencion_service import programa_actual

router = APIRouter(prefix="/consentimientos", tags=["Consentimientos Informados"])


@router.get("/paciente/{paciente_id}", response_class=HTMLResponse)
async def listado(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))

    return templates.TemplateResponse(
        request=request, name="consentimientos/lista.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "consentimientos": consentimientos_service.listar_por_paciente(paciente_id),
            "tipos": consentimientos_service.TIPOS_CONSENTIMIENTO,
        },
    )


@router.get("/generar-texto/{paciente_id}")
async def generar_texto(paciente_id: int, tipo: str, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = dict(consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,)))

    if tipo == "Ingreso al Programa de Atención Domiciliaria":
        programa = programa_actual(paciente_id)
        nombre_programa = programa["programa_nombre"] if programa else ""
        texto = consentimientos_service.generar_texto_ingreso_programa(paciente, nombre_programa)
    else:
        texto = f"CONSENTIMIENTO INFORMADO — {tipo}\n\nPaciente: {paciente.get('primer_nombre','')} {paciente.get('primer_apellido','')}\n\n(Complete aquí el contenido de este consentimiento.)"

    return {"texto": texto}


@router.post("/crear")
async def crear(
    request: Request,
    paciente_id: int = Form(...),
    tipo: str = Form(...),
    contenido_texto: str = Form(...),
    usuario=Depends(requiere_permiso("pacientes")),
):
    try:
        nuevo_id = consentimientos_service.crear_consentimiento(
            paciente_id, tipo, contenido_texto,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
        return templates.TemplateResponse(
            request=request, name="consentimientos/lista.html",
            context={
                "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
                "consentimientos": consentimientos_service.listar_por_paciente(paciente_id),
                "tipos": consentimientos_service.TIPOS_CONSENTIMIENTO,
                "error": str(error),
            },
        )

    return RedirectResponse(url=f"/consentimientos/ver/{nuevo_id}", status_code=303)


@router.get("/ver/{consentimiento_id}", response_class=HTMLResponse)
async def ver(request: Request, consentimiento_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    consentimiento = dict(consentimientos_service.obtener(consentimiento_id))
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (consentimiento["paciente_id"],))

    from services.configuracion_empresa_service import obtener as obtener_config_empresa
    empresa = obtener_config_empresa()

    return templates.TemplateResponse(
        request=request, name="consentimientos/ver.html",
        context={
            "usuario": usuario, "paciente": paciente, "consentimiento": consentimiento,
            "empresa": empresa,
        },
    )


@router.post("/firmar/{consentimiento_id}")
async def firmar(consentimiento_id: int, datos: dict, usuario=Depends(requiere_permiso("pacientes"))):
    try:
        consentimientos_service.firmar_consentimiento(
            consentimiento_id,
            firmante=datos.get("firmante"),
            nombre_firmante=datos.get("nombre_firmante", ""),
            documento_firmante=datos.get("documento_firmante", ""),
            parentesco_firmante=datos.get("parentesco_firmante", ""),
            firma_base64=datos.get("firma_base64"),
        )
        return {"ok": True}
    except ValueError as error:
        return {"ok": False, "error": str(error)}
