"""
HomeCare Enterprise - Limitador de peticiones (Rate Limiting)

Protege contra abuso y ataques de fuerza bruta limitando
cuántas peticiones puede hacer una misma dirección IP en una
ventana de tiempo. Está pensado para una instalación de un
solo servidor (no necesita Redis ni nada externo) -- guarda
los contadores en memoria.

Dos niveles:
- Rutas de LOGIN (mucho mas estrictas): protegen contra
  adivinar contraseñas a la fuerza. Se suma a que
  AuthService ya bloquea la CUENTA tras varios intentos
  fallidos -- esto ademas limita la IP, asi alguien no pueda
  probar contra MUCHAS cuentas distintas rapidamente.
- El resto de la API (mas permisiva): protege contra un uso
  descontrolado o un error en un cliente que empiece a
  mandar peticiones en bucle.
"""

import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# (ruta, limite_peticiones, ventana_segundos)
REGLAS_ESTRICTAS = [
    ("/login", 10, 60),
    ("/api/movil/login", 10, 60),
]
LIMITE_GENERAL = 300
VENTANA_GENERAL_SEGUNDOS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)
        # clave -> deque de marcas de tiempo de las peticiones recientes
        self._peticiones = defaultdict(deque)
        self._contador_peticiones_totales = 0

    def _limite_para_ruta(self, ruta: str):
        for prefijo, limite, ventana in REGLAS_ESTRICTAS:
            if ruta.startswith(prefijo):
                return limite, ventana, True
        return LIMITE_GENERAL, VENTANA_GENERAL_SEGUNDOS, False

    async def dispatch(self, request: Request, call_next):
        # Los archivos estáticos no se limitan (css/js/imágenes propias del programa)
        if request.url.path.startswith("/static") or request.url.path.startswith("/app/"):
            return await call_next(request)

        ip_cliente = request.client.host if request.client else "desconocido"
        limite, ventana, es_ruta_sensible = self._limite_para_ruta(request.url.path)
        clave = f"{ip_cliente}:{request.url.path}" if es_ruta_sensible else ip_cliente

        ahora = time.time()
        marcas = self._peticiones[clave]

        # Se descartan las marcas fuera de la ventana de tiempo
        while marcas and marcas[0] < ahora - ventana:
            marcas.popleft()

        if len(marcas) >= limite:
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas solicitudes. Intente de nuevo en un momento."},
                headers={"Retry-After": str(ventana)},
            )

        marcas.append(ahora)

        # Cada tanto, se limpian las claves que ya quedaron sin
        # peticiones recientes, para no acumular memoria con
        # direcciones IP/rutas que ya no vuelven a aparecer.
        self._contador_peticiones_totales += 1
        if self._contador_peticiones_totales % 1000 == 0:
            claves_vacias = [k for k, v in self._peticiones.items() if not v]
            for k in claves_vacias:
                del self._peticiones[k]

        respuesta = await call_next(request)

        # Las paginas y respuestas de la API pueden traer datos
        # clinicos de pacientes -- se le dice al navegador (y a
        # cualquier proxy/cache intermedio) que NO las guarde,
        # para que no queden visibles despues en un computador
        # compartido (ej. con el boton "atras", o en la cache
        # de un proxy corporativo).
        respuesta.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        respuesta.headers["Pragma"] = "no-cache"

        return respuesta
