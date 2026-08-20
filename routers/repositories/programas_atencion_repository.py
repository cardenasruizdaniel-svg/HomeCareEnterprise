"""HomeCare Enterprise - Repositorio: Programas de Atención"""

from database.database import consultar_escalar, consultar_todos, consultar_uno, ejecutar

PROGRAMAS_INICIALES = [
    {
        "nombre": "Paciente Crónico Complejidad Alta - Con Traqueostomía",
        "tipo": "Crónico Complejidad Alta",
        "subtipo": "Con Traqueostomía",
        "descripcion": "Paciente crónico de alta complejidad que requiere manejo de traqueostomía.",
    },
    {
        "nombre": "Paciente Crónico Complejidad Alta - Paciente Neurológico Agudo",
        "tipo": "Crónico Complejidad Alta",
        "subtipo": "Paciente Neurológico Agudo",
        "descripcion": "Paciente crónico de alta complejidad con cuadro neurológico agudo.",
    },
    {
        "nombre": "Paciente Crónico Baja Complejidad - Con Terapias",
        "tipo": "Crónico Baja Complejidad",
        "subtipo": "Con Terapias",
        "descripcion": "Paciente crónico de baja complejidad que requiere terapias.",
    },
    {
        "nombre": "Paciente Crónico Baja Complejidad - Sin Terapias",
        "tipo": "Crónico Baja Complejidad",
        "subtipo": "Sin Terapias",
        "descripcion": "Paciente crónico de baja complejidad que no requiere terapias.",
    },
]


class ProgramasAtencionRepository:

    @staticmethod
    def sembrar_si_vacio():
        total = consultar_escalar("SELECT COUNT(*) FROM programas_atencion")
        if total and total > 0:
            return

        for programa in PROGRAMAS_INICIALES:
            ejecutar(
                """
                INSERT INTO programas_atencion(nombre, tipo, subtipo, descripcion)
                VALUES (:nombre, :tipo, :subtipo, :descripcion)
                """,
                programa,
            )

    @staticmethod
    def listar_activos():
        return consultar_todos(
            "SELECT * FROM programas_atencion WHERE activo=1 ORDER BY tipo, subtipo"
        )

    @staticmethod
    def obtener(programa_id: int):
        return consultar_uno("SELECT * FROM programas_atencion WHERE id=?", (programa_id,))

    @staticmethod
    def crear(nombre, tipo, subtipo, descripcion, usuario_id) -> int:
        return ejecutar(
            """
            INSERT INTO programas_atencion(nombre, tipo, subtipo, descripcion, usuario_creacion)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nombre, tipo, subtipo, descripcion, usuario_id),
        )

    @staticmethod
    def desactivar(programa_id: int):
        ejecutar("UPDATE programas_atencion SET activo=0 WHERE id=?", (programa_id,))

    @staticmethod
    def conteo_pacientes_por_programa():
        return consultar_todos(
            """
            SELECT pa.id, pa.nombre, pa.tipo, pa.subtipo,
                   COUNT(pp.id) AS total_pacientes
            FROM programas_atencion pa
            LEFT JOIN paciente_programas pp
                ON pp.programa_id = pa.id AND pp.es_actual = 1
            WHERE pa.activo = 1
            GROUP BY pa.id
            ORDER BY pa.tipo, pa.subtipo
            """
        )
