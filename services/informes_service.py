"""
HomeCare Enterprise - Módulo de Informes

Reportes de los distintos aspectos del programa, pensados
para verse en pantalla, imprimirse, y descargarse en Excel --
inspirados en el formato de caracterización de pacientes
crónicos que ya maneja la IPS.
"""

from database.database import consultar_todos


def caracterizacion_pacientes(zona=None, tipo_cuidado=None) -> list:
    """
    Un renglón por paciente, con sus datos de identificación,
    ubicación/zona, aseguramiento, tipo de cuidado, el
    diagnóstico principal activo, el profesional asignado, y
    la fecha de su última nota registrada -- el reporte base
    de caracterización de pacientes.
    """

    condiciones = []
    parametros = []
    if zona:
        condiciones.append("p.zona_ciudad = ?")
        parametros.append(zona)
    if tipo_cuidado:
        condiciones.append("p.tipo_cuidado = ?")
        parametros.append(tipo_cuidado)

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    filas = consultar_todos(
        f"""
        SELECT p.id, p.tipo_documento, p.documento,
               p.primer_nombre || ' ' || COALESCE(p.segundo_nombre,'') || ' ' || p.primer_apellido
                 || ' ' || COALESCE(p.segundo_apellido,'') AS nombre_completo,
               p.fecha_nacimiento, p.sexo, p.eps, p.regimen, p.tipo_cuidado, p.zona_ciudad,
               p.municipio, p.departamento, p.direccion, p.barrio, p.celular, p.estado,
               p.fecha_registro,
               (SELECT dx.diagnostico || ' (' || dx.codigo_cie10 || ')'
                FROM diagnosticos dx WHERE dx.paciente_id=p.id AND dx.estado='Activo'
                ORDER BY dx.fecha_diagnostico DESC LIMIT 1) AS diagnostico_principal,
               (SELECT COUNT(*) FROM diagnosticos dx WHERE dx.paciente_id=p.id AND dx.estado='Activo') AS total_diagnosticos,
               (SELECT GROUP_CONCAT(DISTINCT sp.tipo_servicio) FROM servicios_paciente sp
                WHERE sp.paciente_id=p.id AND sp.estado='Activo') AS servicios_activos,
               (SELECT pr.nombre_completo FROM servicios_paciente sp
                JOIN profesionales pr ON pr.id = sp.profesional_id
                WHERE sp.paciente_id=p.id AND sp.estado='Activo' AND sp.profesional_id IS NOT NULL
                ORDER BY sp.id DESC LIMIT 1) AS profesional_principal,
               (SELECT MAX(e.fecha) FROM evoluciones e WHERE e.paciente_id=p.id AND e.tipo_registro='INFORME') AS fecha_ultima_nota
        FROM pacientes p
        {where}
        ORDER BY p.primer_apellido, p.primer_nombre
        """,
        tuple(parametros),
    )
    return [dict(f) for f in filas]


def resumen_por_zona() -> list:
    """Cantidad de pacientes por zona de la ciudad -- igual al reporte dinámico que ya manejan en Excel."""
    filas = consultar_todos(
        """
        SELECT COALESCE(NULLIF(zona_ciudad, ''), 'Sin zona asignada') AS zona,
               COUNT(*) AS total_pacientes,
               SUM(CASE WHEN tipo_cuidado='Ventilado' THEN 1 ELSE 0 END) AS ventilados
        FROM pacientes
        WHERE estado='ACTIVO'
        GROUP BY zona
        ORDER BY total_pacientes DESC
        """
    )
    return [dict(f) for f in filas]


def resumen_por_municipio() -> list:
    filas = consultar_todos(
        """
        SELECT COALESCE(NULLIF(municipio, ''), 'Sin municipio') AS municipio,
               COUNT(*) AS total_pacientes
        FROM pacientes
        WHERE estado='ACTIVO'
        GROUP BY municipio
        ORDER BY total_pacientes DESC
        """
    )
    return [dict(f) for f in filas]


def resumen_por_eps() -> list:
    filas = consultar_todos(
        """
        SELECT COALESCE(NULLIF(eps, ''), 'Sin EPS') AS eps, COUNT(*) AS total_pacientes
        FROM pacientes
        WHERE estado='ACTIVO'
        GROUP BY eps
        ORDER BY total_pacientes DESC
        """
    )
    return [dict(f) for f in filas]


def equipo_profesional() -> list:
    """Un renglón por profesional, con cuántos pacientes tiene asignados activos."""
    filas = consultar_todos(
        """
        SELECT pr.id, pr.documento, pr.nombre_completo, pr.especialidad_principal,
               pr.tipo_vinculacion, pr.estado, pr.celular, pr.correo,
               (SELECT COUNT(DISTINCT sp.paciente_id) FROM servicios_paciente sp
                WHERE sp.profesional_id=pr.id AND sp.estado='Activo') AS pacientes_asignados
        FROM profesionales pr
        ORDER BY pr.primer_apellido, pr.primer_nombre
        """
    )
    return [dict(f) for f in filas]
