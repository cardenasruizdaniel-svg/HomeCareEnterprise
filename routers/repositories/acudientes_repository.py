from database.database import get_connection


# ==========================================
# LISTAR ACUDIENTES DE UN PACIENTE
# ==========================================

def listar_por_paciente(paciente_id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM acudientes

        WHERE paciente_id=?
          AND estado='Activo'

        ORDER BY es_principal DESC,
                 nombre

    """, (paciente_id,))

    datos = cursor.fetchall()

    conexion.close()

    return datos

# ==========================================
# OBTENER ACUDIENTE
# ==========================================

def obtener(id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM acudientes

        WHERE id=?

    """, (id,))

    dato = cursor.fetchone()

    conexion.close()

    return dato


# ==========================================
# CREAR ACUDIENTE
# ==========================================

def crear(

    paciente_id,
    nombre,
    tipo_documento,
    documento,
    parentesco,
    telefono_principal,
    telefono_secundario,
    correo,
    direccion,
    barrio,
    municipio,
    departamento,
    ciudad,
    ocupacion,
    observaciones,
    es_principal,
    autoriza_decisiones,
    recibe_informacion

):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        INSERT INTO acudientes(

            paciente_id,
            nombre,
            tipo_documento,
            documento,
            parentesco,
            telefono_principal,
            telefono_secundario,
            correo,
            direccion,
            barrio,
            municipio,
            departamento,
            ciudad,
            ocupacion,
            observaciones,
            es_principal,
            autoriza_decisiones,
            recibe_informacion

        )

        VALUES(

            ?,?,?,?,?,?,
            ?,?,?,?,?,?,
            ?,?,?,?,?,?

        )

    """, (

        paciente_id,
        nombre,
        tipo_documento,
        documento,
        parentesco,
        telefono_principal,
        telefono_secundario,
        correo,
        direccion,
        barrio,
        municipio,
        departamento,
        ciudad,
        ocupacion,
        observaciones,
        es_principal,
        autoriza_decisiones,
        recibe_informacion

    ))

    conexion.commit()
    conexion.close()


# ==========================================
# ACTUALIZAR
# ==========================================

def actualizar(

    id,
    nombre,
    tipo_documento,
    documento,
    parentesco,
    telefono_principal,
    telefono_secundario,
    correo,
    direccion,
    barrio,
    municipio,
    departamento,
    ciudad,
    ocupacion,
    observaciones,
    es_principal,
    autoriza_decisiones,
    recibe_informacion

):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE acudientes

        SET

            nombre=?,
            tipo_documento=?,
            documento=?,
            parentesco=?,
            telefono_principal=?,
            telefono_secundario=?,
            correo=?,
            direccion=?,
            barrio=?,
            municipio=?,
            departamento=?,
            ciudad=?,
            ocupacion=?,
            observaciones=?,
            es_principal=?,
            autoriza_decisiones=?,
            recibe_informacion=?,
            fecha_actualizacion=CURRENT_TIMESTAMP

        WHERE id=?

    """, (

        nombre,
        tipo_documento,
        documento,
        parentesco,
        telefono_principal,
        telefono_secundario,
        correo,
        direccion,
        barrio,
        municipio,
        departamento,
        ciudad,
        ocupacion,
        observaciones,
        es_principal,
        autoriza_decisiones,
        recibe_informacion,
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

        UPDATE acudientes

        SET estado='Inactivo'

        WHERE id=?

    """, (id,))

    conexion.commit()
    conexion.close()


# ==========================================
# DEFINIR ACUDIENTE PRINCIPAL
# ==========================================

def establecer_principal(id, paciente_id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE acudientes

        SET es_principal=0

        WHERE paciente_id=?

    """, (paciente_id,))

    cursor.execute("""

        UPDATE acudientes

        SET es_principal=1

        WHERE id=?

    """, (id,))

    conexion.commit()
    conexion.close()