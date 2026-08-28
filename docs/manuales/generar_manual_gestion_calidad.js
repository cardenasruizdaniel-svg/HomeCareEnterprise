const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, BorderStyle, PageBreak, LevelFormat,
} = require("docx");

const COLOR_MARCA = "0A8F86";
const COLOR_ROSA = "FF3399";
const COLOR_GRIS = "6C757D";
const COLOR_FONDO_TABLA = "E5FBF9";
const COLOR_ALERTA = "FFF3CD";

function titulo(texto) {
  return new Paragraph({ text: texto, heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 200 } });
}
function subtitulo(texto) {
  return new Paragraph({ text: texto, heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 } });
}
function parrafo(texto, opciones = {}) {
  return new Paragraph({
    children: [new TextRun({ text: texto, bold: opciones.bold || false, italics: opciones.italics || false })],
    spacing: { after: 160 },
  });
}
function vineta(texto, nivel = 0) {
  return new Paragraph({ text: texto, bullet: { level: nivel }, spacing: { after: 80 } });
}
function numerada(texto, indice) {
  return new Paragraph({
    children: [new TextRun({ text: `${indice}. `, bold: true, color: COLOR_MARCA }), new TextRun({ text: texto })],
    spacing: { after: 100 },
  });
}
function codigo(texto) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [new TableRow({ children: [new TableCell({
      shading: { type: ShadingType.CLEAR, fill: "1F2937" },
      children: texto.split("\n").map((linea) => new Paragraph({
        children: [new TextRun({ text: linea, color: "E5FBF9", font: "Consolas" })],
      })),
      margins: { top: 120, bottom: 120, left: 150, right: 150 },
    })] })],
  });
}
function cajaNota(titulo, texto, colorFondo = COLOR_ALERTA) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [new TableRow({ children: [new TableCell({
      shading: { type: ShadingType.CLEAR, fill: colorFondo },
      children: [
        new Paragraph({ children: [new TextRun({ text: titulo, bold: true })], spacing: { after: 60 } }),
        new Paragraph({ children: [new TextRun({ text: texto })] }),
      ],
      margins: { top: 150, bottom: 150, left: 150, right: 150 },
    })] })],
  });
}
function espacio() { return new Paragraph({ text: "", spacing: { after: 120 } }); }

function celda(texto, opciones = {}) {
  return new TableCell({
    width: { size: opciones.ancho || 2000, type: WidthType.DXA },
    shading: opciones.encabezado ? { type: ShadingType.CLEAR, fill: COLOR_MARCA } : undefined,
    children: [new Paragraph({
      children: [new TextRun({ text: texto, bold: opciones.encabezado || false, color: opciones.encabezado ? "FFFFFF" : undefined })],
    })],
    margins: { top: 100, bottom: 100, left: 120, right: 120 },
  });
}
function tabla(encabezados, filas, anchos) {
  const filaEncabezado = new TableRow({ children: encabezados.map((e, i) => celda(e, { encabezado: true, ancho: anchos[i] })), tableHeader: true });
  const filasDatos = filas.map((fila) => new TableRow({ children: fila.map((valor, i) => celda(String(valor), { ancho: anchos[i] })) }));
  return new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, columnWidths: anchos, rows: [filaEncabezado, ...filasDatos] });
}

const doc = new Document({
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 } } },
    children: [
      // ===================== PORTADA =====================
      new Paragraph({ children: [new TextRun({ text: "HomeCare del Quindío I.P.S.", bold: true, size: 32, color: COLOR_MARCA })], spacing: { after: 100 } }),
      new Paragraph({ children: [new TextRun({ text: "Manual del Sistema de Gestión de Calidad, PQR/SIAU y Portal Web", bold: true, size: 36 })], spacing: { after: 200 } }),
      new Paragraph({ children: [new TextRun({ text: "PAMEC, auditorías, hallazgos, riesgos, seguridad del paciente, PQR con radicado, y el sitio público conectado al sistema", italics: true, color: COLOR_GRIS, size: 22 })], spacing: { after: 400 } }),
      cajaNota(
        "🩺 Para quién es este manual",
        "Para el equipo de Calidad, SIAU, y coordinación -- cubre el ciclo completo de gestión de calidad de la IPS, y cómo se conecta con el sitio web público que ven los pacientes y usuarios.",
        COLOR_FONDO_TABLA
      ),
      new Paragraph({ children: [new PageBreak()] }),

      // ===================== 1. VISION GENERAL =====================
      titulo("1. Visión general — cómo fluye la información"),
      parrafo("Todo el sistema sigue un mismo camino, de afuera hacia adentro:"),
      codigo("USUARIO / PACIENTE\n  -> PORTAL WEB (/portal)\n  -> PQR / SOLICITUD / CONTACTO\n  -> BANDEJA INTERNA (radicado + linea de tiempo)\n  -> Si amerita: HALLAZGO DE CALIDAD (analisis + acciones CAPA)\n  -> DASHBOARD GERENCIAL (alertas navegables)"),
      espacio(),
      parrafo("El Motor de Normatividad (Sección 2) es la base de todo lo demás -- ninguna resolución específica queda escrita en el código, precisamente porque la normativa cambia (la Resolución 3100 de 2019, por ejemplo, fue derogada por la Resolución 1732 de 2026)."),
      espacio(),

      // ===================== 2. MOTOR DE NORMATIVIDAD =====================
      titulo("2. Motor de Normatividad"),
      parrafo("En Gestión de Calidad → Normas Regulatorias se registra cada norma que aplica: tipo, número, año, entidad, estado (Vigente / En transición / Derogada), fechas de vigencia, y qué norma deroga (si reemplaza a otra)."),
      cajaNota("⚠ Revisar periódicamente", "El estado de una norma (Vigente, En transición, Derogada) hay que actualizarlo manualmente cuando cambie algo -- el sistema no lo hace solo, solo lo deja evidenciado y trazable.", "FFE3E3"),
      espacio(),

      // ===================== 3. CICLO DE CALIDAD (PHVA) =====================
      titulo("3. Ciclo de Calidad — Planear, Ejecutar, Verificar, Actuar"),
      subtitulo("PAMEC"),
      parrafo("Un ciclo PAMEC agrupa un periodo (ej. \u201cPAMEC 2026\u201d) con sus procesos priorizados -- cada proceso tiene un indicador, una meta, y se le va registrando el resultado real y el porcentaje de cumplimiento."),
      subtitulo("Auditorías de Calidad"),
      parrafo("Se crean con un tipo (Interna, PAMEC, Habilitación, Seguimiento, Seguridad del paciente), un objetivo y un alcance -- y opcionalmente se vinculan a un ciclo PAMEC. Durante la auditoría se registran los hallazgos; al cerrarla, el sistema calcula solo el porcentaje de cumplimiento según cuántos hallazgos fueron críticos o mayores."),
      subtitulo("Hallazgos y Acciones (CAPA)"),
      parrafo("Cada hallazgo se clasifica (Crítico / Mayor / Menor / Observación), se le hace un análisis de causa raíz (5 Porqués, Ishikawa, PHVA), y se le crean una o más acciones de mejora -- correctivas, preventivas, o de mejora."),
      cajaNota(
        "✅ Regla importante: no se puede cerrar un hallazgo sin verificar la eficacia",
        "Un hallazgo solo se puede cerrar si tiene al menos una acción que ya fue ejecutada Y verificada como eficaz -- el sistema lo bloquea si se intenta cerrar antes de tiempo.",
        COLOR_FONDO_TABLA
      ),
      espacio(),

      // ===================== 4. RIESGOS Y SEGURIDAD DEL PACIENTE =====================
      titulo("4. Matriz de Riesgos y Seguridad del Paciente"),
      subtitulo("Matriz de Riesgos"),
      parrafo("Cada riesgo se registra con su probabilidad y su impacto (5 niveles cada uno) -- el sistema calcula solo el nivel (Bajo / Medio / Alto / Extremo) usando una matriz estándar 5x5, sin necesidad de calcularlo a mano."),
      subtitulo("Seguridad del Paciente"),
      parrafo("Eventos adversos, incidentes, eventos centinela, caídas, medicamentos, etc. -- con severidad (Leve / Moderada / Grave / Centinela)."),
      cajaNota(
        "🔗 Conexión clave: escalar a hallazgo formal",
        "Un evento Grave o Centinela se puede \u201cescalar\u201d con un clic a un hallazgo de calidad, clasificado automáticamente como Crítico -- así hereda todo el rigor del ciclo CAPA (causa raíz, acciones verificables) sin tener que registrar todo de nuevo.",
        COLOR_FONDO_TABLA
      ),
      espacio(),

      // ===================== 5. PQR / SIAU =====================
      titulo("5. PQR / SIAU"),
      parrafo("Cada PQR recibe un radicado único (PQR-2026-000001) apenas se registra -- ya sea desde adentro (Gestión de Calidad → PQR/SIAU) o desde el portal público."),
      subtitulo("La bandeja interna"),
      parrafo("Muestra indicadores (vencidas, próximas a vencer, alto riesgo), permite asignar/reasignar el área responsable, cambiar el estado, agregar comentarios, y responder/cerrar -- todo queda en una línea de tiempo completa, visible en el detalle de cada PQR."),
      subtitulo("El seguimiento público"),
      parrafo("Cualquier persona puede consultar el estado de su PQR en /portal/pqr/seguimiento, con el radicado y una clave de seguimiento de 6 caracteres que se le entrega al presentarla -- sin necesidad de usuario del sistema."),
      cajaNota(
        "🔒 Privacidad -- muy importante",
        "El seguimiento público NUNCA muestra el contenido de la queja ni el de la respuesta interna -- solo el estado administrativo (Nueva, En trámite, Cerrada, etc.) y las fechas. Esto está probado con pruebas automatizadas que confirman que ese contenido nunca se filtra.",
        "FFE3E3"
      ),
      espacio(),

      // ===================== 6. PORTAL WEB PUBLICO =====================
      titulo("6. Portal Web Público"),
      parrafo("El sitio público vive en /portal -- Inicio, Servicios, Nosotros, Contacto, y Atención al Usuario (acceso a PQR). Todo el contenido (textos, misión/visión, teléfono, redes sociales, y la lista de servicios) se administra desde Gestión de Calidad → (menú) Portal Web Público, sin tocar código."),
      subtitulo("El formulario de Contacto"),
      parrafo("No crea una tabla de mensajes aparte -- reutiliza el mismo sistema de PQR (como tipo \u201cSolicitud\u201d), así que cualquier mensaje que llegue por ahí aparece en la misma bandeja interna, con su propio radicado."),
      subtitulo("SEO"),
      parrafo("El sitio incluye robots.txt, sitemap.xml, meta description, Open Graph, y datos estructurados Schema.org (tipo MedicalOrganization) -- para que buscadores como Google entiendan de qué se trata la página."),
      espacio(),

      // ===================== 7. DASHBOARD GERENCIAL =====================
      titulo("7. Dashboard Gerencial — alertas navegables"),
      parrafo("El Dashboard principal (la pantalla de inicio del sistema) muestra alertas de calidad junto a las demás alertas gerenciales -- cada una es un botón que lleva directo al detalle correspondiente:"),
      tabla(
        ["Alerta", "A dónde lleva"],
        [
          ["Eventos graves/centinela de seguridad", "Seguridad del Paciente"],
          ["PQR de alto riesgo / vencidas", "Bandeja PQR/SIAU"],
          ["Hallazgos críticos de calidad", "Listado de Hallazgos"],
          ["Riesgos altos/extremos activos", "Matriz de Riesgos"],
        ],
        [4500, 4500]
      ),
      espacio(),

      // ===================== 8. PRUEBAS AUTOMATIZADAS =====================
      titulo("8. Pruebas automatizadas"),
      parrafo("El sistema incluye una suite de pruebas (carpeta tests/) que se puede correr en cualquier momento para confirmar que todo sigue funcionando, antes de subir un cambio a producción:"),
      codigo("pip install pytest --break-system-packages\npytest -v"),
      espacio(),
      parrafo("Cubre: generación de radicados PQR, la matriz de riesgo, la regla de \u201cno cerrar hallazgo sin acción verificada\u201d, que el portal público nunca filtre información privada, el límite de envíos del formulario público, y que las rutas internas sigan exigiendo inicio de sesión."),

      espacio(),
      new Paragraph({ children: [new TextRun({ text: "HomeCare Enterprise — Manual del Sistema de Gestión de Calidad, PQR/SIAU y Portal Web", italics: true, color: COLOR_GRIS, size: 18 })] }),
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  require("fs").writeFileSync("Manual_Gestion_Calidad_PQR_Portal_Web.docx", buffer);
  console.log("Manual generado correctamente");
});
