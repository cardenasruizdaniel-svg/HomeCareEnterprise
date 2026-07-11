"""
HomeCare Enterprise - Reinicio de la base de datos (desde la web)

A diferencia del script reiniciar_base_datos.py (que borra el
archivo completo y solo se puede correr con el programa
cerrado), esta version funciona con el servidor CORRIENDO:
vacía todas las tablas por SQL, conservando la tabla de
usuarios intacta (para no perder ninguna cuenta de acceso), y
vuelve a sembrar los catálogos de referencia. Es la forma
segura de hacerlo sin tocar el archivo de la base de datos
mientras esta en uso (en Windows, borrar un archivo abierto
falla).

Solo debe estar disponible para el Administrador maestro,
justo antes de lanzar el programa a producción real.
"""

from database.database import consultar_todos, ejecutar, get_connection

# Tablas que NUNCA se vacian en un reinicio: la de usuarios
# (para no perder ninguna cuenta de acceso) y las internas de
# SQLite.
TABLAS_PROTEGIDAS = {"usuarios", "sqlite_sequence"}


def reiniciar_base_datos_en_blanco(usuario_id=None) -> dict:
    """
    Deja el sistema como recien instalado: sin pacientes,
    profesionales, visitas, historias clinicas, ni ningun dato
    de prueba -- pero CONSERVA todos los usuarios (cuentas de
    acceso) tal cual estaban, y vuelve a sembrar los catalogos
    de referencia para que el sistema quede funcional de
    inmediato.
    """

    filas_tablas = consultar_todos(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tablas = [dict(f)["name"] for f in filas_tablas]

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF")

    tablas_vaciadas = []
    for tabla in tablas:
        if tabla in TABLAS_PROTEGIDAS:
            continue
        cursor.execute(f"DELETE FROM {tabla}")
        tablas_vaciadas.append(tabla)

    # Reinicia los contadores de autoincremento de las tablas
    # que se vaciaron, para que los IDs vuelvan a empezar desde 1.
    for tabla in tablas_vaciadas:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name=?", (tabla,))

    conexion.commit()
    conexion.close()

    # Vuelve a sembrar los catálogos de referencia (no son
    # "datos de prueba" -- el sistema los necesita para
    # funcionar: programas de atencion, actividades, EPS,
    # bancos, DIVIPOLA, CUPS, CUM, CIE-10, turnos).
    from repositories.programas_atencion_repository import ProgramasAtencionRepository
    from repositories.catalogo_actividades_repository import CatalogoActividadesRepository
    from repositories.catalogo_eps_repository import CatalogoEPSRepository
    from repositories.catalogo_bancos_repository import CatalogoBancosRepository
    from repositories.catalogos_repository import DivipolaRepository, CUPSRepository, CUMRepository
    from repositories.turnos_repository import CatalogoTurnosRepository
    from repositories import cie10_repository
    from repositories.catalogo_examenes_laboratorio_repository import sembrar_si_vacio as sembrar_examenes_lab

    ProgramasAtencionRepository.sembrar_si_vacio()
    CatalogoActividadesRepository.sembrar_si_vacio()
    CatalogoEPSRepository.sembrar_si_vacio()
    CatalogoBancosRepository.sembrar_si_vacio()
    DivipolaRepository.sembrar_si_vacio()
    CUPSRepository.sembrar_si_vacio()
    CUMRepository.sembrar_si_vacio()
    CatalogoTurnosRepository.sembrar_si_vacio()
    cie10_repository.sembrar_si_vacio()
    sembrar_examenes_lab()

    from database.database import consultar_escalar
    total_usuarios = consultar_escalar("SELECT COUNT(*) FROM usuarios")

    return {
        "tablas_vaciadas": len(tablas_vaciadas),
        "usuarios_conservados": total_usuarios,
    }
