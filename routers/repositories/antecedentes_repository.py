from database.database import get_connection


# ==========================================
# LISTAR ANTECEDENTES
# ==========================================

def listar(paciente_id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM antecedentes

        WHERE paciente_id=?

        ORDER BY fecha_creacion DESC

    """, (paciente_id,))

    datos = cursor.fetchall()

    conexion.close()

    return datos


# ==========================================
# OBTENER POR ID
# ==========================================

def obtener(id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM antecedentes

        WHERE id=?

    """, (id,))

    dato = cursor.fetchone()

    conexion.close()

    return dato


# ==========================================
# CREAR
# ==========================================

def crear(

    paciente_id,

    tipo,

    descripcion,

    observaciones,

    usuario

):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        INSERT INTO antecedentes(

            paciente_id,

            tipo,

            descripcion,

            observaciones,

            usuario_creacion

        )

        VALUES(

            ?,?,?,?,?

        )

    """, (

        paciente_id,

        tipo,

        descripcion,

        observaciones,

        usuario

    ))

    conexion.commit()

    conexion.close()


# ==========================================
# ACTUALIZAR
# ==========================================

def actualizar(

    id,

    tipo,

    descripcion,

    observaciones,

    usuario

):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE antecedentes

        SET

            tipo=?,

            descripcion=?,

            observaciones=?,

            usuario_actualizacion=?,

            fecha_actualizacion=CURRENT_TIMESTAMP

        WHERE id=?

    """, (

        tipo,

        descripcion,

        observaciones,

        usuario,

        id

    ))

    conexion.commit()

    conexion.close()


# ==========================================
# ELIMINAR
# ==========================================

def eliminar(id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        DELETE

        FROM antecedentes

        WHERE id=?

    """, (id,))

    conexion.commit()

    conexion.close()