from dataclasses import dataclass

@dataclass
class Disponibilidad:
    profesional_id:int
    dia_semana:int
    hora_inicio:str
    hora_fin:str
    activo:bool=True
