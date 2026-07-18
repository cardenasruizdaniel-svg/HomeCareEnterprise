"""
HomeCare Enterprise - Generador de PDF para el módulo de Inventario

Produce los documentos descargables: informe de existencias,
informe de compras, informe de ingresos y egresos (kardex), y
el documento de convenio con un proveedor.
"""

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.config import EXPORTS_DIR

COLOR_MARCA = colors.HexColor("#0a8f86")


def _estilos():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("Titulo", parent=base["Heading1"], fontSize=15, textColor=COLOR_MARCA, spaceAfter=4),
        "subtitulo": ParagraphStyle("Subtitulo", parent=base["Normal"], fontSize=9, textColor=colors.grey, spaceAfter=12),
        "seccion": ParagraphStyle("Seccion", parent=base["Heading2"], fontSize=12, textColor=COLOR_MARCA, spaceBefore=12, spaceAfter=6),
        "normal": ParagraphStyle("NormalDoc", parent=base["Normal"], fontSize=10, spaceAfter=4, leading=14),
    }


def _encabezado(nombre_empresa: str, titulo_documento: str, subtitulo: str, estilos):
    elementos = [
        Paragraph(nombre_empresa or "HomeCare del Quindío I.P.S.", estilos["titulo"]),
        Paragraph(titulo_documento, estilos["seccion"]),
        Paragraph(subtitulo, estilos["subtitulo"]),
    ]
    return elementos


def _tabla_estandar(encabezados, filas, anchos=None):
    datos = [encabezados] + filas
    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_MARCA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tabla


def generar_pdf_existencias(informe: dict, nombre_empresa: str = "") -> str:
    carpeta = Path(EXPORTS_DIR) / "inventario"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"informe_existencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    estilos = _estilos()
    doc = SimpleDocTemplate(str(ruta), pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm)

    elementos = _encabezado(
        nombre_empresa, "Informe de Existencias de Inventario",
        f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}", estilos,
    )
    elementos.append(Paragraph(
        f"<b>Total de insumos activos:</b> {informe['total_insumos']} &nbsp;&nbsp; "
        f"<b>Valor total del inventario:</b> ${informe['total_valorizado']:,.2f}", estilos["normal"],
    ))
    if informe["insumos_stock_bajo"]:
        elementos.append(Paragraph(f"⚠ {len(informe['insumos_stock_bajo'])} insumo(s) con stock por debajo del mínimo.", estilos["normal"]))
    elementos.append(Spacer(1, 10))

    filas = [
        [i.get("codigo") or "-", i["nombre"], i.get("categoria") or "", str(i["stock_actual"]), i["unidad_medida"],
         f"${(i.get('costo_promedio') or 0):,.2f}", f"${i['valor_existencia']:,.2f}",
         "⚠ Bajo" if i["stock_bajo"] else ("Exceso" if i["stock_exceso"] else "Normal")]
        for i in informe["insumos"]
    ]
    elementos.append(_tabla_estandar(
        ["Código", "Insumo", "Categoría", "Stock", "Unidad", "Costo prom.", "Valor total", "Estado"], filas,
        anchos=[1.8*cm, 4.2*cm, 2.8*cm, 1.5*cm, 1.8*cm, 2.2*cm, 2.2*cm, 2*cm],
    ))
    doc.build(elementos)
    return str(ruta)


def generar_pdf_compras(informe: dict, fecha_desde: str, fecha_hasta: str, nombre_empresa: str = "") -> str:
    carpeta = Path(EXPORTS_DIR) / "inventario"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"informe_compras_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    estilos = _estilos()
    doc = SimpleDocTemplate(str(ruta), pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm)

    elementos = _encabezado(nombre_empresa, "Informe de Compras", f"Del {fecha_desde} al {fecha_hasta}", estilos)
    elementos.append(Paragraph(
        f"<b>Total comprado:</b> ${informe['total_comprado']:,.2f} &nbsp;&nbsp; "
        f"<b>Movimientos:</b> {informe['total_movimientos']}", estilos["normal"],
    ))
    elementos.append(Spacer(1, 10))

    filas = [
        [m["fecha"][:10], m.get("codigo") or "-", m["insumo"], m.get("proveedor") or "-",
         m.get("numero_factura") or "-", str(m["cantidad"]), f"${(m.get('costo_unitario') or 0):,.2f}", f"${m['valor_total']:,.2f}"]
        for m in informe["movimientos"]
    ]
    elementos.append(_tabla_estandar(
        ["Fecha", "Código", "Insumo", "Proveedor", "N.° Factura", "Cant.", "Costo Unit.", "Valor Total"], filas,
        anchos=[1.8*cm, 1.5*cm, 3.2*cm, 2.8*cm, 2*cm, 1.3*cm, 1.8*cm, 1.8*cm],
    ))

    if informe["por_proveedor"]:
        elementos.append(Paragraph("Total comprado por proveedor", estilos["seccion"]))
        filas_prov = [[p["proveedor"], f"${p['valor']:,.2f}"] for p in informe["por_proveedor"]]
        elementos.append(_tabla_estandar(["Proveedor", "Valor total comprado"], filas_prov))

    doc.build(elementos)
    return str(ruta)


def generar_pdf_movimientos(informe: dict, fecha_desde: str, fecha_hasta: str, nombre_empresa: str = "") -> str:
    carpeta = Path(EXPORTS_DIR) / "inventario"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"informe_movimientos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    estilos = _estilos()
    doc = SimpleDocTemplate(str(ruta), pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm)

    elementos = _encabezado(nombre_empresa, "Informe de Ingresos y Egresos (Kardex)", f"Del {fecha_desde} al {fecha_hasta}", estilos)
    elementos.append(Paragraph(
        f"<b>Total ingresos:</b> {informe['total_entradas']} &nbsp;&nbsp; "
        f"<b>Total egresos:</b> {informe['total_salidas']} &nbsp;&nbsp; "
        f"<b>Movimientos:</b> {informe['total_movimientos']}", estilos["normal"],
    ))
    elementos.append(Spacer(1, 10))

    filas = []
    for m in informe["movimientos"]:
        destino = ""
        if m["tipo"] == "Salida" and m.get("primer_nombre"):
            destino = f"{m['primer_nombre']} {m.get('primer_apellido','')}"
        elif m["tipo"] == "Entrada":
            destino = m.get("proveedor") or "-"
        filas.append([
            m["fecha"][:16], m["insumo"], m["tipo"], str(m["cantidad"]), destino, m.get("motivo") or "-",
            str(m.get("saldo_despues") if m.get("saldo_despues") is not None else "-"),
        ])
    elementos.append(_tabla_estandar(
        ["Fecha", "Insumo", "Tipo", "Cant.", "Proveedor / Paciente", "Motivo", "Saldo"], filas,
        anchos=[2.2*cm, 3*cm, 1.5*cm, 1.2*cm, 3*cm, 3*cm, 1.5*cm],
    ))
    doc.build(elementos)
    return str(ruta)


def generar_pdf_convenio(convenio: dict, nombre_empresa: str = "", nit_empresa: str = "") -> str:
    carpeta = Path(EXPORTS_DIR) / "inventario"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"convenio_{convenio['id']}.pdf"

    estilos = _estilos()
    doc = SimpleDocTemplate(str(ruta), pagesize=letter, topMargin=2.5 * cm, bottomMargin=2.5 * cm, leftMargin=2.5 * cm, rightMargin=2.5 * cm)

    elementos = [
        Paragraph(nombre_empresa or "HomeCare del Quindío I.P.S.", estilos["titulo"]),
        Paragraph(f"CONVENIO DE {convenio['tipo'].upper()} N.° {convenio.get('numero_convenio') or convenio['id']}", estilos["seccion"]),
        Spacer(1, 10),
    ]

    texto_partes = (
        f"Entre <b>{nombre_empresa or 'HomeCare del Quindío I.P.S.'}</b>"
        f"{' identificada con NIT ' + nit_empresa if nit_empresa else ''}, en adelante \"LA IPS\", "
        f"y <b>{convenio['proveedor']}</b>"
        f"{' identificado con NIT ' + convenio['proveedor_nit'] if convenio.get('proveedor_nit') else ''}, "
        f"en adelante \"EL PROVEEDOR\", se celebra el presente convenio de {convenio['tipo'].lower()}, "
        f"que se regirá por las siguientes condiciones:"
    )
    elementos.append(Paragraph(texto_partes, estilos["normal"]))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("Datos del proveedor", estilos["seccion"]))
    datos_proveedor = [
        ["Razón social", convenio["proveedor"]],
        ["NIT", convenio.get("proveedor_nit") or "-"],
        ["Contacto", convenio.get("proveedor_contacto") or "-"],
        ["Teléfono", convenio.get("proveedor_telefono") or "-"],
        ["Correo", convenio.get("proveedor_correo") or "-"],
        ["Dirección", convenio.get("proveedor_direccion") or "-"],
    ]
    elementos.append(_tabla_estandar(["Dato", "Valor"], datos_proveedor, anchos=[4*cm, 11*cm]))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("Condiciones del convenio", estilos["seccion"]))
    datos_convenio = [
        ["Tipo de convenio", convenio["tipo"]],
        ["Fecha de inicio", convenio.get("fecha_inicio") or "-"],
        ["Fecha de finalización", convenio.get("fecha_fin") or "Indefinido"],
        ["Valor", f"${convenio['valor']:,.2f}" if convenio.get("valor") else "No aplica / según consumo"],
        ["Estado", convenio.get("estado") or "Vigente"],
    ]
    elementos.append(_tabla_estandar(["Condición", "Valor"], datos_convenio, anchos=[4*cm, 11*cm]))
    elementos.append(Spacer(1, 10))

    if convenio.get("condiciones"):
        elementos.append(Paragraph("Cláusulas y condiciones adicionales", estilos["seccion"]))
        elementos.append(Paragraph(convenio["condiciones"].replace("\n", "<br/>"), estilos["normal"]))
        elementos.append(Spacer(1, 20))

    elementos.append(Spacer(1, 30))
    firmas = Table([["_______________________________", "_______________________________"],
                     ["Representante Legal de la IPS", "Representante del Proveedor"]],
                    colWidths=[7.5 * cm, 7.5 * cm])
    firmas.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTSIZE", (0, 0), (-1, -1), 9)]))
    elementos.append(firmas)

    doc.build(elementos)
    return str(ruta)
