"""
=========================================================
HomeCare Enterprise
Repositorios de catalogos oficiales: DIVIPOLA, CUPS, CUM

Incluyen metodos de importacion masiva desde CSV para que
la IPS pueda cargar los archivos oficiales completos
(el DIVIPOLA ya viene sembrado por completo; CUPS y CUM
traen solo un lote inicial ilustrativo, ver
database/catalogos/cups_data.py y cum_data.py).

Las busquedas son insensibles a tildes/mayusculas gracias a
las columnas "*_normalizado" (ver core/texto_utils.normalizar).
=========================================================
"""

import csv
import io

from core.texto_utils import normalizar
from database.database import consultar, consultar_escalar, consultar_uno, ejecutar, ejecutarmany


def _condicion_por_palabras(columna: str, texto: str):
    """
    Construye una condicion SQL que exige que TODAS las
    palabras del texto de busqueda aparezcan (en cualquier
    orden) dentro de la columna normalizada indicada.
    Devuelve (fragmento_sql, parametros).
    """

    palabras = [p for p in normalizar(texto).split(" ") if p]

    if not palabras:
        return "1=1", []

    condiciones = [f"{columna} LIKE ?" for _ in palabras]
    parametros = [f"%{p}%" for p in palabras]

    return " AND ".join(condiciones), parametros


# ==========================================================
# DIVIPOLA
# ==========================================================

class DivipolaRepository:

    @staticmethod
    def buscar_municipios(texto: str, limite: int = 20):
        condicion, parametros = _condicion_por_palabras("nombre_normalizado", texto)
        return consultar(
            f"""
            SELECT * FROM divipola
            WHERE {condicion}
            ORDER BY nombre_departamento, nombre_municipio
            LIMIT ?
            """,
            (*parametros, limite),
        )

    @staticmethod
    def obtener_por_codigo(codigo_municipio: str):
        return consultar_uno(
            "SELECT * FROM divipola WHERE codigo_municipio=?",
            (codigo_municipio,),
        )

    @staticmethod
    def total():
        return consultar_escalar("SELECT COUNT(*) FROM divipola")

    @staticmethod
    def sembrar_si_vacio():
        if DivipolaRepository.total() > 0:
            return 0

        from database.catalogos.divipola_data import DIVIPOLA

        filas = [
            (cod_dpto, dpto, cod_mpio, nom_mpio, normalizar(f"{dpto} {nom_mpio}"))
            for cod_dpto, dpto, cod_mpio, nom_mpio in DIVIPOLA
        ]

        ejecutarmany(
            "INSERT OR IGNORE INTO divipola "
            "(codigo_departamento, nombre_departamento, codigo_municipio, "
            "nombre_municipio, nombre_normalizado) VALUES (?,?,?,?,?)",
            filas,
        )
        return len(filas)

    @staticmethod
    def listar_todos(texto: str = ""):
        if texto:
            condicion, parametros = _condicion_por_palabras("nombre_normalizado", texto)
            return consultar(
                f"SELECT * FROM divipola WHERE {condicion} ORDER BY nombre_departamento, nombre_municipio",
                tuple(parametros),
            )
        return consultar(
            "SELECT * FROM divipola ORDER BY nombre_departamento, nombre_municipio LIMIT 500"
        )

    @staticmethod
    def crear(codigo_departamento, nombre_departamento, codigo_municipio, nombre_municipio, codigo_postal=None):
        ejecutar(
            """
            INSERT INTO divipola(codigo_departamento, nombre_departamento, codigo_municipio,
                                  nombre_municipio, nombre_normalizado, codigo_postal)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (codigo_departamento, nombre_departamento, codigo_municipio, nombre_municipio,
             normalizar(f"{nombre_departamento} {nombre_municipio}"), codigo_postal or None),
        )

    @staticmethod
    def actualizar_codigo_postal(codigo_municipio: str, codigo_postal: str):
        ejecutar(
            "UPDATE divipola SET codigo_postal=? WHERE codigo_municipio=?",
            (codigo_postal or None, codigo_municipio),
        )

    @staticmethod
    def eliminar(codigo_municipio: str):
        ejecutar("DELETE FROM divipola WHERE codigo_municipio=?", (codigo_municipio,))


# ==========================================================
# CUPS
# ==========================================================

class CUPSRepository:

    @staticmethod
    def buscar(texto: str, limite: int = 20):
        condicion, parametros = _condicion_por_palabras("descripcion_normalizada", texto)
        return consultar(
            f"""
            SELECT * FROM cups
            WHERE activo=1 AND (codigo LIKE ? OR ({condicion}))
            ORDER BY descripcion
            LIMIT ?
            """,
            (f"%{texto.strip()}%", *parametros, limite),
        )

    @staticmethod
    def total():
        return consultar_escalar("SELECT COUNT(*) FROM cups")

    @staticmethod
    def sembrar_si_vacio():
        if CUPSRepository.total() > 0:
            return 0

        from database.catalogos.cups_data import CUPS_DOMICILIARIO

        filas = [
            (codigo, descripcion, normalizar(descripcion), capitulo)
            for codigo, descripcion, capitulo in CUPS_DOMICILIARIO
        ]

        ejecutarmany(
            "INSERT OR IGNORE INTO cups (codigo, descripcion, descripcion_normalizada, capitulo) "
            "VALUES (?,?,?,?)",
            filas,
        )
        return len(filas)

    @staticmethod
    def importar_csv(contenido: str) -> int:
        """
        Carga masiva desde un CSV con columnas:
        codigo,descripcion,capitulo
        (tal como se puede exportar del archivo oficial del
        Ministerio, ajustando encabezados si es necesario).
        """

        lector = csv.DictReader(io.StringIO(contenido))
        filas = [
            (
                fila["codigo"].strip(),
                fila["descripcion"].strip(),
                normalizar(fila["descripcion"]),
                fila.get("capitulo", "").strip(),
            )
            for fila in lector
            if fila.get("codigo")
        ]

        ejecutarmany(
            "INSERT OR REPLACE INTO cups (codigo, descripcion, descripcion_normalizada, capitulo) "
            "VALUES (?,?,?,?)",
            filas,
        )
        return len(filas)


# ==========================================================
# CUM
# ==========================================================

class CUMRepository:

    @staticmethod
    def buscar(texto: str, limite: int = 20):
        condicion, parametros = _condicion_por_palabras("nombre_normalizado", texto)
        return consultar(
            f"""
            SELECT * FROM cum
            WHERE activo=1 AND (codigo LIKE ? OR ({condicion}))
            ORDER BY nombre
            LIMIT ?
            """,
            (f"%{texto.strip()}%", *parametros, limite),
        )

    @staticmethod
    def total():
        return consultar_escalar("SELECT COUNT(*) FROM cum")

    @staticmethod
    def sembrar_si_vacio():
        if CUMRepository.total() > 0:
            return 0

        from database.catalogos.cum_data import CUM_FRECUENTES

        filas = [
            (codigo, nombre, normalizar(nombre), principio, concentracion, forma)
            for codigo, nombre, principio, concentracion, forma in CUM_FRECUENTES
        ]

        ejecutarmany(
            "INSERT OR IGNORE INTO cum "
            "(codigo, nombre, nombre_normalizado, principio_activo, concentracion, forma_farmaceutica) "
            "VALUES (?,?,?,?,?,?)",
            filas,
        )
        return len(filas)

    @staticmethod
    def importar_csv(contenido: str) -> int:
        """
        Carga masiva desde un CSV con columnas:
        codigo,nombre,principio_activo,concentracion,forma_farmaceutica
        (tal como se puede exportar del portal de consulta de
        registros sanitarios del INVIMA).
        """

        lector = csv.DictReader(io.StringIO(contenido))
        filas = [
            (
                fila["codigo"].strip(),
                fila["nombre"].strip(),
                normalizar(fila["nombre"]),
                fila.get("principio_activo", "").strip(),
                fila.get("concentracion", "").strip(),
                fila.get("forma_farmaceutica", "").strip(),
            )
            for fila in lector
            if fila.get("codigo")
        ]

        ejecutarmany(
            "INSERT OR REPLACE INTO cum "
            "(codigo, nombre, nombre_normalizado, principio_activo, concentracion, forma_farmaceutica) "
            "VALUES (?,?,?,?,?,?)",
            filas,
        )
        return len(filas)
