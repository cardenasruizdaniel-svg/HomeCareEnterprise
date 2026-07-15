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


def generar_factura_servicio(servicio_paciente_id: int, valor_servicio: float, medio_pago: str,
                                usuario=None, plazo_dias_pago: int = 30) -> dict:
    """
    Factura un SERVICIO/informe ya prestado (ej. las visitas
    de un mes de terapia), no solo un copago -- para poder
    facturarle a la EPS o al paciente particular el valor
    completo del servicio brindado. Queda con estado de
    cartera "Pendiente de pago" y una fecha de vencimiento
    (30 días por defecto, el plazo habitual con EPS), para
    poder hacerle seguimiento en el dashboard de facturación.
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

    from datetime import datetime, timedelta
    fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fecha_vencimiento = (datetime.now() + timedelta(days=plazo_dias_pago)).strftime("%Y-%m-%d")
    entidad_responsable = paciente.get("eps") or "Particular"

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
        "entidad_responsable_pago": entidad_responsable,
        "fecha_vencimiento": fecha_vencimiento,
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


def _generar_factura_desde_items(items: list, usuario_id=None) -> dict:
    """
    Arma UNA factura a partir de una lista de cuentas por cobrar
    ya agrupadas (según el modo elegido: por EPS, por paciente,
    o por paciente+servicio) -- todas las cuentas de la lista
    deben ser de la MISMA EPS. Si son de un solo paciente, la
    factura queda a nombre de ese paciente (con su documento);
    si son de varios pacientes de la misma EPS, la factura
    queda a nombre de la EPS.
    """
    from datetime import datetime, timedelta

    primero = items[0]
    valor_total = sum(item["valor"] for item in items)
    pacientes_distintos = {item["paciente_id"] for item in items}

    numero = FacturacionRepository.siguiente_numero(PREFIJO_FACTURACION)
    fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    if len(pacientes_distintos) == 1:
        nombre_adquirente = f"{primero.get('primer_nombre','')} {primero.get('primer_apellido','')}".strip()
        documento_adquirente = primero.get("documento", "")
        tipo_documento_adquirente = primero.get("tipo_documento", "CC")
        concepto = f"Servicios de salud domiciliaria — {primero['eps']} ({len(items)} concepto(s))"
    else:
        nombre_adquirente = primero["eps"]
        documento_adquirente = ""  # se completa manualmente si se conoce el NIT exacto de la EPS
        tipo_documento_adquirente = "NIT"
        concepto = f"Servicios de salud domiciliaria — {primero['eps']} ({len(pacientes_distintos)} paciente(s), {len(items)} concepto(s))"

    from services.convenios_eps_service import obtener_convenio
    convenio = obtener_convenio(primero["convenio_id"])
    if convenio and convenio.get("nit_eps") and len(pacientes_distintos) > 1:
        documento_adquirente = convenio["nit_eps"]

    datos_ubl = {
        "prefijo": PREFIJO_FACTURACION,
        "numero": numero,
        "fecha_emision": fecha_emision,
        "valor_subtotal": valor_total,
        "valor_iva": 0,
        "valor_total": valor_total,
        "nit_emisor": RIPS_NIT_PRESTADOR or "PENDIENTE-CONFIGURAR-NIT",
        "razon_social_emisor": RIPS_RAZON_SOCIAL,
        "documento_adquirente": documento_adquirente,
        "tipo_documento_adquirente": tipo_documento_adquirente,
        "nombre_adquirente": nombre_adquirente,
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
        "servicio_paciente_id": None,
        "concepto": concepto,
        # La columna paciente_id de esta tabla es obligatoria (NOT NULL) y pensada
        # para una factura de un solo paciente -- cuando la factura agrupa VARIOS
        # pacientes (modo "por EPS"), se deja aquí el primero solo como referencia
        # de enlace; el detalle real de TODOS los pacientes incluidos queda en el
        # PDF/XML y en el enlace de cada cuenta_por_cobrar_eps.factura_id.
        "paciente_id": primero["paciente_id"],
        "valor_subtotal": valor_total,
        "valor_iva": 0,
        "valor_total": valor_total,
        "forma_pago": "Contado",
        "medio_pago": "EPS",
        "cufe": cufe,
        "estado": "Generada",
        "entidad_responsable_pago": primero["eps"],
        "fecha_vencimiento": fecha_vencimiento,
        "xml_path": str(ruta_xml),
        "pdf_path": None,
        "usuario_creacion": usuario_id,
    })

    factura = dict(FacturacionRepository.obtener(factura_id))
    factura["nombre_adquirente"] = nombre_adquirente
    factura["documento_adquirente"] = documento_adquirente

    from services.factura_eps_pdf_service import generar_pdf_factura_eps
    from services.configuracion_empresa_service import obtener as obtener_config_empresa
    config = obtener_config_empresa()
    ruta_pdf = generar_pdf_factura_eps(factura, items, config.get("razon_social", ""))
    FacturacionRepository.actualizar_pdf_path(factura_id, ruta_pdf)

    return {
        "factura_id": factura_id,
        "numero_completo": f"{PREFIJO_FACTURACION}{numero}",
        "eps": primero["eps"],
        "pacientes": len(pacientes_distintos),
        "items": len(items),
        "valor_total": valor_total,
        "pdf_path": ruta_pdf,
    }


def listar_por_paciente(paciente_id: int):
    return [dict(f) for f in FacturacionRepository.listar_por_paciente(paciente_id)]


def listar_todas():
    return [dict(f) for f in FacturacionRepository.listar_todas()]


def obtener(factura_id: int):
    return FacturacionRepository.obtener(factura_id)


def marcar_pagada(factura_id: int, valor_pagado: float, metodo_pago: str, fecha_pago: str = None):
    from datetime import date
    if not valor_pagado or valor_pagado <= 0:
        raise ValueError("Debe indicar el valor pagado.")
    FacturacionRepository.marcar_pagada(factura_id, valor_pagado, metodo_pago, fecha_pago or date.today().isoformat())


def anular_factura(factura_id: int, motivo: str):
    if not motivo:
        raise ValueError("Debe indicar el motivo de la anulación.")
    FacturacionRepository.anular(factura_id, motivo)


def listar_cartera(estado_cartera=None):
    FacturacionRepository.marcar_vencidas()  # actualiza el estado antes de mostrar el listado
    return [dict(f) for f in FacturacionRepository.listar_cartera(estado_cartera)]


def pendientes_facturar():
    return [dict(f) for f in FacturacionRepository.pendientes_facturar()]


def dashboard_facturacion():
    FacturacionRepository.marcar_vencidas()
    resumen = dict(FacturacionRepository.resumen_dashboard())
    for clave in ("total_facturado", "total_cobrado", "cartera_pendiente", "cartera_vencida"):
        resumen[clave] = resumen.get(clave) or 0

    return {
        **resumen,
        "por_mes": [dict(m) for m in FacturacionRepository.facturado_por_mes()],
        "top_eps": [dict(e) for e in FacturacionRepository.top_eps()],
        "total_pendientes_facturar": len(pendientes_facturar()),
    }


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
