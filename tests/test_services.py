"""
HomeCare Enterprise - Pruebas unitarias de servicios

Prueban la LÓGICA DE NEGOCIO directamente (sin pasar por HTTP),
para los módulos más nuevos y con reglas más delicadas: PQR/SIAU,
Sistema de Gestión de Calidad, y Configuración del Portal Web.
"""

import pytest


class TestPQRService:

    def test_radicado_tiene_el_formato_correcto(self, client):
        from services import pqr_service as pqr
        resultado = pqr.radicar_pqr({
            "tipo": "Queja", "descripcion": "Prueba de formato de radicado",
            "solicitante_nombre": "Prueba Radicado",
        })
        assert resultado["radicado"].startswith("PQR-2026-")
        assert len(resultado["radicado"]) == len("PQR-2026-000001")

    def test_radicados_consecutivos_no_se_repiten(self, client):
        from services import pqr_service as pqr
        r1 = pqr.radicar_pqr({"tipo": "Sugerencia", "descripcion": "Prueba A", "solicitante_nombre": "Prueba Uno"})
        r2 = pqr.radicar_pqr({"tipo": "Sugerencia", "descripcion": "Prueba B", "solicitante_nombre": "Prueba Dos"})
        assert r1["radicado"] != r2["radicado"]

    def test_pqr_publica_recibe_clave_de_seguimiento(self, client):
        from services import pqr_service as pqr
        resultado = pqr.radicar_pqr(
            {"tipo": "Petición", "descripcion": "Prueba", "solicitante_nombre": "Prueba Clave"},
            es_publica=True,
        )
        assert resultado["clave_seguimiento"] is not None
        assert len(resultado["clave_seguimiento"]) == 6

    def test_pqr_interna_no_recibe_clave_de_seguimiento(self, client):
        from services import pqr_service as pqr
        resultado = pqr.radicar_pqr(
            {"tipo": "Petición", "descripcion": "Prueba", "solicitante_nombre": "Prueba Interna"},
            es_publica=False,
        )
        assert resultado["clave_seguimiento"] is None

    def test_no_se_puede_radicar_sin_tipo_valido(self, client):
        from services import pqr_service as pqr
        with pytest.raises(ValueError):
            pqr.radicar_pqr({"tipo": "Tipo inventado", "descripcion": "x", "solicitante_nombre": "x"})

    def test_consulta_publica_exige_radicado_y_clave_correctos(self, client):
        from services import pqr_service as pqr
        resultado = pqr.radicar_pqr(
            {"tipo": "Queja", "descripcion": "Prueba", "solicitante_nombre": "Prueba Consulta"},
            es_publica=True,
        )
        encontrada = pqr.consultar_estado_publico(resultado["radicado"], resultado["clave_seguimiento"])
        assert encontrada is not None
        assert encontrada["radicado"] == resultado["radicado"]

        no_encontrada = pqr.consultar_estado_publico(resultado["radicado"], "CLAVE-FALSA")
        assert no_encontrada is None

    def test_consulta_publica_nunca_expone_la_descripcion(self, client):
        """La consulta pública es solo administrativa -- nunca debe filtrar el contenido de la queja/respuesta."""
        from services import pqr_service as pqr
        resultado = pqr.radicar_pqr(
            {"tipo": "Queja", "descripcion": "CONTENIDO_QUE_NO_DEBE_FILTRARSE", "solicitante_nombre": "Prueba Privacidad"},
            es_publica=True,
        )
        encontrada = pqr.consultar_estado_publico(resultado["radicado"], resultado["clave_seguimiento"])
        assert "CONTENIDO_QUE_NO_DEBE_FILTRARSE" not in str(encontrada)

    def test_linea_de_tiempo_registra_la_radicacion(self, client):
        from services import pqr_service as pqr
        resultado = pqr.radicar_pqr({"tipo": "Queja", "descripcion": "Prueba", "solicitante_nombre": "Prueba Timeline"})
        registro = pqr.obtener_pqr_completa(resultado["id"])
        assert len(registro["eventos"]) >= 1
        assert registro["eventos"][0]["tipo_evento"] == "Radicación"


class TestCalidadAvanzadaService:

    @pytest.mark.parametrize("probabilidad,impacto,esperado", [
        ("Rara vez", "Insignificante", "Bajo"),
        ("Casi seguro", "Catastrófico", "Extremo"),
        ("Posible", "Moderado", "Alto"),
        ("Probable", "Mayor", "Extremo"),
    ])
    def test_matriz_de_riesgo_calcula_el_nivel_correcto(self, client, probabilidad, impacto, esperado):
        from services import calidad_avanzada_service as ca
        assert ca.calcular_nivel_riesgo(probabilidad, impacto) == esperado

    def test_no_se_puede_cerrar_un_hallazgo_sin_acciones(self, client):
        from services import calidad_avanzada_service as ca
        hallazgo_id = ca.crear_hallazgo({
            "clasificacion": "Menor", "proceso": "Prueba", "fecha": "2026-08-24",
            "descripcion": "Hallazgo de prueba sin acciones",
        })
        with pytest.raises(ValueError):
            ca.cerrar_hallazgo(hallazgo_id)

    def test_si_se_puede_cerrar_un_hallazgo_con_accion_verificada(self, client):
        from services import calidad_avanzada_service as ca
        hallazgo_id = ca.crear_hallazgo({
            "clasificacion": "Menor", "proceso": "Prueba", "fecha": "2026-08-24",
            "descripcion": "Hallazgo de prueba con accion completa",
        })
        accion_id = ca.crear_accion(hallazgo_id, {
            "tipo": "Correctiva", "descripcion": "Accion de prueba", "fecha_compromiso": "2026-09-01",
        })
        ca.ejecutar_accion(accion_id, "2026-08-30", "Evidencia de prueba")
        ca.verificar_eficacia_accion(accion_id, True, "Verificacion de prueba")
        ca.cerrar_hallazgo(hallazgo_id)

    def test_evento_de_seguridad_se_puede_escalar_a_hallazgo_critico(self, client):
        from services import calidad_avanzada_service as ca
        evento_id = ca.crear_evento_seguridad({
            "tipo": "Relacionado con caídas", "severidad": "Grave", "fecha": "2026-08-24",
            "descripcion": "Evento de prueba para escalamiento",
        })
        hallazgo_id = ca.escalar_evento_a_hallazgo(evento_id)
        hallazgo = ca.obtener_hallazgo(hallazgo_id)
        assert hallazgo["clasificacion"] == "Crítico"
        assert hallazgo["fuente"] == "Seguridad del paciente"


class TestConfiguracionWebService:

    def test_guardar_y_leer_configuracion(self, client):
        from services import configuracion_web_service as cw
        cw.guardar_configuracion({"hero_titulo": "Título de prueba", "telefono": "3000000000"})
        config = cw.obtener_configuracion()
        assert config["hero_titulo"] == "Título de prueba"
        assert config["telefono"] == "3000000000"

    def test_guardar_dos_veces_no_crea_filas_duplicadas(self, client):
        from services import configuracion_web_service as cw
        cw.guardar_configuracion({"hero_titulo": "Primero"})
        cw.guardar_configuracion({"hero_titulo": "Segundo"})
        assert cw.obtener_configuracion()["id"] == 1
        assert cw.obtener_configuracion()["hero_titulo"] == "Segundo"

    def test_no_se_puede_crear_servicio_sin_nombre(self, client):
        from services import configuracion_web_service as cw
        with pytest.raises(ValueError):
            cw.crear_servicio({"descripcion": "Sin nombre"})

    def test_desactivar_servicio_lo_saca_del_listado_publico(self, client):
        from services import configuracion_web_service as cw
        servicio_id = cw.crear_servicio({"nombre": "Servicio de prueba para desactivar"})
        assert any(s["id"] == servicio_id for s in cw.listar_servicios(solo_activos=True))
        cw.desactivar_servicio(servicio_id)
        assert not any(s["id"] == servicio_id for s in cw.listar_servicios(solo_activos=True))
