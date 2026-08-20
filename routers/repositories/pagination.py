"""
=========================================================
HomeCare Enterprise
Pagination
Sprint 3.4A
Versión 8.0
=========================================================
"""

from __future__ import annotations

from math import ceil


class Pagination:
    """
    Administrador de paginación para consultas SQL.
    """

    DEFAULT_PER_PAGE = 25
    MAX_PER_PAGE = 500

    def __init__(

        self,

        page: int = 1,

        per_page: int = DEFAULT_PER_PAGE,

        total: int = 0,

    ):

        self.page = max(1, page)

        self.per_page = max(

            1,

            min(

                per_page,

                self.MAX_PER_PAGE,

            ),

        )

        self.total = max(0, total)

    # =====================================================
    # OFFSET
    # =====================================================

    @property
    def offset(self):

        return (

            self.page - 1

        ) * self.per_page

    # =====================================================
    # TOTAL PÁGINAS
    # =====================================================

    @property
    def pages(self):

        if self.total == 0:

            return 1

        return ceil(

            self.total / self.per_page

        )

    # =====================================================
    # PÁGINA ANTERIOR
    # =====================================================

    @property
    def previous(self):

        if self.page <= 1:

            return None

        return self.page - 1

    # =====================================================
    # PÁGINA SIGUIENTE
    # =====================================================

    @property
    def next(self):

        if self.page >= self.pages:

            return None

        return self.page + 1

    # =====================================================
    # PRIMERA
    # =====================================================

    @property
    def first(self):

        return 1

    # =====================================================
    # ÚLTIMA
    # =====================================================

    @property
    def last(self):

        return self.pages

    # =====================================================
    # APPLY SQL
    # =====================================================

    def apply(

        self,

        sql: str,

    ):

        sql += """

LIMIT ?

OFFSET ?

"""

        parametros = (

            self.per_page,

            self.offset,

        )

        return sql, parametros

    # =====================================================
    # INFO
    # =====================================================

    def info(self):

        return {

            "page": self.page,

            "per_page": self.per_page,

            "total": self.total,

            "pages": self.pages,

            "previous": self.previous,

            "next": self.next,

            "first": self.first,

            "last": self.last,

            "offset": self.offset,

        }

    # =====================================================
    # TO DICT
    # =====================================================

    def to_dict(self):

        return self.info()

    # =====================================================
    # HAS NEXT
    # =====================================================

    def has_next(self):

        return self.next is not None

    # =====================================================
    # HAS PREVIOUS
    # =====================================================

    def has_previous(self):

        return self.previous is not None

    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.page = 1

        self.total = 0

        self.per_page = self.DEFAULT_PER_PAGE