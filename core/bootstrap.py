"""
=========================================================
HomeCare Enterprise
Bootstrap del Sistema
Versión 7.2.0
=========================================================
"""

from pathlib import Path

from core.config import BASE_DIR

from database.database import (
    get_connection,
    crear_tablas,
)

from database.migrations import ejecutar_migraciones


DIRECTORIOS = [

    "logs",

    "uploads",

    "exports",

    "backups",

    "temp",

    "static/documentos",

    "static/firmas",

]


def crear_directorios():

    for carpeta in DIRECTORIOS:

        Path(BASE_DIR / carpeta).mkdir(
            parents=True,
            exist_ok=True,
        )


def crear_usuario_admin():

    from services.auth_service import AuthService

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT COUNT(*)

        FROM usuarios

        WHERE usuario='admin'

    """)

    existe = cursor.fetchone()[0]

    if existe == 0:

        password_cifrada = AuthService.generar_hash("admin123")

        cursor.execute("""

            INSERT INTO usuarios(

                nombre,
                usuario,
                password,
                rol

            )

            VALUES(

                'Administrador',
                'admin',
                ?,
                'Administrador'

            )

        """, (password_cifrada,))

        conexion.commit()

        print("[OK] Usuario administrador creado.")

    else:

        # Reparacion automatica: si el admin ya existe pero su
        # contraseña quedo guardada en texto plano (bug de una
        # version anterior de este instalador, antes de que se
        # cifrara con bcrypt), se corrige sola sin perder el
        # resto de la informacion ya cargada en el sistema.

        cursor.execute("SELECT password FROM usuarios WHERE usuario='admin'")

        password_actual = cursor.fetchone()[0]

        es_hash_valido = isinstance(password_actual, str) and password_actual.startswith(("$2a$", "$2b$", "$2y$"))

        if not es_hash_valido:

            password_cifrada = AuthService.generar_hash("admin123")

            cursor.execute(
                "UPDATE usuarios SET password=? WHERE usuario='admin'",
                (password_cifrada,),
            )

            conexion.commit()

            print("[OK] Se reparo la contraseña del administrador (quedo en texto plano por una version anterior). Sigue siendo 'admin123'.")

    conexion.close()


def iniciar_sistema():

    print("\n====================================")

    print(" HOMECARE ENTERPRISE")

    print(" Inicializando sistema...")

    print("====================================")

    crear_directorios()

    # -------------------------------------------------
    # CREA TODAS LAS TABLAS DEL SCHEMA
    # -------------------------------------------------

    crear_tablas()

    # -------------------------------------------------
    # EJECUTA MIGRACIONES
    # -------------------------------------------------

    ejecutar_migraciones()

    # -------------------------------------------------
    # CREA ADMIN SI NO EXISTE
    # -------------------------------------------------

    crear_usuario_admin()

    # -------------------------------------------------
    # SIEMBRA DE CATALOGOS (DIVIPOLA / CUPS / CUM)
    # -------------------------------------------------

    from repositories.catalogos_repository import (
        CUMRepository,
        CUPSRepository,
        DivipolaRepository,
    )

    nuevos_divipola = DivipolaRepository.sembrar_si_vacio()
    nuevos_cups = CUPSRepository.sembrar_si_vacio()
    nuevos_cum = CUMRepository.sembrar_si_vacio()

    from repositories import cie10_repository
    nuevos_cie10 = cie10_repository.sembrar_si_vacio()

    if nuevos_divipola or nuevos_cups or nuevos_cum or nuevos_cie10:
        print(
            f"Catalogos sembrados: DIVIPOLA={nuevos_divipola}, "
            f"CUPS={nuevos_cups}, CUM={nuevos_cum}, CIE10={nuevos_cie10}"
        )

    from repositories.programas_atencion_repository import ProgramasAtencionRepository
    ProgramasAtencionRepository.sembrar_si_vacio()

    from repositories.catalogo_actividades_repository import CatalogoActividadesRepository
    CatalogoActividadesRepository.sembrar_si_vacio()

    from repositories.catalogo_eps_repository import CatalogoEPSRepository
    CatalogoEPSRepository.sembrar_si_vacio()

    from repositories.catalogo_bancos_repository import CatalogoBancosRepository
    CatalogoBancosRepository.sembrar_si_vacio()

    from repositories.turnos_repository import CatalogoTurnosRepository
    CatalogoTurnosRepository.sembrar_si_vacio()

    print()

    print("[OK] Sistema listo.")
    print()