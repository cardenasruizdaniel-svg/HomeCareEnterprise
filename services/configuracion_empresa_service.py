"""
HomeCare Enterprise - Configuración de la Empresa

Guarda los datos legales y el logo de la IPS en un solo lugar
(una sola fila en la base de datos), para que todos los
reportes impresos (consentimientos, informes de historia
clínica, etc.) usen siempre la misma información oficial, sin
tener que editar archivos de configuración a mano.
"""

from database.database import consultar_uno, ejecutar

VALORES_POR_DEFECTO = {
    "razon_social": "HomeCare Enterprise",
    "nit": "",
    "resolucion_habilitacion": "",
    "direccion": "",
    "telefono": "",
    "correo": "",
    "ciudad": "",
    "departamento": "",
    "representante_legal": "",
    "logo_base64": None,
}


def obtener() -> dict:
    fila = consultar_uno("SELECT * FROM configuracion_empresa WHERE id=1")
    if not fila:
        return {**VALORES_POR_DEFECTO, "id": 1}
    return dict(fila)


def guardar(datos: dict, usuario_id=None) -> dict:

    if not datos.get("razon_social"):
        raise ValueError("La razón social es obligatoria.")

    existente = consultar_uno("SELECT id FROM configuracion_empresa WHERE id=1")

    campos = {
        "razon_social": datos.get("razon_social", ""),
        "nit": datos.get("nit", ""),
        "resolucion_habilitacion": datos.get("resolucion_habilitacion", ""),
        "direccion": datos.get("direccion", ""),
        "telefono": datos.get("telefono", ""),
        "correo": datos.get("correo", ""),
        "ciudad": datos.get("ciudad", ""),
        "departamento": datos.get("departamento", ""),
        "representante_legal": datos.get("representante_legal", ""),
    }

    # El logo solo se actualiza si mandaron uno nuevo (para no
    # borrarlo sin querer al editar solo los datos de texto).
    if datos.get("logo_base64"):
        campos["logo_base64"] = datos["logo_base64"]

    if existente:
        asignaciones = ", ".join(f"{campo}=:{campo}" for campo in campos)
        ejecutar(
            f"UPDATE configuracion_empresa SET {asignaciones}, fecha_actualizacion=CURRENT_TIMESTAMP WHERE id=1",
            campos,
        )
    else:
        campos.setdefault("logo_base64", None)
        columnas = ", ".join(campos.keys())
        marcadores = ", ".join(f":{c}" for c in campos.keys())
        ejecutar(
            f"INSERT INTO configuracion_empresa(id, {columnas}) VALUES (1, {marcadores})",
            campos,
        )

    return obtener()
