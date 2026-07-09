"""
HomeCare Enterprise - Representacion grafica (PDF) de la
Factura Electronica de Venta, para entregar al paciente.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.config import EXPORTS_DIR


def generar_pdf_factura(factura: dict, paciente: dict) -> str:

    carpeta = Path(EXPORTS_DIR) / "facturas"
    carpeta.mkdir(parents=True, exist_ok=True)

    numero_completo = f"{factura['prefijo']}{factura['numero']}"
    ruta = carpeta / f"factura_{numero_completo}.pdf"

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle("Titulo", parent=estilos["Heading1"], fontSize=16,
                             textColor=colors.HexColor("#0d6efd"), spaceAfter=4)
    subtitulo = ParagraphStyle("Subtitulo", parent=estilos["Normal"], fontSize=10, textColor=colors.grey)

    doc = SimpleDocTemplate(str(ruta), pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)

    elementos = [
        Paragraph("HomeCare IPS", titulo),
        Paragraph(f"Factura Electrónica de Venta N.° {numero_completo}", subtitulo),
        Spacer(1, 10),
    ]

    nombre_paciente = paciente.get("nombre_completo") or " ".join(
        x for x in [paciente.get("primer_nombre"), paciente.get("primer_apellido")] if x
    )

    datos_tabla = [
        ["Adquirente", nombre_paciente],
        ["Documento", f"{paciente.get('tipo_documento', '')} {paciente.get('documento', '')}"],
        ["Fecha de emisión", str(factura.get("fecha_emision", ""))[:19]],
        ["Concepto", factura.get("concepto", "Copago servicio de salud domiciliario")],
        ["Forma de pago", factura.get("forma_pago", "Contado")],
        ["Medio de pago", factura.get("medio_pago", "")],
    ]

    tabla = Table(datos_tabla, colWidths=[5 * cm, 10 * cm])
    tabla.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 16))

    valores = [
        ["Subtotal", f"$ {factura.get('valor_subtotal', 0):,.0f}"],
        ["IVA (servicios de salud excluidos, Art. 476 E.T.)", f"$ {factura.get('valor_iva', 0):,.0f}"],
        ["TOTAL", f"$ {factura.get('valor_total', 0):,.0f}"],
    ]
    tabla_valores = Table(valores, colWidths=[11 * cm, 4 * cm])
    tabla_valores.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
    ]))
    elementos.append(tabla_valores)
    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph(f"<b>CUFE:</b> {factura.get('cufe', '')}",
                                ParagraphStyle("cufe", parent=estilos["Normal"], fontSize=7, textColor=colors.grey)))

    elementos.append(Spacer(1, 10))
    elementos.append(Paragraph(
        "Nota: este documento es una representación gráfica generada por HomeCare Enterprise. "
        "El CUFE mostrado es una referencia local; la validez fiscal de esta factura ante la DIAN "
        "requiere la habilitación como facturador electrónico y la transmisión a través de un "
        "proveedor tecnológico o software homologado.",
        ParagraphStyle("nota", parent=estilos["Normal"], fontSize=7, textColor=colors.grey),
    ))

    doc.build(elementos)

    return str(ruta)
