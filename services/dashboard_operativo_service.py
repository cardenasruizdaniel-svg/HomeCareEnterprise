"""
HomeCare Enterprise - Panel Operativo (Dashboard)

Complementa el dashboard ejecutivo con la operacion del dia a
dia que el coordinador necesita ver de un vistazo:

1. Pacientes con servicios ya asignados (programa/paquete)
   que todavia tienen visitas SIN PROGRAMAR.
2. Qué pacientes y qué servicios SI estan programados hoy.
3. Que profesional esta actualmente en una visita (ya marco
   ingreso, aun no marca salida), y quien acaba de terminar,
   con hora, fecha y si la ubicacion quedo verificada.
"""

from datetime import date

from database.database import consultar_todos


def visitas_no_realizadas_hoy():
    """
    Visitas de HOY que ya deberían haberse hecho (la hora
    programada ya pasó) pero nadie marcó que se completaran --
    ni tampoco se canceló. Es la señal de que algo no se
    cumplió y hay que revisar qué pasó.
    """
    from datetime import datetime

    ahora = datetime.now()
    hoy = ahora.date().isoformat()
    hora_actual = ahora.strftime("%H:%M")

    filas = consultar_todos(
        """
        SELECT
            p.id, p.hora_inicio, p.hora_fin, p.servicio, p.estado,
            (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente,
            pa.id AS paciente_id,
            pr.nombre_completo AS profesional
        FROM programaciones p
        JOIN pacientes pa ON pa.id = p.paciente_id
        LEFT JOIN profesionales pr ON pr.id = p.profesional_id
        WHERE p.fecha = ? AND p.eliminado = 0
          AND p.estado NOT IN ('Completada', 'Cancelada')
          AND p.hora_fin < ?
        ORDER BY p.hora_fin
        """,
        (hoy, hora_actual),
    )
    return [dict(f) for f in filas]


# Servicios donde perderse una visita programada es
# especialmente delicado (medicamentos, sueros, toma de
# muestras) -- se agrupan aparte para poder vigilarlos con más
# cuidado, con una ventana propia y alertas si no se cumplen.
SERVICIOS_CRITICOS = ("Aplicación de Medicamentos", "Aplicación de Sueros", "Toma y traslado de muestras de laboratorio")


def panel_servicios_criticos():
    """
    Ventana dedicada para el seguimiento de los servicios donde
    el horario importa mucho (aplicación de medicamentos,
    sueros, toma de muestras): qué está programado hoy, qué
    está en curso, qué ya se completó, y una alerta clara para
    lo que ya se pasó de hora sin haberse hecho.
    """
    from datetime import datetime

    ahora = datetime.now()
    hoy = ahora.date().isoformat()
    hora_actual = ahora.strftime("%H:%M")

    filas = consultar_todos(
        """
        SELECT
            p.id, p.hora_inicio, p.hora_fin, p.hora_real_inicio, p.hora_real_fin,
            p.servicio, p.estado,
            (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente,
            pa.id AS paciente_id,
            pr.nombre_completo AS profesional
        FROM programaciones p
        JOIN pacientes pa ON pa.id = p.paciente_id
        LEFT JOIN profesionales pr ON pr.id = p.profesional_id
        WHERE p.fecha = ? AND p.eliminado = 0 AND p.estado != 'Cancelada'
          AND p.servicio IN ({})
        ORDER BY p.hora_inicio
        """.format(",".join("?" * len(SERVICIOS_CRITICOS))),
        (hoy, *SERVICIOS_CRITICOS),
    )
    filas = [dict(f) for f in filas]

    programadas, en_curso, completadas, alertas = [], [], [], []
    for f in filas:
        if f["estado"] == "Completada":
            completadas.append(f)
        elif f["hora_real_inicio"] and not f["hora_real_fin"]:
            en_curso.append(f)
        elif f["hora_fin"] and f["hora_fin"] < hora_actual:
            alertas.append(f)
        else:
            programadas.append(f)

    return {
        "programadas": programadas, "en_curso": en_curso, "completadas": completadas, "alertas": alertas,
        "servicios_incluidos": list(SERVICIOS_CRITICOS),
    }


def servicios_con_visitas_sin_programar():
    """
    Por cada servicio/actividad activa de un paciente, cuenta
    cuantas de sus visitas siguen "Pendiente" (nunca se
    programo fecha/hora/profesional exacto). Solo devuelve los
    que SI tienen pendientes. Incluye el nombre del programa
    de atencion asignado (si el servicio viene de uno) y la
    fecha en que se asigno, para que quede explicito que ese
    paciente YA tiene programa y fechas, pero aun le faltan
    visitas por programar.
    """

    filas = consultar_todos(
        """
        SELECT
            sp.id AS servicio_id,
            sp.tipo_servicio,
            sp.subtipo,
            sp.fecha_inicio,
            (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente,
            pa.id AS paciente_id,
            pgm.nombre AS programa_nombre,
            pp.fecha_asignacion AS programa_fecha_asignacion,
            COUNT(pv.id) AS total_visitas,
            SUM(CASE WHEN pv.estado = 'Pendiente' THEN 1 ELSE 0 END) AS pendientes
        FROM servicios_paciente sp
        JOIN pacientes pa ON pa.id = sp.paciente_id
        LEFT JOIN planilla_visitas pv ON pv.servicio_paciente_id = sp.id
        LEFT JOIN paciente_programas pp ON pp.id = sp.paciente_programa_id
        LEFT JOIN programas_atencion pgm ON pgm.id = pp.programa_id
        WHERE sp.estado = 'Activo'
        GROUP BY sp.id
        HAVING pendientes > 0
        ORDER BY pendientes DESC
        """
    )

    return [dict(f) for f in filas]


def visitas_programadas_hoy():
    """Pacientes y servicios que SI quedaron programados para hoy."""

    hoy = date.today().isoformat()

    filas = consultar_todos(
        """
        SELECT
            p.id, p.hora_inicio, p.hora_fin, p.servicio, p.estado,
            (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente,
            pr.nombre_completo AS profesional
        FROM programaciones p
        JOIN pacientes pa ON pa.id = p.paciente_id
        LEFT JOIN profesionales pr ON pr.id = p.profesional_id
        WHERE p.fecha = ? AND p.eliminado = 0 AND p.estado != 'Cancelada'
        ORDER BY p.hora_inicio
        """,
        (hoy,),
    )

    return [dict(f) for f in filas]


def profesionales_en_visita_ahora():
    """
    Visitas de HOY donde ya se marco ingreso pero todavia no
    se ha marcado salida -- el profesional esta actualmente
    en el domicilio del paciente.
    """

    hoy = date.today().isoformat()

    filas = consultar_todos(
        """
        SELECT
            p.id, p.hora_real_inicio, p.servicio,
            p.geocerca_inicio_ok, p.distancia_inicio_metros,
            (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente,
            pr.nombre_completo AS profesional
        FROM programaciones p
        JOIN pacientes pa ON pa.id = p.paciente_id
        LEFT JOIN profesionales pr ON pr.id = p.profesional_id
        WHERE p.fecha = ?
          AND p.hora_real_inicio IS NOT NULL
          AND p.hora_real_fin IS NULL
          AND p.eliminado = 0
        ORDER BY p.hora_real_inicio DESC
        """,
        (hoy,),
    )

    return [dict(f) for f in filas]


def profesionales_que_finalizaron_hoy():
    """Visitas de HOY que ya se completaron (marcaron salida)."""

    hoy = date.today().isoformat()

    filas = consultar_todos(
        """
        SELECT
            p.id, p.hora_real_inicio, p.hora_real_fin, p.servicio, p.horas_trabajadas,
            p.geocerca_fin_ok, p.distancia_fin_metros,
            (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente,
            pr.nombre_completo AS profesional
        FROM programaciones p
        JOIN pacientes pa ON pa.id = p.paciente_id
        LEFT JOIN profesionales pr ON pr.id = p.profesional_id
        WHERE p.fecha = ?
          AND p.hora_real_fin IS NOT NULL
          AND p.eliminado = 0
        ORDER BY p.hora_real_fin DESC
        """,
        (hoy,),
    )

    return [dict(f) for f in filas]


def panel_operativo_completo():
    return {
        "servicios_sin_programar": servicios_con_visitas_sin_programar(),
        "visitas_hoy": visitas_programadas_hoy(),
        "en_visita_ahora": profesionales_en_visita_ahora(),
        "finalizaron_hoy": profesionales_que_finalizaron_hoy(),
        "no_realizadas_hoy": visitas_no_realizadas_hoy(),
        "servicios_criticos": panel_servicios_criticos(),
    }
