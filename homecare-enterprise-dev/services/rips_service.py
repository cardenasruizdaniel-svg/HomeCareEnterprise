"""
=========================================================
HomeCare Enterprise
Servicio RIPS

Consolida, para un periodo de facturación, las visitas
domiciliarias completadas, sus diagnósticos y los
medicamentos administrados, y arma el archivo RIPS en
formato JSON (Resolución 948 de 2026).
=========================================================
"""

import json
from pathlib import Path

from core.config import EXPORTS_DIR, RIPS_NIT_PRESTADOR
from core.rips.rips_builder import (
    construir_consulta,
    construir_medicamento,
    construir_transaccion,
    construir_usuario_rips,
)
from database.database import consultar_todos


class RIPSService:

    # ------------------------------------------------------
    # PACIENTES ATENDIDOS EN EL PERIODO
    # ------------------------------------------------------

    @staticmethod
    def _pacientes_con_visitas(fecha_inicio: str, fecha_fin: str):
        return consultar_todos(
            """
            SELECT DISTINCT p.*
            FROM pacientes p
            JOIN programaciones pr ON pr.paciente_id = p.id
            WHERE pr.estado = 'Completada'
              AND pr.fecha BETWEEN ? AND ?
            ORDER BY p.primer_apellido, p.primer_nombre
            """,
            (fecha_inicio, fecha_fin),
        )

    @staticmethod
    def _visitas_paciente(paciente_id: int, fecha_inicio: str, fecha_fin: str):
        return consultar_todos(
            """
            SELECT
                pr.*,
                pf.documento AS profesional_documento,
                pf.tipo_documento AS profesional_documento_tipo
            FROM programaciones pr
            LEFT JOIN profesionales pf ON pf.id = pr.profesional_id
            WHERE pr.paciente_id = ?
              AND pr.estado = 'Completada'
              AND pr.fecha BETWEEN ? AND ?
            ORDER BY pr.fecha, pr.hora_inicio
            """,
            (paciente_id, fecha_inicio, fecha_fin),
        )

    @staticmethod
    def _diagnostico_principal(paciente_id: int):
        return consultar_todos(
            """
            SELECT * FROM diagnosticos
            WHERE paciente_id = ?
            ORDER BY fecha_diagnostico DESC
            LIMIT 1
            """,
            (paciente_id,),
        )

    @staticmethod
    def _medicamentos_paciente(paciente_id: int, fecha_inicio: str, fecha_fin: str):
        return consultar_todos(
            """
            SELECT * FROM medicamentos
            WHERE paciente_id = ?
              AND (
                    (fecha_inicio IS NOT NULL AND fecha_inicio BETWEEN ? AND ?)
                    OR estado = 'ACTIVO'
              )
            """,
            (paciente_id, fecha_inicio, fecha_fin),
        )

    # ------------------------------------------------------
    # GENERAR RIPS DE UN PERIODO
    # ------------------------------------------------------

    @staticmethod
    def generar(
        fecha_inicio: str,
        fecha_fin: str,
        numero_factura: str,
        nit_prestador: str = None,
    ) -> dict:

        nit_prestador = nit_prestador or RIPS_NIT_PRESTADOR

        pacientes = RIPSService._pacientes_con_visitas(fecha_inicio, fecha_fin)

        usuarios = []
        pendientes = []  # campos faltantes, para avisar al usuario

        for p in pacientes:
            paciente = dict(p)

            # Cumplimiento: se usa el documento que estaba
            # VIGENTE al cierre del periodo que se esta
            # reportando (no necesariamente el documento actual
            # del paciente hoy), para que un cambio posterior de
            # documento (por ejemplo, de Tarjeta de Identidad a
            # Cedula) no altere retroactivamente como se
            # identifico al paciente en un RIPS ya generado.
            try:
                from services.historial_documentos_service import documento_vigente_en_fecha
                doc_vigente = documento_vigente_en_fecha(paciente["id"], fecha_fin)
                paciente["tipo_documento"] = doc_vigente["tipo_documento"]
                paciente["documento"] = doc_vigente["numero_documento"]
            except Exception:
                pass  # si algo falla, se usa el documento actual del paciente

            if not paciente.get("codigo_municipio_divipola"):
                pendientes.append(
                    f"Paciente {paciente.get('documento')}: falta código DIVIPOLA del municipio de residencia."
                )

            usuario = construir_usuario_rips(paciente)

            visitas = RIPSService._visitas_paciente(paciente["id"], fecha_inicio, fecha_fin)
            diag_rows = RIPSService._diagnostico_principal(paciente["id"])
            diagnostico = dict(diag_rows[0]) if diag_rows else None

            for v in visitas:
                visita = dict(v)

                if not visita.get("codigo_cups"):
                    pendientes.append(
                        f"Visita {visita.get('id')} del {visita.get('fecha')}: falta código CUPS."
                    )

                usuario["servicios"]["consultas"].append(
                    construir_consulta(visita, diagnostico)
                )

            medicamentos = RIPSService._medicamentos_paciente(
                paciente["id"], fecha_inicio, fecha_fin
            )

            for m in medicamentos:
                medicamento = dict(m)

                if not medicamento.get("codigo_cum"):
                    pendientes.append(
                        f"Medicamento '{medicamento.get('nombre')}' del paciente "
                        f"{paciente.get('documento')}: falta código CUM."
                    )

                usuario["servicios"]["medicamentos"].append(
                    construir_medicamento(medicamento)
                )

            usuarios.append(usuario)

        transaccion = construir_transaccion(nit_prestador, numero_factura, usuarios)

        return {
            "transaccion": transaccion,
            "total_usuarios": len(usuarios),
            "pendientes": pendientes,
            "nit_prestador_configurado": bool(nit_prestador),
        }

    # ------------------------------------------------------
    # GUARDAR ARCHIVO
    # ------------------------------------------------------

    @staticmethod
    def guardar_archivo(transaccion: dict, numero_factura: str) -> str:

        carpeta = Path(EXPORTS_DIR) / "rips"
        carpeta.mkdir(parents=True, exist_ok=True)

        nombre = f"RIPS_{numero_factura or 'sin-factura'}.json"
        ruta = carpeta / nombre

        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(transaccion, archivo, ensure_ascii=False, indent=2)

        return str(ruta)
