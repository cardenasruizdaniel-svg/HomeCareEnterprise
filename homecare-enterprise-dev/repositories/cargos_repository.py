"""
=========================================================
HomeCare Enterprise
Repositorio: Cargos (puestos de trabajo)
=========================================================
"""

from database.database import consultar_todos, consultar_uno, ejecutar


class CargosRepository:

    @staticmethod
    def listar(solo_activos: bool = True):
        if solo_activos:
            return consultar_todos("SELECT * FROM cargos WHERE activo=1 ORDER BY nombre")
        return consultar_todos("SELECT * FROM cargos ORDER BY nombre")

    @staticmethod
    def obtener(cargo_id: int):
        return consultar_uno("SELECT * FROM cargos WHERE id=?", (cargo_id,))

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO cargos (
                nombre, descripcion, tipo_contrato_sugerido, salario_base,
                valor_hora_base, periodicidad_pago, nivel_riesgo_arl, documentos_requeridos
            ) VALUES (
                :nombre, :descripcion, :tipo_contrato_sugerido, :salario_base,
                :valor_hora_base, :periodicidad_pago, :nivel_riesgo_arl, :documentos_requeridos
            )
            """,
            datos,
        )

    @staticmethod
    def actualizar(cargo_id: int, datos: dict):
        datos = dict(datos)
        datos["id"] = cargo_id
        ejecutar(
            """
            UPDATE cargos SET
                nombre=:nombre, descripcion=:descripcion,
                tipo_contrato_sugerido=:tipo_contrato_sugerido,
                salario_base=:salario_base, valor_hora_base=:valor_hora_base,
                periodicidad_pago=:periodicidad_pago, nivel_riesgo_arl=:nivel_riesgo_arl,
                documentos_requeridos=:documentos_requeridos
            WHERE id=:id
            """,
            datos,
        )

    @staticmethod
    def desactivar(cargo_id: int):
        ejecutar("UPDATE cargos SET activo=0 WHERE id=?", (cargo_id,))
