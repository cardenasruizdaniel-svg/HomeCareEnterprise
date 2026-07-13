"""
HomeCare Enterprise - App Gerencial

Una aplicación web/PWA aparte de la app de campo (que usan los
profesionales para sus visitas) -- esta es para la gerencia y
administración de alto nivel: un Dashboard Ejecutivo completo,
optimizado para celular, para ver cómo va la operación desde
donde estén.

Es de SOLO LECTURA (no se puede registrar nada desde aquí) y
el acceso está restringido a los roles de dirección
(Administrador, Director Médico, Coordinador) -- un profesional
normal o un cuidador no pueden entrar aquí.
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from core.dependencies import usuario_actual
from core.permissions.permissions import tiene_permiso
from services.auth_service import AuthService

router = APIRouter(prefix="/api/gerencial", tags=["App Gerencial"])


# ==========================================================
# ARCHIVOS ESTÁTICOS DE LA APP (PWA)
# Se sirven con un montaje StaticFiles(html=True) en main.py,
# igual que la app de campo -- no hace falta ninguna ruta aquí
# para eso.
# ==========================================================


def _verificar_acceso_gerencial(usuario: dict):
    """
    Igual que cualquier otro módulo del sistema: el acceso lo
    define el permiso "app_gerencial" del rol (configurable
    desde Roles y Permisos) -- Administrador y Director Médico
    ya lo tienen por su acceso total, y cualquier rol nuevo que
    se cree (ej. un "Super Usuario") puede recibir este permiso
    ahí mismo, sin tocar código.
    """
    if not usuario or not tiene_permiso(usuario.get("rol"), "app_gerencial"):
        raise HTTPException(
            status_code=403,
            detail="Este usuario no tiene permiso para usar la App Gerencial "
                   "(se activa desde Roles y Permisos, módulo 'App Gerencial').",
        )


# ==========================================================
# LOGIN (mismo AuthService de siempre, pero restringido a roles de dirección)
# ==========================================================

@router.post("/login")
async def login_gerencial(datos: dict = Body(...), request: Request = None):
    usuario = datos.get("usuario")
    password = datos.get("password")

    resultado = AuthService.autenticar(usuario, password)
    if resultado is None:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")

    resultado = dict(resultado)

    if not tiene_permiso(resultado["rol"], "app_gerencial"):
        raise HTTPException(
            status_code=403,
            detail="Este usuario no tiene permiso para usar la App Gerencial "
                   "(se activa desde Roles y Permisos, módulo 'App Gerencial').",
        )

    resultado.pop("password", None)

    request.session["usuario_id"] = resultado["id"]
    request.session["usuario"] = resultado["usuario"]
    request.session["nombre"] = resultado["nombre"]
    request.session["rol"] = resultado["rol"]

    return {"ok": True, "usuario": resultado}


@router.get("/perfil")
async def perfil_gerencial(usuario=Depends(usuario_actual)):
    _verificar_acceso_gerencial(usuario)
    return {"usuario": usuario}


@router.post("/logout")
async def logout_gerencial(request: Request):
    request.session.clear()
    return {"ok": True}


# ==========================================================
# DASHBOARD EJECUTIVO
# ==========================================================

@router.get("/dashboard")
async def dashboard_gerencial(usuario=Depends(usuario_actual)):
    _verificar_acceso_gerencial(usuario)

    from services.dashboard_service import DashboardService
    from services.dashboard_operativo_service import panel_operativo_completo

    ds = DashboardService()

    gerencial = ds.resumen_gerencial()
    operativo = panel_operativo_completo()
    grafico = ds.grafico_produccion()

    return {
        "gerencial": gerencial,
        "operativo": {
            "visitas_hoy_total": len(operativo["visitas_hoy"]),
            "visitas_hoy": operativo["visitas_hoy"][:20],
            "en_visita_ahora": operativo["en_visita_ahora"],
            "finalizaron_hoy": operativo["finalizaron_hoy"],
            "servicios_sin_programar": operativo["servicios_sin_programar"][:10],
            "total_servicios_sin_programar": len(operativo["servicios_sin_programar"]),
        },
        "grafico_produccion": grafico,
    }


@router.get("/cartera")
async def cartera_gerencial(usuario=Depends(usuario_actual)):
    _verificar_acceso_gerencial(usuario)
    from services.facturacion_service import listar_cartera
    filas = listar_cartera()
    return [dict(f) for f in filas][:30]


@router.get("/inventario-resumen")
async def inventario_resumen_gerencial(usuario=Depends(usuario_actual)):
    _verificar_acceso_gerencial(usuario)
    from services import inventario_service
    informe = inventario_service.informe_existencias()
    return {
        "total_valorizado": informe["total_valorizado"],
        "total_insumos": informe["total_insumos"],
        "insumos_stock_bajo": informe["insumos_stock_bajo"][:10],
        "total_stock_bajo": len(informe["insumos_stock_bajo"]),
    }
