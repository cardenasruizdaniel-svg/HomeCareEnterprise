from repositories.antecedentes_repository import (
    listar,
    obtener,
    crear,
    actualizar,
    eliminar
)

# ==========================================
# TIPOS PERMITIDOS
# ==========================================

TIPOS_VALIDOS = [
    "AP",  # Antecedentes Personales
    "AF",  # Antecedentes Familiares
    "AQ",  # Antecedentes Quirúrgicos
    "AH",  # Hospitalizaciones
    "AL",  # Alergias
    "HT",  # Hábitos
    "GO",  # Gineco-Obstétricos
    "OC",  # Ocupacionales
    "FA"   # Farmacológicos
]

# ==========================================
# LISTAR
# ==========================================

def listar_antecedentes(paciente_id):

    return listar(paciente_id)


# ==========================================
# OBTENER
# ==========================================

def obtener_antecedente(id):

    return obtener(id)


# ==========================================
# CREAR
# ==========================================

def crear_antecedente(

    paciente_id,
    tipo,
    descripcion,
    observaciones,
    usuario

):

    if not paciente_id:

        raise Exception(
            "Debe seleccionar un paciente."
        )

    if tipo not in TIPOS_VALIDOS:

        raise Exception(
            "Tipo de antecedente no válido."
        )

    if descripcion.strip() == "":

        raise Exception(
            "Debe ingresar la descripción."
        )

    antecedentes = listar(paciente_id)

    for item in antecedentes:

        if (
            item["tipo"] == tipo
            and
            item["descripcion"].strip().upper()
            ==
            descripcion.strip().upper()
        ):

            raise Exception(
                "Este antecedente ya existe."
            )

    crear(

        paciente_id,
        tipo,
        descripcion,
        observaciones,
        usuario

    )


# ==========================================
# ACTUALIZAR
# ==========================================

def actualizar_antecedente(

    id,
    tipo,
    descripcion,
    observaciones,
    usuario

):

    if tipo not in TIPOS_VALIDOS:

        raise Exception(
            "Tipo inválido."
        )

    actualizar(

        id,
        tipo,
        descripcion,
        observaciones,
        usuario

    )


# ==========================================
# ELIMINAR
# ==========================================

def eliminar_antecedente(id):

    eliminar(id)