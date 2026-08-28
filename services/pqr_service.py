"""
HomeCare Enterprise - Sistema PQR / SIAU (Fase 2)

Evoluciona el registro básico de PQR que ya existía en
calidad_service.py hacia un sistema completo: radicado único,
datos del solicitante (que puede ser el paciente, un familiar,
un acudiente, o cualquier otra persona), línea de tiempo
completa, clasificación de riesgo, escalamiento entre áreas, y
consulta pública de estado sin necesitar iniciar sesión.

No reemplaza 'calidad_service.py::listar_pqr/crear_pqr' (se
siguen usando para el registro interno rápido) -- este módulo
opera sobre la MISMA tabla 'calidad_pqr', ya extendida con las
columnas nuevas por la migración correspondiente.
"""

import random
import string
from datetime import date, datetime

from database.database import consultar_todos, consultar_uno, ejecutar

TIPOS_PQR = ("Petición", "Queja", "Reclamo", "Sugerencia", "Felicitación", "Solicitud", "Denuncia")
CANALES = ("Presencial/Interno", "Portal web", "Teléfono", "WhatsApp", "Correo", "Otro")
RIESGOS = ("Normal", "Prioritaria", "Alta", "Riesgo para la vida/integridad")
ESTADOS_PQR = ("Nueva", "En análisis", "Asignada", "En trámite", "Pendiente de respuesta", "Cerrada")
AREAS_RESPONSABLES = (
    "Calidad", "SIAU", "Dirección", "Coordinación", "Talento humano",
    "Enfermería", "Médico", "Facturación", "Cartera", "Administración", "Otra",
)
RELACIONES_SOLICITANTE = ("Paciente", "Familiar", "Acudiente", "Cuidador", "Representante", "Otro")

# Días hábiles de referencia por tipo de riesgo -- son
# PARAMETRIZABLES (se pueden ajustar aquí) y deben revisarse
# contra la normativa vigente en cada momento; el sistema no
# afirma que cumplirlos garantice cumplimiento legal, solo
# ayuda a hacerles seguimiento y no perderlos de vista.
DIAS_LIMITE_POR_RIESGO = {
    "Riesgo para la vida/integridad": 1,
    "Alta": 3,
    "Prioritaria": 10,
    "Normal": 15,
}


def _generar_radicado() -> str:
    """PQR-AAAA-NNNNNN, con un número que no se repite dentro del mismo año."""
    anio = date.today().year
    fila = consultar_uno(
        "SELECT COUNT(*) AS total FROM calidad_pqr WHERE radicado LIKE ?", (f"PQR-{anio}-%",)
    )
    consecutivo = (dict(fila)["total"] if fila else 0) + 1
    return f"PQR-{anio}-{consecutivo:06d}"


def _generar_clave_seguimiento() -> str:
    """Clave corta adicional al radicado, para que el seguimiento público no dependa solo de un número consecutivo adivinable."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _registrar_evento(pqr_id: int, tipo_evento: str, descripcion: str = None, area_anterior: str = None, area_nueva: str = None, usuario_id=None):
    ejecutar(
        "INSERT INTO pqr_eventos(pqr_id, tipo_evento, descripcion, area_anterior, area_nueva, usuario_id) VALUES (?, ?, ?, ?, ?, ?)",
        (pqr_id, tipo_evento, descripcion, area_anterior, area_nueva, usuario_id),
    )


def _calcular_fecha_limite(riesgo: str) -> str:
    from datetime import timedelta
    dias = DIAS_LIMITE_POR_RIESGO.get(riesgo, 15)
    return (date.today() + timedelta(days=dias)).isoformat()


def radicar_pqr(datos: dict, usuario_id=None, es_publica=False) -> dict:
    """
    Crea una PQR nueva con radicado único. Se usa tanto desde
    el registro interno (un empleado la digita) como desde el
    formulario público del portal web -- 'es_publica' solo
    cambia el canal por defecto y si se genera clave de
    seguimiento (necesaria para que alguien de afuera pueda
    consultarla sin iniciar sesión).
    """
    if datos.get("tipo") not in TIPOS_PQR:
        raise ValueError(f"Tipo no válido. Use uno de: {', '.join(TIPOS_PQR)}")
    if not datos.get("descripcion"):
        raise ValueError("Debe describir la petición, queja o reclamo.")
    if not datos.get("solicitante_nombre"):
        raise ValueError("Debe indicar el nombre de quien presenta la solicitud.")

    riesgo = datos.get("riesgo") or "Normal"
    if riesgo not in RIESGOS:
        riesgo = "Normal"

    radicado = _generar_radicado()
    clave_seguimiento = _generar_clave_seguimiento() if es_publica else None
    fecha_limite = _calcular_fecha_limite(riesgo)

    pqr_id = ejecutar(
        """
        INSERT INTO calidad_pqr(
            tipo, asunto, descripcion, prioridad, estado, radicado,
            solicitante_es_paciente, solicitante_relacion, solicitante_nombre,
            solicitante_documento, solicitante_telefono, solicitante_correo,
            paciente_id, canal, riesgo, fecha_limite, clave_seguimiento, usuario_creacion
        ) VALUES (?, ?, ?, ?, 'Nueva', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos["tipo"], datos.get("asunto") or datos["tipo"], datos["descripcion"], datos.get("prioridad", "Media"),
            radicado, 1 if datos.get("solicitante_relacion", "Paciente") == "Paciente" else 0,
            datos.get("solicitante_relacion", "Paciente"), datos["solicitante_nombre"],
            datos.get("solicitante_documento"), datos.get("solicitante_telefono"), datos.get("solicitante_correo"),
            datos.get("paciente_id") or None, datos.get("canal") or ("Portal web" if es_publica else "Presencial/Interno"),
            riesgo, fecha_limite, clave_seguimiento, usuario_id,
        ),
    )

    _registrar_evento(pqr_id, "Radicación", f"PQR radicada por canal: {datos.get('canal') or ('Portal web' if es_publica else 'Presencial/Interno')}", usuario_id=usuario_id)

    return {"id": pqr_id, "radicado": radicado, "clave_seguimiento": clave_seguimiento, "fecha_limite": fecha_limite}


def listar_bandeja(estado=None, riesgo=None, area_responsable=None, vencidas=False):
    sql = "SELECT * FROM calidad_pqr WHERE radicado IS NOT NULL"
    parametros = []
    if estado:
        sql += " AND estado=?"
        parametros.append(estado)
    if riesgo:
        sql += " AND riesgo=?"
        parametros.append(riesgo)
    if area_responsable:
        sql += " AND area_responsable=?"
        parametros.append(area_responsable)
    if vencidas:
        sql += " AND estado != 'Cerrada' AND date(fecha_limite) < date('now')"
    sql += """
        ORDER BY
            CASE riesgo WHEN 'Riesgo para la vida/integridad' THEN 0 WHEN 'Alta' THEN 1 WHEN 'Prioritaria' THEN 2 ELSE 3 END,
            fecha_creacion DESC
    """
    return [dict(f) for f in consultar_todos(sql, tuple(parametros))]


def obtener_pqr_completa(pqr_id: int):
    fila = consultar_uno("SELECT * FROM calidad_pqr WHERE id=?", (pqr_id,))
    if not fila:
        return None
    pqr = dict(fila)
    eventos = consultar_todos("SELECT * FROM pqr_eventos WHERE pqr_id=? ORDER BY fecha ASC", (pqr_id,))
    pqr["eventos"] = [dict(e) for e in eventos]
    return pqr


def asignar_area(pqr_id: int, area_responsable: str, usuario_id=None):
    if area_responsable not in AREAS_RESPONSABLES:
        raise ValueError(f"Área no válida. Use una de: {', '.join(AREAS_RESPONSABLES)}")

    actual = consultar_uno("SELECT area_responsable, estado FROM calidad_pqr WHERE id=?", (pqr_id,))
    if not actual:
        raise ValueError("La PQR no existe.")
    area_anterior = dict(actual)["area_responsable"]

    nuevo_estado = "Asignada" if dict(actual)["estado"] in ("Nueva", "En análisis") else dict(actual)["estado"]
    ejecutar("UPDATE calidad_pqr SET area_responsable=?, estado=? WHERE id=?", (area_responsable, nuevo_estado, pqr_id))

    tipo_evento = "Reasignación" if area_anterior else "Asignación"
    _registrar_evento(pqr_id, tipo_evento, area_anterior=area_anterior, area_nueva=area_responsable, usuario_id=usuario_id)


def cambiar_estado_pqr(pqr_id: int, estado: str, comentario: str = "", usuario_id=None):
    if estado not in ESTADOS_PQR:
        raise ValueError(f"Estado no válido. Use uno de: {', '.join(ESTADOS_PQR)}")
    ejecutar("UPDATE calidad_pqr SET estado=? WHERE id=?", (estado, pqr_id))
    _registrar_evento(pqr_id, "Cambio de estado", comentario or f"Estado cambiado a: {estado}", usuario_id=usuario_id)


def responder_pqr(pqr_id: int, respuesta: str, medio_respuesta: str, usuario_id=None):
    if not respuesta:
        raise ValueError("Debe escribir la respuesta.")
    ejecutar(
        "UPDATE calidad_pqr SET respuesta=?, medio_respuesta=?, estado='Cerrada', fecha_cierre=CURRENT_TIMESTAMP WHERE id=?",
        (respuesta, medio_respuesta, pqr_id),
    )
    _registrar_evento(pqr_id, "Respuesta y cierre", f"Respondida por {medio_respuesta}", usuario_id=usuario_id)


def agregar_comentario(pqr_id: int, comentario: str, usuario_id=None):
    if not comentario:
        raise ValueError("El comentario no puede estar vacío.")
    _registrar_evento(pqr_id, "Comentario", comentario, usuario_id=usuario_id)


def indicadores_pqr_siau():
    resumen = consultar_uno(
        """
        SELECT
            SUM(CASE WHEN estado != 'Cerrada' THEN 1 ELSE 0 END) AS abiertas,
            SUM(CASE WHEN estado = 'Nueva' THEN 1 ELSE 0 END) AS nuevas,
            SUM(CASE WHEN estado != 'Cerrada' AND date(fecha_limite) < date('now') THEN 1 ELSE 0 END) AS vencidas,
            SUM(CASE WHEN estado != 'Cerrada' AND date(fecha_limite) BETWEEN date('now') AND date('now', '+2 days') THEN 1 ELSE 0 END) AS proximas_vencer,
            SUM(CASE WHEN estado != 'Cerrada' AND riesgo IN ('Alta', 'Riesgo para la vida/integridad') THEN 1 ELSE 0 END) AS alto_riesgo
        FROM calidad_pqr WHERE radicado IS NOT NULL
        """
    )
    r = dict(resumen) if resumen else {}
    return {
        "abiertas": r.get("abiertas") or 0,
        "nuevas": r.get("nuevas") or 0,
        "vencidas": r.get("vencidas") or 0,
        "proximas_vencer": r.get("proximas_vencer") or 0,
        "alto_riesgo": r.get("alto_riesgo") or 0,
    }


# ==========================================================
# CONSULTA PÚBLICA (sin iniciar sesión)
# ==========================================================

def consultar_estado_publico(radicado: str, clave_seguimiento: str):
    """
    Para la página pública de seguimiento -- exige el radicado
    Y la clave de seguimiento juntos (no solo el número
    consecutivo, que sería adivinable), y NUNCA devuelve datos
    clínicos ni información sensible del paciente -- solo el
    estado administrativo de la solicitud.
    """
    fila = consultar_uno(
        "SELECT * FROM calidad_pqr WHERE radicado=? AND clave_seguimiento=?",
        (radicado.strip().upper(), clave_seguimiento.strip().upper()),
    )
    if not fila:
        return None

    pqr = dict(fila)
    return {
        "radicado": pqr["radicado"],
        "tipo": pqr["tipo"],
        "estado": pqr["estado"],
        "fecha_creacion": pqr["fecha_creacion"],
        "fecha_limite": pqr["fecha_limite"],
        "fecha_cierre": pqr["fecha_cierre"],
        "ultima_actualizacion": _ultima_actualizacion(pqr["id"]),
    }


def _ultima_actualizacion(pqr_id: int):
    fila = consultar_uno("SELECT fecha FROM pqr_eventos WHERE pqr_id=? ORDER BY fecha DESC LIMIT 1", (pqr_id,))
    return dict(fila)["fecha"] if fila else None
