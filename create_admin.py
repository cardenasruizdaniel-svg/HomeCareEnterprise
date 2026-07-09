import bcrypt
import sqlite3

cn = sqlite3.connect("database.db")

cur = cn.cursor()

password = bcrypt.hashpw(
    "Admin123*".encode(),
    bcrypt.gensalt()
).decode()

cur.execute("""
INSERT INTO usuarios
(
    nombre,
    usuario,
    password,
    rol,
    correo,
    telefono,
    estado
)
VALUES
(
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?
)
""",
(
    "Administrador",
    "admin",
    password,
    "Administrador",
    "admin@homecare.com",
    "",
    "Activo"
))

cn.commit()

print("===================================")
print("Administrador creado correctamente")
print("Usuario : admin")
print("Password: Admin123*")
print("===================================")

cn.close()