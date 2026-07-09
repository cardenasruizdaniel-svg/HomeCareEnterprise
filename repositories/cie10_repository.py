from core.texto_utils import normalizar
from database.database import get_connection


# ==========================================
# BUSCAR POR CÓDIGO O DESCRIPCIÓN
# ==========================================

def buscar(busqueda: str):

    conexion = get_connection()
    cursor = conexion.cursor()

    texto_normalizado = normalizar(busqueda)

    cursor.execute("""

        SELECT
            codigo,
            descripcion,
            categoria,
            capitulo

        FROM cie10

        WHERE activo = 1

        AND (

            codigo LIKE ?

            OR descripcion_normalizada LIKE ?

        )

        ORDER BY codigo

        LIMIT 50

    """, (

        f"%{busqueda}%",

        f"%{texto_normalizado}%"

    ))

    datos = cursor.fetchall()

    conexion.close()

    return datos


# ==========================================
# BUSCAR POR CÓDIGO EXACTO
# ==========================================

def obtener_por_codigo(codigo):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM cie10

        WHERE codigo = ?

        LIMIT 1

    """, (codigo,))

    dato = cursor.fetchone()

    conexion.close()

    return dato


# ==========================================
# INSERTAR REGISTRO
# ==========================================

def insertar(

    codigo,

    descripcion,

    categoria,

    capitulo

):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        INSERT INTO cie10(

            codigo,

            descripcion,

            categoria,

            capitulo

        )

        VALUES(

            ?,?,?,?

        )

    """, (

        codigo,

        descripcion,

        categoria,

        capitulo

    ))

    conexion.commit()

    conexion.close()


# ==========================================
# CONTAR REGISTROS
# ==========================================

def total_registros():

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT COUNT(*)

        FROM cie10

    """)

    total = cursor.fetchone()[0]

    conexion.close()

    return total


# ==========================================
# ELIMINAR TODO
# ==========================================

def eliminar_todo():

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""

        DELETE FROM cie10

    """)

    conexion.commit()

    conexion.close()

# ==========================================
# SIEMBRA INICIAL (lote ilustrativo) E
# IMPORTACIÓN MASIVA DESDE CSV OFICIAL
# ==========================================

def total_activos():
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM cie10")
    total = cursor.fetchone()[0]
    conexion.close()
    return total


def sembrar_si_vacio():
    if total_activos() > 0:
        return 0

    from database.catalogos.cie10_data import CIE10_DOMICILIARIO

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.executemany(
        "INSERT OR IGNORE INTO cie10(codigo, descripcion, descripcion_normalizada, categoria, capitulo) VALUES (?, ?, ?, ?, ?)",
        [
            (codigo, descripcion, normalizar(descripcion), capitulo, capitulo)
            for codigo, descripcion, capitulo in CIE10_DOMICILIARIO
        ],
    )
    conexion.commit()
    conexion.close()
    return len(CIE10_DOMICILIARIO)


def importar_csv(contenido: str) -> int:
    """
    Carga masiva desde un CSV con columnas:
    codigo,descripcion,capitulo
    (tal como se puede exportar del archivo oficial CIE-10 que
    publica el Ministerio de Salud / SISPRO).
    """

    import csv
    import io

    lector = csv.DictReader(io.StringIO(contenido))
    filas = [
        (
            fila["codigo"].strip(),
            fila["descripcion"].strip(),
            normalizar(fila["descripcion"]),
            fila.get("capitulo", "").strip(),
            fila.get("capitulo", "").strip(),
        )
        for fila in lector
        if fila.get("codigo")
    ]

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.executemany(
        "INSERT OR REPLACE INTO cie10(codigo, descripcion, descripcion_normalizada, categoria, capitulo) VALUES (?, ?, ?, ?, ?)",
        filas,
    )
    conexion.commit()
    conexion.close()
    return len(filas)
