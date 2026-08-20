from database.database import consultar, consultar_uno, ejecutar

class HistoriaRepository:
    @staticmethod
    def listar():
        return consultar("SELECT * FROM historias_clinicas ORDER BY id DESC")

    @staticmethod
    def obtener_por_paciente(paciente_id:int):
        return consultar("SELECT * FROM historias_clinicas WHERE paciente_id=?", (paciente_id,))
