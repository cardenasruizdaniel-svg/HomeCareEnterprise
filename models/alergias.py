"""
=========================================================
HomeCare IPS Enterprise
Archivo: models/alergias.py
=========================================================
"""

TABLA_ALERGIAS = """
CREATE TABLE IF NOT EXISTS alergias (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    tipo TEXT,

    alergeno TEXT,

    reaccion TEXT,

    severidad TEXT,

    observaciones TEXT,

    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (paciente_id)
        REFERENCES pacientes(id)
);
"""