"""
HomeCare Enterprise - PDF de la Carpeta del Paciente

Genera un PDF consolidado con los eventos que el usuario haya
seleccionado en la Carpeta del Paciente (notas clínicas,
órdenes, informes de cuidador, consentimientos, etc.) -- útil,
por ejemplo, para mandarle al paciente su historia clínica
reciente junto con una orden médica en un solo documento.
"""

from datetime import date
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
        "subtitulo": ParagraphStyle("Subtitulo", parent=base["Normal"], fontSize=10, textColor=colors.grey, spaceAfter=10),
        "seccion": ParagraphStyle("Seccion", parent=base["Heading2"], fontSize=12, textColor=COLOR_MARCA, spaceBefore=14, spaceAfter=4),
        "evento_titulo": ParagraphStyle("EventoTitulo", parent=base["Normal"], fontSize=11, fontName="Helvetica-Bold", spaceAfter=2),
        "normal": ParagraphStyle("NormalDoc", parent=base["Normal"], fontSize=10, spaceAfter=6, leading=14),
    }


def generar_pdf_carpeta(paciente: dict, eventos_seleccionados: list, nombre_empresa: str = "") -> str:
    carpeta = Path(EXPORTS_DIR) / "carpeta_paciente"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"carpeta_{paciente['id']}_{date.today().isoformat()}.pdf"

    estilos = _estilos()
    doc = SimpleDocTemplate(str(ruta), pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm)

    nombre_paciente = f"{paciente.get('primer_nombre','')} {paciente.get('segundo_nombre','') or ''} {paciente.get('primer_apellido','')} {paciente.get('segundo_apellido','') or ''}".strip()

    elementos = [
        Paragraph(nombre_empresa or "HomeCare del Quindío I.P.S.", estilos["titulo"]),
        Paragraph("Carpeta del Paciente — Registros Seleccionados", estilos["seccion"]),
        Paragraph(f"Generado el {date.today().strftime('%Y-%m-%d')}", estilos["subtitulo"]),
    ]

    datos_paciente = [
        ["Paciente", nombre_paciente],
        ["Documento", f"{paciente.get('tipo_documento','')} {paciente.get('documento','')}"],
        ["EPS", paciente.get("eps") or "-"],
    ]
    tabla_paciente = Table(datos_paciente, colWidths=[4 * cm, 13 * cm])
    tabla_paciente.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla_paciente)
    elementos.append(Spacer(1, 10))

    fecha_actual = None
    for evento in eventos_seleccionados:
        fecha_evento = (evento.get("fecha") or "")[:10]
        if fecha_evento != fecha_actual:
            fecha_actual = fecha_evento
            elementos.append(Paragraph(f"📅 {fecha_actual}", estilos["seccion"]))

        elementos.append(Paragraph(f"{evento.get('tipo','')} — {evento.get('titulo','')}", estilos["evento_titulo"]))
        if evento.get("profesional"):
            elementos.append(Paragraph(f"<i>Registrado por: {evento['profesional']}</i>", estilos["normal"]))
        if evento.get("detalle"):
            elementos.append(Paragraph(evento["detalle"].replace("\n", "<br/>"), estilos["normal"]))
        elementos.append(Spacer(1, 6))

    if not eventos_seleccionados:
        elementos.append(Paragraph("No se seleccionó ningún registro.", estilos["normal"]))

    doc.build(elementos)
    return str(ruta)
