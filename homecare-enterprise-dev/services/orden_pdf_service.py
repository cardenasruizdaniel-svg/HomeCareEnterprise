"""
=========================================================
HomeCare Enterprise
Generador de PDF para Ordenes Medicas

Produce el documento que se adjunta al correo y que se
sirve como enlace descargable para el envio por WhatsApp.
=========================================================
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.config import EXPORTS_DIR


def generar_pdf_orden(orden: dict, paciente: dict, profesional: dict | None = None) -> str:
    """
    Genera el PDF de una orden medica y devuelve la ruta del
    archivo generado (dentro de EXPORTS_DIR/ordenes).
    """

    carpeta = Path(EXPORTS_DIR) / "ordenes"
    carpeta.mkdir(parents=True, exist_ok=True)

    ruta = carpeta / f"orden_{orden.get('id', 'nueva')}.pdf"

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "Titulo", parent=estilos["Heading1"], fontSize=16,
        textColor=colors.HexColor("#0d6efd"), spaceAfter=6,
    )

    subtitulo = ParagraphStyle(
        "Subtitulo", parent=estilos["Normal"], fontSize=10,
        textColor=colors.grey, spaceAfter=14,
    )

    etiqueta = ParagraphStyle(
        "Etiqueta", parent=estilos["Normal"], fontSize=11, spaceAfter=4,
    )

    doc = SimpleDocTemplate(
        str(ruta), pagesize=letter,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )

    elementos = []

    elementos.append(Paragraph("HomeCare IPS", titulo))
    elementos.append(Paragraph("Orden Médica", subtitulo))

    nombre_paciente = paciente.get("nombre_completo") or " ".join(
        x for x in [
            paciente.get("primer_nombre"), paciente.get("primer_apellido"),
        ] if x
    )

    datos_tabla = [
        ["Paciente", nombre_paciente],
        ["Documento", f"{paciente.get('tipo_documento', '')} {paciente.get('documento', '')}"],
        ["Fecha de la orden", str(orden.get("fecha_orden", ""))[:19]],
        ["Tipo de orden", orden.get("tipo", "")],
        ["Profesional", (profesional or {}).get("nombre_completo", "") or (profesional or {}).get("nombre", "")],
    ]

    tabla = Table(datos_tabla, colWidths=[5 * cm, 10 * cm])
    tabla.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#495057")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
    ]))

    elementos.append(tabla)
    elementos.append(Spacer(1, 16))

    elementos.append(Paragraph("<b>Descripción / indicaciones:</b>", etiqueta))
    elementos.append(Paragraph(orden.get("descripcion", "") or "-", estilos["Normal"]))

    if orden.get("codigo_cups"):
        elementos.append(Spacer(1, 10))
        elementos.append(Paragraph(f"<b>Código CUPS:</b> {orden['codigo_cups']}", etiqueta))

    elementos.append(Spacer(1, 40))
    elementos.append(Paragraph(
        "Este documento fue generado automáticamente por el sistema "
        "HomeCare IPS y enviado al paciente por sus medios de contacto "
        "registrados.",
        ParagraphStyle("Pie", parent=estilos["Normal"], fontSize=8, textColor=colors.grey),
    ))

    doc.build(elementos)

    return str(ruta)
