"""
=========================================================
HomeCare Enterprise
Database Schema
Modulo: Pacientes
Versión: 8.0.0
=========================================================
"""

PACIENTES = [

"""
CREATE TABLE IF NOT EXISTS pacientes(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    uuid TEXT UNIQUE,

    tipo_documento TEXT NOT NULL,

    documento TEXT UNIQUE NOT NULL,

    primer_nombre TEXT NOT NULL,

    segundo_nombre TEXT,

    primer_apellido TEXT NOT NULL,

    segundo_apellido TEXT,

    nombre_completo TEXT,

    fecha_nacimiento TEXT,

    edad INTEGER,

    sexo TEXT,

    estado_civil TEXT,

    grupo_sanguineo TEXT,

    factor_rh TEXT,

    eps TEXT,

    regimen TEXT,

    nivel_sisben TEXT,

    afiliacion_activa INTEGER DEFAULT 1,

    telefono TEXT,

    celular TEXT,

    correo TEXT,

    direccion TEXT,

    barrio TEXT,

    municipio TEXT,

    departamento TEXT,

    codigo_postal TEXT,

    latitud REAL,

    longitud REAL,

    zona TEXT,

    estrato INTEGER,

    referencia_direccion TEXT,

    riesgo_clinico TEXT DEFAULT 'MEDIO',

    prioridad_domiciliaria TEXT DEFAULT 'MEDIA',

    dependencia INTEGER DEFAULT 0,

    oxigeno INTEGER DEFAULT 0,

    ventilacion INTEGER DEFAULT 0,

    aislamiento INTEGER DEFAULT 0,

    alergias TEXT,

    diagnostico_principal TEXT,

    observaciones TEXT,

    estado TEXT DEFAULT 'ACTIVO',

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
CREATE TABLE IF NOT EXISTS acudientes(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    nombre TEXT NOT NULL,

    parentesco TEXT,

    telefono TEXT,

    celular TEXT,

    correo TEXT,

    direccion TEXT,

    principal INTEGER DEFAULT 0,

    observaciones TEXT,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS contactos_emergencia(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    nombre TEXT,

    parentesco TEXT,

    telefono TEXT,

    celular TEXT,

    prioridad INTEGER DEFAULT 1,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS pacientes_geografia(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    latitud REAL,

    longitud REAL,

    precision_gps REAL,

    ultima_actualizacion TEXT,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)
        ON DELETE CASCADE

);
""",

"""
CREATE TABLE IF NOT EXISTS pacientes_alertas(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    tipo TEXT,

    descripcion TEXT,

    prioridad TEXT,

    activa INTEGER DEFAULT 1,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)
        ON DELETE CASCADE

);
"""

]