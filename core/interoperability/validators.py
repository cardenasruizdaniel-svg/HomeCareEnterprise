import re

def validar_documento(doc:str)->bool:
    return bool(re.fullmatch(r"[A-Za-z0-9]{5,20}",doc))

def validar_email(email:str)->bool:
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+",email))
