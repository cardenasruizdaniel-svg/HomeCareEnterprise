"""
=========================================================
HomeCare Enterprise
Plantilla Repository
=========================================================
"""

import sqlite3

from database.database import get_connection


class PlantillaRepository:

    def __init__(self):

        self.connection = get_connection()

        # En SQLite hay que pedir explícitamente que las filas se
        # puedan usar como diccionario -- en PostgreSQL esto ya
        # viene así por defecto (a través de la capa de
        # compatibilidad), así que no aplica ahí.
        from database.db_backend import ES_POSTGRES
        if not ES_POSTGRES:
            self.connection.row_factory = sqlite3.Row

    # =====================================================
    # CONSULTAS
    # =====================================================

    def fetch_all(self, sql, parametros=()):

        cursor = self.connection.cursor()

        cursor.execute(sql, parametros)

        return cursor.fetchall()

    def fetch_one(self, sql, parametros=()):

        cursor = self.connection.cursor()

        cursor.execute(sql, parametros)

        return cursor.fetchone()

    def execute(self, sql, parametros=()):

        cursor = self.connection.cursor()

        cursor.execute(sql, parametros)

        self.connection.commit()

        return cursor.lastrowid

# =====================================================
# PLANTILLAS
# =====================================================

    def listar_plantillas(self):

        sql = """

            SELECT

                id,

                uuid,

                nombre,

                categoria,

                especialidad,

                tipo_profesional,

                version,

                estado,

                visibilidad,

                activa

            FROM plantillas

            ORDER BY nombre

        """

        return self.fetch_all(sql)


    # =====================================================
    # CREAR PLANTILLA
    # =====================================================

    def crear_plantilla(
        self,
        uuid,
        nombre,
        categoria,
        especialidad,
        tipo_profesional,
        servicio,
        usuario
    ):

        sql = """
        INSERT INTO plantillas(

            uuid,
            nombre,
            categoria,
            especialidad,
            tipo_profesional,
            servicio,
            version,
            estado,
            visibilidad,
            creada_por,
            fecha_creacion

        )

        VALUES(

            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            '1.0',
            'BORRADOR',
            'PERSONAL',
            ?,
            datetime('now')

        )
        """

        plantilla_id = self.execute(

            sql,

            (

                uuid,
                nombre,
                categoria,
                especialidad,
                tipo_profesional,
                servicio,
                usuario

            )

        )

        sql_version = """
        INSERT INTO plantilla_versiones(

            plantilla_id,
            version,
            descripcion,
            json_estructura,
            publicada,
            vigente,
            creada_por,
            fecha_creacion

        )

        VALUES(

            ?,
            '1.0',
            'Versión inicial',
            '{}',
            0,
            1,
            ?,
            datetime('now')

        )
        """

        self.execute(

            sql_version,

            (

                plantilla_id,
                usuario

            )

        )

        return plantilla_id
    
    # =====================================================
    # COMPONENTES
    # =====================================================

    def listar_componentes(self):

        sql = """

        SELECT

            id,

            codigo,

            nombre,

            icono,

            categoria,

            tipo_dato,

            activo

        FROM plantilla_componentes

        WHERE activo = 1

        ORDER BY categoria, nombre

        """

        return self.fetch_all(sql)