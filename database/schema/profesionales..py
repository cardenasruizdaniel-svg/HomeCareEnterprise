"""
=========================================================
HomeCare Enterprise
Database Schema
Módulo: Profesionales
Versión: 8.0.0
=========================================================
"""

PROFESIONALES = [

"""
CREATE TABLE IF NOT EXISTS profesionales(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    uuid TEXT UNIQUE,

    tipo_documento TEXT,

    documento TEXT UNIQUE NOT NULL,

    primer_nombre TEXT NOT NULL,

    segundo_nombre TEXT,

    primer_apellido TEXT NOT NULL,

    segundo_apellido TEXT,

    nombre_completo TEXT,

    registro_profesional TEXT,

    profesion TEXT,

    especialidad_principal TEXT,

    telefono TEXT,

    celular TEXT,

    correo TEXT,

    direccion TEXT,

    municipio TEXT,

    departamento TEXT,

    latitud REAL,

    longitud REAL,

    estado TEXT DEFAULT 'ACTIVO',

    disponible INTEGER DEFAULT 1,

    acepta_urgencias INTEGER DEFAULT 1,

    capacidad_diaria INTEGER DEFAULT 20,

    tiempo_promedio_visita INTEGER DEFAULT 60,

    radio_cobertura_km REAL DEFAULT 30,

    observaciones TEXT,

    usuario_creacion INTEGER,

    usuario_actualizacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    fecha_actualizacion TEXT,

    FOREIGN KEY(usuario_creacion)
        REFERENCES usuarios(id),

    FOREIGN KEY(usuario_actualizacion)
        REFERENCES usuarios(id)

);
""",

"""
CREATE TABLE IF NOT EXISTS profesionales_especialidades(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    profesional_id INTEGER NOT NULL,

    especialidad TEXT NOT NULL,

    principal INTEGER DEFAULT 0,

    activa INTEGER DEFAULT 1,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS profesionales_disponibilidad(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    profesional_id INTEGER NOT NULL,

    dia_semana INTEGER NOT NULL,

    hora_inicio TEXT NOT NULL,

    hora_fin TEXT NOT NULL,

    activo INTEGER DEFAULT 1,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS profesionales_zonas(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    profesional_id INTEGER NOT NULL,

    departamento TEXT,

    municipio TEXT,

    barrio TEXT,

    zona TEXT,

    prioridad INTEGER DEFAULT 1,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS profesionales_ubicacion(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    profesional_id INTEGER NOT NULL,

    latitud REAL,

    longitud REAL,

    velocidad REAL,

    precision_gps REAL,

    fecha_actualizacion TEXT,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS profesionales_vehiculos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    profesional_id INTEGER NOT NULL,

    tipo TEXT,

    placa TEXT,

    marca TEXT,

    modelo TEXT,

    capacidad TEXT,

    activo INTEGER DEFAULT 1,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)
        ON DELETE CASCADE

);
"""

]