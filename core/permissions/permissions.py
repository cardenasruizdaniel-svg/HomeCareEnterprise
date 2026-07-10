"""
HomeCare Enterprise - Permisos por rol

Parametrización según los perfiles reales de la IPS:

- Administrador: acceso total.
- Médicos: todo el proceso médico (historia, órdenes,
  medicamentos, agenda) y son quienes asignan el programa de
  atención y los servicios que va a recibir el paciente.
- Enfermeros y Cuidadores: pueden hacer notas en el paciente
  (evoluciones, signos vitales, medicamentos administrados) y
  crear sus propios documentos/plantillas de nota.
- Profesionales de terapias (fisioterapia, respiratoria,
  psicología, ocupacional, nutrición): manejan todo el tema
  del paciente -- autorizaciones, órdenes, notas, registros en
  la historia clínica, y revisión de laboratorios.
- Administrativos: creación del paciente y agendamiento de
  visitas.
"""

PERMISSIONS = {

    "Administrador": ["*"],
    "Director Médico": ["*"],

    "Coordinador": [
        "pacientes", "programacion", "ordenes", "medicamentos", "catalogos",
        "profesionales", "usuarios", "interoperabilidad", "rips",
        "nomina", "cargos", "facturacion", "inventario", "calidad",
    ],

    # -----------------------------------------------
    # MÉDICOS: todo el proceso médico + asignan el
    # programa de atención y los servicios del paciente
    # -----------------------------------------------
    "Médico": ["pacientes", "programacion", "ordenes", "medicamentos", "catalogos"],
    "Medico": ["pacientes", "programacion", "ordenes", "medicamentos", "catalogos"],

    # -----------------------------------------------
    # ENFERMEROS Y CUIDADORES: notas en el paciente y
    # sus propios documentos/plantillas
    # -----------------------------------------------
    "Enfermero": ["pacientes", "programacion", "medicamentos"],
    "Enfermeria": ["pacientes", "programacion", "medicamentos"],
    "Cuidador": ["pacientes", "programacion"],

    # -----------------------------------------------
    # PROFESIONALES DE TERAPIAS: todo el tema del
    # paciente -- autorizaciones, ordenes, notas,
    # historia clinica, laboratorios
    # -----------------------------------------------
    "Fisioterapeuta": ["pacientes", "programacion", "ordenes", "catalogos"],
    "Terapeuta Respiratorio": ["pacientes", "programacion", "ordenes", "catalogos"],
    "Psicólogo": ["pacientes", "programacion", "ordenes", "catalogos"],
    "Psicologo": ["pacientes", "programacion", "ordenes", "catalogos"],
    "Salud Ocupacional": ["pacientes", "programacion", "ordenes", "catalogos"],
    "Terapeuta": ["pacientes", "programacion", "ordenes", "catalogos"],
    "Nutricionista": ["pacientes", "programacion", "ordenes", "catalogos"],

    # -----------------------------------------------
    # ADMINISTRATIVOS: creación del paciente y
    # agendamiento de visitas
    # -----------------------------------------------
    "Administrativo": ["pacientes", "programacion", "calidad"],
    "Auxiliar": ["pacientes", "programacion"],

    "Auditor": ["auditoria", "reportes"],
    "Facturación": ["facturacion", "rips", "catalogos"],
    "Facturacion": ["facturacion", "rips", "catalogos"],
    "Inventario": ["inventario"],
    "Consulta": ["pacientes"],

}


def has_permission(role: str, module: str) -> bool:
    perms = PERMISSIONS.get(role, [])
    return "*" in perms or module in perms


# ==========================================================
# COMPATIBILIDAD CON VERSIONES ANTERIORES
# ==========================================================

def tiene_permiso(rol: str, modulo: str) -> bool:
    """
    Alias para mantener compatibilidad con el código existente.
    """
    return has_permission(rol, modulo)
