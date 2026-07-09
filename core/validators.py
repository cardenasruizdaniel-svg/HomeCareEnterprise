"""
=========================================================
HomeCare IPS Enterprise
Validadores Globales
=========================================================
"""

import re
from datetime import datetime

from core.exceptions import ValidacionError


# ==========================================================
# CAMPOS OBLIGATORIOS
# ==========================================================

def requerido(valor, campo):

    if valor is None:
        raise ValidacionError(f"El campo '{campo}' es obligatorio.")

    if isinstance(valor, str) and not valor.strip():
        raise ValidacionError(f"El campo '{campo}' es obligatorio.")

    return valor


# ==========================================================
# LONGITUD MÍNIMA
# ==========================================================

def longitud_minima(texto, minimo, campo):

    requerido(texto, campo)

    if len(texto.strip()) < minimo:
        raise ValidacionError(
            f"El campo '{campo}' debe tener mínimo {minimo} caracteres."
        )

    return texto.strip()


# ==========================================================
# DOCUMENTO
# ==========================================================

def validar_documento(documento):

    requerido(documento, "Documento")

    documento = str(documento).strip()

    if not documento.isdigit():
        raise ValidacionError(
            "El documento solo puede contener números."
        )

    if len(documento) < 5:
        raise ValidacionError(
            "El documento es demasiado corto."
        )

    return documento


# ==========================================================
# TELÉFONO
# ==========================================================

def validar_telefono(telefono):

    requerido(telefono, "Teléfono")

    telefono = str(telefono).strip()

    if not telefono.isdigit():
        raise ValidacionError(
            "El teléfono solo puede contener números."
        )

    if len(telefono) < 7:
        raise ValidacionError(
            "Número telefónico inválido."
        )

    return telefono


# ==========================================================
# EMAIL
# ==========================================================

def validar_email(correo):

    requerido(correo, "Correo")

    patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    if not re.match(patron, correo):
        raise ValidacionError(
            "Correo electrónico inválido."
        )

    return correo.lower()


# ==========================================================
# FECHA
# ==========================================================

def validar_fecha(fecha):

    requerido(fecha, "Fecha")

    try:

        datetime.strptime(fecha, "%Y-%m-%d")

    except ValueError:

        raise ValidacionError(
            "Formato de fecha inválido."
        )

    return fecha


# ==========================================================
# HORA
# ==========================================================

def validar_hora(hora):

    requerido(hora, "Hora")

    try:

        datetime.strptime(hora, "%H:%M")

    except ValueError:

        raise ValidacionError(
            "Formato de hora inválido."
        )

    return hora


# ==========================================================
# NÚMEROS
# ==========================================================

def validar_numero(valor, minimo=None, maximo=None, campo="Valor"):

    try:

        numero = float(valor)

    except (TypeError, ValueError):

        raise ValidacionError(
            f"{campo} debe ser numérico."
        )

    if minimo is not None and numero < minimo:

        raise ValidacionError(
            f"{campo} no puede ser menor que {minimo}."
        )

    if maximo is not None and numero > maximo:

        raise ValidacionError(
            f"{campo} no puede ser mayor que {maximo}."
        )

    return numero


# ==========================================================
# TEXTO
# ==========================================================

def limpiar_texto(texto):

    if texto is None:
        return ""

    return str(texto).strip()


# ==========================================================
# LISTA
# ==========================================================

def validar_opcion(valor, opciones, campo):

    if valor not in opciones:

        raise ValidacionError(

            f"'{valor}' no es una opción válida para {campo}."

        )

    return valor