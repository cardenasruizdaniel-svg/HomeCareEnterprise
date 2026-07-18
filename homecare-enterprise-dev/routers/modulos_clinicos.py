"""
=========================================================
HomeCare Enterprise
Router: Modulos Clinicos (pestañas dinámicas de la ficha
del paciente: diagnósticos, alergias, medicamentos, etc.)
Reconstruido: el archivo original estaba corrupto
(sin router, sin imports, llamaba funciones inexistentes).
=========================================================
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services.pacientes_service import PacientesService
from services.alertas_service import obtener_alertas

router = APIRouter(prefix="/modulos-clinicos", tags=["Módulos Clínicos"])


# ===============================================
# MÓDULOS DISPONIBLES
# ===============================================

MODULOS = {
    "resumen",
    "diagnosticos",
    "antecedentes",
    "alergias",
    "medicamentos",
    "signos",
    "evoluciones",
    "procedimientos",
    "examenes",
    "imagenes",
    "documentos",
    "visitas",
    "programacion",
    "facturacion",
    "auditoria",
}


# ===============================================
# CARGAR MÓDULO (fragmento HTML para la ficha del paciente)
# ===============================================

@router.get(
    "/{paciente_id}/modulo/{modulo}",
    response_class=HTMLResponse,
)
async def cargar_modulo(
    request: Request,
    paciente_id: int,
    modulo: str,
    usuario=Depends(requiere_permiso("pacientes")),
):
    # -------------------------------
    # Validar módulo
    # -------------------------------

    if modulo not in MODULOS:
        return HTMLResponse(
            "<div class='alert alert-warning'>Módulo no disponible.</div>",
            status_code=404,
        )

    # -------------------------------
    # Buscar paciente
    # -------------------------------

    paciente = PacientesService.obtener(paciente_id)

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente no encontrado.",
        )

    # -------------------------------
    # Buscar template
    # -------------------------------

    template = f"pacientes/componentes/contenido/{modulo}.html"

    ruta = Path("templates") / template

    if not ruta.exists():
        return HTMLResponse(f"""
            <div class='alert alert-info'>
                <h4>{modulo.title()}</h4>
                Este módulo aún está en desarrollo.
            </div>
        """)

    # -------------------------------
    # Alertas clínicas
    # -------------------------------

    alertas = obtener_alertas(paciente_id)

    # -------------------------------
    # Contexto
    # -------------------------------

    contexto = {
        "request": request,
        "usuario": usuario,
        "paciente": paciente,
        "alertas": alertas,
        "modulo": modulo,
        # Estos valores se completan a medida que cada
        # módulo se conecta a su service correspondiente.
        "total_diagnosticos": 0,
        "total_alergias": 0,
        "total_medicamentos": 0,
        "total_visitas": 0,
        "diagnostico_principal": "",
        "profesional": "",
        "proxima_visita": "",
    }

    return templates.TemplateResponse(template, contexto)
