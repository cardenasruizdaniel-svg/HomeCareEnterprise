"""
=========================================================
HomeCare Enterprise
Mapeador HL7 FHIR R4

Construye los recursos FHIR que integran el Resumen
Digital de Atencion en Salud (RDA), en el marco de la
Interoperabilidad de la Historia Clinica Electronica
(IHCE - Ley 2015 de 2020, Resolucion 866 de 2021 y
Resolucion 1888 de 2025).

Nota: este modulo genera los recursos localmente. El
envio al mecanismo nacional de interoperabilidad del
Ministerio de Salud (API Gateway, autenticacion API Key +
Subscription Key) requiere credenciales que la IPS debe
solicitar directamente al Ministerio; ese paso de "envio"
queda como un punto de integracion pendiente y se documenta
en docs/INTEROPERABILIDAD.md.
=========================================================
"""

import uuid as uuid_lib
from datetime import datetime, timezone


# ==========================================================
# CATALOGOS DE APOYO (Resolucion 866 de 2021, anexo tecnico)
# ==========================================================

TIPOS_DOCUMENTO_FHIR = {
    "CC": "CC",
    "TI": "TI",
    "CE": "CE",
    "PA": "PA",
    "RC": "RC",
    "NIT": "NIT",
    "AS": "AS",
    "MS": "MS",
}

SEXO_FHIR = {
    "M": "male",
    "MASCULINO": "male",
    "F": "female",
    "FEMENINO": "female",
}


def _texto(valor) -> str:
    return "" if valor is None else str(valor)


def _uuid() -> str:
    return str(uuid_lib.uuid4())


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class FHIRMapper:
    """
    Traduce los registros del modelo de datos de HomeCare
    Enterprise a recursos HL7 FHIR R4, usando el estandar
    internacional exigido por el anexo tecnico del RDA.
    """

    # ------------------------------------------------------
    # PACIENTE -> Patient
    # ------------------------------------------------------

    @staticmethod
    def patient(paciente: dict) -> dict:

        nombre_completo = paciente.get("nombre_completo") or " ".join(
            x for x in [
                paciente.get("primer_nombre"),
                paciente.get("segundo_nombre"),
                paciente.get("primer_apellido"),
                paciente.get("segundo_apellido"),
            ] if x
        )

        tipo_doc = TIPOS_DOCUMENTO_FHIR.get(
            (paciente.get("tipo_documento") or "").upper(),
            paciente.get("tipo_documento") or "CC",
        )

        recurso = {
            "resourceType": "Patient",
            "id": paciente.get("uuid_ihce") or paciente.get("uuid") or str(paciente.get("id", "")),
            "identifier": [{
                "system": f"https://ihce.minsalud.gov.co/documento/{tipo_doc}",
                "type": {"text": tipo_doc},
                "value": _texto(paciente.get("documento")),
            }],
            "name": [{
                "text": nombre_completo,
                "given": [
                    x for x in [
                        paciente.get("primer_nombre"),
                        paciente.get("segundo_nombre"),
                    ] if x
                ],
                "family": " ".join(
                    x for x in [
                        paciente.get("primer_apellido"),
                        paciente.get("segundo_apellido"),
                    ] if x
                ),
            }],
            "telecom": [
                t for t in [
                    {"system": "phone", "value": paciente.get("celular")} if paciente.get("celular") else None,
                    {"system": "phone", "value": paciente.get("telefono")} if paciente.get("telefono") else None,
                    {"system": "email", "value": paciente.get("correo")} if paciente.get("correo") else None,
                ] if t
            ],
            "gender": SEXO_FHIR.get((paciente.get("sexo") or "").upper(), "unknown"),
            "birthDate": paciente.get("fecha_nacimiento") or None,
            "address": [{
                "line": [paciente.get("direccion")] if paciente.get("direccion") else [],
                "city": paciente.get("municipio"),
                "district": paciente.get("barrio"),
                "state": paciente.get("departamento"),
                "country": paciente.get("pais_residencia") or "CO",
            }],
        }

        # -- Elementos de datos clinicos relevantes (Res. 866/2021) --
        extensiones = []

        if paciente.get("hora_nacimiento"):
            extensiones.append({
                "url": "https://ihce.minsalud.gov.co/fhir/StructureDefinition/hora-nacimiento",
                "valueTime": paciente["hora_nacimiento"],
            })

        if paciente.get("identidad_genero"):
            extensiones.append({
                "url": "https://ihce.minsalud.gov.co/fhir/StructureDefinition/identidad-genero",
                "valueString": paciente["identidad_genero"],
            })

        if paciente.get("pertenencia_etnica"):
            extensiones.append({
                "url": "https://ihce.minsalud.gov.co/fhir/StructureDefinition/pertenencia-etnica",
                "valueString": paciente["pertenencia_etnica"],
            })

        if paciente.get("comunidad_etnica"):
            extensiones.append({
                "url": "https://ihce.minsalud.gov.co/fhir/StructureDefinition/comunidad-etnica",
                "valueString": paciente["comunidad_etnica"],
            })

        if paciente.get("indicador_alergias") is not None:
            extensiones.append({
                "url": "https://ihce.minsalud.gov.co/fhir/StructureDefinition/indicador-alergias",
                "valueString": paciente["indicador_alergias"],
            })

        if extensiones:
            recurso["extension"] = extensiones

        return recurso

    # ------------------------------------------------------
    # PROFESIONAL -> Practitioner
    # ------------------------------------------------------

    @staticmethod
    def practitioner(profesional: dict) -> dict:
        return {
            "resourceType": "Practitioner",
            "id": str(profesional.get("id", "")),
            "identifier": [{
                "value": _texto(profesional.get("documento")),
            }],
            "name": [{
                "text": profesional.get("nombre_completo") or profesional.get("nombre", ""),
            }],
            "qualification": [{
                "code": {"text": profesional.get("profesion") or profesional.get("especialidad_principal", "")},
            }],
        }

    # ------------------------------------------------------
    # DIAGNOSTICO -> Condition (codificado en CIE-10)
    # ------------------------------------------------------

    @staticmethod
    def condition(diagnostico: dict, paciente_id) -> dict:
        return {
            "resourceType": "Condition",
            "id": str(diagnostico.get("id", "")),
            "subject": {"reference": f"Patient/{paciente_id}"},
            "code": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": diagnostico.get("codigo_cie10", ""),
                    "display": diagnostico.get("diagnostico", ""),
                }],
                "text": diagnostico.get("diagnostico", ""),
            },
            "clinicalStatus": {
                "coding": [{"code": (diagnostico.get("estado") or "active").lower()}],
            },
            "category": [{"text": diagnostico.get("tipo", "")}],
            "recordedDate": diagnostico.get("fecha_diagnostico") or diagnostico.get("fecha_registro"),
            "recorder": {"display": diagnostico.get("profesional", "")},
        }

    # ------------------------------------------------------
    # ALERGIA -> AllergyIntolerance
    # ------------------------------------------------------

    @staticmethod
    def allergy_intolerance(alergia: dict, paciente_id) -> dict:
        return {
            "resourceType": "AllergyIntolerance",
            "id": str(alergia.get("id", "")),
            "patient": {"reference": f"Patient/{paciente_id}"},
            "code": {
                "coding": [{
                    "code": alergia.get("codigo_alergeno") or "",
                    "display": alergia.get("alergeno", ""),
                }],
                "text": alergia.get("alergeno", ""),
            },
            "type": alergia.get("tipo", ""),
            "criticality": {
                "leve": "low",
                "moderada": "low",
                "severa": "high",
                "grave": "high",
            }.get((alergia.get("severidad") or "").lower(), "unable-to-assess"),
            "clinicalStatus": {
                "coding": [{"code": (alergia.get("estado") or "active").lower()}],
            },
            "reaction": [{
                "description": alergia.get("reaccion", ""),
            }] if alergia.get("reaccion") else [],
        }

    # ------------------------------------------------------
    # MEDICAMENTO -> MedicationStatement (codificado en CUM)
    # ------------------------------------------------------

    @staticmethod
    def medication_statement(medicamento: dict, paciente_id) -> dict:
        return {
            "resourceType": "MedicationStatement",
            "id": str(medicamento.get("id", "")),
            "subject": {"reference": f"Patient/{paciente_id}"},
            "status": (medicamento.get("estado") or "active").lower(),
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "https://www.minsalud.gov.co/cum",
                    "code": medicamento.get("codigo_cum") or "",
                    "display": medicamento.get("nombre", ""),
                }],
                "text": medicamento.get("nombre", ""),
            },
            "dosage": [{
                "text": " ".join(
                    x for x in [
                        medicamento.get("dosis"),
                        medicamento.get("via"),
                        medicamento.get("frecuencia"),
                    ] if x
                ),
            }],
            "effectivePeriod": {
                "start": medicamento.get("fecha_inicio"),
                "end": medicamento.get("fecha_fin"),
            },
        }

    # ------------------------------------------------------
    # SIGNOS VITALES -> Observation
    # ------------------------------------------------------

    _OBSERVACIONES_LOINC = {
        "temperatura": ("8310-5", "Temperatura corporal", "Cel"),
        "frecuencia_cardiaca": ("8867-4", "Frecuencia cardiaca", "/min"),
        "frecuencia_respiratoria": ("9279-1", "Frecuencia respiratoria", "/min"),
        "saturacion_oxigeno": ("2708-6", "Saturacion de oxigeno", "%"),
        "glucemia": ("2339-0", "Glucosa en sangre", "mg/dL"),
        "peso": ("29463-7", "Peso corporal", "kg"),
        "talla": ("8302-2", "Talla", "cm"),
        "imc": ("39156-5", "Indice de masa corporal", "kg/m2"),
    }

    @staticmethod
    def observations(signo: dict, paciente_id) -> list:
        """
        Un registro de signos vitales produce varias
        observaciones FHIR (una por cada parametro medido).
        """

        recursos = []

        fecha = signo.get("fecha") or ""
        hora = signo.get("hora") or ""
        efectivo = f"{fecha}T{hora}" if fecha and hora else fecha or None

        for campo, (codigo, nombre, unidad) in FHIRMapper._OBSERVACIONES_LOINC.items():

            valor = signo.get(campo)

            if valor in (None, ""):
                continue

            recursos.append({
                "resourceType": "Observation",
                "id": f"{signo.get('id', '')}-{campo}",
                "status": "final",
                "subject": {"reference": f"Patient/{paciente_id}"},
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": codigo,
                        "display": nombre,
                    }],
                    "text": nombre,
                },
                "effectiveDateTime": efectivo,
                "valueQuantity": {
                    "value": valor,
                    "unit": unidad,
                },
                "performer": [{"display": signo.get("profesional", "")}],
            })

        presion_sistolica = signo.get("presion_sistolica")
        presion_diastolica = signo.get("presion_diastolica")

        if presion_sistolica or presion_diastolica:
            recursos.append({
                "resourceType": "Observation",
                "id": f"{signo.get('id', '')}-presion-arterial",
                "status": "final",
                "subject": {"reference": f"Patient/{paciente_id}"},
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "85354-9",
                        "display": "Presion arterial",
                    }],
                    "text": "Presion arterial",
                },
                "effectiveDateTime": efectivo,
                "component": [
                    {
                        "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Sistolica"}]},
                        "valueQuantity": {"value": presion_sistolica, "unit": "mmHg"},
                    },
                    {
                        "code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolica"}]},
                        "valueQuantity": {"value": presion_diastolica, "unit": "mmHg"},
                    },
                ],
            })

        return recursos

    # ------------------------------------------------------
    # BUNDLE (RDA - Resumen Digital de Atencion en Salud)
    # ------------------------------------------------------

    @staticmethod
    def bundle(recursos: list, tipo: str = "collection") -> dict:
        return {
            "resourceType": "Bundle",
            "id": _uuid(),
            "type": tipo,
            "timestamp": _timestamp(),
            "meta": {
                "profile": [
                    "https://ihce.minsalud.gov.co/fhir/StructureDefinition/RDA"
                ],
            },
            "entry": [
                {"resource": r} for r in recursos
            ],
        }
