"""
=========================================================
HomeCare Enterprise
Router: Catalogos (DIVIPOLA, CUPS, CUM)

Endpoints de busqueda para autocompletado en los
formularios, y de importacion masiva desde CSV oficial.
=========================================================
"""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from fastapi import Request

from repositories.catalogos_repository import (
    CUMRepository,
    CUPSRepository,
    DivipolaRepository,
)
from repositories import cie10_repository

router = APIRouter(prefix="/catalogos", tags=["Catálogos"])


# ==========================================
# PANEL DE ADMINISTRACIÓN DE CATÁLOGOS
# ==========================================

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel(
    request: Request,
    usuario=Depends(requiere_permiso("catalogos")),
):
    return templates.TemplateResponse(
        request=request,
        name="catalogos/index.html",
        context={
            "usuario": usuario,
            "total_divipola": DivipolaRepository.total(),
            "total_cups": CUPSRepository.total(),
            "total_cum": CUMRepository.total(),
            "total_cie10": cie10_repository.total_activos(),
        },
    )


# ==========================================
# BÚSQUEDA (autocompletado)
# ==========================================

@router.get("/divipola/buscar")
async def buscar_divipola(q: str = ""):
    filas = DivipolaRepository.buscar_municipios(q) if q.strip() else []
    return [
        {
            "codigo": f["codigo_municipio"],
            "texto": f"{f['nombre_municipio']} ({f['nombre_departamento']}) - {f['codigo_municipio']}",
            "municipio": f["nombre_municipio"],
            "departamento": f["nombre_departamento"],
            "codigo_postal": f["codigo_postal"],
        }
        for f in filas
    ]


# ==========================================
# CONFIGURACIÓN: CIUDADES Y DEPARTAMENTOS
# (para poder crear municipios nuevos y
# asignarles su código postal)
# ==========================================

@router.get("/ciudades", response_class=HTMLResponse)
async def ciudades_departamentos(request: Request, q: str = "", usuario=Depends(requiere_permiso("catalogos"))):
    return templates.TemplateResponse(
        request=request, name="catalogos/ciudades.html",
        context={
            "usuario": usuario, "texto_busqueda": q,
            "ciudades": [dict(c) for c in DivipolaRepository.listar_todos(q)],
        },
    )


@router.post("/ciudades/crear")
async def crear_ciudad(
    codigo_departamento: str = Form(...),
    nombre_departamento: str = Form(...),
    codigo_municipio: str = Form(...),
    nombre_municipio: str = Form(...),
    codigo_postal: str = Form(""),
    usuario=Depends(requiere_permiso("catalogos")),
):
    DivipolaRepository.crear(codigo_departamento, nombre_departamento, codigo_municipio, nombre_municipio, codigo_postal)
    return RedirectResponse(url="/catalogos/ciudades", status_code=303)


@router.post("/ciudades/actualizar-codigo-postal/{codigo_municipio}")
async def actualizar_codigo_postal(
    codigo_municipio: str,
    codigo_postal: str = Form(""),
    usuario=Depends(requiere_permiso("catalogos")),
):
    DivipolaRepository.actualizar_codigo_postal(codigo_municipio, codigo_postal)
    return RedirectResponse(url="/catalogos/ciudades", status_code=303)


@router.get("/ciudades/eliminar/{codigo_municipio}")
async def eliminar_ciudad(codigo_municipio: str, usuario=Depends(requiere_permiso("catalogos"))):
    DivipolaRepository.eliminar(codigo_municipio)
    return RedirectResponse(url="/catalogos/ciudades", status_code=303)


@router.get("/cups/buscar")
async def buscar_cups(q: str = ""):
    filas = CUPSRepository.buscar(q) if q.strip() else []
    return [
        {
            "codigo": f["codigo"],
            "texto": f"{f['codigo']} - {f['descripcion']}",
        }
        for f in filas
    ]


@router.get("/cum/buscar")
async def buscar_cum(q: str = ""):
    filas = CUMRepository.buscar(q) if q.strip() else []
    return [
        {
            "codigo": f["codigo"],
            "texto": f"{f['nombre']}" + (f" ({f['codigo']})" if f["codigo"] and not f["codigo"].startswith("PENDIENTE") else " (código CUM pendiente de verificar)"),
        }
        for f in filas
    ]


# ==========================================
# IMPORTACIÓN MASIVA DESDE CSV OFICIAL
# ==========================================

@router.post("/cups/importar")
async def importar_cups(
    archivo: UploadFile = File(...),
    _actor=Depends(requiere_permiso("catalogos")),
):
    contenido = (await archivo.read()).decode("utf-8-sig")
    total = CUPSRepository.importar_csv(contenido)
    return {"importados": total}


@router.post("/cum/importar")
async def importar_cum(
    archivo: UploadFile = File(...),
    _actor=Depends(requiere_permiso("catalogos")),
):
    contenido = (await archivo.read()).decode("utf-8-sig")
    total = CUMRepository.importar_csv(contenido)
    return {"importados": total}


@router.post("/cie10/importar")
async def importar_cie10(
    archivo: UploadFile = File(...),
    _actor=Depends(requiere_permiso("catalogos")),
):
    contenido = (await archivo.read()).decode("utf-8-sig")
    total = cie10_repository.importar_csv(contenido)
    return {"importados": total}
