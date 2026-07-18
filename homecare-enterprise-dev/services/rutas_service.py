from repositories.rutas_repository import RutasRepository

class RutasService:
    @staticmethod
    def generar_ruta(profesional_id:int,fecha:str):
        visitas=RutasRepository.visitas_dia(profesional_id,fecha)
        for i,v in enumerate(visitas,1):
            v["orden"]=i
        return visitas
