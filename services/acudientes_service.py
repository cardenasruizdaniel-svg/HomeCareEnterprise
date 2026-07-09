from repositories.acudientes_repository import (
    listar_por_paciente,
    obtener,
    crear,
    actualizar,
    eliminar,
    establecer_principal
)


# ==========================================
# LISTAR ACUDIENTES
# ==========================================

def obtener_acudientes(paciente_id):

    return listar_por_paciente(paciente_id)


# ==========================================
# OBTENER ACUDIENTE
# ==========================================

def obtener_acudiente(id):

    return obtener(id)


# ==========================================
# CREAR ACUDIENTE
# ==========================================

def crear_acudiente(
    paciente_id,
    nombre,
    tipo_documento,
    documento,
    parentesco,
    telefono_principal,
    telefono_secundario,
    correo,
    direccion,
    barrio,
    municipio,
    departamento,
    ciudad,
    ocupacion,
    observaciones,
    es_principal,
    autoriza_decisiones,
    recibe_informacion
):

    crear(
        paciente_id,
        nombre,
        tipo_documento,
        documento,
        parentesco,
        telefono_principal,
        telefono_secundario,
        correo,
        direccion,
        barrio,
        municipio,
        departamento,
        ciudad,
        ocupacion,
        observaciones,
        es_principal,
        autoriza_decisiones,
        recibe_informacion
    )


# ==========================================
# ACTUALIZAR ACUDIENTE
# ==========================================

def actualizar_acudiente(
    id,
    nombre,
    tipo_documento,
    documento,
    parentesco,
    telefono_principal,
    telefono_secundario,
    correo,
    direccion,
    barrio,
    municipio,
    departamento,
    ciudad,
    ocupacion,
    observaciones,
    es_principal,
    autoriza_decisiones,
    recibe_informacion
):

    actualizar(
        id,
        nombre,
        tipo_documento,
        documento,
        parentesco,
        telefono_principal,
        telefono_secundario,
        correo,
        direccion,
        barrio,
        municipio,
        departamento,
        ciudad,
        ocupacion,
        observaciones,
        es_principal,
        autoriza_decisiones,
        recibe_informacion
    )


# ==========================================
# ELIMINAR
# ==========================================

def eliminar_acudiente(id):

    eliminar(id)


# ==========================================
# DEFINIR ACUDIENTE PRINCIPAL
# ==========================================

def definir_principal(id, paciente_id):

    establecer_principal(id, paciente_id)