from repositories.agenda_repository import AgendaRepository

class AgendaService:
    @staticmethod
    def agenda_semanal(profesional_id:int,inicio:str):
        return AgendaRepository.listar_profesional(profesional_id,inicio)

    @staticmethod
    def reprogramar(cita_id:int,nueva_fecha:str,nueva_hora:str):
        return {
            "cita_id":cita_id,
            "fecha":nueva_fecha,
            "hora":nueva_hora,
            "estado":"REPROGRAMADA"
        }
