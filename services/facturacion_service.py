"""
HomeCare Enterprise - Servicio de Facturacion Electronica

Genera la Factura Electronica de Venta (estructura UBL 2.1 +
representacion en PDF) a partir de un copago ya marcado como
pagado, y la envia al paciente por correo (reutilizando el
mismo servicio de notificaciones de las ordenes medicas).

Ver docs/FACTURACION_ELECTRONICA.md para el detalle de lo
que falta para que esta factura sea válida ante la DIAN.
"""

import json
from pathlib import Path

from core.config import EXPORTS_DIR, RIPS_NIT_PRESTADOR, RIPS_RAZON_SOCIAL
from core.facturacion.xml_builder import construir_factura_ubl, diccionario_a_xml
from database.database import consultar_uno

from repositories.copagos_repository import CopagosRepository
from repositories.facturacion_repository import FacturacionRepository
from services.factura_pdf_service import generar_pdf_factura
from services.notificaciones_service import enviar_email

PREFIJO_FACTURACION = "FEV"


def generar_factura_copago(copago_id: int, medio_pago: str, usuario=None) -> dict:

    copago = CopagosRepository.obtener(copago_id)

    if not copago:
        raise ValueError("El copago no existe.")

    copago = dict(copago)

    if not copago["pagado"]:
        raise ValueError("El copago debe estar marcado como pagado antes de facturarlo.")

    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (copago["paciente_id"],))
    if not paciente:
        raise ValueError("El paciente asociado al copago no existe.")
    paciente = dict(paciente)

    numero = FacturacionRepository.siguiente_numero(PREFIJO_FACTURACION)

    from datetime import datetime
    fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    valor_subtotal = copago["valor_copago"]
    valor_iva = 0  # servicios de salud excluidos de IVA
    valor_total = valor_subtotal + valor_iva

    datos_ubl = {
        "prefijo": PREFIJO_FACTURACION,
        "numero": numero,
        "fecha_emision": fecha_emision,
        "valor_subtotal": valor_subtotal,
        "valor_iva": valor_iva,
        "valor_total": valor_total,
        "nit_emisor": RIPS_NIT_PRESTADOR or "PENDIENTE-CONFIGURAR-NIT",
        "razon_social_emisor": RIPS_RAZON_SOCIAL,
        "documento_adquirente": paciente.get("documento", ""),
        "tipo_documento_adquirente": paciente.get("tipo_documento", "CC"),
        "nombre_adquirente": paciente.get("nombre_completo") or f"{paciente.get('primer_nombre','')} {paciente.get('primer_apellido','')}",
        "concepto": copago.get("concepto", "Copago servicio de salud domiciliario"),
    }

    factura_ubl = construir_factura_ubl(datos_ubl)
    cufe = factura_ubl["_cufe_local"]

    # -----------------------------
    # GUARDAR XML
    # -----------------------------

    carpeta_xml = Path(EXPORTS_DIR) / "facturas"
    carpeta_xml.mkdir(parents=True, exist_ok=True)
    ruta_xml = carpeta_xml / f"factura_{PREFIJO_FACTURACION}{numero}.xml"

    with open(ruta_xml, "w", encoding="utf-8") as archivo:
        archivo.write(diccionario_a_xml(factura_ubl))

    # -----------------------------
    # GUARDAR EN BASE DE DATOS
    # -----------------------------

    factura_id = FacturacionRepository.crear({
        "prefijo": PREFIJO_FACTURACION,
        "numero": numero,
        "copago_id": copago_id,
        "paciente_id": paciente["id"],
        "valor_subtotal": valor_subtotal,
        "valor_iva": valor_iva,
        "valor_total": valor_total,
        "forma_pago": "Contado",
        "medio_pago": medio_pago,
        "cufe": cufe,
        "estado": "Generada",
        "xml_path": str(ruta_xml),
        "pdf_path": None,
        "usuario_creacion": usuario,
    })

    CopagosRepository.vincular_factura(copago_id, factura_id)

    # -----------------------------
    # GENERAR PDF (representación gráfica)
    # -----------------------------

    factura = dict(FacturacionRepository.obtener(factura_id))
    factura["concepto"] = copago.get("concepto")
    ruta_pdf = generar_pdf_factura(factura, paciente)

    FacturacionRepository.actualizar_pdf_path(factura_id, ruta_pdf)

    # -----------------------------
    # ENVIAR AL PACIENTE POR CORREO
    # -----------------------------

    resultado_envio = {"enviado": False, "motivo": "Paciente sin correo registrado."}

    if paciente.get("correo"):
        resultado_envio = enviar_email(
            destinatario=paciente["correo"],
            asunto=f"HomeCare IPS - Factura electrónica {PREFIJO_FACTURACION}{numero}",
            cuerpo_html=(
                f"<p>Hola {datos_ubl['nombre_adquirente']},</p>"
                f"<p>Adjuntamos la factura electrónica de su copago por valor de "
                f"$ {valor_total:,.0f}.</p>"
                f"<p style='color:#888;font-size:12px'>HomeCare IPS - Mensaje generado automáticamente.</p>"
            ),
            adjunto_path=ruta_pdf,
        )

    return {
        "factura_id": factura_id,
        "numero_completo": f"{PREFIJO_FACTURACION}{numero}",
        "cufe": cufe,
        "xml_path": str(ruta_xml),
        "pdf_path": ruta_pdf,
        "envio_correo": resultado_envio,
    }


def generar_factura_servicio(servicio_paciente_id: int, valor_servicio: float, medio_pago: str, usuario=None) -> dict:
    """
    Factura un SERVICIO/informe ya prestado (ej. las visitas
    de un mes de terapia), no solo un copago -- para poder
    facturarle a la EPS o al paciente particular el valor
    completo del servicio brindado.
    """

    servicio = consultar_uno("SELECT * FROM servicios_paciente WHERE id=?", (servicio_paciente_id,))
    if not servicio:
        raise ValueError("El servicio no existe.")
    servicio = dict(servicio)

    if not valor_servicio or valor_servicio <= 0:
        raise ValueError("Debe indicar el valor a facturar del servicio.")

    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (servicio["paciente_id"],))
    if not paciente:
        raise ValueError("El paciente asociado al servicio no existe.")
    paciente = dict(paciente)

    numero = FacturacionRepository.siguiente_numero(PREFIJO_FACTURACION)

    from datetime import datetime
    fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    valor_subtotal = valor_servicio
    valor_iva = 0  # servicios de salud excluidos de IVA
    valor_total = valor_subtotal + valor_iva

    concepto = servicio.get("tipo_servicio", "Servicio de salud domiciliario")
    if servicio.get("subtipo"):
        concepto += f" - {servicio['subtipo']}"

    datos_ubl = {
        "prefijo": PREFIJO_FACTURACION,
        "numero": numero,
        "fecha_emision": fecha_emision,
        "valor_subtotal": valor_subtotal,
        "valor_iva": valor_iva,
        "valor_total": valor_total,
        "nit_emisor": RIPS_NIT_PRESTADOR or "PENDIENTE-CONFIGURAR-NIT",
        "razon_social_emisor": RIPS_RAZON_SOCIAL,
        "documento_adquirente": paciente.get("documento", ""),
        "tipo_documento_adquirente": paciente.get("tipo_documento", "CC"),
        "nombre_adquirente": f"{paciente.get('primer_nombre','')} {paciente.get('primer_apellido','')}",
        "concepto": concepto,
    }

    factura_ubl = construir_factura_ubl(datos_ubl)
    cufe = factura_ubl["_cufe_local"]

    carpeta_xml = Path(EXPORTS_DIR) / "facturas"
    carpeta_xml.mkdir(parents=True, exist_ok=True)
    ruta_xml = carpeta_xml / f"factura_{PREFIJO_FACTURACION}{numero}.xml"

    with open(ruta_xml, "w", encoding="utf-8") as archivo:
        archivo.write(diccionario_a_xml(factura_ubl))

    factura_id = FacturacionRepository.crear({
        "prefijo": PREFIJO_FACTURACION,
        "numero": numero,
        "copago_id": None,
        "servicio_paciente_id": servicio_paciente_id,
        "concepto": concepto,
        "paciente_id": paciente["id"],
        "valor_subtotal": valor_subtotal,
        "valor_iva": valor_iva,
        "valor_total": valor_total,
        "forma_pago": "Contado",
        "medio_pago": medio_pago,
        "cufe": cufe,
        "estado": "Generada",
        "xml_path": str(ruta_xml),
        "pdf_path": None,
        "usuario_creacion": usuario,
    })

    factura = dict(FacturacionRepository.obtener(factura_id))
    factura["concepto"] = concepto
    ruta_pdf = generar_pdf_factura(factura, paciente)
    FacturacionRepository.actualizar_pdf_path(factura_id, ruta_pdf)

    resultado_envio = {"enviado": False, "motivo": "Paciente sin correo registrado."}
    if paciente.get("correo"):
        resultado_envio = enviar_email(
            destinatario=paciente["correo"],
            asunto=f"HomeCare IPS - Factura electrónica {PREFIJO_FACTURACION}{numero}",
            cuerpo_html=(
                f"<p>Hola {datos_ubl['nombre_adquirente']},</p>"
                f"<p>Adjuntamos la factura electrónica por concepto de {concepto}, "
                f"por valor de $ {valor_total:,.0f}.</p>"
                f"<p style='color:#888;font-size:12px'>HomeCare IPS - Mensaje generado automáticamente.</p>"
            ),
            adjunto_path=ruta_pdf,
        )

    return {
        "factura_id": factura_id,
        "numero_completo": f"{PREFIJO_FACTURACION}{numero}",
        "cufe": cufe,
        "xml_path": str(ruta_xml),
        "pdf_path": ruta_pdf,
        "envio_correo": resultado_envio,
    }


def listar_por_paciente(paciente_id: int):
    return [dict(f) for f in FacturacionRepository.listar_por_paciente(paciente_id)]


def listar_todas():
    return [dict(f) for f in FacturacionRepository.listar_todas()]


def obtener(factura_id: int):
    return FacturacionRepository.obtener(factura_id)


# ==========================================================
# REPORTES DE FACTURACIÓN (por paciente, por fecha, por EPS)
# ==========================================================

def reporte_por_paciente(fecha_desde=None, fecha_hasta=None):
    filas = [dict(f) for f in FacturacionRepository.reporte_por_paciente(fecha_desde, fecha_hasta)]
    return filas


def reporte_por_eps(fecha_desde=None, fecha_hasta=None):
    filas = [dict(f) for f in FacturacionRepository.reporte_por_eps(fecha_desde, fecha_hasta)]
    return filas


def reporte_por_fecha(fecha_desde: str, fecha_hasta: str):
    filas = [dict(f) for f in FacturacionRepository.reporte_por_fecha(fecha_desde, fecha_hasta)]
    return filas


def resumen_general(fecha_desde=None, fecha_hasta=None):
    por_paciente = reporte_por_paciente(fecha_desde, fecha_hasta)
    return {
        "total_facturado": sum(f["valor_total"] or 0 for f in por_paciente),
        "total_facturas": sum(f["total_facturas"] or 0 for f in por_paciente),
        "total_pacientes": len(por_paciente),
    }
