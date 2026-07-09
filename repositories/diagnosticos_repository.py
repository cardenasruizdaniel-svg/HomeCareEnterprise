from database.database import consultar, consultar_todos, consultar_uno, ejecutar


class DiagnosticosRepository:
    @staticmethod
    def buscar(texto:str):
        from core.texto_utils import normalizar
        texto_normalizado = normalizar(texto)
        return consultar(
            "SELECT * FROM cie10 WHERE activo=1 AND (codigo LIKE ? OR descripcion_normalizada LIKE ?)",
            (f'%{texto}%', f'%{texto_normalizado}%'),
        )

    # ==========================================
    # CRUD de diagnosticos asignados al paciente
    # (la tabla "diagnosticos" ya existia, pero
    # nunca se habia construido la forma de usarla)
    # ==========================================

    @staticmethod
    def listar_por_paciente(paciente_id: int):
        return consultar_todos(
            "SELECT * FROM diagnosticos WHERE paciente_id=? ORDER BY fecha_diagnostico DESC",
            (paciente_id,),
        )

    @staticmethod
    def listar_activos_por_paciente(paciente_id: int):
        return consultar_todos(
            "SELECT * FROM diagnosticos WHERE paciente_id=? AND estado='Activo' ORDER BY fecha_diagnostico DESC",
            (paciente_id,),
        )

    @staticmethod
    def obtener(diagnostico_id: int):
        return consultar_uno("SELECT * FROM diagnosticos WHERE id=?", (diagnostico_id,))

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO diagnosticos(
                paciente_id, codigo_cie10, diagnostico, tipo, fecha_diagnostico,
                profesional, especialidad, observaciones, usuario_registro,
                codigo_cups, descripcion_cups
            ) VALUES (
                :paciente_id, :codigo_cie10, :diagnostico, :tipo, :fecha_diagnostico,
                :profesional, :especialidad, :observaciones, :usuario_registro,
                :codigo_cups, :descripcion_cups
            )
            """,
            datos,
        )

    @staticmethod
    def cambiar_estado(diagnostico_id: int, estado: str):
        ejecutar(
            "UPDATE diagnosticos SET estado=?, fecha_actualizacion=CURRENT_TIMESTAMP WHERE id=?",
            (estado, diagnostico_id),
        )
