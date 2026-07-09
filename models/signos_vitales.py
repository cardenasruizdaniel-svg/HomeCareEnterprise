from dataclasses import dataclass
from typing import Optional


@dataclass
class SignoVital:

    id: Optional[int] = None

    paciente_id: int = 0

    profesional: str = ""

    fecha: str = ""

    hora: str = ""

    temperatura: float = 0.0

    presion_sistolica: int = 0

    presion_diastolica: int = 0

    frecuencia_cardiaca: int = 0

    frecuencia_respiratoria: int = 0

    saturacion_oxigeno: int = 0

    glucemia: float = 0.0

    peso: float = 0.0

    talla: float = 0.0

    imc: float = 0.0

    dolor: int = 0

    observaciones: str = ""

    usuario_creacion: str = ""

    fecha_creacion: str = ""

    fecha_actualizacion: str = ""

TABLA_SIGNOS_VITALES = """

CREATE TABLE IF NOT EXISTS signos_vitales(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    profesional TEXT,

    fecha TEXT NOT NULL,

    hora TEXT NOT NULL,

    temperatura REAL,

    presion_sistolica INTEGER,

    presion_diastolica INTEGER,

    frecuencia_cardiaca INTEGER,

    frecuencia_respiratoria INTEGER,

    saturacion_oxigeno INTEGER,

    glucemia REAL,

    peso REAL,

    talla REAL,

    imc REAL,

    dolor INTEGER,

    observaciones TEXT,

    usuario_creacion TEXT,

    fecha_creacion TEXT,

    fecha_actualizacion TEXT,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)
        ON DELETE CASCADE

)

"""


INDICE_SIGNOS_VITALES = """

CREATE INDEX IF NOT EXISTS idx_signos_paciente

ON signos_vitales(paciente_id);

"""