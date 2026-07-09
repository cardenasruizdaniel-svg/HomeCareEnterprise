"""
=========================================================
HomeCare Enterprise
Repositorio: Turnos programados (calendario de turnos)
=========================================================
"""

from database.database import consultar_todos, consultar_uno, ejecutar


class TurnosRepository:

    @staticmethod
    def listar_rango(fecha_inicio: str, fecha_fin: str):
        return consultar_todos(
            """
            SELECT t.*, pf.nombre_completo, pf.especialidad_principal
            FROM turnos_programados t
            JOIN profesionales pf ON pf.id = t.profesional_id
            WHERE t.fecha BETWEEN ? AND ?
            ORDER BY t.fecha, t.hora_inicio
            """,
            (fecha_inicio, fecha_fin),
        )

    @staticmethod
    def listar_por_profesional(profesional_id: int, fecha_inicio: str, fecha_fin: str):
        return consultar_todos(
            """
            SELECT * FROM turnos_programados
            WHERE profesional_id=? AND fecha BETWEEN ? AND ?
            ORDER BY fecha, hora_inicio
            """,
            (profesional_id, fecha_inicio, fecha_fin),
        )

    @staticmethod
    def obtener(turno_id: int):
        return consultar_uno("SELECT * FROM turnos_programados WHERE id=?", (turno_id,))

    @staticmethod
    def crear(datos: dict) -> int:
        datos.setdefault("paciente_id", None)
        datos.setdefault("catalogo_turno_id", None)
        return ejecutar(
            """
            INSERT INTO turnos_programados (
                profesional_id, paciente_id, catalogo_turno_id, fecha, turno, hora_inicio, hora_fin,
                zona, observaciones, usuario_creacion
            ) VALUES (
                :profesional_id, :paciente_id, :catalogo_turno_id, :fecha, :turno, :hora_inicio, :hora_fin,
                :zona, :observaciones, :usuario_creacion
            )
            """,
            datos,
        )

    @staticmethod
    def eliminar(turno_id: int):
        ejecutar("DELETE FROM turnos_programados WHERE id=?", (turno_id,))

    @staticmethod
    def visitas_del_profesional_en_fecha(profesional_id: int, fecha: str):
        return consultar_todos(
            """
            SELECT * FROM programaciones
            WHERE profesional_id=? AND fecha=?
              AND hora_real_inicio IS NOT NULL
            ORDER BY hora_real_inicio
            """,
            (profesional_id, fecha),
        )

    @staticmethod
    def listar_rango_con_paciente(fecha_inicio: str, fecha_fin: str):
        return consultar_todos(
            """
            SELECT t.*, pf.nombre_completo, pf.especialidad_principal,
                   (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente_nombre,
                   pa.tipo_cuidado AS paciente_tipo_cuidado
            FROM turnos_programados t
            JOIN profesionales pf ON pf.id = t.profesional_id
            LEFT JOIN pacientes pa ON pa.id = t.paciente_id
            WHERE t.fecha BETWEEN ? AND ?
            ORDER BY t.fecha, t.hora_inicio
            """,
            (fecha_inicio, fecha_fin),
        )

    @staticmethod
    def listar_por_paciente(paciente_id: int, fecha_inicio: str, fecha_fin: str):
        return consultar_todos(
            """
            SELECT t.*, pf.nombre_completo, pf.especialidad_principal
            FROM turnos_programados t
            JOIN profesionales pf ON pf.id = t.profesional_id
            WHERE t.paciente_id=? AND t.fecha BETWEEN ? AND ?
            ORDER BY t.fecha, t.hora_inicio
            """,
            (paciente_id, fecha_inicio, fecha_fin),
        )


class CatalogoTurnosRepository:

    @staticmethod
    def listar_activos():
        return consultar_todos("SELECT * FROM catalogo_turnos WHERE activo=1 ORDER BY nombre")

    @staticmethod
    def obtener(turno_id: int):
        return consultar_uno("SELECT * FROM catalogo_turnos WHERE id=?", (turno_id,))

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO catalogo_turnos(
                nombre, tramo1_inicio, tramo1_fin, tramo2_inicio, tramo2_fin, tipo_cuidado_aplica
            ) VALUES (
                :nombre, :tramo1_inicio, :tramo1_fin, :tramo2_inicio, :tramo2_fin, :tipo_cuidado_aplica
            )
            """,
            datos,
        )

    @staticmethod
    def desactivar(turno_id: int):
        ejecutar("UPDATE catalogo_turnos SET activo=0 WHERE id=?", (turno_id,))

    @staticmethod
    def sembrar_si_vacio():
        total = consultar_uno("SELECT COUNT(*) AS total FROM catalogo_turnos")
        if total and dict(total)["total"] > 0:
            return

        iniciales = [
            ("Turno 1 (partido: 8am-12m y 2pm-6pm)", "08:00", "12:00", "14:00", "18:00", "Ambos"),
            ("Turno 2 (continuo: 8am-4pm)", "08:00", "16:00", None, None, "Ambos"),
            ("Turno Día Completo (7am-7pm)", "07:00", "19:00", None, None, "Ventilado"),
            ("Turno Noche (7pm-7am)", "19:00", "07:00", None, None, "Ventilado"),
            ("Turno Medio Día (8am-1pm)", "08:00", "13:00", None, None, "Ambos"),
        ]
        for nombre, t1i, t1f, t2i, t2f, tipo in iniciales:
            ejecutar(
                """
                INSERT INTO catalogo_turnos(nombre, tramo1_inicio, tramo1_fin, tramo2_inicio, tramo2_fin, tipo_cuidado_aplica)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (nombre, t1i, t1f, t2i, t2f, tipo),
            )
