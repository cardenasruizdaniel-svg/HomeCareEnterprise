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
      new Paragraph({ children: [new TextRun({ text: "Manual de Instalación Local y Acceso Externo", bold: true, size: 40 })], spacing: { after: 200 } }),
      new Paragraph({ children: [new TextRun({ text: "Cómo tener el sistema corriendo en un equipo del consultorio, y cómo entrar a él desde afuera para hacer pruebas", italics: true, color: COLOR_GRIS, size: 22 })], spacing: { after: 400 } }),
      cajaNota(
        "🖥️ Para quién es este manual",
        "Para quien necesite tener HomeCare Enterprise corriendo directamente en un computador (sin depender de Render), y poder entrar a probarlo desde un celular u otra red — ideal para pruebas rápidas antes de subir un cambio a producción.",
        COLOR_FONDO_TABLA
      ),
      new Paragraph({ children: [new PageBreak()] }),

      // ===================== 1. QUE INCLUYE =====================
      titulo("1. ¿Qué incluye esta configuración?"),
      parrafo("Tres archivos, ya incluidos en la carpeta del programa (dentro de deploy/windows), que dejan todo listo con solo hacer doble clic:"),
      tabla(
        ["Archivo", "Qué hace"],
        [
          ["0_Activar_Todo.bat", "El de uso diario: abre el programa Y el acceso externo juntos, en dos ventanas, con un solo doble clic."],
          ["1_Iniciar_Programa_Local.bat", "Solo arranca el programa en este equipo (sin acceso externo)."],
          ["2_Abrir_Acceso_Externo.bat", "Solo abre el túnel de acceso externo (el programa ya debe estar corriendo)."],
        ],
        [3800, 5700]
      ),
      espacio(),
      cajaNota("✅ No hay que escribir ningún comando", "Una vez todo esté configurado la primera vez (siguiente sección), el uso del día a día es solo doble clic en 0_Activar_Todo.bat.", COLOR_FONDO_TABLA),
      espacio(),

      // ===================== 2. INSTALACION LOCAL =====================
      titulo("2. Instalación local del programa"),
      parrafo("Hay dos formas de tener el programa en un equipo — según para qué lo vaya a usar:"),
      subtitulo("Opción A — Instalación completa (recomendada para dejarlo funcionando siempre)"),
      parrafo("Usa el instalador que ya trae el sistema, que deja el programa arrancando solo cada vez que se prende el computador. Está documentado en detalle en el Manual de Instalación (ya disponible en el módulo de Capacitación) — en resumen:"),
      numerada("Clic derecho sobre Instalar_Windows.bat → \u201cEjecutar como administrador\u201d.", 1),
      numerada("El instalador revisa/instala Python, copia el programa a C:\\HomeCareEnterprise, instala las dependencias, y lo deja arrancando automáticamente con Windows.", 2),
      espacio(),
      subtitulo("Opción B — Copia de trabajo rápida (para pruebas y desarrollo)"),
      parrafo("Si ya tiene la carpeta del proyecto en el equipo (por ejemplo, la misma que usa para subir cambios a GitHub), no hace falta el instalador completo — los archivos .bat de este manual detectan solos si hay una instalación completa o no, y funcionan en cualquiera de los dos casos."),
      espacio(),

      // ===================== 3. CONFIGURACION =====================
      titulo("3. Configuración y parametrización de los datos"),
      parrafo("Una vez el programa esté corriendo (local o en Render), la parametrización de la empresa (datos legales, EPS, catálogos de servicios, usuarios, roles) se hace igual en cualquiera de los dos casos, desde dentro del sistema — está documentada en detalle en el Manual de Parametrización (también en el módulo de Capacitación)."),
      cajaNota("📌 Un solo lugar para los manuales", "Todos los manuales del sistema (instalación, parametrización, funcionamiento, y este de acceso externo) quedan disponibles dentro del programa, en el menú \u201cCapacitación\u201d.", COLOR_FONDO_TABLA),
      espacio(),

      // ===================== 4. ACCESO EXTERNO =====================
      titulo("4. Acceso externo — configuración inicial (una sola vez)"),
      parrafo("Esto es lo que permite entrar al programa desde un celular, otra oficina, o cualquier red distinta a la del computador donde está corriendo. Se usa una herramienta gratuita llamada ngrok, que crea una dirección pública temporal (https://...) apuntando al programa local."),
      subtitulo("Paso 1 — Instalar ngrok"),
      parrafo("La forma más simple: buscar \u201cngrok\u201d en la Microsoft Store, y darle \u201cAbrir\u201d/\u201cInstalar\u201d. También se puede descargar directo de ngrok.com/download."),
      subtitulo("Paso 2 — Crear una cuenta gratuita"),
      parrafo("En https://dashboard.ngrok.com/signup — es gratis, solo pide correo y contraseña."),
      subtitulo("Paso 3 — Configurar la clave personal (authtoken)"),
      parrafo("Dentro del dashboard de ngrok, en \u201cYour Authtoken\u201d, copiar la clave larga que aparece ahí (NO el texto de ejemplo que dice \"$YOUR_AUTHTOKEN\" — debe ser la clave real, distinta para cada cuenta). Luego, en una ventana de PowerShell:"),
      codigo("ngrok config add-authtoken PEGAR_AQUI_LA_CLAVE_REAL"),
      espacio(),
      cajaNota("⚠ Esto se hace UNA sola vez", "Una vez guardada la clave, queda configurada en el equipo para siempre — no hay que repetir este paso cada vez que se use el túnel.", "FFE3E3"),
      espacio(),

      // ===================== 5. USO DIARIO =====================
      titulo("5. Uso del día a día"),
      numerada("Doble clic en 0_Activar_Todo.bat.", 1),
      numerada("Se abren dos ventanas — esperar a que la primera diga \u201cSistema listo\u201d.", 2),
      numerada("En la segunda ventana (\u201cHomeCare - Acceso Externo\u201d), buscar la línea que dice \u201cForwarding\u201d — la dirección que aparece ahí (https://algo.ngrok-free.dev) es la que se usa desde afuera.", 3),
      numerada("Para entrar desde un celular: esa misma dirección, con datos móviles (no WiFi de la misma red) para probar de verdad desde afuera.", 4),
      numerada("Para la app móvil de campo, agregar /app al final de esa dirección.", 5),
      espacio(),
      cajaNota(
        "🔄 La dirección cambia cada vez",
        "Con el plan gratis de ngrok, cada vez que se cierra y se vuelve a abrir el túnel, la dirección https:// es distinta — hay que revisarla de nuevo en la ventana cada vez. Si se necesita una dirección fija que nunca cambie, ngrok ofrece \u201cdominios reservados\u201d (gratis uno, o de pago para varios) configurables desde su propio panel.",
        COLOR_FONDO_TABLA
      ),
      espacio(),

      // ===================== 6. ARRANQUE AUTOMATICO =====================
      titulo("6. Arranque automático — sin abrir PowerShell nunca más"),
      parrafo("Para no tener que abrir PowerShell cada vez, hay un configurador que deja todo arrancando solo con Windows, y dos accesos directos en el Escritorio para el uso diario."),
      subtitulo("Configurar (una sola vez)"),
      numerada("Doble clic en Configurar_Inicio_Automatico.bat (dentro de deploy/windows).", 1),
      numerada("Confirma que se crearon el arranque automático y los dos accesos directos del Escritorio.", 2),
      espacio(),
      parrafo("A partir de ahí, cada vez que se prenda el computador y se inicie sesión en Windows, el programa y el túnel arrancan solos (en ventanas minimizadas, sin taparle la pantalla a nadie)."),
      subtitulo("Los dos íconos del Escritorio"),
      tabla(
        ["Ícono", "Para qué sirve"],
        [
          ["HomeCare - Iniciar Todo", "Arranca el programa y el túnel manualmente, sin tener que reiniciar el computador (por ejemplo, si se cerraron las ventanas sin querer)."],
          ["HomeCare - Ver Dirección Externa", "Consulta la dirección https:// actual, la copia sola al portapapeles, y la abre en el navegador — sin tener que buscarla en ninguna ventana."],
        ],
        [4200, 5300]
      ),
      espacio(),
      cajaNota(
        "💡 Recomendado: usar siempre el ícono de \u201cVer Dirección Externa\u201d",
        "Es la forma más rápida de conseguir la dirección del momento para compartirla o abrirla en el celular — la copia sola al portapapeles, lista para pegar.",
        COLOR_FONDO_TABLA
      ),
      espacio(),

      // ===================== 7. SEGURIDAD =====================
      titulo("7. Seguridad — a tener en cuenta"),
      vineta("Mientras el túnel esté abierto, cualquiera con esa dirección puede llegar a la pantalla de login del sistema (aunque sí necesita usuario y contraseña válidos para hacer algo) — no compartir la dirección con quien no deba tenerla."),
      vineta("Cerrar la ventana del túnel (o del programa) cuando ya no se esté usando, sobre todo si el equipo se va a dejar solo."),
      vineta("Este mecanismo es para pruebas y demostraciones — para producción real y permanente, la recomendación sigue siendo el despliegue en Render (o el servidor que la empresa disponga), no dejar un computador de oficina como servidor final."),
      espacio(),

      // ===================== 7. PREGUNTAS FRECUENTES =====================
      titulo("8. Preguntas frecuentes"),
      subtitulo("Me sale \u201c502 Bad Gateway\u201d al entrar por la dirección externa"),
      parrafo("Significa que el túnel está funcionando, pero no encuentra el programa corriendo — verificar que la ventana \u201cHomeCare - Programa\u201d siga abierta y sin errores."),
      subtitulo("Me sale \u201caccepts 1 arg(s), received 0\u201d al configurar el authtoken"),
      parrafo("Se está copiando el texto de ejemplo (\"$YOUR_AUTHTOKEN\") en vez de la clave real — hay que copiar el texto largo que aparece en el dashboard de ngrok, no el nombre de la variable."),
      subtitulo("¿Puedo dejar esto encendido todo el tiempo, sin que nadie esté pendiente?"),
      parrafo("Sí — usando el configurador de arranque automático (sección 6). El programa y el túnel arrancan solos cada vez que se prende el computador, sin abrir PowerShell. La única salvedad: con el plan gratis de ngrok, la dirección https:// cambia en cada arranque — por eso conviene revisarla con el ícono \u201cVer Dirección Externa\u201d en vez de guardarla de un día para otro."),

      espacio(),
      new Paragraph({ children: [new TextRun({ text: "HomeCare Enterprise — Manual interno de Instalación Local y Acceso Externo", italics: true, color: COLOR_GRIS, size: 18 })] }),
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  require("fs").writeFileSync("Manual_Instalacion_Local_Acceso_Externo.docx", buffer);
  console.log("Manual generado correctamente");
});
