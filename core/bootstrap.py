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

    # --------------------------------------------------
    # DIAGNÓSTICO TEMPORAL -- para encontrar por qué el
    # login de admin/admin123 no está funcionando en Render
    # aunque localmente sí funciona. Se puede quitar este
    # bloque una vez se resuelva.
    # --------------------------------------------------
    from database.db_backend import ES_POSTGRES
    from database.database import DB_PATH
    print(f"[DIAGNOSTICO] ¿Usando PostgreSQL?: {ES_POSTGRES}")
    print(f"[DIAGNOSTICO] Ruta del archivo SQLite (si aplica): {DB_PATH}")

    conexion = get_connection()

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT COUNT(*)

        FROM usuarios

        WHERE usuario='admin'

    """)

    existe = cursor.fetchone()[0]
    print(f"[DIAGNOSTICO] ¿Ya existe una fila con usuario='admin'?: {existe}")

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

        # Reparacion automatica: SOLO si la contraseña quedó
        # guardada en texto plano (bug de una version anterior
        # de este instalador, antes de que se cifrara con
        # bcrypt) o de alguna otra forma que no sea un hash de
        # bcrypt válido -- en ese caso sí se corrige sola, sin
        # perder el resto de la información ya cargada.
        #
        # A propósito, esto YA NO revisa si la contraseña
        # coincide con "admin123": si el administrador (o un
        # script de datos de prueba) cambió la contraseña a
        # propósito por una distinta, esa decisión se respeta
        # -- forzarla de vuelta a "admin123" en cada arranque
        # deshacía cualquier cambio de contraseña real que se
        # hiciera por seguridad, lo cual es exactamente lo
        # contrario de lo que se busca.

        cursor.execute("SELECT password FROM usuarios WHERE usuario='admin'")

        password_actual = cursor.fetchone()[0]

        es_hash_valido = isinstance(password_actual, str) and password_actual.startswith(("$2a$", "$2b$", "$2y$"))

        necesita_reparacion = not es_hash_valido

        # Recuperación deliberada: si alguien queda bloqueado
        # fuera del sistema (olvidó la contraseña, o quedó una
        # de una prueba anterior sin anotar), se puede forzar el
        # restablecimiento agregando la variable de entorno
        # RESETEAR_PASSWORD_ADMIN=true en Render (o en el
        # sistema local) y reiniciando -- a diferencia del
        # comportamiento anterior, esto NO pasa solo en cada
        # arranque: hay que pedirlo a propósito, y se recomienda
        # quitar la variable después de recuperar el acceso.
        import os as _os_recuperacion
        recuperacion_solicitada = _os_recuperacion.environ.get("RESETEAR_PASSWORD_ADMIN", "").strip().lower() == "true"

        if recuperacion_solicitada:
            necesita_reparacion = True

        if necesita_reparacion:

            password_cifrada = AuthService.generar_hash("admin123")

            cursor.execute(
                "UPDATE usuarios SET password=? WHERE usuario='admin'",
                (password_cifrada,),
            )

            conexion.commit()

            if recuperacion_solicitada:
                print("[OK] Se restableció la contraseña del administrador a 'admin123' porque se pidió explícitamente con RESETEAR_PASSWORD_ADMIN=true. Recuerde quitar esa variable de entorno después de recuperar el acceso.")
            else:
                print("[OK] Se reparó la contraseña del administrador (estaba guardada en un formato no válido). Ahora es 'admin123'.")

    # El administrador nunca debe quedar bloqueado por intentos
    # fallidos ni inactivo -- cada vez que arranca el sistema se
    # asegura de que la cuenta admin esté totalmente disponible,
    # sin importar lo que haya pasado en arranques anteriores
    # (pruebas de conexión, intentos fallidos durante soporte
    # técnico, etc.).
    cursor.execute(
        "UPDATE usuarios SET intentos_fallidos=0, bloqueado_hasta=NULL, estado='Activo', activo=1 WHERE usuario='admin'"
    )
    conexion.commit()

    # --------------------------------------------------
    # DIAGNÓSTICO TEMPORAL -- muestra el estado final real
    # de la fila del admin, tal como queda guardada, y si
    # bcrypt confirma que "admin123" coincide con lo guardado.
    # --------------------------------------------------
    cursor.execute("SELECT id, usuario, estado, activo, rol, password FROM usuarios WHERE usuario='admin'")
    fila_final = cursor.fetchone()
    if fila_final:
        print(f"[DIAGNOSTICO] Fila final del admin -> id={fila_final[0]}, usuario={fila_final[1]!r}, estado={fila_final[2]!r}, activo={fila_final[3]!r}, rol={fila_final[4]!r}")
        print(f"[DIAGNOSTICO] Hash guardado empieza con: {str(fila_final[5])[:10]}...")
        try:
            import bcrypt as _bcrypt_diagnostico
            hash_guardado = fila_final[5]
            if isinstance(hash_guardado, str):
                hash_guardado = hash_guardado.encode("utf-8")
            coincide = _bcrypt_diagnostico.checkpw("admin123".encode("utf-8"), hash_guardado)
            print(f"[DIAGNOSTICO] ¿bcrypt confirma que 'admin123' coincide con el hash guardado?: {coincide}")
        except Exception as error_verificacion:
            print(f"[DIAGNOSTICO] ERROR al verificar la contraseña: {error_verificacion}")
    else:
        print("[DIAGNOSTICO] ¡No se encontró NINGUNA fila con usuario='admin' después de crear_usuario_admin()!")

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

    from repositories.catalogo_examenes_laboratorio_repository import sembrar_si_vacio as sembrar_examenes_lab
    sembrar_examenes_lab()

    try:
        from services.capacitacion_service import sembrar_manuales_existentes, asegurar_tokens_visor
        manuales_sembrados = sembrar_manuales_existentes()
        if manuales_sembrados:
            print(f"[OK] Módulo de Capacitación: se registraron {len(manuales_sembrados)} manual(es) inicial(es).")
        asegurar_tokens_visor()
    except Exception as error:
        print(f"[AVISO] No se pudo sembrar el módulo de Capacitación: {error}")

    try:
        from services.recomendaciones_examenes_service import sembrar_recomendaciones_estandar
        recomendaciones_sembradas = sembrar_recomendaciones_estandar()
        if recomendaciones_sembradas:
            print(f"[OK] Recomendaciones e Instrucciones: se registraron {len(recomendaciones_sembradas)} recomendación(es) estándar.")
    except Exception as error:
        print(f"[AVISO] No se pudo sembrar las Recomendaciones e Instrucciones: {error}")

    try:
        from services.configuracion_web_service import sembrar_servicios_estandar, actualizar_servicios_con_catalogo_real, completar_con_datos_reales_si_vacio
        servicios_sembrados = sembrar_servicios_estandar()
        if servicios_sembrados:
            print(f"[OK] Portal Web: se registraron {len(servicios_sembrados)} servicio(s) estándar.")
        resultado_actualizacion = actualizar_servicios_con_catalogo_real()
        if resultado_actualizacion["creados"] or resultado_actualizacion["ocultados"]:
            print(f"[OK] Portal Web: se ajustó el catálogo al listado real ({len(resultado_actualizacion['creados'])} agregados, {len(resultado_actualizacion['ocultados'])} genéricos ocultados).")
        campos_completados = completar_con_datos_reales_si_vacio()
        if campos_completados:
            print(f"[OK] Portal Web: se completaron {len(campos_completados)} campo(s) vacío(s) con la información real de la empresa.")
    except Exception as error:
        print(f"[AVISO] No se pudo sembrar los servicios del Portal Web: {error}")

    print()

    print("[OK] Sistema listo.")
    print()