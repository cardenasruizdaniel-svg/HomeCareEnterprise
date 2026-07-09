"""
==============================================================
HomeCare Enterprise
Motor Inteligente de Asignación
Archivo: core/dispatcher/excepciones.py
==============================================================
"""

from __future__ import annotations


class DispatcherException(Exception):
    """
    Excepción base del Motor Inteligente de Asignación.
    """

    codigo = "DISPATCHER_ERROR"

    def __init__(self, mensaje: str = "Error del motor de asignación"):

        self.mensaje = mensaje

        super().__init__(mensaje)


# ==========================================================
# PROFESIONAL
# ==========================================================

class ProfesionalNoEncontrado(DispatcherException):

    codigo = "PROFESIONAL_NO_ENCONTRADO"


class ProfesionalInactivo(DispatcherException):

    codigo = "PROFESIONAL_INACTIVO"


class ProfesionalNoDisponible(DispatcherException):

    codigo = "PROFESIONAL_NO_DISPONIBLE"


class ProfesionalSinEspecialidad(DispatcherException):

    codigo = "PROFESIONAL_SIN_ESPECIALIDAD"


class JornadaExcedida(DispatcherException):

    codigo = "JORNADA_EXCEDIDA"


# ==========================================================
# AGENDA
# ==========================================================

class ConflictoHorario(DispatcherException):

    codigo = "CONFLICTO_HORARIO"


class AgendaNoDisponible(DispatcherException):

    codigo = "AGENDA_NO_DISPONIBLE"


class HorarioInvalido(DispatcherException):

    codigo = "HORARIO_INVALIDO"


# ==========================================================
# UBICACIÓN
# ==========================================================

class MunicipioNoCompatible(DispatcherException):

    codigo = "MUNICIPIO_NO_COMPATIBLE"


class ZonaNoCompatible(DispatcherException):

    codigo = "ZONA_NO_COMPATIBLE"


class DistanciaExcedida(DispatcherException):

    codigo = "DISTANCIA_EXCEDIDA"


# ==========================================================
# VISITAS
# ==========================================================

class VisitaNoEncontrada(DispatcherException):

    codigo = "VISITA_NO_ENCONTRADA"


class VisitaYaAsignada(DispatcherException):

    codigo = "VISITA_YA_ASIGNADA"


class PrioridadInvalida(DispatcherException):

    codigo = "PRIORIDAD_INVALIDA"


# ==========================================================
# MOTOR
# ==========================================================

class NoExisteProfesionalDisponible(DispatcherException):

    codigo = "SIN_PROFESIONALES"


class ErrorOptimizacion(DispatcherException):

    codigo = "ERROR_OPTIMIZACION"


class ErrorAsignacion(DispatcherException):

    codigo = "ERROR_ASIGNACION"


# ==========================================================
# UTILIDAD
# ==========================================================

EXCEPCIONES_CONTROLADAS = (

    ProfesionalNoEncontrado,

    ProfesionalInactivo,

    ProfesionalNoDisponible,

    ProfesionalSinEspecialidad,

    JornadaExcedida,

    ConflictoHorario,

    AgendaNoDisponible,

    HorarioInvalido,

    MunicipioNoCompatible,

    ZonaNoCompatible,

    DistanciaExcedida,

    VisitaNoEncontrada,

    VisitaYaAsignada,

    PrioridadInvalida,

    NoExisteProfesionalDisponible,

    ErrorOptimizacion,

    ErrorAsignacion,

)