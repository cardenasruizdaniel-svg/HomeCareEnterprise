"""
HomeCare Enterprise - Plantillas de texto para visitas

Texto precargado para agilizar la digitación de la nota de la
visita. Se filtran segun el ROL/perfil de quien inicio sesion:
un cuidador solo ve plantillas para cuidadores, un enfermero
solo las de enfermería, etc. Los profesionales de la salud
(médicos, terapeutas, etc.) ademas pueden crear las suyas
propias para su propio uso, sin depender de administracion.

Una misma plantilla se puede asignar a VARIOS perfiles a la vez
(ej. Médico y Enfermero) -- 'rol_destinatario' guarda la lista
separada por comas (o 'Todos', para que la vean todos los
perfiles sin excepción).
"""

from repositories.plantillas_visita_repository import PlantillasVisitaRepository

ROLES_DESTINATARIO = ["Todos", "Cuidador", "Enfermero", "Médico", "Terapeuta", "Aplicador", "Curaciones"]

# Catálogo de "tipos de nota" -- lo que el profesional
# escoge PRIMERO al ir a registrar algo en la historia
# clínica (igual que el selector de "Formato de Historia").
# Cada tipo determina el rol de plantillas que se le muestra.
TIPOS_NOTA = [
    {"codigo": "medica", "nombre": "Nota Médica", "rol": "Médico"},
    {"codigo": "enfermeria", "nombre": "Nota de Enfermería", "rol": "Enfermero"},
    {"codigo": "cuidador", "nombre": "Nota de Cuidador", "rol": "Cuidador"},
    {"codigo": "aplicador", "nombre": "Nota de Aplicador", "rol": "Aplicador"},
    {"codigo": "curaciones", "nombre": "Nota de Curaciones", "rol": "Curaciones"},
    {"codigo": "terapia", "nombre": "Nota de Terapia", "rol": "Terapeuta"},
]


def normalizar_rol_profesional(especialidad_principal: str) -> str:
    """
    La especialidad del profesional es texto libre (ej.
    'Fisioterapeuta', 'Médico General', 'Auxiliar de
    Enfermería'), mientras que las plantillas se etiquetan
    con una categoria fija (ROLES_DESTINATARIO). Esta funcion
    traduce la una a la otra por palabras clave, para que un
    fisioterapeuta sí vea las plantillas de 'Terapeuta', etc.
    """

    texto = (especialidad_principal or "").lower()

    if "cuidador" in texto:
        return "Cuidador"
    if "enfermer" in texto:
        return "Enfermero"
    if "médic" in texto or "medic" in texto:
        return "Médico"
    if any(p in texto for p in ["terap", "fisio", "fonoaudi", "ocupacional", "respirator"]):
        return "Terapeuta"
    if "aplicador" in texto:
        return "Aplicador"

    return "Todos"


def _le_corresponde_por_rol(rol_destinatario: str, rol_buscado: str) -> bool:
    """
    'rol_destinatario' puede traer varios roles separados por
    coma (ej. 'Médico,Enfermero,Terapeuta') -- se considera que
    le corresponde a alguien si su rol está en esa lista, o si
    la plantilla es para 'Todos'.
    """
    roles = [r.strip() for r in (rol_destinatario or "Todos").split(",")]
    return "Todos" in roles or rol_buscado in roles


def listar_disponibles_para_profesional(rol_profesional: str, profesional_id: int = None):
    rol_normalizado = normalizar_rol_profesional(rol_profesional)
    return listar_disponibles_por_rol(rol_normalizado, profesional_id)


def listar_disponibles_por_rol(rol: str, profesional_id: int = None):
    """
    Igual que listar_disponibles_para_profesional, pero
    recibe el rol YA ELEGIDO explicitamente (desde el
    selector de "tipo de nota"), sin inferirlo de la
    especialidad del profesional.
    """
    candidatas = [dict(p) for p in PlantillasVisitaRepository.listar_candidatas(profesional_id)]
    return [
        p for p in candidatas
        if (profesional_id is not None and p.get("profesional_id") == profesional_id)
        or _le_corresponde_por_rol(p.get("rol_destinatario"), rol)
    ]


def listar_todas():
    return [dict(p) for p in PlantillasVisitaRepository.listar_todas()]


def obtener(plantilla_id: int):
    return PlantillasVisitaRepository.obtener(plantilla_id)


def crear_plantilla(nombre, tipo_servicio, subtipo, rol_destinatario, contenido, profesional_id,
                      es_administracion, usuario) -> int:

    if not nombre or not contenido:
        raise ValueError("El nombre y el contenido de la plantilla son obligatorios.")

    if not es_administracion and not profesional_id:
        raise ValueError("Una plantilla personal debe estar asociada a un profesional.")

    return PlantillasVisitaRepository.crear({
        "nombre": nombre,
        "tipo_servicio": tipo_servicio or "General",
        "subtipo": subtipo or None,
        "rol_destinatario": rol_destinatario or "Todos",
        "contenido": contenido,
        "profesional_id": None if es_administracion else profesional_id,
        "creado_por_administracion": 1 if es_administracion else 0,
        "usuario_creacion": usuario,
    })


def actualizar_plantilla(plantilla_id, nombre, tipo_servicio, subtipo, rol_destinatario, contenido) -> None:

    if not nombre or not contenido:
        raise ValueError("El nombre y el contenido de la plantilla son obligatorios.")

    PlantillasVisitaRepository.actualizar(plantilla_id, {
        "nombre": nombre,
        "tipo_servicio": tipo_servicio or "General",
        "subtipo": subtipo or None,
        "rol_destinatario": rol_destinatario or "Todos",
        "contenido": contenido,
    })


def desactivar(plantilla_id: int):
    PlantillasVisitaRepository.desactivar(plantilla_id)
