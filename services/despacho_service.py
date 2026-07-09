"""
==========================================================
HomeCare Enterprise
Centro de Despacho Inteligente
Servicio de Despacho
==========================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from repositories.despacho_repository import DespachoRepository
from models.despacho import (
    Despacho,
    EstadoDespacho,
)


class DespachoService:

    """
    Servicio encargado de administrar el despacho
    operativo diario de la IPS.
    """

    # =====================================================
    # CONSULTAS
    # =====================================================

    @staticmethod
    def listar():

        return DespachoRepository.listar()

    @staticmethod
    def obtener(despacho_id: int):

        return DespachoRepository.obtener(despacho_id)

    @staticmethod
    def pendientes():

        return DespachoRepository.pendientes()

    @staticmethod
    def en_ruta():

        return DespachoRepository.en_ruta()

    @staticmethod
    def por_profesional(
        profesional_id: int,
        fecha: str,
    ):

        return DespachoRepository.por_profesional(
            profesional_id,
            fecha,
        )

    @staticmethod
    def indicadores():

        return DespachoRepository.indicadores()

    # =====================================================
    # CREACIÓN
    # =====================================================

    @staticmethod
    def crear(datos: dict[str, Any]):

        despacho = Despacho(

            programacion_id=datos["programacion_id"],
            paciente_id=datos["paciente_id"],
            profesional_id=datos["profesional_id"],

            fecha=datos["fecha"],

            hora_inicio=datos["hora_inicio"],
            hora_fin=datos["hora_fin"],

            direccion=datos.get("direccion", ""),
            barrio=datos.get("barrio", ""),
            municipio=datos.get("municipio", ""),
            departamento=datos.get("departamento", ""),

            latitud=datos.get("latitud", 0),
            longitud=datos.get("longitud", 0),

            prioridad=datos.get("prioridad", "MEDIA"),

            estado=EstadoDespacho.PENDIENTE,

            observaciones=datos.get(
                "observaciones",
                "",
            ),

            creado_por=datos.get("usuario_id")
        )

        return DespachoRepository.crear(
            despacho.__dict__
        )

    # =====================================================
    # ASIGNACIÓN
    # =====================================================

    @staticmethod
    def asignar_profesional(
        despacho_id: int,
        profesional_id: int,
    ):

        return DespachoRepository.asignar_profesional(
            despacho_id,
            profesional_id,
        )

    # =====================================================
    # ESTADOS
    # =====================================================

    @staticmethod
    def iniciar_ruta(
        despacho_id: int,
    ):

        return DespachoRepository.actualizar_estado(
            despacho_id,
            EstadoDespacho.EN_RUTA.value,
        )

    @staticmethod
    def iniciar_atencion(
        despacho_id: int,
    ):

        return DespachoRepository.actualizar_estado(
            despacho_id,
            EstadoDespacho.EN_ATENCION.value,
        )

    @staticmethod
    def finalizar(
        despacho_id: int,
    ):

        return DespachoRepository.actualizar_estado(
            despacho_id,
            EstadoDespacho.FINALIZADO.value,
        )

    @staticmethod
    def cancelar(
        despacho_id: int,
    ):

        return DespachoRepository.actualizar_estado(
            despacho_id,
            EstadoDespacho.CANCELADO.value,
        )

    @staticmethod
    def reprogramar(
        despacho_id: int,
    ):

        return DespachoRepository.actualizar_estado(
            despacho_id,
            EstadoDespacho.REPROGRAMADO.value,
        )

    # =====================================================
    # MOTOR DE DESPACHO
    # =====================================================

    @staticmethod
    def generar_despacho_diario():

        """
        Punto de entrada del motor inteligente.

        En los siguientes Sprint se incorporará:

        - Balanceo automático
        - IA
        - Optimización de rutas
        - Georreferenciación
        - Tráfico
        - Prioridades
        """

        return {

            "fecha": datetime.now().strftime("%Y-%m-%d"),

            "pendientes": DespachoRepository.pendientes(),

            "en_ruta": DespachoRepository.en_ruta(),

            "indicadores": DespachoRepository.indicadores()

        }

    # =====================================================
    # VALIDACIONES
    # =====================================================

    @staticmethod
    def validar_disponibilidad():

        """
        Sprint 3.4
        """

        return True

    @staticmethod
    def optimizar_rutas():

        """
        Sprint 3.5
        """

        return True

    @staticmethod
    def asignacion_automatica():

        """
        Sprint 3.6
        """

        return True