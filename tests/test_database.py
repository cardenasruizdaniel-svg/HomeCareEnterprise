"""
HomeCare Enterprise - Pruebas de base de datos

Confirman que las migraciones dejan el esquema en el estado
esperado, y que el mecanismo de auto-reparación funciona ante
una base de datos dañada -- sin esto, un problema silencioso
aquí puede tumbar TODO el sistema al arrancar.
"""


class TestMigraciones:

    def test_las_tablas_del_sistema_de_calidad_existen(self, client):
        from database.database import consultar_uno
        tablas_esperadas = [
            "normas_regulatorias", "pamec_ciclos", "auditorias_calidad",
            "hallazgos_calidad", "acciones_mejora", "matriz_riesgos",
            "eventos_seguridad_paciente", "pqr_eventos",
            "configuracion_web", "servicios_web",
        ]
        for tabla in tablas_esperadas:
            fila = consultar_uno("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,))
            assert fila is not None, f"La tabla '{tabla}' debería existir después de las migraciones"

    def test_calidad_pqr_tiene_las_columnas_nuevas(self, client):
        from database.database import consultar_todos
        columnas = [dict(c)["name"] for c in consultar_todos("PRAGMA table_info(calidad_pqr)")]
        for columna in ("radicado", "riesgo", "canal", "fecha_limite", "clave_seguimiento"):
            assert columna in columnas, f"calidad_pqr debería tener la columna '{columna}'"

    def test_correr_las_migraciones_dos_veces_no_falla(self, client):
        """Las migraciones deben ser seguras de correr repetidamente (cada arranque del sistema las vuelve a correr)."""
        from core.bootstrap import iniciar_sistema
        iniciar_sistema()
        iniciar_sistema()  # No debería lanzar ningún error


class TestAutoReparacion:

    def test_se_repara_sola_una_base_de_datos_completamente_invalida(self, tmp_path, monkeypatch):
        import database.database as db_module

        ruta_prueba = tmp_path / "database_prueba.db"
        ruta_prueba.write_bytes(b"esto no es una base de datos SQLite valida" * 20)
        monkeypatch.setattr(db_module, "DB_PATH", ruta_prueba)

        # No debe lanzar ninguna excepcion -- debe repararse sola
        conexion = db_module.get_connection()
        assert conexion is not None

        # El archivo dañado debe quedar guardado a un lado, no perdido
        archivos_danados = list(tmp_path.glob("database_DAÑADA_*.db"))
        assert len(archivos_danados) == 1
