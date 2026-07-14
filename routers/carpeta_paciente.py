"""
HomeCare Enterprise - Router: Carpeta del Paciente

Vista administrativa (distinta de la Historia Clínica formal)
que agrupa por fecha TODO lo que se le ha registrado a un
paciente -- notas clínicas, órdenes, exámenes, informes de
cuidador y consentimientos -- para poder revisarlo o
imprimirlo/descargarlo rápidamente, por ejemplo cuando hay que
enviarle al paciente su historia clínica reciente junto con una
orden médica.
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_uno

from services.historia_clinica_service import obtener_carpeta_completa

router = APIRouter(prefix="/pacientes", tags=["Carpeta del Paciente"])


@router.get("/{paciente_id}/carpeta", response_class=HTMLResponse)
async def ver_carpeta_paciente(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    if not paciente:
        raise HTTPException(status_code=404, detail="El paciente no existe.")

    carpeta = obtener_carpeta_completa(paciente_id)
    return templates.TemplateResponse(
        request=request, name="pacientes/carpeta.html",
        context={"usuario": usuario, "paciente": dict(paciente), "carpeta": carpeta},
    )


@router.post("/{paciente_id}/carpeta/generar-pdf")
async def generar_pdf_carpeta(paciente_id: int, datos: dict = Body(...), usuario=Depends(requiere_permiso("pacientes"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    if not paciente:
        raise HTTPException(status_code=404, detail="El paciente no existe.")

    ids_seleccionados = set(datos.get("ids", []))
    if not ids_seleccionados:
        raise HTTPException(status_code=400, detail="Debe seleccionar al menos un registro.")

    carpeta = obtener_carpeta_completa(paciente_id)
    eventos_todos = [e for grupo in carpeta["eventos_por_fecha"] for e in grupo["eventos"]]
    eventos_seleccionados = [e for e in eventos_todos if e.get("clave_unica") in ids_seleccionados]

    from services.configuracion_empresa_service import obtener as obtener_config_empresa
    from services.carpeta_paciente_pdf_service import generar_pdf_carpeta as generar_pdf
    config = obtener_config_empresa()

    ruta = generar_pdf(dict(paciente), eventos_seleccionados, config.get("razon_social", ""))
    return FileResponse(ruta, media_type="application/pdf", filename=f"carpeta_paciente_{paciente_id}.pdf")
