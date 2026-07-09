"""
=========================================================
HomeCare Enterprise
Constructor de la Factura Electronica de Venta (FEV) para
copagos de pacientes, en estructura UBL 2.1 (la que exige
la DIAN), Resolucion 000227 de 2025 (que unifico la
Resolucion 000165 de 2023 y sus modificatorias).

IMPORTANTE: este modulo arma el XML con la estructura y los
campos correctos, pero el CUFE (Codigo Unico de Factura
Electronica) que aqui se calcula es un HASH LOCAL de
referencia, no el CUFE oficial. El CUFE real exige el
"software ID" y la "clave tecnica" que la DIAN entrega
unicamente tras el proceso de habilitacion del facturador
electronico. Ver docs/FACTURACION_ELECTRONICA.md para el
detalle de lo que falta para transmitir facturas reales.
=========================================================
"""

import hashlib
from datetime import datetime, timezone

# Los servicios de salud estan excluidos de IVA
# (Estatuto Tributario, articulo 476).
TARIFA_IVA_SALUD = 0.0


def _texto(valor) -> str:
    return "" if valor is None else str(valor)


def calcular_cufe_local(datos: dict) -> str:
    """
    Calcula un hash SHA-384 local a partir de los campos que
    exige la DIAN para el CUFE oficial (numero de factura,
    fechas, valores, NIT emisor/adquirente). NO es el CUFE
    oficial: ese solo lo puede emitir la DIAN o un proveedor
    tecnologico habilitado, usando la clave tecnica asignada
    al facturador. Se calcula igual para que la estructura y
    el largo del campo sean representativos.
    """

    cadena = "".join([
        _texto(datos.get("numero_completo")),
        _texto(datos.get("fecha_emision")),
        _texto(datos.get("valor_subtotal")),
        _texto(TARIFA_IVA_SALUD),
        _texto(datos.get("valor_iva")),
        _texto(datos.get("valor_total")),
        _texto(datos.get("nit_emisor")),
        _texto(datos.get("documento_adquirente")),
        "CLAVE-TECNICA-PENDIENTE-HABILITACION-DIAN",
    ])

    return hashlib.sha384(cadena.encode("utf-8")).hexdigest()


def construir_factura_ubl(datos: dict) -> dict:
    """
    Arma la estructura de la Factura Electronica de Venta en
    un diccionario equivalente a UBL 2.1 (los mismos bloques
    que exige el Anexo Tecnico de la DIAN: Invoice, Party
    emisor/adquirente, InvoiceLine, TaxTotal, LegalMonetaryTotal).
    """

    numero_completo = f"{datos['prefijo']}{datos['numero']}"

    cufe = calcular_cufe_local({**datos, "numero_completo": numero_completo})

    return {
        "Invoice": {
            "UBLVersionID": "UBL 2.1",
            "CustomizationID": "10",  # Factura de venta - Resolucion 000227/2025
            "ID": numero_completo,
            "UUID": {
                "value": cufe,
                "schemeName": "CUFE-SHA384 (referencia local, no oficial DIAN)",
            },
            "IssueDate": datos["fecha_emision"][:10],
            "IssueTime": datos["fecha_emision"][11:19] if len(datos["fecha_emision"]) > 10 else "00:00:00",
            "InvoiceTypeCode": "01",  # Factura de venta
            "DocumentCurrencyCode": "COP",
            "LineCountNumeric": 1,

            "AccountingSupplierParty": {
                "PartyName": datos.get("razon_social_emisor", ""),
                "PartyTaxScheme": {
                    "CompanyID": datos.get("nit_emisor", ""),
                    "TaxLevelCode": "R-99-PN",
                },
                "PartyLegalEntity": {
                    "RegistrationName": datos.get("razon_social_emisor", ""),
                },
            },

            "AccountingCustomerParty": {
                "PartyIdentification": {
                    "ID": datos.get("documento_adquirente", ""),
                    "schemeName": datos.get("tipo_documento_adquirente", "CC"),
                },
                "PartyLegalEntity": {
                    "RegistrationName": datos.get("nombre_adquirente", ""),
                },
            },

            "InvoiceLine": [{
                "ID": "1",
                "InvoicedQuantity": 1,
                "LineExtensionAmount": datos["valor_subtotal"],
                "Item": {
                    "Description": datos.get("concepto", "Copago servicio de salud domiciliario"),
                },
                "Price": {
                    "PriceAmount": datos["valor_subtotal"],
                },
                "TaxTotal": {
                    "TaxAmount": 0,
                    "TaxSubtotal": {
                        "TaxableAmount": datos["valor_subtotal"],
                        "TaxAmount": 0,
                        "TaxCategory": {
                            "Percent": TARIFA_IVA_SALUD,
                            "TaxScheme": "IVA - Servicio de salud excluido (Art. 476 E.T.)",
                        },
                    },
                },
            }],

            "TaxTotal": {
                "TaxAmount": 0,
            },

            "LegalMonetaryTotal": {
                "LineExtensionAmount": datos["valor_subtotal"],
                "TaxExclusiveAmount": datos["valor_subtotal"],
                "TaxInclusiveAmount": datos["valor_total"],
                "PayableAmount": datos["valor_total"],
            },
        },
        "_cufe_local": cufe,
    }


def diccionario_a_xml(nodo, nombre_raiz="Invoice") -> str:
    """
    Convierte el diccionario UBL a una representacion XML
    simple e indentada (no es el UBL binario firmado que
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
        f'<{nombre_raiz} xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">\n'
        f"{cuerpo}"
        f"</{nombre_raiz}>\n"
    )
