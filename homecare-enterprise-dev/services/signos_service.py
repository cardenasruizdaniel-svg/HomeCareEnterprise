from repositories.signos_repository import SignosRepository
class SignosService:
    @staticmethod
    def listar(historia_id:int):
        return SignosRepository.listar(historia_id)
