"""
==============================================================
HomeCare Enterprise
Motor Inteligente de Asignación
Archivo: core/dispatcher/__init__.py
==============================================================

Este paquete contiene el motor de decisión encargado de
asignar automáticamente las visitas domiciliarias.

Componentes:

- reglas.py
- disponibilidad.py
- prioridades.py
- excepciones.py
- asignador.py
- optimizador.py

Autor:
HomeCare Enterprise

Versión:
Sprint 3.4
"""

from .reglas import ReglasAsignacion
from .disponibilidad import DisponibilidadProfesional
from .prioridades import PrioridadPaciente
from .asignador import MotorAsignacion
from .optimizador import OptimizadorRutas

__all__ = [

    "ReglasAsignacion",

    "DisponibilidadProfesional",

    "PrioridadPaciente",

    "MotorAsignacion",

    "OptimizadorRutas",

]

VERSION = "3.4.0"

ENGINE = "HomeCare Smart Dispatcher"

AUTHOR = "HomeCare Enterprise"

DESCRIPTION = (
    "Motor Inteligente de Asignación "
    "de Visitas Domiciliarias"
)