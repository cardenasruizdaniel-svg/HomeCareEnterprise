"""
HomeCare Enterprise - Servicio de Nomina Electronica

Genera el Documento Soporte de Pago de Nomina Electronica
(DSNE) para cada profesional de una nomina ya generada,
en formato XML segun el Anexo Tecnico de la DIAN
(Resolucion 000013 de 2021 / Anexo T.5.4 de la Resolucion
000227 de 2025).

Ver docs/NOMINA_ELECTRONICA.md para el detalle de lo que
falta para transmitir estos documentos realmente a la DIAN.
"""

from pathlib import Path

from core.config import EXPORTS_DIR, RIPS_NIT_PRESTADOR, RIPS_RAZON_SOCIAL
from core.nomina_electronica.xml_builder import construir_dsne, diccionario_a_xml_nomina
from database.database import consultar_todos, consultar_uno, ejecutar

from repositories.nomina_repository import NominaRepository


def generar_dsne_nomina(nomina_id: int, usuario=None) -> list:
    """
    Genera un DSNE por cada profesional incluido en la
    nomina indicada.
    """

    nomina = NominaRepository.obtener_nomina(nomina_id)

    if not nomina:
        raise ValueError("La nómina no existe.")

    nomina = dict(nomina)

    detalle_nomina = NominaRepository.detalle_nomina(nomina_id)

    periodo = {
        "periodo_inicio": nomina["periodo_inicio"],
        "periodo_fin": nomina["periodo_fin"],
        "dias_periodo": None,
        "fecha_generacion": nomina["fecha_generacion"],
    }

    from datetime import datetime
    inicio = datetime.strptime(nomina["periodo_inicio"], "%Y-%m-%d")
    fin = datetime.strptime(nomina["periodo_fin"], "%Y-%m-%d")
    periodo["dias_periodo"] = max((fin - inicio).days + 1, 1)

    resultados = []
    carpeta = Path(EXPORTS_DIR) / "nomina_electronica"
    carpeta.mkdir(parents=True, exist_ok=True)

    for fila in detalle_nomina:
        fila = dict(fila)

        profesional = consultar_uno(
            "SELECT * FROM profesionales WHERE id=?", (fila["profesional_id"],)
        )
        profesional = dict(profesional) if profesional else {}

        dsne = construir_dsne(
            fila, profesional, periodo,
            nit_empleador=RIPS_NIT_PRESTADOR or "PENDIENTE-CONFIGURAR-NIT",
            razon_social_empleador=RIPS_RAZON_SOCIAL,
        )

        cune = dsne["_cune_local"]

        ruta_xml = carpeta / f"dsne_{fila['id']}.xml"
        with open(ruta_xml, "w", encoding="utf-8") as archivo:
            archivo.write(diccionario_a_xml_nomina(dsne))

        registro_id = ejecutar(
            """
            INSERT INTO nomina_electronica (
                nomina_detalle_id, numero_consecutivo, cune, estado, xml_path, fecha_generacion
            ) VALUES (?,?,?,?,?,?)
            """,
            (fila["id"], fila["id"], cune, "Generado", str(ruta_xml), nomina["fecha_generacion"]),
        )

        resultados.append({
            "nomina_detalle_id": fila["id"],
            "profesional": profesional.get("nombre_completo", ""),
            "cune": cune,
            "valor_neto": dsne["_valor_neto"],
            "xml_path": str(ruta_xml),
        })

    return resultados


def listar_dsne_de_nomina(nomina_id: int):
    return consultar_todos(
        """
        SELECT ne.*, nd.profesional_id, pf.nombre_completo, nd.valor_a_pagar
        FROM nomina_electronica ne
        JOIN nomina_detalle nd ON nd.id = ne.nomina_detalle_id
        JOIN profesionales pf ON pf.id = nd.profesional_id
        WHERE nd.nomina_id = ?
        ORDER BY pf.nombre_completo
        """,
        (nomina_id,),
    )
