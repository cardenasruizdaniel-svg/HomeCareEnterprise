"""
=========================================================
HomeCare Enterprise
Database Schema
Versión: 10.0.0
Sprint 3.4B.1
=========================================================
"""
# =====================================================
# VERSIÓN DEL ESQUEMA
# =====================================================

SCHEMA_VERSION = "10.0.0"

SCHEMA = [

# =====================================================
# USUARIOS
# =====================================================

"""

CREATE TABLE IF NOT EXISTS usuarios(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    usuario TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL,

    nombre TEXT NOT NULL,

    rol TEXT NOT NULL,

    activo INTEGER DEFAULT 1,

    fecha_creacion TEXT

);

""",

# =====================================================
# PACIENTES
# =====================================================

"""

CREATE TABLE IF NOT EXISTS pacientes(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    tipo_documento TEXT,

    documento TEXT UNIQUE,

    primer_nombre TEXT,

    segundo_nombre TEXT,

    primer_apellido TEXT,

    segundo_apellido TEXT,

    fecha_nacimiento TEXT,

    sexo TEXT,

    eps TEXT,

    regimen TEXT,

    telefono TEXT,

    celular TEXT,

    correo TEXT,

    direccion TEXT,

    barrio TEXT,

    municipio TEXT,

    departamento TEXT,

    estado TEXT DEFAULT 'Activo',

    fecha_registro TEXT

);

""",

# =====================================================
# PROFESIONALES
# =====================================================

"""

CREATE TABLE IF NOT EXISTS profesionales(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    documento TEXT UNIQUE,

    nombre TEXT,

    profesion TEXT,

    telefono TEXT,

    correo TEXT,

    estado TEXT,

    fecha_registro TEXT

);

""",

# =====================================================
# PROGRAMACIONES
# =====================================================

"""

CREATE TABLE IF NOT EXISTS programaciones(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER,

    profesional_id INTEGER,

    servicio TEXT,

    fecha TEXT,

    hora TEXT,

    estado TEXT,

    observaciones TEXT,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);

""",

# =====================================================
# AUDITORIA
# =====================================================

"""

CREATE TABLE IF NOT EXISTS auditoria(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fecha TEXT,

    usuario_id INTEGER,

    usuario TEXT,

    rol TEXT,

    modulo TEXT,

    accion TEXT,

    descripcion TEXT,

    ip TEXT,

    navegador TEXT

);

"""

,

"""
CREATE TABLE IF NOT EXISTS plantillas(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    uuid TEXT UNIQUE,

    nombre TEXT NOT NULL,

    descripcion TEXT,

    categoria TEXT,

    especialidad TEXT,

    tipo_profesional TEXT,

    servicio TEXT,

    version TEXT DEFAULT '1.0',

    estado TEXT DEFAULT 'BORRADOR',

    visibilidad TEXT DEFAULT 'GLOBAL',

    creada_por INTEGER,

    aprobada_por INTEGER,

    requiere_aprobacion INTEGER DEFAULT 1,

    ia_habilitada INTEGER DEFAULT 1,

    dictado_voz INTEGER DEFAULT 1,

    firma_paciente INTEGER DEFAULT 1,

    firma_profesional INTEGER DEFAULT 1,

    geolocalizacion INTEGER DEFAULT 1,

    fotografia INTEGER DEFAULT 0,

    activa INTEGER DEFAULT 1,

    fecha_creacion TEXT,

    fecha_actualizacion TEXT

);
"""

,

"""
CREATE TABLE IF NOT EXISTS plantilla_componentes(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    codigo TEXT UNIQUE,

    nombre TEXT NOT NULL,

    icono TEXT,

    categoria TEXT,

    descripcion TEXT,

    tipo_dato TEXT,

    componente_html TEXT,

    permite_ia INTEGER DEFAULT 1,

    permite_dictado INTEGER DEFAULT 1,

    permite_firma INTEGER DEFAULT 0,

    permite_fotografia INTEGER DEFAULT 0,

    permite_adjuntos INTEGER DEFAULT 0,

    permite_geolocalizacion INTEGER DEFAULT 0,

    activo INTEGER DEFAULT 1

);
"""

,

"""
CREATE TABLE IF NOT EXISTS plantilla_versiones(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    plantilla_id INTEGER NOT NULL,

    version TEXT NOT NULL,

    descripcion TEXT,

    json_estructura TEXT NOT NULL,

    publicada INTEGER DEFAULT 0,

    vigente INTEGER DEFAULT 1,

    creada_por INTEGER,

    fecha_creacion TEXT,

    FOREIGN KEY(plantilla_id)

        REFERENCES plantillas(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_pacientes_documento
ON pacientes(documento);
""",

"""
CREATE INDEX IF NOT EXISTS idx_profesionales_documento
ON profesionales(documento);
""",

"""
CREATE INDEX IF NOT EXISTS idx_programaciones_fecha
ON programaciones(fecha);
""",

"""
CREATE INDEX IF NOT EXISTS idx_programaciones_profesional
ON programaciones(profesional_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_programaciones_paciente
ON programaciones(paciente_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_plantillas_categoria
ON plantillas(categoria);
""",

"""
CREATE INDEX IF NOT EXISTS idx_plantillas_especialidad
ON plantillas(especialidad);
""",

"""
CREATE INDEX IF NOT EXISTS idx_componentes_categoria
ON plantilla_componentes(categoria);
""",

"""
CREATE INDEX IF NOT EXISTS idx_versiones_plantilla
ON plantilla_versiones(plantilla_id);
""",

# =====================================================
# HISTORIAS CLÍNICAS
# (faltaba por completo: los repositorios la consultaban
# pero la tabla nunca se creaba)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS historias_clinicas(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    profesional_id INTEGER,

    fecha_apertura TEXT DEFAULT CURRENT_TIMESTAMP,

    estado TEXT DEFAULT 'ABIERTA',

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)

);
""",

# =====================================================
# CATÁLOGO CIE-10
# =====================================================

"""
CREATE TABLE IF NOT EXISTS cie10(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    codigo TEXT UNIQUE,

    descripcion TEXT,

    descripcion_normalizada TEXT,

    categoria TEXT,

    capitulo TEXT,

    activo INTEGER DEFAULT 1

);
""",

# =====================================================
# DIAGNÓSTICOS (por historia / paciente, codificados en CIE-10
# para cumplir el conjunto de datos clínicos relevantes de la
# Resolución 866 de 2021)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS diagnosticos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    codigo_cie10 TEXT,

    diagnostico TEXT,

    tipo TEXT DEFAULT 'IMPRESION DIAGNOSTICA',

    estado TEXT DEFAULT 'Activo',

    fecha_diagnostico TEXT,

    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,

    profesional TEXT,

    especialidad TEXT,

    observaciones TEXT,

    codigo_cups TEXT,

    descripcion_cups TEXT,

    usuario_registro INTEGER,

    fecha_actualizacion TEXT,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)

);
""",

# =====================================================
# ALERGIAS
# =====================================================

"""
CREATE TABLE IF NOT EXISTS alergias(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    tipo TEXT,

    alergeno TEXT,

    codigo_alergeno TEXT,

    reaccion TEXT,

    severidad TEXT DEFAULT 'LEVE',

    estado TEXT DEFAULT 'Activa',

    observaciones TEXT,

    fecha_diagnostico TEXT,

    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,

    usuario_creacion INTEGER,

    usuario_actualizacion INTEGER,

    fecha_actualizacion TEXT,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)

);
""",

# =====================================================
# ANTECEDENTES
# =====================================================

"""
CREATE TABLE IF NOT EXISTS antecedentes(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    tipo TEXT,

    descripcion TEXT,

    observaciones TEXT,

    activo INTEGER DEFAULT 1,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    usuario_actualizacion INTEGER,

    fecha_actualizacion TEXT,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)

);
""",

# =====================================================
# SIGNOS VITALES
# =====================================================

"""
CREATE TABLE IF NOT EXISTS signos_vitales(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    profesional TEXT,

    fecha TEXT,

    hora TEXT,

    temperatura REAL,

    presion_sistolica INTEGER,

    presion_diastolica INTEGER,

    frecuencia_cardiaca INTEGER,

    frecuencia_respiratoria INTEGER,

    saturacion_oxigeno INTEGER,

    glucemia REAL,

    peso REAL,

    talla REAL,

    imc REAL,

    dolor INTEGER,

    observaciones TEXT,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    fecha_actualizacion TEXT,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)

);
""",

# =====================================================
# MEDICAMENTOS FORMULADOS (por historia / paciente,
# codificados en CUM para interoperabilidad)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS medicamentos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER,

    diagnostico_id INTEGER,

    nombre TEXT,

    principio_activo TEXT,

    concentracion TEXT,

    presentacion TEXT,

    dosis TEXT,

    frecuencia TEXT,

    via TEXT,

    horario TEXT,

    duracion TEXT,

    cantidad TEXT,

    indicaciones TEXT,

    observaciones TEXT,

    fecha_inicio TEXT,

    fecha_fin TEXT,

    estado TEXT DEFAULT 'ACTIVO',

    profesional TEXT,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    fecha_actualizacion TEXT,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)

);
""",

# =====================================================
# ADMINISTRACIÓN DE MEDICAMENTOS
# =====================================================

"""
CREATE TABLE IF NOT EXISTS administracion_medicamentos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    medicamento_id INTEGER,

    paciente_id INTEGER NOT NULL,

    profesional TEXT,

    fecha TEXT,

    hora TEXT,

    dosis TEXT,

    via TEXT,

    observaciones TEXT,

    estado TEXT DEFAULT 'Administrado',

    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(medicamento_id)
        REFERENCES medicamentos(id)
        ON DELETE CASCADE,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)
        ON DELETE CASCADE

);
""",

# =====================================================
# ÓRDENES MÉDICAS
# (necesarias para el envío automático de PDF por
# WhatsApp/correo cuando el médico las genera)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS ordenes_medicas(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    historia_id INTEGER,

    paciente_id INTEGER NOT NULL,

    profesional_id INTEGER,

    tipo TEXT,

    descripcion TEXT,

    codigo_cups TEXT,

    estado TEXT DEFAULT 'PENDIENTE',

    fecha_orden TEXT DEFAULT CURRENT_TIMESTAMP,

    enviado_whatsapp INTEGER DEFAULT 0,

    enviado_correo INTEGER DEFAULT 0,

    token_pdf TEXT,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(historia_id)
        REFERENCES historias_clinicas(id)

);
""",

# =====================================================
# ACUDIENTES / CUIDADORES DE CONTACTO
# =====================================================

"""
CREATE TABLE IF NOT EXISTS acudientes(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    nombre TEXT,

    tipo_documento TEXT,

    documento TEXT,

    parentesco TEXT,

    telefono TEXT,

    telefono_principal TEXT,

    telefono_secundario TEXT,

    celular TEXT,

    correo TEXT,

    direccion TEXT,

    barrio TEXT,

    municipio TEXT,

    departamento TEXT,

    ciudad TEXT,

    ocupacion TEXT,

    observaciones TEXT,

    es_principal INTEGER DEFAULT 0,

    autoriza_decisiones INTEGER DEFAULT 0,

    recibe_informacion INTEGER DEFAULT 1,

    estado TEXT DEFAULT 'Activo',

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    fecha_actualizacion TEXT,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)

);
""",

# =====================================================
# ÍNDICES DE LAS TABLAS CLÍNICAS NUEVAS
# =====================================================

"""
CREATE INDEX IF NOT EXISTS idx_historias_paciente
ON historias_clinicas(paciente_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_diagnosticos_paciente
ON diagnosticos(paciente_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_alergias_paciente
ON alergias(paciente_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_antecedentes_paciente
ON antecedentes(paciente_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_signos_paciente
ON signos_vitales(paciente_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_medicamentos_paciente
ON medicamentos(paciente_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_ordenes_paciente
ON ordenes_medicas(paciente_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_acudientes_paciente
ON acudientes(paciente_id);
""",

# =====================================================
# CATÁLOGOS OFICIALES (DIVIPOLA, CUPS, CUM)
# Necesarios para que el RIPS no dependa de digitación
# manual de códigos.
# =====================================================

"""
CREATE TABLE IF NOT EXISTS divipola(

    codigo_departamento TEXT NOT NULL,

    nombre_departamento TEXT NOT NULL,

    codigo_municipio TEXT PRIMARY KEY,

    nombre_municipio TEXT NOT NULL,

    nombre_normalizado TEXT,

    codigo_postal TEXT

);
"""

,

"""
CREATE TABLE IF NOT EXISTS cups(

    codigo TEXT PRIMARY KEY,

    descripcion TEXT NOT NULL,

    descripcion_normalizada TEXT,

    capitulo TEXT,

    activo INTEGER DEFAULT 1

);
""",

"""
CREATE TABLE IF NOT EXISTS cum(

    codigo TEXT PRIMARY KEY,

    nombre TEXT NOT NULL,

    nombre_normalizado TEXT,

    principio_activo TEXT,

    concentracion TEXT,

    forma_farmaceutica TEXT,

    activo INTEGER DEFAULT 1

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_divipola_departamento
ON divipola(codigo_departamento);
""",

"""
CREATE INDEX IF NOT EXISTS idx_cups_descripcion
ON cups(descripcion);
""",

"""
CREATE INDEX IF NOT EXISTS idx_cum_nombre
ON cum(nombre);
""",

# =====================================================
# NÓMINA
# =====================================================

"""
CREATE TABLE IF NOT EXISTS nomina(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    periodo_inicio TEXT NOT NULL,

    periodo_fin TEXT NOT NULL,

    fecha_generacion TEXT DEFAULT CURRENT_TIMESTAMP,

    usuario_generacion INTEGER,

    estado TEXT DEFAULT 'Generada',

    total_pagar REAL DEFAULT 0,

    observaciones TEXT

);
""",

"""
CREATE TABLE IF NOT EXISTS nomina_detalle(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nomina_id INTEGER NOT NULL,

    profesional_id INTEGER NOT NULL,

    tipo_contrato TEXT,

    numero_visitas INTEGER DEFAULT 0,

    horas_trabajadas REAL DEFAULT 0,

    valor_hora REAL DEFAULT 0,

    salario_fijo REAL DEFAULT 0,

    auxilio_transporte REAL DEFAULT 0,

    valor_a_pagar REAL DEFAULT 0,

    estado_pago TEXT DEFAULT 'Pendiente',

    fecha_pago TEXT,

    FOREIGN KEY(nomina_id)
        REFERENCES nomina(id)
        ON DELETE CASCADE,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_nomina_detalle_nomina
ON nomina_detalle(nomina_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_nomina_detalle_profesional
ON nomina_detalle(profesional_id);
""",

# =====================================================
# CARGOS (puestos de trabajo)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS cargos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL,

    descripcion TEXT,

    tipo_contrato_sugerido TEXT DEFAULT 'POR_HORAS',

    salario_base REAL DEFAULT 0,

    valor_hora_base REAL DEFAULT 0,

    periodicidad_pago TEXT DEFAULT 'MENSUAL',

    nivel_riesgo_arl TEXT DEFAULT 'I',

    documentos_requeridos TEXT,

    activo INTEGER DEFAULT 1,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP

);
""",

# =====================================================
# CONTRATOS (vincula un profesional con un cargo)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS contratos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    profesional_id INTEGER NOT NULL,

    cargo_id INTEGER NOT NULL,

    tipo_contrato TEXT NOT NULL,

    modalidad_pago TEXT DEFAULT 'POR_HORAS',

    salario_mensual REAL DEFAULT 0,

    valor_hora REAL DEFAULT 0,

    periodicidad_pago TEXT DEFAULT 'MENSUAL',

    fecha_inicio TEXT NOT NULL,

    fecha_fin TEXT,

    nivel_riesgo_arl TEXT DEFAULT 'I',

    eps TEXT,

    fondo_pension TEXT,

    fondo_cesantias TEXT,

    caja_compensacion TEXT,

    estado TEXT DEFAULT 'Activo',

    observaciones TEXT,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id),

    FOREIGN KEY(cargo_id)
        REFERENCES cargos(id)

);
""",

# =====================================================
# DOCUMENTOS DEL PROFESIONAL (títulos, cursos, RETHUS...)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS documentos_profesional(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    profesional_id INTEGER NOT NULL,

    tipo_documento TEXT NOT NULL,

    nombre TEXT,

    numero TEXT,

    entidad_emisora TEXT,

    fecha_expedicion TEXT,

    fecha_vencimiento TEXT,

    ruta_archivo TEXT,

    archivo_base64 TEXT,

    nombre_archivo TEXT,

    estado TEXT DEFAULT 'Vigente',

    observaciones TEXT,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
""",

# =====================================================
# TURNOS PROGRAMADOS (calendario de turnos)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS turnos_programados(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    profesional_id INTEGER NOT NULL,

    paciente_id INTEGER,

    catalogo_turno_id INTEGER,

    programacion_id INTEGER,

    fecha TEXT NOT NULL,

    turno TEXT NOT NULL,

    hora_inicio TEXT NOT NULL,

    hora_fin TEXT NOT NULL,

    zona TEXT,

    estado TEXT DEFAULT 'Programado',

    observaciones TEXT,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id),

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)

);
""",

"""
CREATE TABLE IF NOT EXISTS catalogo_turnos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL,

    tramo1_inicio TEXT NOT NULL,

    tramo1_fin TEXT NOT NULL,

    tramo2_inicio TEXT,

    tramo2_fin TEXT,

    tipo_cuidado_aplica TEXT DEFAULT 'Ambos',

    activo INTEGER DEFAULT 1

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_contratos_profesional
ON contratos(profesional_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_documentos_profesional
ON documentos_profesional(profesional_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_turnos_profesional_fecha
ON turnos_programados(profesional_id, fecha);
""",

# =====================================================
# EVOLUCIONES CLÍNICAS (notas de seguimiento por visita)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS evoluciones(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    programacion_id INTEGER,

    profesional_id INTEGER,

    fecha TEXT DEFAULT CURRENT_TIMESTAMP,

    tipo_profesional TEXT,

    nota TEXT NOT NULL,

    latitud REAL,

    longitud REAL,

    origen TEXT DEFAULT 'WEB',

    usuario_creacion INTEGER,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(programacion_id)
        REFERENCES programaciones(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_evoluciones_paciente
ON evoluciones(paciente_id);
""",

# =====================================================
# COPAGOS DE PACIENTES
# =====================================================

"""
CREATE TABLE IF NOT EXISTS copagos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    programacion_id INTEGER,

    orden_id INTEGER,

    concepto TEXT,

    valor_copago REAL NOT NULL DEFAULT 0,

    pagado INTEGER DEFAULT 0,

    fecha_pago TEXT,

    metodo_pago TEXT,

    factura_id INTEGER,

    observaciones TEXT,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(programacion_id)
        REFERENCES programaciones(id),

    FOREIGN KEY(orden_id)
        REFERENCES ordenes_medicas(id)

);
""",

# =====================================================
# FACTURACIÓN ELECTRÓNICA (copagos de pacientes)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS facturas_electronicas(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    prefijo TEXT DEFAULT 'FEV',

    numero INTEGER,

    copago_id INTEGER,

    servicio_paciente_id INTEGER,

    concepto TEXT,

    paciente_id INTEGER NOT NULL,

    fecha_emision TEXT DEFAULT CURRENT_TIMESTAMP,

    valor_subtotal REAL DEFAULT 0,

    valor_iva REAL DEFAULT 0,

    valor_total REAL DEFAULT 0,

    forma_pago TEXT DEFAULT 'Contado',

    medio_pago TEXT,

    cufe TEXT,

    estado TEXT DEFAULT 'Generada',

    xml_path TEXT,

    pdf_path TEXT,

    motivo_rechazo TEXT,

    usuario_creacion INTEGER,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(copago_id)
        REFERENCES copagos(id)

);
""",

# =====================================================
# NÓMINA ELECTRÓNICA (documento soporte DIAN)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS nomina_electronica(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nomina_detalle_id INTEGER NOT NULL,

    numero_consecutivo INTEGER,

    tipo_documento TEXT DEFAULT 'DSNE',

    tipo_nota TEXT,

    cune TEXT,

    estado TEXT DEFAULT 'Generado',

    xml_path TEXT,

    pdf_path TEXT,

    fecha_generacion TEXT DEFAULT CURRENT_TIMESTAMP,

    motivo_rechazo TEXT,

    FOREIGN KEY(nomina_detalle_id)
        REFERENCES nomina_detalle(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_copagos_paciente
ON copagos(paciente_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_facturas_paciente
ON facturas_electronicas(paciente_id);
""",

"""
CREATE INDEX IF NOT EXISTS idx_nomina_electronica_detalle
ON nomina_electronica(nomina_detalle_id);
""",

# =====================================================
# HISTORIAL DE DOCUMENTOS DEL PACIENTE
# (para el cambio de Registro Civil -> Tarjeta de Identidad
# -> Cedula, u otros cambios de documento, exigiendo
# trazabilidad transparente ante Supersalud: los registros
# de ANTES de la fecha de cambio deben quedar con el
# documento anterior, y los de DESPUES con el nuevo)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS historial_documentos_paciente(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    tipo_documento TEXT NOT NULL,

    numero_documento TEXT NOT NULL,

    fecha_inicio_vigencia TEXT NOT NULL,

    fecha_fin_vigencia TEXT,

    es_principal INTEGER DEFAULT 0,

    motivo_cambio TEXT,

    usuario_creacion INTEGER,

    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_historial_documentos_paciente
ON historial_documentos_paciente(paciente_id);
""",

# =====================================================
# SERVICIOS ASIGNADOS AL PACIENTE
# (Medicina General, Terapia [con su tipo], Curaciones,
# Aplicador de medicamentos/sueros, etc. Cada uno con su
# rango de fechas para generar la planilla de visitas)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS servicios_paciente(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    tipo_servicio TEXT NOT NULL,

    subtipo TEXT,

    profesional_id INTEGER,

    frecuencia TEXT DEFAULT 'Diaria',

    fecha_inicio TEXT NOT NULL,

    fecha_fin TEXT NOT NULL,

    hora_inicio TEXT DEFAULT '08:00',

    hora_fin TEXT DEFAULT '09:00',

    indicaciones TEXT,

    actividad_id INTEGER,

    numero_sesiones INTEGER,

    paciente_programa_id INTEGER,

    renovacion_automatica INTEGER DEFAULT 0,

    estado TEXT DEFAULT 'Activo',

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id),

    FOREIGN KEY(actividad_id)
        REFERENCES catalogo_actividades(id),

    FOREIGN KEY(paciente_programa_id)
        REFERENCES paciente_programas(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_servicios_paciente
ON servicios_paciente(paciente_id);
""",

# =====================================================
# PLANILLA DE VISITAS (hoja de control con firma)
# Cada fila representa UN dia de visita generado a partir
# de un servicio asignado, con su firma digital de
# confirmacion (del paciente o del acompañante), foto,
# hora, fecha y ubicacion del momento de la firma.
# =====================================================

"""
CREATE TABLE IF NOT EXISTS planilla_visitas(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    servicio_paciente_id INTEGER NOT NULL,

    programacion_id INTEGER,

    paciente_id INTEGER NOT NULL,

    fecha TEXT NOT NULL,

    hora_inicio TEXT,

    hora_fin TEXT,

    nombre_acompanante TEXT,

    firmante TEXT,

    firma_base64 TEXT,

    foto_base64 TEXT,

    firma_fecha_hora TEXT,

    firma_latitud REAL,

    firma_longitud REAL,

    profesional_id INTEGER,

    motivo_cancelacion TEXT,

    estado TEXT DEFAULT 'Pendiente',

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(servicio_paciente_id)
        REFERENCES servicios_paciente(id),

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(programacion_id)
        REFERENCES programaciones(id),

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_planilla_visitas_servicio
ON planilla_visitas(servicio_paciente_id);
""",

# =====================================================
# PLANTILLAS DE VISITA (texto precargado por tipo de
# servicio, para agilizar la digitacion de evoluciones).
# Pueden ser creadas por el area administrativa (de uso
# general) o por un profesional especifico (de uso propio).
# =====================================================

"""
CREATE TABLE IF NOT EXISTS plantillas_visita(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL,

    tipo_servicio TEXT NOT NULL,

    subtipo TEXT,

    rol_destinatario TEXT DEFAULT 'Todos',

    contenido TEXT NOT NULL,

    profesional_id INTEGER,

    creado_por_administracion INTEGER DEFAULT 1,

    activo INTEGER DEFAULT 1,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_plantillas_visita_tipo
ON plantillas_visita(tipo_servicio);
""",

# =====================================================
# PROGRAMAS DE ATENCIÓN (catálogo flexible)
# Ej: Paciente Crónico Complejidad Alta (con
# traqueostomía / paciente neurológico agudo),
# Paciente Crónico Baja Complejidad (con terapias / sin
# terapias). No es una lista cerrada: se pueden crear
# programas nuevos cuando se necesiten.
# =====================================================

"""
CREATE TABLE IF NOT EXISTS programas_atencion(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL,

    tipo TEXT NOT NULL,

    subtipo TEXT,

    descripcion TEXT,

    activo INTEGER DEFAULT 1,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP

);
""",

# =====================================================
# ASIGNACIÓN DE PROGRAMA AL PACIENTE (con historial)
# La primera asignacion la hace el medico en la visita
# inicial de valoracion; si despues cambia de programa,
# se cierra la anterior y se abre una nueva, quedando
# todo el historial disponible en la historia clinica.
# =====================================================

"""
CREATE TABLE IF NOT EXISTS paciente_programas(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    programa_id INTEGER NOT NULL,

    profesional_id INTEGER,

    fecha_asignacion TEXT NOT NULL,

    fecha_fin TEXT,

    motivo TEXT,

    es_actual INTEGER DEFAULT 1,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(programa_id)
        REFERENCES programas_atencion(id),

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_paciente_programas
ON paciente_programas(paciente_id);
""",

# =====================================================
# CATÁLOGO DE ACTIVIDADES (las que se pueden asignar
# dentro de un programa de atención: valoración médica,
# terapias, enfermería, apoyo nutricional, etc.)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS catalogo_actividades(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL,

    categoria TEXT,

    activo INTEGER DEFAULT 1

);
""",

# =====================================================
# FOTOS DE PROCEDIMIENTOS (registro fotografico de lo
# que se le hace al paciente, subido directamente desde
# su ficha en el sistema web)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS fotos_procedimientos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    descripcion TEXT,

    foto_base64 TEXT NOT NULL,

    profesional_id INTEGER,

    fecha TEXT DEFAULT CURRENT_TIMESTAMP,

    usuario_creacion INTEGER,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_fotos_procedimientos_paciente
ON fotos_procedimientos(paciente_id);
""",

# =====================================================
# CONSENTIMIENTOS INFORMADOS
# (ingreso al programa de atencion domiciliaria, u otros
# que se necesiten mas adelante -- queda con firma y es
# imprimible como un documento formal del paciente)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS consentimientos_informados(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    tipo TEXT NOT NULL,

    contenido_texto TEXT NOT NULL,

    firmante TEXT,

    nombre_firmante TEXT,

    documento_firmante TEXT,

    parentesco_firmante TEXT,

    firma_base64 TEXT,

    fecha_diligenciamiento TEXT DEFAULT CURRENT_TIMESTAMP,

    usuario_creacion INTEGER,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_consentimientos_paciente
ON consentimientos_informados(paciente_id);
""",

# =====================================================
# CATÁLOGO DE EPS (se arrastra automático en el
# formulario de paciente, en vez de escribirla a mano)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS catalogo_eps(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL UNIQUE,

    tipo TEXT DEFAULT 'Contributivo/Subsidiado',

    activo INTEGER DEFAULT 1

);
""",

# =====================================================
# CATÁLOGO DE BANCOS DE COLOMBIA (para los datos
# bancarios de los profesionales, en vez de texto libre)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS catalogo_bancos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL UNIQUE,

    activo INTEGER DEFAULT 1

);
""",

# =====================================================
# SOLICITUDES DE FIRMA REMOTA (código QR)
# Permite que el paciente o el profesional firme desde SU
# PROPIO celular, escaneando un QR que abre una pagina
# simple de firma, sin necesitar cuenta en el sistema.
# =====================================================

"""
CREATE TABLE IF NOT EXISTS solicitudes_firma(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    token TEXT NOT NULL UNIQUE,

    tipo TEXT NOT NULL,

    referencia_id INTEGER NOT NULL,

    estado TEXT DEFAULT 'Pendiente',

    firma_base64 TEXT,

    nombre_firmante TEXT,

    documento_firmante TEXT,

    parentesco_firmante TEXT,

    firmante TEXT,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    fecha_completado TEXT

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_solicitudes_firma_token
ON solicitudes_firma(token);
""",

# =====================================================
# MÓDULO DE INVENTARIO DE INSUMOS MÉDICOS
# Proveedores, catálogo de insumos, y movimientos de
# entrada (compras) y salida (entrega al paciente).
# =====================================================

"""
CREATE TABLE IF NOT EXISTS proveedores(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL,

    nit TEXT,

    contacto TEXT,

    telefono TEXT,

    correo TEXT,

    direccion TEXT,

    estado TEXT DEFAULT 'Activo',

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP

);
""",

"""
CREATE TABLE IF NOT EXISTS insumos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL,

    categoria TEXT,

    unidad_medida TEXT DEFAULT 'Unidad',

    stock_minimo INTEGER DEFAULT 0,

    activo INTEGER DEFAULT 1,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP

);
""",

"""
CREATE TABLE IF NOT EXISTS inventario_movimientos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    insumo_id INTEGER NOT NULL,

    tipo TEXT NOT NULL,

    cantidad INTEGER NOT NULL,

    fecha TEXT DEFAULT CURRENT_TIMESTAMP,

    proveedor_id INTEGER,

    numero_factura TEXT,

    costo_unitario REAL,

    paciente_id INTEGER,

    profesional_id INTEGER,

    motivo TEXT,

    usuario_creacion INTEGER,

    FOREIGN KEY(insumo_id)
        REFERENCES insumos(id),

    FOREIGN KEY(proveedor_id)
        REFERENCES proveedores(id),

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_inventario_movimientos_insumo
ON inventario_movimientos(insumo_id);
""",

# =====================================================
# CONFIGURACIÓN DE LA EMPRESA
# (una sola fila -- se usa para el membrete y los datos
# legales que aparecen en todos los reportes impresos:
# consentimientos, informes de historia clínica, etc.)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS configuracion_empresa(

    id INTEGER PRIMARY KEY CHECK (id = 1),

    razon_social TEXT DEFAULT 'HomeCare Enterprise',

    nit TEXT,

    resolucion_habilitacion TEXT,

    direccion TEXT,

    telefono TEXT,

    correo TEXT,

    ciudad TEXT,

    departamento TEXT,

    representante_legal TEXT,

    logo_base64 TEXT,

    fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP

);
""",

# =====================================================
# RESULTADOS DE LABORATORIO CLÍNICO
# =====================================================

"""
CREATE TABLE IF NOT EXISTS laboratorios_resultados(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    nombre_examen TEXT NOT NULL,

    laboratorio_realizo TEXT,

    fecha_orden TEXT,

    fecha_resultado TEXT,

    resultado_texto TEXT,

    foto_resultado_base64 TEXT,

    profesional_id INTEGER,

    origen TEXT DEFAULT 'WEB',

    usuario_registro INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(paciente_id)
        REFERENCES pacientes(id),

    FOREIGN KEY(profesional_id)
        REFERENCES profesionales(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_laboratorios_resultados_paciente
ON laboratorios_resultados(paciente_id);
""",

# =====================================================
# ÍTEMS MEDIBLES DE CADA RESULTADO DE LABORATORIO
# (ej: en un hemograma, cada fila es un parámetro:
# Glóbulos rojos, Hemoglobina, etc., con su valor
# obtenido y el rango normal, para poder marcar
# automáticamente si quedó alto o bajo)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS laboratorio_items(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    resultado_id INTEGER NOT NULL,

    nombre_parametro TEXT NOT NULL,

    valor_obtenido TEXT,

    valor_numerico REAL,

    unidad TEXT,

    rango_min REAL,

    rango_max REAL,

    interpretacion TEXT,

    FOREIGN KEY(resultado_id)
        REFERENCES laboratorios_resultados(id)

);
""",

"""
CREATE INDEX IF NOT EXISTS idx_laboratorio_items_resultado
ON laboratorio_items(resultado_id);
""",

# =====================================================
# MÓDULO DE CALIDAD
# PQR/Solicitudes, planificación de trabajo con
# responsables, y evaluación de la atención al paciente.
# =====================================================

"""
CREATE TABLE IF NOT EXISTS calidad_pqr(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    tipo TEXT NOT NULL DEFAULT 'PQR',

    paciente_id INTEGER,

    asunto TEXT NOT NULL,

    descripcion TEXT,

    prioridad TEXT DEFAULT 'Media',

    estado TEXT DEFAULT 'Abierto',

    responsable_id INTEGER,

    respuesta TEXT,

    fecha_cierre TEXT,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY(responsable_id) REFERENCES profesionales(id)

);
""",

"""
CREATE TABLE IF NOT EXISTS calidad_planificacion(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    titulo TEXT NOT NULL,

    descripcion TEXT,

    responsable_id INTEGER,

    fecha_inicio TEXT,

    fecha_limite TEXT,

    prioridad TEXT DEFAULT 'Media',

    estado TEXT DEFAULT 'Pendiente',

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(responsable_id) REFERENCES profesionales(id)

);
""",

"""
CREATE TABLE IF NOT EXISTS calidad_evaluaciones(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    profesional_id INTEGER,

    calificacion INTEGER NOT NULL,

    aspectos_evaluados TEXT,

    comentario TEXT,

    usuario_registro INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY(profesional_id) REFERENCES profesionales(id)

);
""",

# =====================================================
# EXAMEN FÍSICO POR SISTEMAS
# (cabeza, boca, cuello, torax, abdomen, extremidades,
# vascular, neurologico, columna -- como en el formato
# de historia clinica de medicina general de la IPS)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS examen_fisico(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    programacion_id INTEGER,

    profesional_id INTEGER,

    tipo_profesional TEXT,

    fecha TEXT DEFAULT CURRENT_TIMESTAMP,

    cabeza TEXT,

    cara TEXT,

    boca TEXT,

    cuello TEXT,

    torax TEXT,

    abdomen TEXT,

    extremidades TEXT,

    vascular TEXT,

    neurologico TEXT,

    columna TEXT,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY(profesional_id) REFERENCES profesionales(id)

);
""",

# =====================================================
# RECOMENDACIONES / PLAN MÉDICO
# (diagnostico principal + 3 relacionados, tipo de
# consulta, y marcas de incapacidad/nota aclaratoria/
# orden de medicamentos/orden de procedimientos --
# tal como en el formato de historia clinica de la IPS)
# =====================================================

"""
CREATE TABLE IF NOT EXISTS recomendaciones_medicas(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    paciente_id INTEGER NOT NULL,

    programacion_id INTEGER,

    profesional_id INTEGER,

    fecha TEXT DEFAULT CURRENT_TIMESTAMP,

    diagnostico_ppal_codigo TEXT,

    diagnostico_ppal_nombre TEXT,

    diagnostico_rel1_codigo TEXT,

    diagnostico_rel1_nombre TEXT,

    diagnostico_rel2_codigo TEXT,

    diagnostico_rel2_nombre TEXT,

    diagnostico_rel3_codigo TEXT,

    diagnostico_rel3_nombre TEXT,

    tipo_consulta TEXT,

    incapacidad INTEGER DEFAULT 0,

    nota_aclaratoria INTEGER DEFAULT 0,

    orden_medicamentos INTEGER DEFAULT 0,

    orden_procedimientos INTEGER DEFAULT 0,

    recomendaciones_texto TEXT,

    usuario_creacion INTEGER,

    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY(profesional_id) REFERENCES profesionales(id)

);
""",

]