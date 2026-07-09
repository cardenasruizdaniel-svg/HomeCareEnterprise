"""
=========================================================
HomeCare Enterprise
Servicio: Ordenes Medicas

Cuando el medico genera una orden (medicamentos, examenes),
este servicio arma el PDF y lo envia automaticamente al
paciente por WhatsApp y correo electronico, usando los
datos de contacto que ya tiene registrados.
=========================================================
"""

from database.database import consultar_uno

from core.config import PUBLIC_BASE_URL
from repositories.ordenes_repository import OrdenesRepository
from services.orden_pdf_service import generar_pdf_orden
from services.notificaciones_service import enviar_email, enviar_whatsapp


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
    def obtener(orden_id: int):
        return OrdenesRepository.obtener(orden_id)

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

        paciente = consultar_uno(
            "SELECT * FROM pacientes WHERE id=?", (paciente_id,)
        )
        paciente = dict(paciente) if paciente else {}

        profesional = consultar_uno(
            "SELECT * FROM profesionales WHERE id=?", (profesional_id,)
        ) if profesional_id else None
        profesional = dict(profesional) if profesional else None

        resultado = {
            "orden_id": orden_id,
            "pdf": None,
            "correo": {"enviado": False},
            "whatsapp": {"enviado": False},
        }

        # -----------------------------
        # GENERAR PDF
        # -----------------------------

        try:
            ruta_pdf = generar_pdf_orden(orden, paciente, profesional)
            resultado["pdf"] = ruta_pdf
        except Exception as error:
            ruta_pdf = None
            resultado["pdf_error"] = str(error)

        nombre_paciente = paciente.get("nombre_completo") or " ".join(
            x for x in [paciente.get("primer_nombre"), paciente.get("primer_apellido")] if x
        )

        mensaje_texto = (
            f"Hola {nombre_paciente}, HomeCare IPS le informa que se generó una "
            f"nueva orden médica de tipo *{tipo}*.\n\n"
            f"{descripcion}\n\n"
            f"Si tiene dudas, comuníquese con su equipo de atención."
        )

        # -----------------------------
        # ENVIAR CORREO
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
                    f"<p>Adjuntamos el documento en PDF.</p>"
                    f"<p style='color:#888;font-size:12px'>HomeCare IPS - "
                    f"Mensaje generado automáticamente.</p>"
                ),
                adjunto_path=ruta_pdf,
            )
        else:
            resultado["correo"] = {"enviado": False, "motivo": "Paciente sin correo registrado."}

        # -----------------------------
        # ENVIAR WHATSAPP
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

        nombre_paciente = paciente.get("nombre_completo") or " ".join(
            x for x in [paciente.get("primer_nombre"), paciente.get("primer_apellido")] if x
        )

        mensaje_texto = (
            f"Hola {nombre_paciente}, HomeCare IPS le reenvía la orden médica "
            f"de tipo *{orden['tipo']}*.\n\n{orden['descripcion']}"
        )

        correo_paciente = paciente.get("correo")
        if correo_paciente:
            resultado["correo"] = enviar_email(
                destinatario=correo_paciente,
                asunto=f"HomeCare IPS - Reenvío orden médica ({orden['tipo']})",
                cuerpo_html=f"<p>{mensaje_texto}</p>",
                adjunto_path=ruta_pdf,
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
        else:
            resultado["whatsapp"] = {"enviado": False, "motivo": "Paciente sin celular registrado."}

        OrdenesRepository.marcar_envio(
            orden_id,
            whatsapp=resultado["whatsapp"].get("enviado", False),
            correo=resultado["correo"].get("enviado", False),
        )

        return resultado
