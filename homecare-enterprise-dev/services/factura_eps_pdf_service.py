"""
HomeCare Enterprise - PDF de Facturación EPS (con detalle de ítems)

A diferencia del PDF de factura de un solo servicio, esta
genera el PDF de una factura que puede agrupar VARIOS
conceptos (varios pacientes, o varios servicios de un mismo
paciente, según el modo de facturación elegido) -- mostrando
la tabla completa de qué se está cobrando.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.config import EXPORTS_DIR

COLOR_MARCA = colors.HexColor("#0a8f86")


def generar_pdf_factura_eps(factura: dict, items: list, nombre_empresa: str = "") -> str:
    carpeta = Path(EXPORTS_DIR) / "facturas"
    carpeta.mkdir(parents=True, exist_ok=True)

    numero_completo = f"{factura['prefijo']}{factura['numero']}"
    ruta = carpeta / f"factura_{numero_completo}.pdf"

    base = getSampleStyleSheet()
    titulo = ParagraphStyle("Titulo", parent=base["Heading1"], fontSize=16, textColor=COLOR_MARCA, spaceAfter=4)
    subtitulo = ParagraphStyle("Subtitulo", parent=base["Normal"], fontSize=10, textColor=colors.grey, spaceAfter=10)
    normal = ParagraphStyle("NormalDoc", parent=base["Normal"], fontSize=10, spaceAfter=4)

    doc = SimpleDocTemplate(str(ruta), pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm)

    elementos = [
        Paragraph(nombre_empresa or "HomeCare del Quindío I.P.S.", titulo),
        Paragraph(f"Factura Electrónica {numero_completo}", subtitulo),
    ]

    datos_encabezado = [
        ["Fecha de emisión", factura.get("fecha_emision", "")[:10]],
        ["Facturado a", factura.get("nombre_adquirente", "")],
        ["Documento / NIT", factura.get("documento_adquirente", "")],
        ["Total ítems", str(len(items))],
        ["Valor total", f"$ {factura.get('valor_total', 0):,.0f}"],
    ]
    tabla_encabezado = Table(datos_encabezado, colWidths=[4.5 * cm, 12 * cm])
    tabla_encabezado.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla_encabezado)
    elementos.append(Spacer(1, 14))

    elementos.append(Paragraph("Detalle de servicios facturados", ParagraphStyle("Seccion", parent=base["Heading2"], fontSize=12, textColor=COLOR_MARCA, spaceAfter=6)))

    filas = [["Paciente", "Documento", "Servicio", "Fecha", "Tipo", "Valor"]]
    for item in items:
        nombre_paciente = f"{item.get('primer_nombre','')} {item.get('primer_apellido','')}".strip()
        filas.append([
            nombre_paciente, item.get("documento", ""), item.get("tipo_servicio", ""),
            (item.get("fecha_servicio") or "")[:10],
            "Adicional" if item.get("es_adicional") else "Incluido",
            f"$ {item.get('valor', 0):,.0f}",
        ])
    filas.append(["", "", "", "", "TOTAL", f"$ {factura.get('valor_total', 0):,.0f}"])

    tabla_detalle = Table(filas, colWidths=[3.5 * cm, 2.3 * cm, 3.8 * cm, 2 * cm, 2 * cm, 2.4 * cm], repeatRows=1)
    tabla_detalle.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_MARCA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#dee2e6")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla_detalle)

    doc.build(elementos)
    return str(ruta)
