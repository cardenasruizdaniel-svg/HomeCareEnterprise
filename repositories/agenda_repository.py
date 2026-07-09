from database.database import consultar, consultar_uno, ejecutar

class AgendaRepository:

    @staticmethod
    def listar_por_fecha(fecha:str):
        return consultar(
            "SELECT * FROM programacion WHERE fecha=? ORDER BY hora",
            (fecha,)
        )

    @staticmethod
    def listar_profesional(profesional_id:int, fecha:str):
        return consultar(
            "SELECT * FROM programacion WHERE profesional_id=? AND fecha=? ORDER BY hora",
            (profesional_id, fecha)
        )

    @staticmethod
    def validar_cruce(profesional_id:int, fecha:str, hora:str):
        return consultar_uno(
            "SELECT id FROM programacion WHERE profesional_id=? AND fecha=? AND hora=?",
            (profesional_id, fecha, hora)
        )

    @staticmethod
    def crear(sql:str,parametros:tuple):
        return ejecutar(sql,parametros)
