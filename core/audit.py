"""
=========================================================
HomeCare IPS Enterprise
Archivo: core/audit.py
Versión: 7.0.0
=========================================================
"""

from datetime import datetime

from database.database import ejecutar


def registrar_auditoria(
    usuario_id=None,
    usuario="",
    rol="",
    modulo="",
    accion="",
    descripcion="",
    ip="",
    navegador=""
):
    """
    Registra un evento de auditoría.
    """

    ejecutar(
        """
        INSERT INTO auditoria(

            fecha,

            usuario_id,

            usuario,

            rol,

            modulo,

            accion,

            descripcion,

            ip,

            navegador

        )

        VALUES(?,?,?,?,?,?,?,?,?)

        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            usuario_id,
            usuario,
            rol,
            modulo,
            accion,
            descripcion,
            ip,
            navegador,
        )
    )