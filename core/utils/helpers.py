from uuid import uuid4

def generar_uuid()->str:
    return str(uuid4())

def limpiar_texto(texto:str)->str:
    return " ".join(texto.strip().split())
