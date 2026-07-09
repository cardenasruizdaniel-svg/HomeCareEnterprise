"""HomeCare Enterprise - Servicio: Contratos"""

from core.nomina.parametros_legales import (
    ARL_POR_NIVEL_RIESGO,
    APORTE_PENSION_EMPLEADO,
    APORTE_PENSION_EMPLEADOR,
    APORTE_SALUD_EMPLEADO,
    APORTE_SALUD_EMPLEADOR,
    AUXILIO_TRANSPORTE_2026,
    CESANTIAS,
    INTERESES_CESANTIAS,
    PRIMA_SERVICIOS,
    TOPE_AUXILIO_TRANSPORTE,
    VACACIONES,
)
from repositories.contratos_repository import ContratosRepository

TIPOS_CONTRATO = [
    "Término indefinido",
    "Término fijo",
    "Obra o labor",
    "Prestación de servicios",
]


def listar():
    return ContratosRepository.listar()


def listar_por_profesional(profesional_id: int):
    return ContratosRepository.listar_por_profesional(profesional_id)


def obtener(contrato_id: int):
    return ContratosRepository.obtener(contrato_id)


def crear(datos: dict, usuario=None) -> int:
    if not datos.get("profesional_id") or not datos.get("cargo_id"):
        raise ValueError("Debe seleccionar profesional y cargo.")
    if not datos.get("fecha_inicio"):
        raise ValueError("Debe indicar la fecha de inicio del contrato.")

    datos = dict(datos)
    datos.setdefault("fecha_fin", None)
    datos["usuario_creacion"] = usuario

    return ContratosRepository.crear(datos)


def finalizar(contrato_id: int, fecha_fin: str):
    return ContratosRepository.finalizar(contrato_id, fecha_fin)


def liquidacion_prestacional(salario_mensual: float, nivel_riesgo_arl: str = "I") -> dict:
    """
    Desglose informativo de lo que le cuesta al empleador un
    trabajador con contrato laboral (término indefinido/fijo)
    con ese salario, segun la legislacion vigente en Colombia
    2026. Es orientativo: la liquidacion formal de nómina
    (retención en la fuente, novedades, incapacidades, etc.)
    debe validarla el área contable de la IPS.
    """

    tiene_auxilio = salario_mensual <= TOPE_AUXILIO_TRANSPORTE
    auxilio_transporte = AUXILIO_TRANSPORTE_2026 if tiene_auxilio else 0

    ibc = salario_mensual  # ingreso base de cotización (simplificado)

    descuentos_empleado = {
        "salud_empleado": round(ibc * APORTE_SALUD_EMPLEADO, 2),
        "pension_empleado": round(ibc * APORTE_PENSION_EMPLEADO, 2),
    }

    tasa_arl = ARL_POR_NIVEL_RIESGO.get(nivel_riesgo_arl, ARL_POR_NIVEL_RIESGO["I"])

    aportes_empleador = {
        "salud_empleador": round(ibc * APORTE_SALUD_EMPLEADOR, 2),
        "pension_empleador": round(ibc * APORTE_PENSION_EMPLEADOR, 2),
        "arl": round(ibc * tasa_arl, 2),
        "cesantias": round(salario_mensual * CESANTIAS, 2),
        "intereses_cesantias": round(salario_mensual * CESANTIAS * INTERESES_CESANTIAS, 2),
        "prima_servicios": round(salario_mensual * PRIMA_SERVICIOS, 2),
        "vacaciones": round(salario_mensual * VACACIONES, 2),
    }

    total_devengado = salario_mensual + auxilio_transporte
    total_descuentos = sum(descuentos_empleado.values())
    neto_a_pagar = round(total_devengado - total_descuentos, 2)
    costo_total_empleador = round(salario_mensual + auxilio_transporte + sum(aportes_empleador.values()), 2)

    return {
        "salario_mensual": salario_mensual,
        "tiene_auxilio_transporte": tiene_auxilio,
        "auxilio_transporte": auxilio_transporte,
        "total_devengado": total_devengado,
        "descuentos_empleado": descuentos_empleado,
        "total_descuentos": round(total_descuentos, 2),
        "neto_a_pagar": neto_a_pagar,
        "aportes_empleador": aportes_empleador,
        "costo_total_empleador": costo_total_empleador,
    }
