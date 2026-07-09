import bcrypt

from repositories.usuarios_repository import UsuariosRepository


class AuthService:

    @staticmethod
    def autenticar(usuario: str, password: str):

        datos = UsuariosRepository.obtener_por_usuario(usuario)

        if datos is None:
            return None

        password_db = datos["password"]

        if isinstance(password_db, str):
            password_db = password_db.encode("utf-8")

        if bcrypt.checkpw(
            password.encode("utf-8"),
            password_db,
        ):
            return datos

        return None

    @staticmethod
    def generar_hash(password: str):

        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")