from database.database import consultar,ejecutar
class EvolucionRepository:
    @staticmethod
    def listar(historia_id:int):
        return consultar("SELECT * FROM evoluciones WHERE historia_id=?",(historia_id,))
