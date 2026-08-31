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
      new Paragraph({ children: [new TextRun({ text: "Protocolo Operativo de Toma de Muestras y Lista de Supervisión", bold: true, size: 34 })], spacing: { after: 200 } }),
      new Paragraph({ children: [new TextRun({ text: "Guía paso a paso para el auxiliar que toma la muestra, y para quien supervisa que se haga bien", italics: true, color: COLOR_GRIS, size: 22 })], spacing: { after: 400 } }),
      cajaNota(
        "🩸 Para quién es este manual",
        "Parte 1 (protocolo clínico) es para el auxiliar o profesional que toma muestras en el domicilio del paciente. Parte 2 (lista de supervisión) es para Calidad/Coordinación, que audita en sitio que el protocolo se esté cumpliendo.",
        COLOR_FONDO_TABLA
      ),
      new Paragraph({ children: [new PageBreak()] }),

      // ===================== PARTE 1: PROTOCOLO =====================
      titulo("Parte 1 — Protocolo paso a paso"),
      parrafo("Estos son los pasos correctos, en orden, para tomar una muestra a domicilio con seguridad para el paciente y validez para el laboratorio. Es el mismo estándar contra el que se audita en la Lista de Supervisión (Parte 2)."),
      espacio(),

      subtitulo("1. Identificación del paciente"),
      numerada("Pida al paciente (o a su acudiente) que diga su nombre completo en voz alta — nunca lo diga usted primero ni asuma que la persona frente a usted es el paciente correcto.", 1),
      numerada("Solicite el documento de identidad y compárelo con la orden del examen.", 2),
      numerada("Confirme un segundo dato (fecha de nacimiento, número de historia clínica) para descartar homónimos.", 3),
      numerada("Si el paciente está inconsciente, es menor de edad, o tiene alguna barrera de comunicación, verifique su identidad con el acompañante presente.", 4),
      espacio(),

      subtitulo("2. Verificación de datos demográficos"),
      numerada("Confirme el sexo del paciente y su procedencia (EPS/asegurador, servicio).", 1),
      numerada("Revise que los datos que va a poner en el rótulo coincidan exactamente con la orden médica y con lo que aparece en el sistema.", 2),
      espacio(),

      subtitulo("3. Antes de la punción"),
      numerada("Higiene de manos — siempre, antes de tocar cualquier insumo.", 1),
      numerada("Colóquese los elementos de protección personal (guantes, tapabocas).", 2),
      numerada("Revise la fecha de vencimiento y el estado de los tubos, agujas y demás insumos que va a usar.", 3),
      numerada("Seleccione el tubo o recipiente correcto según el examen solicitado — el color de la tapa importa (ver el Manual de Trazabilidad de Muestras para la tabla completa).", 4),
      espacio(),

      subtitulo("4. Durante la punción"),
      numerada("Realice la antisepsia del sitio de punción.", 1),
      numerada("Aplique la técnica correcta de punción venosa o capilar, según el protocolo institucional.", 2),
      numerada("Respete el orden de llenado de los tubos cuando el examen lo requiera (orden de extracción).", 3),
      espacio(),

      subtitulo("5. Inmediatamente después de la toma"),
      numerada("Rotule los tubos de inmediato, en presencia del paciente — nunca después, y nunca en otro lugar.", 1),
      numerada("El rótulo debe incluir: nombre completo, documento de identidad, fecha, hora, y tipo de muestra.", 2),
      numerada("Homogenice las muestras que lo requieran (inversión suave, el número de veces que indique el tipo de tubo).", 3),
      numerada("Descarte los elementos cortopunzantes en el guardián — nunca en la basura común.", 4),
      numerada("Aplique presión y/o apósito en el sitio de punción, y verifique que no siga sangrando antes de retirarse.", 5),
      espacio(),

      subtitulo("6. Cierre del procedimiento"),
      numerada("Registre el procedimiento en el sistema (módulo de Trazabilidad de Muestras) o en la planilla correspondiente.", 1),
      numerada("Transporte y almacene la muestra en las condiciones que requiera (temperatura, tiempo máximo, protección de la luz).", 2),
      numerada("Durante todo el procedimiento, trate al paciente con respeto, amabilidad y privacidad.", 3),
      espacio(),

      cajaNota(
        "🔗 Esto se conecta con el sistema",
        "Cada uno de estos 23 pasos es exactamente lo que un supervisor verifica con la Lista de Supervisión digital (Parte 2) — y el registro final se hace en el módulo de Trazabilidad de Muestras, que ya trae la lista completa de tipos de tubo y sus colores.",
        COLOR_FONDO_TABLA
      ),
      new Paragraph({ children: [new PageBreak()] }),

      // ===================== PARTE 2: LISTA DE SUPERVISIÓN =====================
      titulo("Parte 2 — Lista de Supervisión digital"),
      parrafo("Herramienta para que Calidad/Coordinación audite en sitio, sin papel, cómo un auxiliar está tomando las muestras — mismos 23 puntos del protocolo de la Parte 1."),
      espacio(),

      subtitulo("Cómo registrar una supervisión"),
      numerada("Ir a Muestras Pendientes de Entrega → Supervisión Toma de Muestras → Nueva supervisión.", 1),
      numerada("Llenar la fecha, el punto de toma (dirección/IPS), y el nombre del auxiliar supervisado.", 2),
      numerada("Para cada uno de los 23 puntos, marcar Cumple / No cumple / N/A — y agregar una observación cuando algo no cumpla, para que quede claro qué corregir.", 3),
      numerada("Guardar — el sistema calcula solo el porcentaje de cumplimiento (sobre los puntos que sí aplicaban ese día).", 4),
      espacio(),

      cajaNota(
        "📊 Cómo se calcula el porcentaje",
        "Se calcula solo sobre los puntos marcados Cumple o No cumple — los marcados N/A no cuentan ni a favor ni en contra, porque simplemente no aplicaron ese día (por ejemplo, el orden de llenado de tubos no aplica si solo se tomó un tubo).",
        COLOR_FONDO_TABLA
      ),
      espacio(),

      subtitulo("Los 23 puntos verificados"),
      tabla(
        ["Bloque", "Cuántos puntos"],
        [
          ["1. Identificación del paciente", "5"],
          ["2. Verificación de datos demográficos", "3"],
          ["3. Supervisión de la toma de muestras (técnica)", "15"],
        ],
        [6500, 2500]
      ),
      espacio(),
      parrafo("El listado completo con cada punto exacto está en la Parte 1 de este manual — son el mismo protocolo, visto desde dos ángulos: cómo hacerlo (Parte 1) y cómo verificar que se hizo bien (Parte 2)."),

      espacio(),
      new Paragraph({ children: [new TextRun({ text: "HomeCare Enterprise — Protocolo Operativo de Toma de Muestras y Lista de Supervisión", italics: true, color: COLOR_GRIS, size: 18 })] }),
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  require("fs").writeFileSync("Manual_Protocolo_Toma_Muestras_Supervision.docx", buffer);
  console.log("Manual generado correctamente");
});
