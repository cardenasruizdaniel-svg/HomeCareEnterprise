"""
HomeCare Enterprise - Módulo de Calidad

Tres frentes:
1. PQR/Solicitudes: quejas, peticiones, reclamos y
   solicitudes, con responsable asignado y respuesta.
2. Planificación de trabajo: tareas/planes con
   responsable, fecha límite y estado.
3. Evaluación de la atención al paciente: calificación
   (1-5) de la atención recibida, por paciente y
   opcionalmente por profesional.
"""

from database.database import consultar_escalar, consultar_todos, consultar_uno, ejecutar

ESTADOS_PQR = ["Abierto", "En proceso", "Cerrado"]
PRIORIDADES = ["Baja", "Media", "Alta", "Urgente"]
TIPOS_PQR = ["Petición", "Queja", "Reclamo", "Solicitud", "Sugerencia", "Felicitación"]
ESTADOS_PLANIFICACION = ["Pendiente", "En curso", "Completada", "Atrasada"]


# ==========================================================
# PQR / SOLICITUDES
# ==========================================================

def listar_pqr(estado=None, tipo=None):
    condiciones, parametros = [], []
    if estado:
        condiciones.append("q.estado=?")
        parametros.append(estado)
    if tipo:
        condiciones.append("q.tipo=?")
        parametros.append(tipo)
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    filas = consultar_todos(
        f"""
        SELECT q.*, p.primer_nombre || ' ' || p.primer_apellido AS paciente_nombre,
               pr.nombre_completo AS responsable_nombre
        FROM calidad_pqr q
        LEFT JOIN pacientes p ON p.id = q.paciente_id
        LEFT JOIN profesionales pr ON pr.id = q.responsable_id
        {where}
        ORDER BY q.fecha_creacion DESC
        """,
        tuple(parametros),
    )
    return [dict(f) for f in filas]


def obtener_pqr(pqr_id: int):
    fila = consultar_uno(
        """
        SELECT q.*, p.primer_nombre || ' ' || p.primer_apellido AS paciente_nombre,
               pr.nombre_completo AS responsable_nombre
        FROM calidad_pqr q
        LEFT JOIN pacientes p ON p.id = q.paciente_id
        LEFT JOIN profesionales pr ON pr.id = q.responsable_id
        WHERE q.id=?
        """,
        (pqr_id,),
    )
    return dict(fila) if fila else None


def crear_pqr(tipo, paciente_id, asunto, descripcion, prioridad, responsable_id, usuario_id) -> int:
    if not asunto:
        raise ValueError("Debe indicar el asunto.")
    return ejecutar(
        """
        INSERT INTO calidad_pqr(tipo, paciente_id, asunto, descripcion, prioridad, responsable_id, usuario_creacion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (tipo or "PQR", paciente_id or None, asunto, descripcion or "", prioridad or "Media",
         responsable_id or None, usuario_id),
    )


def actualizar_estado_pqr(pqr_id, estado, respuesta=None):
    from datetime import date
    fecha_cierre = date.today().isoformat() if estado == "Cerrado" else None
    ejecutar(
        "UPDATE calidad_pqr SET estado=?, respuesta=COALESCE(?, respuesta), fecha_cierre=? WHERE id=?",
        (estado, respuesta, fecha_cierre, pqr_id),
    )


def indicadores_pqr():
    total = consultar_escalar("SELECT COUNT(*) FROM calidad_pqr") or 0
    abiertos = consultar_escalar("SELECT COUNT(*) FROM calidad_pqr WHERE estado != 'Cerrado'") or 0
    return {"total": total, "abiertos": abiertos, "cerrados": total - abiertos}


# ==========================================================
# PLANIFICACIÓN DE TRABAJO
# ==========================================================

def listar_planificacion(estado=None):
    condicion = "WHERE p.estado=?" if estado else ""
    parametros = (estado,) if estado else ()
    filas = consultar_todos(
        f"""
        SELECT p.*, pr.nombre_completo AS responsable_nombre
        FROM calidad_planificacion p
        LEFT JOIN profesionales pr ON pr.id = p.responsable_id
        {condicion}
        ORDER BY p.fecha_limite
        """,
        parametros,
    )
    return [dict(f) for f in filas]


def crear_planificacion(titulo, descripcion, responsable_id, fecha_inicio, fecha_limite, prioridad, usuario_id) -> int:
    if not titulo:
        raise ValueError("Debe indicar el título de la tarea/plan.")
    return ejecutar(
        """
        INSERT INTO calidad_planificacion(titulo, descripcion, responsable_id, fecha_inicio, fecha_limite, prioridad, usuario_creacion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (titulo, descripcion or "", responsable_id or None, fecha_inicio or None, fecha_limite or None,
         prioridad or "Media", usuario_id),
    )


def actualizar_estado_planificacion(planificacion_id, estado):
    ejecutar("UPDATE calidad_planificacion SET estado=? WHERE id=?", (estado, planificacion_id))


# ==========================================================
# EVALUACIÓN DE LA ATENCIÓN AL PACIENTE
# ==========================================================

def listar_evaluaciones(paciente_id=None):
    condicion = "WHERE e.paciente_id=?" if paciente_id else ""
    parametros = (paciente_id,) if paciente_id else ()
    filas = consultar_todos(
        f"""
        SELECT e.*, p.primer_nombre || ' ' || p.primer_apellido AS paciente_nombre,
               pr.nombre_completo AS profesional_nombre
        FROM calidad_evaluaciones e
        JOIN pacientes p ON p.id = e.paciente_id
        LEFT JOIN profesionales pr ON pr.id = e.profesional_id
        {condicion}
        ORDER BY e.fecha_creacion DESC
        """,
        parametros,
    )
    return [dict(f) for f in filas]


def crear_evaluacion(paciente_id, profesional_id, calificacion, aspectos_evaluados, comentario, usuario_id) -> int:
    if not paciente_id:
        raise ValueError("Debe indicar el paciente evaluado.")
    if not calificacion or not (1 <= int(calificacion) <= 5):
        raise ValueError("La calificación debe ser de 1 a 5.")
    return ejecutar(
        """
        INSERT INTO calidad_evaluaciones(paciente_id, profesional_id, calificacion, aspectos_evaluados, comentario, usuario_registro)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (paciente_id, profesional_id or None, int(calificacion), aspectos_evaluados or "", comentario or "", usuario_id),
    )


def promedio_calificacion():
    promedio = consultar_escalar("SELECT AVG(calificacion) FROM calidad_evaluaciones")
    return round(promedio, 1) if promedio else None


def dashboard_calidad():
    return {
        "pqr": indicadores_pqr(),
        "planificacion_pendientes": consultar_escalar(
            "SELECT COUNT(*) FROM calidad_planificacion WHERE estado IN ('Pendiente','En curso')"
        ) or 0,
        "promedio_evaluacion": promedio_calificacion(),
        "total_evaluaciones": consultar_escalar("SELECT COUNT(*) FROM calidad_evaluaciones") or 0,
    }
