"""
=========================================================
HomeCare Enterprise
Clasificacion de horas trabajadas para liquidar nomina por
horas segun la legislacion laboral colombiana.

Toma el ingreso y la salida REALES de una visita (marcados
por el profesional en el domicilio del paciente) y separa
las horas en los conceptos que exige el Codigo Sustantivo
del Trabajo: ordinaria diurna, ordinaria nocturna, dominical/
festiva diurna, dominical/festiva nocturna, y las horas que
exceden la jornada ordinaria diaria (extra).

Simplificacion asumida: se calculan horas extra por turno
individual que supere las 8 horas continuas. El calculo
formal de horas extra semanales (que exige acumular todos
los turnos de la semana) requiere ademas revisar el
convenio/jornada pactada de cada profesional; este modulo
dejar sentada la base por turno, que es lo minimo exigible
para pagar correctamente el trabajo domiciliario nocturno
y dominical.
=========================================================
"""

from datetime import datetime, timedelta

from core.nomina.parametros_legales import (
    HORA_FIN_NOCTURNA,
    HORA_INICIO_NOCTURNA,
    RECARGO_EXTRA_DIURNA,
    RECARGO_EXTRA_NOCTURNA,
    RECARGO_NOCTURNO,
    es_dominical_o_festivo,
    recargo_dominical_festivo,
)

JORNADA_ORDINARIA_DIARIA_HORAS = 8


def _es_hora_nocturna(hora: int) -> bool:
    return hora >= HORA_INICIO_NOCTURNA or hora < HORA_FIN_NOCTURNA


def clasificar_turno(hora_real_inicio: str, hora_real_fin: str) -> dict:
    """
    Recibe "YYYY-MM-DD HH:MM:SS" de inicio y fin y devuelve
    las horas (en fracciones) por cada concepto legal.
    """

    inicio = datetime.strptime(hora_real_inicio, "%Y-%m-%d %H:%M:%S")
    fin = datetime.strptime(hora_real_fin, "%Y-%m-%d %H:%M:%S")

    if fin <= inicio:
        return {
            "horas_diurnas": 0, "horas_nocturnas": 0,
            "horas_dominicales_diurnas": 0, "horas_dominicales_nocturnas": 0,
            "horas_extra_diurnas": 0, "horas_extra_nocturnas": 0,
            "total_horas": 0,
        }

    # -----------------------------------------------
    # Recorrer minuto a minuto en bloques de 1 minuto
    # es preciso pero costoso; usamos bloques de 1 hora
    # con prorrateo de fracciones, suficiente para nomina.
    # -----------------------------------------------

    total_diurnas = 0.0
    total_nocturnas = 0.0
    total_dom_diurnas = 0.0
    total_dom_nocturnas = 0.0

    cursor = inicio
    paso = timedelta(minutes=15)

    while cursor < fin:
        siguiente = min(cursor + paso, fin)
        duracion_h = (siguiente - cursor).total_seconds() / 3600

        es_nocturna = _es_hora_nocturna(cursor.hour)
        es_dom = es_dominical_o_festivo(cursor.date())

        if es_dom and es_nocturna:
            total_dom_nocturnas += duracion_h
        elif es_dom:
            total_dom_diurnas += duracion_h
        elif es_nocturna:
            total_nocturnas += duracion_h
        else:
            total_diurnas += duracion_h

        cursor = siguiente

    total_horas = total_diurnas + total_nocturnas + total_dom_diurnas + total_dom_nocturnas

    # -----------------------------------------------
    # Horas extra: lo que exceda la jornada ordinaria
    # diaria (8h) en este turno, tomado proporcionalmente
    # de las horas diurnas/nocturnas ordinarias (no de las
    # dominicales, que ya tienen su propio recargo pleno).
    # -----------------------------------------------

    horas_ordinarias = total_diurnas + total_nocturnas
    exceso = max(horas_ordinarias - JORNADA_ORDINARIA_DIARIA_HORAS, 0)

    horas_extra_diurnas = 0.0
    horas_extra_nocturnas = 0.0

    if exceso > 0 and horas_ordinarias > 0:
        proporcion_nocturna = total_nocturnas / horas_ordinarias
        horas_extra_nocturnas = round(exceso * proporcion_nocturna, 4)
        horas_extra_diurnas = round(exceso - horas_extra_nocturnas, 4)

        total_diurnas = max(total_diurnas - (exceso - horas_extra_nocturnas), 0)
        total_nocturnas = max(total_nocturnas - horas_extra_nocturnas, 0)

    return {
        "horas_diurnas": round(total_diurnas, 4),
        "horas_nocturnas": round(total_nocturnas, 4),
        "horas_dominicales_diurnas": round(total_dom_diurnas, 4),
        "horas_dominicales_nocturnas": round(total_dom_nocturnas, 4),
        "horas_extra_diurnas": round(horas_extra_diurnas, 4),
        "horas_extra_nocturnas": round(horas_extra_nocturnas, 4),
        "total_horas": round(total_horas, 4),
    }


def valor_turno(clasificacion: dict, valor_hora_ordinaria: float, fecha) -> dict:
    """
    Aplica los recargos legales vigentes a cada tipo de hora
    y devuelve el desglose de valores en pesos.
    """

    recargo_dom = recargo_dominical_festivo(fecha)

    valores = {
        "diurnas": clasificacion["horas_diurnas"] * valor_hora_ordinaria,
        "nocturnas": clasificacion["horas_nocturnas"] * valor_hora_ordinaria * (1 + RECARGO_NOCTURNO),
        "dominicales_diurnas": clasificacion["horas_dominicales_diurnas"] * valor_hora_ordinaria * (1 + recargo_dom),
        "dominicales_nocturnas": clasificacion["horas_dominicales_nocturnas"] * valor_hora_ordinaria * (1 + recargo_dom + RECARGO_NOCTURNO),
        "extra_diurnas": clasificacion["horas_extra_diurnas"] * valor_hora_ordinaria * (1 + RECARGO_EXTRA_DIURNA),
        "extra_nocturnas": clasificacion["horas_extra_nocturnas"] * valor_hora_ordinaria * (1 + RECARGO_EXTRA_NOCTURNA),
    }

    valores = {k: round(v, 2) for k, v in valores.items()}
    valores["total"] = round(sum(valores.values()), 2)

    return valores
