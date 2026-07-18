from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from routers.pacientes import router as pacientes_router
from routers import despacho
from routers.plantillas import router as plantillas_router

from core.config import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    SECRET_KEY,
    STATIC_DIR,
    SESSION_TIMEOUT,
    COOKIE_NAME,
    COOKIE_SECURE,
    COOKIE_SAMESITE
)

from core.bootstrap import iniciar_sistema

from routers.auth import router as auth_router
from routers.dashboard import router as dashboard_router
from middleware.session import SessionTimeoutMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Inicialización del sistema.
    Se ejecuta una sola vez al arrancar FastAPI.
    """
    iniciar_sistema()
    yield


def create_app() -> FastAPI:

    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        lifespan=lifespan,
    )

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

    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )

    app.include_router(auth_router)

    app.include_router(dashboard_router)

    app.include_router(pacientes_router)

    app.include_router(despacho.router)

    app.include_router(plantillas_router)


@app.get("/health", tags=["Sistema"])
async def health():

    return {
        "status": "ok",
        "application": APP_NAME,
        "version": APP_VERSION,
    }

    return app


app = create_app()