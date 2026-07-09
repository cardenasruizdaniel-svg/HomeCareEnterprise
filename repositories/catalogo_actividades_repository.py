"""HomeCare Enterprise - Repositorio: Catálogo de Actividades del Programa"""

from database.database import consultar_escalar, consultar_todos, consultar_uno, ejecutar

ACTIVIDADES_INICIALES = [
    ("Visita de valoración médica inicial", "Médica"),
    ("Visita de valoración médica final", "Médica"),
    ("Visita de Medicina General", "Médica"),
    ("Curaciones", "Enfermería"),
    ("Aplicación de Medicamentos", "Aplicador"),
    ("Aplicación de Sueros", "Aplicador"),
    ("Cuidador", "Cuidado"),
    ("Terapia de Fonoaudiología", "Terapia"),
    ("Terapia Respiratoria", "Terapia"),
    ("Terapia Física", "Terapia"),
    ("Terapia Ocupacional", "Terapia"),
    ("Consulta con especialista a domicilio - Pediatra", "Especialista"),
    ("Consulta con especialista a domicilio - Fisiatra", "Especialista"),
    ("Visita de enfermería profesional", "Enfermería"),
    ("Apoyo nutricional a domicilio", "Apoyo"),
    ("Soporte psicológico a domicilio", "Apoyo"),
    ("Telemedicina y monitoreo a distancia", "Telemedicina"),
    ("Trabajo social", "Apoyo"),
]

# Actividades que ya no se ofrecen -- se desactivan (no se
# borran, para no perder el historial de lo ya asignado con
# ellas) en las instalaciones que ya las tenian sembradas.
ACTIVIDADES_RETIRADAS = [
    "Toma y traslado de muestras de laboratorio",
    "Manejo de insumos y elementos de protección",
    "Manejo y recolección de residuos hospitalarios",
]


class CatalogoActividadesRepository:

    @staticmethod
    def sembrar_si_vacio():
        # Ya no se detiene si la tabla tiene datos: agrega
        # cualquier actividad del catalogo unificado que aun no
        # exista (por nombre), para que instalaciones antiguas
        # reciban las actividades nuevas (ej. Curaciones,
        # Aplicador) sin duplicar las que ya tenian.
        for nombre, categoria in ACTIVIDADES_INICIALES:
            existe = consultar_escalar(
                "SELECT COUNT(*) FROM catalogo_actividades WHERE nombre=?", (nombre,)
            )
            if not existe:
                ejecutar(
                    "INSERT INTO catalogo_actividades(nombre, categoria) VALUES (?, ?)",
                    (nombre, categoria),
                )

        # Las actividades que ya no se ofrecen se desactivan
        # (no se borran, para no perder el historial de lo que
        # ya se asigno con ellas en el pasado).
        for nombre in ACTIVIDADES_RETIRADAS:
            ejecutar(
                "UPDATE catalogo_actividades SET activo=0 WHERE nombre=?", (nombre,)
            )

    @staticmethod
    def listar_activas():
        return consultar_todos("SELECT * FROM catalogo_actividades WHERE activo=1 ORDER BY categoria, nombre")

    @staticmethod
    def obtener(actividad_id: int):
        return consultar_uno("SELECT * FROM catalogo_actividades WHERE id=?", (actividad_id,))

    @staticmethod
    def crear(nombre: str, categoria: str) -> int:
        return ejecutar(
            "INSERT INTO catalogo_actividades(nombre, categoria) VALUES (?, ?)",
            (nombre, categoria),
        )

    @staticmethod
    def desactivar(actividad_id: int):
        ejecutar("UPDATE catalogo_actividades SET activo=0 WHERE id=?", (actividad_id,))
