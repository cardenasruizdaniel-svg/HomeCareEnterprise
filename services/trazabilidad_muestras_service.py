"""
HomeCare Enterprise - Trazabilidad de Toma de Muestras de Laboratorio

Cadena de custodia completa de una muestra: desde que se
recolecta en el domicilio del paciente, hasta que se entrega y
se procesa en el laboratorio. Cada cambio de estado queda
registrado con fecha, hora, y quién lo hizo -- para que nunca
quede la duda de en qué momento se pudo haber dañado, demorado,
o perdido una muestra.

Estados por los que pasa una muestra:
    Recolectada -> En tránsito -> Entregada al laboratorio -> Procesada
                                                             -> Rechazada (si el laboratorio la rechaza)
"""

from database.database import consultar_todos, consultar_uno, ejecutar

# Tipos de muestra más comunes en atención domiciliaria
TIPOS_MUESTRA = (
    "Sangre venosa", "Sangre capilar (glucometría)", "Orina", "Orina 24 horas",
    "Materia fecal (coprológico)", "Esputo", "Hisopado nasofaríngeo", "Hisopado faríngeo",
    "Secreción de herida", "Líquido corporal", "Otro",
)

# Tipos de recipiente / tubo, con el código de color estándar que se usa
# en Colombia para identificar el anticoagulante o aditivo que contiene
# -- fundamental para que la muestra no se dañe ni quede inservible.
TIPOS_RECIPIENTE = (
    "Tubo tapa roja (sin anticoagulante — química, serología)",
    "Tubo tapa lila/morada (EDTA — hematología, cuadro hemático)",
    "Tubo tapa azul (citrato de sodio — pruebas de coagulación)",
    "Tubo tapa amarilla (gel separador — química, hormonas)",
    "Tubo tapa gris (fluoruro de sodio — glicemia)",
    "Tubo tapa verde (heparina — química especial)",
    "Frasco estéril de boca ancha (urocultivo/coprocultivo)",
    "Frasco para orina 24 horas",
    "Frasco coprológico",
    "Hisopo con medio de transporte",
    "Otro",
)

CONDICIONES_TRANSPORTE = ("Temperatura ambiente", "Refrigerada (2-8°C)", "Congelada", "Protegida de la luz")

ESTADOS = ("Recolectada", "En tránsito", "Entregada al laboratorio", "Procesada", "Rechazada")


def registrar_recoleccion(paciente_id, profesional_id, tipo_muestra, tipo_recipiente, fecha_hora_recoleccion,
                             cantidad_recipientes=1, examenes_solicitados="", condiciones_transporte="Temperatura ambiente",
                             laboratorio_destino="", observaciones="", foto_muestra_base64=None,
                             firma_recoleccion_base64=None, servicio_paciente_id=None, programacion_id=None,
                             usuario_id=None, usuario_nombre="") -> int:
    """
    Registra la recolección de una muestra -- el primer eslabón
    de la cadena de custodia. Se llama en el momento exacto en
    que el profesional toma la muestra en el domicilio del
    paciente.
    """
    if not tipo_muestra:
        raise ValueError("Debe indicar el tipo de muestra tomada.")
    if not tipo_recipiente:
        raise ValueError("Debe indicar en qué tipo de recipiente/frasco se tomó la muestra.")
    if not fecha_hora_recoleccion:
        raise ValueError("Debe indicar la fecha y hora exacta de la recolección.")

    muestra_id = ejecutar(
        """
        INSERT INTO trazabilidad_muestras(
            servicio_paciente_id, programacion_id, paciente_id, profesional_id, tipo_muestra, tipo_recipiente,
            cantidad_recipientes, examenes_solicitados, fecha_hora_recoleccion, condiciones_transporte,
            estado, laboratorio_destino, observaciones, foto_muestra_base64, firma_recoleccion_base64, usuario_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Recolectada', ?, ?, ?, ?, ?)
        """,
        (servicio_paciente_id, programacion_id, paciente_id, profesional_id, tipo_muestra, tipo_recipiente,
         cantidad_recipientes or 1, examenes_solicitados or "", fecha_hora_recoleccion, condiciones_transporte or "",
         laboratorio_destino or "", observaciones or "", foto_muestra_base64, firma_recoleccion_base64, usuario_id),
    )

    _registrar_evento(muestra_id, "Recolectada", usuario_id, usuario_nombre, f"Muestra recolectada — {tipo_muestra} en {tipo_recipiente}.")

    return muestra_id


def _registrar_evento(muestra_id: int, estado: str, usuario_id, usuario_nombre, observaciones=""):
    ejecutar(
        "INSERT INTO trazabilidad_muestras_eventos(muestra_id, estado, usuario_id, usuario_nombre, observaciones) VALUES (?, ?, ?, ?, ?)",
        (muestra_id, estado, usuario_id, usuario_nombre or "", observaciones or ""),
    )


def cambiar_estado(muestra_id: int, nuevo_estado: str, usuario_id, usuario_nombre="", observaciones="",
                     responsable_entrega=None, responsable_recibe=None, incidencia=None):
    """
    Avanza (o retrocede, si hace falta corregir) la muestra por
    la cadena de custodia -- cada cambio queda con su propio
    registro en el historial, sin borrar los anteriores.
    """
    if nuevo_estado not in ESTADOS:
        raise ValueError(f"Estado no válido. Use uno de: {', '.join(ESTADOS)}")

    muestra = consultar_uno("SELECT * FROM trazabilidad_muestras WHERE id=?", (muestra_id,))
    if not muestra:
        raise ValueError("La muestra indicada no existe.")

    if nuevo_estado == "Rechazada" and not incidencia:
        raise ValueError("Debe indicar el motivo por el que se rechaza la muestra.")

    campos_extra = ""
    valores_extra = []
    if nuevo_estado == "Entregada al laboratorio":
        campos_extra = ", fecha_entrega_laboratorio=CURRENT_TIMESTAMP"
    if responsable_entrega:
        campos_extra += ", responsable_entrega=?"
        valores_extra.append(responsable_entrega)
    if responsable_recibe:
        campos_extra += ", responsable_recibe=?"
        valores_extra.append(responsable_recibe)
    if incidencia:
        campos_extra += ", incidencia=?"
        valores_extra.append(incidencia)

    ejecutar(
        f"UPDATE trazabilidad_muestras SET estado=?{campos_extra} WHERE id=?",
        (nuevo_estado, *valores_extra, muestra_id),
    )

    _registrar_evento(muestra_id, nuevo_estado, usuario_id, usuario_nombre, observaciones or incidencia or "")


def obtener(muestra_id: int):
    fila = consultar_uno(
        """
        SELECT m.*, p.primer_nombre, p.primer_apellido, p.documento, p.tipo_documento,
               pr.primer_nombre AS prof_nombre, pr.primer_apellido AS prof_apellido
        FROM trazabilidad_muestras m
        JOIN pacientes p ON p.id = m.paciente_id
        LEFT JOIN profesionales pr ON pr.id = m.profesional_id
        WHERE m.id=?
        """,
        (muestra_id,),
    )
    if not fila:
        return None
    muestra = dict(fila)
    muestra["eventos"] = listar_eventos(muestra_id)
    return muestra


def listar_eventos(muestra_id: int):
    filas = consultar_todos(
        "SELECT * FROM trazabilidad_muestras_eventos WHERE muestra_id=? ORDER BY fecha_hora ASC",
        (muestra_id,),
    )
    return [dict(f) for f in filas]


def listar_por_paciente(paciente_id: int):
    filas = consultar_todos(
        "SELECT * FROM trazabilidad_muestras WHERE paciente_id=? ORDER BY fecha_hora_recoleccion DESC",
        (paciente_id,),
    )
    return [dict(f) for f in filas]


def listar_pendientes_entrega():
    """Muestras ya recolectadas (o en tránsito) que todavía no se han entregado al laboratorio -- para hacerles seguimiento y que no se queden olvidadas."""
    filas = consultar_todos(
        """
        SELECT m.*, p.primer_nombre, p.primer_apellido, p.documento
        FROM trazabilidad_muestras m
        JOIN pacientes p ON p.id = m.paciente_id
        WHERE m.estado IN ('Recolectada', 'En tránsito')
        ORDER BY m.fecha_hora_recoleccion ASC
        """
    )
    return [dict(f) for f in filas]


def resumen_dashboard():
    fila = consultar_uno(
        """
        SELECT
            SUM(CASE WHEN estado IN ('Recolectada', 'En tránsito') THEN 1 ELSE 0 END) AS pendientes_entrega,
            SUM(CASE WHEN estado = 'Rechazada' THEN 1 ELSE 0 END) AS rechazadas,
            COUNT(*) AS total
        FROM trazabilidad_muestras
        WHERE date(fecha_hora_recoleccion) >= date('now', '-30 days')
        """
    )
    f = dict(fila) if fila else {}
    return {"pendientes_entrega": f.get("pendientes_entrega") or 0, "rechazadas": f.get("rechazadas") or 0, "total": f.get("total") or 0}
