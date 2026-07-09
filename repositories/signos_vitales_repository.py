from database.database import get_connection


# =====================================================
# LISTAR POR PACIENTE
# =====================================================

def listar_por_paciente(paciente_id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM signos_vitales

        WHERE paciente_id = ?

        ORDER BY fecha DESC,
                 hora DESC,
                 id DESC

    """, (paciente_id,))

    datos = cursor.fetchall()

    conexion.close()

    return datos


# =====================================================
# OBTENER
# =====================================================

def obtener(id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM signos_vitales

        WHERE id = ?

    """, (id,))

    dato = cursor.fetchone()

    conexion.close()

    return dato


# =====================================================
# OBTENER ÚLTIMO REGISTRO
# =====================================================

def obtener_ultimo(paciente_id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM signos_vitales

        WHERE paciente_id = ?

        ORDER BY fecha DESC,
                 hora DESC,
                 id DESC

        LIMIT 1

    """, (paciente_id,))

    dato = cursor.fetchone()

    conexion.close()

    return dato


# =====================================================
# CREAR
# =====================================================

def crear(

    paciente_id,
    profesional,
    fecha,
    hora,
    temperatura,
    presion_sistolica,
    presion_diastolica,
    frecuencia_cardiaca,
    frecuencia_respiratoria,
    saturacion_oxigeno,
    glucemia,
    peso,
    talla,
    imc,
    dolor,
    observaciones,
    usuario_creacion,
    fecha_creacion

):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        INSERT INTO signos_vitales(

            paciente_id,

            profesional,

            fecha,

            hora,

            temperatura,

            presion_sistolica,

            presion_diastolica,

            frecuencia_cardiaca,

            frecuencia_respiratoria,

            saturacion_oxigeno,

            glucemia,

            peso,

            talla,

            imc,

            dolor,

            observaciones,

            usuario_creacion,

            fecha_creacion

        )

        VALUES(

            ?,?,?,?,?,?,?,?,?,?,
            ?,?,?,?,?,?,?,?

        )

    """,(

        paciente_id,

        profesional,

        fecha,

        hora,

        temperatura,

        presion_sistolica,

        presion_diastolica,

        frecuencia_cardiaca,

        frecuencia_respiratoria,

        saturacion_oxigeno,

        glucemia,

        peso,

        talla,

        imc,

        dolor,

        observaciones,

        usuario_creacion,

        fecha_creacion

    ))

    nuevo_id = cursor.lastrowid

    conexion.commit()

    conexion.close()

    return nuevo_id


# =====================================================
# ACTUALIZAR
# =====================================================

def actualizar(

    id,

    profesional,

    fecha,

    hora,

    temperatura,

    presion_sistolica,

    presion_diastolica,

    frecuencia_cardiaca,

    frecuencia_respiratoria,

    saturacion_oxigeno,

    glucemia,

    peso,

    talla,

    imc,

    dolor,

    observaciones,

    fecha_actualizacion

):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE signos_vitales

        SET

            profesional=?,

            fecha=?,

            hora=?,

            temperatura=?,

            presion_sistolica=?,

            presion_diastolica=?,

            frecuencia_cardiaca=?,

            frecuencia_respiratoria=?,

            saturacion_oxigeno=?,

            glucemia=?,

            peso=?,

            talla=?,

            imc=?,

            dolor=?,

            observaciones=?,

            fecha_actualizacion=?

        WHERE id=?

    """,(

        profesional,

        fecha,

        hora,

        temperatura,

        presion_sistolica,

        presion_diastolica,

        frecuencia_cardiaca,

        frecuencia_respiratoria,

        saturacion_oxigeno,

        glucemia,

        peso,

        talla,

        imc,

        dolor,

        observaciones,

        fecha_actualizacion,

        id

    ))

    conexion.commit()

    conexion.close()


# =====================================================
# ELIMINAR
# =====================================================

def eliminar(id):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        DELETE

        FROM signos_vitales

        WHERE id=?

    """, (id,))

    conexion.commit()

    conexion.close()


# =====================================================
# HISTÓRICO POR RANGO
# =====================================================

def listar_por_rango(

    paciente_id,

    fecha_inicio,

    fecha_fin

):

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM signos_vitales

        WHERE paciente_id = ?

        AND fecha BETWEEN ? AND ?

        ORDER BY fecha,
                 hora

    """,(

        paciente_id,

        fecha_inicio,

        fecha_fin

    ))

    datos = cursor.fetchall()

    conexion.close()

    return datos