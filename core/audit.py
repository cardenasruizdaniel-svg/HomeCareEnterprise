"""
=========================================================
HomeCare IPS Enterprise
Archivo: core/audit.py
Versión: 7.0.0

Este archivo se conserva por compatibilidad -- todas las
llamadas existentes en el sistema a `registrar_auditoria()`
siguen funcionando igual que antes, pero ahora quedan
respaldadas por el servicio de auditoría completo (que agrega
resultado, detalle de errores, etc.), en vez de escribir a la
tabla por su cuenta y duplicar la lógica.
=========================================================
"""

from services.auditoria_service import registrar as _registrar_completo


def registrar_auditoria(
    usuario_id=None,
    usuario="",
    rol="",
    modulo="",
    accion="",
    descripcion="",
    ip="",
    navegador="",
    resultado="Éxito",
    detalle_error=None,
):
    """
    Registra un evento de auditoría.
    """

    _registrar_completo(
        usuario_id=usuario_id, usuario=usuario, rol=rol, modulo=modulo, accion=accion,
        descripcion=descripcion, ip=ip, navegador=navegador,
        resultado=resultado, detalle_error=detalle_error,
    )