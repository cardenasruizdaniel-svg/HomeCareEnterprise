import bcrypt

from repositories.usuarios_repository import UsuariosRepository

MAXIMO_INTENTOS_FALLIDOS = 5
MINUTOS_BLOQUEO = 15


class AuthService:

    @staticmethod
    def autenticar(usuario: str, password: str):
        """
        Además de validar la contraseña, protege contra
        adivinar contraseñas a la fuerza (fuerza bruta):
        después de 5 intentos fallidos seguidos, la cuenta
        queda bloqueada temporalmente (15 minutos), incluso si
        alguien después acierta la contraseña correcta.
        """
        from datetime import datetime, timedelta
        from database.database import ejecutar

        datos = UsuariosRepository.obtener_por_usuario(usuario)

        if datos is None:
            return None

        datos = dict(datos)

        bloqueado_hasta = datos.get("bloqueado_hasta")
        if bloqueado_hasta:
            try:
                if datetime.strptime(bloqueado_hasta, "%Y-%m-%d %H:%M:%S") > datetime.now():
                    return None  # sigue bloqueada, ni siquiera se valida la contraseña
            except (TypeError, ValueError):
                pass

        password_db = datos["password"]

        if isinstance(password_db, str):
            password_db = password_db.encode("utf-8")

        if bcrypt.checkpw(
            password.encode("utf-8"),
            password_db,
        ):
            # Contraseña correcta: se limpia cualquier bloqueo/contador anterior
            if datos.get("intentos_fallidos") or datos.get("bloqueado_hasta"):
                ejecutar(
                    "UPDATE usuarios SET intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=?",
                    (datos["id"],),
                )
            return datos

        # Contraseña incorrecta: se cuenta el intento fallido
        intentos = (datos.get("intentos_fallidos") or 0) + 1
        bloqueo = None
        if intentos >= MAXIMO_INTENTOS_FALLIDOS:
            bloqueo = (datetime.now() + timedelta(minutes=MINUTOS_BLOQUEO)).strftime("%Y-%m-%d %H:%M:%S")
            intentos = 0  # se reinicia el contador; el bloqueo es lo que rige ahora

        ejecutar(
            "UPDATE usuarios SET intentos_fallidos=?, bloqueado_hasta=? WHERE id=?",
            (intentos, bloqueo, datos["id"]),
        )

        return None

    @staticmethod
    def generar_hash(password: str):

        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")