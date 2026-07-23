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
function parrafoRico(partes) {
  return new Paragraph({
    children: partes.map((p) => new TextRun({ text: p.texto, bold: p.bold || false, color: p.color || undefined })),
    spacing: { after: 160 },
  });
}
function vineta(texto, nivel = 0) {
  return new Paragraph({
    text: texto,
    bullet: { level: nivel },
    spacing: { after: 80 },
  });
}
function numerada(texto, indice) {
  return new Paragraph({
    children: [new TextRun({ text: `${indice}. `, bold: true, color: COLOR_MARCA }), new TextRun({ text: texto })],
    spacing: { after: 100 },
  });
}
function cajaNota(titulo, texto, colorFondo = COLOR_ALERTA) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            shading: { type: ShadingType.CLEAR, fill: colorFondo },
            children: [
              new Paragraph({ children: [new TextRun({ text: titulo, bold: true })], spacing: { after: 60 } }),
              new Paragraph({ children: [new TextRun({ text: texto })] }),
            ],
            margins: { top: 150, bottom: 150, left: 150, right: 150 },
          }),
        ],
      }),
    ],
  });
}
function espacio() {
  return new Paragraph({ text: "", spacing: { after: 120 } });
}

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
  const filaEncabezado = new TableRow({
    children: encabezados.map((e, i) => celda(e, { encabezado: true, ancho: anchos[i] })),
    tableHeader: true,
  });
  const filasDatos = filas.map((fila) => new TableRow({
    children: fila.map((valor, i) => celda(String(valor), { ancho: anchos[i] })),
  }));
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: anchos,
    rows: [filaEncabezado, ...filasDatos],
  });
}

const doc = new Document({
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 } } },
    children: [
      // ===================== PORTADA =====================
      new Paragraph({
        children: [new TextRun({ text: "HomeCare del Quindío I.P.S.", bold: true, size: 32, color: COLOR_MARCA })],
        spacing: { after: 100 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "Manual de Convenios EPS, Autorizaciones y Facturación", bold: true, size: 44 })],
        spacing: { after: 200 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "Convenio → Programa → Servicios, control automático de topes, autorizaciones de excedentes, y generación de facturación electrónica a las EPS", italics: true, color: COLOR_GRIS, size: 22 })],
        spacing: { after: 400 },
      }),
      cajaNota(
        "⚠ Documento delicado — de uso interno",
        "Este módulo gestiona directamente los valores que se cobran a cada EPS, las autorizaciones de servicios adicionales, y la generación de facturación electrónica. Cualquier cambio debe hacerse con conocimiento del área administrativa/financiera.",
        "FFE3E3",
      ),
      new Paragraph({ children: [new PageBreak()] }),

      // ===================== 1. INTRODUCCIÓN =====================
      titulo("1. ¿Para qué sirve este módulo?"),
      parrafo(
        "Cada EPS le paga a HomeCare del Quindío I.P.S. según uno o varios convenios pactados. Dentro de cada convenio, se contratan uno o varios PROGRAMAS (Crónicos, Paliativos, Materno, Respiratorio, Adulto Mayor, etc.), y cada programa incluye una cantidad determinada de cada tipo de servicio (terapias, enfermería, medicina general, etc.) dentro de un periodo."
      ),
      parrafo("El sistema controla todo esto automáticamente:"),
      vineta("Cuenta cuántas veces se ha usado cada servicio dentro del ciclo vigente del paciente."),
      vineta("Decide solo si un servicio se cobra al valor normal (incluido) o al valor adicional (excedente autorizado)."),
      vineta("BLOQUEA de verdad la programación de sesiones que superen lo autorizado, hasta que exista una autorización de la EPS para el excedente."),
      vineta("Genera la cuenta por cobrar automáticamente cada vez que se completa una visita."),
      vineta("Genera las facturas electrónicas agrupadas como usted prefiera al final del periodo."),
      espacio(),

      // ===================== 2. CONCEPTOS =====================
      titulo("2. Conceptos clave, antes de empezar"),

      subtitulo("2.1 Jerarquía del módulo"),
      parrafoRico([
        { texto: "EPS", bold: true }, { texto: " → " },
        { texto: "Convenio", bold: true, color: COLOR_MARCA }, { texto: " (el contrato marco: número, vigencia, NIT) → " },
        { texto: "Programa", bold: true, color: COLOR_MARCA }, { texto: " (Crónicos, Paliativos...) → " },
        { texto: "Servicios parametrizados", bold: true, color: COLOR_MARCA }, { texto: " (cuántas sesiones de cada uno incluye)." },
      ]),
      parrafo("Un convenio puede tener VARIOS programas. Un paciente se asigna a UN programa específico, no al convenio en general."),

      subtitulo("2.2 Servicios parametrizados de un programa"),
      tabla(
        ["Campo", "Qué significa"],
        [
          ["Cantidad incluida", "Cuántas veces se cubre ese servicio dentro de un periodo, sin cobrar el valor adicional."],
          ["Se reinicia cada (días)", "Cada cuántos días se vuelve a contar desde cero."],
          ["Valor normal", "Lo que se cobra por cada uso MIENTRAS esté dentro del tope."],
          ["Valor adicional", "Lo que se cobra por cada uso EXCEDENTE, ya autorizado por la EPS."],
          ["Grupo (tope compartido)", "Cuando varios servicios distintos deben compartir un mismo tope."],
        ],
        [3200, 6300]
      ),
      espacio(),
      cajaNota(
        "📌 Ejemplo real: las 4 terapias",
        "El paciente tiene derecho a 12 sesiones de terapia al mes en total, sin importar la mezcla. Se configuran las 4 terapias (Física, Ocupacional, Respiratoria, Fonoaudiología) como servicios distintos del mismo programa, cada una con su propio valor, pero con el MISMO texto en \"Grupo\" (ej. \"Terapias\"). El sistema las cuenta juntas: la sesión número 13 de cualquiera de las 4 excede el tope. La MEZCLA exacta (cuántas de cada tipo) la decide el médico al ordenarlas — la oficina solo parametriza el máximo total.",
        COLOR_FONDO_TABLA
      ),
      espacio(),

      subtitulo("2.3 Ciclo (el periodo que se reinicia)"),
      parrafo(
        "El conteo se reinicia cada N días DESDE LA FECHA de ingreso del paciente al programa — no el día 1 del mes calendario."
      ),
      espacio(),

      // ===================== 3. CREAR UN CONVENIO Y SUS PROGRAMAS =====================
      titulo("3. Crear un convenio y sus programas"),
      numerada("Ir a \u201cConvenios EPS (Parametrización)\u201d → \u201cNuevo convenio\u201d.", 1),
      numerada("Llenar: EPS, NIT de la EPS (importante para facturar correctamente), número de convenio, fechas de vigencia.", 2),
      numerada("Dentro del convenio ya creado, presionar \u201cNuevo programa\u201d por cada programa contratado (Crónicos, Paliativos, etc.) — el nombre se elige de los Programas de Atención ya creados en el sistema.", 3),
      numerada("Indicar el valor mensual contratado de ese programa.", 4),
      espacio(),
      cajaNota(
        "⚠ El NIT de la EPS es obligatorio para facturar correctamente",
        "La factura electrónica SIEMPRE se emite a nombre de la EPS (no del paciente). Si no se registra su NIT, la factura quedará incompleta.",
        "FFE3E3"
      ),
      espacio(),

      // ===================== 4. CONFIGURAR SERVICIOS DE UN PROGRAMA =====================
      titulo("4. Configurar los servicios de un programa"),
      parrafo("Dentro de cada programa, se presiona \u201cAgregar servicio\u201d por cada concepto que cubra ese programa específicamente."),
      cajaNota(
        "⚠ El nombre debe coincidir exactamente",
        "El servicio se elige de una LISTA (no se escribe a mano) — se toma automáticamente del catálogo de actividades del sistema, así siempre coincide con lo que se usa al programar visitas de los pacientes.",
        "FFE3E3"
      ),
      espacio(),

      // ===================== 5. ASIGNAR UN PROGRAMA AL PACIENTE =====================
      titulo("5. Asignar un programa a un paciente"),
      numerada("Desde el convenio, en \u201cAsignar un programa a un paciente\u201d, buscar al paciente por nombre o documento.", 1),
      numerada("Elegir el PROGRAMA específico (no solo el convenio) al que queda asignado.", 2),
      numerada("Indicar la fecha de ingreso — punto de partida para contar los ciclos.", 3),
      numerada("Opcionalmente: número de autorización de la EPS, médico tratante, y profesional tratante.", 4),
      numerada("La fecha \u201cautorizado hasta\u201d se sugiere sola a 3 meses si se deja vacía — se puede cambiar.", 5),
      espacio(),

      // ===================== 6. AUTORIZACIONES DE SERVICIOS ADICIONALES (NUEVO) =====================
      titulo("6. Cuando el médico pide más de lo autorizado — Autorizaciones de Servicios Adicionales"),
      parrafo(
        "Esta es la protección más importante del módulo: si el médico ordena más sesiones de un servicio de las que el programa tiene incluidas, el sistema BLOQUEA DE VERDAD esa parte excedente — no se puede programar, agendar ni asignar hasta que exista una autorización de la EPS."
      ),
      espacio(),
      subtitulo("6.1 Qué pasa exactamente"),
      cajaNota(
        "📌 Ejemplo real",
        "Un programa tiene 12 terapias incluidas. El médico ya usó las 12, y ordena 8 terapias más. El sistema NO programa ninguna de esas 8 — en su lugar, crea automáticamente una \u201csolicitud de autorización\u201d con estado \u201cPendiente autorización EPS\u201d, y avisa claramente que esas 8 sesiones quedan pendientes.",
        COLOR_FONDO_TABLA
      ),
      espacio(),
      parrafo("Si de lo que se pide, una PARTE sí cabe dentro de lo autorizado y otra parte no, el sistema programa automáticamente la parte que sí cabe, y deja como solicitud pendiente solo el excedente real."),
      espacio(),

      subtitulo("6.2 Cómo autorizar una solicitud pendiente"),
      numerada("Ir a \u201cAutorizaciones EPS\u201d en el menú (o desde la alerta del Dashboard).", 1),
      numerada("Buscar la solicitud en la pestaña \u201cPendientes\u201d.", 2),
      numerada("Presionar \u201cAutorizar\u201d, y registrar: número de autorización de la EPS, fecha, cantidad autorizada (puede ser menor a la solicitada, si la EPS aprobó menos), y el valor autorizado.", 3),
      numerada("Desde ese momento, esa cantidad autorizada queda disponible para programarse — se suma automáticamente al tope normal del programa.", 4),
      espacio(),
      cajaNota(
        "✅ Autorización parcial",
        "Si la EPS autoriza menos de lo solicitado (ej: 5 de las 8 pedidas), el sistema permite programar hasta esas 5 — al intentar programar la sexta, se vuelve a bloquear automáticamente, sin necesidad de configurar nada extra.",
        COLOR_FONDO_TABLA
      ),
      espacio(),
      subtitulo("6.3 Rechazar una solicitud"),
      parrafo("Si la EPS no autoriza el excedente, se marca como \u201cRechazada\u201d con el motivo — esas sesiones quedan definitivamente sin poder programarse por esta vía."),
      espacio(),

      // ===================== 7. FACTURACIÓN AUTOMÁTICA =====================
      titulo("7. Cómo se genera la cuenta por cobrar (automático)"),
      parrafo("Cada vez que se completa una visita, el sistema revisa si el paciente tiene un programa de EPS asignado, calcula el ciclo correspondiente, y genera la cuenta por cobrar al valor normal o adicional según corresponda — sin intervención manual."),
      espacio(),

      // ===================== 8. FACTURACIÓN =====================
      titulo("8. Generar las facturas (al momento del corte)"),
      parrafo("En \u201cFacturación por Plan\u201d se ve, agrupado por EPS, todo lo pendiente de facturar. Los modos de agrupación disponibles:"),
      tabla(
        ["Modo", "Qué hace"],
        [
          ["Por EPS", "Una sola factura que junta TODOS los pacientes y programas de esa EPS."],
          ["Por programa", "Una factura por cada programa, con todos sus pacientes juntos."],
          ["Por paciente", "Una factura por cada paciente, con todos sus servicios juntos."],
          ["Por paciente y servicio", "Una factura separada por cada combinación paciente + servicio."],
        ],
        [2600, 6900]
      ),
      espacio(),
      cajaNota(
        "✅ Importante: la factura SIEMPRE queda a nombre de la EPS",
        "Sin importar el modo elegido, el comprador legal de la factura es siempre la EPS (con su NIT) — el paciente aparece como detalle de cada línea.",
        COLOR_FONDO_TABLA
      ),
      espacio(),

      // ===================== 9. PREGUNTAS FRECUENTES =====================
      titulo("9. Preguntas frecuentes"),

      subtitulo("¿Un convenio puede tener varios programas al tiempo?"),
      parrafo("Sí — esa es justamente la idea. Un convenio con una EPS puede incluir el Programa Crónicos, el Programa Paliativos, etc., cada uno con su propio valor y sus propios servicios."),

      subtitulo("¿Qué pasa si cambian las tarifas de un programa?"),
      parrafo("Se entra al programa correspondiente y se edita el servicio afectado — el cambio aplica desde ese momento; lo ya facturado no se modifica."),

      subtitulo("¿El médico puede seguir mandando cualquier mezcla de terapias?"),
      parrafo("Sí. La oficina solo define el máximo TOTAL del grupo (ej. 12 terapias). El médico decide libremente cuántas de cada tipo específico, siempre que la suma no pase el máximo autorizado (más lo que se haya autorizado como adicional)."),

      subtitulo("¿Qué pasa con una solicitud de autorización que nunca se responde?"),
      parrafo("Queda visible indefinidamente en \u201cPendientes\u201d hasta que alguien la autorice o la rechace — no se pierde ni se vence sola."),

      subtitulo("¿Se puede tener más de un programa vigente para el mismo paciente?"),
      parrafo("No al mismo tiempo — cada paciente tiene un único programa activo. Si cambia de programa o de EPS, el anterior queda en su historial."),

      espacio(),
      new Paragraph({
        children: [new TextRun({ text: "HomeCare Enterprise — Manual interno de Convenios EPS, Autorizaciones y Facturación", italics: true, color: COLOR_GRIS, size: 18 })],
      }),
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  require("fs").writeFileSync("Manual_Convenios_EPS_Facturacion.docx", buffer);
  console.log("Manual generado correctamente");
});
