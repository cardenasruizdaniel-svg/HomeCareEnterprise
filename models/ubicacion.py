from dataclasses import dataclass
@dataclass
class Ubicacion:
    paciente_id:int
    latitud:float
    longitud:float
    direccion:str=""
