"""
=========================================================
HomeCare Enterprise
Database Migration Manager
Versión 10.0
Sprint 3.4B.1
=========================================================
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from database.database import get_connection
from database.schema import (
    SCHEMA,
    SCHEMA_VERSION,
)
from database.indexes import INDEXES


class MigrationManager:
    """
    Administrador central de migraciones de HomeCare Enterprise.

    Responsable de:

    - Crear tablas
    - Crear índices
    - Actualizar esquemas
    - Migraciones Legacy
    - Validaciones
    - Auditoría
    """

    def __init__(self):

        self.connection: Optional[sqlite3.Connection] = None

        self.cursor: Optional[sqlite3.Cursor] = None

            # =====================================================
    # CONEXIÓN
    # =====================================================

    def conectar(self):

        if self.connection is None:

            self.connection = get_connection()

            self.cursor = self.connection.cursor()

        return self.connection

    # =====================================================
    # CERRAR
    # =====================================================

    def cerrar(self):

        if self.connection:

            self.connection.close()

            self.connection = None

            self.cursor = None

        # =====================================================
    # TABLA VERSIONES
    # =====================================================

    def crear_tabla_versiones(self):

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version(

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                version TEXT NOT NULL,

                descripcion TEXT,

                fecha TEXT DEFAULT CURRENT_TIMESTAMP

            )
            """
        )

        self.connection.commit()

        # =====================================================
    # VERSIÓN INSTALADA
    # =====================================================

    def version_actual(self):

        self.cursor.execute(
            """
            SELECT version

            FROM schema_version

            ORDER BY id DESC

            LIMIT 1
            """
        )

        fila = self.cursor.fetchone()

        if fila is None:

            return None

        return fila["version"]

        # =====================================================
    # NECESITA MIGRACIÓN
    # =====================================================

    def necesita_migracion(self):

        try:
            version = self.version_actual()
        except Exception:
            # si la tabla schema_version aun no existe, claramente
            # hace falta migrar
            return True

        return version != SCHEMA_VERSION
    
        # =====================================================
    # REGISTRAR VERSIÓN
    # =====================================================

    def registrar_version(

        self,

        version: str,

        descripcion: str,

    ):

        self.cursor.execute(
            """
            INSERT INTO schema_version(

                version,

                descripcion

            )

            VALUES(?,?)
            """,
            (
                version,
                descripcion,
            ),
        )

        self.connection.commit()

    # =====================================================
    # EJECUTAR SQL
    # =====================================================

    def ejecutar_sql(
        self,
        sql: str,
    ) -> tuple[bool, str]:

        try:

            self.cursor.execute(sql)

            self.connection.commit()

            return True, ""

        except sqlite3.Error as ex:

            self.connection.rollback()

            return False, str(ex)

    # =====================================================
    # CREAR TABLAS
    # =====================================================

    def crear_tablas(self):

        resultado = []

        for numero, sentencia in enumerate(
            SCHEMA,
            start=1,
        ):

            ok, error = self.ejecutar_sql(sentencia)

            resultado.append(
                {
                    "orden": numero,
                    "ok": ok,
                    "error": error,
                }
            )

        return resultado

    # =====================================================
    # CREAR ÍNDICES
    # =====================================================

    def crear_indices(self):

        resultado = []

        for numero, sentencia in enumerate(
            INDEXES,
            start=1,
        ):

            ok, error = self.ejecutar_sql(sentencia)

            resultado.append(
                {
                    "orden": numero,
                    "ok": ok,
                    "error": error,
                }
            )

        return resultado
    
        # =====================================================
    # TOTAL TABLAS
    # =====================================================

    def total_tablas(self):

        self.cursor.execute(
            """
            SELECT COUNT(*)

            FROM sqlite_master

            WHERE type='table'
            """
        )

        return self.cursor.fetchone()[0]

    # =====================================================
    # LISTAR TABLAS
    # =====================================================

    def listar_tablas(self):

        self.cursor.execute(
            """
            SELECT name

            FROM sqlite_master

            WHERE type='table'

            ORDER BY name
            """
        )

        return [

            fila["name"]

            for fila in self.cursor.fetchall()

        ]
    
        # =====================================================
    # EXISTE TABLA
    # =====================================================

    def existe_tabla(
        self,
        nombre: str,
    ) -> bool:

        self.cursor.execute(
            """
            SELECT name

            FROM sqlite_master

            WHERE type='table'

            AND name=?
            """,
            (nombre,),
        )

        return self.cursor.fetchone() is not None

    # =====================================================
    # EXISTE COLUMNA
    # =====================================================

    def existe_columna(
        self,
        tabla: str,
        columna: str,
    ) -> bool:

        self.cursor.execute(
            f"PRAGMA table_info({tabla})"
        )

        columnas = self.cursor.fetchall()

        return any(

            c["name"] == columna

            for c in columnas

        )
    
        # =====================================================
    # OBTENER COLUMNAS
    # =====================================================

    def obtener_columnas(
        self,
        tabla: str,
    ) -> list[str]:

        self.cursor.execute(
            f"PRAGMA table_info({tabla})"
        )

        return [
            fila["name"]
            for fila in self.cursor.fetchall()
        ]

    # =====================================================
    # AGREGAR COLUMNA
    # =====================================================

    def agregar_columna(
        self,
        tabla: str,
        definicion: str,
    ) -> bool:

        try:

            sql = (
                f"ALTER TABLE {tabla} "
                f"ADD COLUMN {definicion}"
            )

            self.cursor.execute(sql)

            self.connection.commit()

            return True

        except sqlite3.Error:

            self.connection.rollback()

            return False
        
        # =====================================================
    # SINCRONIZAR COLUMNAS
    # =====================================================

    def sincronizar_columnas(
        self,
        tabla: str,
        columnas: dict[str, str],
    ):

        existentes = self.obtener_columnas(tabla)

        resultado = []

        for nombre, definicion in columnas.items():

            if nombre in existentes:
                continue

            agregado = self.agregar_columna(
                tabla,
                definicion,
            )

            resultado.append(
                {
                    "tabla": tabla,
                    "columna": nombre,
                    "agregada": agregado,
                }
            )

        return resultado
    
        # =====================================================
    # PACIENTES - RESOLUCIÓN 866 DE 2021
    # Conjunto de elementos de datos clínicos relevantes
    # para la interoperabilidad de la historia clínica
    # (IHCE / Ley 2015 de 2020).
    # =====================================================

    def migrar_pacientes_866(self):

        if not self.existe_tabla("pacientes"):
            return []

        columnas = {

            "hora_nacimiento":
                "hora_nacimiento TEXT",

            "identidad_genero":
                "identidad_genero TEXT",

            "pertenencia_etnica":
                "pertenencia_etnica TEXT",

            "comunidad_etnica":
                "comunidad_etnica TEXT",

            "pais_nacimiento":
                "pais_nacimiento TEXT DEFAULT 'CO'",

            "pais_residencia":
                "pais_residencia TEXT DEFAULT 'CO'",

            "zona_residencia":
                "zona_residencia TEXT DEFAULT 'URBANA'",

            "indicador_alergias":
                "indicador_alergias TEXT",

            "uuid_ihce":
                "uuid_ihce TEXT",
        }

        return self.sincronizar_columnas(
            "pacientes",
            columnas,
        )

        # =====================================================
    # DATOS CLÍNICOS - CODIFICACIÓN PARA INTEROPERABILIDAD
    # (permite construir el RDA/FHIR sin perder los datos
    # que ya existen en las tablas actuales)
    # =====================================================

    def migrar_interoperabilidad_866(self):

        cambios = []

        if self.existe_tabla("medicamentos"):
            cambios.extend(
                self.sincronizar_columnas(
                    "medicamentos",
                    {
                        "codigo_cum": "codigo_cum TEXT",
                        "historia_id": "historia_id INTEGER",
                    },
                )
            )

        if self.existe_tabla("diagnosticos"):
            cambios.extend(
                self.sincronizar_columnas(
                    "diagnosticos",
                    {
                        "historia_id": "historia_id INTEGER",
                    },
                )
            )

        if self.existe_tabla("alergias"):
            cambios.extend(
                self.sincronizar_columnas(
                    "alergias",
                    {
                        "codigo_alergeno": "codigo_alergeno TEXT",
                        "estado": "estado TEXT DEFAULT 'Activa'",
                        "fecha_diagnostico": "fecha_diagnostico TEXT",
                        "usuario_creacion": "usuario_creacion INTEGER",
                        "usuario_actualizacion": "usuario_actualizacion INTEGER",
                        "fecha_actualizacion": "fecha_actualizacion TEXT",
                    },
                )
            )

        if self.existe_tabla("signos_vitales"):
            cambios.extend(
                self.sincronizar_columnas(
                    "signos_vitales",
                    {
                        "historia_id": "historia_id INTEGER",
                    },
                )
            )

        if self.existe_tabla("ordenes_medicas"):
            cambios.extend(
                self.sincronizar_columnas(
                    "ordenes_medicas",
                    {
                        "token_pdf": "token_pdf TEXT",
                    },
                )
            )

        cambios.extend(self.migrar_rips())

        return cambios

        # =====================================================
    # RIPS JSON (Resolución 948 de 2026, antes 2275 de 2023)
    # Campos minimos para poder construir el archivo de
    # transacción sin modificar la operación clínica diaria.
    # =====================================================

    def migrar_divipola_codigo_postal(self):
        cambios = []
        if self.existe_tabla("divipola"):
            cambios.extend(
                self.sincronizar_columnas(
                    "divipola",
                    {"codigo_postal": "codigo_postal TEXT"},
                )
            )
        return cambios

    def migrar_documentos_profesional_archivo(self):
        cambios = []
        if self.existe_tabla("documentos_profesional"):
            cambios.extend(
                self.sincronizar_columnas(
                    "documentos_profesional",
                    {
                        "archivo_base64": "archivo_base64 TEXT",
                        "nombre_archivo": "nombre_archivo TEXT",
                    },
                )
            )
        return cambios

    def migrar_facturacion_servicios(self):
        cambios = []
        if self.existe_tabla("facturas_electronicas"):
            cambios.extend(
                self.sincronizar_columnas(
                    "facturas_electronicas",
                    {
                        "servicio_paciente_id": "servicio_paciente_id INTEGER",
                        "concepto": "concepto TEXT",
                    },
                )
            )
        return cambios

    def migrar_cartera_facturacion(self):
        cambios = []
        if self.existe_tabla("facturas_electronicas"):
            cambios.extend(
                self.sincronizar_columnas(
                    "facturas_electronicas",
                    {
                        "entidad_responsable_pago": "entidad_responsable_pago TEXT",
                        "estado_cartera": "estado_cartera TEXT DEFAULT 'Pendiente de pago'",
                        "fecha_vencimiento": "fecha_vencimiento TEXT",
                        "fecha_pago": "fecha_pago TEXT",
                        "valor_pagado": "valor_pagado REAL DEFAULT 0",
                        "metodo_pago_recibido": "metodo_pago_recibido TEXT",
                        "motivo_anulacion": "motivo_anulacion TEXT",
                    },
                )
            )
        return cambios

    def migrar_bloqueo_login(self):
        cambios = []
        if self.existe_tabla("usuarios"):
            cambios.extend(
                self.sincronizar_columnas(
                    "usuarios",
                    {
                        "intentos_fallidos": "intentos_fallidos INTEGER DEFAULT 0",
                        "bloqueado_hasta": "bloqueado_hasta TEXT",
                    },
                )
            )
        return cambios

    def migrar_flujo_chatbot(self):
        cambios = []

        if self.existe_tabla("whatsapp_hilos"):
            cambios.extend(
                self.sincronizar_columnas(
                    "whatsapp_hilos",
                    {"departamento": "departamento TEXT", "opcion_actual_id": "opcion_actual_id INTEGER"},
                )
            )

        if not self.existe_tabla("whatsapp_flujo_opciones"):
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS whatsapp_flujo_opciones(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    padre_id INTEGER,
                    orden INTEGER DEFAULT 0,
                    texto_boton TEXT NOT NULL,
                    tipo_accion TEXT NOT NULL DEFAULT 'respuesta_automatica',
                    contenido_respuesta TEXT,
                    departamento TEXT,
                    activo INTEGER DEFAULT 1,
                    FOREIGN KEY(padre_id) REFERENCES whatsapp_flujo_opciones(id)
                );
            """)
            self.connection.commit()
            cambios.append("Se creó la tabla whatsapp_flujo_opciones")

        # Siembra el flujo por defecto SOLO si la tabla esta
        # vacia -- para que un administrador que ya haya
        # personalizado el suyo no se lo pisen en una
        # actualizacion futura.
        total_opciones = self.connection.execute("SELECT COUNT(*) FROM whatsapp_flujo_opciones").fetchone()[0]
        if total_opciones == 0:
            cursor = self.connection.cursor()

            raiz = [
                (1, "Mi próxima visita programada", "respuesta_automatica", "{proxima_visita}", None),
                (2, "Mi última orden médica", "respuesta_automatica", "{ultima_orden}", None),
                (3, "Últimas recomendaciones del médico", "respuesta_automatica", "{ultimas_recomendaciones}", None),
                (4, "Facturación y cartera", "submenu", None, None),
                (5, "Programación / Agendamiento de visitas", "submenu", None, None),
                (6, "Coordinación médica / Historia clínica", "submenu", None, None),
                (7, "Hablar con un asesor", "derivar_departamento", "Ya lo comunicamos con un asesor de Atención al Usuario. En un momento le atenderán por este mismo medio.", "Atención al Usuario"),
            ]
            ids_raiz = {}
            for orden, texto, tipo, contenido, depto in raiz:
                cursor.execute(
                    "INSERT INTO whatsapp_flujo_opciones(padre_id, orden, texto_boton, tipo_accion, contenido_respuesta, departamento) "
                    "VALUES (NULL, ?, ?, ?, ?, ?)",
                    (orden, texto, tipo, contenido, depto),
                )
                ids_raiz[orden] = cursor.lastrowid

            submenu_facturacion = [
                (1, "Consultar el estado de una factura", "derivar_departamento",
                 "Lo comunicamos con Facturación para revisar el estado de su factura.", "Facturación"),
                (2, "Reportar un problema de cobro", "derivar_departamento",
                 "Lo comunicamos con Facturación para revisar su caso.", "Facturación"),
            ]
            for orden, texto, tipo, contenido, depto in submenu_facturacion:
                cursor.execute(
                    "INSERT INTO whatsapp_flujo_opciones(padre_id, orden, texto_boton, tipo_accion, contenido_respuesta, departamento) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (ids_raiz[4], orden, texto, tipo, contenido, depto),
                )

            submenu_programacion = [
                (1, "Solicitar o cambiar una cita", "derivar_departamento",
                 "Lo comunicamos con el área de Programación para agendar o modificar su cita.", "Programación"),
                (2, "Cancelar una visita", "derivar_departamento",
                 "Lo comunicamos con el área de Programación para cancelar su visita.", "Programación"),
            ]
            for orden, texto, tipo, contenido, depto in submenu_programacion:
                cursor.execute(
                    "INSERT INTO whatsapp_flujo_opciones(padre_id, orden, texto_boton, tipo_accion, contenido_respuesta, departamento) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (ids_raiz[5], orden, texto, tipo, contenido, depto),
                )

            submenu_medico = [
                (1, "Hablar con Coordinación Médica", "derivar_departamento",
                 "Lo comunicamos con Coordinación Médica.", "Coordinación Médica"),
                (2, "Solicitar copia de mi historia clínica", "derivar_departamento",
                 "Lo comunicamos con Coordinación Médica para tramitar su solicitud.", "Coordinación Médica"),
            ]
            for orden, texto, tipo, contenido, depto in submenu_medico:
                cursor.execute(
                    "INSERT INTO whatsapp_flujo_opciones(padre_id, orden, texto_boton, tipo_accion, contenido_respuesta, departamento) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (ids_raiz[6], orden, texto, tipo, contenido, depto),
                )

            self.connection.commit()
            cambios.append("Se sembró el flujo por defecto del chatbot")

        return cambios

    def migrar_whatsapp_hilos(self):
        cambios = []
        if not self.existe_tabla("whatsapp_hilos"):
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS whatsapp_hilos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_celular TEXT NOT NULL UNIQUE,
                    paciente_id INTEGER,
                    atendido_por_humano INTEGER DEFAULT 0,
                    agente_asignado_id INTEGER,
                    estado TEXT DEFAULT 'Abierto',
                    ultimo_mensaje TEXT,
                    ultima_actividad TEXT DEFAULT CURRENT_TIMESTAMP,
                    no_leidos INTEGER DEFAULT 0,
                    FOREIGN KEY(paciente_id) REFERENCES pacientes(id),
                    FOREIGN KEY(agente_asignado_id) REFERENCES usuarios(id)
                );
            """)
            self.connection.commit()
            cambios.append("Se creó la tabla whatsapp_hilos")
        return cambios

    def migrar_perfil_asistencial(self):
        cambios = []
        cursor = self.connection.cursor()
        existente = cursor.execute("SELECT id FROM roles WHERE nombre='Asistencial'").fetchone()

        if not existente:
            cursor.execute(
                "INSERT INTO roles(nombre, descripcion, acceso_total, es_del_sistema) VALUES "
                "('Asistencial', 'Chatbot y agente de WhatsApp, creación de pacientes, programación de agendas, "
                "inventario y facturación.', 0, 1)"
            )
            rol_id = cursor.lastrowid
            for modulo in ("chatbot_whatsapp", "agente_whatsapp", "pacientes", "programacion", "inventario", "facturacion"):
                cursor.execute("INSERT INTO roles_permisos(rol_id, modulo) VALUES (?, ?)", (rol_id, modulo))
            self.connection.commit()
            cambios.append("Se creó el perfil 'Asistencial'")
        else:
            # Si el perfil ya existía de una version anterior (antes de
            # que existiera el panel de Agente WhatsApp), se le agrega
            # ese permiso nuevo, sin tocar el resto de sus permisos.
            rol_id = existente[0]
            tiene_agente = cursor.execute(
                "SELECT 1 FROM roles_permisos WHERE rol_id=? AND modulo='agente_whatsapp'", (rol_id,)
            ).fetchone()
            if not tiene_agente:
                cursor.execute("INSERT INTO roles_permisos(rol_id, modulo) VALUES (?, 'agente_whatsapp')", (rol_id,))
                self.connection.commit()
                cambios.append("Se agregó el permiso 'agente_whatsapp' al perfil 'Asistencial'")

        return cambios

    def migrar_roles_permisos(self):
        cambios = []
        if not self.existe_tabla("roles"):
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS roles(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    descripcion TEXT,
                    acceso_total INTEGER DEFAULT 0,
                    es_del_sistema INTEGER DEFAULT 0,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS roles_permisos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rol_id INTEGER NOT NULL,
                    modulo TEXT NOT NULL,
                    FOREIGN KEY(rol_id) REFERENCES roles(id),
                    UNIQUE(rol_id, modulo)
                );
            """)
            self.connection.commit()
            cambios.append("Se crearon las tablas roles y roles_permisos")

        # Sembrar los roles que ya existian en el codigo (solo si
        # la tabla de roles esta vacia -- para no duplicar ni
        # pisar cambios que ya haya hecho un administrador).
        total_roles = self.connection.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
        if total_roles == 0:
            from core.permissions.permissions import PERMISSIONS
            cursor = self.connection.cursor()
            descripciones = {
                "Administrador": "Acceso total al sistema.",
                "Director Médico": "Acceso total al sistema.",
                "Coordinador": "Coordinación operativa: pacientes, programación, facturación, nómina, inventario.",
                "Médico": "Proceso médico completo: historia clínica, órdenes, medicamentos, y asignación del programa de atención.",
                "Enfermero": "Notas clínicas del paciente y administración de medicamentos.",
                "Cuidador": "Cuidado directo del paciente (solo desde la app móvil).",
                "Fisioterapeuta": "Profesional de terapias: notas, órdenes, historia clínica.",
                "Terapeuta Respiratorio": "Profesional de terapias: notas, órdenes, historia clínica.",
                "Psicólogo": "Profesional de terapias: notas, órdenes, historia clínica.",
                "Salud Ocupacional": "Profesional de terapias: notas, órdenes, historia clínica.",
                "Terapeuta": "Profesional de terapias: notas, órdenes, historia clínica.",
                "Nutricionista": "Profesional de terapias: notas, órdenes, historia clínica.",
                "Administrativo": "Creación de pacientes y agendamiento de visitas.",
                "Auxiliar": "Creación de pacientes y agendamiento de visitas.",
                "Auditor": "Solo consulta: auditoría y reportes.",
                "Facturación": "Facturación, RIPS y catálogos.",
                "Inventario": "Inventario de insumos.",
                "Consulta": "Solo consulta de pacientes.",
            }
            for nombre_rol, permisos in PERMISSIONS.items():
                acceso_total = 1 if "*" in permisos else 0
                cursor.execute(
                    "INSERT OR IGNORE INTO roles(nombre, descripcion, acceso_total, es_del_sistema) VALUES (?, ?, ?, 1)",
                    (nombre_rol, descripciones.get(nombre_rol, ""), acceso_total),
                )
                rol_id = cursor.execute("SELECT id FROM roles WHERE nombre=?", (nombre_rol,)).fetchone()[0]
                if not acceso_total:
                    for modulo in permisos:
                        cursor.execute(
                            "INSERT OR IGNORE INTO roles_permisos(rol_id, modulo) VALUES (?, ?)",
                            (rol_id, modulo),
                        )
            self.connection.commit()
            cambios.append(f"Se sembraron {len(PERMISSIONS)} roles con sus permisos")

        return cambios

    def migrar_chatbot_whatsapp(self):
        cambios = []
        if not self.existe_tabla("configuracion_whatsapp"):
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS configuracion_whatsapp(
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    habilitado INTEGER DEFAULT 0,
                    token_acceso TEXT,
                    id_numero_telefono TEXT,
                    token_verificacion_webhook TEXT,
                    mensaje_bienvenida TEXT DEFAULT 'Hola, soy el asistente virtual de HomeCare del Quindío I.P.S. 👋',
                    fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP,
                    usuario_actualizacion INTEGER
                );
            """)
            cambios.append("Se creó la tabla configuracion_whatsapp")

        if not self.existe_tabla("whatsapp_conversaciones"):
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS whatsapp_conversaciones(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_celular TEXT NOT NULL,
                    paciente_id INTEGER,
                    direccion TEXT NOT NULL,
                    mensaje TEXT,
                    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(paciente_id) REFERENCES pacientes(id)
                );
            """)
            cambios.append("Se creó la tabla whatsapp_conversaciones")

        self.connection.commit()
        return cambios

    def migrar_configuracion_legal(self):
        cambios = []
        if not self.existe_tabla("configuracion_legal"):
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS configuracion_legal(
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    reps_codigo_habilitacion TEXT, reps_numero_habilitacion TEXT,
                    reps_fecha_habilitacion TEXT, reps_vigencia_hasta TEXT,
                    rips_nit_prestador TEXT, rips_codigo_prestador TEXT, rips_razon_social TEXT,
                    dian_nit TEXT, dian_digito_verificacion TEXT,
                    dian_resolucion_numero TEXT, dian_resolucion_prefijo TEXT,
                    dian_resolucion_rango_desde TEXT, dian_resolucion_rango_hasta TEXT,
                    dian_resolucion_fecha_desde TEXT, dian_resolucion_fecha_hasta TEXT,
                    dian_software_id TEXT, dian_software_pin TEXT,
                    dian_certificado_nombre_archivo TEXT, dian_certificado_base64 TEXT, dian_certificado_password TEXT,
                    dian_ambiente TEXT DEFAULT 'Habilitación', dian_test_set_id TEXT,
                    dian_nomina_software_id TEXT, dian_nomina_software_pin TEXT,
                    dian_nomina_ambiente TEXT DEFAULT 'Habilitación', dian_nomina_test_set_id TEXT,
                    pila_operador TEXT, pila_usuario TEXT, pila_clave TEXT,
                    sic_numero_registro_rnbd TEXT, sic_fecha_registro TEXT,
                    arl_nit TEXT, arl_nombre TEXT,
                    fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP,
                    usuario_actualizacion INTEGER
                );
            """)
            self.connection.commit()
            cambios.append("Se creó la tabla configuracion_legal")
        return cambios

    def migrar_reconocimiento_facial(self):
        cambios = []
        if self.existe_tabla("profesionales"):
            cambios.extend(
                self.sincronizar_columnas(
                    "profesionales",
                    {"foto_enrolamiento_base64": "foto_enrolamiento_base64 TEXT"},
                )
            )
        return cambios

    def migrar_catalogo_examenes_laboratorio(self):
        cambios = []
        if not self.existe_tabla("catalogo_examenes_laboratorio"):
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS catalogo_examenes_laboratorio(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_examen TEXT NOT NULL UNIQUE,
                    categoria TEXT,
                    activo INTEGER DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS catalogo_parametros_laboratorio(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    examen_id INTEGER NOT NULL,
                    nombre_parametro TEXT NOT NULL,
                    unidad TEXT,
                    rango_min REAL,
                    rango_max REAL,
                    orden INTEGER DEFAULT 0,
                    FOREIGN KEY(examen_id) REFERENCES catalogo_examenes_laboratorio(id)
                );
            """)
            self.connection.commit()
            cambios.append("Se creó el catálogo de exámenes de laboratorio")
        return cambios

    def migrar_firma_contratos(self):
        cambios = []
        if self.existe_tabla("contratos"):
            cambios.extend(
                self.sincronizar_columnas(
                    "contratos",
                    {
                        "firma_base64": "firma_base64 TEXT",
                        "firmado": "firmado INTEGER DEFAULT 0",
                        "fecha_firma": "fecha_firma TEXT",
                    },
                )
            )
        return cambios

    def migrar_examen_fisico_recomendaciones(self):
        cambios = []
        if not self.existe_tabla("examen_fisico"):
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS examen_fisico(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id INTEGER NOT NULL,
                    programacion_id INTEGER,
                    profesional_id INTEGER,
                    tipo_profesional TEXT,
                    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
                    cabeza TEXT, cara TEXT, boca TEXT, cuello TEXT, torax TEXT,
                    abdomen TEXT, extremidades TEXT, vascular TEXT, neurologico TEXT, columna TEXT,
                    usuario_creacion INTEGER,
                    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(paciente_id) REFERENCES pacientes(id),
                    FOREIGN KEY(profesional_id) REFERENCES profesionales(id)
                );
            """)
            cambios.append("Se creó la tabla examen_fisico")

        if not self.existe_tabla("recomendaciones_medicas"):
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS recomendaciones_medicas(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id INTEGER NOT NULL,
                    programacion_id INTEGER,
                    profesional_id INTEGER,
                    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
                    diagnostico_ppal_codigo TEXT, diagnostico_ppal_nombre TEXT,
                    diagnostico_rel1_codigo TEXT, diagnostico_rel1_nombre TEXT,
                    diagnostico_rel2_codigo TEXT, diagnostico_rel2_nombre TEXT,
                    diagnostico_rel3_codigo TEXT, diagnostico_rel3_nombre TEXT,
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
            """)
            cambios.append("Se creó la tabla recomendaciones_medicas")

        self.connection.commit()
        return cambios

    def migrar_calidad(self):
        cambios = []
        if not self.existe_tabla("calidad_pqr"):
            self.connection.executescript("""
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
            """)
            cambios.append("Se creó la tabla calidad_pqr")

        if not self.existe_tabla("calidad_planificacion"):
            self.connection.executescript("""
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
            """)
            cambios.append("Se creó la tabla calidad_planificacion")

        if not self.existe_tabla("calidad_evaluaciones"):
            self.connection.executescript("""
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
            """)
            cambios.append("Se creó la tabla calidad_evaluaciones")

        self.connection.commit()
        return cambios

    def migrar_laboratorio_items(self):
        cambios = []
        if not self.existe_tabla("laboratorio_items"):
            self.connection.executescript("""
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
                    FOREIGN KEY(resultado_id) REFERENCES laboratorios_resultados(id)
                );
                CREATE INDEX IF NOT EXISTS idx_laboratorio_items_resultado
                ON laboratorio_items(resultado_id);
            """)
            self.connection.commit()
            cambios.append("Se creó la tabla laboratorio_items")
        return cambios

    def migrar_laboratorios_resultados(self):
        cambios = []
        if not self.existe_tabla("laboratorios_resultados"):
            self.connection.executescript("""
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
                    FOREIGN KEY(paciente_id) REFERENCES pacientes(id),
                    FOREIGN KEY(profesional_id) REFERENCES profesionales(id)
                );
                CREATE INDEX IF NOT EXISTS idx_laboratorios_resultados_paciente
                ON laboratorios_resultados(paciente_id);
            """)
            self.connection.commit()
            cambios.append("Se creó la tabla laboratorios_resultados")
        return cambios

    def migrar_catalogo_turnos(self):
        cambios = []

        if not self.existe_tabla("catalogo_turnos"):
            self.connection.executescript("""
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
            """)
            self.connection.commit()
            cambios.append("Se creó la tabla catalogo_turnos")

        if self.existe_tabla("turnos_programados"):
            cambios.extend(
                self.sincronizar_columnas(
                    "turnos_programados",
                    {
                        "paciente_id": "paciente_id INTEGER",
                        "catalogo_turno_id": "catalogo_turno_id INTEGER",
                        "programacion_id": "programacion_id INTEGER",
                    },
                )
            )

        return cambios

    def migrar_geolocalizacion_pacientes(self):
        # Coordenadas del domicilio del paciente, necesarias
        # para verificar (por geocercas) que el profesional
        # realmente estuvo en la ubicacion del paciente al
        # marcar ingreso/salida de una visita.

        cambios = []

        if self.existe_tabla("pacientes"):
            cambios.extend(
                self.sincronizar_columnas(
                    "pacientes",
                    {
                        "latitud": "latitud REAL",
                        "longitud": "longitud REAL",
                        "radio_geocerca_metros": "radio_geocerca_metros INTEGER DEFAULT 150",
                        "ubicacion_confirmada": "ubicacion_confirmada INTEGER DEFAULT 0",
                        "tipo_cuidado": "tipo_cuidado TEXT DEFAULT 'No Ventilado'",
                        "zona_ciudad": "zona_ciudad TEXT",
                    },
                )
            )

        return cambios

    def migrar_rips(self):

        cambios = []

        if self.existe_tabla("pacientes"):
            cambios.extend(
                self.sincronizar_columnas(
                    "pacientes",
                    {
                        "codigo_municipio_divipola": "codigo_municipio_divipola TEXT",
                        "codigo_pais_residencia": "codigo_pais_residencia TEXT DEFAULT '170'",
                        "incapacidad": "incapacidad TEXT DEFAULT 'NO'",
                        "tipo_usuario_rips": "tipo_usuario_rips TEXT",
                    },
                )
            )

        if self.existe_tabla("programaciones"):
            cambios.extend(
                self.sincronizar_columnas(
                    "programaciones",
                    {
                        "codigo_cups": "codigo_cups TEXT",
                        "valor_servicio": "valor_servicio REAL DEFAULT 0",
                        "finalidad_tecnologia_salud": "finalidad_tecnologia_salud TEXT",
                        "causa_externa": "causa_externa TEXT",
                        "numero_autorizacion": "numero_autorizacion TEXT",
                        "numero_factura": "numero_factura TEXT",
                    },
                )
            )

        if self.existe_tabla("diagnosticos"):
            cambios.extend(
                self.sincronizar_columnas(
                    "diagnosticos",
                    {
                        "codigo_cie11": "codigo_cie11 TEXT",
                        "tipo_diagnostico_rips": "tipo_diagnostico_rips TEXT",
                    },
                )
            )

        if self.existe_tabla("profesionales"):
            cambios.extend(
                self.sincronizar_columnas(
                    "profesionales",
                    {
                        "codigo_rethus": "codigo_rethus TEXT",
                        "usuario_id": "usuario_id INTEGER",
                    },
                )
            )

        return cambios

        # =====================================================
    # APP MÓVIL - administracion_medicamentos.medicamento_id
    # debe poder quedar en NULL (la app permite registrar un
    # medicamento administrado sin vincularlo a una fórmula
    # previamente cargada en el sistema). SQLite no permite
    # quitar un NOT NULL con ALTER TABLE, así que se reconstruye
    # la tabla preservando los datos existentes.
    # =====================================================

    def migrar_administracion_medicamentos_nullable(self):

        if not self.existe_tabla("administracion_medicamentos"):
            return []

        self.conectar()

        self.cursor.execute("PRAGMA table_info(administracion_medicamentos)")
        columnas = self.cursor.fetchall()

        columna_medicamento = next(
            (c for c in columnas if c[1] == "medicamento_id"), None
        )

        # columna[3] == 1 significa NOT NULL en PRAGMA table_info
        if columna_medicamento is None or columna_medicamento[3] == 0:
            return []

        try:
            self.cursor.executescript("""

                ALTER TABLE administracion_medicamentos
                RENAME TO administracion_medicamentos_old;

                CREATE TABLE administracion_medicamentos(

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

                INSERT INTO administracion_medicamentos (
                    id, medicamento_id, paciente_id, profesional, fecha, hora,
                    dosis, via, observaciones, estado, fecha_registro
                )
                SELECT
                    id, medicamento_id, paciente_id, profesional, fecha, hora,
                    dosis, via, observaciones, estado, fecha_registro
                FROM administracion_medicamentos_old;

                DROP TABLE administracion_medicamentos_old;

            """)

            self.connection.commit()

            return ["administracion_medicamentos: medicamento_id ahora acepta NULL"]

        except Exception as ex:
            self.connection.rollback()
            return [f"ERROR migrando administracion_medicamentos: {ex}"]

    def migrar_usuarios(self):
        # La tabla base de schema.py nunca tuvo "estado",
        # "correo" ni "telefono", pero el modulo de usuarios
        # los exige desde siempre (login, edicion, listado).
        # Nunca se detecto antes porque las pruebas de esta
        # sesion siempre corrieron contra una base de datos
        # que ya las tenia de una version anterior.

        cambios = []

        if self.existe_tabla("usuarios"):
            cambios.extend(
                self.sincronizar_columnas(
                    "usuarios",
                    {
                        "estado": "estado TEXT DEFAULT 'Activo'",
                        "correo": "correo TEXT",
                        "telefono": "telefono TEXT",
                        "ultimo_acceso": "ultimo_acceso TEXT",
                    },
                )
            )

        return cambios

    def migrar_plantillas_visita_rol(self):
        cambios = []
        if self.existe_tabla("plantillas_visita"):
            cambios.extend(
                self.sincronizar_columnas(
                    "plantillas_visita",
                    {"rol_destinatario": "rol_destinatario TEXT DEFAULT 'Todos'"},
                )
            )
        return cambios

    def migrar_consentimientos(self):
        if not self.existe_tabla("consentimientos_informados"):
            self.connection.executescript("""
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
                    FOREIGN KEY(paciente_id) REFERENCES pacientes(id)
                );
                CREATE INDEX IF NOT EXISTS idx_consentimientos_paciente
                ON consentimientos_informados(paciente_id);
            """)
            self.connection.commit()
            return ["Se creó la tabla consentimientos_informados"]
        return []

    def migrar_diagnosticos_cups(self):
        cambios = []
        if self.existe_tabla("diagnosticos"):
            cambios.extend(
                self.sincronizar_columnas(
                    "diagnosticos",
                    {
                        "codigo_cups": "codigo_cups TEXT",
                        "descripcion_cups": "descripcion_cups TEXT",
                    },
                )
            )
        return cambios

    def migrar_cie10_normalizado(self):
        # La busqueda de CIE-10 comparaba el texto escrito
        # directo contra la descripcion, y SQLite LIKE no
        # ignora tildes en caracteres Unicode -- "ulcera" no
        # encontraba "Úlcera". Se agrega una columna con el
        # texto sin tildes/mayusculas (igual que ya se hace
        # para CUPS y CUM) y se recalcula para lo que ya exista.

        cambios = []

        if not self.existe_tabla("cie10"):
            return cambios

        cambios.extend(
            self.sincronizar_columnas(
                "cie10",
                {"descripcion_normalizada": "descripcion_normalizada TEXT"},
            )
        )

        from core.texto_utils import normalizar

        cursor = self.connection.cursor()
        cursor.execute("SELECT id, descripcion FROM cie10 WHERE descripcion_normalizada IS NULL OR descripcion_normalizada=''")
        pendientes = cursor.fetchall()

        if pendientes:
            cursor.executemany(
                "UPDATE cie10 SET descripcion_normalizada=? WHERE id=?",
                [(normalizar(fila[1] or ""), fila[0]) for fila in pendientes],
            )
            self.connection.commit()
            cambios.append(f"Se normalizaron {len(pendientes)} descripciones de CIE-10")

        return cambios

    def migrar_fotos_procedimientos(self):
        if not self.existe_tabla("fotos_procedimientos"):
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS fotos_procedimientos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id INTEGER NOT NULL,
                    descripcion TEXT,
                    foto_base64 TEXT NOT NULL,
                    profesional_id INTEGER,
                    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
                    usuario_creacion INTEGER,
                    FOREIGN KEY(paciente_id) REFERENCES pacientes(id),
                    FOREIGN KEY(profesional_id) REFERENCES profesionales(id)
                );
                CREATE INDEX IF NOT EXISTS idx_fotos_procedimientos_paciente
                ON fotos_procedimientos(paciente_id);
            """)
            self.connection.commit()
            return ["Se creó la tabla fotos_procedimientos"]
        return []

    def migrar_firma_y_consecutivos(self):
        # Firma digital del profesional (capturada al crearlo),
        # y el sistema de consecutivo + notas aclaratorias para
        # que todo informe de historia clinica (evoluciones)
        # quede numerado y trazable.

        cambios = []

        if self.existe_tabla("profesionales"):
            cambios.extend(
                self.sincronizar_columnas(
                    "profesionales",
                    {
                        "firma_base64": "firma_base64 TEXT",
                    },
                )
            )

        if self.existe_tabla("evoluciones"):
            cambios.extend(
                self.sincronizar_columnas(
                    "evoluciones",
                    {
                        "consecutivo": "consecutivo INTEGER",
                        "tipo_registro": "tipo_registro TEXT DEFAULT 'INFORME'",
                        "nota_aclaratoria_de": "nota_aclaratoria_de INTEGER",
                        "firma_profesional_base64": "firma_profesional_base64 TEXT",
                    },
                )
            )

        return cambios

    def migrar_acudientes(self):
        # La tabla base solo tenia 6 columnas, pero el modulo
        # completo de acudientes (creado, editado desde el
        # formulario) siempre necesito muchas mas -- nunca se
        # habian agregado.

        cambios = []

        if self.existe_tabla("acudientes"):
            cambios.extend(
                self.sincronizar_columnas(
                    "acudientes",
                    {
                        "tipo_documento": "tipo_documento TEXT",
                        "documento": "documento TEXT",
                        "telefono_principal": "telefono_principal TEXT",
                        "telefono_secundario": "telefono_secundario TEXT",
                        "correo": "correo TEXT",
                        "barrio": "barrio TEXT",
                        "municipio": "municipio TEXT",
                        "departamento": "departamento TEXT",
                        "ciudad": "ciudad TEXT",
                        "ocupacion": "ocupacion TEXT",
                        "observaciones": "observaciones TEXT",
                        "es_principal": "es_principal INTEGER DEFAULT 0",
                        "autoriza_decisiones": "autoriza_decisiones INTEGER DEFAULT 0",
                        "recibe_informacion": "recibe_informacion INTEGER DEFAULT 1",
                        "estado": "estado TEXT DEFAULT 'Activo'",
                        "fecha_creacion": "fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP",
                        "fecha_actualizacion": "fecha_actualizacion TEXT",
                    },
                )
            )

        return cambios

    def migrar_actividades_programa(self):
        # Agrega el catalogo de actividades y las columnas
        # nuevas de servicios_paciente (para instalaciones que
        # ya tenian esa tabla de una version anterior).

        cambios = []

        if not self.existe_tabla("catalogo_actividades"):
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS catalogo_actividades(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    categoria TEXT,
                    activo INTEGER DEFAULT 1
                );
            """)
            self.connection.commit()
            cambios.append("Se creó la tabla catalogo_actividades")

        if self.existe_tabla("servicios_paciente"):
            cambios.extend(
                self.sincronizar_columnas(
                    "servicios_paciente",
                    {
                        "actividad_id": "actividad_id INTEGER",
                        "numero_sesiones": "numero_sesiones INTEGER",
                        "paciente_programa_id": "paciente_programa_id INTEGER",
                        "renovacion_automatica": "renovacion_automatica INTEGER DEFAULT 0",
                    },
                )
            )

        if self.existe_tabla("planilla_visitas"):
            cambios.extend(
                self.sincronizar_columnas(
                    "planilla_visitas",
                    {
                        "profesional_id": "profesional_id INTEGER",
                        "motivo_cancelacion": "motivo_cancelacion TEXT",
                    },
                )
            )

        return cambios

    def migrar_verificacion_geocerca(self):
        # Guarda si se pudo confirmar que el profesional
        # realmente estaba en el domicilio del paciente al
        # marcar ingreso/salida, y a que distancia. Tambien
        # guarda la foto tomada en ese momento, como
        # corroboracion adicional (ademas del GPS) de que el
        # profesional si estaba en el lugar.

        cambios = []

        if self.existe_tabla("programaciones"):
            cambios.extend(
                self.sincronizar_columnas(
                    "programaciones",
                    {
                        "geocerca_inicio_ok": "geocerca_inicio_ok INTEGER",
                        "distancia_inicio_metros": "distancia_inicio_metros REAL",
                        "geocerca_fin_ok": "geocerca_fin_ok INTEGER",
                        "distancia_fin_metros": "distancia_fin_metros REAL",
                        "foto_ingreso_base64": "foto_ingreso_base64 TEXT",
                        "foto_salida_base64": "foto_salida_base64 TEXT",
                    },
                )
            )

        return cambios

    def migrar_nomina(self):

        cambios = []

        if self.existe_tabla("nomina_detalle"):
            cambios.extend(
                self.sincronizar_columnas(
                    "nomina_detalle",
                    {
                        "auxilio_transporte": "auxilio_transporte REAL DEFAULT 0",
                    },
                )
            )

        if self.existe_tabla("profesionales"):
            cambios.extend(
                self.sincronizar_columnas(
                    "profesionales",
                    {
                        "tipo_contrato":
                            "tipo_contrato TEXT DEFAULT 'POR_HORAS'",

                        "salario_fijo": "salario_fijo REAL DEFAULT 0",

                        "valor_hora": "valor_hora REAL DEFAULT 0",

                        "numero_cuenta": "numero_cuenta TEXT",

                        "banco": "banco TEXT",

                        "tipo_cuenta": "tipo_cuenta TEXT",

                        "eps_profesional": "eps_profesional TEXT",

                        "arl": "arl TEXT",

                        "fondo_pension": "fondo_pension TEXT",

                        "tipo_vinculacion": "tipo_vinculacion TEXT DEFAULT 'Prestación de Servicios'",

                        "nivel_riesgo_arl": "nivel_riesgo_arl TEXT DEFAULT 'I'",
                    },
                )
            )

        if self.existe_tabla("programaciones"):
            cambios.extend(
                self.sincronizar_columnas(
                    "programaciones",
                    {
                        "hora_real_inicio": "hora_real_inicio TEXT",

                        "hora_real_fin": "hora_real_fin TEXT",

                        "latitud_inicio": "latitud_inicio REAL",

                        "longitud_inicio": "longitud_inicio REAL",

                        "latitud_fin": "latitud_fin REAL",

                        "longitud_fin": "longitud_fin REAL",

                        "horas_trabajadas": "horas_trabajadas REAL",

                        "liquidado": "liquidado INTEGER DEFAULT 0",

                        "nomina_id": "nomina_id INTEGER",
                    },
                )
            )

        return cambios

    def migrar_programaciones_completar(self):

        if not self.existe_tabla("programaciones"):
            return []

        columnas = {

            "eliminado": "eliminado INTEGER DEFAULT 0",

            "procedimiento": "procedimiento TEXT",

            "observaciones": "observaciones TEXT",

            "diagnostico_id": "diagnostico_id INTEGER",

            "telefono_contacto": "telefono_contacto TEXT",

            "nombre_contacto": "nombre_contacto TEXT",
        }

        return self.sincronizar_columnas(
            "programaciones",
            columnas,
        )

        # =====================================================
    # PACIENTES LEGACY
    # =====================================================

    def migrar_pacientes_legacy(self):

        if not self.existe_tabla("pacientes"):
            return []

        columnas = {

            "uuid": "uuid TEXT",

            "nombre_completo": "nombre_completo TEXT",

            "edad": "edad INTEGER",

            "latitud": "latitud REAL",

            "longitud": "longitud REAL",

            "riesgo_clinico":
                "riesgo_clinico TEXT DEFAULT 'MEDIO'",

            "prioridad_domiciliaria":
                "prioridad_domiciliaria TEXT DEFAULT 'MEDIA'",

            "estado": "estado TEXT DEFAULT 'Activo'",
        }

        return self.sincronizar_columnas(
            "pacientes",
            columnas,
        )
    
        # =====================================================
    # PROFESIONALES LEGACY
    # =====================================================

    def migrar_profesionales_legacy(self):

        if not self.existe_tabla("profesionales"):
            return []

        columnas = {

            "primer_nombre": "primer_nombre TEXT",

            "segundo_nombre": "segundo_nombre TEXT",

            "primer_apellido": "primer_apellido TEXT",

            "segundo_apellido": "segundo_apellido TEXT",

            "nombre_completo": "nombre_completo TEXT",

            "especialidad_principal":
                "especialidad_principal TEXT",

            "municipio": "municipio TEXT",

            "departamento": "departamento TEXT",

            "disponible":
                "disponible INTEGER DEFAULT 1",

            "latitud": "latitud REAL",

            "longitud": "longitud REAL",

            "capacidad_diaria":
                "capacidad_diaria INTEGER DEFAULT 20",
        }

        return self.sincronizar_columnas(
            "profesionales",
            columnas,
        )
    
        # =====================================================
    # PROFESIONALES - COMPLETAR COLUMNAS DEL REPOSITORIO
    # (el repositorio de profesionales fue escrito para un
    # esquema mas rico del que existia en la tabla real)
    # =====================================================

    def migrar_profesionales_completar(self):

        if not self.existe_tabla("profesionales"):
            return []

        columnas = {

            "uuid": "uuid TEXT",

            "tipo_documento": "tipo_documento TEXT",

            "celular": "celular TEXT",

            "direccion": "direccion TEXT",

            "registro_profesional": "registro_profesional TEXT",

            "acepta_urgencias":
                "acepta_urgencias INTEGER DEFAULT 0",

            "tiempo_promedio_visita":
                "tiempo_promedio_visita INTEGER DEFAULT 45",

            "radio_cobertura_km":
                "radio_cobertura_km REAL DEFAULT 10",

            "observaciones": "observaciones TEXT",

            "usuario_creacion": "usuario_creacion INTEGER",

            "usuario_actualizacion": "usuario_actualizacion INTEGER",

            "fecha_creacion":
                "fecha_creacion TEXT",

            "fecha_actualizacion": "fecha_actualizacion TEXT",
        }

        return self.sincronizar_columnas(
            "profesionales",
            columnas,
        )
    
        # =====================================================
    # PROGRAMACIONES LEGACY
    # =====================================================

    def migrar_programaciones_legacy(self):

        if not self.existe_tabla("programaciones"):
            return []

        columnas = {

            "uuid": "uuid TEXT",

            "hora_inicio": "hora_inicio TEXT",

            "hora_fin": "hora_fin TEXT",

            "duracion":
                "duracion INTEGER DEFAULT 60",

            "prioridad":
                "prioridad TEXT DEFAULT 'MEDIA'",

            "direccion": "direccion TEXT",

            "barrio": "barrio TEXT",

            "municipio": "municipio TEXT",

            "departamento": "departamento TEXT",

            "latitud": "latitud REAL",

            "longitud": "longitud REAL",

            "usuario_creacion":
                "usuario_creacion INTEGER",

            "usuario_actualizacion":
                "usuario_actualizacion INTEGER",

            "fecha_actualizacion":
                "fecha_actualizacion TEXT",
        }

        return self.sincronizar_columnas(
            "programaciones",
            columnas,
        )
    
        # =====================================================
    # MIGRACIÓN INCREMENTAL
    # =====================================================

    def migracion_incremental(self):

        cambios = []

        cambios.extend(
            self.migrar_pacientes_legacy()
        )

        cambios.extend(
            self.migrar_pacientes_866()
        )

        cambios.extend(
            self.migrar_interoperabilidad_866()
        )

        cambios.extend(
            self.migrar_programaciones_completar()
        )

        cambios.extend(
            self.migrar_profesionales_legacy()
        )

        cambios.extend(
            self.migrar_profesionales_completar()
        )

        cambios.extend(
            self.migrar_programaciones_legacy()
        )

        cambios.extend(
            self.migrar_nomina()
        )

        cambios.extend(
            self.migrar_administracion_medicamentos_nullable()
        )

        cambios.extend(
            self.migrar_usuarios()
        )

        cambios.extend(
            self.migrar_catalogo_turnos()
        )

        cambios.extend(
            self.migrar_laboratorios_resultados()
        )

        cambios.extend(
            self.migrar_laboratorio_items()
        )

        cambios.extend(
            self.migrar_divipola_codigo_postal()
        )

        cambios.extend(
            self.migrar_documentos_profesional_archivo()
        )

        cambios.extend(
            self.migrar_facturacion_servicios()
        )

        cambios.extend(
            self.migrar_cartera_facturacion()
        )

        cambios.extend(
            self.migrar_bloqueo_login()
        )

        cambios.extend(
            self.migrar_roles_permisos()
        )

        cambios.extend(
            self.migrar_flujo_chatbot()
        )

        cambios.extend(
            self.migrar_whatsapp_hilos()
        )

        cambios.extend(
            self.migrar_perfil_asistencial()
        )

        cambios.extend(
            self.migrar_chatbot_whatsapp()
        )

        cambios.extend(
            self.migrar_configuracion_legal()
        )

        cambios.extend(
            self.migrar_reconocimiento_facial()
        )

        cambios.extend(
            self.migrar_catalogo_examenes_laboratorio()
        )

        cambios.extend(
            self.migrar_firma_contratos()
        )

        cambios.extend(
            self.migrar_examen_fisico_recomendaciones()
        )

        cambios.extend(
            self.migrar_calidad()
        )

        cambios.extend(
            self.migrar_geolocalizacion_pacientes()
        )

        cambios.extend(
            self.migrar_verificacion_geocerca()
        )

        cambios.extend(
            self.migrar_actividades_programa()
        )

        cambios.extend(
            self.migrar_acudientes()
        )

        cambios.extend(
            self.migrar_plantillas_visita_rol()
        )

        cambios.extend(
            self.migrar_firma_y_consecutivos()
        )

        cambios.extend(
            self.migrar_fotos_procedimientos()
        )

        cambios.extend(
            self.migrar_consentimientos()
        )

        cambios.extend(
            self.migrar_diagnosticos_cups()
        )

        cambios.extend(
            self.migrar_cie10_normalizado()
        )

        return cambios
    
        # =====================================================
    # VALIDAR ESQUEMA
    # =====================================================

    def validar_esquema(self):

        resultado = {

            "tablas_existentes": [],

            "tablas_faltantes": [],

            "total": 0,

        }

        tablas = set(self.listar_tablas())

        requeridas = {

            "usuarios",

            "pacientes",

            "profesionales",

            "programaciones",

            "despachos",

            "asignaciones",

        }

        resultado["total"] = len(requeridas)

        for tabla in sorted(requeridas):

            if tabla in tablas:

                resultado["tablas_existentes"].append(tabla)

            else:

                resultado["tablas_faltantes"].append(tabla)

        return resultado
    
        # =====================================================
    # ESTADÍSTICAS
    # =====================================================

    def estadisticas(self):

        return {

            "version": self.version_actual(),

            "tablas": self.total_tablas(),

            "indices": len(INDEXES),

            "requiere_migracion":

                self.necesita_migracion(),

        }
    
        # =====================================================
    # REPORTE
    # =====================================================

    def reporte(self):

        return {

            "schema":

                self.validar_esquema(),

            "estadisticas":

                self.estadisticas(),

        }
    
        # =====================================================
    # VERIFICAR
    # =====================================================

    def verificar(self):

        datos = self.reporte()

        print()

        print("=" * 60)

        print("HOMECARE ENTERPRISE")

        print("VALIDADOR DE MIGRACIONES")

        print("=" * 60)

        print()

        print(

            "Versión:",

            datos["estadisticas"]["version"]

        )

        print(

            "Tablas:",

            datos["estadisticas"]["tablas"]

        )

        print(

            "Faltantes:",

            len(

                datos["schema"]["tablas_faltantes"]

            )

        )

        print()

        return datos
    
        # =====================================================
    # MIGRACIÓN COMPLETA
    # =====================================================

    def migrar(self):

        self.conectar()

        try:

            self.crear_tabla_versiones()

            tablas = self.crear_tablas()

            cambios = self.migracion_incremental()

            indices = self.crear_indices()

            if self.necesita_migracion():

                self.registrar_version(

                    SCHEMA_VERSION,

                    "Migración automática",

                )

            return {

                "ok": True,

                "tablas": tablas,

                "cambios": cambios,

                "indices": indices,

                "validacion":

                    self.validar_esquema(),

            }

        except Exception as ex:

            if self.connection:

                self.connection.rollback()

            return {

                "ok": False,

                "error": str(ex),

            }

        finally:

            self.cerrar()

        # =====================================================
    # REINICIALIZAR BASE (SOLO DESARROLLO)
    # =====================================================

    def reinicializar(self):

        self.conectar()

        self.cursor.execute(
            """
            SELECT name

            FROM sqlite_master

            WHERE type='table'
            """
        )

        tablas = self.cursor.fetchall()

        for tabla in tablas:

            nombre = tabla["name"]

            if nombre.startswith("sqlite"):
                continue

            self.cursor.execute(
                f"DROP TABLE IF EXISTS {nombre}"
            )

        self.connection.commit()

        self.cerrar()

        return True
    
        # =====================================================
    # INFORMACIÓN
    # =====================================================

    def info(self):

        return {

            "version":

                self.version_actual(),

            "tablas":

                self.total_tablas(),

            "indices":

                len(INDEXES),

            "estado":

                self.validar_esquema(),

        }

   # ==========================================================
# FACTORY
# ==========================================================

migration_manager = MigrationManager()


# ==========================================================
# API PÚBLICA
# ==========================================================

def ejecutar_migraciones():
    """
    Ejecuta todas las migraciones pendientes.
    """
    return migration_manager.migrar()


def migrate():
    """
    Alias de compatibilidad.
    """
    return ejecutar_migraciones()


def verify():
    """
    Verifica el estado del esquema.
    """
    return migration_manager.verificar()


def info():
    """
    Información general.
    """
    return migration_manager.info()


def reset_database():
    """
    Reinicia completamente la base de datos.
    Solo para desarrollo.
    """
    return migration_manager.reinicializar()