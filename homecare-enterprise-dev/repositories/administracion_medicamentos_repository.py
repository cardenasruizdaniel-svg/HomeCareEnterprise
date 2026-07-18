from database.database import get_connection


# ======================================================
# CREAR ADMINISTRACIÓN
# ======================================================

def crear(
    medicamento_id,
    paciente_id,
    fecha_programada,
    hora_programada,
    fecha_aplicacion,
    hora_aplicacion,
    profesional,
    estado,
    observaciones,
    firma_profesional,
    firma_paciente,
    usuario,
    fecha_registro
):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        INSERT INTO administracion_medicamentos(

            medicamento_id,
            paciente_id,
            fecha_programada,
            hora_programada,
            fecha_aplicacion,
            hora_aplicacion,
            profesional,
            estado,
            observaciones,
            firma_profesional,
            firma_paciente,
            usuario,
            fecha_registro

        )

        VALUES(

            ?,?,?,?,?,?,?,?,?,?,?,?,?

        )

    """,(

        medicamento_id,
        paciente_id,
        fecha_programada,
        hora_programada,
        fecha_aplicacion,
        hora_aplicacion,
        profesional,
        estado,
        observaciones,
        firma_profesional,
        firma_paciente,
        usuario,
        fecha_registro

    ))

    conexion.commit()

    conexion.close()


# ======================================================
# LISTAR POR PACIENTE
# ======================================================

def listar_por_paciente(paciente_id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM administracion_medicamentos

        WHERE paciente_id = ?

        ORDER BY fecha_programada DESC,
                 hora_programada DESC

    """,(paciente_id,))

    datos = cursor.fetchall()

    conexion.close()

    return datos


# ======================================================
# LISTAR POR MEDICAMENTO
# ======================================================

def listar_por_medicamento(medicamento_id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM administracion_medicamentos

        WHERE medicamento_id = ?

        ORDER BY fecha_programada DESC,
                 hora_programada DESC

    """,(medicamento_id,))

    datos = cursor.fetchall()

    conexion.close()

    return datos


# ======================================================
# OBTENER
# ======================================================

def obtener(id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM administracion_medicamentos

        WHERE id=?

    """,(id,))

    dato = cursor.fetchone()

    conexion.close()

    return dato


# ======================================================
# CAMBIAR ESTADO
# ======================================================

def cambiar_estado(id, estado):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE administracion_medicamentos

        SET estado=?

        WHERE id=?

    """,(estado,id))

    conexion.commit()

    conexion.close()


# ======================================================
# REGISTRAR APLICACIÓN
# ======================================================

def registrar_aplicacion(

    id,

    fecha_aplicacion,

    hora_aplicacion,

    profesional,

    observaciones,

    firma_profesional,

    firma_paciente

):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE administracion_medicamentos

        SET

            fecha_aplicacion=?,

            hora_aplicacion=?,

            profesional=?,

            observaciones=?,

            firma_profesional=?,

            firma_paciente=?,

            estado='Aplicado'

        WHERE id=?

    """,(

        fecha_aplicacion,

        hora_aplicacion,

        profesional,

        observaciones,

        firma_profesional,

        firma_paciente,

        id

    ))

    conexion.commit()

    conexion.close()


# ======================================================
# ELIMINAR
# ======================================================

def eliminar(id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        DELETE

        FROM administracion_medicamentos

        WHERE id=?

    """,(id,))

    conexion.commit()

    conexion.close()