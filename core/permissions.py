"""
=========================================================
HomeCare IPS Enterprise
Archivo: core/permissions.py
Versión: 7.0.0
=========================================================
"""

from core.roles import *


# =========================================================
# PERMISOS DEL SISTEMA
# =========================================================

PERMISSIONS = {

    # -----------------------------------------------------
    # ADMINISTRADOR
    # -----------------------------------------------------

    ADMIN: {

        "*"

    },

    # -----------------------------------------------------
    # DIRECTOR MÉDICO
    # -----------------------------------------------------

    DIRECTOR: {

        "dashboard",

        "pacientes",

        "historia",

        "diagnosticos",

        "alergias",

        "antecedentes",

        "medicamentos",

        "tratamientos",

        "signos",

        "agenda",

        "profesionales",

        "reportes",

    },

    # -----------------------------------------------------
    # COORDINADOR
    # -----------------------------------------------------

    COORDINADOR: {

        "dashboard",

        "pacientes",

        "agenda",

        "programacion",

        "profesionales",

        "reportes",

    },

    # -----------------------------------------------------
    # MÉDICO
    # -----------------------------------------------------

    MEDICO: {

        "dashboard",

        "pacientes",

        "historia",

        "diagnosticos",

        "antecedentes",

        "alergias",

        "medicamentos",

        "tratamientos",

        "signos",

    },

    # -----------------------------------------------------
    # ENFERMERO
    # -----------------------------------------------------

    ENFERMERO: {

        "dashboard",

        "pacientes",

        "medicamentos",

        "tratamientos",

        "signos",

    },

    # -----------------------------------------------------
    # FISIOTERAPIA
    # -----------------------------------------------------

    FISIOTERAPEUTA: {

        "dashboard",

        "pacientes",

        "tratamientos",

    },

    # -----------------------------------------------------
    # TERAPIA RESPIRATORIA
    # -----------------------------------------------------

    RESPIRATORIO: {

        "dashboard",

        "pacientes",

        "tratamientos",

    },

    # -----------------------------------------------------
    # AUXILIAR
    # -----------------------------------------------------

    AUXILIAR: {

        "dashboard",

        "agenda",

        "pacientes",

    },

    # -----------------------------------------------------
    # FACTURACIÓN
    # -----------------------------------------------------

    FACTURACION: {

        "dashboard",

        "facturacion",

        "reportes",

    },

    # -----------------------------------------------------
    # INVENTARIO
    # -----------------------------------------------------

    INVENTARIO: {

        "dashboard",

        "inventario",

        "medicamentos",

    },

    # -----------------------------------------------------
    # CONSULTA
    # -----------------------------------------------------

    CONSULTA: {

        "dashboard",

    }

}


# =========================================================
# VALIDACIÓN DE PERMISOS
# =========================================================

def tiene_permiso(rol: str, modulo: str) -> bool:
    """
    Valida si un rol puede acceder a un módulo.
    """

    permisos = PERMISSIONS.get(rol, set())

    if "*" in permisos:
        return True

    return modulo in permisos


# =========================================================
# OBTENER PERMISOS
# =========================================================

def obtener_permisos(rol: str):

    return PERMISSIONS.get(rol, set())


# =========================================================
# LISTAR ROLES
# =========================================================

def listar_roles():

    return list(PERMISSIONS.keys())