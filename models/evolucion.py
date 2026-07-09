from dataclasses import dataclass
from datetime import datetime
@dataclass
class Evolucion:
    historia_id:int
    profesional_id:int
    nota:str=""
    plan:str=""
    fecha:str=datetime.now().isoformat()
