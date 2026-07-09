"""
=========================================================
HomeCare Enterprise
Repositorio: Documentos del profesional (titulos, cursos,
certificaciones, RETHUS, etc.)
=========================================================
"""

from database.database import consultar_todos, consultar_uno, ejecutar


class DocumentosProfesionalRepository:

    @staticmethod
    def listar_por_profesional(profesional_id: int):
        return consultar_todos(
            "SELECT * FROM documentos_profesional WHERE profesional_id=? ORDER BY fecha_vencimiento",
            (profesional_id,),
        )

    @staticmethod
    def obtener(documento_id: int):
        return consultar_uno("SELECT * FROM documentos_profesional WHERE id=?", (documento_id,))

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO documentos_profesional (
                profesional_id, tipo_documento, nombre, numero, entidad_emisora,
                fecha_expedicion, fecha_vencimiento, ruta_archivo, observaciones, usuario_creacion
            ) VALUES (
                :profesional_id, :tipo_documento, :nombre, :numero, :entidad_emisora,
                :fecha_expedicion, :fecha_vencimiento, :ruta_archivo, :observaciones, :usuario_creacion
            )
            """,
            datos,
        )

    @staticmethod
    def eliminar(documento_id: int):
        ejecutar("DELETE FROM documentos_profesional WHERE id=?", (documento_id,))

    @staticmethod
    def vencidos_o_por_vencer(dias: int = 30):
        return consultar_todos(
            """
            SELECT d.*, pf.nombre_completo, pf.documento AS documento_profesional
            FROM documentos_profesional d
            JOIN profesionales pf ON pf.id = d.profesional_id
            WHERE d.fecha_vencimiento IS NOT NULL
              AND date(d.fecha_vencimiento) <= date('now', '+' || ? || ' days')
            ORDER BY d.fecha_vencimiento
            """,
            (dias,),
        )
