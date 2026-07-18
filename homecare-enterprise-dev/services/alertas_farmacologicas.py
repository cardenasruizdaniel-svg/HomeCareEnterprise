from datetime import datetime

from repositories.medicamentos_repository import (
    listar_activos
)

from repositories.alergias_repository import (
    listar as listar_alergias


)


def validar_medicamento(

    paciente_id,

    nombre,

    principio_activo,

    dosis,

    frecuencia,

    via,

    fecha_inicio,

    fecha_fin

):

    alertas = []

    # ==========================================
    # Nombre obligatorio
    # ==========================================

    if not nombre.strip():

        alertas.append(
            "Debe indicar el medicamento."
        )

    # ==========================================
    # Dosis
    # ==========================================

    if not dosis.strip():

        alertas.append(
            "Debe indicar la dosis."
        )

    # ==========================================
    # Frecuencia
    # ==========================================

    if not frecuencia.strip():

        alertas.append(
            "Debe indicar la frecuencia."
        )

    # ==========================================
    # Vía
    # ==========================================

    if not via.strip():

        alertas.append(
            "Debe indicar la vía de administración."
        )

    # ==========================================
    # Fechas
    # ==========================================

    if fecha_inicio and fecha_fin:

        inicio = datetime.strptime(
            fecha_inicio,
            "%Y-%m-%d"
        )

        fin = datetime.strptime(
            fecha_fin,
            "%Y-%m-%d"
        )

        if fin < inicio:

            alertas.append(
                "La fecha final no puede ser anterior a la fecha inicial."
            )

    # ==========================================
    # Medicamentos duplicados
    # ==========================================

    activos = listar_activos(paciente_id)

    for medicamento in activos:

        if medicamento["nombre"].upper() == nombre.upper():

            alertas.append(
                "El paciente ya tiene este medicamento activo."
            )

        if (
            principio_activo
            and medicamento["principio_activo"].upper()
            == principio_activo.upper()
        ):

            alertas.append(
                "Ya existe un medicamento con el mismo principio activo."
            )

    # ==========================================
    # Alergias
    # ==========================================

    alergias = listar_alergias(paciente_id)

    for alergia in alergias:

        alergeno = (alergia["alergeno"] or "").upper()

        if nombre.upper() in alergeno or alergeno in nombre.upper():

            alertas.append(
                f"⚠ El medicamento coincide con la alergia registrada a '{alergia['alergeno']}'."
            )

        if (
            principio_activo
            and (
                principio_activo.upper() in alergeno
                or alergeno in principio_activo.upper()
            )
        ):

            alertas.append(
                f"⚠ El principio activo coincide con la alergia registrada a '{alergia['alergeno']}'."
            )

    return alertas