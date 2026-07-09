"""
=========================================================
HomeCare Enterprise
Database Schema
Modulo: Usuarios
Versión: 8.0.0
=========================================================
"""

USUARIOS = [

"""
CREATE TABLE IF NOT EXISTS usuarios(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    uuid TEXT UNIQUE,

    usuario TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL,

    nombre TEXT NOT NULL,

    apellido TEXT,

    documento TEXT,

    correo TEXT UNIQUE,

    telefono TEXT,

    cargo TEXT,

    rol TEXT NOT NULL,

    activo INTEGER DEFAULT 1,

    requiere_cambio_password INTEGER DEFAULT 0,

    doble_factor INTEGER DEFAULT 0,

    ultimo_login TEXT,

    ultimo_ip TEXT,

    intentos_fallidos INTEGER DEFAULT 0,

    bloqueado INTEGER DEFAULT 0,

    fecha_bloqueo TEXT,

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
CREATE TABLE IF NOT EXISTS sesiones(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    usuario_id INTEGER NOT NULL,

    token TEXT UNIQUE,

    ip TEXT,

    navegador TEXT,

    sistema_operativo TEXT,

    dispositivo TEXT,

    fecha_inicio TEXT,

    fecha_expiracion TEXT,

    fecha_cierre TEXT,

    activa INTEGER DEFAULT 1,

    FOREIGN KEY(usuario_id)
        REFERENCES usuarios(id)

);
""",

"""
CREATE TABLE IF NOT EXISTS permisos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    codigo TEXT UNIQUE,

    nombre TEXT,

    descripcion TEXT,

    categoria TEXT,

    activo INTEGER DEFAULT 1

);
""",

"""
CREATE TABLE IF NOT EXISTS roles_permisos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    rol TEXT,

    permiso_id INTEGER,

    FOREIGN KEY(permiso_id)
        REFERENCES permisos(id)

);
""",

"""
CREATE TABLE IF NOT EXISTS usuarios_permisos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    usuario_id INTEGER,

    permiso_id INTEGER,

    permitido INTEGER DEFAULT 1,

    FOREIGN KEY(usuario_id)
        REFERENCES usuarios(id),

    FOREIGN KEY(permiso_id)
        REFERENCES permisos(id)

);
"""

]