"""
HomeCare Enterprise - Configuración del Portal Web Público

Contenido administrable del sitio público: textos del Inicio
(hero), historia/misión/visión, datos de contacto, redes
sociales, y el listado de servicios que se muestran -- todo
editable desde el sistema, sin tocar código.
"""

from database.database import consultar_todos, consultar_uno, ejecutar

VALORES_POR_DEFECTO = {
    "hero_titulo": "Bienestar en casa",
    "hero_subtitulo": "Servicios médicos domiciliarios. Especialistas en infancia y tercera edad.",
    "historia": "Home Care del Quindío nace de la experiencia de dos padres de familia quindianos que han padecido las dificultades de acceso a servicios domiciliarios de salud eficientes y de calidad. A raíz de esta experiencia tenemos la convicción de transformar los servicios domiciliarios en salud en la mejor opción de recuperación y prevención de enfermedades, ofreciendo siempre calidad y oportunidad en el servicio.",
    "mision": "", "vision": "",
    "valores": "Somos una I.P.S. que brinda una amplia gama de servicios con un grupo de profesionales de la salud altamente calificados y comprometidos con el aprendizaje continuo, prestando servicios de salud a nuestros usuarios con calidad, responsabilidad, humanidad y respeto.",
    "telefono": "+57 323 479 0311", "whatsapp": "323 479 0311", "correo": "quindiohomecare@gmail.com",
    "direccion": "Carrera 13 #3N 50, Medicentro Alcázar cons 706, Armenia, Quindío", "horarios": "",
    "facebook": "https://www.facebook.com/homecaredelquindio", "instagram": "https://www.instagram.com/homecaredelquindio",
    "tiktok": "", "youtube": "", "linkedin": "",
    "nit": "901.540.816-8", "enlace_pagos": "",
    "hero_imagen": "", "experiencia_imagen": "",
}

ICONOS_DISPONIBLES = (
    "fa-solid fa-house-medical", "fa-solid fa-user-nurse", "fa-solid fa-syringe",
    "fa-solid fa-hand-holding-medical", "fa-solid fa-vial", "fa-solid fa-band-aid",
    "fa-solid fa-heart-pulse", "fa-solid fa-kit-medical", "fa-solid fa-stethoscope",
)


def obtener_configuracion() -> dict:
    fila = consultar_uno("SELECT * FROM configuracion_web WHERE id=1")
    config = dict(fila) if fila else {**VALORES_POR_DEFECTO, "id": 1}

    # El campo "whatsapp" se captura como el usuario lo escriba
    # (con espacios, guiones, +57, etc.) -- para el enlace
    # "wa.me" hace falta solo los dígitos, calculado una sola vez
    # aquí para que todo el sitio público lo use igual.
    digitos = "".join(c for c in (config.get("whatsapp") or "") if c.isdigit())
    if digitos and not digitos.startswith("57") and len(digitos) == 10:
        digitos = f"57{digitos}"  # Colombia -- si no trae indicativo, se lo agrega
    config["whatsapp_link"] = digitos

    return config


def guardar_configuracion(datos: dict, usuario_id=None):
    existente = consultar_uno("SELECT id FROM configuracion_web WHERE id=1")

    campos = {clave: datos.get(clave, "") for clave in VALORES_POR_DEFECTO}

    if existente:
        ejecutar(
            f"""
            UPDATE configuracion_web SET
                {', '.join(f'{c}=?' for c in campos)},
                fecha_actualizacion=CURRENT_TIMESTAMP, usuario_actualizacion=?
            WHERE id=1
            """,
            (*campos.values(), usuario_id),
        )
    else:
        columnas = list(campos.keys())
        ejecutar(
            f"INSERT INTO configuracion_web(id, {', '.join(columnas)}, usuario_actualizacion) VALUES (1, {', '.join(['?'] * len(columnas))}, ?)",
            (*campos.values(), usuario_id),
        )


EXTENSIONES_IMAGEN_PERMITIDAS = (".jpg", ".jpeg", ".png", ".webp")
TAMANO_MAXIMO_IMAGEN_MB = 8


def guardar_imagen_portal(campo: str, nombre_archivo: str, contenido: bytes) -> str:
    """
    Guarda una imagen que el administrador sube desde el panel
    (para el Hero o la sección de Experiencia Humana) en la
    carpeta pública /static, y actualiza el campo
    correspondiente en configuracion_web.

    campo debe ser 'hero_imagen' o 'experiencia_imagen' -- son
    las únicas dos columnas de imagen que existen hoy.
    """
    from pathlib import Path
    import re, time
    from core.config import STATIC_DIR

    if campo not in ("hero_imagen", "experiencia_imagen"):
        raise ValueError("Campo de imagen no válido.")

    extension = Path(nombre_archivo).suffix.lower()
    if extension not in EXTENSIONES_IMAGEN_PERMITIDAS:
        raise ValueError(f"Formato no permitido. Use uno de: {', '.join(EXTENSIONES_IMAGEN_PERMITIDAS)}")

    if len(contenido) > TAMANO_MAXIMO_IMAGEN_MB * 1024 * 1024:
        raise ValueError(f"La imagen no puede pesar más de {TAMANO_MAXIMO_IMAGEN_MB} MB.")

    carpeta = Path(STATIC_DIR) / "img" / "portal"
    carpeta.mkdir(parents=True, exist_ok=True)

    nombre_limpio = re.sub(r"[^A-Za-z0-9_.-]", "_", Path(nombre_archivo).stem)
    nombre_final = f"{campo}_{int(time.time())}_{nombre_limpio}{extension}"
    with open(carpeta / nombre_final, "wb") as f:
        f.write(contenido)

    url_publica = f"/static/img/portal/{nombre_final}"
    actual = obtener_configuracion()
    datos_finales = {c: actual.get(c, "") for c in VALORES_POR_DEFECTO if c != "id"}
    datos_finales[campo] = url_publica
    guardar_configuracion(datos_finales)

    return url_publica


def completar_con_datos_reales_si_vacio(usuario_id=None) -> list:
    """
    Completa SOLO los campos de configuracion_web que sigan
    vacíos, con la información real del sitio actual de
    HomeCare del Quindío (teléfono, correo, historia de
    fundación, NIT, redes sociales, etc.) -- nunca sobrescribe
    un campo que ya haya sido personalizado manualmente desde
    el panel, sin importar cuántas veces se corra esto.
    """
    actual = obtener_configuracion()
    campos_completados = []

    campos_a_completar = {}
    for clave, valor_real in VALORES_POR_DEFECTO.items():
        if clave == "id":
            continue
        valor_actual = (actual.get(clave) or "").strip()
        if not valor_actual and valor_real:
            campos_a_completar[clave] = valor_real
            campos_completados.append(clave)

    if not campos_a_completar:
        return []

    # Se guarda partiendo de TODO lo que ya existe (para no
    # perder ningún campo ya personalizado), solo reemplazando
    # los que estaban vacíos.
    datos_finales = {clave: actual.get(clave, "") for clave in VALORES_POR_DEFECTO if clave != "id"}
    datos_finales.update(campos_a_completar)
    guardar_configuracion(datos_finales, usuario_id=usuario_id)

    return campos_completados


def listar_servicios(solo_activos=False):
    sql = "SELECT * FROM servicios_web"
    if solo_activos:
        sql += " WHERE activo=1"
    sql += " ORDER BY orden, nombre"
    return [dict(f) for f in consultar_todos(sql)]


def obtener_servicio(servicio_id: int):
    fila = consultar_uno("SELECT * FROM servicios_web WHERE id=?", (servicio_id,))
    return dict(fila) if fila else None


def crear_servicio(datos: dict, usuario_id=None) -> int:
    if not datos.get("nombre"):
        raise ValueError("Debe indicar el nombre del servicio.")
    return ejecutar(
        "INSERT INTO servicios_web(nombre, descripcion, icono, orden, usuario_creacion) VALUES (?, ?, ?, ?, ?)",
        (datos["nombre"], datos.get("descripcion", ""), datos.get("icono") or ICONOS_DISPONIBLES[0], int(datos.get("orden") or 0), usuario_id),
    )


def actualizar_servicio(servicio_id: int, datos: dict):
    if not datos.get("nombre"):
        raise ValueError("Debe indicar el nombre del servicio.")
    ejecutar(
        "UPDATE servicios_web SET nombre=?, descripcion=?, icono=?, orden=? WHERE id=?",
        (datos["nombre"], datos.get("descripcion", ""), datos.get("icono") or ICONOS_DISPONIBLES[0], int(datos.get("orden") or 0), servicio_id),
    )


def desactivar_servicio(servicio_id: int):
    ejecutar("UPDATE servicios_web SET activo=0 WHERE id=?", (servicio_id,))


def reactivar_servicio(servicio_id: int):
    ejecutar("UPDATE servicios_web SET activo=1 WHERE id=?", (servicio_id,))


def sembrar_servicios_estandar(usuario_id=None) -> list:
    """Servicios típicos de una IPS de atención domiciliaria, para que el portal no arranque vacío."""
    ya_existe = consultar_uno("SELECT COUNT(*) AS total FROM servicios_web")
    if ya_existe and dict(ya_existe)["total"] > 0:
        return []

    servicios_iniciales = [
        ("Medicina General", "Consulta médica a domicilio, valoración y seguimiento.", "fa-solid fa-stethoscope"),
        ("Enfermería", "Cuidados de enfermería, aplicación de medicamentos y procedimientos.", "fa-solid fa-user-nurse"),
        ("Terapias", "Terapia física, respiratoria y del lenguaje en casa.", "fa-solid fa-hand-holding-medical"),
        ("Toma de Muestras", "Recolección de muestras de laboratorio a domicilio.", "fa-solid fa-vial"),
        ("Clínica de Heridas", "Manejo y curación especializada de heridas.", "fa-solid fa-band-aid"),
        ("Hospitalización Domiciliaria", "Atención hospitalaria completa en el hogar del paciente.", "fa-solid fa-house-medical"),
    ]

    creados = []
    for indice, (nombre, descripcion, icono) in enumerate(servicios_iniciales):
        servicio_id = crear_servicio({"nombre": nombre, "descripcion": descripcion, "icono": icono, "orden": indice}, usuario_id=usuario_id)
        creados.append(servicio_id)
    return creados


def actualizar_servicios_con_catalogo_real(usuario_id=None) -> dict:
    """
    Ajusta el listado de servicios para que coincida con el
    catálogo real y completo de HomeCare del Quindío (15
    servicios específicos, en vez de las 6 categorías genéricas
    con las que arrancó el módulo por defecto).

    No es destructivo: las categorías genéricas que ya no
    reflejan la realidad ("Terapias", "Hospitalización
    Domiciliaria") se OCULTAN (desactivar_servicio), no se
    borran -- y solo se agregan los servicios reales que
    todavía no existan (por nombre exacto), para no duplicar
    nada si esto se corre más de una vez.
    """
    genericos_a_ocultar = ["Terapias", "Hospitalización Domiciliaria"]
    servicios_reales = [
        ("Hospitalización Pediátrica", "La pediatría es la rama de la medicina que estudia al niño y el adolescente, sus enfermedades y comportamientos.", "fa-solid fa-baby", 1),
        ("Hospitalización Paciente Crónico con Ventilador", "Busca mejorar la calidad de vida de los pacientes y de sus familiares.", "fa-solid fa-lungs", 2),
        ("Hospitalización Paciente Agudo y Crónico sin Ventilador", "Extensión hospitalaria y/o ambulatoria con manejo integral del paciente de baja complejidad.", "fa-solid fa-bed-pulse", 3),
        ("Terapia Respiratoria", "Atención especializada en la comodidad del hogar del paciente.", "fa-solid fa-lungs-virus", 6),
        ("Terapia Ocupacional", "Aborda desafíos físicos, cognitivos, emocionales y sociales, para todas las edades.", "fa-solid fa-hands-holding-child", 7),
        ("Fisioterapia", "Atención integral que facilita la recuperación y la mejora de la función física.", "fa-solid fa-person-walking", 8),
        ("Fonoaudiología y Terapia del Lenguaje", "Atención especializada para dificultades del habla, lenguaje, auditivas y de deglución.", "fa-solid fa-comment-medical", 9),
        ("Nutrición y Dietética", "Promoción de hábitos alimenticios saludables y gestión de condiciones relacionadas con la nutrición.", "fa-solid fa-apple-whole", 10),
        ("Psicología", "Sesiones terapéuticas individualizadas y estrategias de manejo del estrés.", "fa-solid fa-brain", 11),
        ("Licenciadas en Pedagogía Infantil", "Enfoque educativo que se adapta a las necesidades individuales y al entorno familiar del niño.", "fa-solid fa-child-reaching", 13),
        ("Cuidadoras", "Asistencia y cuidados personalizados para quien necesita atención especial en casa.", "fa-solid fa-hands-holding-circle", 14),
    ]

    ocultados = []
    for nombre in genericos_a_ocultar:
        fila = consultar_uno("SELECT id, activo FROM servicios_web WHERE nombre=?", (nombre,))
        if fila and dict(fila)["activo"]:
            desactivar_servicio(dict(fila)["id"])
            ocultados.append(nombre)

    creados = []
    for nombre, descripcion, icono, orden in servicios_reales:
        ya_existe = consultar_uno("SELECT id FROM servicios_web WHERE nombre=?", (nombre,))
        if ya_existe:
            continue
        servicio_id = crear_servicio({"nombre": nombre, "descripcion": descripcion, "icono": icono, "orden": orden}, usuario_id=usuario_id)
        creados.append(nombre)

    return {"ocultados": ocultados, "creados": creados}
