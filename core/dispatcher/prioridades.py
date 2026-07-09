"""
==============================================================
HomeCare Enterprise
Motor Inteligente de Asignación
Archivo: core/dispatcher/prioridades.py
==============================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NivelPrioridad(str, Enum):

    CRITICA = "CRITICA"

    ALTA = "ALTA"

    MEDIA = "MEDIA"

    BAJA = "BAJA"


@dataclass(slots=True)
class ResultadoPrioridad:

    nivel: NivelPrioridad

    puntaje: int

    motivo: str


class PrioridadPaciente:

    """
    Motor de priorización clínica.

    Calcula un puntaje para cada visita que luego será
    utilizado por el Motor de Asignación Inteligente.
    """

    PUNTAJES = {

        NivelPrioridad.CRITICA: 100,

        NivelPrioridad.ALTA: 75,

        NivelPrioridad.MEDIA: 50,

        NivelPrioridad.BAJA: 25,

    }

    # ==========================================================
    # PRIORIDAD SEGÚN SERVICIO
    # ==========================================================

    SERVICIOS = {

        "codigo azul": NivelPrioridad.CRITICA,

        "urgencias": NivelPrioridad.CRITICA,

        "hospitalizacion": NivelPrioridad.ALTA,

        "medicina": NivelPrioridad.MEDIA,

        "enfermeria": NivelPrioridad.MEDIA,

        "terapia respiratoria": NivelPrioridad.ALTA,

        "terapia fisica": NivelPrioridad.MEDIA,

        "terapia ocupacional": NivelPrioridad.MEDIA,

        "fonoaudiologia": NivelPrioridad.MEDIA,

        "psicologia": NivelPrioridad.MEDIA,

        "nutricion": NivelPrioridad.BAJA,

    }

    # ==========================================================
    # CLASIFICAR SERVICIO
    # ==========================================================

    @classmethod
    def por_servicio(
        cls,
        servicio: str,
    ) -> ResultadoPrioridad:

        nivel = cls.SERVICIOS.get(

            servicio.lower(),

            NivelPrioridad.MEDIA

        )

        return ResultadoPrioridad(

            nivel=nivel,

            puntaje=cls.PUNTAJES[nivel],

            motivo=f"Servicio: {servicio}"

        )

    # ==========================================================
    # ADULTO MAYOR
    # ==========================================================

    @classmethod
    def por_edad(
        cls,
        edad: int,
    ) -> ResultadoPrioridad:

        if edad >= 85:

            nivel = NivelPrioridad.CRITICA

        elif edad >= 70:

            nivel = NivelPrioridad.ALTA

        elif edad >= 50:

            nivel = NivelPrioridad.MEDIA

        else:

            nivel = NivelPrioridad.BAJA

        return ResultadoPrioridad(

            nivel=nivel,

            puntaje=cls.PUNTAJES[nivel],

            motivo=f"Edad: {edad}"

        )

    # ==========================================================
    # PACIENTE PALIATIVO
    # ==========================================================

    @classmethod
    def paliativo(
        cls,
        es_paliativo: bool,
    ) -> ResultadoPrioridad:

        if es_paliativo:

            return ResultadoPrioridad(

                NivelPrioridad.CRITICA,

                cls.PUNTAJES[NivelPrioridad.CRITICA],

                "Paciente paliativo"

            )

        return ResultadoPrioridad(

            NivelPrioridad.BAJA,

            0,

            "No aplica"

        )

    # ==========================================================
    # VENTANA DE ATENCIÓN
    # ==========================================================

    @classmethod
    def ventana_horaria(
        cls,
        minutos_restantes: int,
    ) -> ResultadoPrioridad:

        if minutos_restantes <= 30:

            nivel = NivelPrioridad.CRITICA

        elif minutos_restantes <= 60:

            nivel = NivelPrioridad.ALTA

        elif minutos_restantes <= 120:

            nivel = NivelPrioridad.MEDIA

        else:

            nivel = NivelPrioridad.BAJA

        return ResultadoPrioridad(

            nivel,

            cls.PUNTAJES[nivel],

            "Ventana horaria"

        )

    # ==========================================================
    # CÁLCULO GLOBAL
    # ==========================================================

    @classmethod
    def calcular(

        cls,

        servicio: str,

        edad: int,

        paliativo: bool,

        minutos_restantes: int,

    ) -> dict:

        resultados = [

            cls.por_servicio(servicio),

            cls.por_edad(edad),

            cls.paliativo(paliativo),

            cls.ventana_horaria(minutos_restantes),

        ]

        puntaje = max(

            r.puntaje

            for r in resultados

        )

        nivel = max(

            resultados,

            key=lambda r: r.puntaje

        ).nivel

        return {

            "nivel": nivel.value,

            "puntaje": puntaje,

            "criterios": resultados

        }