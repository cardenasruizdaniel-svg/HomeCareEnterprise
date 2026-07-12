"""
HomeCare Enterprise - Permisos dinámicos (leídos de la base de datos)

Guarda en memoria un mapa {rol: set(modulos)} para no tener
que consultar la base de datos en cada clic -- se recarga
solo (con el decorador de cache simple de aquí abajo) cuando
un administrador guarda cambios en Configuración de Roles y
Permisos.
"""

_cache_permisos = None


def _cargar_desde_bd():
    from database.database import consultar_todos

    mapa = {}
    roles = consultar_todos("SELECT id, nombre, acceso_total FROM roles WHERE activo=1")
    for rol in roles:
        rol = dict(rol)
        if rol["acceso_total"]:
            mapa[rol["nombre"]] = {"*"}
        else:
            permisos = consultar_todos("SELECT modulo FROM roles_permisos WHERE rol_id=?", (rol["id"],))
            mapa[rol["nombre"]] = {dict(p)["modulo"] for p in permisos}
    return mapa


def invalidar_cache():
    """Se llama después de guardar cambios en Configuración de Roles y Permisos."""
    global _cache_permisos
    _cache_permisos = None


def tiene_permiso_bd(rol: str, modulo: str) -> bool:
    global _cache_permisos
    if _cache_permisos is None:
        _cache_permisos = _cargar_desde_bd()

    permisos_rol = _cache_permisos.get(rol)
    if permisos_rol is None:
        raise KeyError(f"Rol '{rol}' no encontrado en la base de datos")  # dispara el respaldo del diccionario fijo

    return "*" in permisos_rol or modulo in permisos_rol
