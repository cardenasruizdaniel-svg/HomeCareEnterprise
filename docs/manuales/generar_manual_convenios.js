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
        children: [new TextRun({ text: "Manual de Convenios EPS y Facturación por Plan", bold: true, size: 44 })],
        spacing: { after: 200 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "Parametrización de tarifas, topes de servicios, y generación automática de facturación electrónica a las EPS", italics: true, color: COLOR_GRIS, size: 22 })],
        spacing: { after: 400 },
      }),
      cajaNota(
        "⚠ Documento delicado — de uso interno",
        "Este módulo gestiona directamente los valores que se cobran a cada EPS y la generación de facturación electrónica. Cualquier cambio en las tarifas o en los topes de servicios debe hacerse con conocimiento del área administrativa/financiera, ya que afecta directamente lo que se le factura a cada entidad.",
        "FFE3E3",
      ),
      new Paragraph({ children: [new PageBreak()] }),

      // ===================== 1. INTRODUCCIÓN =====================
      titulo("1. ¿Para qué sirve este módulo?"),
      parrafo(
        "Cada EPS le paga a HomeCare del Quindío I.P.S. según un convenio pactado, que normalmente incluye un número de sesiones o visitas de cada servicio (terapias, enfermería, medicina general, psicología, etc.) por cada paciente, dentro de un periodo determinado. Cuando un paciente supera esa cantidad, los servicios adicionales se cobran a un valor distinto."
      ),
      parrafo(
        "El módulo de Convenios EPS le permite configurar esas reglas UNA sola vez por cada EPS, y a partir de ahí el sistema:"
      ),
      vineta("Cuenta automáticamente cuántas veces se le ha prestado cada servicio a un paciente, dentro del periodo vigente."),
      vineta("Decide solo si ese servicio se cobra al valor normal (incluido en el plan) o al valor adicional (una vez se pasó el tope)."),
      vineta("Genera la cuenta por cobrar a la EPS cada vez que un profesional completa una visita — sin que nadie tenga que hacerlo a mano."),
      vineta("Le permite, al final del periodo de corte, generar las facturas electrónicas ya agrupadas como usted prefiera."),
      espacio(),

      // ===================== 2. CONCEPTOS =====================
      titulo("2. Conceptos clave, antes de empezar"),

      subtitulo("2.1 Convenio"),
      parrafo("Es el contrato/plan pactado con una EPS específica. Una misma EPS puede tener varios convenios si maneja distintos planes (por ejemplo, un plan estándar y uno ampliado)."),

      subtitulo("2.2 Plan de servicios"),
      parrafo("Dentro de cada convenio, se configura QUÉ servicios cubre, y para cada uno:"),
      tabla(
        ["Campo", "Qué significa"],
        [
          ["Cantidad incluida", "Cuántas veces se cubre ese servicio dentro de un periodo, sin cobrar el valor adicional."],
          ["Se reinicia cada (días)", "Cada cuántos días se vuelve a contar desde cero — 30 para algo mensual, 90 para algo trimestral."],
          ["Valor normal", "Lo que se cobra por cada uso MIENTRAS esté dentro del tope."],
          ["Valor adicional", "Lo que se cobra por cada uso EXCEDENTE, una vez se pasó el tope."],
          ["Grupo (tope compartido)", "Opcional — cuando varios servicios distintos deben compartir un mismo tope (ver ejemplo abajo)."],
        ],
        [3200, 6300]
      ),
      espacio(),

      cajaNota(
        "📌 Ejemplo real: las 4 terapias",
        "El paciente tiene derecho a 12 sesiones de terapia al mes, repartidas como sea entre Terapia Física, Terapia Ocupacional, Terapia Respiratoria y Fonoaudiología. Para lograr esto, se configuran las 4 como servicios distintos (cada una con su propio valor), pero a las 4 se les pone el MISMO texto en \"Grupo\", por ejemplo \"Terapias\". El sistema entonces las cuenta juntas: la sesión número 13 de cualquiera de las 4 (sin importar cuál) sale como adicional.",
        COLOR_FONDO_TABLA
      ),
      espacio(),

      subtitulo("2.3 Ciclo (el periodo que se reinicia)"),
      parrafo(
        "El conteo NO se reinicia el día 1 de cada mes calendario — se reinicia cada N días DESDE LA FECHA en que el paciente ingresó a ese plan. Por ejemplo, si un paciente ingresó el 5 de julio, y el servicio se reinicia cada 30 días, el primer periodo va del 5 de julio al 3 de agosto, el segundo del 4 de agosto al 2 de septiembre, y así sucesivamente."
      ),
      espacio(),

      // ===================== 3. CREAR UN CONVENIO =====================
      titulo("3. Crear un convenio nuevo"),
      numerada("Ir al menú \u201cConvenios EPS (Parametrización)\u201d.", 1),
      numerada("Presionar \u201cNuevo convenio\u201d.", 2),
      numerada("Llenar: nombre de la EPS, NIT de la EPS (importante — ver nota más abajo), nombre del plan, número de convenio si aplica, y fechas de vigencia.", 3),
      numerada("Guardar — lo lleva directo a la pantalla para configurar el plan de servicios.", 4),
      espacio(),
      cajaNota(
        "⚠ El NIT de la EPS es obligatorio para facturar correctamente",
        "La factura electrónica SIEMPRE se emite a nombre de la EPS (no del paciente) — es ella quien tiene el contrato y quien paga. Si no se registra su NIT aquí, la factura quedará incompleta en ese dato y habrá que corregirla manualmente.",
        "FFE3E3"
      ),
      espacio(),

      // ===================== 4. CONFIGURAR EL PLAN =====================
      titulo("4. Configurar el plan de servicios"),
      parrafo("Dentro del convenio ya creado, en \u201cPlan de servicios\u201d, se presiona \u201cAgregar servicio al plan\u201d por cada concepto que cubra ese convenio."),
      cajaNota(
        "⚠ El nombre debe coincidir exactamente",
        "El campo \u201cNombre del servicio\u201d debe escribirse EXACTAMENTE igual a como se llama el servicio cuando se programa la visita del paciente (por ejemplo: \u201cTerapia Física\u201d, \u201cVisita de enfermería profesional\u201d). Si no coincide exactamente, el sistema no va a reconocer que ese servicio pertenece al plan, y no generará ninguna cuenta por cobrar para él.",
        "FFE3E3"
      ),
      espacio(),
      parrafo("Ejemplo de un plan típico configurado:"),
      tabla(
        ["Servicio", "Grupo", "Incluidos", "Cada (días)", "Normal", "Adicional"],
        [
          ["Terapia Física", "Terapias", "12", "30", "$45.000", "$38.000"],
          ["Terapia Ocupacional", "Terapias", "12", "30", "$45.000", "$38.000"],
          ["Terapia Respiratoria", "Terapias", "12", "30", "$48.000", "$40.000"],
          ["Fonoaudiología", "Terapias", "12", "30", "$45.000", "$38.000"],
          ["Visita de enfermería profesional", "—", "1", "30", "$60.000", "$55.000"],
          ["Visita de valoración médica inicial", "—", "1", "30", "$90.000", "$80.000"],
          ["Psicología", "—", "1", "90", "$70.000", "$65.000"],
          ["Trabajo social", "—", "1", "90", "$65.000", "$60.000"],
        ],
        [2600, 1300, 1200, 1300, 1300, 1300]
      ),
      espacio(),

      // ===================== 5. ASIGNAR AL PACIENTE =====================
      titulo("5. Asignar el convenio a un paciente"),
      numerada("Desde la misma pantalla del convenio, en \u201cAsignar este plan a un paciente\u201d, buscar al paciente por nombre o documento.", 1),
      numerada("Indicar la \u201cFecha de ingreso al plan\u201d — esta es la fecha que se usa como punto de partida para contar los ciclos, así que debe ser exacta.", 2),
      numerada("Presionar \u201cAsignar\u201d.", 3),
      parrafo("Si el paciente ya tenía otro convenio asignado, ese anterior queda archivado en su historial (no se pierde), y el nuevo pasa a ser el activo."),
      espacio(),

      // ===================== 6. FACTURACIÓN AUTOMÁTICA =====================
      titulo("6. Cómo se genera la cuenta por cobrar (automático)"),
      parrafo("No hay que hacer nada manual para esto. Cada vez que un profesional marca una visita como completada (desde la app, al finalizar la atención), el sistema:"),
      numerada("Revisa si el paciente tiene un convenio EPS asignado.", 1),
      numerada("Revisa si el servicio de esa visita está contemplado en el plan del convenio.", 2),
      numerada("Calcula en qué ciclo va (según la fecha de ingreso del paciente al plan).", 3),
      numerada("Cuenta cuántas veces se ha usado ese servicio (o su grupo compartido) en ese mismo ciclo.", 4),
      numerada("Si todavía está dentro del tope, genera la cuenta al valor normal; si ya se pasó, la genera al valor adicional.", 5),
      parrafo("Si el paciente NO tiene convenio asignado, o el servicio prestado no está en su plan, simplemente no se genera ninguna cuenta — no es un error, solo significa que ese servicio no se está facturando a ninguna EPS por este medio."),
      espacio(),

      // ===================== 7. FACTURACIÓN =====================
      titulo("7. Generar las facturas (al momento del corte)"),
      parrafo("En \u201cFacturación por Plan\u201d se ve, agrupado por EPS, todo lo que está pendiente de facturar en el rango de fechas que se elija. Desde ahí se generan las facturas, escogiendo cómo agruparlas:"),
      tabla(
        ["Modo", "Qué hace", "Cuándo usarlo"],
        [
          ["Por EPS", "Una sola factura que junta TODOS los pacientes y servicios de esa EPS en el periodo.", "Cuando la EPS pide un solo documento consolidado por periodo."],
          ["Por paciente", "Una factura por cada paciente, con todos los servicios que se le prestaron juntos.", "Cuando se necesita ver claramente cuánto se generó por cada paciente."],
          ["Por paciente y servicio", "Una factura separada por cada combinación de paciente + tipo de servicio.", "Cuando la EPS exige el detalle más desglosado posible."],
        ],
        [2200, 3800, 3300]
      ),
      espacio(),
      cajaNota(
        "✅ Importante: la factura SIEMPRE queda a nombre de la EPS",
        "Sin importar el modo que se elija, el \u201ccomprador\u201d legal de la factura electrónica es siempre la EPS (con su NIT) — nunca un paciente individual, porque el contrato es con la EPS. Aun así, dentro del detalle de la factura (y en el PDF) se ve claramente qué paciente recibió cada servicio.",
        COLOR_FONDO_TABLA
      ),
      espacio(),
      parrafo("Una vez generadas, esas cuentas quedan marcadas como \u201cFacturado\u201d y ya no vuelven a aparecer como pendientes — así no hay riesgo de cobrar dos veces lo mismo."),
      espacio(),

      // ===================== 8. PREGUNTAS FRECUENTES =====================
      titulo("8. Preguntas frecuentes"),

      subtitulo("¿Qué pasa si cambian las tarifas de una EPS?"),
      parrafo("Se entra al convenio correspondiente y se edita el servicio afectado (valor normal y/o adicional) — el cambio aplica desde ese momento en adelante; lo ya facturado no se modifica."),

      subtitulo("¿Qué pasa si la EPS aumenta el número de sesiones cubiertas (por ejemplo, de 12 a 16 terapias)?"),
      parrafo("Se edita el mismo servicio y se cambia \u201cCantidad incluida\u201d — aplica para los ciclos que se calculen de ahí en adelante."),

      subtitulo("¿Se puede tener más de un convenio vigente para la misma EPS?"),
      parrafo("Sí — por ejemplo, si maneja un plan estándar y uno ampliado. Cada paciente solo puede tener UN convenio activo a la vez, así que se elige cuál le corresponde al asignarlo."),

      subtitulo("¿Qué pasa si un paciente cambia de EPS?"),
      parrafo("Se le asigna el nuevo convenio desde la pantalla correspondiente — el anterior queda en su historial, y los ciclos del nuevo convenio empiezan a contar desde la nueva fecha de ingreso que se indique."),

      subtitulo("¿Qué pasa si se completa una visita de un servicio que no está en el plan del paciente?"),
      parrafo("No pasa nada malo — simplemente no se genera ninguna cuenta por cobrar para ese servicio específico, porque el sistema entiende que no está cubierto por el convenio."),

      espacio(),
      new Paragraph({
        children: [new TextRun({ text: "HomeCare Enterprise — Manual interno de Convenios EPS", italics: true, color: COLOR_GRIS, size: 18 })],
      }),
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  require("fs").writeFileSync("Manual_Convenios_EPS_Facturacion.docx", buffer);
  console.log("Manual generado correctamente");
});
