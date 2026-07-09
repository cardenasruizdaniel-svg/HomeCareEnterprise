"""
HomeCare Enterprise
Sprint 1.1 - Modelo Paciente
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Paciente:
    id: Optional[int]=None
    tipo_documento:str=""
    documento:str=""
    primer_nombre:str=""
    segundo_nombre:str=""
    primer_apellido:str=""
    segundo_apellido:str=""
    fecha_nacimiento:str=""
    sexo:str=""
    eps:str=""
    regimen:str=""
    tipo_cuidado:str="No Ventilado"
    telefono:str=""
    celular:str=""
    correo:str=""
    direccion:str=""
    barrio:str=""
    municipio:str=""
    departamento:str=""
    latitud:float=None
    longitud:float=None
    codigo_municipio_divipola:str=""
    estado:str="ACTIVO"
    fecha_registro:str=field(default_factory=lambda: datetime.now().isoformat())

    @property
    def nombre_completo(self)->str:
        return " ".join(x for x in [
            self.primer_nombre,
            self.segundo_nombre,
            self.primer_apellido,
            self.segundo_apellido] if x)

    def validar(self)->list[str]:
        errores=[]
        if not self.documento:
            errores.append("Documento obligatorio")
        if not self.primer_nombre:
            errores.append("Primer nombre obligatorio")
        if not self.primer_apellido:
            errores.append("Primer apellido obligatorio")
        return errores

    def to_dict(self)->dict:
        return self.__dict__.copy()
