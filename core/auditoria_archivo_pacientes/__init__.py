"""
HomeCare Enterprise
Audit Package
"""

from .audit import (
    crear_evento,
    registrar_auditoria,
)

__all__ = [
    "crear_evento",
    "registrar_auditoria",
]