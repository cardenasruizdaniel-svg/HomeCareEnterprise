"""
HomeCare Enterprise - Recomendaciones e Instrucciones para Exámenes

Documentos con las indicaciones que debe seguir el paciente
antes de un examen de laboratorio (ayuno, tipo de recolección,
cuidados especiales) -- para enviárselos por WhatsApp o correo
antes de la toma de muestra, y evitar que la muestra salga mal
por falta de preparación del paciente.

Este módulo es DISTINTO al de "Recomendaciones Médicas" (que
hace parte de la historia clínica / plan de diagnóstico) -- este
es contenido informativo dirigido al PACIENTE, no un registro
clínico del profesional.
"""

from database.database import consultar_todos, consultar_uno, ejecutar

CATEGORIAS = ("Sangre", "Orina", "Materia fecal", "Otros fluidos", "Imagenología", "General")


def listar_todo(incluir_inactivos=True):
    sql = "SELECT * FROM recomendaciones_examenes"
    if not incluir_inactivos:
        sql += " WHERE activo=1"
    sql += " ORDER BY categoria, titulo"
    return [dict(f) for f in consultar_todos(sql)]


def listar_activas_por_categoria():
    filas = consultar_todos("SELECT * FROM recomendaciones_examenes WHERE activo=1 ORDER BY categoria, titulo")
    agrupado = {}
    for f in filas:
        item = dict(f)
        agrupado.setdefault(item["categoria"], []).append(item)
    return agrupado


def obtener(recomendacion_id: int):
    fila = consultar_uno("SELECT * FROM recomendaciones_examenes WHERE id=?", (recomendacion_id,))
    return dict(fila) if fila else None


def buscar_por_tipo_examen(texto: str):
    """Busca la recomendación cuyo tipo de examen coincida (parcial) con el texto -- para sugerirla automáticamente al programar un examen con ese nombre."""
    if not texto:
        return []
    filas = consultar_todos(
        "SELECT * FROM recomendaciones_examenes WHERE activo=1 AND tipo_examen LIKE ?",
        (f"%{texto}%",),
    )
    return [dict(f) for f in filas]


def crear(titulo, tipo_examen, categoria, descripcion, contenido_texto, archivo_path=None, usuario_id=None) -> int:
    if not titulo or not titulo.strip():
        raise ValueError("Debe indicar el título de la recomendación.")
    if not tipo_examen or not tipo_examen.strip():
        raise ValueError("Debe indicar a qué examen corresponde esta recomendación.")
    if not contenido_texto and not archivo_path:
        raise ValueError("Debe escribir el contenido de la recomendación, o adjuntar un archivo.")

    return ejecutar(
        """
        INSERT INTO recomendaciones_examenes(titulo, tipo_examen, categoria, descripcion, contenido_texto, archivo_path, usuario_creacion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (titulo.strip(), tipo_examen.strip(), categoria or "General", descripcion or "", contenido_texto or "", archivo_path, usuario_id),
    )


def actualizar(recomendacion_id, titulo, tipo_examen, categoria, descripcion, contenido_texto, archivo_path=None):
    if not titulo or not titulo.strip():
        raise ValueError("Debe indicar el título de la recomendación.")

    ejecutar(
        """
        UPDATE recomendaciones_examenes SET
            titulo=?, tipo_examen=?, categoria=?, descripcion=?, contenido_texto=?, archivo_path=COALESCE(?, archivo_path)
        WHERE id=?
        """,
        (titulo.strip(), tipo_examen.strip(), categoria or "General", descripcion or "", contenido_texto or "", archivo_path, recomendacion_id),
    )


def desactivar(recomendacion_id: int):
    ejecutar("UPDATE recomendaciones_examenes SET activo=0 WHERE id=?", (recomendacion_id,))


def reactivar(recomendacion_id: int):
    ejecutar("UPDATE recomendaciones_examenes SET activo=1 WHERE id=?", (recomendacion_id,))


def generar_pdf(recomendacion_id: int) -> str:
    """
    Genera un PDF con el título y el contenido de la
    recomendación -- para poder descargarla, imprimirla, o
    adjuntarla al enviarla por WhatsApp/correo. Si la
    recomendación tiene un archivo propio adjunto (subido por
    el usuario), ese archivo se usa directamente en vez de
    generar uno nuevo.
    """
    from pathlib import Path
    from datetime import datetime
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from core.config import EXPORTS_DIR, RECURSOS_DIR

    recomendacion = obtener(recomendacion_id)
    if not recomendacion:
        raise ValueError("La recomendación indicada no existe.")

    # Si ya tiene un archivo propio adjunto, se usa ese directamente -- no hace falta generar nada nuevo.
    if recomendacion.get("archivo_path"):
        ruta_archivo = Path(RECURSOS_DIR) / recomendacion["archivo_path"]
        if ruta_archivo.exists():
            return str(ruta_archivo)

    carpeta = Path(EXPORTS_DIR) / "recomendaciones"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"recomendacion_{recomendacion_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"

    base = getSampleStyleSheet()
    titulo_estilo = ParagraphStyle("Titulo", parent=base["Heading1"], fontSize=15, textColor=colors.HexColor("#0a8f86"), spaceAfter=4)
    subtitulo_estilo = ParagraphStyle("Subtitulo", parent=base["Normal"], fontSize=11, textColor=colors.grey, spaceAfter=14)
    normal = ParagraphStyle("NormalDoc", parent=base["Normal"], fontSize=11, spaceAfter=8, leading=16)

    doc = SimpleDocTemplate(str(ruta), pagesize=letter, topMargin=2.5 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm)

    elementos = [
        Paragraph("HomeCare del Quindío I.P.S.", titulo_estilo),
        Paragraph(f"Indicaciones para: {recomendacion['tipo_examen']}", ParagraphStyle("Sec", parent=base["Heading2"], fontSize=13, spaceAfter=6)),
        Paragraph(recomendacion["titulo"], subtitulo_estilo),
    ]

    for parrafo_texto in (recomendacion.get("contenido_texto") or "").split("\n"):
        if parrafo_texto.strip():
            elementos.append(Paragraph(parrafo_texto.replace("•", "&#8226;"), normal))

    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph(
        "Ante cualquier duda sobre estas indicaciones, comuníquese con su equipo de atención antes de la toma de la muestra.",
        ParagraphStyle("Nota", parent=base["Normal"], fontSize=9, textColor=colors.grey),
    ))

    doc.build(elementos)
    return str(ruta)


def enviar_a_paciente(recomendacion_id: int, paciente_id: int, base_url: str = None) -> dict:
    """
    Envía la recomendación al paciente por WhatsApp y correo,
    reutilizando el mismo mecanismo ya usado para enviar órdenes
    médicas y la historia clínica -- para que el paciente sepa
    con anticipación cómo prepararse para el examen.

    'base_url' es la URL pública del sistema (se calcula sola a
    partir de la petición que llega, no depende de tener
    configurada ninguna variable de entorno aparte) -- se usa
    para que WhatsApp pueda descargar el PDF adjunto.
    """
    from services.notificaciones_service import enviar_whatsapp, enviar_email

    recomendacion = obtener(recomendacion_id)
    if not recomendacion:
        raise ValueError("La recomendación indicada no existe.")

    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    if not paciente:
        raise ValueError("El paciente indicado no existe.")
    paciente = dict(paciente)

    # El PDF se genera siempre (o se usa el archivo propio si ya
    # tiene uno adjunto) -- así el paciente recibe un documento
    # que puede guardar e imprimir, no solo un mensaje de texto.
    ruta_pdf = generar_pdf(recomendacion_id)

    nombre_paciente = f"{paciente.get('primer_nombre','')} {paciente.get('primer_apellido','')}".strip()
    resultado = {"whatsapp": {"enviado": False}, "correo": {"enviado": False}}

    mensaje_texto = (
        f"Hola {nombre_paciente}, HomeCare IPS le comparte las indicaciones para su examen "
        f"de *{recomendacion['tipo_examen']}*:\n\n{recomendacion['contenido_texto']}\n\n"
        f"Por favor téngalas en cuenta antes de la toma de la muestra. Le adjuntamos también el documento."
    )

    celular_paciente = paciente.get("celular") or paciente.get("telefono")
    if celular_paciente:
        adjunto_url = None
        if base_url:
            adjunto_url = f"{base_url.rstrip('/')}/recomendaciones/{recomendacion_id}/pdf"
        resultado["whatsapp"] = enviar_whatsapp(numero=celular_paciente, mensaje=mensaje_texto, adjunto_url=adjunto_url)
    else:
        resultado["whatsapp"] = {"enviado": False, "motivo": "Paciente sin celular registrado."}

    correo_paciente = paciente.get("correo")
    if correo_paciente:
        resultado["correo"] = enviar_email(
            destinatario=correo_paciente, asunto=f"HomeCare IPS - Indicaciones para su examen ({recomendacion['tipo_examen']})",
            cuerpo_html=(
                f"<p>Hola {nombre_paciente},</p>"
                f"<p>Estas son las indicaciones para su examen de <b>{recomendacion['tipo_examen']}</b>:</p>"
                f"<p>{recomendacion['contenido_texto'].replace(chr(10), '<br>')}</p>"
                f"<p style='color:#888;font-size:12px'>HomeCare IPS - Mensaje generado automáticamente.</p>"
            ),
            adjunto_path=ruta_pdf,
        )
    else:
        resultado["correo"] = {"enviado": False, "motivo": "Paciente sin correo registrado."}

    return resultado


def sembrar_recomendaciones_estandar(usuario_id=None) -> list:
    """
    Siembra las recomendaciones más comunes usadas en el sector
    salud colombiano para los exámenes de laboratorio más
    solicitados en atención domiciliaria -- así el módulo
    arranca con contenido útil desde el primer día, que se
    puede editar o ampliar cuando haga falta.
    """
    ya_existe = consultar_uno("SELECT COUNT(*) AS total FROM recomendaciones_examenes")
    if ya_existe and dict(ya_existe)["total"] > 0:
        return []

    recomendaciones_iniciales = [
        (
            "Glicemia en ayunas", "Glicemia", "Sangre",
            "Preparación para la toma de glicemia (azúcar en sangre) en ayunas.",
            "• Debe estar en ayuno de 8 a 12 horas antes del examen (no comer ni beber nada, excepto agua).\n"
            "• Puede tomar sus medicamentos habituales con un sorbo de agua, salvo indicación médica contraria.\n"
            "• Evite hacer ejercicio intenso el día anterior.\n"
            "• No consuma alcohol 24 horas antes del examen.",
        ),
        (
            "Perfil lipídico (colesterol y triglicéridos)", "Perfil lipídico", "Sangre",
            "Preparación para la toma de colesterol total, HDL, LDL y triglicéridos.",
            "• Ayuno estricto de 9 a 12 horas (solo se permite tomar agua).\n"
            "• Evite el consumo de alcohol durante las 72 horas previas al examen.\n"
            "• Mantenga su dieta habitual los días anteriores (no cambie su alimentación antes del examen).\n"
            "• Evite el ejercicio físico intenso 24 horas antes.",
        ),
        (
            "Cuadro hemático (hemograma)", "Hemograma", "Sangre",
            "Preparación para la toma de cuadro hemático completo.",
            "• No requiere ayuno obligatorio, pero se recomienda estar en ayunas de 4 horas si se va a tomar junto con otros exámenes.\n"
            "• Evite el ejercicio físico intenso antes de la toma.\n"
            "• Informe al profesional si está tomando anticoagulantes o tiene tendencia a sangrado.",
        ),
        (
            "Uroanálisis (parcial de orina)", "Uroanálisis", "Orina",
            "Preparación para la toma de muestra de orina para parcial de orina.",
            "• Se debe recolectar la PRIMERA orina de la mañana (es la más concentrada y da mejores resultados).\n"
            "• Realice aseo genital previo con agua y jabón, sin usar productos íntimos perfumados.\n"
            "• Deseche el primer chorro de orina y recolecte la muestra de la mitad del chorro (chorro medio), en el frasco estéril entregado.\n"
            "• Entregue la muestra al profesional dentro de la primera hora después de recolectada.\n"
            "• Evite la toma durante el período menstrual, de ser posible.",
        ),
        (
            "Urocultivo", "Urocultivo", "Orina",
            "Preparación para la toma de muestra de orina para cultivo (identificar infección urinaria).",
            "• Realice un aseo genital riguroso con agua y jabón antes de la toma.\n"
            "• Recolecte la muestra de la mitad del chorro (chorro medio) en el frasco ESTÉRIL entregado, sin tocar el interior del frasco ni la tapa.\n"
            "• Preferiblemente la primera orina de la mañana.\n"
            "• Si está tomando antibióticos, informe al profesional antes de la toma, ya que puede afectar el resultado.",
        ),
        (
            "Coprológico (examen de materia fecal)", "Coprológico", "Materia fecal",
            "Preparación para la toma de muestra de materia fecal.",
            "• La muestra debe ser reciente (recolectada máximo 1-2 horas antes de la entrega al profesional).\n"
            "• Recolecte la muestra en el frasco limpio y seco entregado, evitando que se contamine con orina o agua del sanitario.\n"
            "• No es necesario ayuno.\n"
            "• Informe si está tomando algún medicamento antiparasitario o antibiótico recientemente.",
        ),
        (
            "Antígeno prostático (PSA)", "PSA", "Sangre",
            "Preparación para la toma de antígeno prostático específico.",
            "• Evite la eyaculación durante las 48 horas previas al examen.\n"
            "• Evite montar en bicicleta los 2 días anteriores.\n"
            "• Si se realizó un tacto rectal recientemente, informe al profesional, ya que puede alterar el resultado — se recomienda esperar al menos 1 semana después de un tacto rectal.\n"
            "• No requiere ayuno.",
        ),
        (
            "Hormonas tiroideas (TSH, T3, T4)", "Tiroideas", "Sangre",
            "Preparación para la toma de perfil tiroideo.",
            "• Se recomienda tomar la muestra en ayunas y en horas de la mañana, ya que los niveles hormonales varían durante el día.\n"
            "• Informe si está tomando medicamentos para la tiroides — el profesional le indicará si debe tomarlos antes o después del examen.\n"
            "• Evite el estrés físico o emocional intenso antes de la toma.",
        ),
        (
            "Prueba de embarazo en orina (BHCG)", "Embarazo BHCG", "Orina",
            "Preparación para la prueba de embarazo en orina.",
            "• Se recomienda usar la primera orina de la mañana, ya que está más concentrada y da un resultado más confiable.\n"
            "• Recolecte la muestra en el frasco limpio entregado.\n"
            "• No requiere ayuno ni preparación especial adicional.",
        ),
        (
            "Toma de muestra en general — recomendaciones para el paciente y la familia", "General", "General",
            "Recomendaciones generales que aplican a cualquier toma de muestra en el domicilio.",
            "• Tenga lista su identificación (documento) y la orden médica del examen.\n"
            "• Informe al profesional cualquier alergia, medicamento que esté tomando, o condición especial (embarazo, anticoagulantes, etc.).\n"
            "• Procure tener un espacio limpio, bien iluminado, y con una superficie firme donde el profesional pueda trabajar.\n"
            "• Si tiene mascotas, es preferible mantenerlas en otra habitación durante la toma de la muestra.\n"
            "• Guarde el comprobante de la toma de muestra para el seguimiento de sus resultados.",
        ),
    ]

    creados = []
    for titulo, tipo_examen, categoria, descripcion, contenido in recomendaciones_iniciales:
        recomendacion_id = crear(titulo, tipo_examen, categoria, descripcion, contenido, usuario_id=usuario_id)
        creados.append(recomendacion_id)

    return creados
