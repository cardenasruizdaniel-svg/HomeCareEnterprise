"""
=========================================================
HomeCare Enterprise
Repository Manager
Sprint 3.4A
Versión: 8.0
=========================================================
"""

from __future__ import annotations

from repositories.programacion_repository import ProgramacionRepository
from repositories.profesionales_repository import ProfesionalesRepository
from repositories.despacho_repository import DespachoRepository

# Estos repositorios se irán incorporando durante los
# siguientes PR del Sprint 3.4A.
#
# from repositories.pacientes_repository import PacientesRepository
# from repositories.agenda_repository import AgendaRepository
# from repositories.asignacion_repository import AsignacionRepository
# from repositories.usuarios_repository import UsuariosRepository
# from repositories.medicamentos_repository import MedicamentosRepository
# from repositories.tratamientos_repository import TratamientosRepository


class RepositoryManager:
    """
    Contenedor central de repositorios.

    Expone una única instancia de cada repositorio para
    ser reutilizada por toda la aplicación.
    """

    def __init__(self):

        self._programacion = ProgramacionRepository()
        self._profesionales = ProfesionalesRepository()
        self._despacho = DespachoRepository()

        # Se habilitarán conforme se construyan
        #
        # self._pacientes = PacientesRepository()
        # self._agenda = AgendaRepository()
        # self._asignacion = AsignacionRepository()
        # self._usuarios = UsuariosRepository()
        # self._medicamentos = MedicamentosRepository()
        # self._tratamientos = TratamientosRepository()

    # =====================================================
    # PROGRAMACIÓN
    # =====================================================

    @property
    def programacion(self):

        return self._programacion

    # =====================================================
    # PROFESIONALES
    # =====================================================

    @property
    def profesionales(self):

        return self._profesionales

    # =====================================================
    # DESPACHO
    # =====================================================

    @property
    def despacho(self):

        return self._despacho

    # =====================================================
    # REGISTRO DINÁMICO
    # =====================================================

    def register(
        self,
        nombre: str,
        repositorio,
    ):

        setattr(
            self,
            f"_{nombre}",
            repositorio,
        )

    # =====================================================
    # OBTENER REPOSITORIO
    # =====================================================

    def get(
        self,
        nombre: str,
    ):

        atributo = f"_{nombre}"

        if not hasattr(self, atributo):

            raise AttributeError(

                f"Repositorio '{nombre}' no registrado."

            )

        return getattr(self, atributo)

    # =====================================================
    # LISTAR REPOSITORIOS
    # =====================================================

    def repositories(self):

        return {

            nombre.replace("_", ""): valor

            for nombre, valor

            in self.__dict__.items()

            if nombre.startswith("_")

        }

    # =====================================================
    # HEALTH CHECK
    # =====================================================

    def health(self):

        estado = {}

        for nombre, repo in self.repositories().items():

            try:

                estado[nombre] = repo.health_check()

            except Exception:

                estado[nombre] = False

        return estado


# =========================================================
# INSTANCIA GLOBAL
# =========================================================

repos = RepositoryManager()