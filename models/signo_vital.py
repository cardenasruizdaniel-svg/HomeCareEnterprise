from dataclasses import dataclass
from datetime import datetime
@dataclass
class SignoVital:
    historia_id:int
    fecha:str=datetime.now().isoformat()
    ta:str=''
    fc:int=0
    fr:int=0
    temperatura:float=0.0
    saturacion:int=0
    peso:float=0.0
    talla:float=0.0
