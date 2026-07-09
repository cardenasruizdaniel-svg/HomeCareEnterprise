"""
==========================================================
HomeCare Enterprise
Módulo: Despacho Inteligente
Archivo: models/despacho.py
Autor: HomeCare Enterprise
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EstadoDespacho(str, Enum):
    PENDIENTE = "PENDIENTE"
    ASIGNADO = "ASIGNADO"
    EN_RUTA = "EN_RUTA"
    EN_ATENCION = "EN_ATENCION"
    FINALIZADO = "FINALIZADO"
    CANCELADO = "CANCELADO"
    REPROGRAMADO = "REPROGRAMADO"


class PrioridadDespacho(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


@dataclass(slots=True)
class Despacho:

    # ============================
    # Identificación
    # ============================

    id: Optional[int] = None
    uuid: Optional[str] = None

    # ============================
    # Relación con Programación
    # ============================

    programacion_id: int = 0
    paciente_id: int = 0
    profesional_id: int = 0

    # ============================
    # Agenda
    # ============================

    fecha: str = ""
    hora_inicio: str = ""
    hora_fin: str = ""

    # ============================
    # Ubicación
    # ============================

    direccion: str = ""
    barrio: str = ""
    municipio: str = ""
    departamento: str = ""

    latitud: float = 0.0
    longitud: float = 0.0

    # ============================
    # Ruta
    # ============================

    orden_ruta: int = 0

    distancia_km: float = 0.0

    tiempo_estimado_min: int = 0

    tiempo_real_min: int = 0

    # ============================
    # Estado
    # ============================

    estado: EstadoDespacho = EstadoDespacho.PENDIENTE

    prioridad: PrioridadDespacho = PrioridadDespacho.MEDIA

    observaciones: str = ""

    # ============================
    # Auditoría
    # ============================

    creado_por: Optional[int] = None

    actualizado_por: Optional[int] = None

    fecha_creacion: datetime = field(default_factory=datetime.now)

    fecha_actualizacion: datetime = field(default_factory=datetime.now)

    eliminado: bool = False

    # ============================
    # Operación
    # ============================

    def asignar(self, profesional_id: int):

        self.profesional_id = profesional_id
        self.estado = EstadoDespacho.ASIGNADO
        self.fecha_actualizacion = datetime.now()

    def iniciar_ruta(self):

        self.estado = EstadoDespacho.EN_RUTA
        self.fecha_actualizacion = datetime.now()

    def iniciar_atencion(self):

        self.estado = EstadoDespacho.EN_ATENCION
        self.fecha_actualizacion = datetime.now()

    def finalizar(self):

        self.estado = EstadoDespacho.FINALIZADO
        self.fecha_actualizacion = datetime.now()

    def cancelar(self):

        self.estado = EstadoDespacho.CANCELADO
        self.fecha_actualizacion = datetime.now()

    def reprogramar(self):

        self.estado = EstadoDespacho.REPROGRAMADO
        self.fecha_actualizacion = datetime.now()

    @property
    def coordenadas(self):

        return (self.latitud, self.longitud)

    @property
    def pendiente(self):

        return self.estado == EstadoDespacho.PENDIENTE

    @property
    def en_ruta(self):

        return self.estado == EstadoDespacho.EN_RUTA

    @property
    def atendiendo(self):

        return self.estado == EstadoDespacho.EN_ATENCION

    @property
    def finalizado(self):

        return self.estado == EstadoDespacho.FINALIZADO