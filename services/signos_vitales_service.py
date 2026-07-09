from datetime import datetime

from services.alertas_clinicas import generar_alertas

from repositories.signos_vitales_repository import (
    listar_por_paciente,
    obtener,
    obtener_ultimo,
    crear,
    actualizar,
    eliminar,
    listar_por_rango
)


# =====================================================
# LISTAR
# =====================================================

def listar_signos_vitales(paciente_id):

    return listar_por_paciente(paciente_id)


# =====================================================
# OBTENER
# =====================================================

def obtener_signo_vital(id):

    return obtener(id)


# =====================================================
# ÚLTIMO REGISTRO
# =====================================================

def obtener_ultimo_signo(paciente_id):

    return obtener_ultimo(paciente_id)


# =====================================================
# CALCULAR IMC
# =====================================================

def calcular_imc(peso, talla):

    if not talla or talla <= 0:
        return 0

    return round(peso / (talla * talla), 2)


# =====================================================
# VALIDAR DATOS
# =====================================================

def validar_signos(

    temperatura,
    sistolica,
    diastolica,
    frecuencia_cardiaca,
    frecuencia_respiratoria,
    saturacion,
    glucemia,
    peso,
    talla,
    dolor

):

    errores = []

    if temperatura < 30 or temperatura > 45:
        errores.append("Temperatura fuera del rango permitido.")

    if sistolica < 40 or sistolica > 300:
        errores.append("Presión sistólica inválida.")

    if diastolica < 20 or diastolica > 200:
        errores.append("Presión diastólica inválida.")

    if frecuencia_cardiaca < 20 or frecuencia_cardiaca > 250:
        errores.append("Frecuencia cardíaca inválida.")

    if frecuencia_respiratoria < 5 or frecuencia_respiratoria > 80:
        errores.append("Frecuencia respiratoria inválida.")

    if saturacion < 40 or saturacion > 100:
        errores.append("Saturación de oxígeno inválida.")

    if glucemia < 0 or glucemia > 1000:
        errores.append("Glucemia inválida.")

    if peso < 0 or peso > 500:
        errores.append("Peso inválido.")

    if talla < 0.30 or talla > 3:
        errores.append("Talla inválida.")

    if dolor < 0 or dolor > 10:
        errores.append("La escala del dolor debe estar entre 0 y 10.")

    return errores


# =====================================================
# CREAR
# =====================================================

def crear_signos_vitales(

    paciente_id,
    profesional,
    fecha,
    hora,
    temperatura,
    presion_sistolica,
    presion_diastolica,
    frecuencia_cardiaca,
    frecuencia_respiratoria,
    saturacion_oxigeno,
    glucemia,
    peso,
    talla,
    dolor,
    observaciones,
    usuario

):

    errores = validar_signos(

        temperatura,
        presion_sistolica,
        presion_diastolica,
        frecuencia_cardiaca,
        frecuencia_respiratoria,
        saturacion_oxigeno,
        glucemia,
        peso,
        talla,
        dolor

    )

    if errores:

        raise Exception("\n".join(errores))

    imc = calcular_imc(peso, talla)

    alertas = generar_alertas(

        temperatura,
        presion_sistolica,
        presion_diastolica,
        frecuencia_cardiaca,
        frecuencia_respiratoria,
        saturacion_oxigeno,
        glucemia,
        imc,
        dolor

    )

    nuevo_id = crear(

        paciente_id,
        profesional,
        fecha,
        hora,
        temperatura,
        presion_sistolica,
        presion_diastolica,
        frecuencia_cardiaca,
        frecuencia_respiratoria,
        saturacion_oxigeno,
        glucemia,
        peso,
        talla,
        imc,
        dolor,
        observaciones,
        usuario,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    )

    return {

        "id": nuevo_id,

        "imc": imc,

        "alertas": alertas

    }


# =====================================================
# ACTUALIZAR
# =====================================================

def actualizar_signos_vitales(

    id,
    profesional,
    fecha,
    hora,
    temperatura,
    presion_sistolica,
    presion_diastolica,
    frecuencia_cardiaca,
    frecuencia_respiratoria,
    saturacion_oxigeno,
    glucemia,
    peso,
    talla,
    dolor,
    observaciones

):

    errores = validar_signos(

        temperatura,
        presion_sistolica,
        presion_diastolica,
        frecuencia_cardiaca,
        frecuencia_respiratoria,
        saturacion_oxigeno,
        glucemia,
        peso,
        talla,
        dolor

    )

    if errores:

        raise Exception("\n".join(errores))

    imc = calcular_imc(peso, talla)

    alertas = generar_alertas(

        temperatura,
        presion_sistolica,
        presion_diastolica,
        frecuencia_cardiaca,
        frecuencia_respiratoria,
        saturacion_oxigeno,
        glucemia,
        imc,
        dolor

    )

    actualizar(

        id,
        profesional,
        fecha,
        hora,
        temperatura,
        presion_sistolica,
        presion_diastolica,
        frecuencia_cardiaca,
        frecuencia_respiratoria,
        saturacion_oxigeno,
        glucemia,
        peso,
        talla,
        imc,
        dolor,
        observaciones,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    )

    return {

        "id": id,

        "imc": imc,

        "alertas": alertas

    }


# =====================================================
# ELIMINAR
# =====================================================

def eliminar_signo_vital(id):

    eliminar(id)


# =====================================================
# HISTÓRICO
# =====================================================

def obtener_historico(

    paciente_id,
    fecha_inicio,
    fecha_fin

):

    return listar_por_rango(

        paciente_id,
        fecha_inicio,
        fecha_fin

    )