from passlib.hash import bcrypt
from database.database import get_connection


def listar_usuarios():
    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM usuarios
        ORDER BY nombre
    """)

    datos = cursor.fetchall()
    conexion.close()
    return datos


def obtener_usuario(id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM usuarios
        WHERE id=?
    """, (id,))

    usuario = cursor.fetchone()

    conexion.close()

    return usuario


def crear_usuario(nombre, usuario, password, rol, correo, telefono):

    conexion = get_connection()
    cursor = conexion.cursor()

    password = bcrypt.hash(password)

    cursor.execute("""
        INSERT INTO usuarios(

            nombre,
            usuario,
            password,
            rol,
            correo,
            telefono

        )

        VALUES(?,?,?,?,?,?)

    """, (

        nombre,
        usuario,
        password,
        rol,
        correo,
        telefono

    ))

    conexion.commit()
    conexion.close()


def actualizar_usuario(
        id,
        nombre,
        usuario,
        rol,
        correo,
        telefono,
        estado,
        password=None,
):

    conexion = get_connection()
    cursor = conexion.cursor()

    if password:

        password_cifrada = bcrypt.hash(password)

        cursor.execute("""

            UPDATE usuarios

            SET

                nombre=?,
                usuario=?,
                rol=?,
                correo=?,
                telefono=?,
                estado=?,
                password=?

            WHERE id=?

        """, (

            nombre,
            usuario,
            rol,
            correo,
            telefono,
            estado,
            password_cifrada,
            id

        ))

    else:

        cursor.execute("""

            UPDATE usuarios

            SET

                nombre=?,
                usuario=?,
                rol=?,
                correo=?,
                telefono=?,
                estado=?

            WHERE id=?

        """, (

            nombre,
            usuario,
            rol,
            correo,
            telefono,
            estado,
            id

        ))

    conexion.commit()
    conexion.close()


def eliminar_usuario(id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE usuarios

        SET estado='Inactivo'

        WHERE id=?

    """, (id,))

    conexion.commit()
    conexion.close()

