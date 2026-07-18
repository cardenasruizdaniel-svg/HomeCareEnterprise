"""
=========================================================
HomeCare Enterprise
Database Schema
Módulo: Agenda Clínica Inteligente
Versión: 8.0.0
=========================================================
"""

AGENDA = [

"""
CREATE TABLE IF NOT EXISTS programaciones(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    uuid TEXT UNIQUE,

    paciente_id INTEGER NOT NULL,

    profesional_id INTEGER,

    servicio TEXT NOT NULL,

    procedimiento TEXT,

    prioridad TEXT DEFAULT 'MEDIA',

    estado TEXT DEFAULT 'PROGRAMADA',

    fecha TEXT NOT NULL,

    hora_inicio TEXT NOT NULL,

    hora_fin TEXT NOT NULL,

    duracion INTEGER DEFAULT 60,

    direccion TEXT,

    barrio TEXT,

    municipio TEXT,

    departamento TEXT,

    latitud REAL,

    longitud REAL,

    observaciones TEXT,

    usuario_creacion INTEGER,

    usuario_actualizacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    fecha_actualizacion TEXT,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
""",

"""
CREATE TABLE IF NOT EXISTS agenda_bloqueos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    profesional_id INTEGER NOT NULL,

    fecha TEXT NOT NULL,

    hora_inicio TEXT NOT NULL,

    hora_fin TEXT NOT NULL,

    motivo TEXT,

    tipo TEXT,

    usuario_id INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
""",

"""
CREATE TABLE IF NOT EXISTS agenda_reprogramaciones(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    programacion_id INTEGER NOT NULL,

    fecha_anterior TEXT,

    hora_anterior TEXT,

    fecha_nueva TEXT,

    hora_nueva TEXT,

    motivo TEXT,

    usuario_id INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(programacion_id)
        REFERENCES programaciones(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS agenda_cancelaciones(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    programacion_id INTEGER NOT NULL,

    motivo TEXT,

    usuario_id INTEGER,

    fecha_cancelacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(programacion_id)
        REFERENCES programaciones(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS agenda_historial(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    programacion_id INTEGER NOT NULL,

    estado_anterior TEXT,

    estado_nuevo TEXT,

    descripcion TEXT,

    usuario_id INTEGER,

    fecha_evento TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(programacion_id)
        REFERENCES programaciones(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS agenda_disponibilidad(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    profesional_id INTEGER NOT NULL,

    fecha TEXT NOT NULL,

    hora_inicio TEXT NOT NULL,

    hora_fin TEXT NOT NULL,

    disponible INTEGER DEFAULT 1,

    motivo TEXT,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)
        ON DELETE CASCADE

);
"""

]