"""
HomeCare Enterprise
Sprint 1.2 - Repository Pacientes
"""
from typing import Any
from database.database import consultar, consultar_uno, ejecutar

class PacientesRepository:

    @staticmethod
    def listar():
        sql = """
        SELECT * FROM pacientes
        ORDER BY primer_apellido, primer_nombre
        """
        return consultar(sql)

    @staticmethod
    def obtener_por_id(paciente_id:int):
        return consultar_uno(
            "SELECT * FROM pacientes WHERE id=?",
            (paciente_id,)
        )

    @staticmethod
    def obtener_por_documento(documento:str):
        return consultar_uno(
            "SELECT * FROM pacientes WHERE documento=?",
            (documento,)
        )

    @staticmethod
    def buscar(texto:str):
        criterio=f"%{texto}%"
        sql="""
        SELECT * FROM pacientes
        WHERE documento LIKE ?
           OR primer_nombre LIKE ?
           OR segundo_nombre LIKE ?
           OR primer_apellido LIKE ?
           OR segundo_apellido LIKE ?
        ORDER BY primer_apellido
        """
        return consultar(sql,(criterio,criterio,criterio,criterio,criterio))

    @staticmethod
    def insertar(datos:dict):
        columnas=", ".join(datos.keys())
        marcadores=", ".join(["?"]*len(datos))
        sql=f"INSERT INTO pacientes ({columnas}) VALUES ({marcadores})"
        return ejecutar(sql, tuple(datos.values()))

    @staticmethod
    def actualizar(paciente_id:int, datos:dict):
        campos=", ".join(f"{k}=?" for k in datos.keys())
        sql=f"UPDATE pacientes SET {campos} WHERE id=?"
        valores=list(datos.values())
        valores.append(paciente_id)
        return ejecutar(sql, tuple(valores))

    @staticmethod
    def eliminar(paciente_id:int):
        return ejecutar("DELETE FROM pacientes WHERE id=?", (paciente_id,))
