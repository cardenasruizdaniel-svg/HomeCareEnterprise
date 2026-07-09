from dataclasses import dataclass
from datetime import datetime
from typing import Optional
@dataclass
class HistoriaClinica:
    id:Optional[int]=None
    paciente_id:int=0
    profesional_id:int=0
    fecha_apertura:str=datetime.now().isoformat()
    estado:str='ABIERTA'
