from repositories.cie10_repository import (

    buscar,

    obtener_por_codigo,

    insertar,

    total_registros,

    eliminar_todo

)


# ==========================================
# BUSCAR DIAGNÓSTICOS
# ==========================================

def buscar_cie10(texto):

    if texto is None:

        texto = ""

    texto = texto.strip()

    if len(texto) < 2:

        return []

    return buscar(texto)


# ==========================================
# OBTENER POR CÓDIGO
# ==========================================

def obtener_diagnostico(codigo):

    return obtener_por_codigo(codigo)


# ==========================================
# INSERTAR DIAGNÓSTICO
# ==========================================

def crear_diagnostico(

    codigo,

    descripcion,

    categoria,

    capitulo

):

    existente = obtener_por_codigo(codigo)

    if existente:

        return False

    insertar(

        codigo,

        descripcion,

        categoria,

        capitulo

    )

    return True


# ==========================================
# TOTAL DEL CATÁLOGO
# ==========================================

def cantidad_diagnosticos():

    return total_registros()


# ==========================================
# REINICIAR CATÁLOGO
# ==========================================

def limpiar_catalogo():

    eliminar_todo()


# ==========================================
# IMPORTAR REGISTRO
# ==========================================

def importar_registro(fila):

    codigo = fila["codigo"].strip()

    descripcion = fila["descripcion"].strip()

    categoria = fila.get("categoria", "")

    capitulo = fila.get("capitulo", "")

    crear_diagnostico(

        codigo,

        descripcion,

        categoria,

        capitulo

    )