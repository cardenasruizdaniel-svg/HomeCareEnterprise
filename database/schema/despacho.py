"""
=========================================================
HomeCare Enterprise
Database Schema
Módulo: Centro de Despacho Inteligente
Versión: 8.0.0
=========================================================
"""

DESPACHO = [

"""
CREATE TABLE IF NOT EXISTS despachos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    uuid TEXT UNIQUE,

    programacion_id INTEGER NOT NULL,

    paciente_id INTEGER NOT NULL,

    profesional_id INTEGER NOT NULL,

    fecha TEXT NOT NULL,

    hora_salida TEXT,

    hora_llegada TEXT,

    hora_inicio TEXT,

    hora_finalizacion TEXT,

    estado TEXT DEFAULT 'PENDIENTE',

    prioridad TEXT DEFAULT 'MEDIA',

    orden_ruta INTEGER DEFAULT 0,

    distancia_estimada REAL DEFAULT 0,

    distancia_real REAL DEFAULT 0,

    tiempo_estimado INTEGER DEFAULT 0,

    tiempo_real INTEGER DEFAULT 0,

    latitud_salida REAL,

    longitud_salida REAL,

    latitud_llegada REAL,

    longitud_llegada REAL,

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
        REFERENCES profesionales(id)

);
""",

"""
CREATE TABLE IF NOT EXISTS despacho_eventos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    despacho_id INTEGER NOT NULL,

    tipo_evento TEXT NOT NULL,

    descripcion TEXT,

    latitud REAL,

    longitud REAL,

    precision_gps REAL,

    velocidad REAL,

    usuario_id INTEGER,

    fecha_evento TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(despacho_id)
        REFERENCES despachos(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS despacho_incidencias(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    despacho_id INTEGER NOT NULL,

    categoria TEXT,

    prioridad TEXT,

    descripcion TEXT,

    solucion TEXT,

    estado TEXT DEFAULT 'ABIERTA',

    usuario_id INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    fecha_cierre TEXT,

    FOREIGN KEY(despacho_id)
        REFERENCES despachos(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS despacho_confirmaciones(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    despacho_id INTEGER NOT NULL,

    confirmado INTEGER DEFAULT 0,

    fecha_confirmacion TEXT,

    nombre_contacto TEXT,

    observaciones TEXT,

    FOREIGN KEY(despacho_id)
        REFERENCES despachos(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS despacho_rutas(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    profesional_id INTEGER NOT NULL,

    fecha TEXT NOT NULL,

    distancia_total REAL,

    tiempo_total INTEGER,

    visitas_programadas INTEGER,

    visitas_realizadas INTEGER DEFAULT 0,

    estado TEXT DEFAULT 'PENDIENTE',

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
""",

"""
CREATE TABLE IF NOT EXISTS despacho_gps(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    despacho_id INTEGER NOT NULL,

    latitud REAL,

    longitud REAL,

    velocidad REAL,

    rumbo REAL,

    precision_gps REAL,

    bateria INTEGER,

    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(despacho_id)
        REFERENCES despachos(id)
        ON DELETE CASCADE

);
"""

]