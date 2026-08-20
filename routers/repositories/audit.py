"""
=========================================================
HomeCare Enterprise
Audit Repository
Sprint 3.4A
Versión 8.0
=========================================================
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json

from database.database import ejecutar


class Audit:

    """
    Motor centralizado de auditoría.

    Registra todas las operaciones realizadas por
    los repositorios y servicios.
    """

    LOG_DIR = Path("logs")

    LOG_FILE = LOG_DIR / "audit.log"

    # =====================================================
    # CREAR DIRECTORIO
    # =====================================================

    @classmethod
    def initialize(cls):

        cls.LOG_DIR.mkdir(

            exist_ok=True,

            parents=True,

        )

    # =====================================================
    # REGISTRO GENERAL
    # =====================================================

    @classmethod
    def log(

        cls,

        accion: str,

        tabla: str,

        registro_id=None,

        usuario="Sistema",

        datos=None,

        ip=None,

    ):

        cls.initialize()

        evento = {

            "fecha": datetime.now().isoformat(),

            "accion": accion,

            "tabla": tabla,

            "registro_id": registro_id,

            "usuario": usuario,

            "ip": ip,

            "datos": datos,

        }

        with open(

            cls.LOG_FILE,

            "a",

            encoding="utf-8",

        ) as archivo:

            archivo.write(

                json.dumps(

                    evento,

                    ensure_ascii=False,

                )

            )

            archivo.write("\n")

        return evento

    # =====================================================
    # INSERT
    # =====================================================

    @classmethod
    def insert(

        cls,

        tabla,

        registro_id,

        usuario="Sistema",

        datos=None,

    ):

        return cls.log(

            "INSERT",

            tabla,

            registro_id,

            usuario,

            datos,

        )

    # =====================================================
    # UPDATE
    # =====================================================

    @classmethod
    def update(

        cls,

        tabla,

        registro_id,

        usuario="Sistema",

        datos=None,

    ):

        return cls.log(

            "UPDATE",

            tabla,

            registro_id,

            usuario,

            datos,

        )

    # =====================================================
    # DELETE
    # =====================================================

    @classmethod
    def delete(

        cls,

        tabla,

        registro_id,

        usuario="Sistema",

    ):

        return cls.log(

            "DELETE",

            tabla,

            registro_id,

            usuario,

        )

    # =====================================================
    # LOGIN
    # =====================================================

    @classmethod
    def login(

        cls,

        usuario,

        ip=None,

    ):

        return cls.log(

            "LOGIN",

            "usuarios",

            usuario=usuario,

            ip=ip,

        )

    # =====================================================
    # LOGOUT
    # =====================================================

    @classmethod
    def logout(

        cls,

        usuario,

        ip=None,

    ):

        return cls.log(

            "LOGOUT",

            "usuarios",

            usuario=usuario,

            ip=ip,

        )

    # =====================================================
    # ERROR
    # =====================================================

    @classmethod
    def error(

        cls,

        mensaje,

        usuario="Sistema",

    ):

        return cls.log(

            "ERROR",

            "sistema",

            usuario=usuario,

            datos={

                "mensaje": mensaje,

            },

        )

    # =====================================================
    # AUDITORÍA EN BASE DE DATOS
    # =====================================================

    @classmethod
    def database(

        cls,

        accion,

        tabla,

        registro_id,

        usuario,

        datos=None,

    ):

        sql = """

        INSERT INTO audit_log(

            fecha,

            accion,

            tabla,

            registro_id,

            usuario,

            datos

        )

        VALUES(

            CURRENT_TIMESTAMP,

            ?,?,?,?,?

        )

        """

        ejecutar(

            sql,

            (

                accion,

                tabla,

                registro_id,

                usuario,

                json.dumps(

                    datos,

                    ensure_ascii=False,

                )

                if datos

                else None,

            ),

        )