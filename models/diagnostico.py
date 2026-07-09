from dataclasses import dataclass
@dataclass
class Diagnostico:
    historia_id:int
    codigo:str=""
    descripcion:str=""
    principal:bool=False
