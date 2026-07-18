"""
HomeCare Enterprise - Historia Clínica Consolidada

Une en una sola línea de tiempo todo lo que le ha pasado al
paciente: notas de evolución (incluidas las asignaciones de
programa), medicamentos administrados, órdenes médicas
(exámenes/procedimientos) y visitas domiciliarias realizadas.
"""

from database.database import consultar_todos, consultar_uno


def obtener_informes_cuidador(paciente_id: int) -> list:
    """
    Las notas que hace el Cuidador NO se mezclan con la
    historia clínica principal (esa es para el personal de
    salud). Quedan aparte, como su propio registro de
    informes de las visitas del cuidador al paciente, que se
    puede consultar e imprimir de forma independiente.
    """

    filas = consultar_todos(
        """
        SELECT e.id, e.fecha, e.nota, e.consecutivo, e.tipo_registro,
               e.nota_aclaratoria_de, e.firma_profesional_base64,
               pr.nombre_completo AS profesional
        FROM evoluciones e
        LEFT JOIN profesionales pr ON pr.id = e.profesional_id
        WHERE e.paciente_id=? AND e.tipo_profesional='Nota de Cuidador'
        ORDER BY e.consecutivo DESC
        """,
        (paciente_id,),
    )
    return [dict(f) for f in filas]


def obtener_linea_tiempo(paciente_id: int) -> list:

    eventos = []

    evoluciones = consultar_todos(
        """
        SELECT e.id, e.fecha, e.tipo_profesional, e.nota, e.origen,
               e.consecutivo, e.tipo_registro, e.nota_aclaratoria_de,
               e.firma_profesional_base64,
               pr.nombre_completo AS profesional
        FROM evoluciones e
        LEFT JOIN profesionales pr ON pr.id = e.profesional_id
        WHERE e.paciente_id=? AND e.origen != 'ASIGNACION_PROGRAMA'
          AND (e.tipo_profesional != 'Nota de Cuidador' OR e.tipo_profesional IS NULL)
        """,
        (paciente_id,),
    )
    for e in evoluciones:
        e = dict(e)

        if e["tipo_registro"] == "NOTA_ACLARATORIA":
            tipo = "Nota aclaratoria"
            icono = "fa-pen-to-square"
            color = "danger"
        else:
            tipo = "Evolución"
            icono = "fa-notes-medical"
            color = "secondary"

        eventos.append({
            "id": e["id"],
            "fecha": e["fecha"],
            "tipo": tipo,
            "icono": icono,
            "color": color,
            "titulo": e["tipo_profesional"] or "Evolución clínica",
            "detalle": e["nota"],
            "profesional": e["profesional"],
            "consecutivo": e["consecutivo"],
            "tipo_registro": e["tipo_registro"],
            "nota_aclaratoria_de": e["nota_aclaratoria_de"],
            "firma": e["firma_profesional_base64"],
            "es_informe": e["tipo_registro"] == "INFORME",
        })

    medicamentos = consultar_todos(
        """
        SELECT am.fecha, am.hora, am.dosis, am.via, am.observaciones, am.profesional,
               m.nombre AS medicamento
        FROM administracion_medicamentos am
        LEFT JOIN medicamentos m ON m.id = am.medicamento_id
        WHERE am.paciente_id=?
        """,
        (paciente_id,),
    )
    for m in medicamentos:
        m = dict(m)
        eventos.append({
            "fecha": f"{m['fecha']} {m['hora'] or ''}".strip(),
            "tipo": "Medicamento",
            "icono": "fa-pills",
            "color": "success",
            "titulo": m["medicamento"] or "Medicamento administrado",
            "detalle": f"Dosis: {m['dosis'] or '—'} · Vía: {m['via'] or '—'}" + (f" · {m['observaciones']}" if m["observaciones"] else ""),
            "profesional": m["profesional"],
        })

    ordenes = consultar_todos(
        """
        SELECT o.fecha_orden AS fecha, o.tipo, o.descripcion, o.estado,
               pr.nombre_completo AS profesional
        FROM ordenes_medicas o
        LEFT JOIN profesionales pr ON pr.id = o.profesional_id
        WHERE o.paciente_id=?
        """,
        (paciente_id,),
    )
    for o in ordenes:
        o = dict(o)
        eventos.append({
            "fecha": o["fecha"],
            "tipo": "Orden médica",
            "icono": "fa-file-prescription",
            "color": "warning",
            "titulo": f"{o['tipo'] or 'Orden médica'} ({o['estado']})",
            "detalle": o["descripcion"],
            "profesional": o["profesional"],
        })

    # NOTA: la programación/agenda de visitas (quién la atiende,
    # cuándo, cuántas sesiones) NO se muestra aquí -- eso se
    # consulta desde el botón "Servicios Asignados" del
    # paciente. La Historia Clínica solo debe reflejar el
    # contenido clínico: informes, notas aclaratorias, órdenes,
    # medicamentos administrados y fotos de procedimientos.

    fotos = consultar_todos(
        """
        SELECT fp.fecha, fp.descripcion, fp.foto_base64, pr.nombre_completo AS profesional
        FROM fotos_procedimientos fp
        LEFT JOIN profesionales pr ON pr.id = fp.profesional_id
        WHERE fp.paciente_id=?
        """,
        (paciente_id,),
    )
    for f in fotos:
        f = dict(f)
        eventos.append({
            "fecha": f["fecha"],
            "tipo": "Foto de procedimiento",
            "icono": "fa-camera",
            "color": "dark",
            "titulo": f["descripcion"] or "Foto de procedimiento",
            "detalle": "",
            "imagen": f["foto_base64"],
            "profesional": f["profesional"],
        })

    insumos_entregados = consultar_todos(
        """
        SELECT m.fecha, m.cantidad, m.motivo, i.nombre AS insumo, i.unidad_medida,
               pr.nombre_completo AS profesional
        FROM inventario_movimientos m
        JOIN insumos i ON i.id = m.insumo_id
        LEFT JOIN profesionales pr ON pr.id = m.profesional_id
        WHERE m.paciente_id=? AND m.tipo='Salida'
        """,
        (paciente_id,),
    )
    for m in insumos_entregados:
        m = dict(m)
        eventos.append({
            "fecha": m["fecha"],
            "tipo": "Entrega de insumos",
            "icono": "fa-box-open",
            "color": "warning",
            "titulo": f"Entrega: {m['insumo']} ({m['cantidad']} {m['unidad_medida']})",
            "detalle": m["motivo"] or "Insumos entregados para el tratamiento del paciente.",
            "profesional": m["profesional"],
        })

    resultados_laboratorio = consultar_todos(
        """
        SELECT lr.*, pr.nombre_completo AS profesional
        FROM laboratorios_resultados lr
        LEFT JOIN profesionales pr ON pr.id = lr.profesional_id
        WHERE lr.paciente_id=?
        """,
        (paciente_id,),
    )
    for r in resultados_laboratorio:
        r = dict(r)

        items = consultar_todos(
            "SELECT * FROM laboratorio_items WHERE resultado_id=? ORDER BY id", (r["id"],)
        )
        items = [dict(i) for i in items]

        detalle = r["resultado_texto"] or ""
        if r["laboratorio_realizo"]:
            detalle = f"Laboratorio: {r['laboratorio_realizo']}. " + detalle

        alterados = [i for i in items if i["interpretacion"] in ("Alto", "Bajo")]
        if items:
            resumen_items = "; ".join(
                f"{i['nombre_parametro']}: {i['valor_obtenido']} {i['unidad'] or ''}"
                + (f" ({i['interpretacion']})" if i["interpretacion"] in ("Alto", "Bajo") else "")
                for i in items
            )
            detalle = (detalle + " — " if detalle else "") + resumen_items

        eventos.append({
            "fecha": r["fecha_resultado"] or r["fecha_creacion"],
            "tipo": "Resultado de laboratorio",
            "icono": "fa-vial-circle-check",
            "color": "danger" if alterados else "success",
            "titulo": r["nombre_examen"] + (" ⚠ valores fuera de rango" if alterados else ""),
            "detalle": detalle,
            "imagen": r["foto_resultado_base64"],
            "profesional": r["profesional"],
        })

    examenes_fisicos = consultar_todos(
        """
        SELECT ef.*, pr.nombre_completo AS profesional
        FROM examen_fisico ef
        LEFT JOIN profesionales pr ON pr.id = ef.profesional_id
        WHERE ef.paciente_id=?
        """,
        (paciente_id,),
    )
    for ef in examenes_fisicos:
        ef = dict(ef)
        sistemas_con_hallazgo = []
        for sistema in ("cabeza", "cara", "boca", "cuello", "torax", "abdomen", "extremidades", "vascular", "neurologico", "columna"):
            if ef.get(sistema):
                sistemas_con_hallazgo.append(f"{sistema.capitalize()}: {ef[sistema]}")
        eventos.append({
            "fecha": ef["fecha_creacion"],
            "tipo": "Examen físico",
            "icono": "fa-stethoscope",
            "color": "primary",
            "titulo": f"Examen físico ({ef.get('tipo_profesional') or 'sin especificar'})",
            "detalle": " | ".join(sistemas_con_hallazgo) if sistemas_con_hallazgo else "Sin hallazgos registrados.",
            "imagen": None,
            "profesional": ef["profesional"],
        })

    recomendaciones = consultar_todos(
        """
        SELECT r.*, pr.nombre_completo AS profesional
        FROM recomendaciones_medicas r
        LEFT JOIN profesionales pr ON pr.id = r.profesional_id
        WHERE r.paciente_id=?
        """,
        (paciente_id,),
    )
    for r in recomendaciones:
        r = dict(r)
        detalle = f"Dx principal: {r['diagnostico_ppal_nombre']} ({r['diagnostico_ppal_codigo']})"
        for n in (1, 2, 3):
            if r.get(f"diagnostico_rel{n}_nombre"):
                detalle += f" | Relacionado {n}: {r[f'diagnostico_rel{n}_nombre']}"
        if r.get("recomendaciones_texto"):
            detalle += f" — {r['recomendaciones_texto']}"
        eventos.append({
            "fecha": r["fecha_creacion"],
            "tipo": "Recomendaciones / Plan médico",
            "icono": "fa-clipboard-list",
            "color": "danger",
            "titulo": f"Plan médico — {r['tipo_consulta']}",
            "detalle": detalle,
            "imagen": None,
            "profesional": r["profesional"],
        })

    eventos.sort(key=lambda e: e["fecha"] or "", reverse=True)

    return eventos


def obtener_carpeta_completa(paciente_id: int) -> dict:
    """
    La "Carpeta del Paciente" -- a diferencia de la Historia
    Clínica (que es el documento clínico formal, reservado al
    personal de salud), esta es una vista administrativa de
    TODO lo que se le ha registrado al paciente, agrupada por
    fecha: notas clínicas, órdenes, exámenes, y también los
    informes de los cuidadores y los consentimientos firmados
    -- todo junto, para poder revisar o imprimir rápidamente lo
    que se necesite (por ejemplo, la historia clínica reciente
    junto con una orden médica, para enviárselas juntas al
    paciente).
    """
    eventos = obtener_linea_tiempo(paciente_id)

    informes_cuidador = obtener_informes_cuidador(paciente_id)
    for c in informes_cuidador:
        eventos.append({
            "id": c["id"], "fecha": c["fecha"], "tipo": "Informe de Cuidador",
            "icono": "fa-hands-holding-child", "color": "info",
            "titulo": "Informe de cuidador" + (" (nota aclaratoria)" if c["tipo_registro"] == "NOTA_ACLARATORIA" else ""),
            "detalle": c["nota"], "profesional": c["profesional"],
            "consecutivo": c["consecutivo"], "tipo_registro": c["tipo_registro"],
            "nota_aclaratoria_de": c["nota_aclaratoria_de"], "firma": c["firma_profesional_base64"],
            "es_informe_cuidador": True,
        })

    consentimientos = consultar_todos(
        "SELECT * FROM consentimientos_informados WHERE paciente_id=? ORDER BY fecha_diligenciamiento DESC",
        (paciente_id,),
    )
    for cons in consentimientos:
        cons = dict(cons)
        eventos.append({
            "id": cons["id"], "fecha": cons["fecha_diligenciamiento"], "tipo": "Consentimiento Informado",
            "icono": "fa-file-signature", "color": "dark",
            "titulo": f"Consentimiento — {cons['tipo']}",
            "detalle": f"Firmado por: {cons.get('nombre_firmante') or '—'} ({cons.get('firmante') or 'paciente'})",
            "profesional": None, "es_consentimiento": True,
        })

    eventos.sort(key=lambda e: e["fecha"] or "", reverse=True)

    # Cada evento necesita una clave única para poder
    # seleccionarlo en la pantalla -- algunos tipos (medicamentos,
    # fotos, insumos, laboratorios, examen físico, recomendaciones)
    # no traen un "id" individual desde su consulta original, así
    # que se les asigna uno aquí, basado en su posición.
    for indice, evento in enumerate(eventos):
        evento["clave_unica"] = f"{evento['tipo']}-{evento.get('id') if evento.get('id') is not None else indice}"

    grupos = {}
    for e in eventos:
        clave_fecha = (e["fecha"] or "")[:10] or "Sin fecha"
        grupos.setdefault(clave_fecha, []).append(e)

    return {
        "eventos_por_fecha": [{"fecha": f, "eventos": grupos[f]} for f in sorted(grupos.keys(), reverse=True)],
        "total_eventos": len(eventos),
    }


def obtener_informe_para_imprimir(evolucion_id: int) -> dict:
    """
    Junta todo lo necesario para imprimir UN informe (o nota
    aclaratoria) individual, con los datos completos del
    paciente y la fecha/hora exacta en que se hizo -- para que
    cada reporte se pueda imprimir por separado, tal como
    quedó redactado y firmado en su momento.
    """

    from datetime import date

    fila = consultar_uno(
        """
        SELECT e.*, pr.nombre_completo AS profesional_nombre,
               pr.especialidad_principal AS profesional_especialidad,
               pr.registro_profesional, pr.documento AS profesional_documento
        FROM evoluciones e
        LEFT JOIN profesionales pr ON pr.id = e.profesional_id
        WHERE e.id=?
        """,
        (evolucion_id,),
    )

    if not fila:
        raise ValueError("El informe solicitado no existe.")

    fila = dict(fila)

    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (fila["paciente_id"],))
    if not paciente:
        raise ValueError("El paciente de este informe ya no existe.")
    paciente = dict(paciente)

    edad = None
    if paciente.get("fecha_nacimiento"):
        try:
            nacimiento = date.fromisoformat(str(paciente["fecha_nacimiento"])[:10])
            hoy = date.today()
            edad = hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))
        except ValueError:
            edad = None

    informe_corregido = None
    if fila.get("nota_aclaratoria_de"):
        informe_corregido = consultar_uno(
            "SELECT consecutivo, fecha, nota FROM evoluciones WHERE paciente_id=? AND consecutivo=? AND tipo_registro='INFORME'",
            (fila["paciente_id"], fila["nota_aclaratoria_de"]),
        )
        informe_corregido = dict(informe_corregido) if informe_corregido else None

    return {
        "informe": fila,
        "paciente": paciente,
        "edad": edad,
        "informe_corregido": informe_corregido,
    }
