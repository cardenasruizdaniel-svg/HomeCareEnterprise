"""
HomeCare Enterprise - Planilla de visitas

Cada fila de la planilla corresponde a un dia de un servicio
asignado al paciente (terapia, curacion, aplicador, etc.). Al
confirmar la visita del dia, se firma digitalmente (el
paciente o su acompañante) y queda registrada la foto, la
fecha/hora y la ubicacion GPS de ese momento -- todo esto
debe poder hacerse tambien sin conexion desde la app movil,
sincronizando despues.
"""

from datetime import datetime

from database.database import consultar_uno
from repositories.planilla_visitas_repository import PlanillaVisitasRepository


def listar_por_servicio(servicio_paciente_id: int):
    return [dict(p) for p in PlanillaVisitasRepository.listar_por_servicio(servicio_paciente_id)]


def obtener(planilla_id: int):
    return PlanillaVisitasRepository.obtener(planilla_id)


def firmar_visita(planilla_id: int, firmante: str, nombre_acompanante: str,
                    firma_base64: str, foto_base64: str = None,
                    latitud: float = None, longitud: float = None,
                    fecha_hora: str = None) -> dict:
    """
    Registra la confirmacion firmada de una visita de la
    planilla. Tambien verifica, si hay coordenadas, que la
    firma se hizo en el domicilio del paciente (igual que con
    el ingreso/salida de la visita).
    """

    if not firma_base64:
        raise ValueError("Se requiere la firma digital para confirmar la visita.")

    if firmante not in ("Paciente", "Acompañante"):
        raise ValueError("Debe indicar quién firma: el paciente o su acompañante.")

    planilla = PlanillaVisitasRepository.obtener(planilla_id)
    if not planilla:
        raise ValueError("La fila de la planilla no existe.")

    planilla = dict(planilla)

    paciente = consultar_uno(
        "SELECT latitud, longitud, radio_geocerca_metros FROM pacientes WHERE id=?",
        (planilla["paciente_id"],),
    )
    paciente = dict(paciente) if paciente else {}

    verificacion = {"verificable": False}
    if latitud is not None and longitud is not None:
        from core.geolocalizacion import verificar_geocerca
        verificacion = verificar_geocerca(
            latitud, longitud, paciente.get("latitud"), paciente.get("longitud"),
            paciente.get("radio_geocerca_metros") or 150,
        )

    PlanillaVisitasRepository.firmar(planilla_id, {
        "nombre_acompanante": nombre_acompanante if firmante == "Acompañante" else None,
        "firmante": firmante,
        "firma_base64": firma_base64,
        "foto_base64": foto_base64,
        "firma_fecha_hora": fecha_hora or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "firma_latitud": latitud,
        "firma_longitud": longitud,
    })

    try:
        from services.servicios_paciente_service import renovar_si_corresponde
        renovar_si_corresponde(planilla["servicio_paciente_id"])
    except Exception:
        pass  # la firma de la visita no debe fallar por esto

    return {"ok": True, "geocerca": verificacion}
