TABLA_ACUDIENTES = """
CREATE TABLE IF NOT EXISTS acudientes(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    nombre TEXT NOT NULL,

    tipo_documento TEXT,

    documento TEXT,

    parentesco TEXT NOT NULL,

    telefono_principal TEXT NOT NULL,

    telefono_secundario TEXT,

    correo TEXT,

    direccion TEXT,

    barrio TEXT,

    municipio TEXT,

    departamento TEXT,

    ciudad TEXT,

    ocupacion TEXT,

    observaciones TEXT,

    es_principal INTEGER DEFAULT 1,

    autoriza_decisiones INTEGER DEFAULT 0,

    recibe_informacion INTEGER DEFAULT 1,

    estado TEXT DEFAULT 'Activo',

    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,

    fecha_actualizacion TEXT,

    FOREIGN KEY(paciente_id)

        REFERENCES pacientes(id)

        ON DELETE CASCADE

)
"""