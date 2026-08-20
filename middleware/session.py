"""
=========================================================
HomeCare Enterprise
Middleware de Sesión
Versión 7.0

Cierra la sesión sola después de 20 minutos sin actividad --
para que, si alguien deja el sistema abierto sin usarlo, no
quede una sesión de un paciente o un profesional expuesta.

Única excepción: el Administrador (el "super admin", una
persona de confianza que suele dejar el sistema abierto para
tareas de configuración largas) no queda sujeto a este cierre
automático.
=========================================================
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import RedirectResponse

MINUTOS_INACTIVIDAD = 20


class SessionTimeoutMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        if request.url.path.startswith("/static"):

            return await call_next(request)

        if request.url.path.startswith("/login"):

            return await call_next(request)

        rol_sesion = (request.session.get("rol") or "").strip().lower()
        es_super_admin = rol_sesion == "administrador"

        ahora = int(time.time())

        ultimo = request.session.get("last_activity")

        if ultimo and not es_super_admin:

            if ahora - ultimo > MINUTOS_INACTIVIDAD * 60:

                request.session.clear()

                return RedirectResponse(
                    "/login?motivo=inactividad",
                    status_code=302
                )

        request.session["last_activity"] = ahora

        return await call_next(request)