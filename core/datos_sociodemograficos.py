"""
HomeCare Enterprise - Datos sociodemográficos del paciente

Catálogos con las categorías oficiales usadas en los registros
de salud en Colombia (DANE / RIPS / Ministerio de Salud), para
la caracterización diferencial del paciente: discapacidad,
pertenencia étnica, víctima del conflicto armado, estrato,
escolaridad, e identidad de género.
"""

TIPOS_DISCAPACIDAD = [
    "Ninguna",
    "Física / Motora",
    "Visual",
    "Auditiva",
    "Sordoceguera",
    "Intelectual / Cognitiva",
    "Psicosocial / Mental",
    "Múltiple",
    "Otra",
]

GRUPOS_ETNICOS = [
    "Ninguno de los anteriores",
    "Indígena",
    "Rom (Gitano)",
    "Raizal del Archipiélago de San Andrés, Providencia y Santa Catalina",
    "Palenquero de San Basilio",
    "Negro, mulato, afrocolombiano o afrodescendiente",
]

NIVELES_ESCOLARIDAD = [
    "Ninguna",
    "Preescolar",
    "Básica primaria",
    "Básica secundaria",
    "Media (bachillerato)",
    "Técnica",
    "Tecnológica",
    "Universitaria",
    "Posgrado",
]

# Identidad de género -- categorías usadas en los registros de
# salud colombianos para reconocer la identidad de género de la
# persona, más allá del sexo biológico registrado.
IDENTIDADES_GENERO = [
    "Mujer cisgénero",
    "Hombre cisgénero",
    "Mujer trans",
    "Hombre trans",
    "No binario",
    "Prefiere no reportar",
]

ESTRATOS_SOCIOECONOMICOS = [1, 2, 3, 4, 5, 6]
