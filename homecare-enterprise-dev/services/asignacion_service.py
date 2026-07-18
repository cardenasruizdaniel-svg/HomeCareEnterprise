"""
==============================================================
HomeCare Enterprise
Motor Inteligente de Asignación
Archivo: services/asignacion_service.py
Sprint 3.4
==============================================================
"""

from __future__ import annotations

from datetime import datetime

from core.dispatcher.asignador import MotorAsignacion

from repositories import (
    programacion_repository,
    profesionales_repository,
)

from repositories.despacho_repository import (
    DespachoRepository,
)


class AsignacionService:

    """
    Servicio encargado de coordinar el Motor Inteligente
    con Agenda, Programación y Centro de Despacho.
    """

    # ======================================================
    # VISITAS PENDIENTES
    # ======================================================

    @staticmethod
    def visitas_pendientes():

        return programacion_repository.pendientes()

    # ======================================================
    # PROFESIONALES
    # ======================================================

    @staticmethod
    def profesionales():

        return profesionales_repository.disponibles()

    # ======================================================
    # ASIGNAR UNA VISITA
    # ======================================================

    @staticmethod
    def asignar_visita(programacion):

        resultado = MotorAsignacion.asignar(
            programacion
        )

        return resultado

    # ======================================================
    # ASIGNACIÓN AUTOMÁTICA
    # ======================================================

    @classmethod
    def asignacion_automatica(
        cls,
        fecha=None,
    ):

        if fecha is None:

            fecha = datetime.now().strftime(
                "%Y-%m-%d"
            )

        visitas = programacion_repository.agenda_dia(
            fecha
        )

        asignaciones = []

        for visita in visitas:

            if visita["profesional_id"]:

                continue

            try:

                asignacion = cls.asignar_visita(
                    visita
                )

                programacion_repository.actualizar_profesional(
                    visita["id"],
                    asignacion["profesional_id"],
                )

                DespachoRepository.crear(

                    {

                        "programacion_id":
                            visita["id"],

                        "paciente_id":
                            visita["paciente_id"],

                        "profesional_id":
                            asignacion["profesional_id"],

                        "fecha":
                            visita["fecha"],

                        "hora_inicio":
                            visita["hora_inicio"],

                        "hora_fin":
                            visita["hora_fin"],

                        "direccion":
                            visita["direccion"],

                        "barrio":
                            visita["barrio"],

                        "municipio":
                            visita["ciudad"],

                        "departamento":
                            visita["departamento"],

                        "latitud":
                            visita["latitud"],

                        "longitud":
                            visita["longitud"],

                        "prioridad":
                            asignacion["prioridad"],

                        "estado":
                            "PENDIENTE",

                        "observaciones":
                            "Asignación automática",

                        "creado_por":
                            None,

                    }

                )

                asignaciones.append(

                    {

                        "programacion":

                            visita["id"],

                        **asignacion,

                    }

                )

            except Exception as ex:

                asignaciones.append(

                    {

                        "programacion":

                            visita["id"],

                        "error":

                            str(ex),

                    }

                )

        return asignaciones

    # ======================================================
    # INDICADORES
    # ======================================================

    @staticmethod
    def indicadores():

        pendientes = len(
            programacion_repository.pendientes()
        )

        disponibles = len(
            profesionales_repository.disponibles()
        )

        return {

            "visitas_pendientes":
                pendientes,

            "profesionales_disponibles":
                disponibles,

        }

    # ======================================================
    # DASHBOARD
    # ======================================================

    @classmethod
    def dashboard(cls):

        return {

            "indicadores":

                cls.indicadores(),

            "visitas":

                cls.visitas_pendientes(),

            "profesionales":

                cls.profesionales(),

        }