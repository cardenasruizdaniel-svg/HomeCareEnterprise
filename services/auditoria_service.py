"""
HomeCare Enterprise - Auditoría del sistema

Registra automáticamente qué hace cada usuario dentro del
sistema: qué pantalla o acción usó, si le salió bien, si hubo
una advertencia (algo que el sistema no le permitió hacer, o un
dato que le faltó), o si hubo un error real -- con el detalle
exacto, para poder ver de un vistazo cómo está operando cada
usuario y ayudarle a corregir lo que esté haciendo mal.

La mayoría de los registros los genera solo el middleware
(automático, para toda acción que cambie algo o que falle) --
pero los módulos también pueden llamar a `registrar()`
directamente para dejar una nota más clara y de negocio sobre
una acción puntual (por ejemplo, "intentó programar más
terapias de las autorizadas").
"""

from database.database import consultar_todos, consultar_uno, ejecutar

RESULTADOS = ("Éxito", "Advertencia", "Error")

# Módulos que generan mucho ruido de auditoría sin aportar nada útil
# (archivos estáticos, comprobaciones de sesión, etc.) -- no se
# registran, para que el módulo sea legible y no se llene de
# entradas irrelevantes.
RUTAS_IGNORADAS_PREFIJOS = ("/static/", "/favicon", "/docs", "/openapi.json", "/redoc")


def registrar(usuario_id=None, usuario=None, rol=None, modulo="", accion="", descripcion="",
               resultado="Éxito", detalle_error=None, ip=None, navegador=None,
               metodo_http=None, ruta=None, codigo_estado=None, duracion_ms=None):
    if resultado not in RESULTADOS:
        resultado = "Éxito"
    ejecutar(
        """
        INSERT INTO auditoria(
            fecha, usuario_id, usuario, rol, modulo, accion, descripcion, ip, navegador,
            resultado, detalle_error, metodo_http, ruta, codigo_estado, duracion_ms
        ) VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (usuario_id, usuario, rol, modulo, accion, descripcion, ip, navegador,
         resultado, detalle_error, metodo_http, ruta, codigo_estado, duracion_ms),
    )


def modulo_desde_ruta(ruta: str) -> str:
    """Deriva un nombre de módulo legible a partir de la ruta -- ej. '/pacientes/5' -> 'pacientes'."""
    if not ruta:
        return "General"
    partes = [p for p in ruta.strip("/").split("/") if p]
    return partes[0] if partes else "General"


def listar(fecha_desde=None, fecha_hasta=None, usuario_id=None, modulo=None, resultado=None, limite=300):
    sql = "SELECT * FROM auditoria WHERE 1=1"
    parametros = []
    if fecha_desde:
        sql += " AND date(fecha) >= date(?)"
        parametros.append(fecha_desde)
    if fecha_hasta:
        sql += " AND date(fecha) <= date(?)"
        parametros.append(fecha_hasta)
    if usuario_id:
        sql += " AND usuario_id = ?"
        parametros.append(usuario_id)
    if modulo:
        sql += " AND modulo = ?"
        parametros.append(modulo)
    if resultado:
        sql += " AND resultado = ?"
        parametros.append(resultado)
    sql += " ORDER BY fecha DESC LIMIT ?"
    parametros.append(limite)

    filas = consultar_todos(sql, tuple(parametros))
    return [dict(f) for f in filas]


def resumen_dashboard(horas=24):
    """Para el Dashboard: cuántos errores y advertencias ha habido en las últimas N horas."""
    fila = consultar_uno(
        """
        SELECT
            SUM(CASE WHEN resultado='Error' THEN 1 ELSE 0 END) AS errores,
            SUM(CASE WHEN resultado='Advertencia' THEN 1 ELSE 0 END) AS advertencias,
            COUNT(*) AS total
        FROM auditoria
        WHERE datetime(fecha) >= datetime('now', ?)
        """,
        (f"-{horas} hours",),
    )
    f = dict(fila) if fila else {}
    return {"errores": f.get("errores") or 0, "advertencias": f.get("advertencias") or 0, "total": f.get("total") or 0}


def resumen_por_usuario(fecha_desde=None, fecha_hasta=None):
    """Cuántas acciones, advertencias y errores ha tenido cada usuario -- para ver quién necesita apoyo o capacitación."""
    sql = """
        SELECT usuario, rol, usuario_id,
            COUNT(*) AS total_acciones,
            SUM(CASE WHEN resultado='Error' THEN 1 ELSE 0 END) AS errores,
            SUM(CASE WHEN resultado='Advertencia' THEN 1 ELSE 0 END) AS advertencias,
            MAX(fecha) AS ultima_actividad
        FROM auditoria
        WHERE usuario IS NOT NULL
    """
    parametros = []
    if fecha_desde:
        sql += " AND date(fecha) >= date(?)"
        parametros.append(fecha_desde)
    if fecha_hasta:
        sql += " AND date(fecha) <= date(?)"
        parametros.append(fecha_hasta)
    sql += " GROUP BY usuario, rol, usuario_id ORDER BY (errores + advertencias) DESC, total_acciones DESC"

    filas = consultar_todos(sql, tuple(parametros))
    return [dict(f) for f in filas]


def listar_modulos_con_actividad():
    filas = consultar_todos("SELECT DISTINCT modulo FROM auditoria WHERE modulo IS NOT NULL AND modulo != '' ORDER BY modulo")
    return [dict(f)["modulo"] for f in filas]


def historial_usuario(usuario_id: int, limite=100):
    """Todo lo que ha hecho un usuario específico -- para revisar su actividad en detalle."""
    filas = consultar_todos(
        "SELECT * FROM auditoria WHERE usuario_id=? ORDER BY fecha DESC LIMIT ?",
        (usuario_id, limite),
    )
    return [dict(f) for f in filas]
