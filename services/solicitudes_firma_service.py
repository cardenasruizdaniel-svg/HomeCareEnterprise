"""
HomeCare Enterprise - Firma remota por código QR

Permite que quien deba firmar (el paciente o el profesional)
lo haga desde SU PROPIO celular: se genera un enlace de un
solo uso (token), se muestra como código QR en la pantalla de
quien esta gestionando el documento, la persona lo escanea con
su celular, firma en una pagina simple sin necesitar cuenta en
el sistema, y la pantalla original detecta automaticamente
que ya se firmo.
"""

import uuid

from database.database import consultar_uno, ejecutar

TIPOS_VALIDOS = ("planilla_visita", "consentimiento", "contrato")


def crear_solicitud(tipo: str, referencia_id: int) -> str:

    if tipo not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo de solicitud de firma no válido: {tipo}")

    token = uuid.uuid4().hex

    ejecutar(
        "INSERT INTO solicitudes_firma(token, tipo, referencia_id) VALUES (?, ?, ?)",
        (token, tipo, referencia_id),
    )

    return token


def obtener_por_token(token: str):
    fila = consultar_uno("SELECT * FROM solicitudes_firma WHERE token=?", (token,))
    return dict(fila) if fila else None


def completar_firma(token: str, firma_base64: str, firmante: str = "",
                      nombre_firmante: str = "", documento_firmante: str = "",
                      parentesco_firmante: str = "") -> dict:

    solicitud = obtener_por_token(token)

    if not solicitud:
        raise ValueError("Este enlace de firma no es válido.")

    if solicitud["estado"] == "Completada":
        raise ValueError("Este documento ya fue firmado anteriormente.")

    if not firma_base64:
        raise ValueError("Debe capturar la firma antes de enviarla.")

    ejecutar(
        """
        UPDATE solicitudes_firma
        SET estado='Completada', firma_base64=?, firmante=?, nombre_firmante=?,
            documento_firmante=?, parentesco_firmante=?, fecha_completado=CURRENT_TIMESTAMP
        WHERE token=?
        """,
        (firma_base64, firmante, nombre_firmante, documento_firmante, parentesco_firmante, token),
    )

    # Aplicar la firma en el documento real correspondiente
    if solicitud["tipo"] == "planilla_visita":
        from services.planilla_visitas_service import firmar_visita
        firmar_visita(
            solicitud["referencia_id"], firmante or "Paciente", nombre_firmante,
            firma_base64,
        )
    elif solicitud["tipo"] == "consentimiento":
        from services.consentimientos_service import firmar_consentimiento
        firmar_consentimiento(
            solicitud["referencia_id"], firmante or "Paciente", nombre_firmante,
            documento_firmante, parentesco_firmante, firma_base64,
        )
    elif solicitud["tipo"] == "contrato":
        from services.contratos_service import firmar_contrato
        firmar_contrato(solicitud["referencia_id"], firma_base64)

    return {"ok": True}
