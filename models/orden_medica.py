from dataclasses import dataclass
@dataclass
class OrdenMedica:
    historia_id:int
    profesional_id:int
    tipo:str=""
    descripcion:str=""
    estado:str="PENDIENTE"
