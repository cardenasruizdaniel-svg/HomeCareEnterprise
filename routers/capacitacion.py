"""HomeCare Enterprise - Router: Módulo de Capacitación"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse

from core.dependencies import usuario_actual, requiere_gerencia_o_admin
from core.templates import templates

from services import capacitacion_service as capacitacion

router = APIRouter(prefix="/capacitacion", tags=["Capacitación"])


def _id_usuario(usuario):
    return usuario.get("id") if isinstance(usuario, dict) else None


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel(request: Request, usuario=Depends(usuario_actual)):
    categorias = capacitacion.listar_categorias_con_contenido(usuario.get("rol"), "Web")
    return templates.TemplateResponse(
        request=request, name="capacitacion/panel.html",
        context={"usuario": usuario, "categorias": categorias},
    )


@router.get("/{capacitacion_id}/archivo")
async def descargar_archivo(capacitacion_id: int, usuario=Depends(usuario_actual)):
    item = capacitacion.obtener(capacitacion_id)
    if not item or not item.get("archivo_path"):
        raise HTTPException(status_code=404, detail="El archivo no existe.")

    roles = [r.strip() for r in (item.get("roles_permitidos") or "Todos").split(",")]
    if "Todos" not in roles and usuario.get("rol") not in roles:
        raise HTTPException(status_code=403, detail="Este contenido no está disponible para su perfil.")

    from core.config import RECURSOS_DIR
    ruta = RECURSOS_DIR / item["archivo_path"]
    if not ruta.exists():
        raise HTTPException(status_code=404, detail="El archivo ya no se encuentra en el servidor.")
    return FileResponse(ruta, filename=ruta.name)


EXTENSIONES_OFFICE = (".pptx", ".ppt", ".docx", ".doc", ".xlsx", ".xls")


@router.get("/{capacitacion_id}/ver", response_class=HTMLResponse)
async def ver_contenido(request: Request, capacitacion_id: int, usuario=Depends(usuario_actual)):
    """
    Pantalla de visualización: abre el PDF directo en el
    navegador, o -- si es una presentación de PowerPoint/Word/
    Excel -- la muestra con el visor de Office en línea, para
    que se pueda repasar sin tener que descargar nada, ideal
    para volver a consultarla cuando surja una duda.
    """
    item = capacitacion.obtener(capacitacion_id)
    if not item:
        raise HTTPException(status_code=404, detail="El contenido no existe.")

    roles = [r.strip() for r in (item.get("roles_permitidos") or "Todos").split(",")]
    if "Todos" not in roles and usuario.get("rol") not in roles:
        raise HTTPException(status_code=403, detail="Este contenido no está disponible para su perfil.")

    from core.config import PUBLIC_BASE_URL
    extension = ("." + item["archivo_path"].rsplit(".", 1)[-1].lower()) if item.get("archivo_path") and "." in item["archivo_path"] else ""

    # Se usa PUBLIC_BASE_URL si está configurada -- si no, se
    # calcula sola a partir de la misma petición que está
    # entrando, para que el visor de Office funcione sin tener
    # que configurar nada aparte.
    base_url = PUBLIC_BASE_URL.rstrip("/") if PUBLIC_BASE_URL else str(request.base_url).rstrip("/")

    url_visor_publico = None
    if item.get("token_visor"):
        url_visor_publico = f"{base_url}/capacitacion/visor-publico/{item['token_visor']}"

    return templates.TemplateResponse(
        request=request, name="capacitacion/ver.html",
        context={
            "usuario": usuario, "item": item, "es_pdf": extension == ".pdf",
            "es_office": extension in EXTENSIONES_OFFICE, "url_visor_publico": url_visor_publico,
        },
    )


@router.get("/visor-publico/{token}")
async def visor_publico(token: str):
    """
    Sirve el archivo sin pedir sesión -- SOLO accesible con un
    token largo e imposible de adivinar, que nunca se muestra en
    ningún listado. Existe porque el visor de Office en línea de
    Microsoft necesita poder buscar el archivo desde sus propios
    servidores para poder mostrarlo, y no tiene forma de mandar
    la sesión de quien lo está viendo.
    """
    item = capacitacion.obtener_por_token(token)
    if not item or not item.get("archivo_path"):
        raise HTTPException(status_code=404, detail="Este enlace ya no es válido.")

    from core.config import RECURSOS_DIR
    ruta = RECURSOS_DIR / item["archivo_path"]
    if not ruta.exists():
        raise HTTPException(status_code=404, detail="El archivo ya no se encuentra en el servidor.")
    return FileResponse(ruta)


# ==========================================================
# ADMINISTRACIÓN DEL MÓDULO (solo Gerencia / Administración)
# ==========================================================

@router.get("/administrar/todo", response_class=HTMLResponse)
async def administrar(request: Request, usuario=Depends(requiere_gerencia_o_admin())):
    from services.roles_service import listar_roles as listar_roles
    return templates.TemplateResponse(
        request=request, name="capacitacion/administrar.html",
        context={
            "usuario": usuario, "items": capacitacion.listar_todo(),
            "tipos": capacitacion.TIPOS_CONTENIDO, "categorias_disponibles": capacitacion.CATEGORIAS,
            "plataformas": capacitacion.PLATAFORMAS, "roles": [dict(r) for r in listar_roles()],
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/administrar/crear")
async def crear(
    request: Request,
    titulo: str = Form(...), descripcion: str = Form(""), tipo: str = Form(...), categoria: str = Form(...),
    plataforma: str = Form("Web"), roles_permitidos: str = Form("Todos"), url_externa: str = Form(""),
    archivo: UploadFile = File(None), orden: int = Form(0),
    usuario=Depends(requiere_gerencia_o_admin()),
):
    archivo_path = None
    try:
        if archivo and archivo.filename:
            from core.config import RECURSOS_DIR
            import re, time
            carpeta = RECURSOS_DIR / "uploads" / "capacitacion"
            carpeta.mkdir(parents=True, exist_ok=True)
            nombre_limpio = re.sub(r"[^A-Za-z0-9_.-]", "_", archivo.filename)
            nombre_final = f"{int(time.time())}_{nombre_limpio}"
            ruta_destino = carpeta / nombre_final
            with open(ruta_destino, "wb") as f:
                f.write(await archivo.read())
            archivo_path = f"uploads/capacitacion/{nombre_final}"

        capacitacion.crear(
            titulo=titulo, descripcion=descripcion, tipo=tipo, categoria=categoria, plataforma=plataforma,
            roles_permitidos=roles_permitidos, archivo_path=archivo_path, url_externa=url_externa or None,
            usuario_id=_id_usuario(usuario), usuario_nombre=usuario.get("nombre"), orden=orden,
        )
    except ValueError as error:
        return RedirectResponse(url=f"/capacitacion/administrar/todo?error={error}", status_code=303)
    return RedirectResponse(url="/capacitacion/administrar/todo?guardado=1", status_code=303)


@router.post("/administrar/{capacitacion_id}/actualizar")
async def actualizar(
    capacitacion_id: int,
    titulo: str = Form(...), descripcion: str = Form(""), tipo: str = Form(...), categoria: str = Form(...),
    plataforma: str = Form("Web"), roles_permitidos: str = Form("Todos"), url_externa: str = Form(""),
    archivo: UploadFile = File(None), orden: int = Form(0),
    usuario=Depends(requiere_gerencia_o_admin()),
):
    archivo_path = None
    try:
        if archivo and archivo.filename:
            from core.config import RECURSOS_DIR
            import re, time
            carpeta = RECURSOS_DIR / "uploads" / "capacitacion"
            carpeta.mkdir(parents=True, exist_ok=True)
            nombre_limpio = re.sub(r"[^A-Za-z0-9_.-]", "_", archivo.filename)
            nombre_final = f"{int(time.time())}_{nombre_limpio}"
            ruta_destino = carpeta / nombre_final
            with open(ruta_destino, "wb") as f:
                f.write(await archivo.read())
            archivo_path = f"uploads/capacitacion/{nombre_final}"

        capacitacion.actualizar(
            capacitacion_id, titulo=titulo, descripcion=descripcion, tipo=tipo, categoria=categoria,
            plataforma=plataforma, roles_permitidos=roles_permitidos,
            archivo_path=archivo_path, url_externa=url_externa or None, orden=orden,
        )
    except ValueError as error:
        return RedirectResponse(url=f"/capacitacion/administrar/todo?error={error}", status_code=303)
    return RedirectResponse(url="/capacitacion/administrar/todo?guardado=1", status_code=303)


@router.post("/administrar/{capacitacion_id}/desactivar")
async def desactivar(capacitacion_id: int, usuario=Depends(requiere_gerencia_o_admin())):
    capacitacion.desactivar(capacitacion_id)
    return RedirectResponse(url="/capacitacion/administrar/todo?guardado=1", status_code=303)


@router.post("/administrar/{capacitacion_id}/reactivar")
async def reactivar(capacitacion_id: int, usuario=Depends(requiere_gerencia_o_admin())):
    capacitacion.reactivar(capacitacion_id)
    return RedirectResponse(url="/capacitacion/administrar/todo?guardado=1", status_code=303)


@router.post("/administrar/{capacitacion_id}/eliminar")
async def eliminar(capacitacion_id: int, usuario=Depends(requiere_gerencia_o_admin())):
    capacitacion.eliminar(capacitacion_id)
    return RedirectResponse(url="/capacitacion/administrar/todo?guardado=1", status_code=303)
