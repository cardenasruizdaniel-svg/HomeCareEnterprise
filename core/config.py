"""
=========================================================
HomeCare IPS Enterprise
Archivo: main.py
Versión: 6.0.1
Módulo: Core
Autor: Proyecto HomeCare IPS Enterprise

Descripción:
Punto de entrada principal de la aplicación.
=========================================================
"""

from pathlib import Path
import secrets

# =========================================================
# INFORMACIÓN GENERAL
# =========================================================

APP_NAME = "HomeCare IPS"

APP_VERSION = "5.0.0"

APP_DESCRIPTION = (
    "Sistema Integral de Gestión para Atención Domiciliaria"
)

EMPRESA = "IPS HomeCare del Quindío"

# =========================================================
# RUTAS DEL PROYECTO
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"

DATABASE_FILE = BASE_DIR / "database.db"

STATIC_DIR = BASE_DIR / "static"

TEMPLATES_DIR = BASE_DIR / "templates"

UPLOADS_DIR = BASE_DIR / "uploads"

DOCUMENTOS_DIR = STATIC_DIR / "documentos"

FIRMAS_DIR = STATIC_DIR / "firmas"

IMG_DIR = STATIC_DIR / "img"

LOGS_DIR = BASE_DIR / "logs"

BACKUPS_DIR = BASE_DIR / "backups"

EXPORTS_DIR = BASE_DIR / "exports"

TEMP_DIR = BASE_DIR / "temp"

# =========================================================
# SESIONES
# =========================================================

SECRET_KEY = "homecare-ips-2026"

SESSION_NAME = "HOMECARE_SESSION"

SESSION_MAX_AGE = 60 * 60 * 8

# =========================================================
# BASE DE DATOS
# =========================================================

DATABASE_TIMEOUT = 30

DATABASE_CACHE = 20000

DATABASE_FOREIGN_KEYS = True

DATABASE_WAL = True

# =========================================================
# PAGINACIÓN
# =========================================================

DEFAULT_PAGE_SIZE = 20

MAX_PAGE_SIZE = 100

# =========================================================
# HISTORIA CLÍNICA
# =========================================================

LONGITUD_HISTORIA = 10

# =========================================================
# FORMATOS
# =========================================================

DATE_FORMAT = "%Y-%m-%d"

TIME_FORMAT = "%H:%M"

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# =========================================================
# SUBIDA DE ARCHIVOS
# =========================================================

MAX_UPLOAD_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {

    ".pdf",

    ".jpg",

    ".jpeg",

    ".png",

    ".doc",

    ".docx",

    ".xls",

    ".xlsx"

}

# =========================================================
# SEGURIDAD
# =========================================================

PASSWORD_MIN_LENGTH = 8

TOKEN_BYTES = 32

# =========================================================
# DEBUG
# =========================================================

DEBUG = True

# =========================================================
# CREAR DIRECTORIOS
# =========================================================

DIRECTORIOS = [

    LOGS_DIR,

    UPLOADS_DIR,

    BACKUPS_DIR,

    EXPORTS_DIR,

    TEMP_DIR,

    DOCUMENTOS_DIR,

    FIRMAS_DIR

]

for directorio in DIRECTORIOS:

    directorio.mkdir(parents=True, exist_ok=True)

# ==========================================================
# SESIONES
# ==========================================================

SESSION_TIMEOUT = 30 * 60          # 30 minutos

SESSION_REFRESH = True

COOKIE_NAME = "homecare_session"

COOKIE_SECURE = False              # True cuando exista HTTPS

COOKIE_HTTPONLY = True

COOKIE_SAMESITE = "lax"