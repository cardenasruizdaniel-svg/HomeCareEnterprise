"""
=========================================================
HomeCare Enterprise
Base Repository
Sprint 3.4A
Versión: 8.0
=========================================================
"""

from __future__ import annotations

from typing import Any

from database.database import (
    get_connection,
    consultar_todos,
    consultar_uno,
    consultar_escalar,
    ejecutar,
    ejecutarmany,
)


class BaseRepository:
    """
    Clase base para todos los repositorios.

    Centraliza el acceso a la base de datos y elimina la
    duplicación de código en toda la aplicación.
    """

    # =====================================================
    # CONEXIÓN
    # =====================================================

    @staticmethod
    def connection():
        return get_connection()

    # =====================================================
    # FETCH ALL
    # =====================================================

    @staticmethod
    def fetch_all(
        sql: str,
        parametros: tuple = (),
    ):
        return consultar_todos(sql, parametros)

    # =====================================================
    # FETCH ONE
    # =====================================================

    @staticmethod
    def fetch_one(
        sql: str,
        parametros: tuple = (),
    ):
        return consultar_uno(sql, parametros)

    # =====================================================
    # SCALAR
    # =====================================================

    @staticmethod
    def scalar(
        sql: str,
        parametros: tuple = (),
    ):
        return consultar_escalar(sql, parametros)

    # =====================================================
    # EXECUTE
    # =====================================================

    @staticmethod
    def execute(
        sql: str,
        parametros: tuple = (),
    ):
        return ejecutar(sql, parametros)

    # =====================================================
    # EXECUTE MANY
    # =====================================================

    @staticmethod
    def execute_many(
        sql: str,
        datos,
    ):
        return ejecutarmany(sql, datos)

    # =====================================================
    # EXISTS
    # =====================================================

    @classmethod
    def exists(
        cls,
        tabla: str,
        registro_id: int,
    ) -> bool:

        sql = f"""

            SELECT COUNT(*)

            FROM {tabla}

            WHERE id=?

        """

        return cls.scalar(sql, (registro_id,)) > 0

    # =====================================================
    # COUNT
    # =====================================================

    @classmethod
    def count(
        cls,
        tabla: str,
    ) -> int:

        sql = f"""

            SELECT COUNT(*)

            FROM {tabla}

        """

        return cls.scalar(sql)

    # =====================================================
    # DELETE
    # =====================================================

    @classmethod
    def delete(
        cls,
        tabla: str,
        registro_id: int,
    ):

        sql = f"""

            DELETE

            FROM {tabla}

            WHERE id=?

        """

        return cls.execute(

            sql,

            (

                registro_id,

            ),

        )
    
        # =====================================================
    # INSERT
    # =====================================================

    @classmethod
    def insert(
        cls,
        tabla: str,
        datos: dict[str, Any],
    ):

        columnas = ", ".join(datos.keys())

        parametros = ", ".join(
            [f":{campo}" for campo in datos.keys()]
        )

        sql = f"""
            INSERT INTO {tabla}
            ({columnas})
            VALUES
            ({parametros})
        """

        return cls.execute(sql, datos)


    # =====================================================
    # UPDATE
    # =====================================================

    @classmethod
    def update(
        cls,
        tabla: str,
        registro_id: int,
        datos: dict[str, Any],
    ):

        asignaciones = ", ".join(
            [f"{campo}=:{campo}" for campo in datos.keys()]
        )

        datos["id"] = registro_id

        sql = f"""
            UPDATE {tabla}

            SET

                {asignaciones}

            WHERE id=:id
        """

        return cls.execute(sql, datos)


    # =====================================================
    # PAGINACIÓN
    # =====================================================

    @classmethod
    def paginate(
        cls,
        sql: str,
        pagina: int = 1,
        limite: int = 25,
        parametros: tuple = (),
    ):

        offset = (pagina - 1) * limite

        sql = f"""

            {sql}

            LIMIT ?

            OFFSET ?

        """

        parametros = parametros + (

            limite,

            offset,

        )

        return cls.fetch_all(

            sql,

            parametros,

        )


    # =====================================================
    # BEGIN
    # =====================================================

    @staticmethod
    def begin():

        conexion = get_connection()

        conexion.execute(

            "BEGIN"

        )

        return conexion


    # =====================================================
    # COMMIT
    # =====================================================

    @staticmethod
    def commit(
        conexion,
    ):

        conexion.commit()


    # =====================================================
    # ROLLBACK
    # =====================================================

    @staticmethod
    def rollback(
        conexion,
    ):

        conexion.rollback()


    # =====================================================
    # CLOSE
    # =====================================================

    @staticmethod
    def close(
        conexion,
    ):

        conexion.close()


    # =====================================================
    # TRANSACTION
    # =====================================================

    @classmethod
    def transaction(
        cls,
        operaciones,
    ):

        conexion = cls.begin()

        try:

            resultado = operaciones(

                conexion

            )

            cls.commit(

                conexion

            )

            return resultado

        except Exception:

            cls.rollback(

                conexion

            )

            raise

        finally:

            cls.close(

                conexion

            )


    # =====================================================
    # FETCH DICT
    # =====================================================

    @classmethod
    def fetch_dict(
        cls,
        sql: str,
        parametros: tuple = (),
    ):

        filas = cls.fetch_all(

            sql,

            parametros,

        )

        return [

            dict(fila)

            for fila in filas

        ]


    # =====================================================
    # FETCH FIRST
    # =====================================================

    @classmethod
    def fetch_first(
        cls,
        sql: str,
        parametros: tuple = (),
    ):

        fila = cls.fetch_one(

            sql,

            parametros,

        )

        if fila is None:

            return None

        return dict(fila)
    
        # =====================================================
    # VALIDAR TABLA
    # =====================================================

    @staticmethod
    def validar_tabla(tabla: str):

        if not tabla:

            raise ValueError(
                "Debe indicar el nombre de la tabla."
            )

        return tabla


    # =====================================================
    # SQL LOG
    # =====================================================

    @staticmethod
    def log_sql(
        sql: str,
        parametros=None,
    ):

        """
        Método preparado para futuras auditorías.

        Posteriormente podrá escribir en:

            logs/sql.log

        o en la tabla audit_log.
        """

        return {

            "sql": sql,

            "parametros": parametros,

        }


    # =====================================================
    # EJECUTAR SQL LIBRE
    # =====================================================

    @classmethod
    def execute_sql(

        cls,

        sql: str,

        parametros: tuple | dict[str, Any] = (),

    ):

        cls.log_sql(

            sql,

            parametros,

        )

        return cls.execute(

            sql,

            parametros,

        )


    # =====================================================
    # FETCH COMO LISTA DE DICCIONARIOS
    # =====================================================

    @classmethod
    def fetch_list(

        cls,

        sql: str,

        parametros: tuple | dict[str, Any] = (),

    ):

        filas = cls.fetch_all(

            sql,

            parametros,

        )

        return [

            dict(fila)

            for fila in filas

        ]


    # =====================================================
    # FETCH PRIMERO O VACÍO
    # =====================================================

    @classmethod
    def fetch_or_empty(

        cls,

        sql: str,

        parametros: tuple | dict[str, Any] = (),

    ):

        fila = cls.fetch_one(

            sql,

            parametros,

        )

        if fila is None:

            return {}

        return dict(fila)


    # =====================================================
    # OBTENER ÚLTIMO ID
    # =====================================================

    @classmethod
    def last_insert_id(

        cls,

        tabla: str,

    ):

        tabla = cls.validar_tabla(tabla)

        sql = f"""

            SELECT

                MAX(id)

            FROM {tabla}

        """

        return cls.scalar(sql)


    # =====================================================
    # TRUNCATE LÓGICO
    # =====================================================

    @classmethod
    def logical_delete(

        cls,

        tabla: str,

        registro_id: int,

    ):

        tabla = cls.validar_tabla(tabla)

        sql = f"""

            UPDATE {tabla}

            SET

                eliminado=1

            WHERE id=?

        """

        return cls.execute(

            sql,

            (

                registro_id,

            ),

        )


    # =====================================================
    # REACTIVAR REGISTRO
    # =====================================================

    @classmethod
    def restore(

        cls,

        tabla: str,

        registro_id: int,

    ):

        tabla = cls.validar_tabla(tabla)

        sql = f"""

            UPDATE {tabla}

            SET

                eliminado=0

            WHERE id=?

        """

        return cls.execute(

            sql,

            (

                registro_id,

            ),

        )


    # =====================================================
    # TOTAL FILAS
    # =====================================================

    @classmethod
    def total(

        cls,

        tabla: str,

    ):

        return cls.count(tabla)
    
        # =====================================================
    # TABLAS PERMITIDAS
    # =====================================================

    ALLOWED_TABLES = {

        "pacientes",

        "profesionales",

        "programaciones",

        "despachos",

        "usuarios",

        "medicamentos",

        "tratamientos",

        "agenda",

        "visitas",

        "inventario",

        "vehiculos",

        "profesionales_especialidades",

        "profesionales_zonas",

        "profesionales_ubicacion",

    }


    # =====================================================
    # VALIDAR TABLA
    # =====================================================

    @classmethod
    def validate_table(
        cls,
        tabla: str,
    ):

        if tabla not in cls.ALLOWED_TABLES:

            raise ValueError(

                f"Tabla no permitida: {tabla}"

            )

        return tabla


    # =====================================================
    # AUDITORÍA (PREPARADO)
    # =====================================================

    @staticmethod
    def audit(
        accion: str,
        tabla: str,
        registro=None,
    ):

        """
        Placeholder.

        En Sprint 3.5 escribirá automáticamente en:

            audit_log

        o

            logs/audit.log
        """

        return {

            "accion": accion,

            "tabla": tabla,

            "registro": registro,

        }


    # =====================================================
    # BEFORE INSERT
    # =====================================================

    @staticmethod
    def before_insert(
        datos: dict,
    ):

        return datos


    # =====================================================
    # AFTER INSERT
    # =====================================================

    @staticmethod
    def after_insert(
        nuevo_id: int,
    ):

        return nuevo_id


    # =====================================================
    # BEFORE UPDATE
    # =====================================================

    @staticmethod
    def before_update(
        datos: dict,
    ):

        return datos


    # =====================================================
    # AFTER UPDATE
    # =====================================================

    @staticmethod
    def after_update(
        filas: int,
    ):

        return filas


    # =====================================================
    # BEFORE DELETE
    # =====================================================

    @staticmethod
    def before_delete(
        registro_id: int,
    ):

        return registro_id


    # =====================================================
    # AFTER DELETE
    # =====================================================

    @staticmethod
    def after_delete(
        filas: int,
    ):

        return filas


    # =====================================================
    # TO DICT
    # =====================================================

    @staticmethod
    def to_dict(
        fila,
    ):

        if fila is None:

            return None

        return dict(fila)


    # =====================================================
    # TO LIST
    # =====================================================

    @staticmethod
    def to_list(
        filas,
    ):

        return [

            dict(f)

            for f in filas

        ]


    # =====================================================
    # HEALTH CHECK
    # =====================================================

    @classmethod
    def health_check(cls):

        try:

            cls.scalar(

                "SELECT 1"

            )

            return True

        except Exception:

            return False


    # =====================================================
    # VERSIÓN
    # =====================================================

    VERSION = "8.0.0"