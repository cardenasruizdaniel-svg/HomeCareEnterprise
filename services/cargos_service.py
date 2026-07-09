"""HomeCare Enterprise - Servicio: Cargos"""

from repositories.cargos_repository import CargosRepository

CARGOS_SUGERIDOS_IPS_DOMICILIARIA = [
    "Médico General", "Médico Especialista", "Enfermero Jefe",
    "Auxiliar de Enfermería", "Cuidador", "Fisioterapeuta",
    "Terapeuta Respiratorio", "Terapeuta Ocupacional", "Psicólogo",
    "Fonoaudiólogo", "Nutricionista", "Profesional en Salud Ocupacional",
    "Coordinador Asistencial", "Auxiliar Administrativo",
]


def listar(solo_activos: bool = True):
    return CargosRepository.listar(solo_activos)


def obtener(cargo_id: int):
    return CargosRepository.obtener(cargo_id)


def crear(datos: dict) -> int:
    if not datos.get("nombre"):
        raise ValueError("El cargo debe tener un nombre.")
    datos.setdefault("descripcion", "")
    datos.setdefault("documentos_requeridos", "")
    return CargosRepository.crear(datos)


def actualizar(cargo_id: int, datos: dict):
    return CargosRepository.actualizar(cargo_id, datos)


def desactivar(cargo_id: int):
    return CargosRepository.desactivar(cargo_id)
