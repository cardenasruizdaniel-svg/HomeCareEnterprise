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
from database.db_backend import (
    DATABASE_URL,
    ES_POSTGRES,
    ConnectionCompatible,
    conectar_postgres,
    traducir_sql_a_postgres,
)

# Antes esto era Path("database.db") -- una ruta RELATIVA a la
# carpeta desde donde se arranca el programa. En Render eso
# funciona porque siempre arranca desde la misma carpeta, pero
# en un ejecutable de Windows la carpeta "actual" al hacer
# doble clic no es confiable, así que la base de datos se
# guarda en la carpeta de datos persistente de la aplicación
# (BASE_DIR ya sabe distinguir si está empaquetada como .exe
# o no, y elegir la carpeta correcta en cada caso).
try:
    from core.config import BASE_DIR
    DB_PATH = BASE_DIR / "database.db"
except ImportError:
    DB_PATH = Path("database.db")


# =====================================================
# CONEXIÓN
#
# Si existe la variable de entorno DATABASE_URL con una URL de
# PostgreSQL (como la que entrega Render al conectar una base
# de datos administrada), se usa esa. Si no, se sigue usando
# SQLite exactamente igual que siempre -- así, quien esté
# desarrollando o probando en su computador no necesita
# instalar ni configurar nada distinto.
# =====================================================

def get_connection():

    if ES_POSTGRES:
        return ConnectionCompatible(conectar_postgres())

    try:
        conexion = _conectar_sqlite(DB_PATH)
    except sqlite3.DatabaseError as error:

        # "database disk image is malformed" y errores similares
        # significan que el archivo se corrompió (por ejemplo,
        # tras un corte de luz, un cierre forzado del programa,
        # o un antivirus interfiriendo mientras escribía). En vez
        # de que el sistema completo se caiga sin poder arrancar
        # nunca más, se guarda el archivo dañado a un lado (por
        # si alguien necesita intentar recuperarlo después) y se
        # empieza con una base de datos nueva y limpia -- el
        # arranque normal del sistema se encarga de recrear las
        # tablas y los datos base (usuario administrador,
        # catálogos, etc.) en el archivo nuevo.

        mensaje_error = str(error).lower()
        es_corrupcion = any(pista in mensaje_error for pista in (
            "malformed", "corrupt", "not a database", "file is encrypted",
        ))

        if not es_corrupcion:
            raise

        print(f"[AVISO] La base de datos parece estar dañada ({error}). Se va a reparar automáticamente...")

        if DB_PATH.exists():
            respaldo_dañado = DB_PATH.with_name(f"database_DAÑADA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")

            # En Windows, si quedó otro proceso con el archivo
            # abierto (por ejemplo, una ventana anterior del
            # programa que no se cerró del todo), moverlo falla
            # con "PermissionError" aunque el archivo sí exista.
            # Se reintenta varias veces, esperando cada vez un
            # poco más entre intento e intento (empieza en 2
            # segundos, hasta llegar a 10) -- un antivirus
            # escaneando el archivo justo en ese momento puede
            # tardar bastante más que unos pocos segundos en
            # soltarlo.
            import time

            total_intentos = 15
            for intento in range(1, total_intentos + 1):
                try:
                    shutil.move(str(DB_PATH), str(respaldo_dañado))
                    print(f"[AVISO] El archivo dañado se guardó como: {respaldo_dañado.name}")
                    break
                except PermissionError:
                    if intento == total_intentos:
                        raise RuntimeError(
                            "No se pudo reparar la base de datos automáticamente porque el archivo "
                            f"'{DB_PATH}' está siendo usado por otro proceso. "
                            "Cierre TODAS las ventanas de PowerShell/CMD que hayan corrido este programa "
                            "antes (revise también el Administrador de Tareas por si quedó algún "
                            "proceso 'python.exe' abierto y termínelo -- y de paso revise que su "
                            "antivirus no esté escaneando la carpeta del programa justo en este momento), "
                            "y vuelva a intentarlo. Si el problema persiste, puede borrar manualmente el "
                            f"archivo '{DB_PATH.name}' y volver a arrancar el programa."
                        ) from error
                    espera = min(2 + intento, 10)
                    print(f"[AVISO] El archivo sigue en uso por otro proceso, reintentando en {espera} segundos... (intento {intento} de {total_intentos})")
                    time.sleep(espera)

        conexion = _conectar_sqlite(DB_PATH)
        print("[OK] Se creó una base de datos nueva. El sistema la va a llenar con la información base al arrancar.")

    return ConnectionCompatible(conexion)


def _conectar_sqlite(ruta):

    conexion = sqlite3.connect(
        ruta,
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

    if ES_POSTGRES:
        filas = consultar_todos("""
            SELECT tablename AS name
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
    else:
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

            sql_final = traducir_sql_a_postgres(sql) if ES_POSTGRES else sql
            cur.executescript(sql_final)

        # ================================
        # ÍNDICES
        # ================================

        for sql in INDEXES:

            sql_final = traducir_sql_a_postgres(sql) if ES_POSTGRES else sql
            cur.executescript(sql_final)

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
#
# En PostgreSQL, el VACUUM normal lo hace solo el motor
# automáticamente (autovacuum) -- no hace falta ni conviene
# forzarlo a mano seguido como sí se hacía con SQLite.
# =====================================================

def vacuum():

    if ES_POSTGRES:
        return

    with get_connection() as cn:

        cn.execute("VACUUM")


# =====================================================
# OPTIMIZE
# =====================================================

def optimize():

    if ES_POSTGRES:
        return

    with get_connection() as cn:

        cn.execute("PRAGMA optimize;")


# =====================================================
# INTEGRIDAD
# =====================================================

def verificar_integridad():

    if ES_POSTGRES:
        # PostgreSQL garantiza la integridad de la base con sus
        # propias verificaciones internas (WAL + checksums) --
        # aquí simplemente se confirma que se puede consultar
        # con normalidad.
        try:
            consultar_uno("SELECT 1")
            return True
        except Exception:
            return False

    fila = consultar_uno(

        "PRAGMA integrity_check"

    )

    return fila[0] == "ok"


# =====================================================
# BACKUP
#
# En SQLite, el respaldo es copiar el archivo tal cual. En
# PostgreSQL (sobre todo el administrado por Render), los
# respaldos automáticos los maneja el proveedor -- aun así,
# aquí se deja lista la generación de un volcado (dump) con
# pg_dump para tener una copia adicional bajo control propio.
# =====================================================

def backup():

    carpeta = Path("backups")

    carpeta.mkdir(exist_ok=True)

    if ES_POSTGRES:
        import subprocess

        nombre = datetime.now().strftime("database_%Y%m%d_%H%M%S.sql")
        destino = carpeta / nombre
        try:
            with open(destino, "wb") as archivo_salida:
                subprocess.run(["pg_dump", DATABASE_URL], stdout=archivo_salida, check=True)
            return destino
        except (FileNotFoundError, subprocess.CalledProcessError) as error:
            # Si "pg_dump" no está instalado en este servidor, se
            # avisa claramente en vez de fallar de forma confusa --
            # en Render, los respaldos automáticos del proveedor
            # siguen funcionando igual, esto es un respaldo adicional.
            raise RuntimeError(
                "No se pudo generar el respaldo con pg_dump en este servidor. "
                "Los respaldos automáticos de Render siguen funcionando normalmente. "
                f"Detalle: {error}"
            )

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