"""
=========================================================
HomeCare Enterprise
Repository Exceptions
Sprint 3.4A
Versión 8.0
=========================================================
"""

from __future__ import annotations


class RepositoryError(Exception):
    """
    Excepción base para todos los errores
    relacionados con los repositorios.
    """

    def __init__(self, message: str = "Error del repositorio"):
        super().__init__(message)


# =========================================================
# CONEXIÓN
# =========================================================

class DatabaseConnectionError(RepositoryError):
    """Error al establecer conexión con la base de datos."""


class TransactionError(RepositoryError):
    """Error durante una transacción."""


# =========================================================
# CONSULTAS
# =========================================================

class QueryError(RepositoryError):
    """Error ejecutando una consulta SQL."""


class InvalidQueryError(QueryError):
    """Consulta SQL inválida."""


# =========================================================
# ENTIDADES
# =========================================================

class EntityNotFoundError(RepositoryError):
    """La entidad solicitada no existe."""


class DuplicateRecordError(RepositoryError):
    """El registro ya existe."""


class RecordDeletedError(RepositoryError):
    """El registro fue eliminado lógicamente."""


# =========================================================
# VALIDACIONES
# =========================================================

class ValidationError(RepositoryError):
    """Los datos enviados no son válidos."""


class InvalidTableError(ValidationError):
    """Tabla no permitida."""


class InvalidColumnError(ValidationError):
    """Columna no permitida."""


class InvalidFilterError(ValidationError):
    """Filtro inválido."""


# =========================================================
# PERMISOS
# =========================================================

class PermissionDeniedError(RepositoryError):
    """Acceso denegado."""


# =========================================================
# PAGINACIÓN
# =========================================================

class PaginationError(RepositoryError):
    """Error de paginación."""


# =========================================================
# AUDITORÍA
# =========================================================

class AuditError(RepositoryError):
    """Error registrando auditoría."""


# =========================================================
# IMPORTACIÓN / EXPORTACIÓN
# =========================================================

class ExportError(RepositoryError):
    """Error durante la exportación."""


class ImportErrorRepository(RepositoryError):
    """Error durante la importación."""