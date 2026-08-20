"""HomeCare Enterprise - Repositorio: Historial de documentos del paciente"""

from database.database import consultar_todos, consultar_uno, ejecutar


class HistorialDocumentosRepository:

    @staticmethod
    def listar_por_paciente(paciente_id: int):
        return consultar_todos(
            "SELECT * FROM historial_documentos_paciente "
            "WHERE paciente_id=? ORDER BY fecha_inicio_vigencia DESC",
            (paciente_id,),
        )

    @staticmethod
    def obtener_principal(paciente_id: int):
        return consultar_uno(
            "SELECT * FROM historial_documentos_paciente "
            "WHERE paciente_id=? AND es_principal=1",
            (paciente_id,),
        )

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO historial_documentos_paciente(
                paciente_id, tipo_documento, numero_documento,
                fecha_inicio_vigencia, fecha_fin_vigencia, es_principal,
                motivo_cambio, usuario_creacion
            ) VALUES (
                :paciente_id, :tipo_documento, :numero_documento,
                :fecha_inicio_vigencia, :fecha_fin_vigencia, :es_principal,
                :motivo_cambio, :usuario_creacion
            )
            """,
            datos,
        )

    @staticmethod
    def cerrar_vigencia(historial_id: int, fecha_fin: str):
        ejecutar(
            "UPDATE historial_documentos_paciente "
            "SET fecha_fin_vigencia=?, es_principal=0 WHERE id=?",
            (fecha_fin, historial_id),
        )

    @staticmethod
    def marcar_principal(paciente_id: int, historial_id: int):
        ejecutar(
            "UPDATE historial_documentos_paciente SET es_principal=0 WHERE paciente_id=?",
            (paciente_id,),
        )
        ejecutar(
            "UPDATE historial_documentos_paciente SET es_principal=1, fecha_fin_vigencia=NULL WHERE id=?",
            (historial_id,),
        )

    @staticmethod
    def documento_vigente_en_fecha(paciente_id: int, fecha: str):
        return consultar_uno(
            """
            SELECT * FROM historial_documentos_paciente
            WHERE paciente_id=?
              AND fecha_inicio_vigencia <= ?
              AND (fecha_fin_vigencia IS NULL OR fecha_fin_vigencia >= ?)
            ORDER BY fecha_inicio_vigencia DESC
            LIMIT 1
            """,
            (paciente_id, fecha, fecha),
        )
