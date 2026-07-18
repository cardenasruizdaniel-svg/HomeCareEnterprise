"""
HomeCare Enterprise - Historial de documentos del paciente

Maneja el cambio de tipo/numero de documento de un paciente
(por ejemplo, Registro Civil -> Tarjeta de Identidad -> Cedula
en menores de edad) dejando un historial completo y
transparente, tal como lo exige la Supersalud: los registros
de ANTES de la fecha de cambio deben poder consultarse con el
documento que era valido en ese momento, y los de DESPUES con
el documento nuevo.

Diseño:
- La tabla `pacientes` siempre guarda el documento VIGENTE
  (el que se usa para toda operacion nueva: agenda, ordenes,
  RIPS, facturacion, etc.).
- La tabla `historial_documentos_paciente` guarda cada
  documento que el paciente ha tenido, con su rango de
  vigencia (fecha_inicio_vigencia / fecha_fin_vigencia).
- Para saber que documento era valido en una fecha pasada
  (por ejemplo, al generar RIPS de un periodo anterior), se
  usa `documento_vigente_en_fecha`, en vez de leer siempre el
  documento actual del paciente.
"""

from datetime import date, timedelta

from database.database import get_connection
from repositories.historial_documentos_repository import HistorialDocumentosRepository


def inicializar_historial(paciente_id: int, tipo_documento: str, numero_documento: str,
                            fecha_inicio: str = None, usuario=None):
    """
    Se llama al crear un paciente nuevo, para dejar registrado
    su primer documento como el vigente desde el inicio.
    """

    if HistorialDocumentosRepository.obtener_principal(paciente_id):
        return  # ya tiene historial, no se duplica

    HistorialDocumentosRepository.crear({
        "paciente_id": paciente_id,
        "tipo_documento": tipo_documento,
        "numero_documento": numero_documento,
        "fecha_inicio_vigencia": fecha_inicio or date.today().isoformat(),
        "fecha_fin_vigencia": None,
        "es_principal": 1,
        "motivo_cambio": "Registro inicial",
        "usuario_creacion": usuario,
    })


def obtener_historial(paciente_id: int):
    return [dict(h) for h in HistorialDocumentosRepository.listar_por_paciente(paciente_id)]


def cambiar_documento(paciente_id: int, tipo_documento_nuevo: str, numero_documento_nuevo: str,
                        fecha_cambio: str, motivo: str, usuario=None):
    """
    Registra un cambio de documento (ej. de Registro Civil a
    Tarjeta de Identidad). A partir de fecha_cambio, el
    documento nuevo queda como el vigente/principal; el
    anterior queda cerrado en esa misma fecha, pero disponible
    en el historial para consultar registros anteriores.
    """

    if not tipo_documento_nuevo or not numero_documento_nuevo:
        raise ValueError("Debe indicar el tipo y número del nuevo documento.")

    if not fecha_cambio:
        raise ValueError("Debe indicar la fecha a partir de la cual aplica el cambio.")

    principal_actual = HistorialDocumentosRepository.obtener_principal(paciente_id)

    if principal_actual:
        principal_actual = dict(principal_actual)

        if principal_actual["numero_documento"] == numero_documento_nuevo and \
           principal_actual["tipo_documento"] == tipo_documento_nuevo:
            raise ValueError("El documento nuevo es igual al que ya está vigente.")

        if fecha_cambio <= principal_actual["fecha_inicio_vigencia"]:
            raise ValueError(
                f"La fecha del cambio ({fecha_cambio}) debe ser posterior a la fecha desde la que "
                f"el documento actual está vigente ({principal_actual['fecha_inicio_vigencia']})."
            )

        # El documento anterior queda vigente HASTA el día
        # anterior al cambio (para que ambos rangos no se
        # traslapen ni dejen huecos).
        fecha_fin_anterior = (
            date.fromisoformat(fecha_cambio) - timedelta(days=1)
        ).isoformat()

        HistorialDocumentosRepository.cerrar_vigencia(principal_actual["id"], fecha_fin_anterior)

    nuevo_id = HistorialDocumentosRepository.crear({
        "paciente_id": paciente_id,
        "tipo_documento": tipo_documento_nuevo,
        "numero_documento": numero_documento_nuevo,
        "fecha_inicio_vigencia": fecha_cambio,
        "fecha_fin_vigencia": None,
        "es_principal": 1,
        "motivo_cambio": motivo or "Cambio de documento",
        "usuario_creacion": usuario,
    })

    # Se actualiza el documento "vigente" del paciente, que es
    # el que usa el resto del sistema para operaciones nuevas.
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE pacientes SET tipo_documento=?, documento=? WHERE id=?",
        (tipo_documento_nuevo, numero_documento_nuevo, paciente_id),
    )
    conexion.commit()
    conexion.close()

    return nuevo_id


def marcar_como_principal(paciente_id: int, historial_id: int):
    """
    Permite elegir manualmente cual de los documentos del
    historial queda como el vigente/principal (por ejemplo,
    si un cambio se registró por error). Esto NO reordena las
    fechas de vigencia ya registradas, solo cambia cuál es el
    que el sistema usa de aquí en adelante.
    """

    HistorialDocumentosRepository.marcar_principal(paciente_id, historial_id)

    from database.database import consultar_uno
    doc = consultar_uno(
        "SELECT tipo_documento, numero_documento FROM historial_documentos_paciente WHERE id=?",
        (historial_id,),
    )

    if not doc:
        raise ValueError("El documento del historial no existe.")

    doc = dict(doc)

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE pacientes SET tipo_documento=?, documento=? WHERE id=?",
        (doc["tipo_documento"], doc["numero_documento"], paciente_id),
    )
    conexion.commit()
    conexion.close()


def documento_vigente_en_fecha(paciente_id: int, fecha: str) -> dict:
    """
    Devuelve el documento (tipo + numero) que era vigente para
    este paciente en una fecha determinada -- para usar en
    reportes historicos (RIPS de periodos pasados, por
    ejemplo), en vez de asumir siempre el documento actual.
    Si el paciente no tiene historial (por ejemplo, si se creó
    antes de existir esta funcionalidad), se usa su documento
    actual como respaldo.
    """

    registro = HistorialDocumentosRepository.documento_vigente_en_fecha(paciente_id, fecha)

    if registro:
        registro = dict(registro)
        return {"tipo_documento": registro["tipo_documento"], "numero_documento": registro["numero_documento"]}

    from database.database import consultar_uno
    paciente = consultar_uno("SELECT tipo_documento, documento FROM pacientes WHERE id=?", (paciente_id,))

    if not paciente:
        raise ValueError("El paciente no existe.")

    paciente = dict(paciente)
    return {"tipo_documento": paciente["tipo_documento"], "numero_documento": paciente["documento"]}
