"""
==============================================================
HomeCare Enterprise
Motor Inteligente de Asignación
Archivo: core/dispatcher/disponibilidad.py
==============================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable


@dataclass(slots=True)
class BloqueHorario:
    inicio: datetime
    fin: datetime
    descripcion: str = ""


class DisponibilidadProfesional:
    """
    Motor encargado de validar si un profesional
    tiene disponibilidad para recibir una nueva visita.
    """

    JORNADA_MAXIMA_HORAS = 12
    TIEMPO_DESPLAZAMIENTO = 20  # minutos

    # =====================================================
    # VALIDAR CRUCE DE HORARIOS
    # =====================================================

    @staticmethod
    def existe_conflicto(
        inicio: datetime,
        fin: datetime,
        agenda: Iterable[BloqueHorario],
    ) -> bool:

        for bloque in agenda:

            if inicio < bloque.fin and fin > bloque.inicio:
                return True

        return False

    # =====================================================
    # VALIDAR JORNADA
    # =====================================================

    @classmethod
    def jornada_valida(
        cls,
        agenda: Iterable[BloqueHorario],
    ) -> bool:

        if not agenda:
            return True

        agenda = sorted(
            agenda,
            key=lambda x: x.inicio
        )

        inicio = agenda[0].inicio
        fin = agenda[-1].fin

        horas = (
            fin - inicio
        ).total_seconds() / 3600

        return horas <= cls.JORNADA_MAXIMA_HORAS

    # =====================================================
    # CALCULAR HORA LIBRE
    # =====================================================

    @classmethod
    def siguiente_hora_disponible(
        cls,
        agenda: Iterable[BloqueHorario],
    ) -> datetime | None:

        agenda = sorted(
            agenda,
            key=lambda x: x.fin
        )

        if not agenda:
            return None

        return (
            agenda[-1].fin
            + timedelta(
                minutes=cls.TIEMPO_DESPLAZAMIENTO
            )
        )

    # =====================================================
    # VALIDAR NUEVA VISITA
    # =====================================================

    @classmethod
    def disponible(
        cls,
        inicio: datetime,
        duracion_minutos: int,
        agenda: Iterable[BloqueHorario],
    ) -> bool:

        fin = inicio + timedelta(
            minutes=duracion_minutos
        )

        if cls.existe_conflicto(
            inicio,
            fin,
            agenda,
        ):
            return False

        nueva_agenda = list(agenda)

        nueva_agenda.append(
            BloqueHorario(
                inicio=inicio,
                fin=fin,
                descripcion="Nueva visita",
            )
        )

        return cls.jornada_valida(
            nueva_agenda
        )

    # =====================================================
    # TIEMPO TOTAL DEL DÍA
    # =====================================================

    @staticmethod
    def minutos_programados(
        agenda: Iterable[BloqueHorario],
    ) -> int:

        total = 0

        for bloque in agenda:

            total += int(
                (
                    bloque.fin
                    - bloque.inicio
                ).total_seconds()
                / 60
            )

        return total

    # =====================================================
    # CANTIDAD DE VISITAS
    # =====================================================

    @staticmethod
    def numero_visitas(
        agenda: Iterable[BloqueHorario],
    ) -> int:

        return len(list(agenda))

    # =====================================================
    # RESUMEN OPERATIVO
    # =====================================================

    @classmethod
    def resumen(
        cls,
        agenda: Iterable[BloqueHorario],
    ) -> dict:

        agenda = list(agenda)

        return {

            "visitas": cls.numero_visitas(
                agenda
            ),

            "minutos_programados":
                cls.minutos_programados(
                    agenda
                ),

            "hora_disponible":
                cls.siguiente_hora_disponible(
                    agenda
                ),

            "jornada_valida":
                cls.jornada_valida(
                    agenda
                )

        }