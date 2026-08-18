"""
HomeCare Enterprise - Middleware de Auditoría

Registra automáticamente, para cada petición que cambie algo
(POST/PUT/DELETE/PATCH) o que termine en error, quién la hizo,
qué intentó hacer, y qué pasó -- sin que cada módulo tenga que
acordarse de llamarlo a mano. Los módulos de negocio pueden,
además, dejar una nota más clara y específica llamando a
`services.auditoria_service.registrar()` directamente cuando
haga falta más contexto (por ejemplo, el motivo exacto por el
que se bloqueó una acción).
"""

import time
import traceback

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from services.auditoria_service import registrar, modulo_desde_ruta, RUTAS_IGNORADAS_PREFIJOS


class AuditoriaMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        ruta = request.url.path

        if ruta.startswith(RUTAS_IGNORADAS_PREFIJOS):
            return await call_next(request)

        inicio = time.time()

        usuario_id = request.session.get("usuario_id") if hasattr(request, "session") else None
        usuario = request.session.get("usuario") if hasattr(request, "session") else None
        rol = request.session.get("rol") if hasattr(request, "session") else None

        ip_cliente = request.client.host if request.client else None
        navegador = request.headers.get("user-agent", "")[:250]

        try:
            respuesta = await call_next(request)
        except Exception as error:
            duracion_ms = int((time.time() - inicio) * 1000)
            registrar(
                usuario_id=usuario_id, usuario=usuario, rol=rol,
                modulo=modulo_desde_ruta(ruta), accion=f"{request.method} {ruta}",
                descripcion="El sistema tuvo un error inesperado procesando esta acción.",
                resultado="Error", detalle_error=f"{type(error).__name__}: {error}\n{traceback.format_exc()[-2000:]}",
                ip=ip_cliente, navegador=navegador, metodo_http=request.method, ruta=ruta,
                codigo_estado=500, duracion_ms=duracion_ms,
            )
            raise

        duracion_ms = int((time.time() - inicio) * 1000)

        # Solo se registran las acciones que cambian algo (no las
        # simples consultas/GET, que generarían demasiado ruido),
        # y CUALQUIER petición -- incluyendo GET -- que haya
        # terminado en un código de error, para no perder de
        # vista cuando algo no le funcionó a un usuario.
        es_cambio = request.method in ("POST", "PUT", "PATCH", "DELETE")
        es_error_o_advertencia = respuesta.status_code >= 400

        if es_cambio or es_error_o_advertencia:
            if respuesta.status_code >= 500:
                resultado = "Error"
                descripcion = "El sistema tuvo un error interno procesando esta acción."
            elif respuesta.status_code >= 400:
                resultado = "Advertencia"
                descripcion = _mensaje_para_codigo(respuesta.status_code)
            else:
                resultado = "Éxito"
                descripcion = f"Acción completada correctamente ({request.method} {ruta})."

            registrar(
                usuario_id=usuario_id, usuario=usuario, rol=rol,
                modulo=modulo_desde_ruta(ruta), accion=f"{request.method} {ruta}",
                descripcion=descripcion, resultado=resultado,
                ip=ip_cliente, navegador=navegador, metodo_http=request.method, ruta=ruta,
                codigo_estado=respuesta.status_code, duracion_ms=duracion_ms,
            )

        return respuesta


def _mensaje_para_codigo(codigo: int) -> str:
    mensajes = {
        400: "El usuario envió datos incompletos o inválidos para esta acción.",
        401: "Intentó entrar a una pantalla sin haber iniciado sesión.",
        403: "Intentó una acción para la que su rol no tiene permiso -- puede necesitar que se le habilite el acceso, o puede ser un intento indebido.",
        404: "Intentó acceder a algo que no existe (puede que ya se haya eliminado, o que el enlace esté mal).",
        422: "Los datos enviados no cumplían el formato esperado por el sistema.",
        429: "El usuario hizo demasiadas peticiones seguidas en poco tiempo.",
    }
    return mensajes.get(codigo, f"La acción no se pudo completar (código {codigo}).")
