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
      new Paragraph({ children: [new TextRun({ text: "Manual de Trazabilidad — Toma de Muestras de Laboratorio", bold: true, size: 40 })], spacing: { after: 200 } }),
      new Paragraph({ children: [new TextRun({ text: "Cadena de custodia, tipos de recipientes, y envío de indicaciones al paciente", italics: true, color: COLOR_GRIS, size: 22 })], spacing: { after: 400 } }),
      cajaNota(
        "🩸 Por qué importa este manual",
        "Una muestra mal recolectada, mal rotulada, o entregada tarde al laboratorio se pierde o se daña — obligando a repetir la visita y a que el paciente vuelva a pasar por el procedimiento. Seguir este proceso al pie de la letra evita eso.",
        "FFE3E3"
      ),
      new Paragraph({ children: [new PageBreak()] }),

      // ===================== 1. INTRODUCCIÓN =====================
      titulo("1. ¿Para qué sirve este módulo?"),
      parrafo("El módulo de Trazabilidad de Muestras registra, con fecha y hora exactas, cada paso por el que pasa una muestra desde que se recolecta en el domicilio del paciente hasta que el laboratorio la procesa:"),
      vineta("Quién la recolectó, cuándo, y en qué tipo de recipiente."),
      vineta("En qué condiciones se transportó (temperatura ambiente, refrigerada, etc.)."),
      vineta("A qué laboratorio se entregó, cuándo, y quién la recibió allá."),
      vineta("Si hubo alguna incidencia (derrame, rotura, rechazo) — con el motivo exacto."),
      espacio(),
      cajaNota("✅ Esto no es un formulario más", "Es la cadena de custodia legal de la muestra — si algo sale mal, este historial es lo que permite saber exactamente en qué punto pasó.", COLOR_FONDO_TABLA),
      espacio(),

      // ===================== 2. TIPOS DE RECIPIENTE =====================
      titulo("2. Tipos de recipiente — el color de la tapa importa"),
      parrafo("Cada tubo tiene un aditivo distinto según el color de su tapa. Usar el tubo equivocado inutiliza la muestra, sin importar qué tan bien se haya tomado."),
      tabla(
        ["Color de tapa", "Contiene", "Se usa para"],
        [
          ["Roja", "Sin anticoagulante", "Química sanguínea, serología"],
          ["Lila / morada", "EDTA", "Hematología, cuadro hemático"],
          ["Azul", "Citrato de sodio", "Pruebas de coagulación"],
          ["Amarilla", "Gel separador", "Química, hormonas"],
          ["Gris", "Fluoruro de sodio", "Glicemia"],
          ["Verde", "Heparina", "Química especial"],
        ],
        [2500, 3000, 4000]
      ),
      espacio(),
      parrafo("Para orina y materia fecal se usan frascos estériles de boca ancha (no tubos) — el sistema ya trae la lista completa al momento de registrar."),
      espacio(),

      // ===================== 3. REGISTRAR LA RECOLECCIÓN =====================
      titulo("3. Registrar la recolección de una muestra"),
      numerada("Entrar a la ficha del paciente → botón \u201cToma de Muestras\u201d → \u201cRegistrar nueva muestra\u201d.", 1),
      numerada("Elegir el tipo de muestra (sangre, orina, materia fecal, etc.) y el tipo exacto de recipiente usado.", 2),
      numerada("Registrar la fecha y hora EXACTA de la recolección — no la fecha de la visita, sino el momento real en que se tomó la muestra.", 3),
      numerada("Indicar las condiciones de transporte (temperatura ambiente, refrigerada, etc.) según lo que requiera ese examen.", 4),
      numerada("Tomarle una foto a la muestra ya etiquetada — sirve como respaldo visual de que se rotuló correctamente.", 5),
      numerada("Guardar — la muestra queda en estado \u201cRecolectada\u201d, primer eslabón de la cadena de custodia.", 6),
      espacio(),

      // ===================== 4. CADENA DE CUSTODIA =====================
      titulo("4. Avanzar la cadena de custodia"),
      parrafo("Desde la pantalla de la muestra, se puede ir actualizando su estado a medida que avanza:"),
      tabla(
        ["Estado", "Qué significa"],
        [
          ["Recolectada", "Se acaba de tomar en el domicilio del paciente."],
          ["En tránsito", "Va camino al laboratorio."],
          ["Entregada al laboratorio", "Ya la recibió el laboratorio — queda registrada la fecha automáticamente, y se puede indicar quién entrega y quién recibe."],
          ["Procesada", "El laboratorio ya generó el resultado."],
          ["Rechazada", "El laboratorio no la pudo procesar — es OBLIGATORIO indicar el motivo exacto."],
        ],
        [3200, 6300]
      ),
      espacio(),
      cajaNota("⚠ Toda la historia queda visible", "Cada cambio de estado se guarda por separado, sin borrar los anteriores — se puede ver la línea de tiempo completa de la muestra en cualquier momento.", "FFE3E3"),
      espacio(),

      // ===================== 5. RECOMENDACIONES AL PACIENTE =====================
      titulo("5. Enviar las indicaciones al paciente antes de la toma"),
      parrafo("El sistema trae un módulo aparte, \u201cRecomendaciones e Instrucciones\u201d, con las indicaciones estándar para los exámenes más comunes (ayuno, tipo de recolección, cuidados especiales) — ya cargadas desde el primer día, y se pueden editar o agregar más cuando haga falta."),
      numerada("Desde la misma pantalla de registrar una muestra, buscar el examen en el cuadro \u201cEnviar indicaciones al paciente\u201d.", 1),
      numerada("Elegir la recomendación correspondiente y darle \u201cEnviar\u201d.", 2),
      numerada("El paciente la recibe por WhatsApp y por correo, con las indicaciones completas.", 3),
      espacio(),
      cajaNota(
        "📌 Lo ideal: enviarlas ANTES de la visita",
        "Aunque se puede enviar el mismo día, lo mejor es mandarlas con anticipación (al programar la visita), para que el paciente llegue preparado — sobre todo en exámenes que requieren ayuno o una recolección especial.",
        COLOR_FONDO_TABLA
      ),
      espacio(),

      // ===================== 6. BUENAS PRÁCTICAS =====================
      titulo("6. Buenas prácticas para que la muestra no se dañe"),
      vineta("Rotular el recipiente ANTES de tomar la muestra, no después."),
      vineta("Verificar que el tipo de tubo/frasco corresponda exactamente al examen solicitado."),
      vineta("Respetar las condiciones de transporte indicadas (una muestra que debía ir refrigerada y no lo estuvo, se rechaza)."),
      vineta("Entregar al laboratorio dentro del tiempo indicado — no dejar muestras acumuladas de un día para otro."),
      vineta("Si algo sale mal, registrar la incidencia de inmediato, con el detalle exacto — no dejarlo para después."),
      espacio(),

      // ===================== 7. PREGUNTAS FRECUENTES =====================
      titulo("7. Preguntas frecuentes"),
      subtitulo("¿Qué pasa si me equivoco de tipo de recipiente al registrar?"),
      parrafo("Se puede editar el registro mientras la muestra siga en estado \u201cRecolectada\u201d — una vez avanza en la cadena, se recomienda dejar la corrección como una observación en el siguiente cambio de estado, para no perder el rastro de lo que realmente pasó."),
      subtitulo("¿Es obligatorio tomar la foto de la muestra?"),
      parrafo("Se recomienda siempre, pero no es obligatoria — sí lo son el tipo de muestra, el tipo de recipiente, y la fecha/hora de recolección."),
      subtitulo("¿Dónde veo las muestras que llevan mucho tiempo sin entregar al laboratorio?"),
      parrafo("En el menú \u201cMuestras Pendientes de Entrega\u201d — también aparece como alerta en el Dashboard si hay alguna pendiente."),

      espacio(),
      new Paragraph({ children: [new TextRun({ text: "HomeCare Enterprise — Manual interno de Trazabilidad de Toma de Muestras", italics: true, color: COLOR_GRIS, size: 18 })] }),
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  require("fs").writeFileSync("Manual_Trazabilidad_Toma_Muestras.docx", buffer);
  console.log("Manual generado correctamente");
});
