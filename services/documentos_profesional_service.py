"""HomeCare Enterprise - Servicio: Documentos del profesional"""

from datetime import date

from repositories.documentos_profesional_repository import DocumentosProfesionalRepository

TIPOS_DOCUMENTO = [
    "Título profesional",
    "Tarjeta profesional",
    "RETHUS",
    "Curso / Certificación",
    "Certificado de vacunación",
    "Certificado judicial",
    "Hoja de vida",
    "Referencias laborales",
    "Examen médico ocupacional",
    "Otro",
]


def listar_por_profesional(profesional_id: int):
    documentos = [dict(d) for d in DocumentosProfesionalRepository.listar_por_profesional(profesional_id)]

    hoy = date.today().isoformat()

    for d in documentos:
        if d.get("fecha_vencimiento"):
            d["vencido"] = d["fecha_vencimiento"] < hoy
        else:
            d["vencido"] = False

    return documentos


def obtener(documento_id: int):
    return DocumentosProfesionalRepository.obtener(documento_id)


def crear(profesional_id, tipo_documento, nombre, numero, entidad_emisora,
          fecha_expedicion, fecha_vencimiento, ruta_archivo, observaciones, usuario):

    if not tipo_documento:
        raise ValueError("Debe indicar el tipo de documento.")

    return DocumentosProfesionalRepository.crear({
        "profesional_id": profesional_id,
        "tipo_documento": tipo_documento,
        "nombre": nombre,
        "numero": numero,
        "entidad_emisora": entidad_emisora,
        "fecha_expedicion": fecha_expedicion or None,
        "fecha_vencimiento": fecha_vencimiento or None,
        "ruta_archivo": ruta_archivo,
        "observaciones": observaciones,
        "usuario_creacion": usuario,
    })


def eliminar(documento_id: int):
    return DocumentosProfesionalRepository.eliminar(documento_id)


def vencidos_o_por_vencer(dias: int = 30):
    return DocumentosProfesionalRepository.vencidos_o_por_vencer(dias)
