"""HomeCare Enterprise - Servicio: Fotos de Procedimientos del Paciente"""

from repositories.fotos_procedimientos_repository import FotosProcedimientosRepository


def listar_por_paciente(paciente_id: int):
    return [dict(f) for f in FotosProcedimientosRepository.listar_por_paciente(paciente_id)]


def subir_foto(paciente_id: int, descripcion: str, foto_base64: str, profesional_id, usuario_id) -> int:
    if not foto_base64:
        raise ValueError("Debe seleccionar una foto para subir.")

    return FotosProcedimientosRepository.crear({
        "paciente_id": paciente_id,
        "descripcion": descripcion or "",
        "foto_base64": foto_base64,
        "profesional_id": profesional_id or None,
        "usuario_creacion": usuario_id,
    })


def eliminar_foto(foto_id: int):
    FotosProcedimientosRepository.eliminar(foto_id)
