"""
=========================================================
HomeCare Enterprise
Constructor de la estructura JSON del RIPS

Arma el objeto "transacción" tal como lo describe el
Documento Técnico 1 (Resolución 948 de 2026, que preserva
la arquitectura de datos introducida por la Resolución
2275 de 2023): transacción -> usuarios[] -> servicios{}.

Este modulo SOLO construye el documento; no lo transmite
al Mecanismo Único de Validación (MUV) del Ministerio, ya
que eso requiere: (a) factura electrónica de venta (FEV)
validada por la DIAN, (b) el contrato registrado en el
SIIFA con su CUCON, y (c) las credenciales del prestador
ante el MUV. Ver docs/RIPS.md para el detalle de lo que
falta para una transmisión real.
=========================================================
"""

from core.rips.catalogos import PAIS_COLOMBIA


def construir_usuario_rips(paciente: dict) -> dict:
    """
    Construye el objeto "usuario" del RIPS a partir de un
    registro de la tabla pacientes.
    """

    return {
        "tipoDocumentoIdentificacion": paciente.get("tipo_documento"),
        "numDocumentoIdentificacion": paciente.get("documento"),
        "tipoUsuario": paciente.get("tipo_usuario_rips"),
        "fechaNacimiento": paciente.get("fecha_nacimiento"),
        "codSexo": paciente.get("sexo"),
        "codPaisResidencia": paciente.get("codigo_pais_residencia") or PAIS_COLOMBIA,
        "codMunicipioResidencia": paciente.get("codigo_municipio_divipola"),
        "codZonaTerritorialResidencia": None,
        "incapacidad": paciente.get("incapacidad") or "NO",
        "consecutivo": None,  # se asigna al ensamblar la transacción
        "codPaisOrigen": PAIS_COLOMBIA,
        "servicios": {
            "consultas": [],
            "procedimientos": [],
            "urgencias": [],
            "hospitalizacion": [],
            "recienNacidos": [],
            "medicamentos": [],
            "otrosServicios": [],
        },
    }


def construir_consulta(visita: dict, diagnostico: dict | None) -> dict:
    """
    Construye un objeto "consulta" (tipo de servicio C) a
    partir de una visita domiciliaria (programación) y su
    diagnóstico asociado.
    """

    return {
        "codPrestador": None,  # código de habilitación de la sede que atendió
        "fechaInicioAtencion": f"{visita.get('fecha')} {visita.get('hora_inicio')}",
        "numAutorizacion": visita.get("numero_autorizacion"),
        "codConsulta": visita.get("codigo_cups"),
        "modalidadGrupoServicioTecSal": "04",  # domiciliaria
        "grupoServicios": None,
        "codServicio": None,
        "finalidadTecnologiaSalud": visita.get("finalidad_tecnologia_salud"),
        "causaMotivoAtencion": visita.get("causa_externa"),
        "codDiagnosticoPrincipal": (diagnostico or {}).get("codigo_cie10"),
        "codDiagnosticoRelacionado1": None,
        "codDiagnosticoRelacionado2": None,
        "codDiagnosticoRelacionado3": None,
        "tipoDiagnosticoPrincipal": (diagnostico or {}).get("tipo_diagnostico_rips"),
        "tipoDocumentoIdentificacion": visita.get("profesional_documento_tipo"),
        "numDocumentoIdentificacion": visita.get("profesional_documento"),
        "vrServicio": visita.get("valor_servicio") or 0,
        "conceptoRecaudo": None,
        "valorPagoModerador": 0,
        "numFEVPagoModerador": None,
        "consecutivo": None,  # se asigna al ensamblar
    }


def construir_medicamento(med: dict) -> dict:
    """
    Construye un objeto "medicamentos" (tipo de servicio M).
    """

    return {
        "codPrestador": None,
        "numAutorizacion": None,
        "codDiagnosticoPrincipal": None,
        "codDiagnosticoRelacionado": None,
        "tipoMedicamento": None,
        "codTecnologiaSalud": med.get("codigo_cum"),
        "nomTecnologiaSalud": med.get("nombre"),
        "concentracionMedicamento": med.get("concentracion"),
        "unidadMedida": None,
        "formaFarmaceutica": med.get("presentacion"),
        "unidadMinDispensa": None,
        "cantidadMedicamento": None,
        "diasTratamiento": None,
        "tipoDocumentoIdentificacion": None,
        "numDocumentoIdentificacion": None,
        "vrUnitMedicamento": None,
        "vrServicio": 0,
        "conceptoRecaudo": None,
        "valorPagoModerador": 0,
        "numFEVPagoModerador": None,
        "consecutivo": None,
    }


def construir_transaccion(
    nit_prestador: str,
    numero_factura: str,
    usuarios: list,
) -> dict:
    """
    Ensambla el objeto raíz "transacción" del RIPS y asigna
    los consecutivos requeridos por el anexo técnico.
    """

    for i, usuario in enumerate(usuarios, start=1):
        usuario["consecutivo"] = i

        for lista in usuario["servicios"].values():
            for j, servicio in enumerate(lista, start=1):
                servicio["consecutivo"] = j

    return {
        "numDocumentoIdObligado": nit_prestador,
        "numFactura": numero_factura,
        "tipoNota": None,
        "numNota": None,
        "usuarios": usuarios,
    }
