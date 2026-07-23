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

        fila_autorizaciones = consultar_uno(
            "SELECT COUNT(*) AS total FROM autorizaciones_eps_servicios_adicionales WHERE estado='Pendiente autorización EPS'"
        )
        autorizaciones_pendientes = dict(fila_autorizaciones)["total"] if fila_autorizaciones else 0

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
            "autorizaciones_pendientes": autorizaciones_pendientes,
        }

    def grafico_produccion_detallado(self):
        """
        A diferencia del grafico anterior (que solo contaba
        TODAS las visitas sin distinguir su estado, lo cual
        confundia), este muestra por separado, mes a mes:
        cuantas visitas se PROGRAMARON vs cuantas se
        COMPLETARON de verdad -- asi se ve claramente la
        diferencia entre lo planeado y lo realmente entregado.
        """
        from database.database import consultar_todos

        filas = consultar_todos(
            """
            SELECT
                strftime('%Y-%m', fecha) AS periodo,
                COUNT(*) AS programadas,
                SUM(CASE WHEN estado='Completada' THEN 1 ELSE 0 END) AS completadas,
                SUM(CASE WHEN estado='Cancelada' THEN 1 ELSE 0 END) AS canceladas
            FROM programaciones
            WHERE eliminado = 0
            GROUP BY periodo
            ORDER BY periodo ASC
            LIMIT 12
            """
        )
        filas = [dict(f) for f in filas]
        return {
            "labels": [f["periodo"] for f in filas],
            "programadas": [f["programadas"] for f in filas],
            "completadas": [f["completadas"] for f in filas],
            "canceladas": [f["canceladas"] for f in filas],
        }

    def grafico_cumplimiento_historico(self, meses=6):
        """
        Tendencia del % de cumplimiento (visitas completadas /
        visitas programadas) mes a mes, para ver si la
        operación está mejorando o empeorando en el tiempo, no
        solo el dato de este mes.
        """
        from database.database import consultar_todos

        filas = consultar_todos(
            """
            SELECT
                strftime('%Y-%m', fecha) AS periodo,
                COUNT(*) AS total,
                SUM(CASE WHEN estado='Completada' THEN 1 ELSE 0 END) AS completadas
            FROM programaciones
            WHERE eliminado = 0 AND fecha >= date('now', ?)
            GROUP BY periodo
            ORDER BY periodo ASC
            """,
            (f"-{meses} months",),
        )
        filas = [dict(f) for f in filas]
        return {
            "labels": [f["periodo"] for f in filas],
            "porcentajes": [round((f["completadas"] / f["total"]) * 100, 1) if f["total"] else 0 for f in filas],
        }

    def grafico_altas_bajas(self, meses=6):
        """
        Cuántos pacientes y cuánto personal (profesionales y
        cuidadores) se activaron vs se inactivaron cada mes --
        para tener una idea de la rotación real del negocio.

        IMPORTANTE: esto solo es preciso desde que se empezó a
        registrar la fecha de cambio de estado (columna
        fecha_cambio_estado) -- los cambios de estado que
        pasaron ANTES de esa actualización no quedan reflejados
        aquí, porque no había forma de saber cuándo pasaron.
        """
        from database.database import consultar_todos

        pacientes_altas = consultar_todos(
            """
            SELECT strftime('%Y-%m', fecha_registro) AS periodo, COUNT(*) AS total
            FROM pacientes WHERE fecha_registro >= date('now', ?)
            GROUP BY periodo ORDER BY periodo ASC
            """,
            (f"-{meses} months",),
        )
        pacientes_bajas = consultar_todos(
            """
            SELECT strftime('%Y-%m', fecha_cambio_estado) AS periodo, COUNT(*) AS total
            FROM pacientes WHERE UPPER(estado)='INACTIVO' AND fecha_cambio_estado >= date('now', ?)
            GROUP BY periodo ORDER BY periodo ASC
            """,
            (f"-{meses} months",),
        )
        personal_altas = consultar_todos(
            """
            SELECT strftime('%Y-%m', fecha_registro) AS periodo, COUNT(*) AS total
            FROM profesionales WHERE fecha_registro >= date('now', ?)
            GROUP BY periodo ORDER BY periodo ASC
            """,
            (f"-{meses} months",),
        )
        personal_bajas = consultar_todos(
            """
            SELECT strftime('%Y-%m', fecha_cambio_estado) AS periodo, COUNT(*) AS total
            FROM profesionales WHERE UPPER(estado)='INACTIVO' AND fecha_cambio_estado >= date('now', ?)
            GROUP BY periodo ORDER BY periodo ASC
            """,
            (f"-{meses} months",),
        )

        def _a_diccionario(filas):
            return {dict(f)["periodo"]: dict(f)["total"] for f in filas if dict(f)["periodo"]}

        pa, pb = _a_diccionario(pacientes_altas), _a_diccionario(pacientes_bajas)
        na, nb = _a_diccionario(personal_altas), _a_diccionario(personal_bajas)

        # Se arma la lista de los ultimos N meses en orden, aunque algun mes no tenga ningun movimiento
        # (sin depender de dateutil, para no agregar una dependencia nueva al proyecto)
        from datetime import date
        hoy = date.today()
        periodos = []
        anio, mes = hoy.year, hoy.month
        for _ in range(meses):
            periodos.append(f"{anio:04d}-{mes:02d}")
            mes -= 1
            if mes == 0:
                mes = 12
                anio -= 1
        periodos.reverse()

        return {
            "labels": periodos,
            "pacientes_altas": [pa.get(p, 0) for p in periodos],
            "pacientes_bajas": [pb.get(p, 0) for p in periodos],
            "personal_altas": [na.get(p, 0) for p in periodos],
            "personal_bajas": [nb.get(p, 0) for p in periodos],
        }

    def dashboard_context(self):

        return {

            "dashboard":

                self.dashboard(),

            "resumen":

                self.resumen_ejecutivo(),

        }