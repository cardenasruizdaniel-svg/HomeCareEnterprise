"""
=========================================================
HomeCare Enterprise
Servicio: Ordenes Medicas

Cuando el medico genera una orden (medicamentos, examenes,
procedimientos), este servicio arma el PDF y lo envia
automaticamente al paciente por WhatsApp y correo
electronico, usando los datos de contacto que ya tiene
registrados -- adjuntando, junto con la orden, la historia
clinica del paciente.

Por seguridad, SOLO se envían automáticamente las órdenes de
tipo Medicamento, Procedimiento o Examen -- las de Remisión u
Otro tipo se pueden seguir creando con normalidad, pero no se
mandan solas al paciente (esas se gestionan de otra forma,
no como un envío directo).
=========================================================
"""

from database.database import consultar_uno

from core.config import PUBLIC_BASE_URL
from repositories.ordenes_repository import OrdenesRepository
from services.orden_pdf_service import generar_pdf_orden
from services.notificaciones_service import enviar_email, enviar_whatsapp

# Únicos tipos de orden que se envían automáticamente al
# paciente cuando el médico las guarda -- cualquier otro tipo
# se puede seguir registrando en el sistema, pero no dispara
# ningún envío.
TIPOS_ORDEN_CON_ENVIO_AUTOMATICO = ("Medicamento", "Procedimiento", "Examen")


class OrdenesService:

    # ------------------------------------------------------
    # LISTAR
    # ------------------------------------------------------

    @staticmethod
    def listar(historia_id: int):
        return OrdenesRepository.listar(historia_id)

    @staticmethod
    def listar_por_paciente(paciente_id: int):
        return OrdenesRepository.listar_por_paciente(paciente_id)

    @staticmethod
    def listar_por_rango_fechas(fecha_desde: str = None, fecha_hasta: str = None) -> list:
        """
        Para el Dashboard: todas las órdenes médicas generadas
        entre dos fechas -- si no se indican, se usa el día de
        hoy por defecto (para que siempre se vea, de entrada, lo
        que se generó hoy, sin tener que elegir nada).
        """
        from datetime import date
        hoy = date.today().isoformat()
        fecha_desde = fecha_desde or hoy
        fecha_hasta = fecha_hasta or hoy

        filas = OrdenesRepository.listar_por_rango_fechas(fecha_desde, fecha_hasta)
        resultado = []
        for fila in filas:
            f = dict(fila)
            f["paciente_nombre"] = f"{f.get('paciente_primer_nombre','')} {f.get('paciente_primer_apellido','')}".strip()
            f["profesional_nombre"] = (
                f"{f.get('profesional_primer_nombre','')} {f.get('profesional_primer_apellido','')}".strip()
                or "Sin asignar"
            )
            resultado.append(f)
        return resultado

    @staticmethod
    def obtener(orden_id: int):
        return OrdenesRepository.obtener(orden_id)

    @staticmethod
    def listar_por_rango_fecha(fecha_desde: str, fecha_hasta: str):
        """
        Todas las órdenes generadas en el rango de fechas dado
        (incluyendo ambos extremos), con el nombre del paciente
        y del profesional que la generó ya resueltos -- para
        mostrarlas en el Dashboard.
        """
        from database.database import consultar_todos
        filas = consultar_todos(
            """
            SELECT om.id, om.tipo, om.descripcion, om.estado, om.fecha_orden,
                   om.enviado_whatsapp, om.enviado_correo,
                   p.primer_nombre AS paciente_nombre, p.primer_apellido AS paciente_apellido, p.documento AS paciente_documento,
                   pr.primer_nombre AS profesional_nombre, pr.primer_apellido AS profesional_apellido
            FROM ordenes_medicas om
            JOIN pacientes p ON p.id = om.paciente_id
            LEFT JOIN profesionales pr ON pr.id = om.profesional_id
            WHERE date(om.fecha_orden) >= date(?) AND date(om.fecha_orden) <= date(?)
            ORDER BY om.fecha_orden DESC
            """,
            (fecha_desde, fecha_hasta),
        )
        return [dict(f) for f in filas]

    # ------------------------------------------------------
    # CREAR + ENVIAR AUTOMATICAMENTE
    # ------------------------------------------------------

    @staticmethod
    def crear_y_enviar(
        paciente_id: int,
        profesional_id: int,
        tipo: str,
        descripcion: str,
        codigo_cups: str = "",
        historia_id: int = None,
        usuario_creacion: int = None,
    ) -> dict:

        if not descripcion or not descripcion.strip():
            raise ValueError("Debe describir la orden médica.")

        if tipo not in ("Medicamento", "Examen", "Remisión", "Procedimiento", "Otro"):
            raise ValueError("Tipo de orden no válido.")

        orden_id = OrdenesRepository.crear({
            "historia_id": historia_id,
            "paciente_id": paciente_id,
            "profesional_id": profesional_id,
            "tipo": tipo,
            "descripcion": descripcion,
            "codigo_cups": codigo_cups,
            "estado": "Generada",
            "usuario_creacion": usuario_creacion,
        })

        orden = dict(OrdenesRepository.obtener(orden_id))

        resultado = {
            "orden_id": orden_id,
            "pdf": None,
            "correo": {"enviado": False},
            "whatsapp": {"enviado": False},
        }

        # Solo se envía automáticamente si el tipo de orden está
        # autorizado para eso -- las demás quedan registradas,
        # pero sin disparar ningún mensaje al paciente.
        if tipo not in TIPOS_ORDEN_CON_ENVIO_AUTOMATICO:
            resultado["correo"] = {"enviado": False, "motivo": f"Las órdenes de tipo '{tipo}' no se envían automáticamente."}
            resultado["whatsapp"] = {"enviado": False, "motivo": f"Las órdenes de tipo '{tipo}' no se envían automáticamente."}
            return resultado

        paciente = consultar_uno(
            "SELECT * FROM pacientes WHERE id=?", (paciente_id,)
        )
        paciente = dict(paciente) if paciente else {}

        profesional = consultar_uno(
            "SELECT * FROM profesionales WHERE id=?", (profesional_id,)
        ) if profesional_id else None
        profesional = dict(profesional) if profesional else None

        # -----------------------------
        # GENERAR PDF DE LA ORDEN
        # -----------------------------

        try:
            ruta_pdf = generar_pdf_orden(orden, paciente, profesional)
            resultado["pdf"] = ruta_pdf
        except Exception as error:
            ruta_pdf = None
            resultado["pdf_error"] = str(error)

        # -----------------------------
        # GENERAR PDF DE LA HISTORIA CLÍNICA (se manda junto con la orden)
        # -----------------------------

        ruta_historia_clinica = None
        try:
            from services.whatsapp_documentos_seguros_service import generar_pdf_historia_clinica
            ruta_historia_clinica = generar_pdf_historia_clinica(paciente_id)
        except Exception as error:
            resultado["historia_clinica_error"] = str(error)

        nombre_paciente = paciente.get("nombre_completo") or " ".join(
            x for x in [paciente.get("primer_nombre"), paciente.get("primer_apellido")] if x
        )

        mensaje_texto = (
            f"Hola {nombre_paciente}, HomeCare IPS le informa que se generó una "
            f"nueva orden médica de tipo *{tipo}*.\n\n"
            f"{descripcion}\n\n"
            f"Adjunto también le compartimos su historia clínica actualizada.\n\n"
            f"Si tiene dudas, comuníquese con su equipo de atención."
        )

        # -----------------------------
        # ENVIAR CORREO (orden + historia clínica, en el mismo correo)
        # -----------------------------

        correo_paciente = paciente.get("correo")

        if correo_paciente:
            resultado["correo"] = enviar_email(
                destinatario=correo_paciente,
                asunto=f"HomeCare IPS - Nueva orden médica ({tipo})",
                cuerpo_html=(
                    f"<p>Hola {nombre_paciente},</p>"
                    f"<p>Se generó una nueva orden médica de tipo <b>{tipo}</b>:</p>"
                    f"<p>{descripcion}</p>"
                    f"<p>Adjuntamos el documento de la orden médica, junto con su historia clínica actualizada.</p>"
                    f"<p style='color:#888;font-size:12px'>HomeCare IPS - "
                    f"Mensaje generado automáticamente.</p>"
                ),
                adjunto_path=ruta_pdf,
                adjuntos_adicionales=[ruta_historia_clinica] if ruta_historia_clinica else None,
            )
        else:
            resultado["correo"] = {"enviado": False, "motivo": "Paciente sin correo registrado."}

        # -----------------------------
        # ENVIAR WHATSAPP (la orden, y aparte la historia clínica --
        # WhatsApp solo permite UN documento adjunto por mensaje)
        # -----------------------------

        celular_paciente = paciente.get("celular") or paciente.get("telefono")

        adjunto_url = None
        if ruta_pdf and PUBLIC_BASE_URL:
            token = orden.get("token_pdf", "")
            adjunto_url = f"{PUBLIC_BASE_URL.rstrip('/')}/ordenes-medicas/pdf-publico/{orden_id}/{token}"

        if celular_paciente:
            resultado["whatsapp"] = enviar_whatsapp(
                numero=celular_paciente,
                mensaje=mensaje_texto,
                adjunto_url=adjunto_url,
            )

            # Segundo mensaje, con la historia clínica adjunta -- se
            # genera un enlace seguro propio (de un solo documento,
            # con vencimiento), igual que el que usa el bot del chat.
            if ruta_historia_clinica and PUBLIC_BASE_URL:
                try:
                    from services.whatsapp_documentos_seguros_service import generar_token_documento
                    token_historia = generar_token_documento(paciente_id, "historia_clinica")
                    url_historia = f"{PUBLIC_BASE_URL.rstrip('/')}/documentos-seguros/{token_historia}"
                    resultado["whatsapp_historia_clinica"] = enviar_whatsapp(
                        numero=celular_paciente,
                        mensaje="📋 Aquí tiene su historia clínica actualizada.",
                        adjunto_url=url_historia,
                    )
                except Exception as error:
                    resultado["whatsapp_historia_clinica"] = {"enviado": False, "motivo": str(error)}
        else:
            resultado["whatsapp"] = {"enviado": False, "motivo": "Paciente sin celular registrado."}

        # -----------------------------
        # REGISTRAR ENVÍOS
        # -----------------------------

        OrdenesRepository.marcar_envio(
            orden_id,
            whatsapp=resultado["whatsapp"].get("enviado", False),
            correo=resultado["correo"].get("enviado", False),
        )

        return resultado

    # ------------------------------------------------------
    # REENVIAR MANUALMENTE (misma orden, no crea una nueva)
    # ------------------------------------------------------

    @staticmethod
    def reenviar(orden_id: int) -> dict:

        orden = OrdenesRepository.obtener(orden_id)

        if not orden:
            raise ValueError("La orden no existe.")

        orden = dict(orden)

        paciente = consultar_uno(
            "SELECT * FROM pacientes WHERE id=?", (orden["paciente_id"],)
        )
        paciente = dict(paciente) if paciente else {}

        profesional = consultar_uno(
            "SELECT * FROM profesionales WHERE id=?", (orden["profesional_id"],)
        ) if orden.get("profesional_id") else None
        profesional = dict(profesional) if profesional else None

        resultado = {"orden_id": orden_id, "pdf": None, "correo": {"enviado": False}, "whatsapp": {"enviado": False}}

        try:
            ruta_pdf = generar_pdf_orden(orden, paciente, profesional)
            resultado["pdf"] = ruta_pdf
        except Exception as error:
            ruta_pdf = None
            resultado["pdf_error"] = str(error)

        ruta_historia_clinica = None
        try:
            from services.whatsapp_documentos_seguros_service import generar_pdf_historia_clinica
            ruta_historia_clinica = generar_pdf_historia_clinica(orden["paciente_id"])
        except Exception as error:
            resultado["historia_clinica_error"] = str(error)

        nombre_paciente = paciente.get("nombre_completo") or " ".join(
            x for x in [paciente.get("primer_nombre"), paciente.get("primer_apellido")] if x
        )

        mensaje_texto = (
            f"Hola {nombre_paciente}, HomeCare IPS le reenvía la orden médica "
            f"de tipo *{orden['tipo']}*.\n\n{orden['descripcion']}\n\n"
            f"Adjunto también le compartimos su historia clínica actualizada."
        )

        correo_paciente = paciente.get("correo")
        if correo_paciente:
            resultado["correo"] = enviar_email(
                destinatario=correo_paciente,
                asunto=f"HomeCare IPS - Reenvío orden médica ({orden['tipo']})",
                cuerpo_html=f"<p>{mensaje_texto}</p>",
                adjunto_path=ruta_pdf,
                adjuntos_adicionales=[ruta_historia_clinica] if ruta_historia_clinica else None,
            )
        else:
            resultado["correo"] = {"enviado": False, "motivo": "Paciente sin correo registrado."}

        celular_paciente = paciente.get("celular") or paciente.get("telefono")
        adjunto_url = None
        if ruta_pdf and PUBLIC_BASE_URL:
            token = orden.get("token_pdf", "")
            adjunto_url = f"{PUBLIC_BASE_URL.rstrip('/')}/ordenes-medicas/pdf-publico/{orden_id}/{token}"

        if celular_paciente:
            resultado["whatsapp"] = enviar_whatsapp(
                numero=celular_paciente, mensaje=mensaje_texto, adjunto_url=adjunto_url,
            )
            if ruta_historia_clinica and PUBLIC_BASE_URL:
                try:
                    from services.whatsapp_documentos_seguros_service import generar_token_documento
                    token_historia = generar_token_documento(orden["paciente_id"], "historia_clinica")
                    url_historia = f"{PUBLIC_BASE_URL.rstrip('/')}/documentos-seguros/{token_historia}"
                    resultado["whatsapp_historia_clinica"] = enviar_whatsapp(
                        numero=celular_paciente,
                        mensaje="📋 Aquí tiene su historia clínica actualizada.",
                        adjunto_url=url_historia,
                    )
                except Exception as error:
                    resultado["whatsapp_historia_clinica"] = {"enviado": False, "motivo": str(error)}
        else:
            resultado["whatsapp"] = {"enviado": False, "motivo": "Paciente sin celular registrado."}

        OrdenesRepository.marcar_envio(
            orden_id,
            whatsapp=resultado["whatsapp"].get("enviado", False),
            correo=resultado["correo"].get("enviado", False),
        )

        return resultado
