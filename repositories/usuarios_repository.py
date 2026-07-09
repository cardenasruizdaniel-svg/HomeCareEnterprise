from database.database import get_connection


class UsuariosRepository:

    @staticmethod
    def obtener_por_usuario(usuario: str):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT *
            FROM usuarios
            WHERE usuario = ?
            AND estado='Activo'
            """,
            (usuario,),
        )

        fila = cursor.fetchone()

        conexion.close()

        return fila

    @staticmethod
    def obtener_por_id(usuario_id: int):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT *
            FROM usuarios
            WHERE id = ?
            """,
            (usuario_id,),
        )

        fila = cursor.fetchone()

        conexion.close()

        return fila

    @staticmethod
    def listar():

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT *
            FROM usuarios
            ORDER BY nombre
            """
        )

        datos = cursor.fetchall()

        conexion.close()

        return datos