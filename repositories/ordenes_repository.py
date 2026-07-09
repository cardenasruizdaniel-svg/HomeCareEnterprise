"""
=========================================================
HomeCare Enterprise
Repositorio: Ordenes Medicas
=========================================================
"""

from database.database import consultar, consultar_uno, ejecutar
import secrets


class OrdenesRepository:

    @staticmethod
    def listar(historia_id: int):
        return consultar(
            "SELECT * FROM ordenes_medicas WHERE historia_id=? ORDER BY fecha_orden DESC",
            (historia_id,),
        )

    @staticmethod
    def listar_por_paciente(paciente_id: int):
        return consultar(
            "SELECT * FROM ordenes_medicas WHERE paciente_id=? ORDER BY fecha_orden DESC",
            (paciente_id,),
        )

    @staticmethod
    def obtener(orden_id: int):
        return consultar_uno(
            "SELECT * FROM ordenes_medicas WHERE id=?",
            (orden_id,),
        )

    @staticmethod
    def obtener_por_token(orden_id: int, token: str):
        return consultar_uno(
            "SELECT * FROM ordenes_medicas WHERE id=? AND token_pdf=?",
            (orden_id, token),
        )

    @staticmethod
    def crear(datos: dict) -> int:
        datos = dict(datos)
        datos.setdefault("token_pdf", secrets.token_urlsafe(24))
        return ejecutar(
            """
            INSERT INTO ordenes_medicas(
                historia_id, paciente_id, profesional_id, tipo,
                descripcion, codigo_cups, estado, token_pdf, usuario_creacion
            ) VALUES (
                :historia_id, :paciente_id, :profesional_id, :tipo,
                :descripcion, :codigo_cups, :estado, :token_pdf, :usuario_creacion
            )
            """,
            datos,
        )

    @staticmethod
    def marcar_envio(orden_id: int, whatsapp: bool = None, correo: bool = None):

        if whatsapp is not None:
            ejecutar(
                "UPDATE ordenes_medicas SET enviado_whatsapp=? WHERE id=?",
                (1 if whatsapp else 0, orden_id),
            )

        if correo is not None:
            ejecutar(
                "UPDATE ordenes_medicas SET enviado_correo=? WHERE id=?",
                (1 if correo else 0, orden_id),
            )

    @staticmethod
    def cambiar_estado(orden_id: int, estado: str):
        ejecutar(
            "UPDATE ordenes_medicas SET estado=? WHERE id=?",
            (estado, orden_id),
        )
