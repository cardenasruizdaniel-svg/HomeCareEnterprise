"""
=========================================================
HomeCare Enterprise
Configuración General
=========================================================
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ==========================================================
# RUTAS DEL PROYECTO
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

STATIC_DIR = BASE_DIR / "static"

TEMPLATES_DIR = BASE_DIR / "templates"

LOG_DIR = BASE_DIR / "logs"

UPLOAD_DIR = BASE_DIR / "uploads"

DATABASE_DIR = BASE_DIR / "database"

EXPORTS_DIR = BASE_DIR / "exports"

# --------------------------------------------------------
# Aplicación
# --------------------------------------------------------

APP_NAME = "HomeCare Enterprise"

APP_VERSION = "10.0.0-dev"

APP_DESCRIPTION = (
    "Sistema Integral de Gestión para IPS de Atención "
    "Domiciliaria."
)

DEBUG = True

TIMEZONE = "America/Bogota"

# --------------------------------------------------------
# Seguridad
# --------------------------------------------------------

# --------------------------------------------------------

def _obtener_o_generar_secret_key() -> str:
    """
    Cada instalación necesita su PROPIA clave secreta (usada
    para firmar las cookies de sesión), no una clave fija
    igual en todas las copias del programa -- si fuera fija,
    cualquiera que tuviera el código fuente podría fabricar una
    cookie de sesión válida sin necesitar contraseña.

    La primera vez que arranca el programa en un computador,
    se genera una clave aleatoria y se guarda en un archivo
    local (fuera del código, para no quedar en ningún control
    de versiones). Las veces siguientes, se reutiliza esa
    misma clave para no invalidar las sesiones ya iniciadas.
    """
    import secrets

    archivo_clave = BASE_DIR / "instancia_secret_key.txt"

    if archivo_clave.exists():
        clave = archivo_clave.read_text(encoding="utf-8").strip()
        if clave:
            return clave

    clave_nueva = secrets.token_hex(32)
    try:
        archivo_clave.write_text(clave_nueva, encoding="utf-8")
    except OSError:
        pass  # si no se puede escribir a disco, igual sigue funcionando esta sesión (solo no persiste)

    return clave_nueva


SECRET_KEY = (
    os.environ.get("HOMECARE_SECRET_KEY")
    or _obtener_o_generar_secret_key()
)

SESSION_TIMEOUT = 60 * 60 * 8  # 8 horas

# --------------------------------------------------------
# Cookies
# --------------------------------------------------------

COOKIE_NAME = "homecare_session"

COOKIE_SECURE = False   # Cambiar a True en producción

COOKIE_SAMESITE = "lax"

# --------------------------------------------------------
# Directorios
# --------------------------------------------------------

STATIC_DIR = "static"

TEMPLATES_DIR = "templates"

# ==========================================================
# NOTIFICACIONES - CORREO (SMTP)
# ==========================================================
#
# Configurar mediante variables de entorno (archivo .env en
# la raíz del proyecto). Mientras SMTP_HOST no esté definido,
# el sistema opera en "modo simulado": registra en el log lo
# que habría enviado, sin intentar conectarse a ningún
# servidor, para que el resto de la aplicación nunca se
# bloquee por falta de credenciales.
# ==========================================================

SMTP_HOST = os.environ.get("SMTP_HOST", "")

SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

SMTP_USER = os.environ.get("SMTP_USER", "")

SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

SMTP_FROM = os.environ.get("SMTP_FROM", "notificaciones@homecare.local")

SMTP_FROM_NOMBRE = os.environ.get("SMTP_FROM_NOMBRE", "HomeCare IPS")

SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "1") == "1"

# ==========================================================
# NOTIFICACIONES - WHATSAPP (Meta WhatsApp Business Cloud API)
# ==========================================================
#
# Requiere una cuenta de WhatsApp Business API (Meta for
# Developers). Mientras WHATSAPP_TOKEN no esté definido, el
# sistema opera en modo simulado.
# ==========================================================

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")

WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")

WHATSAPP_API_VERSION = os.environ.get("WHATSAPP_API_VERSION", "v20.0")

WHATSAPP_API_URL = (
    f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"
)

# Indicativo de país por defecto, para completar números
# de celular colombianos que se guarden sin el +57.
PAIS_INDICATIVO_DEFECTO = os.environ.get("PAIS_INDICATIVO_DEFECTO", "57")

# URL pública base del servidor (necesaria para que la API de
# WhatsApp pueda descargar el PDF adjunto; ej:
# https://midominio.com). Si queda vacía, WhatsApp solo envía
# el mensaje de texto con el resumen de la orden, sin adjunto.
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "")

# ==========================================================
# RIPS (Resolución 948 de 2026, antes 2275 de 2023)
# ==========================================================
#
# Datos del prestador que identifican al "facturador
# electrónico del sector salud" en el RIPS.
# ==========================================================

RIPS_NIT_PRESTADOR = os.environ.get("RIPS_NIT_PRESTADOR", "")

RIPS_CODIGO_HABILITACION = os.environ.get("RIPS_CODIGO_HABILITACION", "")

RIPS_RAZON_SOCIAL = os.environ.get("RIPS_RAZON_SOCIAL", "IPS HomeCare del Quindío")