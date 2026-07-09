"""
=========================================================
HomeCare IPS Enterprise
Archivo: models/programacion.py
Versión: 6.0.1
=========================================================
"""

TABLA_PROGRAMACIONES = """
CREATE TABLE IF NOT EXISTS programacion(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    profesional_id INTEGER NOT NULL,
    servicio TEXT,
    fecha DATE,
    hora TIME,
    duracion INTEGER,
    estado TEXT DEFAULT 'Programada',
    direccion TEXT,
    latitud REAL,
    longitud REAL,
    observaciones TEXT,
    firma_paciente TEXT,
    firma_profesional TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Alias para mantener compatibilidad con código antiguo
TABLA_PROGRAMACION = TABLA_PROGRAMACIONES