"""HomeCare Enterprise - Repositorio: Catálogo de Bancos de Colombia"""

from database.database import consultar_escalar, consultar_todos, ejecutar

BANCOS_INICIALES = [
    "Bancolombia", "Davivienda", "Banco de Bogotá", "BBVA Colombia", "Banco Popular",
    "Banco Caja Social", "Banco AV Villas", "Banco Agrario de Colombia",
    "Scotiabank Colpatria", "Itaú Colombia", "Banco Falabella", "Banco Pichincha",
    "Banco Santander Colombia", "Banco Serfinanza", "Bancoomeva", "Banco W",
    "Nequi", "Daviplata", "Movii", "Lulo Bank", "RappiPay",
]


class CatalogoBancosRepository:

    @staticmethod
    def sembrar_si_vacio():
        total = consultar_escalar("SELECT COUNT(*) FROM catalogo_bancos")
        if total and total > 0:
            return
        for nombre in BANCOS_INICIALES:
            ejecutar("INSERT OR IGNORE INTO catalogo_bancos(nombre) VALUES (?)", (nombre,))

    @staticmethod
    def listar_activos():
        return consultar_todos("SELECT * FROM catalogo_bancos WHERE activo=1 ORDER BY nombre")

    @staticmethod
    def crear(nombre: str) -> int:
        return ejecutar("INSERT INTO catalogo_bancos(nombre) VALUES (?)", (nombre,))

    @staticmethod
    def desactivar(banco_id: int):
        ejecutar("UPDATE catalogo_bancos SET activo=0 WHERE id=?", (banco_id,))
