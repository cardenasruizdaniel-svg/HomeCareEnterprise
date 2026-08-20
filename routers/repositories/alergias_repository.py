from database.database import get_connection


# ==========================================
# LISTAR ALERGIAS DE UN PACIENTE
# ==========================================

def listar(paciente_id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM alergias

        WHERE paciente_id = ?

        ORDER BY fecha_registro DESC

    """, (paciente_id,))

    datos = cursor.fetchall()

    conexion.close()

    return datos


# ==========================================
# LISTAR SOLO ACTIVAS
# ==========================================

def listar_activas(paciente_id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM alergias

        WHERE paciente_id = ?

        AND estado='Activa'

        ORDER BY severidad DESC,
                 fecha_registro DESC

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

        FROM alergias

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

    alergeno,

    severidad,

    estado,

    reaccion,

    observaciones,

    fecha_diagnostico,

    usuario

):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        INSERT INTO alergias(

            paciente_id,

            tipo,

            alergeno,

            severidad,

            estado,

            reaccion,

            observaciones,

            fecha_diagnostico,

            usuario_creacion

        )

        VALUES(

            ?,?,?,?,?,?,?,?,?

        )

    """, (

        paciente_id,

        tipo,

        alergeno,

        severidad,

        estado,

        reaccion,

        observaciones,

        fecha_diagnostico,

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

    alergeno,

    severidad,

    estado,

    reaccion,

    observaciones,

    fecha_diagnostico,

    usuario

):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE alergias

        SET

            tipo=?,

            alergeno=?,

            severidad=?,

            estado=?,

            reaccion=?,

            observaciones=?,

            fecha_diagnostico=?,

            usuario_actualizacion=?,

            fecha_actualizacion=CURRENT_TIMESTAMP

        WHERE id=?

    """, (

        tipo,

        alergeno,

        severidad,

        estado,

        reaccion,

        observaciones,

        fecha_diagnostico,

        usuario,

        id

    ))

    conexion.commit()

    conexion.close()


# ==========================================
# CAMBIAR ESTADO
# ==========================================

def cambiar_estado(id, estado):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE alergias

        SET

            estado=?,

            fecha_actualizacion=CURRENT_TIMESTAMP

        WHERE id=?

    """, (

        estado,

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

        FROM alergias

        WHERE id=?

    """, (id,))

    conexion.commit()

    conexion.close()