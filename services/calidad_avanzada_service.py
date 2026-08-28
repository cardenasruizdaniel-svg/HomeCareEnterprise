"""
HomeCare Enterprise - Sistema Integral de Gestión de Calidad (Fase 1)

Motor de Normatividad + PAMEC + Auditorías de Calidad +
Hallazgos/No Conformidades + Acciones de Mejora (CAPA).

Ciclo completo: Planear (PAMEC) -> Ejecutar (Auditoría) ->
Detectar (Hallazgo) -> Corregir (Acción) -> Verificar (Eficacia)
-> Mejorar.

No reemplaza 'calidad_service.py' (PQR simple, planificación
genérica, evaluaciones de satisfacción) -- convive con él.
"""

from database.database import consultar_todos, consultar_uno, ejecutar

# ==========================================================
# MOTOR DE NORMATIVIDAD
# ==========================================================

TIPOS_NORMA = ("Resolución", "Decreto", "Ley", "Circular", "Manual técnico", "Política", "Otro")
ESTADOS_NORMA = ("Vigente", "En transición", "Derogada", "Proyecto")


def listar_normas(solo_vigentes=False):
    sql = "SELECT * FROM normas_regulatorias WHERE activo=1"
    if solo_vigentes:
        sql += " AND estado IN ('Vigente', 'En transición')"
    sql += " ORDER BY anio DESC, numero DESC"
    return [dict(f) for f in consultar_todos(sql)]


def obtener_norma(norma_id: int):
    fila = consultar_uno("SELECT * FROM normas_regulatorias WHERE id=?", (norma_id,))
    return dict(fila) if fila else None


def crear_norma(datos: dict, usuario_id=None) -> int:
    if not datos.get("tipo") or not datos.get("numero") or not datos.get("anio"):
        raise ValueError("Debe indicar el tipo, número y año de la norma.")
    if not datos.get("titulo"):
        raise ValueError("Debe indicar el título/objeto de la norma.")

    return ejecutar(
        """
        INSERT INTO normas_regulatorias(
            tipo, numero, anio, entidad_emisora, titulo, fecha_expedicion,
            fecha_vigencia_desde, fecha_vigencia_hasta, estado, norma_que_deroga,
            procesos_afectados, requisitos, evidencias_requeridas, responsable_id,
            frecuencia_revision, observaciones, usuario_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos["tipo"], datos["numero"], datos["anio"], datos.get("entidad_emisora", "Ministerio de Salud y Protección Social"),
            datos["titulo"], datos.get("fecha_expedicion"), datos.get("fecha_vigencia_desde"), datos.get("fecha_vigencia_hasta"),
            datos.get("estado", "Vigente"), datos.get("norma_que_deroga"), datos.get("procesos_afectados"),
            datos.get("requisitos"), datos.get("evidencias_requeridas"), datos.get("responsable_id") or None,
            datos.get("frecuencia_revision"), datos.get("observaciones"), usuario_id,
        ),
    )


def actualizar_estado_norma(norma_id: int, estado: str):
    if estado not in ESTADOS_NORMA:
        raise ValueError(f"Estado no válido. Use uno de: {', '.join(ESTADOS_NORMA)}")
    ejecutar("UPDATE normas_regulatorias SET estado=? WHERE id=?", (estado, norma_id))


# ==========================================================
# PAMEC
# ==========================================================

ESTADOS_PAMEC = ("Planeado", "En ejecución", "Cerrado")
ESTADOS_PROCESO_PAMEC = ("Planeado", "En ejecución", "Pendiente", "Vencido", "Cerrado", "No efectivo")


def listar_ciclos_pamec():
    return [dict(f) for f in consultar_todos("SELECT * FROM pamec_ciclos ORDER BY periodo_desde DESC")]


def obtener_ciclo_pamec(ciclo_id: int):
    fila = consultar_uno("SELECT * FROM pamec_ciclos WHERE id=?", (ciclo_id,))
    if not fila:
        return None
    ciclo = dict(fila)
    ciclo["procesos"] = listar_procesos_pamec(ciclo_id)
    return ciclo


def crear_ciclo_pamec(datos: dict, usuario_id=None) -> int:
    if not datos.get("nombre"):
        raise ValueError("Debe indicar el nombre del ciclo PAMEC.")
    if not datos.get("periodo_desde") or not datos.get("periodo_hasta"):
        raise ValueError("Debe indicar el periodo (desde/hasta) del ciclo.")

    return ejecutar(
        """
        INSERT INTO pamec_ciclos(nombre, periodo_desde, periodo_hasta, objetivos, alcance,
            criterios_priorizacion, responsable_id, norma_id, usuario_creacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos["nombre"], datos["periodo_desde"], datos["periodo_hasta"], datos.get("objetivos"),
            datos.get("alcance"), datos.get("criterios_priorizacion"), datos.get("responsable_id") or None,
            datos.get("norma_id") or None, usuario_id,
        ),
    )


def actualizar_estado_pamec(ciclo_id: int, estado: str):
    if estado not in ESTADOS_PAMEC:
        raise ValueError(f"Estado no válido. Use uno de: {', '.join(ESTADOS_PAMEC)}")
    ejecutar("UPDATE pamec_ciclos SET estado=? WHERE id=?", (estado, ciclo_id))


def listar_procesos_pamec(ciclo_id: int):
    return [dict(f) for f in consultar_todos("SELECT * FROM pamec_procesos_priorizados WHERE ciclo_id=? ORDER BY id", (ciclo_id,))]


def agregar_proceso_pamec(ciclo_id: int, datos: dict) -> int:
    if not datos.get("proceso"):
        raise ValueError("Debe indicar el nombre del proceso priorizado.")

    return ejecutar(
        """
        INSERT INTO pamec_procesos_priorizados(ciclo_id, proceso, riesgo_identificado, indicador, meta, responsable_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (ciclo_id, datos["proceso"], datos.get("riesgo_identificado"), datos.get("indicador"), datos.get("meta"), datos.get("responsable_id") or None),
    )


def actualizar_resultado_proceso_pamec(proceso_id: int, resultado, porcentaje_cumplimiento, brecha, analisis, estado):
    if estado not in ESTADOS_PROCESO_PAMEC:
        raise ValueError(f"Estado no válido. Use uno de: {', '.join(ESTADOS_PROCESO_PAMEC)}")

    ejecutar(
        """
        UPDATE pamec_procesos_priorizados
        SET resultado=?, porcentaje_cumplimiento=?, brecha=?, analisis=?, estado=?
        WHERE id=?
        """,
        (resultado, porcentaje_cumplimiento, brecha, analisis, estado, proceso_id),
    )


# ==========================================================
# AUDITORÍAS DE CALIDAD
# ==========================================================

TIPOS_AUDITORIA = ("Interna", "PAMEC", "Habilitación", "Seguimiento", "Seguridad del paciente", "Otra")
ESTADOS_AUDITORIA = ("Planeada", "En ejecución", "Cerrada")


def listar_auditorias(estado=None, ciclo_pamec_id=None):
    sql = """
        SELECT a.*, pr.primer_nombre AS auditor_nombre, pr.primer_apellido AS auditor_apellido
        FROM auditorias_calidad a
        LEFT JOIN profesionales pr ON pr.id = a.auditor_id
        WHERE 1=1
    """
    parametros = []
    if estado:
        sql += " AND a.estado=?"
        parametros.append(estado)
    if ciclo_pamec_id:
        sql += " AND a.ciclo_pamec_id=?"
        parametros.append(ciclo_pamec_id)
    sql += " ORDER BY a.fecha DESC"
    return [dict(f) for f in consultar_todos(sql, tuple(parametros))]


def obtener_auditoria(auditoria_id: int):
    fila = consultar_uno(
        """
        SELECT a.*, pr.primer_nombre AS auditor_nombre, pr.primer_apellido AS auditor_apellido,
               pa.primer_nombre AS auditado_nombre, pa.primer_apellido AS auditado_apellido
        FROM auditorias_calidad a
        LEFT JOIN profesionales pr ON pr.id = a.auditor_id
        LEFT JOIN profesionales pa ON pa.id = a.auditado_id
        WHERE a.id=?
        """,
        (auditoria_id,),
    )
    if not fila:
        return None
    auditoria = dict(fila)
    auditoria["hallazgos"] = listar_hallazgos(auditoria_id=auditoria_id)
    return auditoria


def crear_auditoria(datos: dict, usuario_id=None) -> int:
    if datos.get("tipo") not in TIPOS_AUDITORIA:
        raise ValueError(f"Tipo de auditoría no válido. Use uno de: {', '.join(TIPOS_AUDITORIA)}")
    if not datos.get("proceso"):
        raise ValueError("Debe indicar el proceso a auditar.")
    if not datos.get("fecha"):
        raise ValueError("Debe indicar la fecha de la auditoría.")

    return ejecutar(
        """
        INSERT INTO auditorias_calidad(
            ciclo_pamec_id, tipo, proceso, servicio, auditor_id, auditado_id, fecha,
            objetivo, alcance, criterios, norma_id, usuario_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos.get("ciclo_pamec_id") or None, datos["tipo"], datos["proceso"], datos.get("servicio"),
            datos.get("auditor_id") or None, datos.get("auditado_id") or None, datos["fecha"],
            datos.get("objetivo"), datos.get("alcance"), datos.get("criterios"), datos.get("norma_id") or None, usuario_id,
        ),
    )


def cerrar_auditoria(auditoria_id: int, resultado_general: str, observaciones: str = ""):
    hallazgos = listar_hallazgos(auditoria_id=auditoria_id)
    total = len(hallazgos)
    sin_criticos_ni_mayores = sum(1 for h in hallazgos if h["clasificacion"] in ("Crítico", "Mayor"))
    porcentaje = 100.0 if total == 0 else round(100 * (total - sin_criticos_ni_mayores) / total, 1)

    ejecutar(
        """
        UPDATE auditorias_calidad
        SET estado='Cerrada', resultado_general=?, porcentaje_cumplimiento=?, observaciones=?
        WHERE id=?
        """,
        (resultado_general, porcentaje, observaciones, auditoria_id),
    )


# ==========================================================
# HALLAZGOS / NO CONFORMIDADES
# ==========================================================

CLASIFICACIONES_HALLAZGO = ("Crítico", "Mayor", "Menor", "Observación", "Oportunidad de mejora")
ESTADOS_HALLAZGO = ("Abierto", "En análisis", "Con acción asignada", "Cerrado")


def listar_hallazgos(estado=None, auditoria_id=None, clasificacion=None):
    sql = """
        SELECT h.*, pr.primer_nombre AS resp_nombre, pr.primer_apellido AS resp_apellido
        FROM hallazgos_calidad h
        LEFT JOIN profesionales pr ON pr.id = h.responsable_id
        WHERE 1=1
    """
    parametros = []
    if estado:
        sql += " AND h.estado=?"
        parametros.append(estado)
    if auditoria_id:
        sql += " AND h.auditoria_id=?"
        parametros.append(auditoria_id)
    if clasificacion:
        sql += " AND h.clasificacion=?"
        parametros.append(clasificacion)
    sql += " ORDER BY h.fecha DESC"
    return [dict(f) for f in consultar_todos(sql, tuple(parametros))]


def obtener_hallazgo(hallazgo_id: int):
    fila = consultar_uno(
        """
        SELECT h.*, pr.primer_nombre AS resp_nombre, pr.primer_apellido AS resp_apellido
        FROM hallazgos_calidad h
        LEFT JOIN profesionales pr ON pr.id = h.responsable_id
        WHERE h.id=?
        """,
        (hallazgo_id,),
    )
    if not fila:
        return None
    hallazgo = dict(fila)
    hallazgo["acciones"] = listar_acciones(hallazgo_id=hallazgo_id)
    return hallazgo


def crear_hallazgo(datos: dict, usuario_id=None) -> int:
    if datos.get("clasificacion") not in CLASIFICACIONES_HALLAZGO:
        raise ValueError(f"Clasificación no válida. Use una de: {', '.join(CLASIFICACIONES_HALLAZGO)}")
    if not datos.get("proceso"):
        raise ValueError("Debe indicar el proceso donde se identificó el hallazgo.")
    if not datos.get("descripcion"):
        raise ValueError("Debe describir el hallazgo.")
    if not datos.get("fecha"):
        raise ValueError("Debe indicar la fecha del hallazgo.")

    return ejecutar(
        """
        INSERT INTO hallazgos_calidad(
            auditoria_id, fuente, clasificacion, proceso, servicio, fecha, descripcion,
            evidencia, norma_id, responsable_id, riesgo, fecha_limite, usuario_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos.get("auditoria_id") or None, datos.get("fuente", "Auditoría"), datos["clasificacion"],
            datos["proceso"], datos.get("servicio"), datos["fecha"], datos["descripcion"], datos.get("evidencia"),
            datos.get("norma_id") or None, datos.get("responsable_id") or None, datos.get("riesgo"),
            datos.get("fecha_limite"), usuario_id,
        ),
    )


def registrar_analisis_causa(hallazgo_id: int, causa_raiz: str, metodologia_analisis: str):
    if not causa_raiz:
        raise ValueError("Debe registrar la causa raíz identificada.")
    ejecutar(
        "UPDATE hallazgos_calidad SET causa_raiz=?, metodologia_analisis=?, estado='En análisis' WHERE id=?",
        (causa_raiz, metodologia_analisis, hallazgo_id),
    )


def cerrar_hallazgo(hallazgo_id: int):
    acciones = listar_acciones(hallazgo_id=hallazgo_id)
    if not acciones:
        raise ValueError("No se puede cerrar un hallazgo sin al menos una acción de mejora registrada.")
    if any(a["estado"] not in ("Verificado", "Cerrado") for a in acciones):
        raise ValueError("Todas las acciones del hallazgo deben estar verificadas antes de cerrarlo.")
    ejecutar("UPDATE hallazgos_calidad SET estado='Cerrado' WHERE id=?", (hallazgo_id,))


# ==========================================================
# ACCIONES DE MEJORA (CAPA)
# ==========================================================

TIPOS_ACCION = ("Correctiva", "Preventiva", "De mejora")
ESTADOS_ACCION = ("Planeado", "En ejecución", "Vencido", "Ejecutado", "Verificado", "No efectivo", "Cerrado")


def listar_acciones(estado=None, hallazgo_id=None, responsable_id=None):
    sql = """
        SELECT ac.*, pr.primer_nombre AS resp_nombre, pr.primer_apellido AS resp_apellido
        FROM acciones_mejora ac
        LEFT JOIN profesionales pr ON pr.id = ac.responsable_id
        WHERE 1=1
    """
    parametros = []
    if estado:
        sql += " AND ac.estado=?"
        parametros.append(estado)
    if hallazgo_id:
        sql += " AND ac.hallazgo_id=?"
        parametros.append(hallazgo_id)
    if responsable_id:
        sql += " AND ac.responsable_id=?"
        parametros.append(responsable_id)
    sql += " ORDER BY ac.fecha_compromiso ASC"
    return [dict(f) for f in consultar_todos(sql, tuple(parametros))]


def crear_accion(hallazgo_id: int, datos: dict, usuario_id=None) -> int:
    if datos.get("tipo") not in TIPOS_ACCION:
        raise ValueError(f"Tipo de acción no válido. Use uno de: {', '.join(TIPOS_ACCION)}")
    if not datos.get("descripcion"):
        raise ValueError("Debe describir la acción a implementar.")
    if not datos.get("fecha_compromiso"):
        raise ValueError("Debe indicar la fecha compromiso de la acción.")

    accion_id = ejecutar(
        """
        INSERT INTO acciones_mejora(hallazgo_id, tipo, descripcion, responsable_id, fecha_compromiso, usuario_creacion)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (hallazgo_id, datos["tipo"], datos["descripcion"], datos.get("responsable_id") or None, datos["fecha_compromiso"], usuario_id),
    )

    # El hallazgo pasa a "Con acción asignada" en cuanto tiene al menos una accion registrada.
    ejecutar("UPDATE hallazgos_calidad SET estado='Con acción asignada' WHERE id=? AND estado != 'Cerrado'", (hallazgo_id,))

    return accion_id


def ejecutar_accion(accion_id: int, fecha_ejecucion: str, evidencia: str):
    if not fecha_ejecucion:
        raise ValueError("Debe indicar la fecha en que se ejecutó la acción.")
    ejecutar(
        "UPDATE acciones_mejora SET estado='Ejecutado', fecha_ejecucion=?, evidencia=? WHERE id=?",
        (fecha_ejecucion, evidencia, accion_id),
    )


def verificar_eficacia_accion(accion_id: int, fue_eficaz: bool, verificacion_eficacia: str, verificado_por_id=None):
    nuevo_estado = "Verificado" if fue_eficaz else "No efectivo"
    ejecutar(
        """
        UPDATE acciones_mejora
        SET estado=?, verificacion_eficacia=?, fecha_verificacion=CURRENT_TIMESTAMP, verificado_por_id=?
        WHERE id=?
        """,
        (nuevo_estado, verificacion_eficacia, verificado_por_id, accion_id),
    )


# ==========================================================
# DASHBOARD DE CALIDAD (FASE 1)
# ==========================================================

def resumen_dashboard_calidad():
    """Indicadores principales para el dashboard ejecutivo de calidad -- solo lo que ya existe en Fase 1."""
    hallazgos = consultar_uno(
        """
        SELECT
            SUM(CASE WHEN estado != 'Cerrado' THEN 1 ELSE 0 END) AS hallazgos_abiertos,
            SUM(CASE WHEN clasificacion = 'Crítico' AND estado != 'Cerrado' THEN 1 ELSE 0 END) AS hallazgos_criticos
        FROM hallazgos_calidad
        """
    )
    acciones = consultar_uno(
        """
        SELECT
            SUM(CASE WHEN estado NOT IN ('Verificado', 'Cerrado') THEN 1 ELSE 0 END) AS acciones_abiertas,
            SUM(CASE WHEN estado NOT IN ('Verificado', 'Cerrado') AND date(fecha_compromiso) < date('now') THEN 1 ELSE 0 END) AS acciones_vencidas
        FROM acciones_mejora
        """
    )
    auditorias = consultar_uno(
        "SELECT SUM(CASE WHEN estado='Planeada' THEN 1 ELSE 0 END) AS auditorias_pendientes FROM auditorias_calidad"
    )
    ciclos_activos = consultar_uno("SELECT COUNT(*) AS total FROM pamec_ciclos WHERE estado='En ejecución'")
    riesgos = consultar_uno(
        "SELECT COUNT(*) AS riesgos_altos FROM matriz_riesgos WHERE nivel_inherente IN ('Alto', 'Extremo') AND estado NOT IN ('Cerrado', 'Aceptado')"
    )
    eventos_seguridad = consultar_uno(
        """
        SELECT
            SUM(CASE WHEN estado != 'Cerrado' THEN 1 ELSE 0 END) AS eventos_abiertos,
            SUM(CASE WHEN severidad IN ('Grave', 'Centinela') AND estado != 'Cerrado' THEN 1 ELSE 0 END) AS eventos_graves
        FROM eventos_seguridad_paciente
        """
    )
    pqr = consultar_uno(
        """
        SELECT
            SUM(CASE WHEN estado = 'Nueva' THEN 1 ELSE 0 END) AS pqr_nuevas,
            SUM(CASE WHEN estado != 'Cerrada' AND date(fecha_limite) < date('now') THEN 1 ELSE 0 END) AS pqr_vencidas
        FROM calidad_pqr WHERE radicado IS NOT NULL
        """
    )

    h = dict(hallazgos) if hallazgos else {}
    a = dict(acciones) if acciones else {}
    au = dict(auditorias) if auditorias else {}
    c = dict(ciclos_activos) if ciclos_activos else {}
    r = dict(riesgos) if riesgos else {}
    ev = dict(eventos_seguridad) if eventos_seguridad else {}
    pq = dict(pqr) if pqr else {}

    return {
        "hallazgos_abiertos": h.get("hallazgos_abiertos") or 0,
        "hallazgos_criticos": h.get("hallazgos_criticos") or 0,
        "acciones_abiertas": a.get("acciones_abiertas") or 0,
        "acciones_vencidas": a.get("acciones_vencidas") or 0,
        "auditorias_pendientes": au.get("auditorias_pendientes") or 0,
        "ciclos_pamec_activos": c.get("total") or 0,
        "riesgos_altos": r.get("riesgos_altos") or 0,
        "eventos_seguridad_abiertos": ev.get("eventos_abiertos") or 0,
        "eventos_seguridad_graves": ev.get("eventos_graves") or 0,
        "pqr_nuevas": pq.get("pqr_nuevas") or 0,
        "pqr_vencidas": pq.get("pqr_vencidas") or 0,
    }


# ==========================================================
# MATRIZ DE RIESGOS
# ==========================================================

PROBABILIDADES = ("Rara vez", "Improbable", "Posible", "Probable", "Casi seguro")
IMPACTOS = ("Insignificante", "Menor", "Moderado", "Mayor", "Catastrófico")
ESTADOS_RIESGO = ("Identificado", "Con controles", "En tratamiento", "Aceptado", "Cerrado")

# Matriz estándar 5x5 (probabilidad x impacto -> nivel). Fila =
# índice de probabilidad (0-4), columna = índice de impacto (0-4).
# Es una convención habitual de gestión de riesgo, ajustable si
# la IPS define su propia matriz institucional más adelante.
_MATRIZ_NIVELES = [
    ["Bajo",    "Bajo",    "Medio",   "Medio",   "Alto"],
    ["Bajo",    "Medio",   "Medio",   "Alto",    "Alto"],
    ["Medio",   "Medio",   "Alto",    "Alto",    "Extremo"],
    ["Medio",   "Alto",    "Alto",    "Extremo", "Extremo"],
    ["Alto",    "Alto",    "Extremo", "Extremo", "Extremo"],
]


def calcular_nivel_riesgo(probabilidad: str, impacto: str) -> str:
    if probabilidad not in PROBABILIDADES or impacto not in IMPACTOS:
        return "Sin calcular"
    fila = PROBABILIDADES.index(probabilidad)
    columna = IMPACTOS.index(impacto)
    return _MATRIZ_NIVELES[fila][columna]


def listar_riesgos(estado=None):
    sql = """
        SELECT r.*, pr.primer_nombre AS resp_nombre, pr.primer_apellido AS resp_apellido
        FROM matriz_riesgos r
        LEFT JOIN profesionales pr ON pr.id = r.responsable_id
        WHERE 1=1
    """
    parametros = []
    if estado:
        sql += " AND r.estado=?"
        parametros.append(estado)
    sql += " ORDER BY CASE nivel_inherente WHEN 'Extremo' THEN 0 WHEN 'Alto' THEN 1 WHEN 'Medio' THEN 2 ELSE 3 END, r.fecha_identificacion DESC"
    return [dict(f) for f in consultar_todos(sql, tuple(parametros))]


def obtener_riesgo(riesgo_id: int):
    fila = consultar_uno(
        """
        SELECT r.*, pr.primer_nombre AS resp_nombre, pr.primer_apellido AS resp_apellido
        FROM matriz_riesgos r
        LEFT JOIN profesionales pr ON pr.id = r.responsable_id
        WHERE r.id=?
        """,
        (riesgo_id,),
    )
    return dict(fila) if fila else None


def crear_riesgo(datos: dict, usuario_id=None) -> int:
    if not datos.get("proceso") or not datos.get("riesgo"):
        raise ValueError("Debe indicar el proceso y la descripción del riesgo.")
    if datos.get("probabilidad") not in PROBABILIDADES or datos.get("impacto") not in IMPACTOS:
        raise ValueError("Debe indicar una probabilidad y un impacto válidos.")
    if not datos.get("fecha_identificacion"):
        raise ValueError("Debe indicar la fecha de identificación del riesgo.")

    nivel = calcular_nivel_riesgo(datos["probabilidad"], datos["impacto"])

    return ejecutar(
        """
        INSERT INTO matriz_riesgos(
            proceso, riesgo, causa, consecuencia, probabilidad, impacto, nivel_inherente,
            controles, responsable_id, fecha_identificacion, usuario_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos["proceso"], datos["riesgo"], datos.get("causa"), datos.get("consecuencia"),
            datos["probabilidad"], datos["impacto"], nivel, datos.get("controles"),
            datos.get("responsable_id") or None, datos["fecha_identificacion"], usuario_id,
        ),
    )


def actualizar_tratamiento_riesgo(riesgo_id: int, riesgo_residual: str, tratamiento: str, accion: str, estado: str):
    if estado not in ESTADOS_RIESGO:
        raise ValueError(f"Estado no válido. Use uno de: {', '.join(ESTADOS_RIESGO)}")
    ejecutar(
        "UPDATE matriz_riesgos SET riesgo_residual=?, tratamiento=?, accion=?, estado=? WHERE id=?",
        (riesgo_residual, tratamiento, accion, estado, riesgo_id),
    )


# ==========================================================
# SEGURIDAD DEL PACIENTE
# ==========================================================

TIPOS_EVENTO_SEGURIDAD = (
    "Evento adverso", "Incidente", "Evento centinela", "Complicación",
    "Relacionado con medicamentos", "Relacionado con caídas", "Relacionado con atención domiciliaria",
    "Error de identificación", "Error de comunicación", "Relacionado con dispositivos", "Otro",
)
SEVERIDADES_EVENTO = ("Leve", "Moderada", "Grave", "Centinela")
ESTADOS_EVENTO_SEGURIDAD = ("Reportado", "En análisis", "Con plan de mejora", "En seguimiento", "Cerrado")


def listar_eventos_seguridad(estado=None, tipo=None, severidad=None):
    sql = """
        SELECT e.*, p.primer_nombre AS pac_nombre, p.primer_apellido AS pac_apellido,
               pr.primer_nombre AS prof_nombre, pr.primer_apellido AS prof_apellido
        FROM eventos_seguridad_paciente e
        LEFT JOIN pacientes p ON p.id = e.paciente_id
        LEFT JOIN profesionales pr ON pr.id = e.profesional_id
        WHERE 1=1
    """
    parametros = []
    if estado:
        sql += " AND e.estado=?"
        parametros.append(estado)
    if tipo:
        sql += " AND e.tipo=?"
        parametros.append(tipo)
    if severidad:
        sql += " AND e.severidad=?"
        parametros.append(severidad)
    sql += " ORDER BY CASE severidad WHEN 'Centinela' THEN 0 WHEN 'Grave' THEN 1 WHEN 'Moderada' THEN 2 ELSE 3 END, e.fecha DESC"
    return [dict(f) for f in consultar_todos(sql, tuple(parametros))]


def obtener_evento_seguridad(evento_id: int):
    fila = consultar_uno(
        """
        SELECT e.*, p.primer_nombre AS pac_nombre, p.primer_apellido AS pac_apellido,
               pr.primer_nombre AS prof_nombre, pr.primer_apellido AS prof_apellido
        FROM eventos_seguridad_paciente e
        LEFT JOIN pacientes p ON p.id = e.paciente_id
        LEFT JOIN profesionales pr ON pr.id = e.profesional_id
        WHERE e.id=?
        """,
        (evento_id,),
    )
    return dict(fila) if fila else None


def crear_evento_seguridad(datos: dict, usuario_id=None) -> int:
    if datos.get("tipo") not in TIPOS_EVENTO_SEGURIDAD:
        raise ValueError(f"Tipo de evento no válido. Use uno de: {', '.join(TIPOS_EVENTO_SEGURIDAD)}")
    if datos.get("severidad") not in SEVERIDADES_EVENTO:
        raise ValueError(f"Severidad no válida. Use una de: {', '.join(SEVERIDADES_EVENTO)}")
    if not datos.get("descripcion"):
        raise ValueError("Debe describir el evento.")
    if not datos.get("fecha"):
        raise ValueError("Debe indicar la fecha del evento.")

    return ejecutar(
        """
        INSERT INTO eventos_seguridad_paciente(
            paciente_id, servicio, profesional_id, fecha, tipo, severidad, descripcion,
            acciones_inmediatas, usuario_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos.get("paciente_id") or None, datos.get("servicio"), datos.get("profesional_id") or None,
            datos["fecha"], datos["tipo"], datos["severidad"], datos["descripcion"],
            datos.get("acciones_inmediatas"), usuario_id,
        ),
    )


def registrar_analisis_evento(evento_id: int, analisis: str, causa_raiz: str, plan_mejora: str):
    if not analisis:
        raise ValueError("Debe registrar el análisis del evento.")
    ejecutar(
        "UPDATE eventos_seguridad_paciente SET analisis=?, causa_raiz=?, plan_mejora=?, estado='Con plan de mejora' WHERE id=?",
        (analisis, causa_raiz, plan_mejora, evento_id),
    )


def cerrar_evento_seguridad(evento_id: int, seguimiento: str):
    ejecutar(
        "UPDATE eventos_seguridad_paciente SET seguimiento=?, estado='Cerrado', fecha_cierre=CURRENT_TIMESTAMP WHERE id=?",
        (seguimiento, evento_id),
    )


def escalar_evento_a_hallazgo(evento_id: int, usuario_id=None) -> int:
    """
    Para eventos graves o centinela que ameritan tratarse con
    todo el rigor del ciclo de calidad (análisis de causa raíz
    formal + acciones CAPA verificables) -- crea un hallazgo de
    calidad clasificado como Crítico, vinculado al evento.
    """
    evento = obtener_evento_seguridad(evento_id)
    if not evento:
        raise ValueError("El evento no existe.")

    hallazgo_id = crear_hallazgo(
        {
            "fuente": "Seguridad del paciente",
            "clasificacion": "Crítico",
            "proceso": evento.get("servicio") or "Seguridad del paciente",
            "servicio": evento.get("servicio"),
            "fecha": evento["fecha"],
            "descripcion": f"[{evento['tipo']}] {evento['descripcion']}",
        },
        usuario_id=usuario_id,
    )
    ejecutar("UPDATE eventos_seguridad_paciente SET hallazgo_id=? WHERE id=?", (hallazgo_id, evento_id))
    return hallazgo_id

