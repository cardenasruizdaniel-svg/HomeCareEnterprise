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
    def listar_por_rango_fechas(fecha_desde: str, fecha_hasta: str):
        """Todas las órdenes generadas entre dos fechas (inclusive), con el nombre del paciente y del profesional ya resueltos."""
        return consultar(
            """
            SELECT
                om.id, om.tipo, om.descripcion, om.estado, om.fecha_orden,
                om.enviado_whatsapp, om.enviado_correo,
                p.id AS paciente_id, p.primer_nombre AS paciente_primer_nombre, p.primer_apellido AS paciente_primer_apellido, p.documento AS paciente_documento,
                pr.id AS profesional_id, pr.primer_nombre AS profesional_primer_nombre, pr.primer_apellido AS profesional_primer_apellido, pr.especialidad_principal
            FROM ordenes_medicas om
            JOIN pacientes p ON p.id = om.paciente_id
            LEFT JOIN profesionales pr ON pr.id = om.profesional_id
            WHERE date(om.fecha_orden) >= date(?) AND date(om.fecha_orden) <= date(?)
            ORDER BY om.fecha_orden DESC
            """,
            (fecha_desde, fecha_hasta),
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
