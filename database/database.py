"""
=========================================================
HomeCare IPS Enterprise
Archivo: database/database.py
Versión: 7.1.0
=========================================================
"""

import sqlite3
import shutil

from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

from database.schema import SCHEMA
from database.indexes import INDEXES


DB_PATH = Path("database.db")


# =====================================================
# CONEXIÓN
# =====================================================

def get_connection() -> sqlite3.Connection:

    conexion = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
        timeout=30,
    )

    conexion.row_factory = sqlite3.Row

    cursor = conexion.cursor()

    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA temp_store=MEMORY;")
    cursor.execute("PRAGMA cache_size=-64000;")

    return conexion


# =====================================================
# TRANSACCIONES
# =====================================================

@contextmanager
def transaction():

    conexion = get_connection()

    try:

        yield conexion

        conexion.commit()

    except Exception:

        conexion.rollback()

        raise

    finally:

        conexion.close()


# =====================================================
# EJECUTAR
# =====================================================

def ejecutar(sql: str, parametros=()):

    with transaction() as cn:

        cur = cn.cursor()

        cur.execute(sql, parametros)

        return cur.lastrowid


# =====================================================
# EJECUTAR MUCHOS
# =====================================================

def ejecutarmany(sql: str, datos):

    with transaction() as cn:

        cur = cn.cursor()

        cur.executemany(sql, datos)

# =====================================================
# COMPATIBILIDAD CON VERSIONES ANTERIORES
# =====================================================

def consultar(sql: str, parametros=()):
    """
    Alias para mantener compatibilidad con los
    repositorios desarrollados antes del Sprint 3.4A.
    """
    return consultar_todos(sql, parametros)

# =====================================================
# CONSULTAR TODOS
# =====================================================

def consultar_todos(sql: str, parametros=()):

    with get_connection() as cn:

        cur = cn.cursor()

        cur.execute(sql, parametros)

        return cur.fetchall()


# =====================================================
# CONSULTAR UNO
# =====================================================

def consultar_uno(sql: str, parametros=()):

    with get_connection() as cn:

        cur = cn.cursor()

        cur.execute(sql, parametros)

        return cur.fetchone()


# =====================================================
# CONSULTAR ESCALAR
# =====================================================

def consultar_escalar(sql: str, parametros=()):

    fila = consultar_uno(sql, parametros)

    if fila is None:

        return None

    return fila[0]


# =====================================================
# LISTAR TABLAS
# =====================================================

def listar_tablas():

    filas = consultar_todos("""

        SELECT name

        FROM sqlite_master

        WHERE type='table'

        ORDER BY name

    """)

    return [fila["name"] for fila in filas]


# =====================================================
# EXISTE TABLA
# =====================================================

def existe_tabla(nombre):

    return nombre in listar_tablas()


# =====================================================
# CREAR TABLAS
# =====================================================

def crear_tablas():

    with transaction() as cn:

        cur = cn.cursor()

        # ================================
        # TABLAS
        # ================================

        for sql in SCHEMA:

            cur.executescript(sql)

        # ================================
        # ÍNDICES
        # ================================

        for sql in INDEXES:

            cur.executescript(sql)

    print()

    print("=" * 55)

    print("HomeCare Enterprise Database")

    print("=" * 55)

    for tabla in listar_tablas():

        print("[OK]", tabla)

    print("=" * 55)

    print()


# =====================================================
# VACUUM
# =====================================================

def vacuum():

    with get_connection() as cn:

        cn.execute("VACUUM")


# =====================================================
# OPTIMIZE
# =====================================================

def optimize():

    with get_connection() as cn:

        cn.execute("PRAGMA optimize;")


# =====================================================
# INTEGRIDAD
# =====================================================

def verificar_integridad():

    fila = consultar_uno(

        "PRAGMA integrity_check"

    )

    return fila[0] == "ok"


# =====================================================
# BACKUP
# =====================================================

def backup():

    carpeta = Path("backups")

    carpeta.mkdir(exist_ok=True)

    nombre = datetime.now().strftime(

        "database_%Y%m%d_%H%M%S.db"

    )

    destino = carpeta / nombre

    shutil.copy2(DB_PATH, destino)

    return destino


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":

    crear_tablas()

    print("Integridad:", verificar_integridad())