"""
==============================================================
HomeCare Enterprise
Motor Inteligente de Asignación
Archivo: core/dispatcher/reglas.py
==============================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass(slots=True)
class ResultadoRegla:
    valido: bool
    motivo: str = ""
    prioridad: int = 0


class ReglasAsignacion:
    """
    Reglas de negocio para determinar si un profesional
    puede recibir una nueva visita domiciliaria.
    """

    MAX_VISITAS_DIA = 20
    MAX_HORAS_JORNADA = 12
    MAX_DISTANCIA_KM = 30

    # =====================================================
    # REGLA 1
    # =====================================================

    @staticmethod
    def profesional_activo(profesional: dict) -> ResultadoRegla:

        if not profesional:
            return ResultadoRegla(False, "Profesional inexistente")

        if not profesional.get("activo", False):
            return ResultadoRegla(False, "Profesional inactivo")

        return ResultadoRegla(True)

    # =====================================================
    # REGLA 2
    # =====================================================

    @staticmethod
    def especialidad_valida(
        profesional: dict,
        servicio: str,
    ) -> ResultadoRegla:

        especialidades = profesional.get(
            "especialidades",
            [],
        )

        if servicio not in especialidades:

            return ResultadoRegla(
                False,
                "Especialidad incompatible",
            )

        return ResultadoRegla(True)

    # =====================================================
    # REGLA 3
    # =====================================================

    @classmethod
    def carga_laboral(
        cls,
        visitas_programadas: int,
    ) -> ResultadoRegla:

        if visitas_programadas >= cls.MAX_VISITAS_DIA:

            return ResultadoRegla(
                False,
                "Carga laboral máxima",
            )

        prioridad = cls.MAX_VISITAS_DIA - visitas_programadas

        return ResultadoRegla(
            True,
            prioridad=prioridad,
        )

    # =====================================================
    # REGLA 4
    # =====================================================

    @staticmethod
    def municipio(
        profesional: dict,
        municipio: str,
    ) -> ResultadoRegla:

        if profesional.get("municipio") != municipio:

            return ResultadoRegla(
                False,
                "Municipio diferente",
            )

        return ResultadoRegla(True)

    # =====================================================
    # REGLA 5
    # =====================================================

    @classmethod
    def distancia(
        cls,
        kilometros: float,
    ) -> ResultadoRegla:

        if kilometros > cls.MAX_DISTANCIA_KM:

            return ResultadoRegla(
                False,
                "Distancia excedida",
            )

        prioridad = int(
            cls.MAX_DISTANCIA_KM - kilometros
        )

        return ResultadoRegla(
            True,
            prioridad=prioridad,
        )

    # =====================================================
    # REGLA 6
    # =====================================================

    @staticmethod
    def disponibilidad(
        hora_inicio: datetime,
        hora_fin: datetime,
        nueva_hora: datetime,
        duracion_minutos: int,
    ) -> ResultadoRegla:

        nueva_fin = nueva_hora + timedelta(
            minutes=duracion_minutos
        )

        conflicto = (
            nueva_hora < hora_fin
            and nueva_fin > hora_inicio
        )

        if conflicto:

            return ResultadoRegla(
                False,
                "Cruce de horario",
            )

        return ResultadoRegla(True)

    # =====================================================
    # REGLA 7
    # =====================================================

    @staticmethod
    def prioridad_paciente(
        prioridad: str,
    ) -> int:

        prioridades = {

            "CRITICA": 100,

            "ALTA": 75,

            "MEDIA": 50,

            "BAJA": 25,

        }

        return prioridades.get(
            prioridad.upper(),
            0,
        )

    # =====================================================
    # EVALUACIÓN GLOBAL
    # =====================================================

    @classmethod
    def evaluar(
        cls,
        profesional: dict,
        servicio: str,
        municipio: str,
        visitas_programadas: int,
    ) -> list[ResultadoRegla]:

        resultados = [

            cls.profesional_activo(
                profesional
            ),

            cls.especialidad_valida(
                profesional,
                servicio,
            ),

            cls.carga_laboral(
                visitas_programadas,
            ),

            cls.municipio(
                profesional,
                municipio,
            ),

        ]

        return resultados

    # =====================================================
    # RESULTADO FINAL
    # =====================================================

    @staticmethod
    def aprobado(
        resultados: list[ResultadoRegla],
    ) -> bool:

        return all(
            r.valido
            for r in resultados
        )

    @staticmethod
    def puntaje(
        resultados: list[ResultadoRegla],
    ) -> int:

        return sum(
            r.prioridad
            for r in resultados
        )