"""
==============================================================
HomeCare Enterprise
Motor Inteligente de Asignación
Archivo: core/dispatcher/optimizador.py
==============================================================
"""

from __future__ import annotations

from math import radians, sin, cos, sqrt, atan2


class OptimizadorRutas:
    """
    Optimizador básico de rutas.

    En futuros Sprint será reemplazado por integración
    con OpenRouteService, Google Maps u OSRM.
    """

    RADIO_TIERRA = 6371.0

    # ======================================================
    # DISTANCIA ENTRE DOS COORDENADAS
    # ======================================================

    @classmethod
    def distancia(
        cls,
        lat1,
        lon1,
        lat2,
        lon2,
    ):

        if None in (lat1, lon1, lat2, lon2):
            return 999999

        lat1 = radians(float(lat1))
        lon1 = radians(float(lon1))
        lat2 = radians(float(lat2))
        lon2 = radians(float(lon2))

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            sin(dlat / 2) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(dlon / 2) ** 2
        )

        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return cls.RADIO_TIERRA * c

    # ======================================================
    # ORDENAR POR PRIORIDAD
    # ======================================================

    @staticmethod
    def ordenar_prioridad(visitas):

        return sorted(
            visitas,
            key=lambda x: (
                -(x.get("puntaje", 0)),
                x.get("hora_inicio", ""),
            ),
        )

    # ======================================================
    # RUTA MÁS CORTA (HEURÍSTICA)
    # ======================================================

    @classmethod
    def ordenar_por_distancia(
        cls,
        visitas,
    ):

        if not visitas:
            return []

        pendientes = list(visitas)

        ruta = [pendientes.pop(0)]

        while pendientes:

            actual = ruta[-1]

            siguiente = min(

                pendientes,

                key=lambda visita:

                cls.distancia(

                    actual.get("latitud"),

                    actual.get("longitud"),

                    visita.get("latitud"),

                    visita.get("longitud"),

                )

            )

            ruta.append(siguiente)

            pendientes.remove(siguiente)

        return ruta

    # ======================================================
    # CALCULAR ORDEN DE RUTA
    # ======================================================

    @classmethod
    def optimizar(cls, visitas):

        visitas = cls.ordenar_prioridad(visitas)

        visitas = cls.ordenar_por_distancia(visitas)

        for indice, visita in enumerate(visitas, start=1):

            visita["orden_ruta"] = indice

        return visitas

    # ======================================================
    # RESUMEN
    # ======================================================

    @classmethod
    def resumen(cls, visitas):

        total = 0

        if len(visitas) < 2:

            return {

                "distancia_total": 0,

                "visitas": len(visitas)

            }

        for i in range(len(visitas) - 1):

            total += cls.distancia(

                visitas[i]["latitud"],

                visitas[i]["longitud"],

                visitas[i + 1]["latitud"],

                visitas[i + 1]["longitud"],

            )

        return {

            "distancia_total": round(total, 2),

            "visitas": len(visitas),

        }