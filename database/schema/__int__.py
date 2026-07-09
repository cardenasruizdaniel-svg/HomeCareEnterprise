"""
=========================================================
HomeCare Enterprise
Database Schema Package
Archivo: database/schema/__init__.py
Versión: 8.0.0
=========================================================

Este paquete contiene todos los módulos del esquema de
la base de datos de HomeCare Enterprise.

Cada módulo define las tablas correspondientes a un
dominio funcional del sistema.

Ejemplo:

usuarios.py
pacientes.py
profesionales.py
agenda.py
despacho.py
historia_clinica.py
medicamentos.py
diagnosticos.py

El archivo database/schema.py se encargará posteriormente
de unir todos estos módulos para crear el esquema
completo de la base de datos.
"""

__version__ = "8.0.0"

__author__ = "HomeCare Enterprise"

__description__ = (
    "Módulos del esquema de base de datos"
)

# ==========================================================
# IMPORTACIÓN DE MÓDULOS
# ==========================================================

from .usuarios import USUARIOS

from .pacientes import PACIENTES

from .profesionales import PROFESIONALES

from .agenda import AGENDA

from .despacho import DESPACHO

from .asignaciones import ASIGNACIONES

# ==========================================================
# EXPORTACIÓN
# ==========================================================

__all__ = [

    "USUARIOS",

    "PACIENTES",

    "PROFESIONALES",

    "AGENDA",

    "DESPACHO",

    "ASIGNACIONES",

]