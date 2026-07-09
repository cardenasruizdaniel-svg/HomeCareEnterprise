"""
=========================================================
HomeCare IPS Enterprise
Respuestas estandarizadas del sistema
=========================================================
"""

from typing import Any, Dict, List, Optional


class ResponseBuilder:

    @staticmethod
    def success(
        mensaje: str = "Operación realizada correctamente.",
        datos: Optional[Any] = None,
        alertas: Optional[List] = None
    ) -> Dict:

        return {
            "ok": True,
            "mensaje": mensaje,
            "datos": datos,
            "errores": [],
            "alertas": alertas or []
        }

    @staticmethod
    def error(
        mensaje: str = "Ha ocurrido un error.",
        errores: Optional[List] = None
    ) -> Dict:

        return {
            "ok": False,
            "mensaje": mensaje,
            "datos": None,
            "errores": errores or [],
            "alertas": []
        }

    @staticmethod
    def warning(
        mensaje: str,
        datos: Optional[Any] = None,
        alertas: Optional[List] = None
    ) -> Dict:

        return {
            "ok": True,
            "mensaje": mensaje,
            "datos": datos,
            "errores": [],
            "alertas": alertas or []
        }

    @staticmethod
    def validation_error(errores: List) -> Dict:

        return {
            "ok": False,
            "mensaje": "Existen errores de validación.",
            "datos": None,
            "errores": errores,
            "alertas": []
        }