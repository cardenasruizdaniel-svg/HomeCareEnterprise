TABLA_ANTECEDENTES = """
CREATE TABLE IF NOT EXISTS antecedentes (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    tipo TEXT NOT NULL,

    descripcion TEXT NOT NULL,

    observaciones TEXT,

    activo INTEGER DEFAULT 1,

    usuario_creacion TEXT,

    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

    usuario_actualizacion TEXT,

    fecha_actualizacion DATETIME,

    FOREIGN KEY (paciente_id)
        REFERENCES pacientes(id)

)
"""