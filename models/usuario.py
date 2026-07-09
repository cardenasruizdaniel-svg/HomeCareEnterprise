TABLA_USUARIOS = """
CREATE TABLE IF NOT EXISTS usuarios(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL,

    usuario TEXT NOT NULL UNIQUE,

    password TEXT NOT NULL,

    rol TEXT NOT NULL,

    correo TEXT,

    telefono TEXT,

    estado TEXT DEFAULT 'Activo',

    ultimo_acceso TEXT,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP

)
"""