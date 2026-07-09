"""
=========================================================
HomeCare Enterprise
Dashboard Service
Sprint 3.4C
=========================================================
"""

from repositories.dashboard_repository import DashboardRepository


class DashboardService:
    """
    Servicio encargado de preparar la información
    utilizada por el Dashboard Ejecutivo.
    """

    def __init__(self):

        self.repository = DashboardRepository()

    # =====================================================
    # DASHBOARD
    # =====================================================

    def dashboard(self):

        datos = self.repository.dashboard_completo()

        datos["indicadores"] = (

            self.indicadores_dashboard()

        )

        datos["grafico"] = (

            self.grafico_produccion()

        )

        datos["agenda"] = (

            self.agenda_dashboard()

        )

        datos["alertas"] = (

            self.alertas_dashboard()

        )

        return datos
    
    # =====================================================
    # RESUMEN
    # =====================================================

    def resumen(self):

        return self.repository.resumen()
    
        # =====================================================
    # INDICADORES
    # =====================================================

    def indicadores(self):

        return self.repository.indicadores_principales()
    
        # =====================================================
    # FORMATEAR MONEDA
    # =====================================================

    def formato_moneda(
        self,
        valor,
    ) -> str:

        if valor is None:
            valor = 0

        return f"$ {valor:,.0f}".replace(",", ".")
    
        # =====================================================
    # FORMATEAR NÚMEROS
    # =====================================================

    def formato_numero(
        self,
        valor,
    ) -> str:

        if valor is None:
            valor = 0

        return f"{valor:,}".replace(",", ".")
    
        # =====================================================
    # FORMATEAR PORCENTAJE
    # =====================================================

    def formato_porcentaje(
        self,
        valor,
    ) -> str:

        if valor is None:
            valor = 0

        return f"{valor:.1f}%"
    
        # =====================================================
    # KPIs FORMATEADOS
    # =====================================================

    def indicadores_dashboard(self):

        datos = self.repository.indicadores_principales()

        return {

            "pacientes": {

                "valor": datos["pacientes"],

                "texto": self.formato_numero(
                    datos["pacientes"]
                ),
            },

            "profesionales": {

                "valor": datos["profesionales"],

                "texto": self.formato_numero(
                    datos["profesionales"]
                ),
            },

            "visitas_hoy": {

                "valor": datos["visitas_hoy"],

                "texto": self.formato_numero(
                    datos["visitas_hoy"]
                ),
            },

            "pendientes": {

                "valor": datos["pendientes"],

                "texto": self.formato_numero(
                    datos["pendientes"]
                ),
            },

        }
    
        # =====================================================
    # PRODUCCIÓN PARA CHART.JS
    # =====================================================

    def grafico_produccion(self):

        datos = self.repository.produccion_mensual()

        return {

            "labels": [

                fila["periodo"]

                for fila in datos

            ],

            "values": [

                fila["total"]

                for fila in datos

            ]

        }
    
        # =====================================================
    # AGENDA
    # =====================================================

    def agenda_dashboard(self):

        agenda = self.repository.agenda_hoy()

        return {

            "total": len(agenda),

            "datos": agenda,

        }
    
        # =====================================================
    # ALERTAS
    # =====================================================

    def alertas_dashboard(self):

        alertas = self.repository.alertas()

        return {

            "datos": alertas,

            "cantidad":

                sum(

                    alertas.values()

                )

        }

    # =====================================================
    # COLOR DEL KPI
    # =====================================================

    def color_kpi(
        self,
        valor: int,
    ) -> str:

        if valor == 0:
            return "secondary"

        if valor < 10:
            return "warning"

        return "success"
    
        # =====================================================
    # TENDENCIA
    # =====================================================

    def tendencia(
        self,
        actual: int,
        anterior: int = 0,
    ):

        if anterior == 0:

            return {

                "valor": 0,

                "icono": "minus",

                "color": "secondary",

            }

        diferencia = actual - anterior

        porcentaje = round(
            (diferencia / anterior) * 100,
            1,
        )

        return {

            "valor": porcentaje,

            "icono":

                "arrow-up"

                if porcentaje >= 0

                else "arrow-down",

            "color":

                "success"

                if porcentaje >= 0

                else "danger",

        }
    
        # =====================================================
    # RESUMEN EJECUTIVO
    # =====================================================

    def resumen_ejecutivo(self):

        resumen = self.repository.resumen()

        return {

            "kpis":

                resumen["kpis"],

            "agenda":

                resumen["agenda_total"],

            "facturacion":

                self.formato_moneda(

                    resumen["facturacion"]

                ),

            "inventario":

                resumen["inventario"],

            "alertas":

                resumen["alertas"],

        }
    
        # =====================================================
    # CONTEXTO DASHBOARD
    # =====================================================

    def dashboard_context(self):

        return {

            "dashboard":

                self.dashboard(),

            "resumen":

                self.resumen_ejecutivo(),

        }