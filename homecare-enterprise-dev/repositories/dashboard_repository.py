"""
=========================================================
HomeCare Enterprise
Dashboard Repository
Sprint 3.4C
=========================================================
"""

from repositories.base_repository import BaseRepository


class DashboardRepository(BaseRepository):

    """
    Repositorio encargado de obtener todos los indicadores
    utilizados por el Dashboard Ejecutivo.
    """

    def __init__(self):

        super().__init__()

    # =====================================================
    # EJECUTAR SQL
    # =====================================================

    def execute(
        self,
        sql: str,
        parametros: tuple = (),
    ):
        return super().execute(
            sql,
            parametros,
        )
    
        # =====================================================
    # CONSULTAR MUCHOS
    # =====================================================

    def query(
        self,
        sql: str,
        parametros: tuple = (),
    ):
        return super().query(
            sql,
            parametros,
        )
    
        # =====================================================
    # CONSULTAR UNO
    # =====================================================

    def query_one(
        self,
        sql: str,
        parametros: tuple = (),
    ):
        return super().query_one(
            sql,
            parametros,
        )
    
        # =====================================================
    # CONSULTAR ESCALAR
    # =====================================================

    def scalar(
        self,
        sql: str,
        parametros: tuple = (),
    ):
        return super().scalar(
            sql,
            parametros,
        )
    
        # =====================================================
    # TOTAL PACIENTES
    # =====================================================

    def total_pacientes(self) -> int:

        sql = """
            SELECT COUNT(*)
            FROM pacientes
        """

        return self.safe_scalar(sql)
    
        # =====================================================
    # TOTAL PROFESIONALES
    # =====================================================

    def total_profesionales(self) -> int:

        sql = """
            SELECT COUNT(*)
            FROM profesionales
        """

        return self.safe_scalar(sql)
    
        # =====================================================
    # VISITAS PROGRAMADAS HOY
    # =====================================================

    def visitas_hoy(self) -> int:

        sql = """
            SELECT COUNT(*)

            FROM programaciones

            WHERE DATE(fecha)=DATE('now')
        """

        return self.safe_scalar(sql)
    
        # =====================================================
    # VISITAS PENDIENTES
    # =====================================================

    def visitas_pendientes(self) -> int:

        sql = """
            SELECT COUNT(*)

            FROM programaciones

            WHERE estado='Pendiente'
        """

        return self.safe_scalar(sql)
    
        # =====================================================
    # INDICADORES PRINCIPALES
    # =====================================================

    def indicadores_principales(self):

        return {

            "pacientes":

                self.total_pacientes(),

            "profesionales":

                self.total_profesionales(),

            "visitas_hoy":

                self.visitas_hoy(),

            "pendientes":

                self.visitas_pendientes(),

        }
    
        # =====================================================
    # CONSULTA ESCALAR SEGURA
    # =====================================================

    def safe_scalar(
        self,
        sql: str,
        parametros: tuple = (),
        default: int = 0,
    ) -> int:
        """
        Ejecuta una consulta escalar de forma segura.
        Si ocurre cualquier error devuelve el valor por defecto.
        """

        try:

            resultado = self.scalar(
                sql,
                parametros,
            )

            if resultado is None:
                return default

            return resultado

        except Exception:

            return default
        
        # =====================================================
    # VERIFICAR TABLA
    # =====================================================

    def existe_tabla(
        self,
        tabla: str,
    ) -> bool:

        sql = """
            SELECT COUNT(*)

            FROM sqlite_master

            WHERE type='table'

            AND name=?
        """

        return self.safe_scalar(
            sql,
            (tabla,),
        ) > 0
    
        # =====================================================
    # AGENDA DEL DÍA
    # =====================================================

    def agenda_hoy(
        self,
        limite: int = 10,
    ):

        if not self.existe_tabla("programaciones"):
            return []

        sql = """
            SELECT

                id,

                paciente_id,

                profesional_id,

                fecha,

                hora,

                servicio,

                estado,

                prioridad,

                direccion,

                municipio
        """

        try:

            return self.fetch_list(
                sql,
                (limite,),
            )

        except Exception:

            return []
        
        # =====================================================
    # ALERTAS OPERATIVAS
    # =====================================================

    def alertas(self):

        return {

            "visitas_pendientes":

                self.visitas_pendientes(),

            "visitas_hoy":

                self.visitas_hoy(),

        }
    
        # =====================================================
    # PRODUCCIÓN MENSUAL
    # =====================================================

    def produccion_mensual(self):

        if not self.existe_tabla("programaciones"):
            return []

        sql = """
            SELECT

                strftime('%Y-%m', fecha) AS periodo,

                COUNT(*) AS total

            FROM programaciones

            GROUP BY periodo

            ORDER BY periodo DESC

            LIMIT 12
        """

        try:

            return self.fetch_list(sql)

        except Exception:

            return []
        
        # =====================================================
    # PROFESIONALES POR PROFESIÓN
    # =====================================================

    def profesionales_por_profesion(self):

        if not self.existe_tabla("profesionales"):
            return []

        sql = """
            SELECT

                profesion,

                COUNT(*) AS total

            FROM profesionales

            GROUP BY profesion

            ORDER BY total DESC
        """

        try:

            return self.fetch_list(sql)

        except Exception:

            return []
        
        # =====================================================
    # DASHBOARD EJECUTIVO
    # =====================================================

    def dashboard(self):

        return {

            "kpis":

                self.indicadores_principales(),

            "agenda":

                self.agenda_hoy(),

            "alertas":

                self.alertas(),

            "produccion":

                self.produccion_mensual(),

            "profesionales":

                self.profesionales_por_profesion(),

        }
    
        # =====================================================
    # FACTURACIÓN
    # =====================================================

    def facturacion_mes(self):

        if not self.existe_tabla("facturacion"):
            return 0

        sql = """
            SELECT
                COALESCE(SUM(valor),0)

            FROM facturacion

            WHERE strftime('%Y-%m', fecha)=strftime('%Y-%m','now')
        """

        return self.safe_scalar(sql)
    
        # =====================================================
    # INVENTARIO
    # =====================================================

    def inventario_critico(self):

        if not self.existe_tabla("inventario"):
            return 0

        sql = """
            SELECT COUNT(*)

            FROM inventario

            WHERE stock<=stock_minimo
        """

        return self.safe_scalar(sql)
    
        # =====================================================
    # DASHBOARD EJECUTIVO COMPLETO
    # =====================================================

    def dashboard_completo(self):

        return {

            "indicadores":

                self.indicadores_principales(),

            "agenda":

                self.agenda_hoy(),

            "alertas":

                self.alertas(),

            "produccion":

                self.produccion_mensual(),

            "profesionales":

                self.profesionales_por_profesion(),

            "facturacion":

                self.facturacion_mes(),

            "inventario":

                self.inventario_critico(),

        }
    
        # =====================================================
    # RESUMEN EJECUTIVO
    # =====================================================

    def resumen(self):

        datos = self.dashboard_completo()

        return {

            "kpis":

                datos["indicadores"],

            "facturacion":

                datos["facturacion"],

            "inventario":

                datos["inventario"],

            "agenda_total":

                len(datos["agenda"]),

            "alertas":

                datos["alertas"],

        }