"""
=========================================================
HomeCare Enterprise
Repositorio: Alertas clinicas al ingresar a un paciente
=========================================================
"""

from database.database import get_connection


# ==========================================
# ALERGIAS ACTIVAS (medicamentos, alimentos, etc.)
# ==========================================

def obtener_alergias(paciente_id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT
            tipo,
            alergeno,
            severidad,
            reaccion
        FROM alergias
        WHERE paciente_id=?
        AND estado='Activa'
        ORDER BY
            CASE severidad
                WHEN 'Anafilaxia' THEN 1
                WHEN 'Grave' THEN 2
                WHEN 'Moderada' THEN 3
                ELSE 4
            END

    """, (paciente_id,))

    datos = cursor.fetchall()
    conexion.close()
    return datos


# ==========================================
# MEDICAMENTOS ACTIVOS (que el paciente está tomando)
# ==========================================

def obtener_medicamentos_activos(paciente_id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT
            nombre,
            principio_activo,
            dosis,
            frecuencia,
            via
        FROM medicamentos
        WHERE paciente_id=?
        AND estado='ACTIVO'
        ORDER BY fecha_inicio DESC

    """, (paciente_id,))

    datos = cursor.fetchall()
    conexion.close()
    return datos


# ==========================================
# DIAGNÓSTICOS
# ==========================================

def obtener_diagnosticos(paciente_id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT
            codigo_cie10,
            diagnostico
        FROM diagnosticos
        WHERE paciente_id=?
        AND estado='Activo'
        ORDER BY fecha_diagnostico DESC

    """, (paciente_id,))

    datos = cursor.fetchall()
    conexion.close()
    return datos


# ==========================================
# PRÓXIMA VISITA
# ==========================================

def obtener_proxima_visita(paciente_id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT
            fecha,
            hora_inicio
        FROM programaciones
        WHERE paciente_id=?
        AND estado='Programada'
        ORDER BY fecha, hora_inicio
        LIMIT 1

    """, (paciente_id,))

    dato = cursor.fetchone()
    conexion.close()
    return dato
