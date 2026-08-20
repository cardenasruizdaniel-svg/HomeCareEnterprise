from database.database import consultar
class RutasRepository:
    @staticmethod
    def visitas_dia(profesional_id:int,fecha:str):
        return consultar(
            "SELECT * FROM programacion WHERE profesional_id=? AND fecha=? ORDER BY hora",
            (profesional_id,fecha)
        )
