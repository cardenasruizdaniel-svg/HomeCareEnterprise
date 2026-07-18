"""
HomeCare Enterprise - Servicio: Copagos de pacientes

Permite indicar cuanto debe pagar un paciente por una
atencion (copago/cuota moderadora) y si ya lo pago o no.
Cuando se marca como pagado, queda listo para generar su
factura electronica (ver services/facturacion_service.py).
"""

from datetime import date

from repositories.copagos_repository import CopagosRepository


def listar_por_paciente(paciente_id: int):
    return [dict(c) for c in CopagosRepository.listar_por_paciente(paciente_id)]


def listar_pendientes():
    return [dict(c) for c in CopagosRepository.listar_pendientes()]


def obtener(copago_id: int):
    return CopagosRepository.obtener(copago_id)


def crear_copago(paciente_id, valor_copago, concepto, programacion_id=None, orden_id=None, observaciones="", usuario=None) -> int:

    if not paciente_id:
        raise ValueError("Debe indicar el paciente.")

    if not valor_copago or valor_copago <= 0:
        raise ValueError("El valor del copago debe ser mayor a cero.")

    return CopagosRepository.crear({
        "paciente_id": paciente_id,
        "programacion_id": programacion_id,
        "orden_id": orden_id,
        "concepto": concepto or "Copago / cuota moderadora",
        "valor_copago": valor_copago,
        "observaciones": observaciones,
        "usuario_creacion": usuario,
    })


def marcar_pagado(copago_id: int, metodo_pago: str):
    return CopagosRepository.marcar_pago(copago_id, metodo_pago, date.today().isoformat())
