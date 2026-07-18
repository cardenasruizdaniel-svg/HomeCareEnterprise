"""
=========================================================
HomeCare Enterprise
Lote inicial ILUSTRATIVO de codigos CIE-10 para atencion
domiciliaria (diagnosticos mas frecuentes en pacientes
cronicos, geriatricos, y de cuidado en casa).

ADVERTENCIA IMPORTANTE: igual que con CUPS y CUM, estos
codigos se escribieron como referencia general para poder
probar el flujo de busqueda/autocompletado, pero NO
reemplazan el listado oficial vigente. La Clasificacion
Internacional de Enfermedades (CIE-10), adoptada en Colombia
por el Ministerio de Salud, tiene mas de 14.000 codigos.
Antes de usar estos codigos en historia clinica real o en un
RIPS, se debe confirmar cada uno contra la fuente oficial:
https://web.sispro.gov.co/WebPublico/Consultas/ConsultarDetalleReferenciaBasica.aspx?Code=CIE10

Para cargar el catalogo oficial completo, usar
Cie10Repository.importar_csv() con el archivo que publica el
Ministerio de Salud / SISPRO (columnas: codigo,descripcion,capitulo).
=========================================================
"""

# (codigo, descripcion, capitulo)
CIE10_DOMICILIARIO = [
    # Enfermedades del sistema circulatorio
    ("I10X", "Hipertensión esencial (primaria)", "Enfermedades del sistema circulatorio"),
    ("I119", "Enfermedad cardíaca hipertensiva sin insuficiencia cardíaca (congestiva)", "Enfermedades del sistema circulatorio"),
    ("I500", "Insuficiencia cardíaca congestiva", "Enfermedades del sistema circulatorio"),
    ("I509", "Insuficiencia cardíaca, no especificada", "Enfermedades del sistema circulatorio"),
    ("I64X", "Accidente vascular encefálico agudo, no especificado como hemorrágico o isquémico", "Enfermedades del sistema circulatorio"),
    ("I694", "Secuelas de accidente vascular encefálico no especificado como hemorrágico o isquémico", "Enfermedades del sistema circulatorio"),
    ("I739", "Enfermedad vascular periférica, no especificada", "Enfermedades del sistema circulatorio"),
    ("I839", "Venas varicosas de los miembros inferiores sin úlcera ni inflamación", "Enfermedades del sistema circulatorio"),

    # Enfermedades endocrinas, nutricionales y metabólicas
    ("E119", "Diabetes mellitus no insulinodependiente sin mención de complicación", "Enfermedades endocrinas, nutricionales y metabólicas"),
    ("E118", "Diabetes mellitus no insulinodependiente con complicaciones no especificadas", "Enfermedades endocrinas, nutricionales y metabólicas"),
    ("E039", "Hipotiroidismo, no especificado", "Enfermedades endocrinas, nutricionales y metabólicas"),
    ("E440", "Desnutrición proteicocalórica moderada", "Enfermedades endocrinas, nutricionales y metabólicas"),
    ("E43X", "Desnutrición proteicocalórica severa, no especificada", "Enfermedades endocrinas, nutricionales y metabólicas"),
    ("E669", "Obesidad, no especificada", "Enfermedades endocrinas, nutricionales y metabólicas"),
    ("E871", "Hipoosmolalidad e hiponatremia", "Enfermedades endocrinas, nutricionales y metabólicas"),

    # Enfermedades del sistema respiratorio
    ("J449", "Enfermedad pulmonar obstructiva crónica, no especificada", "Enfermedades del sistema respiratorio"),
    ("J189", "Neumonía, no especificada", "Enfermedades del sistema respiratorio"),
    ("J459", "Asma, no especificada", "Enfermedades del sistema respiratorio"),
    ("J969", "Insuficiencia respiratoria, no especificada", "Enfermedades del sistema respiratorio"),
    ("J690", "Neumonitis debida a alimentos y vómito", "Enfermedades del sistema respiratorio"),
    ("R05X", "Tos", "Enfermedades del sistema respiratorio"),
    ("R062", "Sibilancias", "Enfermedades del sistema respiratorio"),

    # Enfermedades del sistema nervioso
    ("G20X", "Enfermedad de Parkinson", "Enfermedades del sistema nervioso"),
    ("G309", "Enfermedad de Alzheimer, no especificada", "Enfermedades del sistema nervioso"),
    ("G819", "Hemiplejía, no especificada", "Enfermedades del sistema nervioso"),
    ("G839", "Síndrome paralítico, no especificado", "Enfermedades del sistema nervioso"),
    ("G40X", "Epilepsia", "Enfermedades del sistema nervioso"),
    ("R470", "Disfasia y afasia", "Enfermedades del sistema nervioso"),

    # Trastornos mentales y del comportamiento
    ("F03X", "Demencia no especificada", "Trastornos mentales y del comportamiento"),
    ("F419", "Trastorno de ansiedad, no especificado", "Trastornos mentales y del comportamiento"),
    ("F329", "Episodio depresivo, no especificado", "Trastornos mentales y del comportamiento"),
    ("F05X", "Delirium no inducido por alcohol ni por otras sustancias psicoactivas", "Trastornos mentales y del comportamiento"),

    # Enfermedades del sistema osteomuscular
    ("M545", "Lumbago no especificado", "Enfermedades del sistema osteomuscular"),
    ("M199", "Artrosis, no especificada", "Enfermedades del sistema osteomuscular"),
    ("M142", "Artropatía diabética", "Enfermedades del sistema osteomuscular"),
    ("M810", "Osteoporosis posmenopáusica", "Enfermedades del sistema osteomuscular"),
    ("M624", "Contractura muscular", "Enfermedades del sistema osteomuscular"),

    # Enfermedades de la piel y tejido subcutáneo
    ("L89X", "Úlcera de decúbito", "Enfermedades de la piel y del tejido subcutáneo"),
    ("L984", "Úlcera crónica de la piel, no clasificada en otra parte", "Enfermedades de la piel y del tejido subcutáneo"),
    ("L030", "Celulitis de los dedos de la mano y del pie", "Enfermedades de la piel y del tejido subcutáneo"),
    ("L974", "Úlcera de miembro inferior, no clasificada en otra parte", "Enfermedades de la piel y del tejido subcutáneo"),

    # Enfermedades del sistema genitourinario
    ("N390", "Infección de vías urinarias, sitio no especificado", "Enfermedades del sistema genitourinario"),
    ("N189", "Enfermedad renal crónica, no especificada", "Enfermedades del sistema genitourinario"),
    ("N400", "Hiperplasia de la próstata sin síntomas del tracto urinario inferior", "Enfermedades del sistema genitourinario"),

    # Neoplasias
    ("C900", "Mieloma múltiple", "Neoplasias"),
    ("C61X", "Tumor maligno de la próstata", "Neoplasias"),
    ("Z511", "Sesión de quimioterapia por tumor", "Factores que influyen en el estado de salud"),
    ("Z515", "Cuidados paliativos", "Factores que influyen en el estado de salud"),

    # Enfermedades del oído
    ("H911", "Presbiacusia", "Enfermedades del oído y de la apófisis mastoides"),

    # Trastornos digestivos
    ("K590", "Estreñimiento", "Enfermedades del sistema digestivo"),
    ("K921", "Melena", "Enfermedades del sistema digestivo"),
    ("K922", "Hemorragia gastrointestinal, no especificada", "Enfermedades del sistema digestivo"),

    # Traumatismos y otras causas externas
    ("S720", "Fractura del cuello del fémur", "Traumatismos, envenenamientos y otras consecuencias de causas externas"),
    ("T814", "Infección consecutiva a un procedimiento, no clasificada en otra parte", "Traumatismos, envenenamientos y otras consecuencias de causas externas"),
    ("W19X", "Caída no especificada", "Causas externas de morbilidad y de mortalidad"),

    # Códigos Z (factores que influyen en la atención)
    ("Z930", "Traqueostomía", "Factores que influyen en el estado de salud"),
    ("Z931", "Gastrostomía", "Factores que influyen en el estado de salud"),
    ("Z950", "Presencia de marcapasos cardíaco", "Factores que influyen en el estado de salud"),
    ("Z992", "Dependencia de diálisis renal", "Factores que influyen en el estado de salud"),
    ("Z991", "Dependencia de respirador [ventilador]", "Factores que influyen en el estado de salud"),
    ("Z741", "Necesidad de asistencia con el cuidado personal", "Factores que influyen en el estado de salud"),
    ("Z540", "Convalecencia consecutiva a cirugía", "Factores que influyen en el estado de salud"),
    ("Z541", "Convalecencia consecutiva a radioterapia", "Factores que influyen en el estado de salud"),
    ("Q390", "Atresia del esófago sin mención de fístula", "Malformaciones congénitas"),
    ("R13X", "Disfagia", "Síntomas, signos y hallazgos anormales"),
    ("F067", "Trastorno cognoscitivo leve", "Trastornos mentales y del comportamiento"),
    ("E232", "Diabetes insípida", "Enfermedades endocrinas, nutricionales y metabólicas"),
    ("C960", "Histiocitosis de células de Langerhans multifocal y multisistémica", "Neoplasias"),

    # Síntomas y signos generales
    ("R509", "Fiebre, no especificada", "Síntomas, signos y hallazgos anormales"),
    ("R42X", "Mareo y desvanecimiento", "Síntomas, signos y hallazgos anormales"),
    ("R268", "Otras anormalidades de la marcha y de la movilidad", "Síntomas, signos y hallazgos anormales"),
    ("R296", "Tendencia a las caídas, no clasificada en otra parte", "Síntomas, signos y hallazgos anormales"),
    ("R531", "Debilidad", "Síntomas, signos y hallazgos anormales"),
]
