"""
HomeCare Enterprise - Capa de compatibilidad SQLite / PostgreSQL

Todo el sistema (573 llamadas, en 134 archivos) pasa por las
funciones centrales de database.py (ejecutar, consultar_todos,
consultar_uno, consultar_escalar) -- gracias a eso, para poder
usar PostgreSQL en producción (y seguir usando SQLite para
desarrollo local) NO hace falta tocar esos 134 archivos, solo
esta capa.

Cómo se elige el motor:
  - Si existe la variable de entorno DATABASE_URL y empieza
    con "postgres://" o "postgresql://" (que es justo lo que
    Render pone automáticamente al conectar una base de datos
    PostgreSQL administrada), se usa PostgreSQL.
  - Si no, se sigue usando SQLite exactamente igual que antes
    (nada cambia para quien esté probando en su computador).

Diferencias que esta capa resuelve de forma transparente:
  1. Los signos de interrogación "?" de los parámetros
     (estándar de SQLite) se traducen a "%s" (estándar de
     PostgreSQL) automáticamente.
  2. El id que genera un INSERT ("lastrowid" en SQLite) se
     obtiene agregando "RETURNING id" a la sentencia cuando se
     usa PostgreSQL.
  3. Las filas se pueden seguir usando como diccionario
     (fila["campo"] o dict(fila)) en ambos motores.
"""

import os
import re

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

# Render (y otros proveedores) a veces entregan la URL como
# "postgres://" -- psycopg2 exige que empiece con "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

ES_POSTGRES = DATABASE_URL.startswith("postgresql://")


def _traducir_placeholders(sql: str) -> str:
    """Convierte los "?" de los parámetros a "%s" -- solo los que son parámetros reales, no los que aparecen dentro de un texto literal ('...')."""
    resultado = []
    dentro_de_texto = False
    for caracter in sql:
        if caracter == "'":
            dentro_de_texto = not dentro_de_texto
        if caracter == "?" and not dentro_de_texto:
            resultado.append("%s")
        else:
            resultado.append(caracter)
    return "".join(resultado)


def _es_insert(sql: str) -> bool:
    return sql.strip().upper().startswith("INSERT")


def _tiene_returning(sql: str) -> bool:
    return "RETURNING" in sql.upper()


def _traducir_funciones_sql(sql: str) -> str:
    """
    Algunas funciones tienen el mismo uso (mismos argumentos,
    en el mismo orden) pero un nombre distinto entre SQLite y
    PostgreSQL -- se traducen aquí para no tener que buscar
    cada consulta suelta que las use.
    """
    sql = re.sub(r"\bGROUP_CONCAT\s*\(", "STRING_AGG(", sql, flags=re.IGNORECASE)
    return sql


def _traducir_funciones_fecha(sql: str) -> str:
    """
    Traduce las formas de manejar fechas "hoy" +/- un intervalo
    que usa SQLite a su equivalente en PostgreSQL -- son de las
    pocas diferencias reales de sintaxis entre los dos motores.

        SQLite                          PostgreSQL
        date('now')                  -> CURRENT_DATE
        datetime('now')              -> CURRENT_TIMESTAMP
        date('now', ?)               -> (CURRENT_DATE + (?)::interval)
        datetime('now', ?)           -> (CURRENT_TIMESTAMP + (?)::interval)
        date('now', '-30 days')      -> (CURRENT_DATE + INTERVAL '-30 days')
        julianday('now')-julianday(X)-> (CURRENT_DATE - (X)::date)

    (Los modificadores tipo "-30 days" que usa SQLite son
    válidos también como texto de un INTERVAL de PostgreSQL,
    así que no hace falta reinterpretarlos, solo reacomodar la
    sintaxis alrededor.)
    """
    # date('now', ?) / datetime('now', ?) -- con un parametro (placeholder) como modificador
    sql = re.sub(r"date\(\s*'now'\s*,\s*\?\s*\)", "(CURRENT_DATE + (?)::interval)", sql, flags=re.IGNORECASE)
    sql = re.sub(r"datetime\(\s*'now'\s*,\s*\?\s*\)", "(CURRENT_TIMESTAMP + (?)::interval)", sql, flags=re.IGNORECASE)

    # date('now', '+' || ? || ' days') -- modificador armado por concatenacion (typico para "en N dias")
    sql = re.sub(
        r"date\(\s*'now'\s*,\s*'\+'\s*\|\|\s*\?\s*\|\|\s*'\s*days'\s*\)",
        "(CURRENT_DATE + ((?) || ' days')::interval)",
        sql, flags=re.IGNORECASE,
    )

    # date('now', 'texto literal') / datetime('now', 'texto literal') -- con el modificador ya escrito en la consulta
    sql = re.sub(r"date\(\s*'now'\s*,\s*'([^']*)'\s*\)", r"(CURRENT_DATE + INTERVAL '\1')", sql, flags=re.IGNORECASE)
    sql = re.sub(r"datetime\(\s*'now'\s*,\s*'([^']*)'\s*\)", r"(CURRENT_TIMESTAMP + INTERVAL '\1')", sql, flags=re.IGNORECASE)

    # date('now') / datetime('now') sueltos, sin modificador
    sql = re.sub(r"date\(\s*'now'\s*\)", "CURRENT_DATE", sql, flags=re.IGNORECASE)
    sql = re.sub(r"datetime\(\s*'now'\s*\)", "CURRENT_TIMESTAMP", sql, flags=re.IGNORECASE)

    # julianday('now') - julianday(X)  ->  diferencia de dias directa entre fechas
    sql = re.sub(
        r"julianday\(\s*'now'\s*\)\s*-\s*julianday\(([^)]+)\)",
        r"(CURRENT_DATE - (\1)::date)",
        sql, flags=re.IGNORECASE,
    )
    sql = re.sub(
        r"julianday\(([^)]+)\)\s*-\s*julianday\(\s*'now'\s*\)",
        r"((\1)::date - CURRENT_DATE)",
        sql, flags=re.IGNORECASE,
    )

    # date(columna) / datetime(columna) -- convertir una columna de texto a fecha, sigue funcionando
    # igual en PostgreSQL siempre que la columna ya sea un texto con formato de fecha (::date funciona parecido),
    # pero "date(x)" y "datetime(x)" NO son funciones válidas en PostgreSQL -- se cambian por el cast "::date"/"::timestamp".
    sql = re.sub(r"\bdate\(([a-zA-Z_][\w\.]*)\)", r"(\1)::date", sql)
    sql = re.sub(r"\bdatetime\(([a-zA-Z_][\w\.]*)\)", r"(\1)::timestamp", sql)

    return sql


def _traducir_insert_or_ignore(sql: str) -> str:
    """
    "INSERT OR IGNORE INTO ..." (sintaxis de SQLite) se traduce
    a la forma de PostgreSQL: "INSERT INTO ... ON CONFLICT DO
    NOTHING" -- sin indicar una columna en particular, así
    aplica a cualquier restricción única que choque, igual que
    hacía el original.
    """
    if re.match(r"^\s*INSERT\s+OR\s+IGNORE\s+INTO", sql, re.IGNORECASE):
        sql = re.sub(r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO", sql, count=1, flags=re.IGNORECASE)
        sql = sql.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
    return sql


class CursorCompatible:
    """
    Envuelve el cursor real (de sqlite3 o de psycopg2) para que
    todo el resto del sistema lo pueda seguir usando exactamente
    igual que hasta ahora: cursor.execute(sql, parametros),
    cursor.fetchone(), cursor.fetchall(), cursor.lastrowid.
    """

    def __init__(self, cursor_real):
        self._cursor = cursor_real
        self._lastrowid = None

    def execute(self, sql, parametros=()):
        if ES_POSTGRES:
            sql_traducido = _traducir_funciones_fecha(sql)
            sql_traducido = _traducir_placeholders(sql_traducido)
            sql_traducido = _traducir_insert_or_ignore(sql_traducido)
            sql_traducido = _traducir_funciones_sql(sql_traducido)
            if _es_insert(sql_traducido) and not _tiene_returning(sql_traducido):
                sql_traducido = sql_traducido.rstrip().rstrip(";") + " RETURNING id"
                self._cursor.execute(sql_traducido, parametros)
                fila = self._cursor.fetchone()
                self._lastrowid = fila["id"] if fila else None
            else:
                self._cursor.execute(sql_traducido, parametros)
        else:
            self._cursor.execute(sql, parametros)
            self._lastrowid = self._cursor.lastrowid
        return self

    def executescript(self, sql: str):
        """SQLite sí soporta varias sentencias separadas por ';' en una sola llamada -- PostgreSQL (via psycopg2) también las ejecuta todas si van en el mismo execute(), así que basta con traducir los placeholders (por si el script trae alguno) y mandarlo tal cual."""
        if ES_POSTGRES:
            self._cursor.execute(_traducir_placeholders(sql))
        else:
            self._cursor.executescript(sql)
        return self

    def executemany(self, sql, datos):
        sql_final = _traducir_placeholders(sql) if ES_POSTGRES else sql
        self._cursor.executemany(sql_final, datos)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def lastrowid(self):
        return self._lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()


class ConnectionCompatible:
    """Envuelve la conexión real para que cursor(), commit(), rollback() y close() sigan funcionando exactamente igual, sin importar el motor."""

    def __init__(self, conexion_real):
        self._conexion = conexion_real

    def cursor(self):
        return CursorCompatible(self._conexion.cursor())

    def execute(self, sql, parametros=()):
        return self.cursor().execute(sql, parametros)

    def executescript(self, sql: str):
        return self.cursor().executescript(sql)

    def commit(self):
        self._conexion.commit()

    def rollback(self):
        self._conexion.rollback()

    def close(self):
        self._conexion.close()

    def __enter__(self):
        return self

    def __exit__(self, tipo, valor, traceback):
        # Se confirma (commit) igual que hacía la conexión nativa
        # de sqlite3 al usarse como "with ... as cn:", pero
        # ADEMÁS se cierra la conexión siempre -- en SQLite no
        # cerrarla no duele mucho (son archivos livianos), pero
        # en PostgreSQL cada conexión cuenta contra un límite
        # real del servidor, así que hay que devolverla siempre.
        try:
            if tipo is None:
                self._conexion.commit()
            else:
                self._conexion.rollback()
        finally:
            self._conexion.close()


def conectar_postgres():
    import psycopg2
    import psycopg2.extras

    conexion = psycopg2.connect(DATABASE_URL, sslmode="require")
    conexion.cursor_factory = psycopg2.extras.RealDictCursor
    conexion_original = conexion.cursor

    def cursor_con_diccionario(*args, **kwargs):
        kwargs.setdefault("cursor_factory", psycopg2.extras.RealDictCursor)
        return conexion_original(*args, **kwargs)

    conexion.cursor = cursor_con_diccionario
    return conexion


def traducir_sql_a_postgres(sql: str) -> str:
    """
    Convierte una sentencia CREATE TABLE (u otra) escrita en la
    sintaxis de SQLite a una compatible con PostgreSQL. Se usa
    UNA sola fuente del esquema (database/schema.py, tal como
    ya existía) y se traduce en el momento de crear las tablas
    -- así no hay dos esquemas por separado que se puedan
    desincronizar con el tiempo.
    """
    resultado = sql

    # "INTEGER PRIMARY KEY AUTOINCREMENT" (SQLite) -> "SERIAL PRIMARY KEY" (PostgreSQL)
    resultado = re.sub(
        r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT",
        "SERIAL PRIMARY KEY",
        resultado,
        flags=re.IGNORECASE,
    )

    # "AUTOINCREMENT" suelto que haya quedado (sin el patrón completo de arriba)
    resultado = re.sub(r"\s+AUTOINCREMENT", "", resultado, flags=re.IGNORECASE)

    # BLOB (SQLite) -> BYTEA (PostgreSQL)
    resultado = re.sub(r"\bBLOB\b", "BYTEA", resultado, flags=re.IGNORECASE)

    # "CREATE TABLE IF NOT EXISTS" y "CREATE INDEX IF NOT EXISTS" son válidos en ambos -- no hace falta tocarlos.

    return resultado
