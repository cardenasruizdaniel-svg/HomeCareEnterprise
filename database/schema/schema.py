"""
=========================================================
HomeCare Enterprise
Database Schema
Archivo Principal
Versión: 8.0.0 Enterprise
=========================================================

Este archivo centraliza todos los módulos del esquema
de la base de datos.

Cada dominio funcional define sus propias tablas y este
archivo las unifica para que database.py y migrations.py
puedan construir automáticamente toda la base de datos.

Arquitectura Modular

database/
│
├── schema.py
│
└── schema/
    ├── usuarios.py
    ├── pacientes.py
    ├── profesionales.py
    ├── agenda.py
    ├── despacho.py
    ├── asignaciones.py
    ├── historia_clinica.py
    ├── medicamentos.py
    ├── diagnosticos.py
    ├── inventario.py
    ├── auditoria.py
    └── configuracion.py

=========================================================
"""

# ==========================================================
# IMPORTACIÓN DE MÓDULOS
# ==========================================================

from database.schema.usuarios import USUARIOS

from database.schema.pacientes import PACIENTES

from database.schema.profesionales import PROFESIONALES

from database.schema.agenda import AGENDA

from database.schema.despacho import DESPACHO

from database.schema.asignaciones import ASIGNACIONES


# ==========================================================
# ESQUEMA GENERAL
# ==========================================================

SCHEMA = (

    USUARIOS

    + PACIENTES

    + PROFESIONALES

    + AGENDA

    + DESPACHO

    + ASIGNACIONES

)


# ==========================================================
# INFORMACIÓN
# ==========================================================

SCHEMA_VERSION = "8.0.0"

SCHEMA_NAME = "HomeCare Enterprise"

TOTAL_MODULOS = 6

TOTAL_TABLAS = sum(len(modulo) for modulo in SCHEMA)


# ==========================================================
# UTILIDADES
# ==========================================================

def obtener_schema():

    """
    Retorna todas las sentencias SQL del esquema.
    """

    return SCHEMA


def obtener_version():

    return SCHEMA_VERSION


def obtener_total_tablas():

    return TOTAL_TABLAS


def obtener_modulos():

    return {

        "usuarios": len(USUARIOS),

        "pacientes": len(PACIENTES),

        "profesionales": len(PROFESIONALES),

        "agenda": len(AGENDA),

        "despacho": len(DESPACHO),

        "asignaciones": len(ASIGNACIONES),

    }


def imprimir_resumen():

    print("=" * 60)

    print("HOMECARE ENTERPRISE DATABASE")

    print("=" * 60)

    print(f"Version        : {SCHEMA_VERSION}")

    print(f"Modulos        : {TOTAL_MODULOS}")

    print(f"Tablas SQL     : {TOTAL_TABLAS}")

    print("=" * 60)

    for nombre, total in obtener_modulos().items():

        print(f"{nombre:<20} {total}")

    print("=" * 60)


if __name__ == "__main__":

    imprimir_resumen()