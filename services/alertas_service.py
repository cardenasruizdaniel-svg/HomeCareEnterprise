"""
=========================================================
HomeCare Enterprise
Servicio: Alertas al ingresar a la ficha del paciente

Muestra de forma inmediata: alergias activas (medicamentos,
alimentos, etc.), medicamentos que el paciente esta tomando
actualmente, diagnosticos activos y proxima visita.
=========================================================
"""

from repositories.alertas_repository import (
    obtener_alergias,
    obtener_diagnosticos,
    obtener_medicamentos_activos,
    obtener_proxima_visita,
)

NIVEL_A_COLOR = {
    "Anafilaxia": "danger",
    "Grave": "danger",
    "Moderada": "warning",
    "Leve": "info",
}


def obtener_alertas(paciente_id):

    alertas = []

    # =====================
    # ALERGIAS (medicamentos, alimentos, látex, etc.)
    # =====================

    alergias = obtener_alergias(paciente_id)

    for a in alergias:
        tipo_legible = {
            "MED": "Medicamento",
            "ALI": "Alimento",
            "LAT": "Látex",
            "CON": "Medio de contraste",
            "PIC": "Picadura/insecto",
            "AMB": "Ambiental",
            "OTR": "Otro",
        }.get(a["tipo"], a["tipo"])

        mensaje = f"Alergia a {tipo_legible.lower()}: {a['alergeno']}"

        if a["reaccion"]:
            mensaje += f" (reacción: {a['reaccion']})"

        alertas.append({
            "tipo": "alergia",
            "categoria": tipo_legible,
            "nivel": a["severidad"],
            "color": NIVEL_A_COLOR.get(a["severidad"], "warning"),
            "icono": "fa-triangle-exclamation",
            "mensaje": mensaje,
        })

    # =====================
    # MEDICAMENTOS ACTUALES
    # =====================

    medicamentos = obtener_medicamentos_activos(paciente_id)

    for m in medicamentos:
        detalle = " · ".join(
            x for x in [m["dosis"], m["frecuencia"], m["via"]] if x
        )

        alertas.append({
            "tipo": "medicamento",
            "categoria": "Medicamento activo",
            "nivel": "Info",
            "color": "primary",
            "icono": "fa-pills",
            "mensaje": f"{m['nombre']}" + (f" — {detalle}" if detalle else ""),
        })

    # =====================
    # DIAGNÓSTICOS
    # =====================

    diagnosticos = obtener_diagnosticos(paciente_id)

    for d in diagnosticos:
        alertas.append({
            "tipo": "diagnostico",
            "categoria": "Diagnóstico",
            "nivel": "Info",
            "color": "secondary",
            "icono": "fa-notes-medical",
            "mensaje": f"{d['codigo_cie10']} - {d['diagnostico']}",
        })

    # =====================
    # PRÓXIMA VISITA
    # =====================

    visita = obtener_proxima_visita(paciente_id)

    if visita:
        alertas.append({
            "tipo": "agenda",
            "categoria": "Agenda",
            "nivel": "Info",
            "color": "success",
            "icono": "fa-calendar-check",
            "mensaje": f"Próxima visita: {visita['fecha']} {visita['hora_inicio']}",
        })

    # =====================
    # COPAGOS PENDIENTES DE PAGO
    # =====================

    from database.database import consultar

    copagos_pendientes = consultar(
        "SELECT concepto, valor_copago FROM copagos WHERE paciente_id=? AND pagado=0",
        (paciente_id,),
    )

    if copagos_pendientes:
        total_pendiente = sum(dict(c)["valor_copago"] for c in copagos_pendientes)

        conceptos = ", ".join(dict(c)["concepto"] or "Copago" for c in copagos_pendientes)

        alertas.append({
            "tipo": "copago",
            "categoria": "Copago pendiente",
            "nivel": "Alerta",
            "color": "danger",
            "icono": "fa-hand-holding-dollar",
            "mensaje": (
                f"Tiene {len(copagos_pendientes)} copago(s) sin pagar por un total de "
                f"$ {total_pendiente:,.0f} ({conceptos})"
            ),
        })

    return alertas


def obtener_resumen_seguridad(paciente_id) -> dict:
    """
    Resumen rapido para mostrar como banner al entrar al
    paciente: cuantas alergias criticas tiene, que
    medicamentos esta tomando actualmente, y si tiene
    copagos pendientes de pago.
    """

    alergias = obtener_alergias(paciente_id)
    medicamentos = obtener_medicamentos_activos(paciente_id)

    criticas = [a for a in alergias if a["severidad"] in ("Grave", "Anafilaxia")]

    from database.database import consultar

    copagos_pendientes = [
        dict(c) for c in consultar(
            "SELECT id, concepto, valor_copago, fecha_creacion FROM copagos "
            "WHERE paciente_id=? AND pagado=0 ORDER BY fecha_creacion",
            (paciente_id,),
        )
    ]

    total_copagos_pendientes = sum(c["valor_copago"] for c in copagos_pendientes)

    return {
        "tiene_alergias": len(alergias) > 0,
        "tiene_alergias_criticas": len(criticas) > 0,
        "total_alergias": len(alergias),
        "alergias": alergias,
        "total_medicamentos": len(medicamentos),
        "medicamentos": medicamentos,
        "tiene_copagos_pendientes": len(copagos_pendientes) > 0,
        "copagos_pendientes": copagos_pendientes,
        "total_copagos_pendientes": total_copagos_pendientes,
    }
