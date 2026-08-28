"""
HomeCare Enterprise - Pruebas de seguridad

Confirman que el sistema mantiene las barreras que deben
existir siempre: rutas internas protegidas, el portal público
no filtra información sensible, y las protecciones básicas
contra abuso funcionan de verdad (no solo están "escritas").
"""


class TestControlDeAcceso:

    def test_rutas_internas_clave_no_son_accesibles_sin_sesion(self, client):
        rutas_protegidas = [
            "/pacientes/", "/gestion-calidad", "/gestion-calidad/pqr",
            "/configuracion-web", "/configuracion-empresa", "/auditoria",
        ]
        for ruta in rutas_protegidas:
            r = client.get(ruta, follow_redirects=False)
            assert r.status_code in (302, 303, 401, 403), f"La ruta {ruta} no debería ser accesible sin iniciar sesión (dio {r.status_code})"

    def test_rutas_publicas_del_portal_no_requieren_sesion(self, client):
        rutas_publicas = ["/portal", "/portal/servicios", "/portal/nosotros", "/portal/contacto", "/portal/pqr"]
        for ruta in rutas_publicas:
            r = client.get(ruta)
            assert r.status_code == 200, f"La ruta pública {ruta} debería cargar sin iniciar sesión"


class TestPrivacidadPQRPublica:

    def test_no_se_puede_consultar_una_pqr_sin_saber_la_clave(self, client):
        r1 = client.post("/portal/pqr/enviar", data={
            "tipo": "Queja", "descripcion": "INFORMACION_SENSIBLE_DE_PRUEBA",
            "solicitante_nombre": "Prueba Privacidad HTTP",
        }, follow_redirects=True)
        import re
        radicado = re.search(r"PQR-\d{4}-\d{6}", r1.text).group(0)

        # Intentar adivinar con una clave cualquiera -- no debe funcionar,
        # y sobre todo NO debe filtrar el contenido de la descripción.
        r2 = client.post("/portal/pqr/seguimiento", data={"radicado": radicado, "clave": "ABCDEF"})
        assert "INFORMACION_SENSIBLE_DE_PRUEBA" not in r2.text
        assert "No se encontró" in r2.text

    def test_la_pagina_publica_de_seguimiento_nunca_expone_el_contenido_de_la_respuesta(self, admin_client, client):
        # Radicar, responder internamente con contenido sensible, y confirmar
        # que la consulta publica NUNCA muestra ese texto.
        from services import pqr_service as pqr
        resultado = pqr.radicar_pqr(
            {"tipo": "Queja", "descripcion": "Prueba", "solicitante_nombre": "Prueba Respuesta Privada"},
            es_publica=True,
        )
        pqr.responder_pqr(resultado["id"], "RESPUESTA_INTERNA_QUE_NO_DEBE_VERSE_PUBLICAMENTE", "Correo")

        r = client.post("/portal/pqr/seguimiento", data={"radicado": resultado["radicado"], "clave": resultado["clave_seguimiento"]})
        assert "RESPUESTA_INTERNA_QUE_NO_DEBE_VERSE_PUBLICAMENTE" not in r.text
        assert "Cerrada" in r.text


class TestLimiteDePeticiones:

    def test_el_formulario_publico_de_pqr_tiene_limite_de_envios(self, client):
        """5 envíos permitidos cada 5 minutos por IP -- el 6to debe rechazarse."""
        for _ in range(5):
            r = client.post("/portal/pqr/enviar", data={
                "tipo": "Sugerencia", "descripcion": "Prueba de limite", "solicitante_nombre": "Prueba Limite",
            })
            assert r.status_code in (200, 303)

        r_extra = client.post("/portal/pqr/enviar", data={
            "tipo": "Sugerencia", "descripcion": "Este debe rechazarse", "solicitante_nombre": "Prueba Limite",
        })
        assert r_extra.status_code == 429


class TestValidacionDeDatos:

    def test_no_se_puede_radicar_pqr_sin_descripcion(self, client):
        r = client.post("/portal/pqr/enviar", data={
            "tipo": "Queja", "solicitante_nombre": "Prueba Sin Descripcion",
        })
        # FastAPI rechaza el campo obligatorio faltante (422) antes de
        # llegar siquiera a la logica de negocio.
        assert r.status_code == 422

    def test_no_se_puede_crear_hallazgo_con_clasificacion_invalida(self, app):
        import pytest
        from services import calidad_avanzada_service as ca
        with pytest.raises(ValueError):
            ca.crear_hallazgo({
                "clasificacion": "Clasificación que no existe", "proceso": "Prueba",
                "fecha": "2026-08-24", "descripcion": "Prueba",
            })
