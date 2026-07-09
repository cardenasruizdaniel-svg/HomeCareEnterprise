"""
=========================================================
HomeCare Enterprise
Servicio: Turnos programados

Valida los turnos REPORTADOS (marcacion real de ingreso y
salida en las visitas) contra los turnos ASIGNADOS en el
calendario, para detectar: turnos sin marcacion (ausencia),
marcaciones sin turno asignado, y desviaciones de horario.
=========================================================
"""

from datetime import datetime, timedelta

from repositories.turnos_repository import CatalogoTurnosRepository, TurnosRepository

TOLERANCIA_MINUTOS = 30


# ==========================================================
# CATÁLOGO DE TURNOS (patrones de horario reutilizables)
# ==========================================================

def listar_catalogo_turnos():
    return [dict(t) for t in CatalogoTurnosRepository.listar_activos()]


def crear_turno_catalogo(nombre, tramo1_inicio, tramo1_fin, tramo2_inicio, tramo2_fin, tipo_cuidado_aplica) -> int:
    if not nombre or not tramo1_inicio or not tramo1_fin:
        raise ValueError("Debe indicar el nombre del turno y al menos un tramo de horario.")

    return CatalogoTurnosRepository.crear({
        "nombre": nombre,
        "tramo1_inicio": tramo1_inicio, "tramo1_fin": tramo1_fin,
        "tramo2_inicio": tramo2_inicio or None, "tramo2_fin": tramo2_fin or None,
        "tipo_cuidado_aplica": tipo_cuidado_aplica or "Ambos",
    })


def desactivar_turno_catalogo(turno_id: int):
    CatalogoTurnosRepository.desactivar(turno_id)


# ==========================================================
# ASIGNACIÓN MASIVA DE TURNOS A UN PACIENTE
# (día a día, toda la semana, o todo el mes)
# ==========================================================

DIAS_SEMANA_ISO = {
    "lunes": 1, "martes": 2, "miercoles": 3, "miércoles": 3, "jueves": 4,
    "viernes": 5, "sabado": 6, "sábado": 6, "domingo": 7,
}


def asignar_turno_paciente(paciente_id, profesional_id, catalogo_turno_id, fecha_inicio, fecha_fin,
                             dias_semana, zona, observaciones, usuario) -> dict:
    """
    Genera, para un paciente, uno o varios turnos (segun el
    patron del catalogo) entre fecha_inicio y fecha_fin. Si el
    turno del catalogo tiene dos tramos (ej. partido 8-12 y
    2-6), se crean AMBOS tramos cada dia. Si se indican
    dias_semana (ej. ["lunes","miercoles","viernes"]), solo se
    generan esos dias; si se deja vacio, se generan TODOS los
    dias del rango (util para "todo el mes" o "toda la semana").
    """

    turno_catalogo = CatalogoTurnosRepository.obtener(catalogo_turno_id)
    if not turno_catalogo:
        raise ValueError("El turno seleccionado no existe en el catálogo.")
    turno_catalogo = dict(turno_catalogo)

    if not fecha_inicio or not fecha_fin:
        raise ValueError("Debe indicar la fecha de inicio y la fecha de fin.")

    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    if fin < inicio:
        raise ValueError("La fecha de fin no puede ser anterior a la fecha de inicio.")

    dias_permitidos = None
    if dias_semana:
        dias_permitidos = {DIAS_SEMANA_ISO[d.strip().lower()] for d in dias_semana if d.strip().lower() in DIAS_SEMANA_ISO}

    tramos = [(turno_catalogo["tramo1_inicio"], turno_catalogo["tramo1_fin"])]
    if turno_catalogo.get("tramo2_inicio") and turno_catalogo.get("tramo2_fin"):
        tramos.append((turno_catalogo["tramo2_inicio"], turno_catalogo["tramo2_fin"]))

    creados = 0
    actual = inicio

    while actual <= fin:
        if dias_permitidos is None or actual.isoweekday() in dias_permitidos:
            for hora_inicio, hora_fin in tramos:
                TurnosRepository.crear({
                    "profesional_id": profesional_id,
                    "paciente_id": paciente_id,
                    "catalogo_turno_id": catalogo_turno_id,
                    "fecha": actual.isoformat(),
                    "turno": turno_catalogo["nombre"],
                    "hora_inicio": hora_inicio,
                    "hora_fin": hora_fin,
                    "zona": zona or "",
                    "observaciones": observaciones or "",
                    "usuario_creacion": usuario,
                })
                creados += 1
        actual += timedelta(days=1)

    return {"turnos_creados": creados, "turno_nombre": turno_catalogo["nombre"]}


def listar_turnos_de_paciente(paciente_id: int, fecha_inicio: str, fecha_fin: str):
    return [dict(t) for t in TurnosRepository.listar_por_paciente(paciente_id, fecha_inicio, fecha_fin)]


def listar_calendario_con_paciente(fecha_inicio: str, fecha_fin: str):
    return [dict(t) for t in TurnosRepository.listar_rango_con_paciente(fecha_inicio, fecha_fin)]


def listar_calendario(fecha_inicio: str, fecha_fin: str):
    return TurnosRepository.listar_rango(fecha_inicio, fecha_fin)


def crear_turno(profesional_id, fecha, turno, hora_inicio, hora_fin, zona, observaciones, usuario):
    return TurnosRepository.crear({
        "profesional_id": profesional_id,
        "fecha": fecha,
        "turno": turno,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "zona": zona,
        "observaciones": observaciones,
        "usuario_creacion": usuario,
    })


def eliminar_turno(turno_id):
    return TurnosRepository.eliminar(turno_id)


def _minutos(hora_str: str) -> int:
    h, m = hora_str.split(":")[:2]
    return int(h) * 60 + int(m)


def validar_turnos_periodo(profesional_id: int, fecha_inicio: str, fecha_fin: str) -> list:
    """
    Compara, dia a dia, los turnos asignados contra las
    visitas realmente marcadas (ingreso/salida) por el
    profesional, y devuelve un reporte de cumplimiento.
    """

    turnos = TurnosRepository.listar_por_profesional(profesional_id, fecha_inicio, fecha_fin)

    resultado = []

    for t in turnos:
        t = dict(t)

        visitas = TurnosRepository.visitas_del_profesional_en_fecha(profesional_id, t["fecha"])

        if not visitas:
            resultado.append({
                **t,
                "cumplimiento": "Ausente",
                "detalle": "No se registró ingreso a labores en la fecha del turno.",
            })
            continue

        turno_inicio_min = _minutos(t["hora_inicio"])

        mejor = min(
            visitas,
            key=lambda v: abs(
                _minutos(datetime.strptime(v["hora_real_inicio"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M"))
                - turno_inicio_min
            ),
        )

        real_inicio_min = _minutos(
            datetime.strptime(mejor["hora_real_inicio"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
        )

        diferencia = real_inicio_min - turno_inicio_min

        if abs(diferencia) <= TOLERANCIA_MINUTOS:
            cumplimiento = "A tiempo"
            detalle = f"Ingreso registrado a las {mejor['hora_real_inicio'][11:16]}."
        elif diferencia > TOLERANCIA_MINUTOS:
            cumplimiento = "Tarde"
            detalle = f"Llegó {diferencia} minutos tarde ({mejor['hora_real_inicio'][11:16]})."
        else:
            cumplimiento = "Anticipado"
            detalle = f"Llegó {abs(diferencia)} minutos antes ({mejor['hora_real_inicio'][11:16]})."

        resultado.append({
            **t,
            "cumplimiento": cumplimiento,
            "detalle": detalle,
            "visita_id": mejor["id"],
        })

    return resultado
