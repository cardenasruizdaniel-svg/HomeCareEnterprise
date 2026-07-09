TABLA_CIE10 = """
CREATE TABLE IF NOT EXISTS cie10 (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    codigo TEXT NOT NULL UNIQUE,

    descripcion TEXT NOT NULL,

    categoria TEXT,

    capitulo TEXT,

    activo INTEGER DEFAULT 1

)
"""