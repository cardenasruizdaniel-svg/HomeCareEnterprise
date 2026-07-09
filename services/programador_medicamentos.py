from datetime import datetime, timedelta

from repositories.administracion_medicamentos_repository import crear


HORARIOS = {

    "Cada 24 horas": [

        "08:00"

    ],

    "Cada 12 horas": [

        "08:00",

        "20:00"

    ],

    "Cada 8 horas": [

        "06:00",

        "14:00",

        "22:00"

    ],

    "Cada 6 horas": [

        "00:00",

        "06:00",

        "12:00",

        "18:00"

    ]

}


def generar_programacion(

    medicamento_id,

    paciente_id,

    fecha_inicio,

    fecha_fin,

    frecuencia,

    usuario

):

    if frecuencia not in HORARIOS:

        return

    fecha = datetime.strptime(

        fecha_inicio,

        "%Y-%m-%d"

    )

    fin = datetime.strptime(

        fecha_fin,

        "%Y-%m-%d"

    )

    while fecha <= fin:

        for hora in HORARIOS[frecuencia]:

            crear(

                medicamento_id,

                paciente_id,

                fecha.strftime("%Y-%m-%d"),

                hora,

                "",

                "",

                "",

                "Pendiente",

                "",

                "",

                "",

                usuario,

                datetime.now().strftime(

                    "%Y-%m-%d %H:%M:%S"

                )

            )

        fecha += timedelta(days=1)