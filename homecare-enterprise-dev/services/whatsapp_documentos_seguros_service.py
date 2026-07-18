"""
HomeCare Enterprise - Envío seguro de documentos por WhatsApp

Permite que el propio paciente, o su acudiente, reciban por
WhatsApp (de forma automática, sin intervención de un asesor)
documentos sensibles como la historia clínica -- pero SOLO si
el número desde el que están escribiendo está registrado, ya
sea como el celular del paciente, o como el de alguno de sus
acudientes.

Cada envío genera un token de un solo uso, con vencimiento
corto, que da acceso a ESE documento de ESE paciente
únicamente -- así el enlace que viaja por WhatsApp no sirve de
nada si alguien más lo llegara a interceptar.
"""

import secrets
from datetime import datetime, timedelta

from database.database import consultar_todos, consultar_uno, ejecutar
from services.notificaciones_service import normalizar_celular

HORAS_VALIDEZ_TOKEN = 48


def numero_autorizado_para_paciente(paciente_id: int, numero_celular: str) -> bool:
    """
    True si el número que está escribiendo coincide con el
    celular/teléfono del PACIENTE, o con el de alguno de sus
    ACUDIENTES registrados -- en cualquiera de los dos casos,
    se considera una persona autorizada para recibir la
    información clínica de ese paciente.
    """
    numero_normalizado = normalizar_celular(numero_celular)
    if not numero_normalizado:
        return False

    paciente = consultar_uno("SELECT celular, telefono FROM pacientes WHERE id=?", (paciente_id,))
    if paciente:
        paciente = dict(paciente)
        for campo in ("celular", "telefono"):
            if paciente.get(campo) and normalizar_celular(paciente[campo]) == numero_normalizado:
                return True

    acudientes = consultar_todos(
        "SELECT celular, telefono, telefono_principal, telefono_secundario FROM acudientes WHERE paciente_id=?",
        (paciente_id,),
    )
    for acudiente in acudientes:
        acudiente = dict(acudiente)
        for campo in ("celular", "telefono", "telefono_principal", "telefono_secundario"):
            if acudiente.get(campo) and normalizar_celular(acudiente[campo]) == numero_normalizado:
                return True

    return False


def generar_token_documento(paciente_id: int, tipo_documento: str) -> str:
    token = secrets.token_urlsafe(32)
    fecha_expiracion = (datetime.now() + timedelta(hours=HORAS_VALIDEZ_TOKEN)).isoformat()
    ejecutar(
        "INSERT INTO whatsapp_tokens_documentos(token, paciente_id, tipo_documento, fecha_expiracion) VALUES (?, ?, ?, ?)",
        (token, paciente_id, tipo_documento, fecha_expiracion),
    )
    return token


def obtener_token_valido(token: str):
    """Devuelve la fila del token si existe, no ha vencido, y no se ha usado todavía -- si no, None."""
    fila = consultar_uno("SELECT * FROM whatsapp_tokens_documentos WHERE token=?", (token,))
    if not fila:
        return None
    fila = dict(fila)
    if fila["usado"]:
        return None
    if fila["fecha_expiracion"] < datetime.now().isoformat():
        return None
    return fila


def marcar_token_usado(token: str):
    ejecutar(
        "UPDATE whatsapp_tokens_documentos SET usado=1, fecha_uso=CURRENT_TIMESTAMP WHERE token=?",
        (token,),
    )


def generar_pdf_historia_clinica(paciente_id: int) -> str:
    """
    Arma el PDF de la historia clínica del paciente (la
    clínica formal -- evoluciones, órdenes, exámenes,
    recomendaciones -- SIN los informes de cuidador, que no
    hacen parte de la historia clínica formal) para el envío
    automático por WhatsApp.
    """
    from pathlib import Path
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from core.config import EXPORTS_DIR
    from services.historia_clinica_service import obtener_linea_tiempo

    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    if not paciente:
        raise ValueError("El paciente no existe.")
    paciente = dict(paciente)

    eventos = obtener_linea_tiempo(paciente_id)

    carpeta = Path(EXPORTS_DIR) / "historias_clinicas_whatsapp"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"historia_clinica_{paciente_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"

    base = getSampleStyleSheet()
    titulo = ParagraphStyle("Titulo", parent=base["Heading1"], fontSize=15, textColor=colors.HexColor("#0a8f86"), spaceAfter=4)
    subtitulo = ParagraphStyle("Subtitulo", parent=base["Normal"], fontSize=10, textColor=colors.grey, spaceAfter=10)
    evento_titulo = ParagraphStyle("EventoTitulo", parent=base["Normal"], fontSize=11, fontName="Helvetica-Bold", spaceAfter=2)
    normal = ParagraphStyle("NormalDoc", parent=base["Normal"], fontSize=10, spaceAfter=6, leading=14)

    doc = SimpleDocTemplate(str(ruta), pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm)

    nombre_paciente = f"{paciente.get('primer_nombre','')} {paciente.get('primer_apellido','')}".strip()
    elementos = [
        Paragraph("HomeCare del Quindío I.P.S.", titulo),
        Paragraph("Historia Clínica", ParagraphStyle("Sec", parent=base["Heading2"], fontSize=13, spaceAfter=4)),
        Paragraph(f"{nombre_paciente} — {paciente.get('tipo_documento','')} {paciente.get('documento','')}", subtitulo),
        Paragraph(
            "Documento generado y enviado de forma automática, únicamente a números verificados del paciente o de su acudiente registrado.",
            ParagraphStyle("Nota", parent=base["Normal"], fontSize=8, textColor=colors.grey, spaceAfter=14),
        ),
    ]

    fecha_actual = None
    for evento in eventos:
        fecha_evento = (evento.get("fecha") or "")[:10]
        if fecha_evento != fecha_actual:
            fecha_actual = fecha_evento
            elementos.append(Paragraph(f"📅 {fecha_actual}", ParagraphStyle("Fecha", parent=base["Heading3"], fontSize=11, textColor=colors.HexColor("#0a8f86"), spaceBefore=10, spaceAfter=4)))

        elementos.append(Paragraph(f"{evento.get('tipo','')} — {evento.get('titulo','')}", evento_titulo))
        if evento.get("profesional"):
            elementos.append(Paragraph(f"<i>Registrado por: {evento['profesional']}</i>", normal))
        if evento.get("detalle"):
            elementos.append(Paragraph(evento["detalle"].replace("\n", "<br/>"), normal))
        elementos.append(Spacer(1, 4))

    if not eventos:
        elementos.append(Paragraph("Este paciente todavía no tiene registros en su historia clínica.", normal))

    doc.build(elementos)
    return str(ruta)
