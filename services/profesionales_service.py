"""
=========================================================
HomeCare Enterprise
Servicio: Profesionales (equipo interdisciplinario)

Envuelve ProfesionalesRepository con la logica minima de
negocio (generacion de nombre_completo/uuid, valores por
defecto) para que el router no dependa de detalles del
repositorio.
=========================================================
"""

import uuid as uuid_lib

from repositories.profesionales_repository import ProfesionalesRepository


def listar():
    return ProfesionalesRepository.listar()


def obtener(profesional_id: int):
    return ProfesionalesRepository.obtener(profesional_id)


def activos():
    return ProfesionalesRepository.activos()


def _nombre_completo(datos: dict) -> str:
    return " ".join(
        x for x in [
            datos.get("primer_nombre"),
            datos.get("segundo_nombre"),
            datos.get("primer_apellido"),
            datos.get("segundo_apellido"),
        ] if x
    )


def crear(datos: dict, usuario_id=None) -> int:

    datos = dict(datos)

    for campo in ("documento", "primer_nombre", "primer_apellido", "especialidad_principal"):
        if not datos.get(campo):
            raise ValueError(f"El campo '{campo}' es obligatorio para crear un profesional.")

    datos.setdefault("uuid", str(uuid_lib.uuid4()))
    datos.setdefault("tipo_documento", "CC")
    datos.setdefault("segundo_nombre", "")
    datos.setdefault("segundo_apellido", "")
    datos.setdefault("profesion", datos.get("especialidad_principal", ""))
    datos.setdefault("telefono", "")
    datos.setdefault("celular", "")
    datos.setdefault("correo", "")
    datos.setdefault("direccion", "")
    datos.setdefault("municipio", "")
    datos.setdefault("departamento", "")
    datos["nombre_completo"] = _nombre_completo(datos)
    datos.setdefault("estado", "ACTIVO")
    datos.setdefault("disponible", 1)
    datos.setdefault("acepta_urgencias", 0)
    datos.setdefault("capacidad_diaria", 20)
    datos.setdefault("tiempo_promedio_visita", 45)
    datos.setdefault("radio_cobertura_km", 10)
    datos.setdefault("latitud", None)
    datos.setdefault("longitud", None)
    datos.setdefault("observaciones", "")
    datos.setdefault("registro_profesional", "")
    datos.setdefault("tipo_contrato", "POR_HORAS")
    datos.setdefault("valor_hora", 0)
    datos.setdefault("salario_fijo", 0)
    datos.setdefault("banco", "")
    datos.setdefault("tipo_cuenta", "")
    datos.setdefault("numero_cuenta", "")
    datos.setdefault("usuario_id", None)
    datos.setdefault("firma_base64", None)
    datos.setdefault("foto_enrolamiento_base64", None)
    datos["usuario_creacion"] = usuario_id

    return ProfesionalesRepository.crear(datos)


def crear_con_cuenta_acceso(datos: dict, nombre_usuario, password, rol, usuario_creacion=None) -> dict:
    """
    Crea, en un solo paso, la cuenta de acceso (usuarios) Y la
    ficha del profesional, ya vinculadas entre si -- para no
    tener que pasar primero por "Usuarios" y luego por
    "Profesionales" por separado. Si no se indica usuario ni
    contraseña, se crea SOLO el profesional (sin cuenta de
    acceso), por si en algun caso no la necesita todavia.
    """

    nuevo_usuario_id = None

    if nombre_usuario and password:
        from repositories.usuarios_repository import UsuariosRepository
        if UsuariosRepository.obtener_por_usuario(nombre_usuario):
            raise ValueError(f"Ya existe un usuario con el nombre de acceso '{nombre_usuario}'.")

        from services.usuarios_service import crear_usuario
        nuevo_usuario_id = crear_usuario(
            datos.get("nombre_completo") or f"{datos.get('primer_nombre','')} {datos.get('primer_apellido','')}".strip(),
            nombre_usuario, password, rol or "Consulta",
            datos.get("correo", ""), datos.get("celular", "") or datos.get("telefono", ""),
        )

    datos = {**datos, "usuario_id": nuevo_usuario_id}
    profesional_id = crear(datos, usuario_creacion)

    return {"profesional_id": profesional_id, "usuario_id": nuevo_usuario_id}


def gestionar_cuenta_acceso(profesional_id, nombre_usuario, password, rol_sistema) -> int | None:
    """
    Se usa desde la pantalla de EDITAR profesional:
    - Si el profesional todavia no tiene cuenta y se indicaron
      usuario+contraseña, crea la cuenta nueva y la vincula.
    - Si el profesional YA tiene cuenta, actualiza su rol (si
      se indico uno) y su contraseña (solo si se escribio una
      nueva; si se deja en blanco, la contraseña actual no se toca).

    Devuelve el usuario_id vinculado (nuevo o existente), o None
    si no hay ninguna cuenta.
    """

    profesional = ProfesionalesRepository.obtener(profesional_id)
    profesional = dict(profesional) if profesional else {}
    usuario_id_actual = profesional.get("usuario_id")

    if not usuario_id_actual:
        if nombre_usuario and password:
            from repositories.usuarios_repository import UsuariosRepository
            if UsuariosRepository.obtener_por_usuario(nombre_usuario):
                raise ValueError(f"Ya existe un usuario con el nombre de acceso '{nombre_usuario}'.")

            from services.usuarios_service import crear_usuario
            return crear_usuario(
                profesional.get("nombre_completo", ""), nombre_usuario, password,
                rol_sistema or profesional.get("especialidad_principal", "Consulta"),
                profesional.get("correo", ""), profesional.get("celular", "") or profesional.get("telefono", ""),
            )
        return None

    # Ya tiene cuenta: solo se actualiza lo que se haya indicado.
    from database.database import ejecutar
    if rol_sistema:
        ejecutar("UPDATE usuarios SET rol=? WHERE id=?", (rol_sistema, usuario_id_actual))
    if password:
        from services.auth_service import AuthService
        ejecutar(
            "UPDATE usuarios SET password=? WHERE id=?",
            (AuthService.generar_hash(password), usuario_id_actual),
        )

    return usuario_id_actual


def actualizar(profesional_id: int, datos: dict, usuario_id=None):

    datos = dict(datos)

    if "latitud" not in datos or "longitud" not in datos:
        fila = ProfesionalesRepository.obtener(profesional_id)
        actual = dict(fila) if fila else {}
        datos.setdefault("latitud", actual.get("latitud"))
        datos.setdefault("longitud", actual.get("longitud"))

    if "usuario_id" not in datos:
        fila = ProfesionalesRepository.obtener(profesional_id)
        actual = dict(fila) if fila else {}
        datos["usuario_id"] = actual.get("usuario_id")

    datos["usuario_actualizacion"] = usuario_id

    return ProfesionalesRepository.actualizar(profesional_id, datos)


def actualizar_firma(profesional_id: int, firma_base64: str):
    if not firma_base64:
        raise ValueError("Debe capturar la firma antes de guardarla.")
    ProfesionalesRepository.actualizar_firma(profesional_id, firma_base64)


def cambiar_estado(profesional_id: int, estado: str):
    return ProfesionalesRepository.cambiar_estado(profesional_id, estado)


def eliminar(profesional_id: int):
    return ProfesionalesRepository.eliminar(profesional_id)
