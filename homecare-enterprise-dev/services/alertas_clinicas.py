# ==========================================================
# MOTOR DE ALERTAS CLÍNICAS
# ==========================================================

def generar_alertas(

    temperatura,
    sistolica,
    diastolica,
    frecuencia_cardiaca,
    frecuencia_respiratoria,
    saturacion,
    glucemia,
    imc,
    dolor

):

    alertas = []

    # ===============================================
    # TEMPERATURA
    # ===============================================

    if temperatura >= 40:

        alertas.append({

            "tipo": "CRITICA",

            "titulo": "Hipertermia grave",

            "mensaje": "Temperatura mayor o igual a 40°C.",

            "color": "danger",

            "icono": "fa-temperature-full"

        })

    elif temperatura >= 38:

        alertas.append({

            "tipo": "ADVERTENCIA",

            "titulo": "Fiebre",

            "mensaje": "Temperatura elevada.",

            "color": "warning",

            "icono": "fa-temperature-three-quarters"

        })

    elif temperatura < 35:

        alertas.append({

            "tipo": "CRITICA",

            "titulo": "Hipotermia",

            "mensaje": "Temperatura menor a 35°C.",

            "color": "danger",

            "icono": "fa-temperature-empty"

        })

    # ===============================================
    # PRESIÓN ARTERIAL
    # ===============================================

    if sistolica >= 180 or diastolica >= 110:

        alertas.append({

            "tipo": "CRITICA",

            "titulo": "Crisis hipertensiva",

            "mensaje": f"TA {sistolica}/{diastolica}",

            "color": "danger",

            "icono": "fa-heart-circle-exclamation"

        })

    elif sistolica >= 140 or diastolica >= 90:

        alertas.append({

            "tipo": "ADVERTENCIA",

            "titulo": "Hipertensión",

            "mensaje": f"TA {sistolica}/{diastolica}",

            "color": "warning",

            "icono": "fa-heart"

        })

    # ===============================================
    # SATURACIÓN
    # ===============================================

    if saturacion < 90:

        alertas.append({

            "tipo": "CRITICA",

            "titulo": "Hipoxemia",

            "mensaje": f"SatO₂ {saturacion}%",

            "color": "danger",

            "icono": "fa-lungs"

        })

    elif saturacion < 94:

        alertas.append({

            "tipo": "ADVERTENCIA",

            "titulo": "Saturación baja",

            "mensaje": f"SatO₂ {saturacion}%",

            "color": "warning",

            "icono": "fa-lungs"

        })

    # ===============================================
    # FRECUENCIA CARDÍACA
    # ===============================================

    if frecuencia_cardiaca > 120:

        alertas.append({

            "tipo": "CRITICA",

            "titulo": "Taquicardia",

            "mensaje": f"{frecuencia_cardiaca} lpm",

            "color": "danger",

            "icono": "fa-heart-pulse"

        })

    elif frecuencia_cardiaca < 50:

        alertas.append({

            "tipo": "ADVERTENCIA",

            "titulo": "Bradicardia",

            "mensaje": f"{frecuencia_cardiaca} lpm",

            "color": "warning",

            "icono": "fa-heart-pulse"

        })

    # ===============================================
    # FRECUENCIA RESPIRATORIA
    # ===============================================

    if frecuencia_respiratoria > 30:

        alertas.append({

            "tipo": "CRITICA",

            "titulo": "Taquipnea",

            "mensaje": f"{frecuencia_respiratoria} rpm",

            "color": "danger",

            "icono": "fa-lungs"

        })

    # ===============================================
    # GLUCEMIA
    # ===============================================

    if glucemia >= 300:

        alertas.append({

            "tipo": "CRITICA",

            "titulo": "Hiperglucemia severa",

            "mensaje": f"{glucemia} mg/dL",

            "color": "danger",

            "icono": "fa-droplet"

        })

    elif glucemia <= 70:

        alertas.append({

            "tipo": "ADVERTENCIA",

            "titulo": "Hipoglucemia",

            "mensaje": f"{glucemia} mg/dL",

            "color": "warning",

            "icono": "fa-droplet"

        })

    # ===============================================
    # IMC
    # ===============================================

    if imc >= 40:

        alertas.append({

            "tipo": "INFORMATIVA",

            "titulo": "Obesidad grado III",

            "mensaje": f"IMC {imc}",

            "color": "secondary",

            "icono": "fa-weight-scale"

        })

    elif imc < 18.5:

        alertas.append({

            "tipo": "INFORMATIVA",

            "titulo": "Bajo peso",

            "mensaje": f"IMC {imc}",

            "color": "secondary",

            "icono": "fa-weight-scale"

        })

    # ===============================================
    # DOLOR
    # ===============================================

    if dolor >= 8:

        alertas.append({

            "tipo": "ADVERTENCIA",

            "titulo": "Dolor intenso",

            "mensaje": f"EVA {dolor}/10",

            "color": "warning",

            "icono": "fa-triangle-exclamation"

        })

    return alertas