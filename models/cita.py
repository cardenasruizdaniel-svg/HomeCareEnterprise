from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Cita:
    id: Optional[int]=None
    paciente_id:int=0
    profesional_id:int=0
    fecha:str=""
    hora_inicio:str=""
    hora_fin:str=""
    servicio:str=""
    estado:str="PROGRAMADA"
    direccion:str=""
    latitud:float=0.0
    longitud:float=0.0
    observaciones:str=""
    creado_en:str=datetime.now().isoformat()
