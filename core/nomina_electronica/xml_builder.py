"""
=========================================================
HomeCare Enterprise
Constructor del Documento Soporte de Pago de Nomina
Electronica (DSNE), Resolucion 000013 de 2021 (Anexo
Tecnico de Nomina Electronica, hoy recopilada en el Anexo
T.5.4 de la Resolucion 000227 de 2025).

IMPORTANTE: el CUNE (Codigo Unico de Nomina Electronica)
que aqui se calcula es un HASH LOCAL de referencia, no el
CUNE oficial. La transmision real a la DIAN exige: RUT con
la responsabilidad de nomina electronica activa, firma
digital, y un software propio validado por la DIAN o un
proveedor tecnologico habilitado (la DIAN NO ofrece
herramienta gratuita para nomina, a diferencia de la
factura de venta). Ver docs/NOMINA_ELECTRONICA.md.
=========================================================
"""

import hashlib

from core.nomina.parametros_legales import (
    APORTE_PENSION_EMPLEADO,
    APORTE_SALUD_EMPLEADO,
)


def _texto(valor) -> str:
    return "" if valor is None else str(valor)


def calcular_cune_local(datos: dict) -> str:
    cadena = "".join([
        _texto(datos.get("numero_consecutivo")),
        _texto(datos.get("fecha_generacion")),
        _texto(datos.get("valor_devengado")),
        _texto(datos.get("valor_deducciones")),
        _texto(datos.get("nit_empleador")),
        _texto(datos.get("documento_trabajador")),
        "CLAVE-TECNICA-PENDIENTE-HABILITACION-DIAN",
    ])
    return hashlib.sha384(cadena.encode("utf-8")).hexdigest()


def construir_dsne(detalle_nomina: dict, profesional: dict, periodo: dict, nit_empleador: str, razon_social_empleador: str) -> dict:
    """
    Arma la estructura del DSNE para UN trabajador en UN
    periodo, siguiendo las secciones que exige el Anexo
    Tecnico de Nomina Electronica: Encabezado, Empleador,
    Trabajador, Periodo, Devengados, Deducciones, y
    Comprobante Total.
    """

    tipo_contrato = detalle_nomina.get("tipo_contrato", "POR_HORAS")
    valor_a_pagar = detalle_nomina.get("valor_a_pagar", 0)
    salario_base = detalle_nomina.get("salario_fijo") or 0
    auxilio_transporte_pagado = detalle_nomina.get("auxilio_transporte") or 0

    # -----------------------------------------------
    # DEVENGADOS
    # -----------------------------------------------
    # valor_a_pagar ya incluye el auxilio de transporte
    # (calculado en services/nomina_service.py); aqui solo
    # se desglosa para el DSNE, sin sumarlo de nuevo.

    sueldo_trabajado = round(valor_a_pagar - auxilio_transporte_pagado, 2)

    devengados = {
        "Basico": {
            "DiasTrabajados": periodo.get("dias_periodo", 30),
            "SueldoTrabajado": sueldo_trabajado,
        },
    }

    if auxilio_transporte_pagado > 0:
        devengados["Transporte"] = {
            "AuxilioTransporte": auxilio_transporte_pagado,
        }

    if tipo_contrato == "POR_HORAS" and detalle_nomina.get("desglose_horas"):
        desglose = detalle_nomina["desglose_horas"]

        if desglose.get("horas_extra_diurnas") or desglose.get("horas_extra_nocturnas"):
            devengados["HorasExtra"] = {
                "HorasExtraDiurnas": desglose.get("horas_extra_diurnas", 0),
                "HorasExtraNocturnas": desglose.get("horas_extra_nocturnas", 0),
            }

        if desglose.get("horas_dominicales_diurnas") or desglose.get("horas_dominicales_nocturnas"):
            devengados["Recargos"] = {
                "RecargoDominicalDiurno": desglose.get("horas_dominicales_diurnas", 0),
                "RecargoDominicalNocturno": desglose.get("horas_dominicales_nocturnas", 0),
            }

    valor_devengado_total = valor_a_pagar

    # -----------------------------------------------
    # DEDUCCIONES (solo aplican a contratos laborales
    # con salario fijo; por prestacion de servicios /
    # por horas informales no hay retencion de nomina)
    # -----------------------------------------------

    deducciones = {}
    valor_deducciones_total = 0

    if tipo_contrato == "FIJO" and salario_base > 0:
        salud = round(salario_base * APORTE_SALUD_EMPLEADO, 2)
        pension = round(salario_base * APORTE_PENSION_EMPLEADO, 2)
        deducciones = {
            "Salud": salud,
            "FondoPension": pension,
        }
        valor_deducciones_total = round(salud + pension, 2)

    valor_neto = round(valor_devengado_total - valor_deducciones_total, 2)

    numero_consecutivo = detalle_nomina.get("id", 0)
    fecha_generacion = periodo.get("fecha_generacion", "")

    cune = calcular_cune_local({
        "numero_consecutivo": numero_consecutivo,
        "fecha_generacion": fecha_generacion,
        "valor_devengado": valor_devengado_total,
        "valor_deducciones": valor_deducciones_total,
        "nit_empleador": nit_empleador,
        "documento_trabajador": profesional.get("documento", ""),
    })

    return {
        "DocumentoSoportePagoNomina": {
            "TipoDocumento": "DSNE",
            "NumeroConsecutivo": numero_consecutivo,
            "CUNE": {
                "value": cune,
                "schemeName": "CUNE-SHA384 (referencia local, no oficial DIAN)",
            },
            "FechaGeneracion": fecha_generacion,
            "PeriodoNomina": {
                "FechaIngreso": periodo.get("periodo_inicio", ""),
                "FechaLiquidacionInicio": periodo.get("periodo_inicio", ""),
                "FechaLiquidacionFin": periodo.get("periodo_fin", ""),
            },
            "Empleador": {
                "NIT": nit_empleador,
                "RazonSocial": razon_social_empleador,
            },
            "Trabajador": {
                "TipoDocumento": profesional.get("tipo_documento", "CC"),
                "NumeroDocumento": profesional.get("documento", ""),
                "PrimerApellido": profesional.get("primer_apellido", ""),
                "PrimerNombre": profesional.get("primer_nombre", ""),
                "TipoContrato": tipo_contrato,
                "Cargo": profesional.get("especialidad_principal", ""),
            },
            "Devengados": devengados,
            "Deducciones": deducciones,
            "ComprobanteTotal": {
                "TotalDevengado": valor_devengado_total,
                "TotalDeducciones": valor_deducciones_total,
                "TotalComprobante": valor_neto,
            },
        },
        "_cune_local": cune,
        "_valor_neto": valor_neto,
    }


def diccionario_a_xml_nomina(nodo, nombre_raiz="DocumentoSoportePagoNomina") -> str:
    """
    Convierte la estructura del DSNE a una representacion XML
    simple e indentada (no es el XML binario firmado que
    exige la DIAN, sino una representacion legible de la
    misma estructura de datos).
    """

    def _serializar(valor, nombre, nivel):
        indent = "  " * nivel

        if isinstance(valor, dict):
            if "value" in valor and len(valor) <= 3:
                atributos = " ".join(
                    f'{k}="{v}"' for k, v in valor.items() if k != "value"
                )
                return f'{indent}<{nombre} {atributos}>{valor["value"]}</{nombre}>\n'

            interior = "".join(
                _serializar(v, k, nivel + 1) for k, v in valor.items()
            )
            return f"{indent}<{nombre}>\n{interior}{indent}</{nombre}>\n"

        if isinstance(valor, list):
            return "".join(_serializar(v, nombre, nivel) for v in valor)

        return f"{indent}<{nombre}>{valor}</{nombre}>\n"

    cuerpo = "".join(
        _serializar(v, k, 1) for k, v in nodo[nombre_raiz].items()
    )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<{nombre_raiz} xmlns="dian:gov:co:facturaelectronica:nomina">\n'
        f"{cuerpo}"
        f"</{nombre_raiz}>\n"
    )
