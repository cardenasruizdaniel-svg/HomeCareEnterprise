"""HomeCare Enterprise - Configuración del Chatbot de WhatsApp"""

import secrets

from database.database import consultar_uno, ejecutar

CAMPOS_SENSIBLES = ("token_acceso",)


def obtener() -> dict:
    fila = consultar_uno("SELECT * FROM configuracion_whatsapp WHERE id=1")
    if not fila:
        # Se genera un token de verificacion aleatorio la primera
        # vez, para que el administrador solo tenga que copiarlo
        # al panel de Meta, sin tener que inventarse uno.
        ejecutar(
            "INSERT INTO configuracion_whatsapp(id, token_verificacion_webhook) VALUES (1, ?)",
            (secrets.token_hex(16),),
        )
        fila = consultar_uno("SELECT * FROM configuracion_whatsapp WHERE id=1")
    return dict(fila)


def guardar(datos: dict, usuario_id=None):
    actual = obtener()
    for campo in CAMPOS_SENSIBLES:
        if not datos.get(campo):
            datos[campo] = actual.get(campo)

    columnas = [c for c in datos.keys() if c != "id"]
    set_clause = ", ".join(f"{c}=:{c}" for c in columnas)

    datos["usuario_actualizacion"] = usuario_id
    ejecutar(
        f"UPDATE configuracion_whatsapp SET {set_clause}, fecha_actualizacion=CURRENT_TIMESTAMP, "
        f"usuario_actualizacion=:usuario_actualizacion WHERE id=1",
        datos,
    )
