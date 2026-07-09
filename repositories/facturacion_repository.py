"""HomeCare Enterprise - Repositorio: Facturacion electronica"""

from database.database import consultar_escalar, consultar_todos, consultar_uno, ejecutar


class FacturacionRepository:

    @staticmethod
    def siguiente_numero(prefijo: str) -> int:
        maximo = consultar_escalar(
            "SELECT MAX(numero) FROM facturas_electronicas WHERE prefijo=?",
            (prefijo,),
        )
        return (maximo or 0) + 1

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO facturas_electronicas (
                prefijo, numero, copago_id, paciente_id, valor_subtotal,
                valor_iva, valor_total, forma_pago, medio_pago, cufe,
                estado, xml_path, pdf_path, usuario_creacion
            ) VALUES (
                :prefijo, :numero, :copago_id, :paciente_id, :valor_subtotal,
                :valor_iva, :valor_total, :forma_pago, :medio_pago, :cufe,
                :estado, :xml_path, :pdf_path, :usuario_creacion
            )
            """,
            datos,
        )

    @staticmethod
    def listar_por_paciente(paciente_id: int):
        return consultar_todos(
            "SELECT * FROM facturas_electronicas WHERE paciente_id=? ORDER BY fecha_emision DESC",
            (paciente_id,),
        )

    @staticmethod
    def listar_todas():
        return consultar_todos(
            """
            SELECT f.*, p.primer_nombre, p.primer_apellido, p.documento
            FROM facturas_electronicas f
            JOIN pacientes p ON p.id = f.paciente_id
            ORDER BY f.fecha_emision DESC
            """
        )

    @staticmethod
    def obtener(factura_id: int):
        return consultar_uno("SELECT * FROM facturas_electronicas WHERE id=?", (factura_id,))

    @staticmethod
    def actualizar_pdf_path(factura_id: int, pdf_path: str):
        ejecutar(
            "UPDATE facturas_electronicas SET pdf_path=? WHERE id=?",
            (pdf_path, factura_id),
        )
