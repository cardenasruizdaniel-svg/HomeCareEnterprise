from repositories.diagnosticos_repository import DiagnosticosRepository
class DiagnosticosService:
    @staticmethod
    def buscar(texto:str):
        return DiagnosticosRepository.buscar(texto)

    @staticmethod
    def listar_por_paciente(paciente_id: int):
        return [dict(d) for d in DiagnosticosRepository.listar_por_paciente(paciente_id)]

    @staticmethod
    def listar_activos_por_paciente(paciente_id: int):
        return [dict(d) for d in DiagnosticosRepository.listar_activos_por_paciente(paciente_id)]

    @staticmethod
    def asignar(paciente_id, codigo_cie10, diagnostico, tipo, fecha_diagnostico,
                 profesional, especialidad, observaciones, usuario_id,
                 codigo_cups=None, descripcion_cups=None) -> int:

        if not diagnostico:
            raise ValueError("Debe indicar el diagnóstico.")

        return DiagnosticosRepository.crear({
            "paciente_id": paciente_id,
            "codigo_cie10": codigo_cie10 or None,
            "diagnostico": diagnostico,
            "tipo": tipo or "IMPRESION DIAGNOSTICA",
            "fecha_diagnostico": fecha_diagnostico,
            "profesional": profesional or "",
            "especialidad": especialidad or "",
            "observaciones": observaciones or "",
            "usuario_registro": usuario_id,
            "codigo_cups": codigo_cups or None,
            "descripcion_cups": descripcion_cups or None,
        })

    @staticmethod
    def resolver(diagnostico_id: int):
        DiagnosticosRepository.cambiar_estado(diagnostico_id, "Resuelto")

    @staticmethod
    def reactivar(diagnostico_id: int):
        DiagnosticosRepository.cambiar_estado(diagnostico_id, "Activo")
