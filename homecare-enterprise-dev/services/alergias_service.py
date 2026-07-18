from repositories.alergias_repository import (
    listar,
    listar_activas,
    obtener,
    crear,
    actualizar,
    cambiar_estado,
    eliminar
)

# ==========================================
# CATÁLOGOS
# ==========================================

TIPOS_VALIDOS = [
    "MED",   # Medicamentos
    "ALI",   # Alimentos
    "LAT",   # Látex
    "CON",   # Contraste
    "PIC",   # Picaduras
    "AMB",   # Ambientales
    "OTR"    # Otros
]

SEVERIDADES = [
    "Leve",
    "Moderada",
    "Grave",
    "Anafilaxia"
]

ESTADOS = [
    "Activa",
    "Inactiva",
    "Descartada"
]


# ==========================================
# LISTAR
# ==========================================

def listar_alergias(paciente_id):

    return listar(paciente_id)


# ==========================================
# LISTAR ACTIVAS
# ==========================================

def obtener_alertas(paciente_id):

    return listar_activas(paciente_id)


# ==========================================
# OBTENER
# ==========================================

def obtener_alergia(id):

    return obtener(id)


# ==========================================
# CREAR
# ==========================================

def crear_alergia(

    paciente_id,
    tipo,
    alergeno,
    severidad,
    estado,
    reaccion,
    observaciones,
    fecha_diagnostico,
    usuario

):

    if not paciente_id:

        raise Exception(
            "Debe seleccionar un paciente."
        )

    if tipo not in TIPOS_VALIDOS:

        raise Exception(
            "Tipo de alergia inválido."
        )

    if severidad not in SEVERIDADES:

        raise Exception(
            "Severidad inválida."
        )

    if estado not in ESTADOS:

        raise Exception(
            "Estado inválido."
        )

    if alergeno.strip() == "":

        raise Exception(
            "Debe indicar el alérgeno."
        )

    alergias = listar(paciente_id)

    for item in alergias:

        if (

            item["alergeno"].strip().upper()

            ==

            alergeno.strip().upper()

            and

            item["estado"] == "Activa"

        ):

            raise Exception(

                "Ya existe una alergia activa para este alérgeno."

            )

    crear(

        paciente_id,

        tipo,

        alergeno,

        severidad,

        estado,

        reaccion,

        observaciones,

        fecha_diagnostico,

        usuario

    )


# ==========================================
# ACTUALIZAR
# ==========================================

def actualizar_alergia(

    id,

    tipo,

    alergeno,

    severidad,

    estado,

    reaccion,

    observaciones,

    fecha_diagnostico,

    usuario

):

    if tipo not in TIPOS_VALIDOS:

        raise Exception(
            "Tipo inválido."
        )

    if severidad not in SEVERIDADES:

        raise Exception(
            "Severidad inválida."
        )

    if estado not in ESTADOS:

        raise Exception(
            "Estado inválido."
        )

    actualizar(

        id,

        tipo,

        alergeno,

        severidad,

        estado,

        reaccion,

        observaciones,

        fecha_diagnostico,

        usuario

    )


# ==========================================
# CAMBIAR ESTADO
# ==========================================

def cambiar_estado_alergia(id, estado):

    if estado not in ESTADOS:

        raise Exception(
            "Estado inválido."
        )

    cambiar_estado(id, estado)


# ==========================================
# ELIMINAR
# ==========================================

def eliminar_alergia(id):

    eliminar(id)