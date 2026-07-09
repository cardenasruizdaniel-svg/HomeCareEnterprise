"""
==============================================================
HomeCare Enterprise
Motor Inteligente de Asignación
Archivo: models/asignacion.py
Versión: Sprint 3.4
==============================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EstadoAsignacion(str, Enum):

    PENDIENTE = "PENDIENTE"

    ASIGNADA = "ASIGNADA"

    EN_PROCESO = "EN_PROCESO"

    FINALIZADA = "FINALIZADA"

    CANCELADA = "CANCELADA"

    RECHAZADA = "RECHAZADA"


@dataclass(slots=True)
class Asignacion:

    # ======================================================
    # IDENTIFICACIÓN
    # ======================================================

    id: Optional[int] = None

    uuid: Optional[str] = None

    # ======================================================
    # RELACIONES
    # ======================================================

    programacion_id: int = 0

    profesional_id: int = 0

    paciente_id: int = 0

    # ======================================================
    # MOTOR DE ASIGNACIÓN
    # ======================================================

    puntaje: float = 0.0

    prioridad: str = "MEDIA"

    algoritmo: str = "SMART_DISPATCH"

    version_motor: str = "3.4"

    # ======================================================
    # RUTA
    # ======================================================

    orden_ruta: int = 0

    distancia_km: float = 0.0

    tiempo_estimado: int = 0

    tiempo_real: int = 0

    # ======================================================
    # ESTADO
    # ======================================================

    estado: EstadoAsignacion = EstadoAsignacion.PENDIENTE

    observaciones: str = ""

    motivo_rechazo: str = ""

    # ======================================================
    # AUDITORÍA
    # ======================================================

    usuario_creacion: Optional[int] = None

    usuario_actualizacion: Optional[int] = None

    fecha_creacion: datetime = field(
        default_factory=datetime.now
    )

    fecha_actualizacion: datetime = field(
        default_factory=datetime.now
    )

    # ======================================================
    # OPERACIONES
    # ======================================================

    def asignar(self):

        self.estado = EstadoAsignacion.ASIGNADA

        self.fecha_actualizacion = datetime.now()

    def iniciar(self):

        self.estado = EstadoAsignacion.EN_PROCESO

        self.fecha_actualizacion = datetime.now()

    def finalizar(self):

        self.estado = EstadoAsignacion.FINALIZADA

        self.fecha_actualizacion = datetime.now()

    def cancelar(self, motivo: str = ""):

        self.estado = EstadoAsignacion.CANCELADA

        self.observaciones = motivo

        self.fecha_actualizacion = datetime.now()

    def rechazar(self, motivo: str):

        self.estado = EstadoAsignacion.RECHAZADA

        self.motivo_rechazo = motivo

        self.fecha_actualizacion = datetime.now()

    # ======================================================
    # SERIALIZACIÓN
    # ======================================================

    def to_dict(self):

        return {

            "id": self.id,

            "uuid": self.uuid,

            "programacion_id": self.programacion_id,

            "profesional_id": self.profesional_id,

            "paciente_id": self.paciente_id,

            "puntaje": self.puntaje,

            "prioridad": self.prioridad,

            "algoritmo": self.algoritmo,

            "version_motor": self.version_motor,

            "orden_ruta": self.orden_ruta,

            "distancia_km": self.distancia_km,

            "tiempo_estimado": self.tiempo_estimado,

            "tiempo_real": self.tiempo_real,

            "estado": self.estado.value,

            "observaciones": self.observaciones,

            "motivo_rechazo": self.motivo_rechazo,

            "usuario_creacion": self.usuario_creacion,

            "usuario_actualizacion": self.usuario_actualizacion,

            "fecha_creacion": self.fecha_creacion,

            "fecha_actualizacion": self.fecha_actualizacion,

        }

    @classmethod
    def from_dict(cls, datos: dict):

        return cls(

            id=datos.get("id"),

            uuid=datos.get("uuid"),

            programacion_id=datos.get("programacion_id", 0),

            profesional_id=datos.get("profesional_id", 0),

            paciente_id=datos.get("paciente_id", 0),

            puntaje=datos.get("puntaje", 0),

            prioridad=datos.get("prioridad", "MEDIA"),

            algoritmo=datos.get(
                "algoritmo",
                "SMART_DISPATCH",
            ),

            version_motor=datos.get(
                "version_motor",
                "3.4",
            ),

            orden_ruta=datos.get("orden_ruta", 0),

            distancia_km=datos.get("distancia_km", 0),

            tiempo_estimado=datos.get("tiempo_estimado", 0),

            tiempo_real=datos.get("tiempo_real", 0),

            estado=EstadoAsignacion(
                datos.get(
                    "estado",
                    EstadoAsignacion.PENDIENTE.value,
                )
            ),

            observaciones=datos.get(
                "observaciones",
                "",
            ),

            motivo_rechazo=datos.get(
                "motivo_rechazo",
                "",
            ),

            usuario_creacion=datos.get(
                "usuario_creacion",
            ),

            usuario_actualizacion=datos.get(
                "usuario_actualizacion",
            ),
        )