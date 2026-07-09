"""
=========================================================
HomeCare IPS Enterprise
Excepciones Personalizadas del Sistema
=========================================================
"""


class HomeCareError(Exception):
    """
    Excepción base del sistema.
    """

    def __init__(self, mensaje="Error interno del sistema."):

        self.mensaje = mensaje

        super().__init__(self.mensaje)


# ==========================================================
# SEGURIDAD
# ==========================================================

class PermisoDenegadoError(HomeCareError):

    def __init__(self):

        super().__init__("No tiene permisos para realizar esta operación.")


class UsuarioNoAutenticadoError(HomeCareError):

    def __init__(self):

        super().__init__("Debe iniciar sesión para continuar.")


# ==========================================================
# PACIENTES
# ==========================================================

class PacienteNoEncontradoError(HomeCareError):

    def __init__(self):

        super().__init__("El paciente no existe.")


class PacienteDuplicadoError(HomeCareError):

    def __init__(self):

        super().__init__("Ya existe un paciente con ese documento.")


# ==========================================================
# MEDICAMENTOS
# ==========================================================

class MedicamentoNoEncontradoError(HomeCareError):

    def __init__(self):

        super().__init__("Medicamento no encontrado.")


class MedicamentoSuspendidoError(HomeCareError):

    def __init__(self):

        super().__init__("El medicamento se encuentra suspendido.")


# ==========================================================
# DIAGNÓSTICOS
# ==========================================================

class DiagnosticoNoEncontradoError(HomeCareError):

    def __init__(self):

        super().__init__("Diagnóstico no encontrado.")


# ==========================================================
# SIGNOS VITALES
# ==========================================================

class SignosVitalesError(HomeCareError):

    def __init__(self, mensaje="Error en los signos vitales registrados."):

        super().__init__(mensaje)


# ==========================================================
# VALIDACIONES
# ==========================================================

class ValidacionError(HomeCareError):

    def __init__(self, mensaje):

        super().__init__(mensaje)


class ValidacionClinicaError(HomeCareError):

    def __init__(self, mensaje):

        super().__init__(mensaje)


# ==========================================================
# BASE DE DATOS
# ==========================================================

class BaseDatosError(HomeCareError):

    def __init__(self):

        super().__init__("Error de conexión con la base de datos.")


# ==========================================================
# ARCHIVOS
# ==========================================================

class ArchivoNoPermitidoError(HomeCareError):

    def __init__(self):

        super().__init__("El archivo seleccionado no está permitido.")


class ArchivoNoEncontradoError(HomeCareError):

    def __init__(self):

        super().__init__("No fue posible encontrar el archivo solicitado.")


# ==========================================================
# AUDITORÍA
# ==========================================================

class AuditoriaError(HomeCareError):

    def __init__(self):

        super().__init__("Error registrando la auditoría del sistema.")