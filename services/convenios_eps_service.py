"""
HomeCare Enterprise - Convenios con EPS

Cada convenio define el plan de servicios pactado con una EPS:
cuántas sesiones/visitas de cada tipo están incluidas, cada
cuántos días se reinicia ese tope, y el valor que se cobra
tanto para lo incluido como para lo que se pase del tope.

Varios tipos de servicio pueden compartir un mismo tope (por
ejemplo, las 4 terapias -- física, ocupacional, respiratoria,
fonoaudiología -- comparten el tope de 12 sesiones al mes,
aunque cada una tenga su propio valor).
"""

from database.database import consultar_todos, consultar_uno, ejecutar

# Nombre del grupo que comparte un mismo tope -- las 4 terapias
# van agrupadas bajo este mismo nombre en el convenio.
GRUPO_TERAPIAS = "Terapias"


# ==========================================
# CONVENIOS (el contrato con la EPS)
# ==========================================

def listar_convenios(solo_vigentes=False):
    sql = "SELECT * FROM convenios_eps"
    if solo_vigentes:
        sql += " WHERE estado='Vigente'"
    sql += " ORDER BY eps, nombre_plan"
    return [dict(c) for c in consultar_todos(sql)]


def obtener_convenio(convenio_id: int):
    fila = consultar_uno("SELECT * FROM convenios_eps WHERE id=?", (convenio_id,))
    if not fila:
        return None
    convenio = dict(fila)
    convenio["servicios"] = listar_servicios_convenio(convenio_id)
    return convenio


def crear_convenio(eps, nit_eps, nombre_plan, numero_convenio, fecha_inicio, fecha_fin, observaciones, usuario_id) -> int:
    if not eps or not nombre_plan:
        raise ValueError("Debe indicar la EPS y el nombre del plan.")
    return ejecutar(
        "INSERT INTO convenios_eps(eps, nit_eps, nombre_plan, numero_convenio, fecha_inicio, fecha_fin, observaciones, usuario_creacion) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (eps.strip(), nit_eps or "", nombre_plan.strip(), numero_convenio or "", fecha_inicio or None, fecha_fin or None, observaciones or "", usuario_id),
    )


def actualizar_convenio(convenio_id, eps, nit_eps, nombre_plan, numero_convenio, fecha_inicio, fecha_fin, estado, observaciones):
    ejecutar(
        "UPDATE convenios_eps SET eps=?, nit_eps=?, nombre_plan=?, numero_convenio=?, fecha_inicio=?, fecha_fin=?, estado=?, observaciones=? WHERE id=?",
        (eps.strip(), nit_eps or "", nombre_plan.strip(), numero_convenio or "", fecha_inicio or None, fecha_fin or None, estado, observaciones or "", convenio_id),
    )


def finalizar_convenio(convenio_id: int):
    ejecutar("UPDATE convenios_eps SET estado='Finalizado' WHERE id=?", (convenio_id,))


# ==========================================
# PLAN DE SERVICIOS DEL CONVENIO
# ==========================================

def listar_servicios_convenio(convenio_id: int):
    filas = consultar_todos(
        "SELECT * FROM convenios_eps_servicios WHERE convenio_id=? AND activo=1 ORDER BY tipo_servicio", (convenio_id,)
    )
    return [dict(f) for f in filas]


def agregar_servicio_convenio(convenio_id, tipo_servicio, grupo_tope, limite_cantidad, dias_ciclo,
                                valor_normal, valor_adicional) -> int:
    if not tipo_servicio:
        raise ValueError("Debe indicar el tipo de servicio.")
    if not limite_cantidad or int(limite_cantidad) <= 0:
        raise ValueError("El límite de cantidad debe ser mayor a cero.")
    if not dias_ciclo or int(dias_ciclo) <= 0:
        raise ValueError("Los días del ciclo deben ser mayores a cero.")

    return ejecutar(
        "INSERT INTO convenios_eps_servicios(convenio_id, tipo_servicio, grupo_tope, limite_cantidad, dias_ciclo, valor_normal, valor_adicional) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (convenio_id, tipo_servicio.strip(), (grupo_tope or "").strip() or None,
         int(limite_cantidad), int(dias_ciclo), float(valor_normal or 0), float(valor_adicional or 0)),
    )


def actualizar_servicio_convenio(servicio_id, tipo_servicio, grupo_tope, limite_cantidad, dias_ciclo,
                                    valor_normal, valor_adicional):
    ejecutar(
        "UPDATE convenios_eps_servicios SET tipo_servicio=?, grupo_tope=?, limite_cantidad=?, dias_ciclo=?, valor_normal=?, valor_adicional=? WHERE id=?",
        (tipo_servicio.strip(), (grupo_tope or "").strip() or None, int(limite_cantidad), int(dias_ciclo),
         float(valor_normal or 0), float(valor_adicional or 0), servicio_id),
    )


def quitar_servicio_convenio(servicio_id: int):
    ejecutar("UPDATE convenios_eps_servicios SET activo=0 WHERE id=?", (servicio_id,))


# ==========================================
# ASIGNACIÓN DEL CONVENIO AL PACIENTE
# ==========================================

def convenio_actual_paciente(paciente_id: int):
    fila = consultar_uno(
        """
        SELECT pc.*, ce.eps, ce.nombre_plan, ce.estado AS convenio_estado
        FROM paciente_convenio pc
        JOIN convenios_eps ce ON ce.id = pc.convenio_id
        WHERE pc.paciente_id=? AND pc.es_actual=1
        """,
        (paciente_id,),
    )
    return dict(fila) if fila else None


def asignar_convenio_paciente(paciente_id, convenio_id, fecha_ingreso, usuario_id) -> int:
    if not convenio_id:
        raise ValueError("Debe indicar el convenio/plan de la EPS.")
    if not fecha_ingreso:
        from datetime import date
        fecha_ingreso = date.today().isoformat()

    # Si ya tenía un convenio activo, se cierra (queda en el historial) antes de abrir el nuevo --
    # igual que se hace con los programas de atención.
    ejecutar(
        "UPDATE paciente_convenio SET es_actual=0, fecha_fin=? WHERE paciente_id=? AND es_actual=1",
        (fecha_ingreso, paciente_id),
    )

    return ejecutar(
        "INSERT INTO paciente_convenio(paciente_id, convenio_id, fecha_ingreso, usuario_creacion) VALUES (?, ?, ?, ?)",
        (paciente_id, convenio_id, fecha_ingreso, usuario_id),
    )


def historial_convenios_paciente(paciente_id: int):
    filas = consultar_todos(
        """
        SELECT pc.*, ce.eps, ce.nombre_plan
        FROM paciente_convenio pc
        JOIN convenios_eps ce ON ce.id = pc.convenio_id
        WHERE pc.paciente_id=?
        ORDER BY pc.fecha_ingreso DESC
        """,
        (paciente_id,),
    )
    return [dict(f) for f in filas]


# ==========================================
# GENERACIÓN AUTOMÁTICA DE CUENTAS POR COBRAR
# ==========================================

def _buscar_servicio_convenio(convenio_id: int, tipo_servicio: str):
    """Encuentra la fila del plan que aplica a este tipo de servicio (comparación sin importar mayúsculas/acentos exactos)."""
    fila = consultar_uno(
        "SELECT * FROM convenios_eps_servicios WHERE convenio_id=? AND activo=1 AND LOWER(tipo_servicio)=LOWER(?)",
        (convenio_id, tipo_servicio),
    )
    return dict(fila) if fila else None


def _numero_ciclo(fecha_ingreso: str, fecha_servicio: str, dias_ciclo: int) -> int:
    from datetime import date

    ingreso = date.fromisoformat(fecha_ingreso[:10])
    servicio = date.fromisoformat(fecha_servicio[:10])
    dias_transcurridos = (servicio - ingreso).days
    if dias_transcurridos < 0:
        dias_transcurridos = 0
    return dias_transcurridos // dias_ciclo


def registrar_consumo_servicio(paciente_id: int, tipo_servicio: str, fecha_servicio: str, programacion_id=None):
    """
    Se llama cada vez que se COMPLETA una visita (no cuando
    solo se programa, ni cuando se cancela) -- revisa si el
    paciente tiene un convenio de EPS asignado, y si ese
    servicio está contemplado en el plan. Si es así, cuenta
    cuántas veces se ha usado ese mismo servicio (o el grupo
    que comparte tope, como las terapias) en el ciclo actual
    (los N días desde que el paciente ingresó al plan), y
    genera la cuenta por cobrar con el valor que corresponda:
    el normal si todavía está dentro del tope, o el adicional
    si ya se pasó.

    Si el paciente no tiene convenio asignado, o el servicio no
    está contemplado en su plan, simplemente no genera nada --
    no es un error, solo significa que ese servicio no se
    factura a ninguna EPS por este medio.
    """
    convenio_actual = convenio_actual_paciente(paciente_id)
    if not convenio_actual:
        return None

    plan_servicio = _buscar_servicio_convenio(convenio_actual["convenio_id"], tipo_servicio)
    if not plan_servicio:
        return None

    ciclo = _numero_ciclo(convenio_actual["fecha_ingreso"], fecha_servicio, plan_servicio["dias_ciclo"])

    # Cuenta lo ya consumido en este mismo ciclo -- si el servicio
    # pertenece a un grupo (como "Terapias"), se cuentan TODOS los
    # servicios de ese grupo juntos, no solo el mismo tipo exacto.
    if plan_servicio.get("grupo_tope"):
        fila_conteo = consultar_uno(
            """
            SELECT COUNT(*) AS total FROM cuentas_por_cobrar_eps
            WHERE paciente_id=? AND convenio_id=? AND grupo_tope=? AND numero_ciclo=?
            """,
            (paciente_id, convenio_actual["convenio_id"], plan_servicio["grupo_tope"], ciclo),
        )
    else:
        fila_conteo = consultar_uno(
            """
            SELECT COUNT(*) AS total FROM cuentas_por_cobrar_eps
            WHERE paciente_id=? AND convenio_id=? AND tipo_servicio=? AND numero_ciclo=? AND grupo_tope IS NULL
            """,
            (paciente_id, convenio_actual["convenio_id"], tipo_servicio, ciclo),
        )
    ya_consumidos = dict(fila_conteo)["total"] if fila_conteo else 0

    es_adicional = ya_consumidos >= plan_servicio["limite_cantidad"]
    valor = plan_servicio["valor_adicional"] if es_adicional else plan_servicio["valor_normal"]

    return ejecutar(
        """
        INSERT INTO cuentas_por_cobrar_eps(
            paciente_id, convenio_id, convenio_servicio_id, programacion_id, tipo_servicio, grupo_tope,
            fecha_servicio, numero_ciclo, es_adicional, valor
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (paciente_id, convenio_actual["convenio_id"], plan_servicio["id"], programacion_id, tipo_servicio,
         plan_servicio.get("grupo_tope"), fecha_servicio, ciclo, 1 if es_adicional else 0, valor),
    )


def resumen_consumo_ciclo_actual(paciente_id: int):
    """Para mostrarle al usuario, de un vistazo, cuánto le queda disponible de cada servicio en el ciclo actual."""
    convenio_actual = convenio_actual_paciente(paciente_id)
    if not convenio_actual:
        return None

    from datetime import date
    hoy = date.today().isoformat()
    plan = listar_servicios_convenio(convenio_actual["convenio_id"])

    resumen = []
    vistos_grupos = set()
    for item in plan:
        clave_grupo = item.get("grupo_tope")
        if clave_grupo:
            if clave_grupo in vistos_grupos:
                continue
            vistos_grupos.add(clave_grupo)

        ciclo = _numero_ciclo(convenio_actual["fecha_ingreso"], hoy, item["dias_ciclo"])
        if clave_grupo:
            fila = consultar_uno(
                "SELECT COUNT(*) AS total FROM cuentas_por_cobrar_eps WHERE paciente_id=? AND convenio_id=? AND grupo_tope=? AND numero_ciclo=?",
                (paciente_id, convenio_actual["convenio_id"], clave_grupo, ciclo),
            )
            etiqueta = clave_grupo
        else:
            fila = consultar_uno(
                "SELECT COUNT(*) AS total FROM cuentas_por_cobrar_eps WHERE paciente_id=? AND convenio_id=? AND tipo_servicio=? AND numero_ciclo=? AND grupo_tope IS NULL",
                (paciente_id, convenio_actual["convenio_id"], item["tipo_servicio"], ciclo),
            )
            etiqueta = item["tipo_servicio"]

        usados = dict(fila)["total"] if fila else 0
        resumen.append({
            "etiqueta": etiqueta, "usados": usados, "limite": item["limite_cantidad"],
            "disponibles": max(0, item["limite_cantidad"] - usados), "ciclo_numero": ciclo,
        })

    return {"convenio": convenio_actual, "servicios": resumen}


# ==========================================
# FACTURACIÓN A LA EPS (con los tres modos de agrupación)
# ==========================================

def listar_cuentas_pendientes(fecha_desde=None, fecha_hasta=None, eps=None, paciente_id=None):
    sql = """
        SELECT cc.*, p.primer_nombre, p.primer_apellido, p.documento, p.tipo_documento, ce.eps, ce.nombre_plan
        FROM cuentas_por_cobrar_eps cc
        JOIN pacientes p ON p.id = cc.paciente_id
        JOIN convenios_eps ce ON ce.id = cc.convenio_id
        WHERE cc.estado='Pendiente'
    """
    parametros = []
    if fecha_desde:
        sql += " AND date(cc.fecha_servicio) >= date(?)"
        parametros.append(fecha_desde)
    if fecha_hasta:
        sql += " AND date(cc.fecha_servicio) <= date(?)"
        parametros.append(fecha_hasta)
    if eps:
        sql += " AND ce.eps = ?"
        parametros.append(eps)
    if paciente_id:
        sql += " AND cc.paciente_id = ?"
        parametros.append(paciente_id)
    sql += " ORDER BY ce.eps, p.primer_apellido, cc.fecha_servicio"

    filas = consultar_todos(sql, tuple(parametros))
    return [dict(f) for f in filas]


def resumen_pendientes_por_eps(fecha_desde=None, fecha_hasta=None):
    """Para la pantalla de facturación: cuánto hay pendiente de cobrar, agrupado por EPS."""
    cuentas = listar_cuentas_pendientes(fecha_desde, fecha_hasta)
    por_eps = {}
    for c in cuentas:
        por_eps.setdefault(c["eps"], {"eps": c["eps"], "cantidad": 0, "valor_total": 0})
        por_eps[c["eps"]]["cantidad"] += 1
        por_eps[c["eps"]]["valor_total"] += c["valor"]
    return list(por_eps.values())


def _agrupar_cuentas(cuentas: list, modo: str) -> dict:
    """
    modo:
      - "por_eps": una sola factura con TODOS los pacientes y servicios de esa EPS.
      - "por_paciente": una factura por paciente, con todos sus servicios juntos.
      - "por_paciente_servicio": una factura por cada combinación paciente + tipo de servicio.
    """
    grupos = {}
    for c in cuentas:
        if modo == "por_eps":
            clave = c["eps"]
        elif modo == "por_paciente":
            clave = (c["eps"], c["paciente_id"])
        else:  # por_paciente_servicio
            clave = (c["eps"], c["paciente_id"], c["tipo_servicio"])
        grupos.setdefault(clave, []).append(c)
    return grupos


def generar_facturacion_eps(fecha_desde, fecha_hasta, modo, eps=None, usuario_id=None) -> dict:
    """
    Genera las facturas de las cuentas por cobrar pendientes en
    el rango de fechas indicado, agrupadas según el modo
    elegido. Cada factura generada queda con el detalle completo
    de qué se está cobrando (paciente, servicio, fecha, si era
    normal o adicional), y las cuentas por cobrar usadas quedan
    marcadas como "Facturado" para no volver a cobrarlas dos
    veces.
    """
    if modo not in ("por_eps", "por_paciente", "por_paciente_servicio"):
        raise ValueError("Modo de facturación no válido.")

    cuentas = listar_cuentas_pendientes(fecha_desde, fecha_hasta, eps)
    if not cuentas:
        return {"facturas_generadas": [], "mensaje": "No hay cuentas pendientes en ese rango de fechas."}

    grupos = _agrupar_cuentas(cuentas, modo)

    from services.facturacion_service import _generar_factura_desde_items

    facturas_generadas = []
    for clave, items in grupos.items():
        resultado = _generar_factura_desde_items(items, usuario_id)
        facturas_generadas.append(resultado)

        ids_cuentas = [str(item["id"]) for item in items]
        ejecutar(
            f"UPDATE cuentas_por_cobrar_eps SET estado='Facturado', factura_id=? WHERE id IN ({','.join(ids_cuentas)})",
            (resultado["factura_id"],),
        )

    return {"facturas_generadas": facturas_generadas, "total_facturas": len(facturas_generadas)}
