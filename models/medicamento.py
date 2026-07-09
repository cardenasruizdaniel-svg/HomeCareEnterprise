from dataclasses import dataclass
@dataclass
class Medicamento:
    historia_id:int
    nombre:str=""
    dosis:str=""
    frecuencia:str=""
    via:str=""
