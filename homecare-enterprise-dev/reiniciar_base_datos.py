"""
=========================================================
HomeCare Enterprise - Reiniciar base de datos en blanco

Deja la base de datos completamente limpia (sin pacientes,
profesionales, visitas, ni ningún dato de prueba), pero
CONSERVA el usuario administrador para poder volver a entrar
de inmediato, y vuelve a sembrar los catálogos de referencia
(programas de atención, actividades, EPS, bancos, DIVIPOLA,
CUPS, CUM, CIE-10) para que el sistema quede funcional desde
el primer momento.

Por seguridad, antes de borrar nada, se guarda una copia de
la base de datos actual con la fecha y hora en el nombre, por
si se necesita recuperar algo despues.

USO: python3 reiniciar_base_datos.py
(ejecutar desde la raíz del proyecto, con el entorno virtual activado)
=========================================================
"""

import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RUTA_BD = "database.db"

print("=" * 60)
print("HomeCare Enterprise - Reiniciar base de datos en blanco")
print("=" * 60)

if os.path.exists(RUTA_BD):
    marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
    respaldo = f"database_respaldo_{marca_tiempo}.db"
    shutil.copy2(RUTA_BD, respaldo)
    print(f"[OK] Se guardó una copia de seguridad de la base actual en: {respaldo}")

    # Se guardan los datos del usuario administrador ANTES de
    # borrar todo, para poder conservarlos exactamente igual
    # (mismo usuario y misma contraseña) en la base nueva.
    import sqlite3
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    admin_actual = conexion.execute(
        "SELECT usuario, password, nombre, rol FROM usuarios WHERE usuario='admin'"
    ).fetchone()
    conexion.close()

    os.remove(RUTA_BD)
    print("[OK] Base de datos anterior eliminada.")
else:
    admin_actual = None
    print("[..] No había una base de datos previa; se creará una nueva.")

from database.database import crear_tablas, ejecutar
from database.migrations import ejecutar_migraciones

crear_tablas()
ejecutar_migraciones()
print("[OK] Esquema creado.")

# Restaurar el usuario administrador que ya existía (misma
# contraseña de siempre), o crear uno nuevo con la contraseña
# por defecto si no existía ninguno.
if admin_actual:
    ejecutar(
        "INSERT INTO usuarios(nombre, usuario, password, rol, activo) VALUES (?, ?, ?, ?, 1)",
        (admin_actual["nombre"], admin_actual["usuario"], admin_actual["password"], admin_actual["rol"]),
    )
    print(f"[OK] Usuario administrador conservado: {admin_actual['usuario']} (misma contraseña de antes)")
else:
    from services.auth_service import AuthService
    ejecutar(
        "INSERT INTO usuarios(nombre, usuario, password, rol, activo) VALUES (?, ?, ?, ?, 1)",
        ("Administrador", "admin", AuthService.generar_hash("admin123"), "Administrador"),
    )
    print("[OK] Usuario administrador nuevo creado: admin / admin123 (cámbiela de inmediato)")

# Volver a sembrar los catálogos de referencia (no son "datos
# de prueba" -- son catálogos que el sistema necesita para
# funcionar: programas de atención, actividades, EPS, bancos,
# DIVIPOLA, CUPS, CUM, CIE-10).
from repositories.programas_atencion_repository import ProgramasAtencionRepository
from repositories.catalogo_actividades_repository import CatalogoActividadesRepository
from repositories.catalogo_eps_repository import CatalogoEPSRepository
from repositories.catalogo_bancos_repository import CatalogoBancosRepository
from repositories.catalogos_repository import DivipolaRepository, CUPSRepository, CUMRepository
from repositories import cie10_repository

ProgramasAtencionRepository.sembrar_si_vacio()
CatalogoActividadesRepository.sembrar_si_vacio()
CatalogoEPSRepository.sembrar_si_vacio()
CatalogoBancosRepository.sembrar_si_vacio()
DivipolaRepository.sembrar_si_vacio()
CUPSRepository.sembrar_si_vacio()
CUMRepository.sembrar_si_vacio()
cie10_repository.sembrar_si_vacio()
print("[OK] Catálogos de referencia sembrados (programas, actividades, EPS, bancos, DIVIPOLA, CUPS, CUM, CIE-10).")

print()
print("=" * 60)
print("BASE DE DATOS REINICIADA EN BLANCO CORRECTAMENTE")
print("=" * 60)
print()
print("La base de datos está completamente vacía de pacientes,")
print("profesionales, visitas e historias clínicas.")
print()
print("El usuario administrador se conservó — ya puede iniciar sesión.")
print()
print("Reinicie el programa (cierre y vuelva a abrir HomeCare Enterprise)")
print("para que tome la base de datos nueva.")
