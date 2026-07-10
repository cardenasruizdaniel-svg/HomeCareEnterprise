"""
=========================================================
HomeCare Enterprise
Servicio de la App Movil (PWA offline-first)

Expone, en un formato compacto para sincronizar, todo lo
que un cuidador/enfermero/terapeuta/aplicador de
medicamentos necesita: su agenda, los datos del paciente y
su historia clinica resumida, y procesa las acciones que la
app registro mientras estaba SIN internet (ingreso/salida,
signos vitales, medicamento administrado, evolucion,
ordenes medicas).
=========================================================
"""

from datetime import datetime

from database.database import consultar, consultar_uno, ejecutar

from services import programacion_service
from services.alertas_service import obtener_resumen_seguridad


# ==========================================================
# AGENDA DEL PROFESIONAL (para el calendario de la app)
# ==========================================================

def agenda_profesional(profesional_id: int, fecha_inicio: str, fecha_fin: str):
    filas = consultar(
        """
        SELECT
            pr.id, pr.fecha, pr.hora_inicio, pr.hora_fin, pr.servicio,
            pr.procedimiento, pr.estado, pr.direccion, pr.barrio, pr.municipio,
            pr.hora_real_inicio, pr.hora_real_fin,
            p.id AS paciente_id, p.documento, p.primer_nombre, p.segundo_nombre,
            p.primer_apellido, p.segundo_apellido, p.celular, p.telefono,
            p.direccion AS direccion_paciente, p.latitud AS lat_paciente, p.longitud AS lon_paciente,
            p.radio_geocerca_metros,
            p.ubicacion_confirmada,
            pv.id AS planilla_id, pv.estado AS planilla_estado
        FROM programaciones pr
        JOIN pacientes p ON p.id = pr.paciente_id
        LEFT JOIN planilla_visitas pv ON pv.programacion_id = pr.id
        WHERE pr.profesional_id=? AND pr.fecha BETWEEN ? AND ? AND pr.eliminado=0
        ORDER BY pr.fecha, pr.hora_inicio
        """,
        (profesional_id, fecha_inicio, fecha_fin),
    )

    return [dict(f) for f in filas]


# ==========================================================
# FICHA DEL PACIENTE (para consulta offline)
# ==========================================================

def ficha_paciente_offline(paciente_id: int) -> dict:
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))

    if not paciente:
        return {}

    paciente = dict(paciente)

    diagnosticos = [dict(d) for d in consultar(
        "SELECT codigo_cie10, diagnostico, fecha_diagnostico FROM diagnosticos "
        "WHERE paciente_id=? AND estado='Activo' ORDER BY fecha_diagnostico DESC",
        (paciente_id,),
    )]

    resumen_seguridad = obtener_resumen_seguridad(paciente_id)

    ordenes = [dict(o) for o in consultar(
        "SELECT tipo, descripcion, fecha_orden FROM ordenes_medicas "
        "WHERE paciente_id=? ORDER BY fecha_orden DESC LIMIT 10",
        (paciente_id,),
    )]

    return {
        "paciente": paciente,
        "diagnosticos": diagnosticos,
        "alergias": resumen_seguridad["alergias"],
        "medicamentos_activos": resumen_seguridad["medicamentos"],
        "ordenes_recientes": ordenes,
    }


# ==========================================================
# ACCIONES QUE LA APP ENVÍA AL SINCRONIZAR
# ==========================================================

def registrar_ingreso(visita_id: int, latitud=None, longitud=None, marca_tiempo_offline=None, foto_base64=None):
    verificacion = programacion_service.registrar_ingreso(visita_id, latitud, longitud, foto_base64)
    return {"ok": True, "geocerca": verificacion}


def registrar_salida(visita_id: int, latitud=None, longitud=None, marca_tiempo_offline=None, foto_base64=None):
    verificacion = programacion_service.registrar_salida(visita_id, latitud, longitud, foto_base64)
    return {"ok": True, "geocerca": verificacion}


def firmar_planilla(planilla_id: int, firmante: str, nombre_acompanante: str,
                      firma_base64: str, foto_base64: str = None,
                      latitud=None, longitud=None, marca_tiempo_offline=None):
    from services.planilla_visitas_service import firmar_visita
    return firmar_visita(
        planilla_id, firmante, nombre_acompanante, firma_base64, foto_base64,
        latitud, longitud, marca_tiempo_offline,
    )


def actualizar_ubicacion_paciente(paciente_id: int, latitud=None, longitud=None, rol_usuario=None):
    """
    Solo el médico que hace la PRIMERA visita (valoración
    inicial) registra la ubicación exacta del paciente. Una
    vez quedó confirmada, la app ya NO permite volver a
    cambiarla -- si hace falta corregirla despues, debe
    hacerse desde la oficina (rol Administrativo/Administrador),
    para evitar que la geocerca de un paciente se mueva por
    error durante visitas posteriores.
    """

    if latitud is None or longitud is None:
        raise ValueError("No se recibió la ubicación del dispositivo.")

    from database.database import consultar_uno, get_connection

    paciente = consultar_uno("SELECT ubicacion_confirmada FROM pacientes WHERE id=?", (paciente_id,))
    ya_confirmada = bool(dict(paciente)["ubicacion_confirmada"]) if paciente else False

    rol_normalizado = (rol_usuario or "").strip().lower()
    es_administrativo = rol_normalizado in ("administrativo", "administrador", "coordinador")

    if ya_confirmada and not es_administrativo:
        raise ValueError(
            "La ubicación de este paciente ya fue registrada en la visita de valoración inicial "
            "y no se puede modificar desde la app. Si es necesario corregirla, debe hacerse desde la oficina."
        )

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE pacientes SET latitud=?, longitud=?, ubicacion_confirmada=1 WHERE id=?",
        (latitud, longitud, paciente_id),
    )
    conexion.commit()
    conexion.close()

    return {"ok": True}


def registrar_signos_vitales(paciente_id, profesional, datos: dict, usuario_id=None) -> dict:
    ejecutar(
        """
        INSERT INTO signos_vitales(
            paciente_id, profesional, fecha, hora, temperatura, presion_sistolica,
            presion_diastolica, frecuencia_cardiaca, frecuencia_respiratoria,
            saturacion_oxigeno, glucemia, peso, talla, imc, dolor, observaciones,
            usuario_creacion
        ) VALUES (
            :paciente_id, :profesional, :fecha, :hora, :temperatura, :presion_sistolica,
            :presion_diastolica, :frecuencia_cardiaca, :frecuencia_respiratoria,
            :saturacion_oxigeno, :glucemia, :peso, :talla, :imc, :dolor, :observaciones,
            :usuario_creacion
        )
        """,
        {
            "paciente_id": paciente_id,
            "profesional": profesional,
            "fecha": datos.get("fecha") or datetime.now().strftime("%Y-%m-%d"),
            "hora": datos.get("hora") or datetime.now().strftime("%H:%M:%S"),
            "temperatura": datos.get("temperatura"),
            "presion_sistolica": datos.get("presion_sistolica"),
            "presion_diastolica": datos.get("presion_diastolica"),
            "frecuencia_cardiaca": datos.get("frecuencia_cardiaca"),
            "frecuencia_respiratoria": datos.get("frecuencia_respiratoria"),
            "saturacion_oxigeno": datos.get("saturacion_oxigeno"),
            "glucemia": datos.get("glucemia"),
            "peso": datos.get("peso"),
            "talla": datos.get("talla"),
            "imc": datos.get("imc"),
            "dolor": datos.get("dolor"),
            "observaciones": datos.get("observaciones", ""),
            "usuario_creacion": usuario_id,
        },
    )
    return {"ok": True}


def registrar_medicamento_administrado(medicamento_id, paciente_id, profesional, dosis, via, observaciones, estado="Administrado") -> dict:
    ejecutar(
        """
        INSERT INTO administracion_medicamentos(
            medicamento_id, paciente_id, profesional, fecha, hora, dosis, via,
            observaciones, estado
        ) VALUES (
            :medicamento_id, :paciente_id, :profesional, :fecha, :hora, :dosis, :via,
            :observaciones, :estado
        )
        """,
        {
            "medicamento_id": medicamento_id,
            "paciente_id": paciente_id,
            "profesional": profesional,
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M:%S"),
            "dosis": dosis,
            "via": via,
            "observaciones": observaciones or "",
            "estado": estado,
        },
    )
    return {"ok": True}


def registrar_resultado_laboratorio(paciente_id, nombre_examen, laboratorio_realizo, fecha_resultado,
                                       resultado_texto, foto_resultado_base64, profesional_id, usuario_id,
                                       items=None):
    """
    Permite que el médico o profesional de la salud registre,
    desde la app de campo durante la visita, el resultado de
    un examen de laboratorio que le mandaron al paciente --
    con sus parámetros medibles (ej. Glóbulos rojos, valor y
    rango normal) y foto del resultado como constancia. Queda
    reflejado en la Historia Clínica igual que si se hubiera
    diligenciado desde la oficina.
    """

    from services.laboratorios_service import registrar_resultado

    if not nombre_examen:
        raise ValueError("Debe indicar el nombre del examen.")

    resultado_id = registrar_resultado(
        paciente_id, nombre_examen, laboratorio_realizo, None, fecha_resultado,
        resultado_texto, foto_resultado_base64, profesional_id, "MOVIL", usuario_id,
        items=items or [],
    )

    return {"ok": True, "id": resultado_id}


def listar_laboratorios_paciente(paciente_id: int):
    from services.laboratorios_service import listar_por_paciente
    return listar_por_paciente(paciente_id)


def crear_orden_medica(paciente_id, profesional_id, tipo, descripcion, codigo_cups, usuario_id):
    """
    Permite que el médico o profesional de la salud genere una
    orden médica (medicamento, examen, remisión, procedimiento)
    desde la app de campo durante la visita. Usa el mismo motor
    que la web: genera el PDF y lo envía automáticamente al
    paciente por WhatsApp/correo.
    """

    from services.ordenes_service import OrdenesService

    return OrdenesService.crear_y_enviar(
        paciente_id, profesional_id, tipo, descripcion, codigo_cups or "",
        usuario_creacion=usuario_id,
    )


def registrar_evolucion(paciente_id, programacion_id, profesional_id, tipo_profesional, nota,
                          latitud=None, longitud=None, usuario_id=None,
                          tipo_registro="INFORME", nota_aclaratoria_de=None) -> dict:

    from services.evoluciones_service import registrar_evolucion as _registrar

    return _registrar(
        paciente_id, programacion_id, profesional_id, tipo_profesional, nota,
        origen="APP_MOVIL", latitud=latitud, longitud=longitud, usuario_id=usuario_id,
        tipo_registro=tipo_registro, nota_aclaratoria_de=nota_aclaratoria_de,
    )
