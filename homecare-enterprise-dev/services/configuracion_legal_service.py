"""
HomeCare Enterprise - Configuración Legal / Cumplimiento Normativo

Centraliza en una sola pantalla todas las "llaves" (códigos,
resoluciones, credenciales) que exigen los distintos entes del
gobierno colombiano para que el sistema pueda operar de forma
legal: Secretaría de Salud (REPS), Ministerio de Salud (RIPS),
DIAN (facturación y nómina electrónica), UGPP/operador PILA, y
SIC (protección de datos).

Antes, algunas de estas quedaban solo en variables de entorno
(archivo .env), lo que requería a alguien con conocimiento
técnico para tocarlas. Ahora quedan en la base de datos, con
una pantalla web donde el administrador las diligencia
directamente.
"""

from database.database import consultar_uno, ejecutar

# Campos que jamás se deben volver a mostrar en texto plano
# una vez guardados, para no exponer contraseñas en pantalla.
CAMPOS_SENSIBLES = ("dian_certificado_password", "pila_clave")


def obtener() -> dict:
    fila = consultar_uno("SELECT * FROM configuracion_legal WHERE id=1")
    if not fila:
        ejecutar("INSERT INTO configuracion_legal(id) VALUES (1)")
        fila = consultar_uno("SELECT * FROM configuracion_legal WHERE id=1")
    return dict(fila)


def guardar(datos: dict, usuario_id=None):
    obtener()  # asegura que exista la fila

    # Los campos sensibles solo se actualizan si mandaron un
    # valor nuevo -- si el campo llega vacío, se conserva el
    # que ya estaba guardado (para no borrarlo por accidente
    # solo por recargar el formulario, que siempre lo muestra
    # en blanco por seguridad).
    actual = obtener()
    for campo in CAMPOS_SENSIBLES:
        if not datos.get(campo):
            datos[campo] = actual.get(campo)

    columnas = [c for c in datos.keys() if c not in ("id",)]
    set_clause = ", ".join(f"{c}=:{c}" for c in columnas)

    datos["usuario_actualizacion"] = usuario_id
    ejecutar(
        f"UPDATE configuracion_legal SET {set_clause}, fecha_actualizacion=CURRENT_TIMESTAMP, "
        f"usuario_actualizacion=:usuario_actualizacion WHERE id=1",
        datos,
    )


def resumen_estado() -> list:
    """
    Un vistazo rápido de qué tan completa está cada sección,
    para que el administrador sepa de un vistazo qué le falta
    diligenciar antes de operar en producción real.
    """
    config = obtener()

    secciones = [
        {
            "nombre": "REPS / Habilitación en Salud",
            "responsable": "Secretaría de Salud Departamental / Ministerio de Salud",
            "completo": bool(config.get("reps_codigo_habilitacion") and config.get("reps_numero_habilitacion")),
        },
        {
            "nombre": "RIPS",
            "responsable": "Ministerio de Salud / SISPRO",
            "completo": bool(config.get("rips_nit_prestador") and config.get("rips_codigo_prestador")),
        },
        {
            "nombre": "DIAN — Facturación Electrónica",
            "responsable": "DIAN",
            "completo": bool(
                config.get("dian_nit") and config.get("dian_resolucion_numero")
                and config.get("dian_software_id") and config.get("dian_certificado_base64")
            ),
        },
        {
            "nombre": "DIAN — Nómina Electrónica",
            "responsable": "DIAN",
            "completo": bool(config.get("dian_nomina_software_id")),
        },
        {
            "nombre": "UGPP / Operador PILA (Seguridad Social)",
            "responsable": "UGPP / Operador de planillas (Aportes en Línea, SOI, etc.)",
            "completo": bool(config.get("pila_operador") and config.get("pila_usuario")),
        },
        {
            "nombre": "SIC — Protección de Datos (RNBD)",
            "responsable": "Superintendencia de Industria y Comercio",
            "completo": bool(config.get("sic_numero_registro_rnbd")),
        },
        {
            "nombre": "ARL",
            "responsable": "Administradora de Riesgos Laborales contratada",
            "completo": bool(config.get("arl_nit")),
        },
    ]
    return secciones
