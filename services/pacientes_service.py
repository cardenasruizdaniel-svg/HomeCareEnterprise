"""
=========================================================
HomeCare IPS Enterprise
Servicio de Pacientes
Versión: 8.0.0 Enterprise
Sprint 1.3
=========================================================
"""

from datetime import datetime
from models.paciente import Paciente
from repositories.pacientes_repository import PacientesRepository
from core.auditoria_archivo_pacientes.audit import crear_evento
from core.auditoria_archivo_pacientes.writer import guardar_evento

class PacientesService:

    @staticmethod
    def listar():
        return PacientesRepository.listar()

    @staticmethod
    def obtener(paciente_id:int):
        return PacientesRepository.obtener_por_id(paciente_id)

    @staticmethod
    def buscar(texto:str):
        return PacientesRepository.buscar(texto)

    @staticmethod
    def guardar(datos:dict):
        paciente=Paciente(**datos)
        errores=paciente.validar()
        if errores:
            raise ValueError("\n".join(errores))
        resultado=PacientesRepository.insertar(paciente.to_dict())
        guardar_evento(crear_evento("sistema","CREAR","PACIENTES",paciente.documento))

        try:
            from services.historial_documentos_service import inicializar_historial
            inicializar_historial(resultado, paciente.tipo_documento, paciente.documento)
        except Exception:
            pass  # no debe impedir la creacion del paciente si esto falla

        try:
            PacientesService._programar_valoracion_inicial(resultado)
        except Exception:
            pass  # tampoco debe impedir la creacion del paciente

        return resultado

    @staticmethod
    def _programar_valoracion_inicial(paciente_id: int):
        """
        Todo paciente nuevo debe tener, desde el primer momento,
        una visita de valoracion medica inicial pendiente de
        programar -- es en esa visita donde el medico evalua al
        paciente y le asigna el programa y los servicios que va
        a recibir. Queda como TENTATIVA (sin profesional aun),
        lista para programarse desde "Gestión de Visitas".
        """

        from datetime import date

        from database.database import consultar_uno
        from services.servicios_paciente_service import asignar_servicio

        actividad = consultar_uno(
            "SELECT id FROM catalogo_actividades WHERE nombre='Visita de valoración médica inicial'"
        )

        if not actividad:
            return

        asignar_servicio(
            paciente_id=paciente_id, tipo_servicio=None, subtipo=None, profesional_id=None,
            frecuencia="Diaria", fecha_inicio=date.today().isoformat(), fecha_fin=None,
            hora_inicio="08:00", hora_fin="09:00",
            indicaciones="Valoración inicial: evaluar al paciente y asignar programa/servicios.",
            usuario=None, actividad_id=dict(actividad)["id"], numero_sesiones=1,
        )

    @staticmethod
    def actualizar(paciente_id:int,datos:dict):
        # Si el estado (Activo/Inactivo) viene en los datos y es
        # distinto al que ya tenia, se guarda la fecha del
        # cambio -- esto es lo que permite despues armar la
        # grafica de cuantos pacientes se activan/inactivan
        # cada mes.
        if "estado" in datos:
            from database.database import consultar_uno
            actual = consultar_uno("SELECT estado FROM pacientes WHERE id=?", (paciente_id,))
            estado_actual = dict(actual)["estado"] if actual else None
            if estado_actual != datos["estado"]:
                from datetime import datetime
                datos["fecha_cambio_estado"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        resultado=PacientesRepository.actualizar(paciente_id,datos)
        guardar_evento(crear_evento("sistema","ACTUALIZAR","PACIENTES",str(paciente_id)))
        return resultado

    @staticmethod
    def eliminar(paciente_id:int):
        resultado=PacientesRepository.eliminar(paciente_id)
        guardar_evento(crear_evento("sistema","ELIMINAR","PACIENTES",str(paciente_id)))
        return resultado
