"""
=========================================================
HomeCare IPS Enterprise

Archivo:
main.py

Versión:
6.0.1

Módulo:
Core

Autor:
Proyecto HomeCare IPS Enterprise

Descripción:
Punto de entrada principal de toda la aplicación.
Desde aquí se inicializan:

- FastAPI
- Middleware
- Base de datos
- Routers
- Eventos
- Archivos estáticos

=========================================================
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from core.config import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    SECRET_KEY,
    STATIC_DIR
)

# ==========================================================
# CONFIGURACIÓN INICIAL
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Eventos de inicio y cierre de la aplicación.
    """

    print("===========================================")
    print(f"Iniciando {APP_NAME}")
    print(f"Versión {APP_VERSION}")
    print("===========================================")

    yield

    print("===========================================")
    print("Aplicación finalizada correctamente")
    print("===========================================")

# ==========================================================
# CREACIÓN DE LA APLICACIÓN
# ==========================================================

def create_app() -> FastAPI:
    """
    Crea y configura la aplicación principal.
    """

    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        lifespan=lifespan
    )

    return app

# ==========================================================
# INSTANCIA PRINCIPAL
# ==========================================================

app = create_app()

