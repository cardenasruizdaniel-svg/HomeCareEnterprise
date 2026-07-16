"""
HomeCare Enterprise - Registro de evoluciones (nota de la visita)

Funcion compartida entre la web y la app movil para guardar
la nota clinica de una visita, usada tanto por cuidadores y
enfermeros como por profesionales de la salud.

Cada nota queda con:
- Un CONSECUTIVO propio del paciente (Informe N.° 1, 2, 3...),
  para que la historia clinica sea trazable.
- La FIRMA del profesional que la hizo, tomada de la que
  quedo guardada al crear su perfil (se copia/"snapshotea" en
  cada nota, para que quede fija tal como era en ese momento,
  aunque despues el profesional actualice su firma).
- Si es una NOTA ACLARATORIA (para corregir un informe
  anterior), el numero de consecutivo del informe que corrige.
"""

from database.database import consultar_escalar, consultar_uno, ejecutar


def _siguiente_consecutivo(paciente_id: int) -> int:
    maximo = consultar_escalar(
        "SELECT MAX(consecutivo) FROM evoluciones WHERE paciente_id=?",
        (paciente_id,),
    )
    return (maximo or 0) + 1


def _construir_resumen_registros_visita(paciente_id: int, programacion_id) -> str:
    """
    Arma un bloque de texto con los signos vitales, el examen
    físico, y las alergias/antecedentes que se hayan registrado
    en la MISMA visita -- para incorporarlo dentro de la nota
    clínica que se está guardando, en vez de dejarlos como
    registros sueltos por separado. Así, cuando se completa la
    visita, todo lo que el profesional documentó (nota, signos
    vitales, examen físico, alergias, antecedentes) queda
    reunido en UN solo registro dentro de la historia clínica.

    Si no hay ningún registro adicional para esa visita, no
    agrega nada (la nota queda tal cual el profesional la
    escribió).
    """
    if not programacion_id:
        return ""

    secciones = []

    fila_signos = consultar_uno(
        "SELECT * FROM signos_vitales WHERE programacion_id=? AND paciente_id=? ORDER BY id DESC LIMIT 1",
        (programacion_id, paciente_id),
    )
    if fila_signos:
        s = dict(fila_signos)
        partes = []
        if s.get("temperatura") is not None: partes.append(f"Temp: {s['temperatura']}°C")
        if s.get("presion_sistolica") is not None and s.get("presion_diastolica") is not None:
            partes.append(f"TA: {s['presion_sistolica']}/{s['presion_diastolica']}")
        if s.get("frecuencia_cardiaca") is not None: partes.append(f"FC: {s['frecuencia_cardiaca']}")
        if s.get("frecuencia_respiratoria") is not None: partes.append(f"FR: {s['frecuencia_respiratoria']}")
        if s.get("saturacion_oxigeno") is not None: partes.append(f"SatO2: {s['saturacion_oxigeno']}%")
        if s.get("glucemia") is not None: partes.append(f"Glucemia: {s['glucemia']}")
        if s.get("peso") is not None: partes.append(f"Peso: {s['peso']}kg")
        if s.get("talla") is not None: partes.append(f"Talla: {s['talla']}cm")
        if s.get("imc") is not None: partes.append(f"IMC: {s['imc']}")
        if s.get("dolor") is not None: partes.append(f"Dolor: {s['dolor']}/10")
        if partes:
            secciones.append("📊 Signos vitales: " + ", ".join(partes))
        if s.get("observaciones"):
            secciones.append(f"   Observaciones: {s['observaciones']}")

    fila_examen = consultar_uno(
        "SELECT * FROM examen_fisico WHERE programacion_id=? AND paciente_id=? ORDER BY id DESC LIMIT 1",
        (programacion_id, paciente_id),
    )
    if fila_examen:
        e = dict(fila_examen)
        campos_examen = ["cabeza", "cara", "boca", "cuello", "torax", "abdomen", "extremidades", "vascular", "neurologico", "columna"]
        hallazgos = [f"{campo.capitalize()}: {e[campo]}" for campo in campos_examen if e.get(campo)]
        if hallazgos:
            secciones.append("🩺 Examen físico: " + " | ".join(hallazgos))

    # Alergias y antecedentes no se registran "por visita" (son
    # datos del paciente en general), así que se toman los que
    # se hayan creado el MISMO día de esta visita -- son los que
    # tiene sentido asumir que se documentaron durante ella.
    fila_fecha_visita = consultar_uno("SELECT fecha FROM programaciones WHERE id=?", (programacion_id,))
    fecha_visita = dict(fila_fecha_visita)["fecha"] if fila_fecha_visita else None

    if fecha_visita:
        alergias_del_dia = consultar_uno(
            "SELECT GROUP_CONCAT(alergeno || ' (' || severidad || ')', '; ') AS lista FROM alergias "
            "WHERE paciente_id=? AND date(fecha_registro)=date(?)",
            (paciente_id, fecha_visita),
        )
        if alergias_del_dia and dict(alergias_del_dia)["lista"]:
            secciones.append("⚠ Alergias registradas en esta visita: " + dict(alergias_del_dia)["lista"])

        antecedentes_del_dia = consultar_uno(
            "SELECT GROUP_CONCAT(tipo || ': ' || descripcion, '; ') AS lista FROM antecedentes "
            "WHERE paciente_id=? AND date(fecha_creacion)=date(?)",
            (paciente_id, fecha_visita),
        )
        if antecedentes_del_dia and dict(antecedentes_del_dia)["lista"]:
            secciones.append("📋 Antecedentes registrados en esta visita: " + dict(antecedentes_del_dia)["lista"])

    if not secciones:
        return ""

    return "\n\n— Registros de esta visita —\n" + "\n".join(secciones)


def registrar_evolucion(paciente_id, programacion_id, profesional_id, tipo_profesional, nota,
                          origen="WEB", latitud=None, longitud=None, usuario_id=None,
                          tipo_registro="INFORME", nota_aclaratoria_de=None) -> dict:

    if not nota or not nota.strip():
        raise ValueError("La nota de la visita no puede estar vacía.")

    if tipo_registro not in ("INFORME", "NOTA_ACLARATORIA"):
        raise ValueError("Tipo de registro no válido.")

    if tipo_registro == "NOTA_ACLARATORIA" and not nota_aclaratoria_de:
        raise ValueError("Debe indicar a qué informe corresponde la nota aclaratoria.")

    # Si es un informe normal (no una nota aclaratoria) de un
    # profesional de la salud, se incorpora dentro de la MISMA
    # nota lo que se haya registrado en esta visita: signos
    # vitales, examen físico, alergias y antecedentes -- así
    # queda todo reunido en un solo registro de la historia
    # clínica, en vez de piezas sueltas por separado. No aplica
    # a los informes de cuidador (ellos no registran estos
    # datos clínicos).
    if tipo_registro == "INFORME" and (tipo_profesional or "").strip().lower() != "cuidador":
        resumen_visita = _construir_resumen_registros_visita(paciente_id, programacion_id)
        if resumen_visita:
            nota = nota.rstrip() + resumen_visita

    firma_profesional = None
    if profesional_id:
        fila_profesional = consultar_uno(
            "SELECT firma_base64 FROM profesionales WHERE id=?", (profesional_id,)
        )
        if fila_profesional:
            firma_profesional = dict(fila_profesional).get("firma_base64")

    consecutivo = _siguiente_consecutivo(paciente_id)

    ejecutar(
        """
        INSERT INTO evoluciones(
            paciente_id, programacion_id, profesional_id, tipo_profesional,
            nota, latitud, longitud, origen, usuario_creacion,
            consecutivo, tipo_registro, nota_aclaratoria_de, firma_profesional_base64
        ) VALUES (
            :paciente_id, :programacion_id, :profesional_id, :tipo_profesional,
            :nota, :latitud, :longitud, :origen, :usuario_creacion,
            :consecutivo, :tipo_registro, :nota_aclaratoria_de, :firma_profesional_base64
        )
        """,
        {
            "paciente_id": paciente_id,
            "programacion_id": programacion_id,
            "profesional_id": profesional_id,
            "tipo_profesional": tipo_profesional,
            "nota": nota,
            "latitud": latitud,
            "longitud": longitud,
            "origen": origen,
            "usuario_creacion": usuario_id,
            "consecutivo": consecutivo,
            "tipo_registro": tipo_registro,
            "nota_aclaratoria_de": nota_aclaratoria_de,
            "firma_profesional_base64": firma_profesional,
        },
    )

    return {"ok": True, "consecutivo": consecutivo}


def listar_informes_para_aclarar(paciente_id: int):
    """
    Lista los informes (no las notas aclaratorias) de un
    paciente, para elegir a cual se le va a hacer una nota
    aclaratoria.
    """
    from database.database import consultar_todos
    return [
        dict(f) for f in consultar_todos(
            """
            SELECT consecutivo, fecha, tipo_profesional, nota
            FROM evoluciones
            WHERE paciente_id=? AND tipo_registro='INFORME'
            ORDER BY consecutivo DESC
            """,
            (paciente_id,),
        )
    ]
