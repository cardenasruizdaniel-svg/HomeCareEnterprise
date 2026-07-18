"""HomeCare Enterprise - Router: Resultados de Laboratorio Clínico"""

from datetime import date

from fastapi import APIRouter, Body, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos, consultar_uno

from services import laboratorios_service

router = APIRouter(prefix="/laboratorios", tags=["Laboratorio Clínico"])


@router.get("/paciente/{paciente_id}", response_class=HTMLResponse)
async def listado(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    profesionales = consultar_todos(
        "SELECT id, nombre_completo FROM profesionales WHERE estado='ACTIVO' ORDER BY nombre_completo"
    )
    from repositories.catalogo_examenes_laboratorio_repository import listar_examenes

    return templates.TemplateResponse(
        request=request, name="laboratorios/lista.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "resultados": laboratorios_service.listar_por_paciente(paciente_id),
            "profesionales": profesionales,
            "catalogo_examenes": [dict(e) for e in listar_examenes()],
        },
    )


@router.get("/catalogo/{examen_id}/parametros")
async def parametros_de_examen(examen_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    """Parámetros estándar (con su rango normal) de un tipo de examen, para autocompletar el formulario."""
    from repositories.catalogo_examenes_laboratorio_repository import listar_parametros_de_examen
    filas = listar_parametros_de_examen(examen_id)
    return [
        {
            "nombre_parametro": f["nombre_parametro"], "unidad": f["unidad"],
            "rango_min": f["rango_min"], "rango_max": f["rango_max"],
        }
        for f in filas
    ]


@router.post("/registrar", response_class=JSONResponse)
async def registrar(
    datos: dict = Body(...),
    usuario=Depends(requiere_permiso("pacientes")),
):
    try:
        resultado_id = laboratorios_service.registrar_resultado(
            datos["paciente_id"], datos["nombre_examen"], datos.get("laboratorio_realizo", ""),
            datos.get("fecha_orden") or None, datos.get("fecha_resultado") or date.today().isoformat(),
            datos.get("resultado_texto", ""), datos.get("foto_resultado_base64") or None,
            int(datos["profesional_id"]) if datos.get("profesional_id") else None,
            "WEB", usuario.get("id") if isinstance(usuario, dict) else None,
            items=datos.get("items", []),
        )
        return {"ok": True, "id": resultado_id}
    except ValueError as error:
        return {"ok": False, "error": str(error)}


@router.get("/eliminar/{resultado_id}/{paciente_id}")
async def eliminar(resultado_id: int, paciente_id: int, _actor=Depends(requiere_permiso("pacientes"))):
    laboratorios_service.eliminar(resultado_id)
    return RedirectResponse(url=f"/laboratorios/paciente/{paciente_id}", status_code=303)
