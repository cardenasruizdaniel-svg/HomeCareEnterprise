"""
=========================================================
HomeCare Enterprise
Database Seed
Versión 10.1
=========================================================
"""

from database.database import get_connection

def ejecutar_sql(sql, parametros=None):

    conn = get_connection()

    cursor = conn.cursor()

    if parametros:

        cursor.execute(sql, parametros)

    else:

        cursor.execute(sql)

    conn.commit()

    conn.close()

# =====================================================
# EJECUTAR MUCHOS
# =====================================================

def ejecutar_many(sql, datos):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.executemany(

        sql,

        datos

    )

    conn.commit()

    conn.close()
    

def imprimir(titulo):

    print()

    print("=" * 60)

    print(titulo)

    print("=" * 60)

# =====================================================
# COMPONENTES DEL DISEÑADOR
# =====================================================

def seed_componentes():

    imprimir("Cargando Componentes del Diseñador")

    componentes = [

        # =================================================
        # BÁSICOS
        # =================================================

        (
            "texto",
            "Texto",
            "bi-input-cursor-text",
            "Básicos",
            "Campo de texto de una línea",
            "TEXT",
            "input",
            1,1,0,0,0,0,1
        ),

        (
            "textarea",
            "Área de texto",
            "bi-textarea-t",
            "Básicos",
            "Campo de varias líneas",
            "TEXT",
            "textarea",
            1,1,0,0,0,0,1
        ),

        (
            "numero",
            "Número",
            "bi-123",
            "Básicos",
            "Número entero",
            "INTEGER",
            "input",
            0,0,0,0,0,0,1
        ),

        (
            "decimal",
            "Número Decimal",
            "bi-calculator",
            "Básicos",
            "Número decimal",
            "REAL",
            "input",
            0,0,0,0,0,0,1
        ),

        (
            "correo",
            "Correo",
            "bi-envelope",
            "Básicos",
            "Correo electrónico",
            "TEXT",
            "input",
            0,0,0,0,0,0,1
        ),

        (
            "telefono",
            "Teléfono",
            "bi-telephone",
            "Básicos",
            "Número telefónico",
            "TEXT",
            "input",
            0,0,0,0,0,0,1
        ),

        (
            "fecha",
            "Fecha",
            "bi-calendar-date",
            "Fecha",
            "Campo fecha",
            "DATE",
            "input",
            0,0,0,0,0,0,1
        ),

        (
            "hora",
            "Hora",
            "bi-clock",
            "Fecha",
            "Campo hora",
            "TIME",
            "input",
            0,0,0,0,0,0,1
        ),

                (
            "checkbox",
            "Casilla de verificación",
            "bi-check-square",
            "Selección",
            "Permite seleccionar Sí/No",
            "BOOLEAN",
            "checkbox",
            0,0,0,0,0,0,1
        ),

        (
            "radio",
            "Opción única",
            "bi-ui-radios",
            "Selección",
            "Grupo de opciones",
            "TEXT",
            "radio",
            0,0,0,0,0,0,1
        ),

        (
            "select",
            "Lista desplegable",
            "bi-menu-button",
            "Selección",
            "Lista de opciones",
            "TEXT",
            "select",
            0,0,0,0,0,0,1
        ),

        (
            "multiselect",
            "Selección múltiple",
            "bi-list-check",
            "Selección",
            "Permite múltiples opciones",
            "TEXT",
            "multiselect",
            0,0,0,0,0,0,1
        ),

        (
            "switch",
            "Interruptor",
            "bi-toggle-on",
            "Selección",
            "Interruptor ON/OFF",
            "BOOLEAN",
            "switch",
            0,0,0,0,0,0,1
        ),

    ]

    sql = """

    INSERT OR IGNORE INTO plantilla_componentes(

        codigo,

        nombre,

        icono,

        categoria,

        descripcion,

        tipo_dato,

        componente_html,

        permite_ia,

        permite_dictado,

        permite_firma,

        permite_fotografia,

        permite_adjuntos,

        permite_geolocalizacion,

        activo

    )

    VALUES(

        ?,?,?,?,?,?,?,?,?,?,?,?,?,?

    )

    """

    ejecutar_many(sql, componentes)

    print(f"[OK] {len(componentes)} componentes registrados")

# =====================================================
# EJECUTAR SEED
# =====================================================

def ejecutar_seed():

    imprimir("HOMECARE ENTERPRISE")

    seed_componentes()

    print()

    print("Seed finalizado correctamente.")


if __name__ == "__main__":

    ejecutar_seed()