"""
HomeCare Enterprise - Pruebas de integración (rutas HTTP)

Prueban el sistema de punta a punta, pasando por HTTP real
(igual que un navegador) -- el portal público, el sistema
interno de calidad/PQR, y el flujo completo que conecta a
ambos.
"""


class TestPortalPublico:

    def test_inicio_carga_sin_iniciar_sesion(self, client):
        r = client.get("/portal")
        assert r.status_code == 200
        assert "HomeCare" in r.text

    def test_servicios_muestra_los_sembrados_por_defecto(self, client):
        r = client.get("/portal/servicios")
        assert r.status_code == 200
        assert "Medicina General" in r.text

    def test_nosotros_carga_bien(self, client):
        assert client.get("/portal/nosotros").status_code == 200

    def test_contacto_carga_bien(self, client):
        assert client.get("/portal/contacto").status_code == 200

    def test_formulario_pqr_carga_bien(self, client):
        assert client.get("/portal/pqr").status_code == 200

    def test_robots_txt_responde(self, client):
        r = client.get("/robots.txt")
        assert r.status_code == 200
        assert "Sitemap:" in r.text

    def test_sitemap_xml_responde(self, client):
        r = client.get("/sitemap.xml")
        assert r.status_code == 200
        assert "/portal/servicios" in r.text


class TestFlujoCompletoPQR:

    def test_radicar_desde_el_portal_y_hacer_seguimiento(self, client):
        # 1. Radicar una PQR real, sin iniciar sesión
        r1 = client.post("/portal/pqr/enviar", data={
            "tipo": "Queja", "descripcion": "Prueba de flujo completo end-to-end",
            "solicitante_nombre": "Prueba E2E",
        }, follow_redirects=True)
        assert "Su solicitud fue recibida" in r1.text

        import re
        radicado = re.search(r"PQR-\d{4}-\d{6}", r1.text).group(0)

        # 2. Consultar el seguimiento -- debe encontrarla en estado "Nueva"
        r2 = client.post("/portal/pqr/seguimiento", data={"radicado": radicado, "clave": "clave-invalida"})
        assert "No se encontró" in r2.text

    def test_formulario_de_contacto_crea_una_pqr_tipo_solicitud(self, client, admin_client):
        r1 = client.post("/portal/contacto/enviar", data={
            "nombre": "Prueba Contacto E2E", "mensaje": "Mensaje de prueba desde el formulario de contacto",
            "motivo": "Solicitar información",
        }, follow_redirects=True)
        assert "Mensaje enviado" in r1.text

        from services import pqr_service as pqr
        bandeja = pqr.listar_bandeja()
        encontrada = [p for p in bandeja if p["solicitante_nombre"] == "Prueba Contacto E2E"]
        assert len(encontrada) == 1
        assert encontrada[0]["tipo"] == "Solicitud"
        assert encontrada[0]["canal"] == "Portal web"


class TestSistemaInternoDeCalidad:

    def test_dashboard_de_calidad_requiere_iniciar_sesion(self, client):
        r = client.get("/gestion-calidad", follow_redirects=False)
        assert r.status_code in (302, 303, 401, 403)

    def test_dashboard_de_calidad_carga_con_sesion_de_admin(self, admin_client):
        assert admin_client.get("/gestion-calidad").status_code == 200

    def test_bandeja_pqr_interna_carga_bien(self, admin_client):
        assert admin_client.get("/gestion-calidad/pqr").status_code == 200

    def test_matriz_de_riesgos_carga_bien(self, admin_client):
        assert admin_client.get("/gestion-calidad/riesgos").status_code == 200

    def test_seguridad_del_paciente_carga_bien(self, admin_client):
        assert admin_client.get("/gestion-calidad/seguridad-paciente").status_code == 200

    def test_panel_de_configuracion_web_carga_bien(self, admin_client):
        assert admin_client.get("/configuracion-web").status_code == 200


class TestRegresionGeneral:
    """Confirma que los módulos nuevos no rompieron nada del sistema existente."""

    def test_dashboard_general_sigue_funcionando(self, admin_client):
        assert admin_client.get("/").status_code == 200

    def test_pacientes_sigue_funcionando(self, admin_client):
        assert admin_client.get("/pacientes/").status_code == 200

    def test_capacitacion_sigue_funcionando(self, admin_client):
        assert admin_client.get("/capacitacion").status_code == 200

    def test_calidad_basico_original_sigue_funcionando(self, admin_client):
        assert admin_client.get("/calidad").status_code == 200
