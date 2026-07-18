"""
=========================================================
HomeCare Enterprise
Plantilla Service
=========================================================
"""

import uuid

from repositories.plantilla_repository import PlantillaRepository


class PlantillaService:

    def __init__(self):

        self.repository = PlantillaRepository()

    # =====================================================
    # COMPONENTES
    # =====================================================

    def componentes(self):

        return self.repository.listar_componentes()

    # =====================================================
    # LISTAR
    # =====================================================

    def listar(self):

        return self.repository.listar_plantillas()

    # =====================================================
    # CREAR
    # =====================================================

    def crear(

        self,

        nombre,

        categoria,

        especialidad,

        tipo_profesional,

        servicio,

        usuario

    ):

        nuevo_uuid = str(uuid.uuid4())

        return self.repository.crear_plantilla(

            nuevo_uuid,

            nombre,

            categoria,

            especialidad,

            tipo_profesional,

            servicio,

            usuario

        )
