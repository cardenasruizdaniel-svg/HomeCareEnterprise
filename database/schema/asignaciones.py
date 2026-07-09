"""
=========================================================
HomeCare Enterprise
Database Schema
Módulo: Motor Inteligente de Asignación
Versión: 8.0.0
=========================================================
"""

ASIGNACIONES = [

"""
CREATE TABLE IF NOT EXISTS asignaciones(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    uuid TEXT UNIQUE,

    programacion_id INTEGER NOT NULL,

    paciente_id INTEGER NOT NULL,

    profesional_id INTEGER NOT NULL,

    despacho_id INTEGER,

    prioridad TEXT DEFAULT 'MEDIA',

    puntaje REAL DEFAULT 0,

    algoritmo TEXT DEFAULT 'SMART_DISPATCH',

    version_motor TEXT DEFAULT '8.0',

    estado TEXT DEFAULT 'ASIGNADA',

    orden_ruta INTEGER DEFAULT 0,

    distancia_km REAL DEFAULT 0,

    tiempo_estimado INTEGER DEFAULT 0,

    tiempo_real INTEGER DEFAULT 0,

    motivo_asignacion TEXT,

    observaciones TEXT,

    usuario_creacion INTEGER,

    usuario_actualizacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    fecha_actualizacion TEXT,

    FOREIGN KEY(programacion_id)
        REFERENCES programaciones(id),

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id),

    FOREIGN KEY(despacho_id)
        REFERENCES despachos(id)

);
""",

"""
CREATE TABLE IF NOT EXISTS asignacion_reglas(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    asignacion_id INTEGER NOT NULL,

    regla TEXT NOT NULL,

    descripcion TEXT,

    valor REAL,

    aprobado INTEGER DEFAULT 1,

    fecha_evaluacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(asignacion_id)
        REFERENCES asignaciones(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS asignacion_candidatos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    asignacion_id INTEGER NOT NULL,

    profesional_id INTEGER NOT NULL,

    puntaje REAL,

    posicion INTEGER,

    seleccionado INTEGER DEFAULT 0,

    motivo TEXT,

    FOREIGN KEY(asignacion_id)
        REFERENCES asignaciones(id)
        ON DELETE CASCADE,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
""",

"""
CREATE TABLE IF NOT EXISTS asignacion_historial(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    asignacion_id INTEGER NOT NULL,

    estado_anterior TEXT,

    estado_nuevo TEXT,

    usuario_id INTEGER,

    observaciones TEXT,

    fecha_evento TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(asignacion_id)
        REFERENCES asignaciones(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS asignacion_metricas(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    asignacion_id INTEGER NOT NULL,

    distancia_calculada REAL,

    tiempo_estimado INTEGER,

    carga_profesional INTEGER,

    prioridad_clinica TEXT,

    prioridad_logistica TEXT,

    tiempo_respuesta INTEGER,

    eficiencia REAL,

    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(asignacion_id)
        REFERENCES asignaciones(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS asignacion_rechazos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    asignacion_id INTEGER NOT NULL,

    profesional_id INTEGER,

    motivo TEXT,

    tipo TEXT,

    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(asignacion_id)
        REFERENCES asignaciones(id)
        ON DELETE CASCADE,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
"""

]