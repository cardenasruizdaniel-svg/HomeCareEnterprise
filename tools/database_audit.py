"""
=========================================================
HomeCare Enterprise
Database Audit Tool
=========================================================
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"

connection = sqlite3.connect(DATABASE)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

print("=" * 60)
print("HOMECARE ENTERPRISE")
print("DATABASE AUDIT")
print("=" * 60)
print()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""")

tablas = cursor.fetchall()

print(f"Tablas encontradas: {len(tablas)}")
print()

for tabla in tablas:

    nombre = tabla["name"]

    print("=" * 60)
    print(nombre.upper())
    print("=" * 60)

    cursor.execute(
        f"PRAGMA table_info({nombre})"
    )

    columnas = cursor.fetchall()

    for columna in columnas:

        print(
            f"{columna['name']:<25} {columna['type']}"
        )

    cursor.execute(
        f"SELECT COUNT(*) total FROM {nombre}"
    )

    total = cursor.fetchone()["total"]

    print()

    print(f"Registros: {total}")

    print()

connection.close()