"""
HomeCare Enterprise - Generador de archivos de calendario (.ics)

El formato iCalendar (.ics) es el estandar universal que
entienden Google Calendar, Outlook y Apple Calendar por igual.
Al enviarlo por correo como adjunto, el paciente o el
profesional simplemente lo abren y el evento se agrega solo a
su calendario personal -- sin necesidad de que la IPS pida
permisos de acceso a la cuenta de nadie.

Para una integracion mas profunda (que HomeCare Enterprise
escriba directamente en el Google Calendar del profesional,
sin que el intervenga), se necesitaria que cada profesional
autorice el acceso via OAuth de Google -- ver
docs/GOOGLE_CALENDAR.md para el detalle de ese camino, que
requiere que la IPS registre una aplicacion en Google Cloud.
"""

import uuid
from datetime import datetime, timedelta


def generar_ics_lote_turnos(turnos: list, nombre_paciente: str, nombre_profesional: str) -> str:
    """
    Igual que generar_ics_visita, pero para un LOTE de varios
    turnos de una vez (ej. cuando se le asignan a un cuidador
    todos los turnos de un mes de una sola vez) -- un solo
    archivo .ics con un evento por cada turno, para que se
    agreguen todos juntos al calendario personal.
    """

    def _formatear(dt):
        return dt.strftime("%Y%m%dT%H%M%S")

    dtstamp = _formatear(datetime.now())

    eventos = []
    for turno in turnos:
        inicio_dt = datetime.strptime(f"{turno['fecha']} {turno['hora_inicio']}", "%Y-%m-%d %H:%M")
        fin_dt = datetime.strptime(f"{turno['fecha']} {turno['hora_fin']}", "%Y-%m-%d %H:%M")
        uid = f"{uuid.uuid4()}@homecare-enterprise"

        resumen = f"HomeCare - {turno.get('turno', 'Turno')} - {nombre_paciente}".replace(",", "\\,")
        descripcion = f"Turno: {turno.get('turno','')}\\nPaciente: {nombre_paciente}\\nProfesional: {nombre_profesional}"

        eventos.append("\r\n".join([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART:{_formatear(inicio_dt)}",
            f"DTEND:{_formatear(fin_dt)}",
            f"SUMMARY:{resumen}",
            f"DESCRIPTION:{descripcion}",
            "STATUS:CONFIRMED",
            "BEGIN:VALARM",
            "TRIGGER:-PT10M",
            "ACTION:DISPLAY",
            "DESCRIPTION:Recordatorio de turno HomeCare",
            "END:VALARM",
            "END:VEVENT",
        ]))

    contenido = "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//HomeCare Enterprise//Turnos//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        *eventos,
        "END:VCALENDAR",
    ])

    return contenido


def generar_ics_visita(visita: dict, nombre_paciente: str, nombre_profesional: str) -> str:
    """
    Genera el contenido de un archivo .ics para una visita
    domiciliaria, listo para adjuntar a un correo.
    """

    fecha = visita["fecha"]
    hora_inicio = visita.get("hora_inicio") or "08:00"
    hora_fin = visita.get("hora_fin") or "09:00"

    inicio_dt = datetime.strptime(f"{fecha} {hora_inicio}", "%Y-%m-%d %H:%M")
    fin_dt = datetime.strptime(f"{fecha} {hora_fin}", "%Y-%m-%d %H:%M")

    def _formatear(dt):
        return dt.strftime("%Y%m%dT%H%M%S")

    uid = f"{uuid.uuid4()}@homecare-enterprise"
    dtstamp = _formatear(datetime.now())

    direccion = ", ".join(
        x for x in [visita.get("direccion"), visita.get("barrio"), visita.get("municipio")] if x
    )

    descripcion = (
        f"Visita domiciliaria - {visita.get('servicio', '')}\\n"
        f"Paciente: {nombre_paciente}\\n"
        f"Profesional: {nombre_profesional}\\n"
        f"Dirección: {direccion}"
    ).replace(",", "\\,")

    resumen = f"HomeCare - {visita.get('servicio', 'Visita domiciliaria')}".replace(",", "\\,")

    direccion_ics = direccion.replace(",", "\\,")

    contenido = "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//HomeCare Enterprise//Visitas Domiciliarias//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{_formatear(inicio_dt)}",
        f"DTEND:{_formatear(fin_dt)}",
        f"SUMMARY:{resumen}",
        f"DESCRIPTION:{descripcion}",
        f"LOCATION:{direccion_ics}",
        "STATUS:CONFIRMED",
        "BEGIN:VALARM",
        "TRIGGER:-PT1H",
        "ACTION:DISPLAY",
        "DESCRIPTION:Recordatorio de visita domiciliaria HomeCare",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ])

    return contenido
