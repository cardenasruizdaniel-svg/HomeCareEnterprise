"""
=========================================================
HomeCare Enterprise
Roles oficiales
Versión 7.1
=========================================================
"""

ADMIN = "Administrador"

DIRECTOR = "Director Médico"

COORDINADOR = "Coordinador"

MEDICO = "Médico"

ENFERMERO = "Enfermero"

FISIOTERAPEUTA = "Fisioterapeuta"

RESPIRATORIO = "Terapeuta Respiratorio"

CUIDADOR = "Cuidador"

PSICOLOGO = "Psicólogo"

SALUD_OCUPACIONAL = "Salud Ocupacional"

AUXILIAR = "Auxiliar"

TERAPEUTA = "Terapeuta"

NUTRICIONISTA = "Nutricionista"

ADMINISTRATIVO = "Administrativo"

AUDITOR = "Auditor"

FACTURACION = "Facturación"

INVENTARIO = "Inventario"

CONSULTA = "Consulta"


ROLES = [

    ADMIN,

    DIRECTOR,

    COORDINADOR,

    MEDICO,

    ENFERMERO,

    FISIOTERAPEUTA,

    RESPIRATORIO,

    CUIDADOR,

    PSICOLOGO,

    SALUD_OCUPACIONAL,

    TERAPEUTA,

    NUTRICIONISTA,

    ADMINISTRATIVO,

    AUXILIAR,

    AUDITOR,

    FACTURACION,

    INVENTARIO,

    CONSULTA,

]


def listar_roles_activos():
    """
    Lista de roles para mostrar en los desplegables (ej. al
    crear un Usuario/Profesional) -- se trae de la base de
    datos, para que los perfiles nuevos que un Administrador
    cree desde Roles y Permisos aparezcan aquí también, sin
    tener que tocar código. Si por algún motivo la base de
    datos no está disponible, se usa la lista fija de arriba
    como respaldo.
    """
    try:
        from database.database import consultar_todos
        filas = consultar_todos("SELECT nombre FROM roles WHERE activo=1 ORDER BY nombre")
        nombres = [dict(f)["nombre"] for f in filas]
        return nombres if nombres else ROLES
    except Exception:
        return ROLES
