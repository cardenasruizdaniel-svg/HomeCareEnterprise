"""
=========================================================
HomeCare Enterprise
Middleware de Sesión
Versión 7.0
=========================================================
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import RedirectResponse


class SessionTimeoutMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        if request.url.path.startswith("/static"):

            return await call_next(request)

        if request.url.path.startswith("/login"):

            return await call_next(request)

        ahora = int(time.time())

        ultimo = request.session.get("last_activity")

        if ultimo:

            if ahora - ultimo > 1800:

                request.session.clear()

                return RedirectResponse(
                    "/login",
                    status_code=302
                )

        request.session["last_activity"] = ahora

        return await call_next(request)