"""
HomeCare Enterprise - Configuración compartida de pruebas (pytest)

Cada corrida de pruebas usa una base de datos limpia (se borra
database.db antes de empezar, para no mezclar datos de
desarrollo con los de las pruebas, y se vuelve a borrar al
terminar).

Para correr las pruebas:
    pytest -v
    pytest tests/test_services.py -v      (solo un archivo)
    pytest -k "pqr" -v                    (solo las que tengan "pqr" en el nombre)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


def _borrar_base_de_datos():
    from database.database import DB_PATH
    for sufijo in ("", "-wal", "-shm", "-journal"):
        ruta = Path(str(DB_PATH) + sufijo)
        if ruta.exists():
            ruta.unlink()


@pytest.fixture(scope="session", autouse=True)
def base_de_datos_limpia():
    """Se ejecuta una sola vez, antes y después de TODA la sesión de pruebas."""
    _borrar_base_de_datos()
    yield
    _borrar_base_de_datos()


@pytest.fixture
def app():
    """La aplicación FastAPI completa, ya inicializada."""
    import main
    return main.create_app()


@pytest.fixture
def client(app):
    """Cliente HTTP anónimo (sin iniciar sesión) -- para probar rutas públicas y seguridad."""
    from fastapi.testclient import TestClient
    with TestClient(app, follow_redirects=True) as cliente:
        yield cliente


@pytest.fixture
def admin_client(client):
    """Cliente HTTP ya autenticado como el administrador -- para probar el sistema interno."""
    client.post("/login", data={"usuario": "admin", "password": "admin123"})
    return client
