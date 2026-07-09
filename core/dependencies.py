"""
=========================================================
HomeCare IPS Enterprise
Archivo: core/dependencies.py
Versión: 7.0.0
=========================================================
"""

from fastapi import HTTPException, Request, status

from core.permissions import tiene_permiso


# ==========================================================
# USUARIO AUTENTICADO
# ==========================================================

def usuario_actual(request: Request):
    """
    Obtiene la información del usuario almacenada en sesión.
    """

    usuario_id = request.session.get("usuario_id")

    if usuario_id is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debe iniciar sesión."
        )

    return {

        "id": usuario_id,

        "usuario": request.session.get("usuario"),

        "nombre": request.session.get("nombre"),

        "rol": request.session.get("rol"),

    }


# ==========================================================
# REQUIERE PERMISO
# ==========================================================

def requiere_permiso(modulo: str):

    async def dependency(request: Request):

        usuario = usuario_actual(request)

        if not tiene_permiso(usuario["rol"], modulo):

            raise HTTPException(

                status_code=status.HTTP_403_FORBIDDEN,

                detail=f"No tiene permiso para acceder al módulo '{modulo}'."

            )

        return usuario

    return dependency


# ==========================================================
# REQUIERE ROL
# ==========================================================

def requiere_rol(*roles):

    async def dependency(request: Request):

        usuario = usuario_actual(request)

        if usuario["rol"] not in roles:

            raise HTTPException(

                status_code=status.HTTP_403_FORBIDDEN,

                detail="No posee el rol requerido."

            )

        return usuario

    return dependency