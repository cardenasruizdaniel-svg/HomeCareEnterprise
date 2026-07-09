"""
HomeCare Enterprise - Consentimientos Informados

Genera el texto del consentimiento informado de ingreso al
programa de atencion domiciliaria (texto propio de HomeCare
Enterprise, no una copia de ningun formato de terceros), lo
deja firmado digitalmente y disponible para imprimir.
"""

from datetime import datetime

from database.database import consultar_todos, consultar_uno, ejecutar

TIPOS_CONSENTIMIENTO = [
    "Ingreso al Programa de Atención Domiciliaria",
    "Consentimiento para Procedimiento Específico",
    "Autorización de Registro Fotográfico",
    "Autorización de Tratamiento de Datos Personales",
]


def generar_texto_ingreso_programa(paciente: dict, programa_nombre: str = "") -> str:
    """
    Texto propio de HomeCare Enterprise para el consentimiento
    de ingreso al programa de atención domiciliaria.
    """

    nombre_paciente = f"{paciente.get('primer_nombre','')} {paciente.get('primer_apellido','')}".strip()
    documento_paciente = f"{paciente.get('tipo_documento','')} {paciente.get('documento','')}".strip()
    programa_texto = f' al programa "{programa_nombre}"' if programa_nombre else ""

    return f"""CONSENTIMIENTO INFORMADO DE INGRESO AL PROGRAMA DE ATENCIÓN DOMICILIARIA

Paciente: {nombre_paciente} — Documento: {documento_paciente}
Fecha de diligenciamiento: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Yo, el paciente arriba identificado (o quien actúa en su representación como acudiente o \
responsable), declaro que he sido informado de manera clara y comprensible sobre las \
condiciones del servicio de atención domiciliaria que HomeCare Enterprise me brindará{programa_texto}, \
y manifiesto mi consentimiento libre e informado bajo las siguientes condiciones:

1. NATURALEZA DEL SERVICIO
El servicio consiste en la atención en salud (médica, de enfermería, terapias, cuidado, u \
otras según lo defina el equipo tratante) prestada en el domicilio del paciente, en las \
fechas y horarios previamente coordinados entre la IPS y el paciente o su familia.

2. RESPONSABILIDADES DEL PACIENTE Y SU FAMILIA
Nos comprometemos a: (a) garantizar que un cuidador o acompañante permanezca en el \
domicilio durante toda la atención; (b) informar oportunamente cualquier cambio de \
dirección, salida del domicilio, o traslado del paciente; (c) seguir las indicaciones, \
tratamientos y recomendaciones dadas por el equipo de salud; (d) mantener un ambiente \
adecuado y seguro para la atención; (e) mantener bajo cuidado cualquier mascota en un \
espacio separado durante la visita del profesional.

3. COPAGOS Y CUOTAS MODERADORAS
Entendemos que, cuando aplique según nuestro régimen de afiliación, deberemos cancelar \
los copagos o cuotas moderadoras correspondientes, conforme a la normatividad vigente del \
Sistema General de Seguridad Social en Salud.

4. REGISTRO FOTOGRÁFICO Y AUDIOVISUAL CON FINES CLÍNICOS
Autorizamos que se realicen registros fotográficos de los procedimientos y evolución del \
paciente, exclusivamente con fines de seguimiento clínico, historia clínica, y control de \
calidad de la atención. Estas imágenes hacen parte de la historia clínica y se manejan con \
la misma confidencialidad que el resto de la información médica.

5. TRATAMIENTO DE DATOS PERSONALES
De conformidad con la Ley 1581 de 2012 y sus decretos reglamentarios, autorizamos a \
HomeCare Enterprise para recolectar, almacenar y tratar nuestros datos personales y datos \
sensibles de salud, con la única finalidad de prestar el servicio de atención domiciliaria, \
realizar el reporte a las entidades de salud que correspondan (EPS, entes de control), y \
dar cumplimiento a las obligaciones legales aplicables al sector salud.

6. DERECHO A LA INFORMACIÓN Y REVOCATORIA
Entendemos que podemos solicitar en cualquier momento información adicional sobre nuestro \
estado de salud y el plan de tratamiento, así como revocar esta autorización, sin que ello \
afecte la atención de urgencia a la que tengamos derecho.

Declaro que he leído y comprendido este documento, que he tenido la oportunidad de resolver \
mis dudas con el personal de HomeCare Enterprise, y que firmo de manera libre y voluntaria \
en constancia de aceptación.
"""


def listar_por_paciente(paciente_id: int):
    return [dict(c) for c in consultar_todos(
        "SELECT * FROM consentimientos_informados WHERE paciente_id=? ORDER BY fecha_diligenciamiento DESC",
        (paciente_id,),
    )]


def obtener(consentimiento_id: int):
    return consultar_uno("SELECT * FROM consentimientos_informados WHERE id=?", (consentimiento_id,))


def crear_consentimiento(paciente_id: int, tipo: str, contenido_texto: str, usuario_id) -> int:

    if tipo not in TIPOS_CONSENTIMIENTO:
        raise ValueError(f"Tipo de consentimiento no válido. Use uno de: {', '.join(TIPOS_CONSENTIMIENTO)}")

    if not contenido_texto or not contenido_texto.strip():
        raise ValueError("El contenido del consentimiento no puede estar vacío.")

    return ejecutar(
        """
        INSERT INTO consentimientos_informados(paciente_id, tipo, contenido_texto, usuario_creacion)
        VALUES (?, ?, ?, ?)
        """,
        (paciente_id, tipo, contenido_texto, usuario_id),
    )


def firmar_consentimiento(consentimiento_id: int, firmante: str, nombre_firmante: str,
                            documento_firmante: str, parentesco_firmante: str, firma_base64: str):

    if not firma_base64:
        raise ValueError("Se requiere la firma digital para completar el consentimiento.")

    if firmante not in ("Paciente", "Acudiente/Responsable"):
        raise ValueError("Debe indicar quién firma.")

    ejecutar(
        """
        UPDATE consentimientos_informados
        SET firmante=?, nombre_firmante=?, documento_firmante=?, parentesco_firmante=?, firma_base64=?
        WHERE id=?
        """,
        (firmante, nombre_firmante, documento_firmante, parentesco_firmante, firma_base64, consentimiento_id),
    )
