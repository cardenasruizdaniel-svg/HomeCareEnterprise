from repositories.evolucion_repository import EvolucionRepository
class EvolucionService:
    @staticmethod
    def listar(historia_id:int):
        return EvolucionRepository.listar(historia_id)
