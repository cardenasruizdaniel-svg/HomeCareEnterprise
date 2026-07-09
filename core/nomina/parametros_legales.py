"""
=========================================================
HomeCare Enterprise
Parametros legales de nomina - Colombia, vigentes 2026

Fuente: Decretos 1469 y 1470 del 29 de diciembre de 2025
(salario minimo y auxilio de transporte 2026); Ley 2466 de
2025 (reforma laboral, jornada nocturna desde las 7:00 p.m.
y recargo dominical/festivo escalonado); Ley 2101 de 2021
(reduccion gradual de la jornada laboral maxima).

IMPORTANTE: estos valores cambian cada año (SMLMV, auxilio
de transporte) y en fechas especificas por la reforma
laboral (recargo dominical: 80% hasta jun/2026, 90% desde
jul/2026, 100% desde jul/2027). Revisar y actualizar este
archivo cuando el Gobierno expida los nuevos decretos.
=========================================================
"""

from datetime import date

# ==========================================================
# SALARIO MÍNIMO Y AUXILIO DE TRANSPORTE 2026
# ==========================================================

SMLMV_2026 = 1_750_905

AUXILIO_TRANSPORTE_2026 = 249_095

TOPE_AUXILIO_TRANSPORTE = SMLMV_2026 * 2  # $3.501.810

# ==========================================================
# JORNADA LABORAL (Ley 2101 de 2021)
# ==========================================================
# Hasta el 14 de julio de 2026: 44 horas/semana.
# Desde el 15 de julio de 2026: 42 horas/semana.

def horas_semanales_legales(fecha) -> float:
    if isinstance(fecha, str):
        fecha = date.fromisoformat(fecha)
    return 42 if fecha >= date(2026, 7, 15) else 44


def horas_mensuales_legales(fecha) -> float:
    """Divisor mensual estandar (horas semanales * 52 / 12)."""
    return round(horas_semanales_legales(fecha) * 52 / 12, 2)

# ==========================================================
# JORNADA NOCTURNA (Ley 2466 de 2025, vigente desde 25-dic-2025)
# ==========================================================

HORA_INICIO_NOCTURNA = 19  # 7:00 p.m.
HORA_FIN_NOCTURNA = 6      # 6:00 a.m.

RECARGO_NOCTURNO = 0.35

# ==========================================================
# RECARGO DOMINICAL / FESTIVO (Ley 2466 de 2025, escalonado)
# ==========================================================

def recargo_dominical_festivo(fecha) -> float:
    if isinstance(fecha, str):
        fecha = date.fromisoformat(fecha)

    if fecha >= date(2027, 7, 1):
        return 1.00
    if fecha >= date(2026, 7, 1):
        return 0.90
    return 0.80

# ==========================================================
# HORAS EXTRA
# ==========================================================

RECARGO_EXTRA_DIURNA = 0.25

RECARGO_EXTRA_NOCTURNA = 0.75

# ==========================================================
# SEGURIDAD SOCIAL Y PARAFISCALES (aportes sobre el salario)
# ==========================================================

APORTE_SALUD_EMPLEADO = 0.04

APORTE_SALUD_EMPLEADOR = 0.085

APORTE_PENSION_EMPLEADO = 0.04

APORTE_PENSION_EMPLEADOR = 0.12

# ARL por nivel de riesgo (tarifas minimas de referencia,
# Decreto 1607 de 2002 - el valor real depende de la ARL y
# la actividad economica especifica de la IPS).
ARL_POR_NIVEL_RIESGO = {
    "I": 0.00522,
    "II": 0.01044,
    "III": 0.02436,
    "IV": 0.04350,
    "V": 0.06960,
}

# ==========================================================
# PRESTACIONES SOCIALES (provisión, empleador)
# ==========================================================

CESANTIAS = 1 / 12          # 8.33%

INTERESES_CESANTIAS = 0.12  # 12% anual sobre las cesantías

PRIMA_SERVICIOS = 1 / 12    # 8.33%

VACACIONES = 1 / 24         # 4.17%

# ==========================================================
# FESTIVOS COLOMBIA 2026 (Ley 51 de 1983 - "Ley Emiliani":
# los que caen entre semana y no son de fecha fija se
# trasladan al lunes siguiente)
# ==========================================================

FESTIVOS_2026 = [
    "2026-01-01",  # Año Nuevo
    "2026-01-12",  # Reyes Magos (trasladado)
    "2026-03-23",  # San José (trasladado)
    "2026-04-02",  # Jueves Santo
    "2026-04-03",  # Viernes Santo
    "2026-05-01",  # Día del Trabajo
    "2026-05-18",  # Ascensión del Señor (trasladado)
    "2026-06-08",  # Corpus Christi (trasladado)
    "2026-06-15",  # Sagrado Corazón (trasladado)
    "2026-06-29",  # San Pedro y San Pablo (trasladado)
    "2026-07-20",  # Independencia
    "2026-08-07",  # Batalla de Boyacá
    "2026-08-17",  # Asunción de la Virgen (trasladado)
    "2026-10-12",  # Día de la Raza (trasladado)
    "2026-11-02",  # Todos los Santos (trasladado)
    "2026-11-16",  # Independencia de Cartagena (trasladado)
    "2026-12-08",  # Inmaculada Concepción
    "2026-12-25",  # Navidad
]


def es_festivo(fecha) -> bool:
    if isinstance(fecha, str):
        return fecha in FESTIVOS_2026
    return fecha.isoformat() in FESTIVOS_2026


def es_dominical_o_festivo(fecha) -> bool:
    if isinstance(fecha, str):
        fecha_obj = date.fromisoformat(fecha)
    else:
        fecha_obj = fecha

    return fecha_obj.weekday() == 6 or es_festivo(fecha_obj)  # 6 = domingo
