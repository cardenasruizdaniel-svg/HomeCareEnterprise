"""
HomeCare Enterprise - Posible Programación de Visitas

Cada día hábil, antes de armar la ruta del día siguiente, esta
pantalla arma una PROPUESTA de a quién habría que visitar,
agrupada por zona y por servicio -- para que la oficina revise
y decida qué sí se programa (y qué se deja pendiente).

Se enfoca en las visitas médicas:
  1. Pacientes NUEVOS con la primera valoración médica
     todavía sin programar.
  2. Pacientes que ya estaban en el programa, pero tienen
     derecho a una visita de Medicina General pendiente de
     programar.
  3. Pacientes de la zona "Cordilleranos" (antes "Zona
     Rural") -- que se visitan una sola vez al mes -- cuando
     ya se cumplió un mes desde su última visita médica.

Reglas de fecha:
  - Solo se arma ruta de lunes a sábado -- domingo no hay
    ruta, así que si "mañana" cae domingo, la propuesta salta
    directo al lunes.
  - Si el día que tocaría es festivo, también se salta al
    siguiente día hábil.
"""

from datetime import date, timedelta

from database.database import consultar_todos, consultar_uno

from core.nomina.parametros_legales import es_dominical_o_festivo
from core.zonas import ZONAS_CIUDAD, ZONAS_CON_PERIODICIDAD_PROPIA

SERVICIO_PRIMERA_VISITA = "Visita de valoración médica inicial"
SERVICIO_VISITA_SEGUIMIENTO = "Visita de Medicina General"


def calcular_proximo_dia_habil(fecha_referencia=None) -> str:
    """
    A partir de una fecha (por defecto hoy), busca el siguiente
    día en que sí se arma ruta -- saltando domingos y festivos.
    Por eso, si hoy es sábado, el resultado es el lunes (o más
    adelante, si el lunes fuera festivo).
    """
    if fecha_referencia is None:
        fecha = date.today()
    elif isinstance(fecha_referencia, str):
        fecha = date.fromisoformat(fecha_referencia)
    else:
        fecha = fecha_referencia

    candidato = fecha + timedelta(days=1)
    while es_dominical_o_festivo(candidato):
        candidato += timedelta(days=1)
    return candidato.isoformat()


def _primera_planilla_pendiente(servicio_paciente_id: int):
    fila = consultar_uno(
        "SELECT id FROM planilla_visitas WHERE servicio_paciente_id=? AND programacion_id IS NULL "
        "AND estado != 'Cancelada' ORDER BY fecha LIMIT 1",
        (servicio_paciente_id,),
    )
    return dict(fila)["id"] if fila else None


def _candidatos_primera_visita() -> list:
    """Pacientes nuevos: su primera valoración médica todavía no se ha programado."""
    filas = consultar_todos(
        """
        SELECT p.id AS paciente_id, p.primer_nombre, p.primer_apellido, p.documento, p.celular,
               p.direccion, p.zona_ciudad, sp.id AS servicio_id
        FROM servicios_paciente sp
        JOIN pacientes p ON p.id = sp.paciente_id
        WHERE sp.tipo_servicio = ? AND sp.estado = 'Activo'
          AND EXISTS (
              SELECT 1 FROM planilla_visitas pv
              WHERE pv.servicio_paciente_id = sp.id AND pv.programacion_id IS NULL AND pv.estado != 'Cancelada'
          )
        """,
        (SERVICIO_PRIMERA_VISITA,),
    )
    candidatos = []
    for fila in filas:
        f = dict(fila)
        planilla_id = _primera_planilla_pendiente(f["servicio_id"])
        if planilla_id:
            candidatos.append({**f, "planilla_id": planilla_id, "servicio": SERVICIO_PRIMERA_VISITA, "motivo": "Primera visita médica (paciente nuevo)"})
    return candidatos


def _candidatos_seguimiento_medico() -> list:
    """Pacientes que ya estaban en el programa, con una visita de Medicina General pendiente de programar."""
    filas = consultar_todos(
        """
        SELECT p.id AS paciente_id, p.primer_nombre, p.primer_apellido, p.documento, p.celular,
               p.direccion, p.zona_ciudad, sp.id AS servicio_id
        FROM servicios_paciente sp
        JOIN pacientes p ON p.id = sp.paciente_id
        WHERE sp.tipo_servicio = ? AND sp.estado = 'Activo'
          AND EXISTS (
              SELECT 1 FROM planilla_visitas pv
              WHERE pv.servicio_paciente_id = sp.id AND pv.programacion_id IS NULL AND pv.estado != 'Cancelada'
          )
        """,
        (SERVICIO_VISITA_SEGUIMIENTO,),
    )
    candidatos = []
    for fila in filas:
        f = dict(fila)
        planilla_id = _primera_planilla_pendiente(f["servicio_id"])
        if planilla_id:
            candidatos.append({**f, "planilla_id": planilla_id, "servicio": SERVICIO_VISITA_SEGUIMIENTO, "motivo": "Visita de Medicina General (seguimiento)"})
    return candidatos


def _candidatos_cordilleranos() -> list:
    """
    Pacientes de la zona "Cordilleranos": se visitan una sola
    vez al mes. Se revisa cuándo fue su última visita médica
    (inicial o de seguimiento) YA COMPLETADA -- si ya pasó un
    mes (o más), se proponen para programar de nuevo. Si nunca
    han tenido una visita médica, se toman como pendientes de
    la primera (ya cubierto arriba), así que aquí solo entran
    los que YA tuvieron al menos una.
    """
    dias_periodicidad = ZONAS_CON_PERIODICIDAD_PROPIA.get("Cordilleranos", 30)
    fecha_limite = (date.today() - timedelta(days=dias_periodicidad)).isoformat()

    filas = consultar_todos(
        """
        SELECT p.id AS paciente_id, p.primer_nombre, p.primer_apellido, p.documento, p.celular,
               p.direccion, p.zona_ciudad, MAX(pr.fecha) AS ultima_visita
        FROM pacientes p
        JOIN programaciones pr ON pr.paciente_id = p.id
        WHERE p.zona_ciudad = 'Cordilleranos' AND p.estado = 'Activo'
          AND pr.servicio IN (?, ?) AND pr.estado = 'Completada'
        GROUP BY p.id
        HAVING MAX(pr.fecha) <= ?
        """,
        (SERVICIO_PRIMERA_VISITA, SERVICIO_VISITA_SEGUIMIENTO, fecha_limite),
    )

    candidatos = []
    for fila in filas:
        f = dict(fila)
        # Se busca (o se deja pendiente de crear manualmente) una sesión de
        # Medicina General ya asignada y sin programar -- si el paciente no
        # tiene ninguna sesión de seguimiento asignada todavía, se marca
        # igual como candidato, pero sin planilla_id (hay que asignarle
        # el servicio primero desde "Servicios Asignados").
        servicio = consultar_uno(
            "SELECT id FROM servicios_paciente WHERE paciente_id=? AND tipo_servicio=? AND estado='Activo' ORDER BY id DESC LIMIT 1",
            (f["paciente_id"], SERVICIO_VISITA_SEGUIMIENTO),
        )
        planilla_id = _primera_planilla_pendiente(dict(servicio)["id"]) if servicio else None
        candidatos.append({
            **f, "planilla_id": planilla_id, "servicio": SERVICIO_VISITA_SEGUIMIENTO,
            "motivo": f"Cordilleranos — se cumplió el mes desde su última visita ({f['ultima_visita'][:10]})",
        })
    return candidatos


def generar_informe_confirmacion_pdf(programacion_ids: list) -> str:
    """
    Arma el PDF con el detalle de las visitas recién
    programadas -- pensado para mandárselo a quien se encarga
    de llamar a los pacientes a confirmar la visita del día
    siguiente: nombre, documento, dirección, celular, hora
    propuesta, y con qué profesional.
    """
    from pathlib import Path
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from core.config import EXPORTS_DIR

    marcadores = ",".join("?" * len(programacion_ids))
    filas = consultar_todos(
        f"""
        SELECT pr.fecha, pr.hora_inicio, pr.servicio,
               p.primer_nombre, p.primer_apellido, p.documento, p.celular, p.direccion, p.zona_ciudad,
               pf.primer_nombre AS prof_nombre, pf.primer_apellido AS prof_apellido
        FROM programaciones pr
        JOIN pacientes p ON p.id = pr.paciente_id
        LEFT JOIN profesionales pf ON pf.id = pr.profesional_id
        WHERE pr.id IN ({marcadores})
        ORDER BY p.zona_ciudad, pr.hora_inicio
        """,
        tuple(programacion_ids),
    )
    visitas = [dict(f) for f in filas]

    carpeta = Path(EXPORTS_DIR) / "informes_confirmacion"
    carpeta.mkdir(parents=True, exist_ok=True)
    fecha_reporte = visitas[0]["fecha"][:10] if visitas else date.today().isoformat()
    ruta = carpeta / f"informe_confirmacion_{fecha_reporte}.pdf"

    base = getSampleStyleSheet()
    titulo = ParagraphStyle("Titulo", parent=base["Heading1"], fontSize=15, textColor=colors.HexColor("#0a8f86"), spaceAfter=4)
    subtitulo = ParagraphStyle("Subtitulo", parent=base["Normal"], fontSize=10, textColor=colors.grey, spaceAfter=12)

    doc = SimpleDocTemplate(str(ruta), pagesize=letter, topMargin=1.8 * cm, bottomMargin=1.8 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm)

    elementos = [
        Paragraph("HomeCare del Quindío I.P.S.", titulo),
        Paragraph(f"Visitas médicas a confirmar — {fecha_reporte}", ParagraphStyle("Sub2", parent=base["Heading2"], fontSize=13, spaceAfter=4)),
        Paragraph(f"{len(visitas)} visita(s) programada(s). Por favor confirmar con cada paciente antes de la visita.", subtitulo),
    ]

    zona_actual = None
    filas_tabla = [["Hora", "Paciente", "Documento", "Celular", "Dirección", "Profesional"]]
    for v in visitas:
        zona = v.get("zona_ciudad") or "Sin zona"
        if zona != zona_actual:
            if zona_actual is not None:
                elementos.append(_tabla_informe(filas_tabla))
                filas_tabla = [["Hora", "Paciente", "Documento", "Celular", "Dirección", "Profesional"]]
            elementos.append(Paragraph(f"📍 {zona}", ParagraphStyle("Zona", parent=base["Heading3"], fontSize=12, textColor=colors.HexColor("#0a8f86"), spaceBefore=10, spaceAfter=4)))
            zona_actual = zona

        nombre_paciente = f"{v['primer_nombre']} {v['primer_apellido']}"
        nombre_prof = f"{v.get('prof_nombre','')} {v.get('prof_apellido','')}".strip() or "Sin asignar"
        filas_tabla.append([
            v["hora_inicio"], nombre_paciente, v["documento"] or "", v["celular"] or "sin celular",
            (v["direccion"] or "")[:35], nombre_prof,
        ])

    if len(filas_tabla) > 1:
        elementos.append(_tabla_informe(filas_tabla))

    doc.build(elementos)
    return str(ruta)


def _tabla_informe(filas):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle

    tabla = Table(filas, colWidths=[1.6 * cm, 3.4 * cm, 2.3 * cm, 2.5 * cm, 4.5 * cm, 3 * cm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a8f86")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tabla


def obtener_posible_programacion(fecha_objetivo=None) -> dict:
    fecha_objetivo = fecha_objetivo or calcular_proximo_dia_habil()

    todos = _candidatos_primera_visita() + _candidatos_seguimiento_medico() + _candidatos_cordilleranos()

    # Se agrupa por zona y, dentro de cada zona, por servicio --
    # así se ve de un vistazo cuántos hay de cada tipo en cada sector.
    agrupado = {}
    for c in todos:
        zona = c.get("zona_ciudad") or "Sin zona asignada"
        agrupado.setdefault(zona, {})
        servicio = c["servicio"]
        agrupado[zona].setdefault(servicio, []).append(c)

    zonas_resultado = []
    for zona in list(ZONAS_CIUDAD) + ["Sin zona asignada"]:
        if zona not in agrupado:
            continue
        servicios_zona = [{"servicio": s, "pacientes": pacientes} for s, pacientes in agrupado[zona].items()]
        total_zona = sum(len(sv["pacientes"]) for sv in servicios_zona)
        zonas_resultado.append({"zona": zona, "servicios": servicios_zona, "total": total_zona})

    return {
        "fecha_objetivo": fecha_objetivo,
        "es_cordilleranos_incluido": True,
        "zonas": zonas_resultado,
        "total_candidatos": len(todos),
    }
