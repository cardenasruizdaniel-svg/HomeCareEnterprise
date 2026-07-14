"""
HomeCare Enterprise - Servicios/actividades asignadas al paciente

Permite indicar que actividades necesita un paciente (del
mismo catalogo unificado que se usa en "Programa de Atención":
ver catalogo_actividades), cuantas sesiones, el rango de
fechas, y si al terminarse las sesiones el servicio se debe
RENOVAR automaticamente de forma indefinida o simplemente
detenerse.

IMPORTANTE (flujo de tentativa -> programada): al asignar la
actividad, el sistema SOLO genera fechas TENTATIVAS (en la
planilla de visitas), sin tocar todavia la agenda real. Cada
visita tentativa debe programarse explicitamente (ver
services/gestion_visitas_service.py) para quedar en la agenda
del profesional y disparar las alertas -- esto permite elegir
la fecha exacta de cada visita antes de confirmarla.
"""

from datetime import date, datetime, timedelta

from database.database import consultar_todos, consultar_uno, ejecutar
from repositories.servicios_paciente_repository import ServiciosPacienteRepository

# Cada frecuencia se traduce a un intervalo de dias entre una
# sesion y la siguiente, para generar las fechas tentativas.
INTERVALO_DIAS_POR_FRECUENCIA = {
    "Diaria": 1,
    "Interdiaria": 2,
    "1 vez por semana": 7,
    "2 veces por semana": 3,
    "3 veces por semana": 2,
    "Cada 8 días": 8,
    "Cada 15 días": 15,
    "Cada 20 días": 20,
    "1 vez al mes": 30,
    # Estas cuatro son distintas a las de arriba: en vez de
    # espaciar los DÍAS entre una visita y otra, reparten VARIAS
    # visitas dentro del MISMO día -- para el caso de aplicación
    # de medicamentos o sueros, donde el paciente puede necesitar
    # que le apliquen 1, 2, 3 o hasta 4 veces al día. El número
    # de sesiones que se indique sigue siendo el total de
    # visitas a programar (no de días).
    "2 veces al día": 1,
    "3 veces al día": 1,
    "4 veces al día": 1,
}

FRECUENCIAS_VALIDAS = list(INTERVALO_DIAS_POR_FRECUENCIA.keys())

# Franjas horarias por defecto para cada visita del mismo día,
# cuando la frecuencia es "N veces al día" -- pensadas para
# aplicación de medicamentos/sueros (espaciadas parejo a lo
# largo del día). Se pueden ajustar luego visita por visita
# desde "Programar ahora", esto solo define el punto de partida.
HORARIOS_POR_FRECUENCIA_DIARIA = {
    "2 veces al día": [("07:00", "08:00"), ("19:00", "20:00")],
    "3 veces al día": [("07:00", "08:00"), ("13:00", "14:00"), ("19:00", "20:00")],
    "4 veces al día": [("06:00", "07:00"), ("12:00", "13:00"), ("18:00", "19:00"), ("00:00", "01:00")],
}


def listar_por_paciente(paciente_id: int):
    return [dict(s) for s in ServiciosPacienteRepository.listar_por_paciente(paciente_id)]


def obtener(servicio_id: int):
    return ServiciosPacienteRepository.obtener(servicio_id)


def _generar_fechas(fecha_inicio: str, fecha_fin: str, frecuencia: str, numero_sesiones=None,
                      hora_inicio=None, hora_fin=None) -> list:
    """
    Devuelve la lista de visitas a crear, como tuplas
    (fecha, hora_inicio, hora_fin) -- para las frecuencias
    normales, hay una visita por fecha con el horario indicado;
    para las de "N veces al día", cada fecha aparece varias
    veces con las franjas horarias correspondientes (mañana,
    tarde, noche, etc.), hasta completar el número de sesiones
    pedido.
    """

    if frecuencia not in INTERVALO_DIAS_POR_FRECUENCIA:
        raise ValueError(f"Frecuencia no válida. Use una de: {', '.join(FRECUENCIAS_VALIDAS)}")

    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()

    if fecha_fin:
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        if fin < inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la fecha de inicio.")
    else:
        fin = date(2100, 1, 1)  # sin límite real; se corta por numero_sesiones

    if not fecha_fin and not numero_sesiones:
        raise ValueError("Debe indicar la fecha de fin o el número de sesiones.")

    visitas = []

    if frecuencia in HORARIOS_POR_FRECUENCIA_DIARIA:
        franjas = HORARIOS_POR_FRECUENCIA_DIARIA[frecuencia]
        actual = inicio
        while actual <= fin:
            if numero_sesiones and len(visitas) >= numero_sesiones:
                break
            for hi, hf in franjas:
                if numero_sesiones and len(visitas) >= numero_sesiones:
                    break
                visitas.append((actual.isoformat(), hi, hf))
            actual += timedelta(days=1)
        return visitas

    intervalo = INTERVALO_DIAS_POR_FRECUENCIA[frecuencia]
    actual = inicio
    while actual <= fin:
        if numero_sesiones and len(visitas) >= numero_sesiones:
            break
        visitas.append((actual.isoformat(), hora_inicio or "08:00", hora_fin or "09:00"))
        actual += timedelta(days=intervalo)

    return visitas


def asignar_servicio(paciente_id, tipo_servicio, subtipo, profesional_id, frecuencia,
                       fecha_inicio, fecha_fin, hora_inicio, hora_fin, indicaciones, usuario,
                       actividad_id=None, numero_sesiones=None, paciente_programa_id=None,
                       renovacion_automatica=False) -> dict:

    if actividad_id:
        # Ruta principal: el nombre del servicio se toma del
        # catalogo unificado de actividades.
        actividad = consultar_uno("SELECT nombre FROM catalogo_actividades WHERE id=?", (actividad_id,))
        if not actividad:
            raise ValueError("La actividad seleccionada no existe.")
        tipo_servicio = dict(actividad)["nombre"]
        subtipo = None

    if not tipo_servicio:
        raise ValueError("Debe seleccionar el servicio/actividad.")

    if frecuencia not in FRECUENCIAS_VALIDAS:
        raise ValueError(f"Frecuencia no válida. Use una de: {', '.join(FRECUENCIAS_VALIDAS)}")

    # Protección contra duplicados: si por un doble clic, doble
    # envío del formulario, o un reintento de red ya se creó
    # HACE UN MOMENTO (últimos 15 segundos) un servicio
    # identico para este mismo paciente, no se vuelve a crear
    # -- se devuelve el que ya existe, en vez de generar una
    # fila repetida.
    reciente = consultar_uno(
        """
        SELECT id, numero_sesiones FROM servicios_paciente
        WHERE paciente_id=? AND tipo_servicio=? AND fecha_inicio=? AND estado='Activo'
          AND datetime(fecha_creacion) >= datetime('now', '-15 seconds')
        ORDER BY id DESC LIMIT 1
        """,
        (paciente_id, tipo_servicio, fecha_inicio),
    )
    if reciente:
        reciente = dict(reciente)
        return {
            "servicio_id": reciente["id"],
            "total_fechas": reciente["numero_sesiones"] or 0,
            "visitas_creadas": 0,
            "duplicado_evitado": True,
        }

    fecha_fin_guardar = fecha_fin

    # El servicio de CUIDADOR es distinto a todos los demás: el
    # médico solo indica CUÁNTAS sesiones/días necesita el
    # paciente (la meta), pero NO a qué hora ni con qué
    # cuidador exacto -- porque ese servicio puede ser en la
    # mañana, en la tarde, en ambas, o incluso por turnos de
    # 24 horas con varios cuidadores distintos rotando. Esa
    # parte se decide después, desde la oficina, en
    # Programación Mensual -- así que aquí NO se generan fechas
    # ni visitas tentativas todavía, solo se deja la actividad
    # asignada con la meta de sesiones para que la oficina sepa
    # cuánto tiene que programarle.
    es_cuidador = (tipo_servicio or "").strip().lower() == "cuidador"

    if es_cuidador:
        fechas = []
        fecha_fin_guardar = fecha_fin_guardar or ""
    else:
        fechas = _generar_fechas(fecha_inicio, fecha_fin, frecuencia, numero_sesiones, hora_inicio, hora_fin)
        # Si no se indico fecha de fin a mano, se calcula una de
        # REFERENCIA automaticamente (la fecha de la ultima sesion
        # generada, segun el numero de sesiones y la periodicidad),
        # para que quede un dato util en pantalla sin obligar al
        # usuario a calcularla el mismo. Igual se puede modificar
        # despues si se indica una fecha de fin manual.
        fecha_fin_guardar = fecha_fin_guardar or (fechas[-1][0] if fechas else "")

    servicio_id = ServiciosPacienteRepository.crear({
        "paciente_id": paciente_id,
        "tipo_servicio": tipo_servicio,
        "subtipo": subtipo or None,
        "profesional_id": profesional_id or None,
        "frecuencia": frecuencia,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin_guardar,
        "hora_inicio": hora_inicio or "08:00",
        "hora_fin": hora_fin or "09:00",
        "indicaciones": indicaciones or "",
        "usuario_creacion": usuario,
    })

    ejecutar(
        "UPDATE servicios_paciente SET actividad_id=?, numero_sesiones=?, paciente_programa_id=?, "
        "renovacion_automatica=? WHERE id=?",
        (actividad_id, numero_sesiones, paciente_programa_id, 1 if renovacion_automatica else 0, servicio_id),
    )

    # Todas las visitas quedan TENTATIVAS (Pendiente): no se
    # toca la agenda real todavia. Se guarda el profesional
    # planeado (si ya se sabe cual va a ser) para agilizar el
    # paso de "Programar" mas adelante. Cada tupla trae su
    # propia hora (para "N veces al día", cada visita del mismo
    # día tiene una franja horaria distinta).
    for fecha, hi, hf in fechas:
        ejecutar(
            """
            INSERT INTO planilla_visitas(
                servicio_paciente_id, paciente_id, fecha, hora_inicio, hora_fin,
                profesional_id, estado
            ) VALUES (?, ?, ?, ?, ?, ?, 'Pendiente')
            """,
            (servicio_id, paciente_id, fecha, hi, hf, profesional_id or None),
        )

    return {
        "servicio_id": servicio_id,
        "total_fechas": len(fechas),
        "visitas_creadas": 0,  # ya no se crean automaticamente; se programan una a una
        "es_cuidador": es_cuidador,
        "mensaje": (
            f"Se asignó la actividad de Cuidador con una meta de {numero_sesiones or 0} sesión(es)/día(s). "
            "Las fechas, horarios y el cuidador específico se programan desde la oficina en Programación Mensual."
            if es_cuidador else None
        ),
    }


def cancelar_servicio(servicio_id: int):
    ServiciosPacienteRepository.cambiar_estado(servicio_id, "Cancelado")

    # Cancela tambien todas las visitas tentativas/pendientes
    # que aun no se hayan programado.
    ejecutar(
        "UPDATE planilla_visitas SET estado='Cancelada', motivo_cancelacion='Servicio cancelado' "
        "WHERE servicio_paciente_id=? AND estado='Pendiente'",
        (servicio_id,),
    )


def listar_activos_por_profesional(profesional_id: int):
    return [dict(s) for s in ServiciosPacienteRepository.listar_activos_por_profesional(profesional_id)]


def renovar_si_corresponde(servicio_id: int):
    """
    Se llama cada vez que se firma/completa una visita. Si ya
    no quedan visitas pendientes ni programadas para este
    servicio (se agotaron las sesiones) y el servicio tiene
    marcada la renovacion automatica, genera un nuevo bloque
    de sesiones (misma frecuencia, hora y profesional),
    empezando el dia siguiente a la ultima visita -- de forma
    indefinida, hasta que alguien cancele el servicio a mano.
    """

    servicio = ServiciosPacienteRepository.obtener(servicio_id)
    if not servicio:
        return

    servicio = dict(servicio)

    if not servicio.get("renovacion_automatica") or servicio.get("estado") != "Activo":
        return

    pendientes_o_programadas = consultar_todos(
        "SELECT id FROM planilla_visitas WHERE servicio_paciente_id=? AND estado IN ('Pendiente', 'Programada')",
        (servicio_id,),
    )
    if pendientes_o_programadas:
        return  # aun quedan visitas por hacer, no toca renovar todavia

    ultima_fecha = consultar_uno(
        "SELECT MAX(fecha) AS ultima FROM planilla_visitas WHERE servicio_paciente_id=?",
        (servicio_id,),
    )
    ultima_fecha = dict(ultima_fecha)["ultima"] if ultima_fecha else None
    if not ultima_fecha:
        return

    intervalo = INTERVALO_DIAS_POR_FRECUENCIA.get(servicio["frecuencia"], 1)
    siguiente_inicio = (
        datetime.strptime(ultima_fecha, "%Y-%m-%d").date() + timedelta(days=intervalo)
    ).isoformat()

    numero_sesiones = servicio.get("numero_sesiones") or 10

    fechas = _generar_fechas(
        siguiente_inicio, None, servicio["frecuencia"], numero_sesiones,
        servicio["hora_inicio"], servicio["hora_fin"],
    )

    for fecha, hi, hf in fechas:
        ejecutar(
            """
            INSERT INTO planilla_visitas(
                servicio_paciente_id, paciente_id, fecha, hora_inicio, hora_fin,
                profesional_id, estado
            ) VALUES (?, ?, ?, ?, ?, ?, 'Pendiente')
            """,
            (servicio_id, servicio["paciente_id"], fecha, hi, hf,
             servicio.get("profesional_id")),
        )

    ejecutar(
        "UPDATE servicios_paciente SET fecha_inicio=?, fecha_fin=NULL WHERE id=?",
        (siguiente_inicio, servicio_id),
    )
