"""
=========================================================
HomeCare Enterprise
Catalogos de referencia para el RIPS

IMPORTANTE: los codigos de este archivo corresponden a las
tablas de referencia historicamente publicadas por el
Ministerio de Salud (SISPRO) para el RIPS. Desde la
Resolucion 948 de 2026, estas tablas se publican como
"Documentos Tecnicos" en el micrositio de facturacion
electronica del SISPRO y pueden actualizarse SIN expedir
una nueva resolucion. Antes de transmitir RIPS en
produccion, se debe validar cada catalogo contra la version
vigente publicada en:
https://www.minsalud.gov.co (micrositio FEV-RIPS / SISPRO)
=========================================================
"""

# ==========================================================
# TIPO DE DOCUMENTO DE IDENTIFICACIÓN (tabla TipoIdPISIS)
# ==========================================================

TIPOS_DOCUMENTO = {
    "CC": "Cédula de ciudadanía",
    "TI": "Tarjeta de identidad",
    "CE": "Cédula de extranjería",
    "PA": "Pasaporte",
    "RC": "Registro civil",
    "CD": "Carné diplomático",
    "SC": "Salvoconducto",
    "PE": "Permiso especial de permanencia",
    "PT": "Permiso por protección temporal",
    "CN": "Certificado de nacido vivo",
    "MS": "Menor sin identificación",
    "AS": "Adulto sin identificación",
}

# ==========================================================
# SEXO (campo codSexo)
# ==========================================================

SEXO = {
    "M": "Masculino",
    "F": "Femenino",
}

# ==========================================================
# ZONA TERRITORIAL DE RESIDENCIA (tabla ZonaTerritorial)
# ==========================================================

ZONA_TERRITORIAL = {
    "01": "Urbana",
    "02": "Rural",
}

# ==========================================================
# PAÍS (DIVIPOLA / ISO). Colombia = 170.
# ==========================================================

PAIS_COLOMBIA = "170"

# ==========================================================
# TIPO DE USUARIO (tabla TipoUsuario) - ⚠ VERIFICAR VIGENCIA
# Valores historicamente usados; confirmar contra el
# Documento Tecnico 1 vigente antes de producción.
# ==========================================================

TIPO_USUARIO = {
    "01": "Contributivo cotizante",
    "02": "Contributivo beneficiario",
    "03": "Contributivo adicional",
    "04": "Subsidiado",
    "05": "Vinculado",
    "06": "Particular",
    "07": "Otro",
    "08": "Especial o excepción - afiliado",
    "09": "Especial o excepción - beneficiario",
    "10": "Población pobre no asegurada (PPNA)",
}

# ==========================================================
# FINALIDAD DE LA TECNOLOGÍA EN SALUD (consulta) - ⚠ VERIFICAR
# (tabla RIPSFinalidadConsultaVersion2)
# ==========================================================

FINALIDAD_CONSULTA = {
    "10": "Detección de alteraciones del desarrollo del joven",
    "11": "Detección de alteraciones del embarazo",
    "12": "Detección de alteraciones del adulto",
    "14": "Detección de alteraciones de agudeza visual",
    "15": "Atención de parto",
    "16": "Atención de otras enfermedades generales",
    "17": "Atención de la planificación familiar",
    "18": "No aplica",
}

# ==========================================================
# TIPO DE DIAGNÓSTICO PRINCIPAL - ⚠ VERIFICAR
# ==========================================================

TIPO_DIAGNOSTICO = {
    "01": "Impresión diagnóstica",
    "02": "Confirmado nuevo",
    "03": "Confirmado repetido",
}

# ==========================================================
# CAUSA EXTERNA - ⚠ VERIFICAR
# ==========================================================

CAUSA_EXTERNA = {
    "04": "Otra",
    "05": "Enfermedad general",
    "15": "Común",
}

# ==========================================================
# MODALIDAD DE ATENCIÓN (para servicios de atención
# domiciliaria, propia de una IPS de HomeCare)
# ==========================================================

MODALIDAD_ATENCION_DOMICILIARIA = "04"  # Domiciliaria
