"""
=========================================================
HomeCare Enterprise
Servicio de Nomina

La nomina se liquida sobre el TIEMPO REALMENTE TRABAJADO:
cada visita solo cuenta si el profesional (medico, enfermero,
cuidador, terapeuta, etc.) registro su ingreso y su salida
en el domicilio del paciente (ver
services/programacion_service.registrar_ingreso/registrar_salida).

Dos modalidades de pago, segun el profesional:
- POR_HORAS: horas_trabajadas * valor_hora.
- FIJO: salario mensual fijo, prorrateado segun los dias del
  periodo liquidado respecto a un mes de 30 dias (el
  profesional de todas formas debe tener marcaciones en el
  periodo para aparecer en la nomina).
=========================================================
"""

from datetime import datetime

from datetime import datetime

from core.nomina.calculo_horas import clasificar_turno, valor_turno
from core.nomina.parametros_legales import (
    APORTE_PENSION_EMPLEADOR,
    APORTE_SALUD_EMPLEADOR,
    ARL_POR_NIVEL_RIESGO,
    AUXILIO_TRANSPORTE_2026,
    CESANTIAS,
    INTERESES_CESANTIAS,
    PRIMA_SERVICIOS,
    TOPE_AUXILIO_TRANSPORTE,
    VACACIONES,
)
from repositories.nomina_repository import NominaRepository


def _prestaciones_y_aportes(devengado: float, auxilio_transporte: float, nivel_riesgo_arl: str) -> dict:
    """
    Solo aplica a quien tiene VINCULACIÓN LABORAL (contrato de
    trabajo). Un contratista de Prestación de Servicios NO
    tiene derecho a estas prestaciones -- por eso esta función
    solo se llama para ese caso.

    Las prestaciones sociales (cesantías, intereses, prima,
    vacaciones) se calculan sobre el salario + auxilio de
    transporte (este último NO es salarial, pero SÍ es base
    para cesantías y su interés, por disposición legal). Los
    aportes patronales (salud, pensión, ARL) se calculan sobre
    el salario base (sin auxilio de transporte, que no es IBC).
    """

    base_prestaciones = devengado + auxilio_transporte

    cesantias = round(base_prestaciones * CESANTIAS, 2)
    intereses_cesantias = round(cesantias * INTERESES_CESANTIAS, 2)
    prima_servicios = round(base_prestaciones * PRIMA_SERVICIOS, 2)
    vacaciones = round(devengado * VACACIONES, 2)  # las vacaciones SÍ son solo sobre salario, sin auxilio

    aporte_salud_empleador = round(devengado * APORTE_SALUD_EMPLEADOR, 2)
    aporte_pension_empleador = round(devengado * APORTE_PENSION_EMPLEADOR, 2)
    tarifa_arl = ARL_POR_NIVEL_RIESGO.get(nivel_riesgo_arl, ARL_POR_NIVEL_RIESGO["I"])
    aporte_arl = round(devengado * tarifa_arl, 2)

    total_prestaciones = cesantias + intereses_cesantias + prima_servicios + vacaciones
    total_aportes_patronales = aporte_salud_empleador + aporte_pension_empleador + aporte_arl

    return {
        "cesantias": cesantias,
        "intereses_cesantias": intereses_cesantias,
        "prima_servicios": prima_servicios,
        "vacaciones": vacaciones,
        "total_prestaciones": round(total_prestaciones, 2),
        "aporte_salud_empleador": aporte_salud_empleador,
        "aporte_pension_empleador": aporte_pension_empleador,
        "aporte_arl": aporte_arl,
        "total_aportes_patronales": round(total_aportes_patronales, 2),
        "costo_total_empresa": round(devengado + auxilio_transporte + total_prestaciones + total_aportes_patronales, 2),
    }


def _dias_periodo(fecha_inicio: str, fecha_fin: str) -> int:
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    return max((fin - inicio).days + 1, 1)


def _liquidar_por_horas(profesional_id: int, fecha_inicio: str, fecha_fin: str, valor_hora: float) -> dict:
    """
    Recorre cada visita del periodo y aplica los recargos
    legales (nocturno, dominical/festivo, horas extra) segun
    el horario REAL trabajado, en vez de multiplicar
    simplemente horas totales x valor hora.
    """

    visitas = NominaRepository.visitas_a_liquidar(profesional_id, fecha_inicio, fecha_fin)

    acumulado = {
        "horas_diurnas": 0, "horas_nocturnas": 0,
        "horas_dominicales_diurnas": 0, "horas_dominicales_nocturnas": 0,
        "horas_extra_diurnas": 0, "horas_extra_nocturnas": 0,
        "total_horas": 0,
    }

    valor_total = 0

    for v in visitas:
        v = dict(v)

        if not v.get("hora_real_inicio") or not v.get("hora_real_fin"):
            continue

        clasificacion = clasificar_turno(v["hora_real_inicio"], v["hora_real_fin"])
        valores = valor_turno(clasificacion, valor_hora, v["fecha"])

        for clave in acumulado:
            acumulado[clave] += clasificacion.get(clave, 0)

        valor_total += valores["total"]

    return {
        "detalle_horas": acumulado,
        "valor_a_pagar": round(valor_total, 2),
    }


def previsualizar_periodo(fecha_inicio: str, fecha_fin: str) -> dict:
    """
    Calcula, SIN guardar nada todavia, cuanto habria que
    pagarle a cada profesional segun el tiempo que
    efectivamente trabajo en el periodo. Esto es lo que se
    muestra cuando "se consulta el sistema para hacer los
    pagos": tiempo a liquidar + valor por persona.
    """

    filas = NominaRepository.horas_por_profesional(fecha_inicio, fecha_fin)
    dias = _dias_periodo(fecha_inicio, fecha_fin)

    detalle = []
    total_pagar = 0

    for f in filas:
        f = dict(f)

        tipo_contrato = f.get("tipo_contrato") or "POR_HORAS"
        tipo_vinculacion = f.get("tipo_vinculacion") or "Prestación de Servicios"
        nivel_riesgo_arl = f.get("nivel_riesgo_arl") or "I"
        horas = round(f.get("horas_trabajadas") or 0, 2)

        if tipo_contrato == "FIJO":
            salario_fijo = f.get("salario_fijo") or 0
            salario_prorrateado = round(salario_fijo * (dias / 30), 2)

            auxilio_transporte = 0
            if 0 < salario_fijo <= TOPE_AUXILIO_TRANSPORTE:
                auxilio_transporte = round(AUXILIO_TRANSPORTE_2026 * (dias / 30), 2)

            valor_a_pagar = round(salario_prorrateado + auxilio_transporte, 2)
            valor_hora = 0
            desglose_horas = None
        else:
            valor_hora = f.get("valor_hora") or 0
            salario_fijo = 0
            auxilio_transporte = 0

            liquidacion = _liquidar_por_horas(
                f["profesional_id"], fecha_inicio, fecha_fin, valor_hora
            )
            valor_a_pagar = liquidacion["valor_a_pagar"]
            desglose_horas = liquidacion["detalle_horas"]

        # Prestaciones sociales y aportes patronales: SOLO si
        # la persona tiene vinculación LABORAL (no aplica a
        # contratistas de Prestación de Servicios).
        prestaciones = None
        if tipo_vinculacion == "Laboral":
            prestaciones = _prestaciones_y_aportes(valor_a_pagar, auxilio_transporte, nivel_riesgo_arl)

        total_pagar += valor_a_pagar

        detalle.append({
            "profesional_id": f["profesional_id"],
            "nombre_completo": f["nombre_completo"],
            "documento": f["documento"],
            "especialidad_principal": f.get("especialidad_principal"),
            "tipo_contrato": tipo_contrato,
            "tipo_vinculacion": tipo_vinculacion,
            "numero_visitas": f["numero_visitas"],
            "horas_trabajadas": horas,
            "desglose_horas": desglose_horas,
            "valor_hora": valor_hora,
            "salario_fijo": salario_fijo,
            "auxilio_transporte": auxilio_transporte,
            "valor_a_pagar": valor_a_pagar,
            "prestaciones": prestaciones,
        })

    total_prestaciones_periodo = sum(d["prestaciones"]["total_prestaciones"] for d in detalle if d["prestaciones"])
    total_aportes_periodo = sum(d["prestaciones"]["total_aportes_patronales"] for d in detalle if d["prestaciones"])

    return {
        "periodo_inicio": fecha_inicio,
        "periodo_fin": fecha_fin,
        "dias_periodo": dias,
        "detalle": detalle,
        "total_pagar": round(total_pagar, 2),
        "total_prestaciones_periodo": round(total_prestaciones_periodo, 2),
        "total_aportes_periodo": round(total_aportes_periodo, 2),
        "costo_total_empresa_periodo": round(total_pagar + total_prestaciones_periodo + total_aportes_periodo, 2),
        "total_profesionales": len(detalle),
    }


def generar_nomina(fecha_inicio: str, fecha_fin: str, usuario_generacion=None) -> int:
    """
    Calcula la previsualizacion y la deja guardada como una
    nomina formal (cabecera + detalle), marcando las visitas
    incluidas como liquidadas para que no se paguen dos veces.
    """

    previsualizacion = previsualizar_periodo(fecha_inicio, fecha_fin)

    if not previsualizacion["detalle"]:
        raise ValueError(
            "No hay tiempos registrados (ingreso y salida) en este periodo "
            "para ningún profesional."
        )

    nomina_id = NominaRepository.crear_nomina(
        fecha_inicio, fecha_fin, usuario_generacion, previsualizacion["total_pagar"]
    )

    for item in previsualizacion["detalle"]:
        NominaRepository.agregar_detalle(nomina_id, item)

        NominaRepository.marcar_visitas_liquidadas(
            item["profesional_id"], fecha_inicio, fecha_fin, nomina_id
        )

    return nomina_id


def listar_nominas():
    return NominaRepository.listar_nominas()


def obtener_nomina_completa(nomina_id: int) -> dict:
    nomina = NominaRepository.obtener_nomina(nomina_id)

    if not nomina:
        raise ValueError("La nómina no existe.")

    return {
        "nomina": dict(nomina),
        "detalle": [dict(d) for d in NominaRepository.detalle_nomina(nomina_id)],
    }


def marcar_pagado(detalle_id: int):
    from datetime import date
    NominaRepository.marcar_pagado(detalle_id, date.today().isoformat())
