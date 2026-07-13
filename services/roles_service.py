"""
HomeCare Enterprise - Gestión de Roles y Permisos

Permite a un Administrador crear perfiles (roles) nuevos, y
activar/desactivar los módulos a los que cada uno tiene
acceso -- sin tener que tocar código. Reemplaza lo que antes
vivía fijo en core/permissions/permissions.py.
"""

from database.database import consultar_todos, consultar_uno, ejecutar

# Catálogo de todos los módulos que existen en el sistema, con
# un nombre amigable para mostrar en la pantalla de permisos.
# Si se agrega un módulo nuevo al sistema más adelante, debe
# añadirse aquí también para que aparezca como opción.
CATALOGO_MODULOS = [
    ("pacientes", "Pacientes"),
    ("programacion", "Programación / Agenda"),
    ("ordenes", "Órdenes Médicas"),
    ("medicamentos", "Medicamentos"),
    ("catalogos", "Catálogos"),
    ("profesionales", "Profesionales"),
    ("usuarios", "Usuarios y Configuración"),
    ("facturacion", "Facturación"),
    ("nomina", "Nómina"),
    ("cargos", "Cargos"),
    ("inventario", "Inventario de Insumos"),
    ("calidad", "Calidad"),
    ("interoperabilidad", "Interoperabilidad"),
    ("rips", "RIPS"),
    ("auditoria", "Auditoría"),
    ("reportes", "Reportes"),
    ("chatbot_whatsapp", "Chatbot de WhatsApp (configuración)"),
    ("agente_whatsapp", "Agente WhatsApp (panel de chat en vivo)"),
]


def listar_roles():
    filas = consultar_todos("SELECT * FROM roles WHERE activo=1 ORDER BY nombre")
    roles = []
    for fila in filas:
        rol = dict(fila)
        if rol["acceso_total"]:
            rol["permisos"] = ["*"]
        else:
            permisos = consultar_todos("SELECT modulo FROM roles_permisos WHERE rol_id=?", (rol["id"],))
            rol["permisos"] = [dict(p)["modulo"] for p in permisos]
        roles.append(rol)
    return roles


def obtener_rol(rol_id: int):
    fila = consultar_uno("SELECT * FROM roles WHERE id=?", (rol_id,))
    if not fila:
        return None
    rol = dict(fila)
    permisos = consultar_todos("SELECT modulo FROM roles_permisos WHERE rol_id=?", (rol_id,))
    rol["permisos"] = [dict(p)["modulo"] for p in permisos]
    return rol


def crear_rol(nombre: str, descripcion: str, acceso_total: bool, modulos: list) -> int:
    if not nombre or not nombre.strip():
        raise ValueError("Debe indicar el nombre del perfil.")

    existente = consultar_uno("SELECT id FROM roles WHERE nombre=?", (nombre.strip(),))
    if existente:
        raise ValueError(f"Ya existe un perfil llamado '{nombre}'.")

    rol_id = ejecutar(
        "INSERT INTO roles(nombre, descripcion, acceso_total, es_del_sistema) VALUES (?, ?, ?, 0)",
        (nombre.strip(), descripcion or "", 1 if acceso_total else 0),
    )

    if not acceso_total:
        for modulo in modulos:
            ejecutar("INSERT OR IGNORE INTO roles_permisos(rol_id, modulo) VALUES (?, ?)", (rol_id, modulo))

    _invalidar_cache()
    return rol_id


def actualizar_permisos_rol(rol_id: int, descripcion: str, acceso_total: bool, modulos: list):
    rol = obtener_rol(rol_id)
    if not rol:
        raise ValueError("El perfil no existe.")

    ejecutar(
        "UPDATE roles SET descripcion=?, acceso_total=? WHERE id=?",
        (descripcion or "", 1 if acceso_total else 0, rol_id),
    )

    ejecutar("DELETE FROM roles_permisos WHERE rol_id=?", (rol_id,))
    if not acceso_total:
        for modulo in modulos:
            ejecutar("INSERT OR IGNORE INTO roles_permisos(rol_id, modulo) VALUES (?, ?)", (rol_id, modulo))

    _invalidar_cache()


def desactivar_rol(rol_id: int):
    rol = obtener_rol(rol_id)
    if not rol:
        raise ValueError("El perfil no existe.")
    if rol["es_del_sistema"]:
        raise ValueError("Este es un perfil base del sistema y no se puede eliminar (pero sí puede cambiar sus permisos).")

    en_uso = consultar_uno("SELECT COUNT(*) AS total FROM usuarios WHERE rol=?", (rol["nombre"],))
    if en_uso and dict(en_uso)["total"] > 0:
        raise ValueError(f"No se puede eliminar: hay {dict(en_uso)['total']} usuario(s) con este perfil asignado.")

    ejecutar("UPDATE roles SET activo=0 WHERE id=?", (rol_id,))
    _invalidar_cache()


def _invalidar_cache():
    from core.permissions.permisos_dinamicos import invalidar_cache
    invalidar_cache()
