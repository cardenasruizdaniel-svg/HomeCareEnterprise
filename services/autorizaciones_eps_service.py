"""
HomeCare Enterprise - Autorizaciones de Servicios Adicionales (EPS)

Cuando el médico ordena más sesiones de un servicio de las que
el programa contratado con la EPS tiene incluidas, ese
excedente NO se puede programar, agendar ni asignar de una vez
-- queda registrado como una SOLICITUD pendiente de
autorización.

Flujo:
    1. Se detecta el excedente (desde servicios_paciente_service,
       al momento de asignar) y se crea automáticamente la
       solicitud, con estado "Pendiente autorización EPS".
    2. Un usuario autorizado revisa la solicitud y, cuando la
       EPS responde, la marca como Autorizada (con número, fecha,
       cantidad y valor autorizado) o Rechazada.
    3. Solo cuando queda Autorizada, esas sesiones adicionales
       quedan disponibles para programarse -- hasta la cantidad
       que efectivamente haya autorizado la EPS (que puede ser
       menor a la solicitada).
"""

from database.database import consultar_todos, consultar_uno, ejecutar

ESTADOS_SOLICITUD = ("Pendiente autorización EPS", "Autorizada", "Rechazada")


def crear_solicitud_autorizacion(paciente_id, programa_convenio_id, tipo_servicio, grupo_tope,
                                    cantidad_solicitada, usuario_id=None) -> int:
    return ejecutar(
        """
        INSERT INTO autorizaciones_eps_servicios_adicionales(
            paciente_id, programa_convenio_id, tipo_servicio, grupo_tope, cantidad_solicitada, usuario_solicitud
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (paciente_id, programa_convenio_id, tipo_servicio, grupo_tope, int(cantidad_solicitada), usuario_id),
    )


def listar_solicitudes(estado=None, paciente_id=None):
    sql = """
        SELECT a.*, p.primer_nombre, p.primer_apellido, p.documento, p.tipo_documento,
               prog.nombre AS nombre_programa, ce.eps
        FROM autorizaciones_eps_servicios_adicionales a
        JOIN pacientes p ON p.id = a.paciente_id
        JOIN programas_convenio prog ON prog.id = a.programa_convenio_id
        JOIN convenios_eps ce ON ce.id = prog.convenio_id
        WHERE 1=1
    """
    parametros = []
    if estado:
        sql += " AND a.estado = ?"
        parametros.append(estado)
    if paciente_id:
        sql += " AND a.paciente_id = ?"
        parametros.append(paciente_id)
    sql += " ORDER BY a.fecha_solicitud DESC"

    filas = consultar_todos(sql, tuple(parametros))
    return [dict(f) for f in filas]


def obtener_solicitud(solicitud_id: int):
    fila = consultar_uno(
        """
        SELECT a.*, p.primer_nombre, p.primer_apellido, p.documento, p.tipo_documento,
               prog.nombre AS nombre_programa, ce.eps
        FROM autorizaciones_eps_servicios_adicionales a
        JOIN pacientes p ON p.id = a.paciente_id
        JOIN programas_convenio prog ON prog.id = a.programa_convenio_id
        JOIN convenios_eps ce ON ce.id = prog.convenio_id
        WHERE a.id=?
        """,
        (solicitud_id,),
    )
    return dict(fila) if fila else None


def autorizar_solicitud(solicitud_id, numero_autorizacion, fecha_autorizacion, cantidad_autorizada,
                          valor_autorizado, documento_soporte, observaciones, usuario_id) -> None:
    if not numero_autorizacion:
        raise ValueError("Debe indicar el número de autorización de la EPS.")
    if not cantidad_autorizada or int(cantidad_autorizada) <= 0:
        raise ValueError("La cantidad autorizada debe ser mayor a cero.")

    ejecutar(
        """
        UPDATE autorizaciones_eps_servicios_adicionales
        SET estado='Autorizada', numero_autorizacion=?, fecha_autorizacion=?, cantidad_autorizada=?,
            valor_autorizado=?, documento_soporte=?, observaciones=?, usuario_autorizacion=?
        WHERE id=?
        """,
        (numero_autorizacion, fecha_autorizacion or None, int(cantidad_autorizada), float(valor_autorizado or 0),
         documento_soporte or None, observaciones or "", usuario_id, solicitud_id),
    )


def rechazar_solicitud(solicitud_id, observaciones, usuario_id) -> None:
    ejecutar(
        "UPDATE autorizaciones_eps_servicios_adicionales SET estado='Rechazada', observaciones=?, usuario_autorizacion=? WHERE id=?",
        (observaciones or "", usuario_id, solicitud_id),
    )


def cantidad_autorizada_disponible(paciente_id: int, tipo_servicio: str, grupo_tope=None) -> int:
    """
    Cuánto de lo YA AUTORIZADO por la EPS para este servicio (o
    grupo) todavía no se ha usado -- esto es lo que se le suma
    al tope normal del programa para saber cuánto se puede
    programar en total.
    """
    if grupo_tope:
        filas = consultar_todos(
            "SELECT * FROM autorizaciones_eps_servicios_adicionales WHERE paciente_id=? AND grupo_tope=? AND estado='Autorizada'",
            (paciente_id, grupo_tope),
        )
    else:
        filas = consultar_todos(
            "SELECT * FROM autorizaciones_eps_servicios_adicionales WHERE paciente_id=? AND tipo_servicio=? AND (grupo_tope IS NULL OR grupo_tope='') AND estado='Autorizada'",
            (paciente_id, tipo_servicio),
        )

    total_disponible = 0
    for fila in filas:
        f = dict(fila)
        total_disponible += max(0, (f["cantidad_autorizada"] or 0) - (f["cantidad_consumida"] or 0))
    return total_disponible


def consumir_autorizacion(paciente_id: int, tipo_servicio: str, cantidad: int, grupo_tope=None) -> int:
    """
    Descuenta 'cantidad' de las autorizaciones ya aprobadas para
    este paciente/servicio, empezando por la más antigua -- para
    llevar la cuenta de cuánto de lo autorizado ya se ha
    programado. Devuelve cuánto realmente se pudo descontar
    (puede ser menor a 'cantidad' si no había suficiente
    autorizado).
    """
    if grupo_tope:
        filas = consultar_todos(
            "SELECT * FROM autorizaciones_eps_servicios_adicionales WHERE paciente_id=? AND grupo_tope=? AND estado='Autorizada' ORDER BY fecha_autorizacion",
            (paciente_id, grupo_tope),
        )
    else:
        filas = consultar_todos(
            "SELECT * FROM autorizaciones_eps_servicios_adicionales WHERE paciente_id=? AND tipo_servicio=? AND (grupo_tope IS NULL OR grupo_tope='') AND estado='Autorizada' ORDER BY fecha_autorizacion",
            (paciente_id, tipo_servicio),
        )

    restante = cantidad
    total_consumido = 0
    for fila in filas:
        if restante <= 0:
            break
        f = dict(fila)
        disponible_en_esta = max(0, (f["cantidad_autorizada"] or 0) - (f["cantidad_consumida"] or 0))
        a_consumir = min(disponible_en_esta, restante)
        if a_consumir > 0:
            ejecutar(
                "UPDATE autorizaciones_eps_servicios_adicionales SET cantidad_consumida = cantidad_consumida + ? WHERE id=?",
                (a_consumir, f["id"]),
            )
            restante -= a_consumir
            total_consumido += a_consumir

    return total_consumido


def resumen_dashboard() -> dict:
    """Para los indicadores del Dashboard: cuántas solicitudes hay en cada estado."""
    filas = consultar_todos(
        "SELECT estado, COUNT(*) AS total FROM autorizaciones_eps_servicios_adicionales GROUP BY estado"
    )
    resumen = {estado: 0 for estado in ESTADOS_SOLICITUD}
    for f in filas:
        f = dict(f)
        resumen[f["estado"]] = f["total"]
    return resumen
