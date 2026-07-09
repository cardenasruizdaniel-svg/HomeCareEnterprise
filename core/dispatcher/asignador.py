"""
==============================================================
HomeCare Enterprise
Motor Inteligente de Asignación
Archivo: core/dispatcher/asignador.py
Versión: Sprint 3.4
==============================================================
"""

from __future__ import annotations

from repositories import (
    profesionales_repository,
    programacion_repository,
)

from .reglas import ReglasAsignacion
from .prioridades import PrioridadPaciente
from .disponibilidad import (
    DisponibilidadProfesional,
    BloqueHorario,
)

from .excepciones import (
    NoExisteProfesionalDisponible,
)

from datetime import (
    datetime,
    timedelta,
)


class MotorAsignacion:

    """
    Motor encargado de seleccionar el mejor profesional
    para una visita domiciliaria.
    """

    # ==========================================================
    # PROFESIONALES CANDIDATOS
    # ==========================================================

    @staticmethod
    def candidatos(servicio, municipio):

        candidatos = []

        profesionales = profesionales_repository.disponibles()

        for profesional in profesionales:

            if profesional["municipio"] != municipio:
                continue

            if (
                profesional["especialidad"]
                != servicio
            ):
                continue

            candidatos.append(profesional)

        return candidatos

    # ==========================================================
    # AGENDA DEL PROFESIONAL
    # ==========================================================

    @staticmethod
    def agenda(profesional_id, fecha):

        agenda = []

        visitas = programacion_repository.agenda_profesional(
            profesional_id,
            fecha,
        )

        for visita in visitas:

            inicio = datetime.strptime(

                f"{visita['fecha']} {visita['hora_inicio']}",

                "%Y-%m-%d %H:%M"

            )

            fin = datetime.strptime(

                f"{visita['fecha']} {visita['hora_fin']}",

                "%Y-%m-%d %H:%M"

            )

            agenda.append(

                BloqueHorario(

                    inicio=inicio,

                    fin=fin,

                    descripcion=visita["servicio"]

                )

            )

        return agenda

    # ==========================================================
    # EVALUAR PROFESIONAL
    # ==========================================================

    @classmethod
    def evaluar(

        cls,

        profesional,

        visita,

    ):

        resultados = ReglasAsignacion.evaluar(

            profesional,

            visita["servicio"],

            visita["ciudad"],

            profesionales_repository.carga_laboral(

                profesional["id"],

                visita["fecha"]

            ),

        )

        if not ReglasAsignacion.aprobado(resultados):

            return None

        agenda = cls.agenda(

            profesional["id"],

            visita["fecha"]

        )

        inicio = datetime.strptime(

            f"{visita['fecha']} {visita['hora_inicio']}",

            "%Y-%m-%d %H:%M"

        )

        disponible = DisponibilidadProfesional.disponible(

            inicio,

            visita["duracion"],

            agenda

        )

        if not disponible:

            return None

        prioridad = PrioridadPaciente.calcular(

            visita["servicio"],

            visita.get("edad", 0),

            visita.get("paliativo", False),

            120,

        )

        puntaje = (

            ReglasAsignacion.puntaje(resultados)

            + prioridad["puntaje"]

        )

        return {

            "profesional": profesional,

            "puntaje": puntaje,

            "prioridad": prioridad,

        }

    # ==========================================================
    # ASIGNAR
    # ==========================================================

    @classmethod
    def asignar(cls, visita):

        candidatos = cls.candidatos(

            visita["servicio"],

            visita["ciudad"],

        )

        evaluaciones = []

        for profesional in candidatos:

            resultado = cls.evaluar(

                profesional,

                visita,

            )

            if resultado:

                evaluaciones.append(resultado)

        if not evaluaciones:

            raise NoExisteProfesionalDisponible(

                "No existen profesionales disponibles para esta visita."

            )

        evaluaciones.sort(

            key=lambda x: x["puntaje"],

            reverse=True,

        )

        mejor = evaluaciones[0]

        return {

            "profesional_id": mejor["profesional"]["id"],

            "puntaje": mejor["puntaje"],

            "prioridad": mejor["prioridad"]["nivel"],

        }

    # ==========================================================
    # ASIGNACIÓN AUTOMÁTICA
    # ==========================================================

    @classmethod
    def asignar_pendientes(cls, fecha):

        visitas = programacion_repository.agenda_dia(fecha)

        asignadas = []

        for visita in visitas:

            if visita["profesional_id"]:

                continue

            try:

                resultado = cls.asignar(visita)

                asignadas.append(

                    {

                        "programacion": visita["id"],

                        **resultado,

                    }

                )

            except NoExisteProfesionalDisponible:

                continue

        return asignadas