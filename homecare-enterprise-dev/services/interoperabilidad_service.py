"""
=========================================================
HomeCare Enterprise
Servicio de Interoperabilidad

Genera el Resumen Digital de Atencion en Salud (RDA) de
un paciente, en cumplimiento de la Resolucion 866 de 2021
y la Resolucion 1888 de 2025 (IHCE), usando HL7 FHIR R4.
=========================================================
"""

from database.database import consultar_todos, consultar_uno
from core.interoperability.fhir_mapper import FHIRMapper
from core.interoperability.exceptions import ValidationError


class InteroperabilidadService:

    # ------------------------------------------------------
    # Compatibilidad con el endpoint previo (paciente suelto)
    # ------------------------------------------------------

    @staticmethod
    def exportar_paciente(datos: dict) -> dict:
        return FHIRMapper.patient(datos)

    # ------------------------------------------------------
    # RDA COMPLETO DE UN PACIENTE
    # ------------------------------------------------------

    @staticmethod
    def generar_rda(paciente_id: int) -> dict:

        paciente = consultar_uno(
            "SELECT * FROM pacientes WHERE id=?",
            (paciente_id,),
        )

        if paciente is None:
            raise ValidationError(
                f"No existe un paciente con id={paciente_id}."
            )

        paciente = dict(paciente)

        recursos = [FHIRMapper.patient(paciente)]

        # -- Diagnosticos (Condition) --
        diagnosticos = consultar_todos(
            "SELECT * FROM diagnosticos WHERE paciente_id=?",
            (paciente_id,),
        )
        for d in diagnosticos:
            recursos.append(
                FHIRMapper.condition(dict(d), paciente_id)
            )

        # -- Alergias (AllergyIntolerance) --
        alergias = consultar_todos(
            "SELECT * FROM alergias WHERE paciente_id=?",
            (paciente_id,),
        )
        for a in alergias:
            recursos.append(
                FHIRMapper.allergy_intolerance(dict(a), paciente_id)
            )

        # -- Medicamentos (MedicationStatement) --
        medicamentos = consultar_todos(
            "SELECT * FROM medicamentos WHERE paciente_id=?",
            (paciente_id,),
        )
        for m in medicamentos:
            recursos.append(
                FHIRMapper.medication_statement(dict(m), paciente_id)
            )

        # -- Signos vitales (Observation) --
        signos = consultar_todos(
            """
            SELECT * FROM signos_vitales
            WHERE paciente_id=?
            ORDER BY fecha DESC, hora DESC
            LIMIT 20
            """,
            (paciente_id,),
        )
        for s in signos:
            recursos.extend(
                FHIRMapper.observations(dict(s), paciente_id)
            )

        return FHIRMapper.bundle(recursos, tipo="document")

    # ------------------------------------------------------
    # RESUMEN DE COMPLETITUD (para el panel de administración)
    # ------------------------------------------------------

    @staticmethod
    def verificar_completitud(paciente_id: int) -> dict:
        """
        Indica que tan completo esta el conjunto de datos
        clinicos relevantes (Res. 866/2021) de un paciente.
        No reemplaza el anexo tecnico oficial: es una
        verificación local orientativa.
        """

        paciente = consultar_uno(
            "SELECT * FROM pacientes WHERE id=?",
            (paciente_id,),
        )

        if paciente is None:
            raise ValidationError(
                f"No existe un paciente con id={paciente_id}."
            )

        paciente = dict(paciente)

        campos_obligatorios = [
            "tipo_documento",
            "documento",
            "primer_nombre",
            "primer_apellido",
            "fecha_nacimiento",
            "sexo",
            "municipio",
            "departamento",
        ]

        campos_recomendados = [
            "identidad_genero",
            "pertenencia_etnica",
            "indicador_alergias",
            "correo",
            "celular",
        ]

        faltantes_obligatorios = [
            c for c in campos_obligatorios if not paciente.get(c)
        ]

        faltantes_recomendados = [
            c for c in campos_recomendados if not paciente.get(c)
        ]

        total = len(campos_obligatorios) + len(campos_recomendados)
        completos = total - len(faltantes_obligatorios) - len(faltantes_recomendados)

        return {
            "paciente_id": paciente_id,
            "porcentaje": round((completos / total) * 100, 1),
            "faltantes_obligatorios": faltantes_obligatorios,
            "faltantes_recomendados": faltantes_recomendados,
            "cumple_minimo": len(faltantes_obligatorios) == 0,
        }
