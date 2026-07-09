from database.database import get_connection


# ==========================================================
# LISTAR PROFESIONALES
# ==========================================================

def listar():

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM profesionales

        ORDER BY primer_apellido,
                 primer_nombre

    """)

    datos = cursor.fetchall()

    conexion.close()

    return datos


# ==========================================================
# OBTENER PROFESIONAL
# ==========================================================

def obtener(profesional_id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM profesionales

        WHERE id = ?

    """, (profesional_id,))

    dato = cursor.fetchone()

    conexion.close()

    return dato


# ==========================================================
# PROFESIONALES ACTIVOS
# ==========================================================

def activos():

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM profesionales

        WHERE estado='Activo'

        ORDER BY primer_apellido,
                 primer_nombre

    """)

    datos = cursor.fetchall()

    conexion.close()

    return datos


# ==========================================================
# POR ESPECIALIDAD
# ==========================================================

def por_especialidad(especialidad):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM profesionales

        WHERE especialidad=?
          AND estado='Activo'

        ORDER BY primer_apellido,
                 primer_nombre

    """, (especialidad,))

    datos = cursor.fetchall()

    conexion.close()

    return datos


# ==========================================================
# POR MUNICIPIO
# ==========================================================

def por_municipio(municipio):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM profesionales

        WHERE municipio=?
          AND estado='Activo'

        ORDER BY primer_apellido,
                 primer_nombre

    """, (municipio,))

    datos = cursor.fetchall()

    conexion.close()

    return datos


# ==========================================================
# DISPONIBLES
# ==========================================================

def disponibles():

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM profesionales

        WHERE estado='Activo'
          AND disponible=1

        ORDER BY primer_apellido,
                 primer_nombre

    """)

    datos = cursor.fetchall()

    conexion.close()

    return datos


# ==========================================================
# CAMBIAR DISPONIBILIDAD
# ==========================================================

def cambiar_disponibilidad(
    profesional_id,
    disponible,
):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE profesionales

        SET disponible=?,
            fecha_actualizacion=CURRENT_TIMESTAMP

        WHERE id=?

    """, (

        disponible,

        profesional_id

    ))

    conexion.commit()

    conexion.close()


# ==========================================================
# CAMBIAR ESTADO
# ==========================================================

def cambiar_estado(
    profesional_id,
    estado,
):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE profesionales

        SET estado=?,
            fecha_actualizacion=CURRENT_TIMESTAMP

        WHERE id=?

    """, (

        estado,

        profesional_id

    ))

    conexion.commit()

    conexion.close()


# ==========================================================
# CARGA LABORAL
# ==========================================================

def carga_laboral(
    profesional_id,
    fecha,
):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT COUNT(*)

        FROM programaciones

        WHERE profesional_id=?
          AND fecha=?

    """, (

        profesional_id,

        fecha

    ))

    total = cursor.fetchone()[0]

    conexion.close()

    return total


# ==========================================================
# INDICADORES
# ==========================================================

def indicadores():

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT

            COUNT(*) total,

            SUM(
                CASE
                    WHEN estado='Activo'
                    THEN 1
                    ELSE 0
                END
            ) activos,

            SUM(
                CASE
                    WHEN disponible=1
                    THEN 1
                    ELSE 0
                END
            ) disponibles

        FROM profesionales

    """)

    datos = cursor.fetchone()

    conexion.close()

    return datos