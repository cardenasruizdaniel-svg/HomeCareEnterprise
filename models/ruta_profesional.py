from dataclasses import dataclass
@dataclass
class RutaProfesional:
    profesional_id:int
    fecha:str
    paciente_id:int
    orden:int=0
    distancia_km:float=0.0
    tiempo_min:int=0
    latitud:float=0.0
    longitud:float=0.0
