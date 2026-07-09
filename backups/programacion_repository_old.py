from database.database import get_connection


# ==========================================
# LISTAR TODAS LAS VISITAS
# ==========================================

def listar():

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT
            p.*,
            pa.nombre AS paciente,
            pr.nombre AS profesional

        FROM programaciones p

        LEFT JOIN pacientes pa
            ON pa.id = p.paciente_id

        LEFT JOIN profesionales pr
            ON pr.id = p.profesional_id

        ORDER BY fecha,hora_inicio

    """)

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

        FROM programaciones

        WHERE id=?

    """,(id,))

    dato = cursor.fetchone()

    conexion.close()

    return dato


# ==========================================
# AGENDA DEL DÍA
# ==========================================

def agenda_dia(fecha):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM programaciones

        WHERE fecha=?

        ORDER BY hora_inicio

    """,(fecha,))

    datos = cursor.fetchall()

    conexion.close()

    return datos


# ==========================================
# AGENDA PROFESIONAL
# ==========================================

def agenda_profesional(profesional_id,fecha):

    conexion=get_connection()

    cursor=conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM programaciones

        WHERE profesional_id=?

        AND fecha=?

        ORDER BY hora_inicio

    """,(profesional_id,fecha))

    datos=cursor.fetchall()

    conexion.close()

    return datos


# ==========================================
# AGENDA PACIENTE
# ==========================================

def agenda_paciente(paciente_id):

    conexion=get_connection()

    cursor=conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM programaciones

        WHERE paciente_id=?

        ORDER BY fecha DESC

    """,(paciente_id,))

    datos=cursor.fetchall()

    conexion.close()

    return datos


# ==========================================
# VISITAS PENDIENTES
# ==========================================

def pendientes():

    conexion=get_connection()

    cursor=conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM programaciones

        WHERE estado='Programada'

        ORDER BY fecha,hora_inicio

    """)

    datos=cursor.fetchall()

    conexion.close()

    return datos


# ==========================================
# CREAR VISITA
# ==========================================

def crear(

    paciente_id,

    profesional_id,

    diagnostico_id,

    fecha,

    hora_inicio,

    hora_fin,

    duracion,

    servicio,

    procedimiento,

    prioridad,

    direccion,

    barrio,

    ciudad,

    departamento,

    telefono_contacto,

    nombre_contacto,

    observaciones,

    usuario

):

    conexion=get_connection()

    cursor=conexion.cursor()

    cursor.execute("""

        INSERT INTO programaciones(

            paciente_id,

            profesional_id,

            diagnostico_id,

            fecha,

            hora_inicio,

            hora_fin,

            duracion,

            servicio,

            procedimiento,

            prioridad,

            direccion,

            barrio,

            ciudad,

            departamento,

            telefono_contacto,

            nombre_contacto,

            observaciones,

            usuario_creacion

        )

        VALUES(

            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?

        )

    """,(

        paciente_id,

        profesional_id,

        diagnostico_id,

        fecha,

        hora_inicio,

        hora_fin,

        duracion,

        servicio,

        procedimiento,

        prioridad,

        direccion,

        barrio,

        ciudad,

        departamento,

        telefono_contacto,

        nombre_contacto,

        observaciones,

        usuario

    ))

    conexion.commit()

    conexion.close()


# ==========================================
# CAMBIAR ESTADO
# ==========================================

def cambiar_estado(id,estado):

    conexion=get_connection()

    cursor=conexion.cursor()

    cursor.execute("""

        UPDATE programaciones

        SET

            estado=?,

            fecha_actualizacion=CURRENT_TIMESTAMP

        WHERE id=?

    """,(estado,id))

    conexion.commit()

    conexion.close()


# ==========================================
# ELIMINAR
# ==========================================

def eliminar(id):

    conexion=get_connection()

    cursor=conexion.cursor()

    cursor.execute("""

        DELETE

        FROM programaciones

        WHERE id=?

    """,(id,))

    conexion.commit()

    conexion.close()