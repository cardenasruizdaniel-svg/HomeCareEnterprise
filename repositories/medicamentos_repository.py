from database.database import consultar


class MedicamentosRepository:
    @staticmethod
    def listar(historia_id:int):
        return consultar("SELECT * FROM medicamentos WHERE historia_id=?",(historia_id,))


def listar_activos(paciente_id: int):
    """
    Medicamentos activos de un paciente (por paciente_id, no
    por historia_id). Usado por el motor de alertas
    farmacologicas al formular un nuevo medicamento.
    """
    return consultar(
        "SELECT * FROM medicamentos WHERE paciente_id=? AND estado='ACTIVO'",
        (paciente_id,),
    )
