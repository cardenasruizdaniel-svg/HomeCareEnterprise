"""
=========================================================
HomeCare Enterprise
Filters
Sprint 3.4A
Versión 8.0
=========================================================
"""

from __future__ import annotations

from typing import Any

from repositories.query_builder import QueryBuilder


class Filters:
    """
    Constructor de filtros reutilizables.

    Aplica automáticamente filtros sobre un QueryBuilder.
    """

    # =====================================================
    # APLICAR
    # =====================================================

    @staticmethod
    def apply(

        qb: QueryBuilder,

        filtros: dict[str, Any],

    ) -> QueryBuilder:

        if not filtros:

            return qb

        for campo, valor in filtros.items():

            if valor is None:

                continue

            if valor == "":

                continue

            qb.where(

                campo,

                valor,

            )

        return qb

    # =====================================================
    # TEXTO
    # =====================================================

    @staticmethod
    def text(

        qb: QueryBuilder,

        columnas: list[str],

        texto: str,

    ):

        if not texto:

            return qb

        condiciones = []

        for columna in columnas:

            condiciones.append(

                f"{columna} LIKE ?"

            )

            qb._params.append(

                f"%{texto}%"

            )

        qb._where.append(

            "(" +

            " OR ".join(condiciones)

            +

            ")"

        )

        return qb

    # =====================================================
    # FECHAS
    # =====================================================

    @staticmethod
    def dates(

        qb: QueryBuilder,

        columna: str,

        fecha_inicio,

        fecha_fin,

    ):

        if fecha_inicio and fecha_fin:

            qb.between(

                columna,

                fecha_inicio,

                fecha_fin,

            )

        return qb

    # =====================================================
    # ESTADO
    # =====================================================

    @staticmethod
    def estado(

        qb: QueryBuilder,

        estado,

    ):

        return qb.where(

            "estado",

            estado,

        )

    # =====================================================
    # MUNICIPIO
    # =====================================================

    @staticmethod
    def municipio(

        qb: QueryBuilder,

        municipio,

    ):

        return qb.where(

            "municipio",

            municipio,

        )

    # =====================================================
    # PROFESIONAL
    # =====================================================

    @staticmethod
    def profesional(

        qb: QueryBuilder,

        profesional_id,

    ):

        return qb.where(

            "profesional_id",

            profesional_id,

        )

    # =====================================================
    # PACIENTE
    # =====================================================

    @staticmethod
    def paciente(

        qb: QueryBuilder,

        paciente_id,

    ):

        return qb.where(

            "paciente_id",

            paciente_id,

        )

    # =====================================================
    # PRIORIDAD
    # =====================================================

    @staticmethod
    def prioridad(

        qb: QueryBuilder,

        prioridad,

    ):

        return qb.where(

            "prioridad",

            prioridad,

        )

    # =====================================================
    # DISPONIBLE
    # =====================================================

    @staticmethod
    def disponible(

        qb: QueryBuilder,

        disponible,

    ):

        return qb.where(

            "disponible",

            disponible,

        )

    # =====================================================
    # ACTIVO
    # =====================================================

    @staticmethod
    def activo(

        qb: QueryBuilder,

        activo,

    ):

        return qb.where(

            "activo",

            activo,

        )

    # =====================================================
    # ORDENAMIENTO
    # =====================================================

    @staticmethod
    def ordenar(

        qb: QueryBuilder,

        columna: str,

        sentido="ASC",

    ):

        qb.order_by(

            columna,

            sentido,

        )

        return qb

    # =====================================================
    # PAGINAR
    # =====================================================

    @staticmethod
    def paginar(

        qb: QueryBuilder,

        limite=25,

        offset=0,

    ):

        qb.limit(

            limite,

        )

        qb.offset(

            offset,

        )

        return qb