"""HomeCare Enterprise - Router: Posible Programación de Visitas (propuesta para el día siguiente)"""

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from core.dependencies import requiere_permiso
from core.templates import templates

router = APIRouter(prefix="/posible-programacion", tags=["Posible Programación"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def ver_posible_programacion(
    request: Request, fecha: str = None, usuario=Depends(requiere_permiso("programacion")),
):
    from services.posible_programacion_service import obtener_posible_programacion
    from services.profesionales_service import activos

    resultado = obtener_posible_programacion(fecha)
    # Esta ruta es solo de visitas médicas -- así que el selector
    # de profesional solo debe mostrar médicos, no cualquier
    # profesional activo (enfermeros, terapeutas, etc. no
    # aplican para este tipo de visita).
    todos_activos = [dict(p) for p in activos()]
    profesionales = [
        p for p in todos_activos
        if "médic" in (p.get("especialidad_principal") or "").lower()
        or "medic" in (p.get("especialidad_principal") or "").lower()
    ]

    return templates.TemplateResponse(
        request=request, name="posible_programacion/panel.html",
        context={
            "usuario": usuario, "resultado": resultado, "profesionales": profesionales,
            "mensaje": request.query_params.get("mensaje"),
        },
    )


@router.post("/programar-seleccionados")
async def programar_seleccionados(datos: dict = Body(...), usuario=Depends(requiere_permiso("programacion"))):
    """
    Recibe la lista de candidatos que el usuario decidió sí
    programar (con el profesional asignado a cada uno), y los
    lleva a la agenda real -- el resto de candidatos que no se
    seleccionaron simplemente quedan pendientes, para revisarlos
    otro día.
    """
    from services.gestion_visitas_service import programar_visita

    seleccionados = datos.get("seleccionados", [])
    fecha = datos.get("fecha")
    if not fecha:
        raise HTTPException(status_code=400, detail="Debe indicar la fecha objetivo.")

    programados, errores = [], []
    usuario_id = usuario.get("id") if isinstance(usuario, dict) else None

    for item in seleccionados:
        try:
            confirmacion = programar_visita(
                int(item["planilla_id"]), fecha, item.get("hora_inicio") or "08:00", item.get("hora_fin") or "09:00",
                int(item["profesional_id"]), usuario_id,
            )
            programados.append(confirmacion["programacion_id"])
        except Exception as error:
            errores.append(f"{item.get('nombre', 'Paciente')}: {error}")

    return {"programados": len(programados), "errores": errores, "programacion_ids": programados}


@router.get("/informe-confirmacion")
async def descargar_informe_confirmacion(ids: str, usuario=Depends(requiere_permiso("programacion"))):
    """
    Genera el PDF con el detalle de las visitas que se acaban
    de programar (paciente, dirección, celular, fecha, hora,
    profesional) -- listo para mandarle a quien se encarga de
    llamar a confirmar cada visita con el paciente.
    """
    from fastapi.responses import FileResponse
    from services.posible_programacion_service import generar_informe_confirmacion_pdf

    try:
        lista_ids = [int(i) for i in ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Lista de IDs no válida.")

    if not lista_ids:
        raise HTTPException(status_code=400, detail="No hay visitas para incluir en el informe.")

    ruta = generar_informe_confirmacion_pdf(lista_ids)
    return FileResponse(ruta, media_type="application/pdf", filename="informe_visitas_a_confirmar.pdf")
