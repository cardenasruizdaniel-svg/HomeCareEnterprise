"""
HomeCare Enterprise - Verificacion de geocerca

Calcula la distancia entre dos coordenadas GPS (formula de
Haversine) para confirmar que el profesional efectivamente
estaba en el domicilio del paciente al marcar su ingreso o
salida de una visita.
"""

import math


def calcular_distancia_metros(lat1, lon1, lat2, lon2) -> float:
    """
    Distancia en metros entre dos puntos GPS usando la formula
    de Haversine (suficientemente precisa para verificar que
    alguien esta en el mismo domicilio, sin necesitar mapas).
    """

    if None in (lat1, lon1, lat2, lon2):
        return None

    radio_tierra_metros = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radio_tierra_metros * c


def verificar_geocerca(lat_profesional, lon_profesional, lat_paciente, lon_paciente, radio_metros=150) -> dict:
    """
    Devuelve si el profesional estaba dentro del radio
    esperado del domicilio del paciente, y a que distancia.
    """

    if lat_paciente is None or lon_paciente is None:
        return {
            "verificable": False,
            "dentro_del_rango": None,
            "distancia_metros": None,
            "mensaje": "El paciente no tiene coordenadas de domicilio registradas; no se puede verificar la ubicación.",
        }

    if lat_profesional is None or lon_profesional is None:
        return {
            "verificable": False,
            "dentro_del_rango": None,
            "distancia_metros": None,
            "mensaje": "No se recibió la ubicación del dispositivo (el profesional no otorgó permiso de ubicación).",
        }

    distancia = calcular_distancia_metros(lat_profesional, lon_profesional, lat_paciente, lon_paciente)
    dentro = distancia <= radio_metros

    return {
        "verificable": True,
        "dentro_del_rango": dentro,
        "distancia_metros": round(distancia, 1),
        "mensaje": (
            f"Ubicación verificada: a {round(distancia)} m del domicilio registrado."
            if dentro else
            f"⚠ El profesional marcó a {round(distancia)} m del domicilio registrado del paciente "
            f"(más del radio esperado de {radio_metros} m)."
        ),
    }
