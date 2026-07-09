"""
=========================================================
HomeCare Enterprise
Utilidad de normalizacion de texto (quita tildes/diacriticos
y pasa a mayusculas) para permitir busquedas insensibles a
acentos en catalogos como DIVIPOLA, CUPS y CUM.
=========================================================
"""

import unicodedata


def normalizar(texto: str) -> str:
    if not texto:
        return ""

    sin_acentos = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))

    return sin_acentos.upper().strip()
