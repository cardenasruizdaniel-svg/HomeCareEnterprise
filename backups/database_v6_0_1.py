import sqlite3

from models.usuario import TABLA_USUARIOS
from models.paciente import TABLA_PACIENTES
from models.acudiente import TABLA_ACUDIENTES
from models.diagnostico import TABLA_DIAGNOSTICOS
from models.cie10 import TABLA_CIE10
from models.programacion import TABLA_PROGRAMACIONES
from models.antecedentes import TABLA_ANTECEDENTES
from models.alergias import TABLA_ALERGIAS
from models.medicamento import TABLA_MEDICAMENTOS
from models.administracion_medicamento import TABLA_ADMINISTRACION_MEDICAMENTOS
from models.signos_vitales import TABLA_SIGNOS_VITALES


from core.config import DATABASE_FILE


def get_connection():
    """
    Crea una conexión optimizada con SQLite.
    """

    conexion = sqlite3.connect(

        DATABASE_FILE,

        timeout=30,

        check_same_thread=False

    )

    conexion.execute("PRAGMA foreign_keys = ON")

    conexion.execute("PRAGMA journal_mode = WAL")

    conexion.execute("PRAGMA synchronous = NORMAL")

    conexion.execute("PRAGMA temp_store = MEMORY")

    conexion.execute("PRAGMA cache_size = -20000")

    conexion.row_factory = sqlite3.Row

    return conexion


def crear_tablas():

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute(TABLA_USUARIOS)

    cursor.execute(TABLA_PACIENTES)

    cursor.execute(TABLA_ACUDIENTES)

    cursor.execute(TABLA_DIAGNOSTICOS)

    cursor.execute(TABLA_CIE10)

    cursor.execute(TABLA_PROGRAMACIONES)

    cursor.execute(TABLA_ALERGIAS)

    cursor.execute(TABLA_ANTECEDENTES)

    cursor.execute(TABLA_MEDICAMENTOS)

    cursor.execute(TABLA_ADMINISTRACION_MEDICAMENTOS)

    cursor.execute(TABLA_SIGNOS_VITALES)

    conexion.commit()

    conexion.close()