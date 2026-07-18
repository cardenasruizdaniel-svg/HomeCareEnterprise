from repositories.historia_repository import HistoriaRepository

class HistoriaService:
    @staticmethod
    def listar():
        return HistoriaRepository.listar()

    @staticmethod
    def historias_paciente(paciente_id:int):
        return HistoriaRepository.obtener_por_paciente(paciente_id)
