"""
==============================================================
HomeCare Enterprise
Repositorio de Profesionales
Sprint 3.4A
Versión 8.0
==============================================================
"""

from __future__ import annotations

from typing import Any

from database.database import get_connection


class ProfesionalesRepository:
    """
    Repositorio Enterprise para la gestión de profesionales.

    Este repositorio centraliza las operaciones relacionadas con:

    • CRUD de profesionales
    • Agenda clínica
    • Motor Inteligente de Asignación
    • Centro de Despacho
    • Dashboard Ejecutivo
    • Georreferenciación
    • Analítica
    """

    # ======================================================
    # LISTAR PROFESIONALES
    # ======================================================

    @staticmethod
    def listar():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT p.*, u.usuario AS nombre_usuario_acceso, u.rol AS rol_sistema_actual,
                   u.activo AS cuenta_activa

            FROM profesionales p
            LEFT JOIN usuarios u ON u.id = p.usuario_id

            ORDER BY

                p.primer_apellido,

                p.primer_nombre

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos

    # ======================================================
    # OBTENER POR ID
    # ======================================================

    @staticmethod
    def obtener(

        profesional_id: int,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales

            WHERE id=?

        """,

        (

            profesional_id,

        ))

        dato = cursor.fetchone()

        conexion.close()

        return dato

    # ======================================================
    # OBTENER POR UUID
    # ======================================================

    @staticmethod
    def obtener_uuid(

        uuid: str,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales

            WHERE uuid=?

        """,

        (

            uuid,

        ))

        dato = cursor.fetchone()

        conexion.close()

        return dato

    # ======================================================
    # VALIDAR EXISTENCIA
    # ======================================================

    @staticmethod
    def existe(

        profesional_id: int,

    ) -> bool:

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT COUNT(*)

            FROM profesionales

            WHERE id=?

        """,

        (

            profesional_id,

        ))

        existe = cursor.fetchone()[0] > 0

        conexion.close()

        return existe

    # ======================================================
    # CREAR
    # ======================================================

    @staticmethod
    def crear(

        datos: dict[str, Any],

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            INSERT INTO profesionales(

                uuid,

                tipo_documento,

                documento,

                primer_nombre,

                segundo_nombre,

                primer_apellido,

                segundo_apellido,

                nombre_completo,

                registro_profesional,

                profesion,

                especialidad_principal,

                telefono,

                celular,

                correo,

                direccion,

                municipio,

                departamento,

                latitud,

                longitud,

                estado,

                disponible,

                acepta_urgencias,

                capacidad_diaria,

                tiempo_promedio_visita,

                radio_cobertura_km,

                observaciones,

                tipo_contrato,

                valor_hora,

                salario_fijo,

                banco,

                tipo_cuenta,

                numero_cuenta,

                usuario_id,

                usuario_creacion,

                firma_base64,

                foto_enrolamiento_base64

            )

            VALUES(

                :uuid,

                :tipo_documento,

                :documento,

                :primer_nombre,

                :segundo_nombre,

                :primer_apellido,

                :segundo_apellido,

                :nombre_completo,

                :registro_profesional,

                :profesion,

                :especialidad_principal,

                :telefono,

                :celular,

                :correo,

                :direccion,

                :municipio,

                :departamento,

                :latitud,

                :longitud,

                :estado,

                :disponible,

                :acepta_urgencias,

                :capacidad_diaria,

                :tiempo_promedio_visita,

                :radio_cobertura_km,

                :observaciones,

                :tipo_contrato,

                :valor_hora,

                :salario_fijo,

                :banco,

                :tipo_cuenta,

                :numero_cuenta,

                :usuario_id,

                :usuario_creacion,

                :firma_base64,

                :foto_enrolamiento_base64

            )

        """, datos)

        conexion.commit()

        nuevo_id = cursor.lastrowid

        conexion.close()

        return nuevo_id

    # ======================================================
    # ELIMINAR
    # ======================================================

    @staticmethod
    def eliminar(

        profesional_id: int,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            DELETE

            FROM profesionales

            WHERE id=?

        """,

        (

            profesional_id,

        ))

        conexion.commit()

        conexion.close()

        # ======================================================
    # PROFESIONALES ACTIVOS
    # ======================================================

    @staticmethod
    def activos():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales

            WHERE estado='ACTIVO'

            ORDER BY

                primer_apellido,

                primer_nombre

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # PROFESIONALES DISPONIBLES
    # ======================================================

    @staticmethod
    def disponibles():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales

            WHERE estado='ACTIVO'
              AND disponible=1

            ORDER BY

                primer_apellido,

                primer_nombre

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # POR ESPECIALIDAD PRINCIPAL
    # ======================================================

    @staticmethod
    def por_especialidad(

        especialidad: str,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales

            WHERE especialidad_principal=?
              AND estado='ACTIVO'

            ORDER BY

                primer_apellido,

                primer_nombre

        """,

        (

            especialidad,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # ESPECIALIDADES DEL PROFESIONAL
    # ======================================================

    @staticmethod
    def especialidades(

        profesional_id: int,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales_especialidades

            WHERE profesional_id=?
              AND activa=1

            ORDER BY principal DESC,
                     especialidad

        """,

        (

            profesional_id,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # ACTUALIZAR INFORMACIÓN
    # ======================================================

    @staticmethod
    def actualizar(

        profesional_id: int,

        datos: dict,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        datos["id"] = profesional_id

        cursor.execute("""

            UPDATE profesionales

            SET

                telefono=:telefono,

                celular=:celular,

                correo=:correo,

                direccion=:direccion,

                municipio=:municipio,

                departamento=:departamento,

                latitud=:latitud,

                longitud=:longitud,

                registro_profesional=:registro_profesional,

                profesion=:profesion,

                especialidad_principal=:especialidad_principal,

                capacidad_diaria=:capacidad_diaria,

                tiempo_promedio_visita=:tiempo_promedio_visita,

                radio_cobertura_km=:radio_cobertura_km,

                observaciones=:observaciones,

                tipo_contrato=:tipo_contrato,

                valor_hora=:valor_hora,

                salario_fijo=:salario_fijo,

                banco=:banco,

                tipo_cuenta=:tipo_cuenta,

                numero_cuenta=:numero_cuenta,

                usuario_id=:usuario_id,

                usuario_actualizacion=:usuario_actualizacion,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=:id

        """, datos)

        conexion.commit()

        conexion.close()


    # ======================================================
    # CAMBIAR ESTADO
    # ======================================================

    @staticmethod
    def cambiar_estado(

        profesional_id: int,

        estado: str,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE profesionales

            SET

                estado=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """,

        (

            estado,

            profesional_id,

        ))

        conexion.commit()

        conexion.close()


    # ======================================================
    # CAMBIAR DISPONIBILIDAD
    # ======================================================

    @staticmethod
    def cambiar_disponibilidad(

        profesional_id: int,

        disponible: int,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE profesionales

            SET

                disponible=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """,

        (

            disponible,

            profesional_id,

        ))

        conexion.commit()

        conexion.close()


    # ======================================================
    # ACEPTA URGENCIAS
    # ======================================================

    @staticmethod
    def acepta_urgencias(

        profesional_id: int,

        acepta: int,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE profesionales

            SET

                acepta_urgencias=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """,

        (

            acepta,

            profesional_id,

        ))

        conexion.commit()

        conexion.close()

            # ======================================================
    # AGENDA DEL PROFESIONAL
    # ======================================================

    @staticmethod
    def agenda_hoy(

        profesional_id: int,

        fecha: str,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE profesional_id=?
              AND fecha=?

            ORDER BY hora_inicio

        """,

        (

            profesional_id,

            fecha,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # CARGA LABORAL
    # ======================================================

    @staticmethod
    def carga_laboral(

        profesional_id: int,

        fecha: str,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) visitas,

                COALESCE(

                    SUM(duracion),

                    0

                ) minutos

            FROM programaciones

            WHERE profesional_id=?
              AND fecha=?
              AND estado<>'CANCELADA'

        """,

        (

            profesional_id,

            fecha,

        ))

        datos = cursor.fetchone()

        conexion.close()

        return datos


    # ======================================================
    # HORAS PROGRAMADAS
    # ======================================================

    @staticmethod
    def horas_programadas(

        profesional_id: int,

        fecha: str,

    ):

        datos = ProfesionalesRepository.carga_laboral(

            profesional_id,

            fecha,

        )

        minutos = datos["minutos"] if datos else 0

        return round(minutos / 60, 2)


    # ======================================================
    # DISPONIBILIDAD REAL
    # ======================================================

    @staticmethod
    def disponibilidad_real(

        profesional_id: int,

        fecha: str,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                capacidad_diaria

            FROM profesionales

            WHERE id=?

        """,

        (

            profesional_id,

        ))

        profesional = cursor.fetchone()

        conexion.close()

        if not profesional:

            return None

        carga = ProfesionalesRepository.carga_laboral(

            profesional_id,

            fecha,

        )

        visitas = carga["visitas"]

        capacidad = profesional["capacidad_diaria"]

        return {

            "capacidad": capacidad,

            "ocupadas": visitas,

            "disponibles": max(

                capacidad - visitas,

                0,

            )

        }


    # ======================================================
    # DISPONIBLES PARA FECHA
    # ======================================================

    @staticmethod
    def disponibles_fecha(

        fecha: str,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales

            WHERE estado='ACTIVO'
              AND disponible=1

            ORDER BY

                primer_apellido,

                primer_nombre

        """)

        profesionales = cursor.fetchall()

        conexion.close()

        resultado = []

        for profesional in profesionales:

            disponibilidad = ProfesionalesRepository.disponibilidad_real(

                profesional["id"],

                fecha,

            )

            if disponibilidad and disponibilidad["disponibles"] > 0:

                resultado.append(profesional)

        return resultado


    # ======================================================
    # HORARIO DISPONIBLE
    # ======================================================

    @staticmethod
    def horario_disponible(

        profesional_id: int,

        fecha: str,

        hora_inicio: str,

        hora_fin: str,

    ) -> bool:

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT COUNT(*)

            FROM programaciones

            WHERE profesional_id=?
              AND fecha=?
              AND estado<>'CANCELADA'
              AND (

                    hora_inicio < ?
                AND hora_fin > ?

              )

        """,

        (

            profesional_id,

            fecha,

            hora_fin,

            hora_inicio,

        ))

        ocupado = cursor.fetchone()[0]

        conexion.close()

        return ocupado == 0


    # ======================================================
    # OCUPACIÓN GENERAL
    # ======================================================

    @staticmethod
    def ocupacion(

        fecha: str,

    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                profesional_id,

                COUNT(*) visitas,

                SUM(duracion) minutos

            FROM programaciones

            WHERE fecha=?

              AND estado<>'CANCELADA'

            GROUP BY profesional_id

            ORDER BY visitas DESC

        """,

        (

            fecha,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos
    
        # ======================================================
    # ACTUALIZAR UBICACIÓN GPS
    # ======================================================

    @staticmethod
    def actualizar_ubicacion(
        profesional_id: int,
        latitud: float,
        longitud: float,
        velocidad: float = 0,
        precision_gps: float = 0,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            INSERT INTO profesionales_ubicacion(

                profesional_id,
                latitud,
                longitud,
                velocidad,
                precision_gps,
                fecha_actualizacion

            )

            VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)

        """,(

            profesional_id,
            latitud,
            longitud,
            velocidad,
            precision_gps

        ))

        conexion.commit()
        conexion.close()


    # ======================================================
    # ÚLTIMA UBICACIÓN
    # ======================================================

    @staticmethod
    def ultima_ubicacion(
        profesional_id: int,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales_ubicacion

            WHERE profesional_id=?

            ORDER BY fecha_actualizacion DESC

            LIMIT 1

        """,(profesional_id,))

        dato = cursor.fetchone()

        conexion.close()

        return dato


    # ======================================================
    # ZONAS DE COBERTURA
    # ======================================================

    @staticmethod
    def zonas_cobertura(
        profesional_id: int,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales_zonas

            WHERE profesional_id=?

            ORDER BY prioridad,
                     municipio,
                     barrio

        """,(profesional_id,))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # MUNICIPIOS DE COBERTURA
    # ======================================================

    @staticmethod
    def municipios_cobertura():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT DISTINCT

                municipio

            FROM profesionales_zonas

            ORDER BY municipio

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # RADIO DE COBERTURA
    # ======================================================

    @staticmethod
    def radio_cobertura(
        profesional_id: int,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                radio_cobertura_km

            FROM profesionales

            WHERE id=?

        """,(profesional_id,))

        dato = cursor.fetchone()

        conexion.close()

        if dato:

            return dato["radio_cobertura_km"]

        return 0


    # ======================================================
    # VEHÍCULOS DEL PROFESIONAL
    # ======================================================

    @staticmethod
    def vehiculos(
        profesional_id: int,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales_vehiculos

            WHERE profesional_id=?
              AND activo=1

            ORDER BY tipo,
                     placa

        """,(profesional_id,))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # PROFESIONALES CERCANOS
    # ======================================================

    @staticmethod
    def profesionales_cercanos(
        municipio: str,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT DISTINCT

                p.*

            FROM profesionales p

            INNER JOIN profesionales_zonas z

                ON z.profesional_id=p.id

            WHERE

                z.municipio=?

                AND p.estado='ACTIVO'

                AND p.disponible=1

            ORDER BY

                p.primer_apellido,

                p.primer_nombre

        """,(municipio,))

        datos = cursor.fetchall()

        conexion.close()

        return datos
    
        # ======================================================
    # DESPACHO DEL DÍA
    # ======================================================

    @staticmethod
    def despacho_dia(
        fecha: str,
    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                pr.id,

                pr.nombre_completo,

                COUNT(pg.id) visitas,

                COALESCE(
                    SUM(pg.duracion),
                    0
                ) minutos

            FROM profesionales pr

            LEFT JOIN programaciones pg

                ON pg.profesional_id = pr.id

                AND pg.fecha = ?

            GROUP BY

                pr.id,

                pr.nombre_completo

            ORDER BY visitas DESC

        """, (

            fecha,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # VISITAS REALIZADAS
    # ======================================================

    @staticmethod
    def visitas_realizadas(
        profesional_id: int,
    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT COUNT(*)

            FROM programaciones

            WHERE profesional_id=?

              AND estado='FINALIZADA'

        """,(

            profesional_id,

        ))

        total = cursor.fetchone()[0]

        conexion.close()

        return total


    # ======================================================
    # VISITAS PENDIENTES
    # ======================================================

    @staticmethod
    def visitas_pendientes(
        profesional_id: int,
    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT COUNT(*)

            FROM programaciones

            WHERE profesional_id=?

              AND estado IN(

                    'PROGRAMADA',

                    'DESPACHADA',

                    'EN_RUTA',

                    'EN_ATENCION'

              )

        """,(

            profesional_id,

        ))

        total = cursor.fetchone()[0]

        conexion.close()

        return total


    # ======================================================
    # PRODUCTIVIDAD
    # ======================================================

    @staticmethod
    def productividad():

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                pr.id,

                pr.nombre_completo,

                COUNT(pg.id) total,

                SUM(

                    CASE

                        WHEN pg.estado='FINALIZADA'

                        THEN 1

                        ELSE 0

                    END

                ) realizadas

            FROM profesionales pr

            LEFT JOIN programaciones pg

                ON pg.profesional_id=pr.id

            GROUP BY

                pr.id,

                pr.nombre_completo

            ORDER BY realizadas DESC

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # TOP PROFESIONALES
    # ======================================================

    @staticmethod
    def top_profesionales(
        limite: int = 10,
    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                pr.id,

                pr.nombre_completo,

                COUNT(pg.id) visitas

            FROM profesionales pr

            INNER JOIN programaciones pg

                ON pg.profesional_id=pr.id

            GROUP BY

                pr.id,

                pr.nombre_completo

            ORDER BY visitas DESC

            LIMIT ?

        """,(

            limite,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # EFICIENCIA
    # ======================================================

    @staticmethod
    def eficiencia():

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) total,

                SUM(

                    CASE

                        WHEN estado='ACTIVO'

                        THEN 1

                        ELSE 0

                    END

                ) activos,

                SUM(

                    CASE

                        WHEN disponible=1

                        THEN 1

                        ELSE 0

                    END

                ) disponibles

            FROM profesionales

        """)

        datos = cursor.fetchone()

        conexion.close()

        return datos


    # ======================================================
    # INDICADORES GENERALES
    # ======================================================

    @staticmethod
    def indicadores():

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) total,

                SUM(

                    CASE

                        WHEN estado='ACTIVO'

                        THEN 1

                        ELSE 0

                    END

                ) activos,

                SUM(

                    CASE

                        WHEN disponible=1

                        THEN 1

                        ELSE 0

                    END

                ) disponibles,

                AVG(capacidad_diaria)

            FROM profesionales

        """)

        datos = cursor.fetchone()

        conexion.close()

        return datos
    
        # ======================================================
    # DATASET PARA IA
    # ======================================================

    @staticmethod
    def dataset_ia():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                p.id,

                p.nombre_completo,

                p.profesion,

                p.especialidad_principal,

                p.capacidad_diaria,

                p.tiempo_promedio_visita,

                p.radio_cobertura_km,

                p.disponible,

                p.acepta_urgencias,

                p.latitud,

                p.longitud,

                COUNT(pg.id) AS visitas

            FROM profesionales p

            LEFT JOIN programaciones pg

                ON pg.profesional_id = p.id

            GROUP BY

                p.id

            ORDER BY

                visitas DESC

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # PROFESIONALES SIN VISITAS
    # ======================================================

    @staticmethod
    def sin_visitas():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales

            WHERE id NOT IN(

                SELECT DISTINCT profesional_id

                FROM programaciones

                WHERE profesional_id IS NOT NULL

            )

            ORDER BY

                primer_apellido,

                primer_nombre

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # PROFESIONALES SOBRECARGADOS
    # ======================================================

    @staticmethod
    def sobrecargados(fecha: str):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                pr.id,

                pr.nombre_completo,

                COUNT(pg.id) visitas,

                SUM(pg.duracion) minutos,

                pr.capacidad_diaria

            FROM profesionales pr

            INNER JOIN programaciones pg

                ON pg.profesional_id = pr.id

            WHERE pg.fecha = ?

              AND pg.estado<>'CANCELADA'

            GROUP BY pr.id

            HAVING visitas >= pr.capacidad_diaria

            ORDER BY visitas DESC

        """, (fecha,))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # RANKING INTELIGENTE
    # ======================================================

    @staticmethod
    def ranking_inteligente():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                id,

                nombre_completo,

                especialidad_principal,

                capacidad_diaria,

                disponible,

                acepta_urgencias,

                radio_cobertura_km

            FROM profesionales

            WHERE estado='ACTIVO'

            ORDER BY

                disponible DESC,

                acepta_urgencias DESC,

                capacidad_diaria DESC,

                radio_cobertura_km DESC

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # EXPORTAR PROFESIONALES
    # ======================================================

    @staticmethod
    def exportar():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales

            ORDER BY

                primer_apellido,

                primer_nombre

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # RESUMEN GENERAL
    # ======================================================

    @staticmethod
    def resumen_general():

        conexion = get_connection()
        cursor = conexion.cursor()

        resumen = {}

        cursor.execute("""

            SELECT COUNT(*)

            FROM profesionales

        """)

        resumen["profesionales"] = cursor.fetchone()[0]

        cursor.execute("""

            SELECT COUNT(*)

            FROM profesionales

            WHERE estado='ACTIVO'

        """)

        resumen["activos"] = cursor.fetchone()[0]

        cursor.execute("""

            SELECT COUNT(*)

            FROM profesionales

            WHERE disponible=1

        """)

        resumen["disponibles"] = cursor.fetchone()[0]

        cursor.execute("""

            SELECT COUNT(*)

            FROM profesionales

            WHERE acepta_urgencias=1

        """)

        resumen["urgencias"] = cursor.fetchone()[0]

        conexion.close()

        return resumen
    
        # ======================================================
    # BUSCAR POR DOCUMENTO
    # ======================================================

    @staticmethod
    def buscar_documento(
        documento: str,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales

            WHERE documento=?

        """,(documento,))

        dato = cursor.fetchone()

        conexion.close()

        return dato


    # ======================================================
    # BUSCAR POR TEXTO
    # ======================================================

    @staticmethod
    def buscar(
        texto: str,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        filtro = f"%{texto}%"

        cursor.execute("""

            SELECT *

            FROM profesionales

            WHERE

                nombre_completo LIKE ?

                OR documento LIKE ?

                OR profesion LIKE ?

                OR especialidad_principal LIKE ?

            ORDER BY

                primer_apellido,

                primer_nombre

        """,(

            filtro,
            filtro,
            filtro,
            filtro,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # ACTUALIZAR CAPACIDAD
    # ======================================================

    @staticmethod
    def actualizar_capacidad(
        profesional_id: int,
        capacidad: int,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE profesionales

            SET

                capacidad_diaria=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """,(

            capacidad,
            profesional_id,

        ))

        conexion.commit()
        conexion.close()


    # ======================================================
    # ACTUALIZAR RADIO COBERTURA
    # ======================================================

    @staticmethod
    def actualizar_radio(
        profesional_id: int,
        radio: float,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE profesionales

            SET

                radio_cobertura_km=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """,(

            radio,
            profesional_id,

        ))

        conexion.commit()
        conexion.close()


    # ======================================================
    # PROFESIONALES POR PROFESIÓN
    # ======================================================

    @staticmethod
    def por_profesion(
        profesion: str,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales

            WHERE profesion=?

              AND estado='ACTIVO'

            ORDER BY

                primer_apellido,

                primer_nombre

        """,(profesion,))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # ESTADÍSTICAS POR MUNICIPIO
    # ======================================================

    @staticmethod
    def estadisticas_municipio():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                municipio,

                COUNT(*) total

            FROM profesionales

            GROUP BY municipio

            ORDER BY total DESC

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # REINICIAR DISPONIBILIDAD
    # ======================================================

    @staticmethod
    def reiniciar_disponibilidad():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE profesionales

            SET

                disponible=1,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE estado='ACTIVO'

        """)

        conexion.commit()

        afectados = cursor.rowcount

        conexion.close()

        return afectados


    # ======================================================
    # PROFESIONALES CON UBICACIÓN
    # ======================================================

    @staticmethod
    def con_ubicacion():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales

            WHERE

                latitud IS NOT NULL

                AND longitud IS NOT NULL

                AND estado='ACTIVO'

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos
    @staticmethod
    def actualizar_firma(profesional_id: int, firma_base64: str):
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE profesionales SET firma_base64=? WHERE id=?",
            (firma_base64, profesional_id),
        )
        conexion.commit()
        conexion.close()

    @staticmethod
    def actualizar_foto_enrolamiento(profesional_id: int, foto_base64: str):
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE profesionales SET foto_enrolamiento_base64=? WHERE id=?",
            (foto_base64, profesional_id),
        )
        conexion.commit()
        conexion.close()
