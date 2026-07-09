from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from core.config import SECRET_KEY

# ==========================================================
# BASE DE DATOS
# ==========================================================

from database.database import crear_tablas

# ==========================================================
# MIDDLEWARE
# ==========================================================

from middleware.auth import LoginMiddleware

# ==========================================================
# ROUTERS - SEGURIDAD
# ==========================================================

from routers.auth import router as auth_router
from routers.usuarios import router as usuarios_router

# ==========================================================
# ROUTERS - DASHBOARD
# ==========================================================

from routers.dashboard import router as dashboard_router

# ==========================================================
# ROUTERS - PACIENTES
# ==========================================================

from routers.pacientes import router as pacientes_router
from routers.acudientes import router as acudientes_router

# ==========================================================
# ROUTERS - CLÍNICOS
# ==========================================================

from routers.diagnosticos import router as diagnosticos_router
from routers.api_cie10 import router as api_cie10_router

from routers.antecedentes import router as antecedentes_router
from routers.alergias import router as alergias_router

from routers.medicamentos import router as medicamentos_router
from routers.signos_vitales import router as signos_vitales_router

# ==========================================================
# ROUTERS - OPERACIÓN
# ==========================================================

from routers.programacion import router as programacion_router
from routers.profesionales import router as profesionales_router

# ==========================================================
# ROUTERS - EXPEDIENTE
# ==========================================================

from routers.modulos_clinicos import router as modulos_clinicos_router


# ==========================================================
# CREAR APP
# ==========================================================

def create_app():

    app = FastAPI(

        title="HomeCare IPS",

        description="Sistema Integral para Atención Domiciliaria",

        version="1.0.0"

    )

# ======================================================
# MIDDLEWARE
# ======================================================

app.middleware("http")(LoginMiddleware())

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY
)

# ======================================================
# ARCHIVOS ESTÁTICOS
# ======================================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

    # ======================================================
    # BASE DE DATOS
    # ======================================================

    try:

        crear_tablas()

        print("✓ Base de datos inicializada correctamente.")

    except Exception as e:

        print(f"Error inicializando la base de datos: {e}")

        raise

    # ======================================================
    # ROUTERS
    # ======================================================

    # Seguridad
    app.include_router(auth_router)
    app.include_router(usuarios_router)

    # Dashboard
    app.include_router(dashboard_router)

    # Pacientes
    app.include_router(pacientes_router)
    app.include_router(acudientes_router)

    # Clínica
    app.include_router(diagnosticos_router)
    app.include_router(api_cie10_router)
    app.include_router(antecedentes_router)
    app.include_router(alergias_router)
    app.include_router(medicamentos_router)
    app.include_router(signos_vitales_router)

    # Expediente Clínico
    app.include_router(modulos_clinicos_router)

    # Operación
    app.include_router(programacion_router)
    app.include_router(profesionales_router)

    return app


# ==========================================================
# INSTANCIA PRINCIPAL
# ==========================================================

app = create_app()