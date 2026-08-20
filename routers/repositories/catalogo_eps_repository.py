"""
HomeCare Enterprise - Repositorio: Catálogo de EPS

IMPORTANTE: el listado de EPS habilitadas en Colombia cambia
con frecuencia (intervenciones, liquidaciones, y desde 2026 la
reorganizacion territorial del Decreto 0182 de 2026). La
siembra inicial es solo un punto de partida -- el
administrador debe revisar y actualizar este catalogo
periodicamente contra el listado oficial vigente en
supersalud.gov.co, agregando o desactivando segun corresponda.
"""

from database.database import consultar_escalar, consultar_todos, ejecutar

EPS_INICIALES = [
    "Nueva EPS", "EPS Sanitas", "EPS Sura", "Salud Total EPS", "Coosalud EPS",
    "Famisanar EPS", "Comfenalco Valle EPS", "S.O.S. (Servicio Occidental de Salud)",
    "Mutual Ser EPS", "Capital Salud EPS", "Asmet Salud EPS", "Emssanar EPS",
    "Cajacopi Atlántico EPS", "Comparta EPS", "Ecoopsos EPS", "Aliansalud EPS",
    "Mallamas EPS (Indígena)", "Dusakawi EPS (Indígena)", "Anas Wayuu EPS (Indígena)",
    "Pijaos Salud EPS (Indígena)", "Comfachocó EPS", "Capresoca EPS", "Savia Salud EPS",
    "Nueva EPS - Régimen Subsidiado", "Particular / Sin EPS",
]


class CatalogoEPSRepository:

    @staticmethod
    def sembrar_si_vacio():
        total = consultar_escalar("SELECT COUNT(*) FROM catalogo_eps")
        if total and total > 0:
            return
        for nombre in EPS_INICIALES:
            ejecutar("INSERT OR IGNORE INTO catalogo_eps(nombre) VALUES (?)", (nombre,))

    @staticmethod
    def listar_activas():
        return consultar_todos("SELECT * FROM catalogo_eps WHERE activo=1 ORDER BY nombre")

    @staticmethod
    def crear(nombre: str) -> int:
        return ejecutar("INSERT INTO catalogo_eps(nombre) VALUES (?)", (nombre,))

    @staticmethod
    def desactivar(eps_id: int):
        ejecutar("UPDATE catalogo_eps SET activo=0 WHERE id=?", (eps_id,))
