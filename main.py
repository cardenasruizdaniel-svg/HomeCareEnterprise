from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from core.config import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    SECRET_KEY,
    STATIC_DIR,
    SESSION_TIMEOUT,
    COOKIE_NAME,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
)

from core.bootstrap import iniciar_sistema

from middleware.session import SessionTimeoutMiddleware

from routers.auth import router as auth_router
from routers.dashboard import router as dashboard_router
from routers.pacientes import router as pacientes_router
from routers.acudientes import router as acudientes_router
from routers.historia_clinica_consolidada import router as historia_clinica_consolidada_router
from routers.fotos_procedimientos import router as fotos_procedimientos_router
from routers.consentimientos import router as consentimientos_router
from routers.firma_remota import router as firma_remota_router
from routers.inventario import router as inventario_router
from routers.configuracion_empresa import router as configuracion_empresa_router
from routers.laboratorios import router as laboratorios_router
from routers.pendientes_agendar import router as pendientes_agendar_router
from routers.calidad import router as calidad_router
from routers.informes import router as informes_router
from routers.examen_fisico import router as examen_fisico_router
from routers.recomendaciones import router as recomendaciones_router
from routers import despacho
from routers.plantillas import router as plantillas_router

from routers.usuarios import router as usuarios_router
from routers.profesionales import router as profesionales_router
from routers.programacion import router as programacion_ui_router
from routers.historia_clinica import router as historia_clinica_router
from routers.medicamentos import router as medicamentos_router
from routers.ordenes_medicas import router as ordenes_medicas_router
from routers.diagnosticos import router as diagnosticos_router
from routers.evoluciones import router as evoluciones_router
from routers.signos_vitales import router as signos_vitales_router
from routers.mapa import router as mapa_router
from routers.rutas import router as rutas_router
from routers.interoperabilidad import router as interoperabilidad_router
from routers.agenda import router as agenda_router
from routers.api import router as api_router
from routers.api_cie10 import router as api_cie10_router
from routers.api_pacientes import router as api_pacientes_router
from routers.modulos_clinicos import router as modulos_clinicos_router
from routers.alergias import router as alergias_router
from routers.antecedentes import router as antecedentes_router
from routers.rips import router as rips_router
from routers.catalogos import router as catalogos_router
from routers.nomina import router as nomina_router
from routers.cargos import router as cargos_router
from routers.contratos import router as contratos_router
from routers.documentos_profesional import router as documentos_profesional_router
from routers.turnos import router as turnos_router
from routers.api_movil import router as api_movil_router
from routers.copagos import router as copagos_router
from routers.facturacion import router as facturacion_router
from routers.historial_documentos import router as historial_documentos_router
from routers.servicios_paciente import router as servicios_paciente_router
from routers.planilla_visitas import router as planilla_visitas_router
from routers.plantillas_visita import router as plantillas_visita_router
from routers.mi_agenda import router as mi_agenda_router
from routers.programas_atencion import router as programas_atencion_router
from routers.gestion_visitas import router as gestion_visitas_router


# ==========================================================
# LIFESPAN
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    iniciar_sistema()

    yield


# ==========================================================
# CREAR APP
# ==========================================================

def create_app() -> FastAPI:

    app = FastAPI(

        title=APP_NAME,

        version=APP_VERSION,

        description=APP_DESCRIPTION,

        lifespan=lifespan,

    )

    # ==========================================
    # MIDDLEWARE
    # ==========================================

    app.add_middleware(
        SessionTimeoutMiddleware
    )

    app.add_middleware(

        SessionMiddleware,

        secret_key=SECRET_KEY,

        session_cookie=COOKIE_NAME,

        max_age=SESSION_TIMEOUT,

        same_site=COOKIE_SAMESITE,

        https_only=COOKIE_SECURE,

    )

    from middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)

    # Comprime las respuestas (HTML, CSS, JS, JSON) antes de
    # enviarlas -- reduce bastante el tamaño de la descarga sin
    # tocar ni un solo caracter del código (a diferencia de
    # minificar, que reescribe el archivo).
    from fastapi.middleware.gzip import GZipMiddleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ==========================================
    # STATIC
    # ==========================================

    app.mount(

        "/static",

        StaticFiles(directory=str(STATIC_DIR)),

        name="static",

    )

    app.mount(

        "/app",

        StaticFiles(directory=str(STATIC_DIR) + "/pwa", html=True),

        name="pwa",

    )

    # ==========================================
    # ROUTERS
    # ==========================================

    app.include_router(auth_router)

    app.include_router(dashboard_router)

    app.include_router(pacientes_router)

    app.include_router(acudientes_router)

    app.include_router(historia_clinica_consolidada_router)

    app.include_router(fotos_procedimientos_router)

    app.include_router(consentimientos_router)

    app.include_router(firma_remota_router)

    app.include_router(inventario_router)

    app.include_router(configuracion_empresa_router)

    app.include_router(laboratorios_router)

    app.include_router(pendientes_agendar_router)

    app.include_router(calidad_router)

    app.include_router(informes_router)

    app.include_router(examen_fisico_router)
    app.include_router(recomendaciones_router)

    app.include_router(despacho.router)

    app.include_router(plantillas_router)

    app.include_router(usuarios_router)

    app.include_router(profesionales_router)

    app.include_router(programacion_ui_router)

    app.include_router(historia_clinica_router)

    app.include_router(medicamentos_router)

    app.include_router(ordenes_medicas_router)

    app.include_router(diagnosticos_router)

    app.include_router(evoluciones_router)

    app.include_router(signos_vitales_router)

    app.include_router(mapa_router)

    app.include_router(rutas_router)

    app.include_router(interoperabilidad_router)

    app.include_router(agenda_router)

    app.include_router(api_router)

    app.include_router(api_cie10_router)

    app.include_router(api_pacientes_router)

    app.include_router(modulos_clinicos_router)

    app.include_router(alergias_router)

    app.include_router(antecedentes_router)

    app.include_router(rips_router)

    app.include_router(catalogos_router)

    app.include_router(nomina_router)

    app.include_router(cargos_router)

    app.include_router(contratos_router)

    app.include_router(documentos_profesional_router)

    app.include_router(turnos_router)

    app.include_router(api_movil_router)

    app.include_router(copagos_router)

    app.include_router(facturacion_router)

    app.include_router(historial_documentos_router)

    app.include_router(servicios_paciente_router)

    app.include_router(planilla_visitas_router)

    app.include_router(plantillas_visita_router)

    app.include_router(mi_agenda_router)

    app.include_router(programas_atencion_router)

    app.include_router(gestion_visitas_router)

    # ==========================================
    # HEALTH
    # ==========================================

    @app.get("/health", tags=["Sistema"])
    async def health():

        return {

            "status": "ok",

            "application": APP_NAME,

            "version": APP_VERSION,

        }

    return app


# ==========================================================
# APP
# ==========================================================

app = create_app()