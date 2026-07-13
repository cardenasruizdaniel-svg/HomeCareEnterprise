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

    # =====================================================
    # RESUMEN GERENCIAL (financiero + operativo + inventario)
    # =====================================================

    def resumen_gerencial(self):
        """
        Vista consolidada para gerencia: qué está facturando,
        qué debe cobrar, cuánto vale el inventario, cuánto se
        ha comprado, y qué alertas requieren atención -- todo
        en un solo lugar, con datos reales de los módulos
        (no de tablas que ya no existen).
        """
        from database.database import consultar_uno, consultar_todos

        # --- Financiero: facturación del mes actual vs el anterior ---
        fila_mes_actual = consultar_uno(
            "SELECT COALESCE(SUM(valor_total),0) AS total, COUNT(*) AS cantidad FROM facturas_electronicas "
            "WHERE strftime('%Y-%m', fecha_emision) = strftime('%Y-%m','now')"
        )
        fila_mes_anterior = consultar_uno(
            "SELECT COALESCE(SUM(valor_total),0) AS total FROM facturas_electronicas "
            "WHERE strftime('%Y-%m', fecha_emision) = strftime('%Y-%m','now','-1 month')"
        )
        facturado_mes = dict(fila_mes_actual)["total"] if fila_mes_actual else 0
        facturas_mes = dict(fila_mes_actual)["cantidad"] if fila_mes_actual else 0
        facturado_mes_anterior = dict(fila_mes_anterior)["total"] if fila_mes_anterior else 0
        tendencia_facturacion = self.tendencia(facturado_mes, facturado_mes_anterior)

        # --- Cartera pendiente de cobro ---
        fila_cartera = consultar_uno(
            "SELECT COALESCE(SUM(valor_total),0) AS total, COUNT(*) AS cantidad FROM facturas_electronicas "
            "WHERE estado NOT IN ('Pagada', 'Anulada')"
        )
        cartera_pendiente = dict(fila_cartera)["total"] if fila_cartera else 0
        facturas_pendientes = dict(fila_cartera)["cantidad"] if fila_cartera else 0

        # --- Inventario: valor y compras del mes ---
        try:
            from services import inventario_service
            existencias = inventario_service.informe_existencias()
            valor_inventario = existencias["total_valorizado"]
            insumos_stock_bajo = len(existencias["insumos_stock_bajo"])
            vencimientos = inventario_service.alertas_vencimiento(60)
            lotes_por_vencer = len([v for v in vencimientos if not v["vencido"]])
            lotes_vencidos = len([v for v in vencimientos if v["vencido"]])

            from datetime import date
            primer_dia_mes = date.today().replace(day=1).isoformat()
            hoy = date.today().isoformat()
            compras_mes_informe = inventario_service.informe_compras(primer_dia_mes, hoy)
            compras_mes = compras_mes_informe["total_comprado"]

            convenios_vigentes = len([c for c in inventario_service.listar_convenios() if c["estado"] == "Vigente"])
        except Exception:
            valor_inventario = insumos_stock_bajo = lotes_por_vencer = lotes_vencidos = compras_mes = convenios_vigentes = 0

        # --- Operativo ---
        indicadores = self.repository.indicadores_principales()

        fila_visitas_mes = consultar_uno(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN estado='Completada' THEN 1 ELSE 0 END) AS completadas "
            "FROM programaciones WHERE strftime('%Y-%m', fecha) = strftime('%Y-%m','now')"
        )
        visitas_mes = dict(fila_visitas_mes)["total"] if fila_visitas_mes else 0
        visitas_completadas_mes = (dict(fila_visitas_mes)["completadas"] or 0) if fila_visitas_mes else 0
        porcentaje_cumplimiento = round((visitas_completadas_mes / visitas_mes) * 100, 1) if visitas_mes else 0

        return {
            "facturado_mes": facturado_mes, "facturado_mes_texto": self.formato_moneda(facturado_mes),
            "facturas_mes": facturas_mes, "tendencia_facturacion": tendencia_facturacion,
            "cartera_pendiente": cartera_pendiente, "cartera_pendiente_texto": self.formato_moneda(cartera_pendiente),
            "facturas_pendientes": facturas_pendientes,
            "valor_inventario": valor_inventario, "valor_inventario_texto": self.formato_moneda(valor_inventario),
            "compras_mes": compras_mes, "compras_mes_texto": self.formato_moneda(compras_mes),
            "insumos_stock_bajo": insumos_stock_bajo, "lotes_por_vencer": lotes_por_vencer, "lotes_vencidos": lotes_vencidos,
            "convenios_vigentes": convenios_vigentes,
            "pacientes_activos": indicadores.get("pacientes", 0),
            "profesionales_activos": indicadores.get("profesionales", 0),
            "visitas_mes": visitas_mes, "visitas_completadas_mes": visitas_completadas_mes,
            "porcentaje_cumplimiento": porcentaje_cumplimiento,
        }

    def dashboard_context(self):

        return {

            "dashboard":

                self.dashboard(),

            "resumen":

                self.resumen_ejecutivo(),

        }