"""
=========================================================
HomeCare Enterprise
Lote inicial ILUSTRATIVO de codigos CUPS para atencion
domiciliaria.

ADVERTENCIA IMPORTANTE: a diferencia del catalogo DIVIPOLA
(descargado directamente de la fuente oficial del DANE),
los codigos de este archivo se escribieron como referencia
general y NO estan verificados contra el listado vigente de
la Resolucion 2706 de 2025 (CUPS 2026). Sirven para probar
el flujo de busqueda/autocompletado, pero antes de usarlos
en un RIPS real hay que confirmarlos uno por uno contra la
fuente oficial:
https://web.sispro.gov.co/WebPublico/Consultas/ConsultarDetalleReferenciaBasica.aspx?Code=CUPS

La Clasificacion Unica de Procedimientos en Salud (CUPS)
tiene mas de 10.000 codigos y se actualiza por resolucion.
Para cargar el catalogo oficial completo, usar
CUPSRepository.importar_csv() con el archivo que publica el
Ministerio.

Cada tupla: (codigo, descripcion, capitulo)
=========================================================
"""

CUPS_DOMICILIARIO = [
    ("890201", "Consulta de primera vez por medicina general", "Consulta externa"),
    ("890202", "Consulta de control o de seguimiento por medicina general", "Consulta externa"),
    ("890301", "Consulta de primera vez por especialista", "Consulta externa"),
    ("890302", "Consulta de control o de seguimiento por especialista", "Consulta externa"),
    ("890381", "Consulta de primera vez por enfermería", "Consulta externa"),
    ("890382", "Consulta de control o de seguimiento por enfermería", "Consulta externa"),
    ("890386", "Consulta de primera vez por psicología", "Consulta externa"),
    ("890387", "Consulta de control o de seguimiento por psicología", "Consulta externa"),
    ("890388", "Consulta de primera vez por nutrición y dietética", "Consulta externa"),
    ("890389", "Consulta de control o de seguimiento por nutrición y dietética", "Consulta externa"),
    ("890391", "Consulta de primera vez por fisioterapia", "Consulta externa"),
    ("890392", "Consulta de control o de seguimiento por fisioterapia", "Consulta externa"),
    ("890396", "Consulta de primera vez por terapia respiratoria", "Consulta externa"),
    ("890397", "Consulta de control o de seguimiento por terapia respiratoria", "Consulta externa"),
    ("933101", "Terapia física integral", "Terapias"),
    ("933301", "Terapia respiratoria integral", "Terapias"),
    ("939101", "Curación de heridas, úlceras y/o quemaduras grado I-II", "Procedimientos de enfermería"),
    ("939102", "Curación de heridas, úlceras y/o quemaduras grado III-IV", "Procedimientos de enfermería"),
    ("939200", "Aplicación de inyección intramuscular", "Procedimientos de enfermería"),
    ("939201", "Aplicación de inyección endovenosa", "Procedimientos de enfermería"),
    ("939301", "Toma de signos vitales", "Procedimientos de enfermería"),
    ("939401", "Colocación de sonda vesical", "Procedimientos de enfermería"),
    ("939501", "Colocación de sonda nasogástrica", "Procedimientos de enfermería"),
    ("990601", "Visita domiciliaria por medicina general", "Atención domiciliaria"),
    ("990602", "Visita domiciliaria por enfermería", "Atención domiciliaria"),
    ("990603", "Visita domiciliaria por especialista", "Atención domiciliaria"),
]
