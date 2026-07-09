"""
=========================================================
HomeCare Enterprise
Seed Database
=========================================================
"""

import sqlite3
import random

from datetime import datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"

connection = sqlite3.connect(DATABASE)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

# =====================================================
# LIMPIAR TABLAS
# =====================================================

def limpiar_tablas():

    tablas = [

        "programaciones",

        "profesionales",

        "pacientes",

    ]

    for tabla in tablas:

        cursor.execute(
            f"DELETE FROM {tabla}"
        )

    connection.commit()

    print("Tablas limpiadas.")

# =====================================================
# CONTAR REGISTROS
# =====================================================

def contar(tabla):

    cursor.execute(

        f"SELECT COUNT(*) FROM {tabla}"

    )

    return cursor.fetchone()[0]

# =====================================================
# CREAR PACIENTES
# =====================================================

def crear_pacientes(cantidad=100):

    municipios = [
        "Armenia",
        "Calarcá",
        "La Tebaida",
        "Montenegro",
        "Circasia",
    ]

    for i in range(1, cantidad + 1):

        cursor.execute(
            """
            INSERT INTO pacientes (

                tipo_documento,
                documento,
                primer_nombre,
                segundo_nombre,
                primer_apellido,
                segundo_apellido,
                fecha_nacimiento,
                sexo,
                eps,
                regimen,
                telefono,
                celular,
                correo,
                direccion,
                barrio,
                municipio,
                departamento,
                fecha_registro,
                uuid,
                nombre_completo,
                edad,
                latitud,
                longitud,
                riesgo_clinico,
                prioridad_domiciliaria

            )

            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

            """,

            (

                "CC",
                f"1000{i:05}",
                f"Paciente{i}",
                "",
                "Prueba",
                "",
                "1990-01-01",
                random.choice(["M", "F"]),
                "Nueva EPS",
                "Contributivo",
                "606000000",
                f"300500{i:04}",
                f"paciente{i}@homecare.com",
                f"Calle {i}",
                "Centro",
                random.choice(municipios),
                "Quindío",
                datetime.now().strftime("%Y-%m-%d"),
                f"PAC-{i:05}",
                f"Paciente{i} Prueba",
                random.randint(18, 90),
                4.53,
                -75.67,
                random.choice([
                    "Bajo",
                    "Medio",
                    "Alto",
                ]),
                random.choice([
                    "Normal",
                    "Prioritaria",
                ]),

            ),

        )

    connection.commit()

    print(f"{cantidad} pacientes creados.")

# =====================================================
# CREAR PROFESIONALES
# =====================================================

def crear_profesionales(cantidad=25):

    profesiones = [
        "Médico",
        "Enfermero",
        "Fisioterapeuta",
        "Terapeuta Respiratorio",
        "Terapeuta Ocupacional",
        "Psicólogo",
        "Nutricionista",
    ]

    municipios = [
        "Armenia",
        "Calarcá",
        "Montenegro",
        "Circasia",
        "La Tebaida",
    ]

    for i in range(1, cantidad + 1):

        profesion = random.choice(profesiones)

        cursor.execute(
            """
            INSERT INTO profesionales(

                documento,
                nombre,
                profesion,
                telefono,
                correo,
                estado,
                primer_nombre,
                segundo_nombre,
                primer_apellido,
                segundo_apellido,
                nombre_completo,
                especialidad_principal,
                municipio,
                departamento,
                disponible,
                latitud,
                longitud,
                capacidad_diaria

            )

            VALUES(
                ?,?,?,?,?,?,
                ?,?,?,?,?,?,
                ?,?,?,?,?,?
            )
            """,

            (

                f"9000{i:05}",
                f"Profesional {i}",
                profesion,
                f"310700{i:04}",
                f"profesional{i}@homecare.com",
                "Activo",

                f"Profesional{i}",
                "",
                "HomeCare",
                "",
                f"Profesional{i} HomeCare",

                profesion,

                random.choice(municipios),

                "Quindío",

                1,

                4.53,

                -75.67,

                random.randint(6,10)

            )

        )

    connection.commit()

    print(f"{cantidad} profesionales creados.")

    # =====================================================
# CREAR PROGRAMACIONES
# =====================================================

def crear_programaciones(cantidad=500):

    estados = [

        "Programada",

        "En curso",

        "Completada",

        "Cancelada",

    ]

    servicios = [

        "Consulta Médica",

        "Enfermería",

        "Curación",

        "Terapia Física",

        "Terapia Respiratoria",

    ]

    municipios = [

        "Armenia",

        "Calarcá",

        "Montenegro",

        "Circasia",

        "La Tebaida",

    ]

    fecha_base = datetime.now()

    for i in range(cantidad):

        fecha = fecha_base + timedelta(

            days=random.randint(-2, 5)

        )

        hora = f"{random.randint(7,17):02}:00"

        cursor.execute(
            """
            INSERT INTO programaciones(

                paciente_id,
                profesional_id,
                fecha,
                hora,
                servicio,
                estado,
                uuid,
                hora_inicio,
                hora_fin,
                duracion,
                prioridad,
                direccion,
                barrio,
                municipio,
                departamento,
                latitud,
                longitud,
                usuario_creacion,
                usuario_actualizacion,
                fecha_actualizacion

            )

            VALUES(

            ?,?,?,?,?,?,
            ?,?,?,?,?,?,
            ?,?,?,?,?,?,
            ?,?

            )
            """,

            (

                random.randint(1,100),

                random.randint(1,25),

                fecha.strftime("%Y-%m-%d"),

                hora,

                random.choice(servicios),

                random.choice(estados),

                f"PROG-{i+1:06}",

                hora,

                f"{int(hora[:2])+1:02}:00",

                60,

                random.choice([
                    "Normal",
                    "Alta",
                ]),

                f"Calle {random.randint(1,80)}",

                "Centro",

                random.choice(municipios),

                "Quindío",

                4.53,

                -75.67,

                1,

                1,

                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            )

        )

    connection.commit()

    print(f"{cantidad} programaciones creadas.")

# =====================================================
# RESUMEN
# =====================================================

def resumen():

    print()

    print("=" * 60)

    print("RESUMEN")

    print("=" * 60)

    print(

        "Pacientes:",

        contar("pacientes")

    )

    print(

        "Profesionales:",

        contar("profesionales")

    )

    print(

        "Programaciones:",

        contar("programaciones")

    )

    print()

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    limpiar_tablas()

    crear_pacientes()

    crear_profesionales()

    crear_programaciones()

    resumen()