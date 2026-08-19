"""HomeCare Enterprise - Router: Recomendaciones e Instrucciones para Exámenes"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse

from core.dependencies import requiere_permiso, usuario_actual
from core.templates import templates

from services import recomendaciones_examenes_service as recomendaciones

router = APIRouter(prefix="/recomendaciones", tags=["Recomendaciones e Instrucciones"])


def _id_usuario(usuario):
    return usuario.get("id") if isinstance(usuario, dict) else None


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel(request: Request, usuario=Depends(requiere_permiso("pacientes"))):
    return templates.TemplateResponse(
        request=request, name="recomendaciones/panel.html",
        context={
            "usuario": usuario, "items": recomendaciones.listar_todo(),
            "categorias": recomendaciones.CATEGORIAS,
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/crear")
async def crear(
    titulo: str = Form(...), tipo_examen: str = Form(...), categoria: str = Form("General"),
    descripcion: str = Form(""), contenido_texto: str = Form(""), archivo: UploadFile = File(None),
    usuario=Depends(requiere_permiso("pacientes")),
):
    archivo_path = None
    try:
        if archivo and archivo.filename:
            from core.config import RECURSOS_DIR
            import re, time
            carpeta = RECURSOS_DIR / "uploads" / "recomendaciones"
            carpeta.mkdir(parents=True, exist_ok=True)
            nombre_limpio = re.sub(r"[^A-Za-z0-9_.-]", "_", archivo.filename)
            nombre_final = f"{int(time.time())}_{nombre_limpio}"
            with open(carpeta / nombre_final, "wb") as f:
                f.write(await archivo.read())
            archivo_path = f"uploads/recomendaciones/{nombre_final}"

        recomendaciones.crear(titulo, tipo_examen, categoria, descripcion, contenido_texto, archivo_path, _id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/recomendaciones?error={error}", status_code=303)
    return RedirectResponse(url="/recomendaciones?guardado=1", status_code=303)


@router.post("/{recomendacion_id}/actualizar")
async def actualizar(
    recomendacion_id: int,
    titulo: str = Form(...), tipo_examen: str = Form(...), categoria: str = Form("General"),
    descripcion: str = Form(""), contenido_texto: str = Form(""), archivo: UploadFile = File(None),
    usuario=Depends(requiere_permiso("pacientes")),
):
    archivo_path = None
    try:
        if archivo and archivo.filename:
            from core.config import RECURSOS_DIR
            import re, time
            carpeta = RECURSOS_DIR / "uploads" / "recomendaciones"
            carpeta.mkdir(parents=True, exist_ok=True)
            nombre_limpio = re.sub(r"[^A-Za-z0-9_.-]", "_", archivo.filename)
            nombre_final = f"{int(time.time())}_{nombre_limpio}"
            with open(carpeta / nombre_final, "wb") as f:
                f.write(await archivo.read())
            archivo_path = f"uploads/recomendaciones/{nombre_final}"

        recomendaciones.actualizar(recomendacion_id, titulo, tipo_examen, categoria, descripcion, contenido_texto, archivo_path)
    except ValueError as error:
        return RedirectResponse(url=f"/recomendaciones?error={error}", status_code=303)
    return RedirectResponse(url="/recomendaciones?guardado=1", status_code=303)


@router.post("/{recomendacion_id}/desactivar")
async def desactivar(recomendacion_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    recomendaciones.desactivar(recomendacion_id)
    return RedirectResponse(url="/recomendaciones?guardado=1", status_code=303)


@router.post("/{recomendacion_id}/reactivar")
async def reactivar(recomendacion_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    recomendaciones.reactivar(recomendacion_id)
    return RedirectResponse(url="/recomendaciones?guardado=1", status_code=303)


@router.get("/{recomendacion_id}/archivo")
async def descargar_archivo(recomendacion_id: int, usuario=Depends(usuario_actual)):
    item = recomendaciones.obtener(recomendacion_id)
    if not item or not item.get("archivo_path"):
        raise HTTPException(status_code=404, detail="El archivo no existe.")
    from core.config import RECURSOS_DIR
    ruta = RECURSOS_DIR / item["archivo_path"]
    if not ruta.exists():
        raise HTTPException(status_code=404, detail="El archivo ya no se encuentra en el servidor.")
    return FileResponse(ruta, filename=ruta.name)


@router.get("/{recomendacion_id}/pdf")
async def descargar_pdf(recomendacion_id: int, usuario=Depends(usuario_actual)):
    """Descarga (o genera al vuelo) el PDF de la recomendación -- para verla, imprimirla, o entregarla físicamente al paciente."""
    try:
        ruta = recomendaciones.generar_pdf(recomendacion_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
    from pathlib import Path
    nombre_descarga = f"{Path(ruta).stem}.pdf" if not str(ruta).endswith(".pdf") else Path(ruta).name
    return FileResponse(ruta, media_type="application/pdf", filename=Path(ruta).name)


@router.get("/buscar")
async def buscar(q: str = "", usuario=Depends(requiere_permiso("pacientes"))):
    """Búsqueda por tipo de examen -- la usa la pantalla de Toma de Muestras, para sugerir la recomendación adecuada."""
    return recomendaciones.buscar_por_tipo_examen(q)


@router.get("/buscar-pacientes")
async def buscar_pacientes(q: str = "", usuario=Depends(requiere_permiso("pacientes"))):
    """Búsqueda de pacientes por nombre o documento -- para elegir a quién enviarle la recomendación desde el panel."""
    from database.database import consultar_todos
    if not q or len(q) < 2:
        return []
    filas = consultar_todos(
        "SELECT id, documento, primer_nombre, primer_apellido, celular, correo FROM pacientes "
        "WHERE (primer_nombre LIKE ? OR primer_apellido LIKE ? OR documento LIKE ?) AND UPPER(estado)='ACTIVO' LIMIT 10",
        (f"%{q}%", f"%{q}%", f"%{q}%"),
    )
    return [dict(f) for f in filas]


@router.post("/{recomendacion_id}/enviar/{paciente_id}", response_class=JSONResponse)
async def enviar(request: Request, recomendacion_id: int, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    from core.config import PUBLIC_BASE_URL
    base_url = PUBLIC_BASE_URL if PUBLIC_BASE_URL else str(request.base_url)
    try:
        resultado = recomendaciones.enviar_a_paciente(recomendacion_id, paciente_id, base_url=base_url)
        return {"ok": True, **resultado}
    except ValueError as error:
        return {"ok": False, "error": str(error)}
