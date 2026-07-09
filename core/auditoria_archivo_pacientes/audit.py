from datetime import datetime


def crear_evento(
    usuario: str,
    accion: str,
    modulo: str,
    registro: str,
    resultado: str = "OK",
) -> dict:

    return {
        "fecha": datetime.utcnow().isoformat(),
        "usuario": usuario,
        "accion": accion,
        "modulo": modulo,
        "registro": registro,
        "resultado": resultado,
    }


# ==========================================================
# COMPATIBILIDAD
# ==========================================================

def registrar_auditoria(
    usuario: str,
    accion: str,
    modulo: str,
    registro: str,
    resultado: str = "OK",
):
    """
    Alias para mantener compatibilidad con el código existente.
    """

    return crear_evento(
        usuario=usuario,
        accion=accion,
        modulo=modulo,
        registro=registro,
        resultado=resultado,
    )