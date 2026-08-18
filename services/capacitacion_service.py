"""
HomeCare Enterprise - Módulo de Capacitación

Un solo lugar, accesible desde la web y desde la app móvil,
donde queda todo el material de formación del personal: los
manuales de configuración, parametrización, funcionamiento y
operación (tanto web como móvil), y cualquier manual, video, o
tema nuevo que se necesite publicar más adelante.

Cada contenido se puede restringir a los perfiles (roles) que
correspondan -- por ejemplo, un manual de facturación no tiene
por qué verlo un cuidador, y un manual de la app móvil no tiene
por qué molestar a un administrativo que solo usa la web.
"""

from pathlib import Path

from database.database import consultar_todos, consultar_uno, ejecutar

TIPOS_CONTENIDO = ("Manual", "Video", "Documento", "Enlace")
CATEGORIAS = (
    "Configuración", "Parametrización", "Funcionamiento", "Operación",
    "App Móvil", "Facturación y Convenios", "Inventario", "Calidad y Normatividad", "Otro",
)
PLATAFORMAS = ("Web", "Móvil", "Ambas")


def listar_para_usuario(rol: str, plataforma: str = "Web"):
    """
    Todo el contenido activo que le corresponde ver a un usuario
    según su rol y desde dónde está entrando (web o móvil) --
    'Ambas' siempre se incluye sin importar la plataforma.
    """
    filas = consultar_todos(
        "SELECT * FROM capacitaciones WHERE activo=1 AND (plataforma=? OR plataforma='Ambas') ORDER BY categoria, orden, titulo",
        (plataforma,),
    )
    resultado = []
    for fila in filas:
        item = dict(fila)
        roles = [r.strip() for r in (item.get("roles_permitidos") or "Todos").split(",")]
        if "Todos" in roles or rol in roles:
            resultado.append(item)
    return resultado


def listar_todo(incluir_inactivos=True):
    sql = "SELECT * FROM capacitaciones"
    if not incluir_inactivos:
        sql += " WHERE activo=1"
    sql += " ORDER BY categoria, orden, titulo"
    return [dict(f) for f in consultar_todos(sql)]


def obtener(capacitacion_id: int):
    fila = consultar_uno("SELECT * FROM capacitaciones WHERE id=?", (capacitacion_id,))
    return dict(fila) if fila else None


def crear(titulo, descripcion, tipo, categoria, plataforma, roles_permitidos,
           archivo_path=None, url_externa=None, usuario_id=None, usuario_nombre=None, orden=0) -> int:
    if not titulo or not titulo.strip():
        raise ValueError("Debe indicar el título de la capacitación.")
    if tipo not in TIPOS_CONTENIDO:
        raise ValueError("Tipo de contenido no válido.")
    if not archivo_path and not url_externa:
        raise ValueError("Debe adjuntar un archivo o indicar un enlace (por ejemplo, de un video).")

    return ejecutar(
        """
        INSERT INTO capacitaciones(
            titulo, descripcion, tipo, categoria, plataforma, archivo_path, url_externa,
            roles_permitidos, orden, usuario_publico_id, usuario_publico_nombre
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (titulo.strip(), descripcion or "", tipo, categoria or "Otro", plataforma or "Web",
         archivo_path, url_externa, roles_permitidos or "Todos", orden or 0, usuario_id, usuario_nombre),
    )


def actualizar(capacitacion_id, titulo, descripcion, tipo, categoria, plataforma, roles_permitidos,
                archivo_path=None, url_externa=None, orden=0):
    if not titulo or not titulo.strip():
        raise ValueError("Debe indicar el título de la capacitación.")

    actual = obtener(capacitacion_id)
    if not actual:
        raise ValueError("La capacitación indicada no existe.")

    ejecutar(
        """
        UPDATE capacitaciones SET
            titulo=?, descripcion=?, tipo=?, categoria=?, plataforma=?, roles_permitidos=?, orden=?,
            archivo_path=COALESCE(?, archivo_path), url_externa=COALESCE(?, url_externa)
        WHERE id=?
        """,
        (titulo.strip(), descripcion or "", tipo, categoria or "Otro", plataforma or "Web",
         roles_permitidos or "Todos", orden or 0, archivo_path, url_externa, capacitacion_id),
    )


def desactivar(capacitacion_id: int):
    ejecutar("UPDATE capacitaciones SET activo=0 WHERE id=?", (capacitacion_id,))


def reactivar(capacitacion_id: int):
    ejecutar("UPDATE capacitaciones SET activo=1 WHERE id=?", (capacitacion_id,))


def eliminar(capacitacion_id: int):
    ejecutar("DELETE FROM capacitaciones WHERE id=?", (capacitacion_id,))


def listar_categorias_con_contenido(rol: str, plataforma: str = "Web"):
    """Agrupa el contenido visible para el usuario por categoría, para mostrarlo organizado."""
    items = listar_para_usuario(rol, plataforma)
    agrupado = {}
    for item in items:
        agrupado.setdefault(item["categoria"], []).append(item)
    return agrupado


def sembrar_manuales_existentes(usuario_id=None, usuario_nombre="Sistema"):
    """
    La primera vez que se activa el módulo, registra
    automáticamente los manuales que ya venían incluidos con el
    sistema (los que están en docs/manuales) -- así el módulo
    arranca completo desde el primer día, sin tener que volver a
    subir nada a mano.
    """
    ya_existe = consultar_uno("SELECT COUNT(*) AS total FROM capacitaciones")
    if ya_existe and dict(ya_existe)["total"] > 0:
        return []

    from core.config import RECURSOS_DIR
    carpeta_manuales = Path(RECURSOS_DIR) / "docs" / "manuales"

    manuales_iniciales = [
        ("MANUAL_INSTALACION.pdf", "Manual de Instalación", "Cómo instalar y poner en marcha el sistema.", "Configuración", "Web", "Administrador"),
        ("MANUAL_PARAMETRIZACION.pdf", "Manual de Parametrización", "Cómo configurar los catálogos, servicios, y parámetros generales del sistema.", "Parametrización", "Web", "Administrador,Coordinador"),
        ("MANUAL_FUNCIONAMIENTO.pdf", "Manual de Funcionamiento General", "Cómo opera el sistema en el día a día, módulo por módulo.", "Funcionamiento", "Web", "Todos"),
        ("MANUAL_CONFIGURACION_LEGAL.pdf", "Manual de Configuración Legal", "Configuración de los datos legales y normativos de la empresa.", "Configuración", "Web", "Administrador"),
        ("MANUAL_CONEXION_WHATSAPP.pdf", "Manual de Conexión de WhatsApp", "Cómo conectar y configurar el bot de WhatsApp.", "Configuración", "Web", "Administrador,Coordinador"),
        ("MANUAL_CONEXION_WHATSAPP_ILUSTRADO.pdf", "Manual de Conexión de WhatsApp (Ilustrado)", "Versión con capturas de pantalla, paso a paso.", "Configuración", "Web", "Administrador,Coordinador"),
        ("Manual_App_Movil_Android_iOS_HomeCare.pdf", "Manual de la App Móvil", "Cómo usar la aplicación móvil de campo -- para todo el personal asistencial.", "App Móvil", "Ambas", "Todos"),
        ("Manual_Convenios_EPS_Facturacion.docx", "Manual de Convenios EPS, Autorizaciones y Facturación", "Cómo parametrizar convenios, programas, autorizaciones, y generar la facturación.", "Facturación y Convenios", "Web", "Administrador,Coordinador,Administrativo"),
        ("Manual_Tramites_Entes_Reguladores_HomeCare.pdf", "Manual de Trámites ante Entes Reguladores", "Guía de los trámites y reportes obligatorios ante las entidades de vigilancia.", "Calidad y Normatividad", "Web", "Administrador,Coordinador"),
    ]

    creados = []
    for nombre_archivo, titulo, descripcion, categoria, plataforma, roles in manuales_iniciales:
        ruta_completa = carpeta_manuales / nombre_archivo
        if not ruta_completa.exists():
            continue
        capacitacion_id = crear(
            titulo=titulo, descripcion=descripcion, tipo="Manual", categoria=categoria, plataforma=plataforma,
            roles_permitidos=roles, archivo_path=f"docs/manuales/{nombre_archivo}",
            usuario_id=usuario_id, usuario_nombre=usuario_nombre,
        )
        creados.append(capacitacion_id)

    return creados
