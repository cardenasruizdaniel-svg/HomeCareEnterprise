from database.database import consultar
class SignosRepository:
    @staticmethod
    def listar(historia_id:int):
        return consultar('SELECT * FROM signos_vitales WHERE historia_id=? ORDER BY fecha DESC',(historia_id,))
