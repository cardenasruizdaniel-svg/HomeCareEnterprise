"""
=========================================================
HomeCare IPS Enterprise
Sistema Centralizado de Logs
=========================================================
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from core.config import LOGS_DIR

# ==========================================================
# CREAR CARPETA DE LOGS
# ==========================================================

LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================================
# ARCHIVO LOG
# ==========================================================

LOG_FILE = LOGS_DIR / "homecare.log"

# ==========================================================
# LOGGER PRINCIPAL
# ==========================================================

logger = logging.getLogger("homecare")

logger.setLevel(logging.INFO)

# Evita duplicar handlers si el módulo se importa varias veces
if not logger.handlers:

    formatter = logging.Formatter(

        "%(asctime)s | %(levelname)s | %(module)s | %(message)s",

        "%Y-%m-%d %H:%M:%S"

    )

    handler = RotatingFileHandler(

        LOG_FILE,

        maxBytes=5 * 1024 * 1024,

        backupCount=10,

        encoding="utf-8"

    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def info(mensaje):

    logger.info(mensaje)


def warning(mensaje):

    logger.warning(mensaje)


def error(mensaje):

    logger.error(mensaje)


def critical(mensaje):

    logger.critical(mensaje)


def exception(ex):

    logger.exception(ex)