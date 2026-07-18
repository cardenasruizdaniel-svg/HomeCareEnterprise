from repositories.medicamentos_repository import MedicamentosRepository
class MedicamentosService:
    @staticmethod
    def listar(historia_id:int):
        return MedicamentosRepository.listar(historia_id)
