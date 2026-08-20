"""
=========================================================
HomeCare Enterprise
Query Builder
Sprint 3.4A
Versión 8.0
=========================================================
"""

from __future__ import annotations

from typing import Any


class QueryBuilder:
    """
    Constructor dinámico de consultas SQL.

    Permite construir consultas parametrizadas
    sin concatenar SQL manualmente.
    """

    def __init__(self, tabla: str):

        self.tabla = tabla

        self._select = "*"

        self._where = []

        self._params = []

        self._order = None

        self._group = None

        self._limit = None

        self._offset = None

    # =====================================================
    # SELECT
    # =====================================================

    def select(self, columnas):

        if isinstance(columnas, list):

            self._select = ", ".join(columnas)

        else:

            self._select = columnas

        return self

    # =====================================================
    # WHERE
    # =====================================================

    def where(

        self,

        columna,

        valor,

        operador="=",

    ):

        if valor is None:

            return self

        self._where.append(

            f"{columna} {operador} ?"

        )

        self._params.append(valor)

        return self

    # =====================================================
    # LIKE
    # =====================================================

    def like(

        self,

        columna,

        texto,

    ):

        if not texto:

            return self

        self._where.append(

            f"{columna} LIKE ?"

        )

        self._params.append(

            f"%{texto}%"

        )

        return self

    # =====================================================
    # IN
    # =====================================================

    def where_in(

        self,

        columna,

        valores,

    ):

        if not valores:

            return self

        placeholders = ",".join(

            ["?"] * len(valores)

        )

        self._where.append(

            f"{columna} IN ({placeholders})"

        )

        self._params.extend(valores)

        return self

    # =====================================================
    # BETWEEN
    # =====================================================

    def between(

        self,

        columna,

        inicio,

        fin,

    ):

        if inicio is None or fin is None:

            return self

        self._where.append(

            f"{columna} BETWEEN ? AND ?"

        )

        self._params.extend(

            [

                inicio,

                fin,

            ]

        )

        return self

    # =====================================================
    # ORDER BY
    # =====================================================

    def order_by(

        self,

        columna,

        sentido="ASC",

    ):

        self._order = (

            columna,

            sentido,

        )

        return self

    # =====================================================
    # GROUP BY
    # =====================================================

    def group_by(

        self,

        columna,

    ):

        self._group = columna

        return self

    # =====================================================
    # LIMIT
    # =====================================================

    def limit(

        self,

        cantidad,

    ):

        self._limit = cantidad

        return self

    # =====================================================
    # OFFSET
    # =====================================================

    def offset(

        self,

        cantidad,

    ):

        self._offset = cantidad

        return self

    # =====================================================
    # BUILD
    # =====================================================

    def build(self):

        sql = f"""

            SELECT

                {self._select}

            FROM

                {self.tabla}

        """

        if self._where:

            sql += "\nWHERE\n"

            sql += "\nAND ".join(

                self._where

            )

        if self._group:

            sql += (

                f"\nGROUP BY {self._group}"

            )

        if self._order:

            sql += (

                f"\nORDER BY "

                f"{self._order[0]} "

                f"{self._order[1]}"

            )

        if self._limit is not None:

            sql += f"\nLIMIT {self._limit}"

        if self._offset is not None:

            sql += f"\nOFFSET {self._offset}"

        return sql, tuple(self._params)

    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self._where.clear()

        self._params.clear()

        self._group = None

        self._order = None

        self._limit = None

        self._offset = None

        self._select = "*"

        return self