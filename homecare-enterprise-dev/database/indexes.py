"""
=========================================================
HomeCare Enterprise
Índices SQLite
=========================================================
"""

INDEXES = [

"""

CREATE INDEX IF NOT EXISTS idx_usuario
ON usuarios(usuario);

""",

"""

CREATE INDEX IF NOT EXISTS idx_documento
ON pacientes(documento);

""",

"""

CREATE INDEX IF NOT EXISTS idx_nombre
ON pacientes(primer_apellido,
             primer_nombre);

""",

"""

CREATE INDEX IF NOT EXISTS idx_programacion_fecha
ON programaciones(fecha);

""",

"""

CREATE INDEX IF NOT EXISTS idx_auditoria_fecha
ON auditoria(fecha);

"""

]