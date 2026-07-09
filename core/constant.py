"""
=========================================================
HomeCare IPS Enterprise
Constantes Globales del Sistema
=========================================================
"""

# =========================================================
# ESTADOS GENERALES
# =========================================================

ESTADO_ACTIVO = "Activo"
ESTADO_INACTIVO = "Inactivo"
ESTADO_SUSPENDIDO = "Suspendido"
ESTADO_FINALIZADO = "Finalizado"
ESTADO_ANULADO = "Anulado"

ESTADOS = [

    ESTADO_ACTIVO,

    ESTADO_INACTIVO,

    ESTADO_SUSPENDIDO,

    ESTADO_FINALIZADO,

    ESTADO_ANULADO

]

# =========================================================
# SEXO
# =========================================================

SEXO_MASCULINO = "Masculino"
SEXO_FEMENINO = "Femenino"
SEXO_OTRO = "Otro"

SEXOS = [

    SEXO_MASCULINO,

    SEXO_FEMENINO,

    SEXO_OTRO

]

# =========================================================
# TIPOS DE DOCUMENTO
# =========================================================

TIPOS_DOCUMENTO = [

    "CC",

    "TI",

    "CE",

    "RC",

    "PA",

    "PEP",

    "NIT"

]

# =========================================================
# REGÍMENES
# =========================================================

REGIMENES = [

    "Contributivo",

    "Subsidiado",

    "Particular",

    "Especial",

    "Medicina Prepagada"

]

# =========================================================
# ROLES
# =========================================================

ROL_ADMIN = "Administrador"
ROL_COORDINADOR = "Coordinador"
ROL_MEDICO = "Médico"
ROL_ENFERMERO = "Enfermero"
ROL_AUXILIAR = "Auxiliar"
ROL_FISIOTERAPEUTA = "Fisioterapeuta"
ROL_PSICOLOGO = "Psicólogo"
ROL_TRABAJO_SOCIAL = "Trabajo Social"
ROL_NUTRICIONISTA = "Nutricionista"
ROL_AUDITOR = "Auditor"
ROL_FACTURACION = "Facturación"

ROLES = [

    ROL_ADMIN,

    ROL_COORDINADOR,

    ROL_MEDICO,

    ROL_ENFERMERO,

    ROL_AUXILIAR,

    ROL_FISIOTERAPEUTA,

    ROL_PSICOLOGO,

    ROL_TRABAJO_SOCIAL,

    ROL_NUTRICIONISTA,

    ROL_AUDITOR,

    ROL_FACTURACION

]

# =========================================================
# ESPECIALIDADES
# =========================================================

ESPECIALIDADES = [

    "Medicina General",

    "Enfermería",

    "Auxiliar de Enfermería",

    "Fisioterapia",

    "Terapia Respiratoria",

    "Terapia Ocupacional",

    "Fonoaudiología",

    "Psicología",

    "Nutrición",

    "Trabajo Social"

]

# =========================================================
# PROGRAMACIÓN
# =========================================================

ESTADOS_PROGRAMACION = [

    "Programada",

    "En Curso",

    "Completada",

    "Cancelada",

    "No Programada",

    "Bloqueada",

    "Rechazada"

]

# =========================================================
# MEDICAMENTOS
# =========================================================

ESTADOS_MEDICAMENTO = [

    "Activo",

    "Suspendido",

    "Finalizado"

]

# =========================================================
# SIGNOS VITALES
# =========================================================

ESCALA_DOLOR = list(range(11))

# =========================================================
# PRIORIDADES
# =========================================================

PRIORIDADES = [

    "Baja",

    "Media",

    "Alta",

    "Urgente"

]

# =========================================================
# TIPOS DE VISITA
# =========================================================

TIPOS_VISITA = [

    "Primera Vez",

    "Control",

    "Urgencia",

    "Procedimiento",

    "Seguimiento"

]

# =========================================================
# VÍAS DE ADMINISTRACIÓN
# =========================================================

VIAS_ADMINISTRACION = [

    "Oral",

    "Intravenosa",

    "Intramuscular",

    "Subcutánea",

    "Tópica",

    "Inhalatoria",

    "Rectal",

    "Oftálmica",

    "Ótica",

    "Nasal"

]

# =========================================================
# FRECUENCIAS
# =========================================================

FRECUENCIAS = [

    "Cada 24 horas",

    "Cada 12 horas",

    "Cada 8 horas",

    "Cada 6 horas",

    "Cada 4 horas",

    "Según necesidad"

]

# =========================================================
# DÍAS DE LA SEMANA
# =========================================================

DIAS_SEMANA = [

    "Lunes",

    "Martes",

    "Miércoles",

    "Jueves",

    "Viernes",

    "Sábado",

    "Domingo"

]