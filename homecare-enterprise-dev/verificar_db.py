import sqlite3

conexion = sqlite3.connect("database.db")

cursor = conexion.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""")

print("\nTABLAS EN LA BASE DE DATOS:\n")

for tabla in cursor.fetchall():
    print(f"✓ {tabla[0]}")

conexion.close()