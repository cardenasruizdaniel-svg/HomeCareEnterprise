from dataclasses import dataclass
from typing import Optional


TABLA_ADMINISTRACION_MEDICAMENTOS = """
CREATE TABLE IF NOT EXISTS administracion_medicamentos (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    medicamento_id INTEGER NOT NULL,

    paciente_id INTEGER NOT NULL,

    profesional TEXT,

    fecha DATE,

    hora TIME,

    dosis TEXT,

    via TEXT,

    observaciones TEXT,

    estado TEXT DEFAULT 'Administrado',

    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (medicamento_id)
        REFERENCES medicamentos(id)
        ON DELETE CASCADE,

    FOREIGN KEY (paciente_id)
        REFERENCES pacientes(id)
        ON DELETE CASCADE
);
"""


@dataclass
class AdministracionMedicamento:

    id: Optional[int] = None

    medicamento_id: int = 0

    paciente_id: int = 0

    profesional: str = ""

    fecha: str = ""

    hora: str = ""

    dosis: str = ""

    via: str = ""

    observaciones: str = ""

    estado: str = "Administrado"

    fecha_registro: str = ""