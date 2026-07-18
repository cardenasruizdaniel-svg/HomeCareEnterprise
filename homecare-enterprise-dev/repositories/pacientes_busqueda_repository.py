from database.database import get_connection


def buscar_pacientes(texto):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT

            id,
            documento,
            (primer_nombre || ' ' || COALESCE(segundo_nombre || ' ', '') ||
             primer_apellido || ' ' || COALESCE(segundo_apellido, '')) AS nombre,
            telefono,
            direccion,
            municipio AS ciudad,
            eps,
            sexo,
            fecha_nacimiento

        FROM pacientes

        WHERE

            documento LIKE ?

            OR primer_nombre LIKE ?

            OR primer_apellido LIKE ?

            OR telefono LIKE ?

            OR celular LIKE ?

            OR eps LIKE ?

            OR municipio LIKE ?

        ORDER BY primer_nombre

        LIMIT 30

    """,(

        f"%{texto}%",

        f"%{texto}%",

        f"%{texto}%",

        f"%{texto}%",

        f"%{texto}%",

        f"%{texto}%",

        f"%{texto}%"

    ))

    datos = cursor.fetchall()

    conexion.close()

    return datos