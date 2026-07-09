"""
=========================================================
HomeCare Enterprise
API para la App Movil (PWA offline-first)

Usa la misma sesion (cookie) que la aplicacion web: el
profesional inicia sesion una vez estando en linea, y desde
ahi la app puede seguir funcionando sin conexion (la cookie
queda guardada en el navegador/dispositivo).

Endpoint clave: POST /api/movil/sync — recibe en un solo
lote todas las acciones que se registraron mientras el
dispositivo estaba sin datos/internet (ingreso, salida,
signos vitales, medicamento administrado, evolucion,
ordenes medicas) y las procesa en el servidor, devolviendo
el resultado de cada una para que la app sepa que ya se
sincronizo y pueda borrarla de su cola local.
=========================================================
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from core.dependencies import requiere_permiso, usuario_actual
from database.database import consultar, consultar_uno

from services import movil_service
from services.auth_service import AuthService
from services.ordenes_service import OrdenesService

router = APIRouter(prefix="/api/movil", tags=["App Móvil"])


# ==========================================
# LOGIN (para la PWA offline-first)
# ==========================================

class CredencialesLogin(BaseModel):
    usuario: str
    password: str


@router.post("/login")
async def login(credenciales: CredencialesLogin, request: Request):
    datos = AuthService.autenticar(credenciales.usuario, credenciales.password)

    if datos is None:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")

    datos = dict(datos)
    datos.pop("password", None)

    request.session["usuario_id"] = datos["id"]
    request.session["usuario"] = datos["usuario"]
    request.session["nombre"] = datos["nombre"]
    request.session["rol"] = datos["rol"]

    return {"ok": True, "usuario": datos}


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}


# ==========================================
# PERFIL DEL PROFESIONAL AUTENTICADO
# ==========================================

@router.get("/perfil")
async def perfil(usuario=Depends(usuario_actual)):
    profesional = consultar_uno(
        "SELECT * FROM profesionales WHERE usuario_id=?",
        (usuario.get("id"),),
    )

    return {
        "usuario": usuario,
        "profesional_id": dict(profesional)["id"] if profesional else None,
    }


# ==========================================
# AGENDA (para el calendario de la app)
# ==========================================

@router.get("/agenda/{profesional_id}")
async def agenda(
    profesional_id: int,
    fecha_inicio: str,
    fecha_fin: str,
    usuario=Depends(requiere_permiso("programacion")),
):
    return {"visitas": movil_service.agenda_profesional(profesional_id, fecha_inicio, fecha_fin)}


# ==========================================
# FICHA DEL PACIENTE (para consulta offline)
# ==========================================

@router.get("/paciente/{paciente_id}")
async def paciente(
    paciente_id: int,
    usuario=Depends(requiere_permiso("pacientes")),
):
    return movil_service.ficha_paciente_offline(paciente_id)


# ==========================================
# PLANILLA DE VISITA PENDIENTE (para firmar en campo)
# ==========================================

@router.get("/planilla/{programacion_id}")
async def planilla_de_visita(
    programacion_id: int,
    usuario=Depends(requiere_permiso("programacion")),
):
    from repositories.planilla_visitas_repository import PlanillaVisitasRepository
    fila = PlanillaVisitasRepository.obtener_por_programacion(programacion_id)
    return dict(fila) if fila else None


@router.get("/paciente/{paciente_id}/informes")
async def informes_paciente(
    paciente_id: int,
    usuario=Depends(requiere_permiso("programacion")),
):
    """Lista los informes (no las notas aclaratorias) del paciente, para elegir a cual corregir."""
    from services.evoluciones_service import listar_informes_para_aclarar
    return listar_informes_para_aclarar(paciente_id)


@router.get("/paciente/{paciente_id}/laboratorios")
async def laboratorios_paciente(
    paciente_id: int,
    usuario=Depends(requiere_permiso("programacion")),
):
    """Lista los resultados de laboratorio ya registrados del paciente, para mostrarlos en la app."""
    return movil_service.listar_laboratorios_paciente(paciente_id)


@router.get("/visita/{programacion_id}/informes")
async def informes_de_visita(
    programacion_id: int,
    usuario=Depends(requiere_permiso("programacion")),
):
    """
    Devuelve todos los registros de historia clinica (informes
    y notas aclaratorias) que se hicieron durante ESTA visita
    en particular -- para el "Ver reporte" que aparece cuando
    ya se finalizaron labores.
    """
    from database.database import consultar_todos
    filas = consultar_todos(
        """
        SELECT e.id, e.consecutivo, e.tipo_registro, e.tipo_profesional, e.nota, e.fecha,
               e.nota_aclaratoria_de, e.firma_profesional_base64,
               pr.nombre_completo AS profesional
        FROM evoluciones e
        LEFT JOIN profesionales pr ON pr.id = e.profesional_id
        WHERE e.programacion_id=?
        ORDER BY e.consecutivo
        """,
        (programacion_id,),
    )
    return [dict(f) for f in filas]


# ==========================================
# MEDICAMENTOS DEL PACIENTE (para el aplicador)
# ==========================================

@router.get("/paciente/{paciente_id}/medicamentos")
async def medicamentos_paciente(
    paciente_id: int,
    usuario=Depends(requiere_permiso("medicamentos")),
):
    filas = consultar(
        "SELECT * FROM medicamentos WHERE paciente_id=? AND estado='ACTIVO'",
        (paciente_id,),
    )
    return {"medicamentos": [dict(f) for f in filas]}


# ==========================================
# SINCRONIZACIÓN POR LOTES
# ==========================================

class AccionOffline(BaseModel):
    id: str
    tipo: str
    payload: dict


class LoteSincronizacion(BaseModel):
    acciones: list[AccionOffline]


@router.post("/sync")
async def sincronizar(
    lote: LoteSincronizacion,
    usuario=Depends(usuario_actual),
):
    resultados = []

    for accion in lote.acciones:
        try:
            resultado = _procesar_accion(accion.tipo, accion.payload, usuario)
            resultados.append({"id": accion.id, "ok": True, "resultado": resultado})
        except Exception as error:
            resultados.append({"id": accion.id, "ok": False, "error": str(error)})

    return {"resultados": resultados}


def _procesar_accion(tipo: str, p: dict, usuario: dict):

    usuario_id = usuario.get("id")

    if tipo == "ingreso":
        return movil_service.registrar_ingreso(
            p["visita_id"], p.get("lat"), p.get("lon"),
            foto_base64=p.get("foto_base64"),
        )

    if tipo == "salida":
        return movil_service.registrar_salida(
            p["visita_id"], p.get("lat"), p.get("lon"),
            foto_base64=p.get("foto_base64"),
        )

    if tipo == "signos_vitales":
        return movil_service.registrar_signos_vitales(
            p["paciente_id"], p.get("profesional", usuario.get("nombre", "")), p.get("datos", {}), usuario_id
        )

    if tipo == "medicamento_administrado":
        return movil_service.registrar_medicamento_administrado(
            p["medicamento_id"], p["paciente_id"], p.get("profesional", usuario.get("nombre", "")),
            p.get("dosis", ""), p.get("via", ""), p.get("observaciones", ""),
            p.get("estado", "Administrado"),
        )

    if tipo == "evolucion":
        return movil_service.registrar_evolucion(
            p["paciente_id"], p.get("programacion_id"), p.get("profesional_id"),
            p.get("tipo_profesional", ""), p.get("nota", ""),
            p.get("lat"), p.get("lon"), usuario_id,
            p.get("tipo_registro", "INFORME"), p.get("nota_aclaratoria_de"),
        )

    if tipo == "orden_medica":
        if usuario.get("rol") not in ("Médico", "Medico", "Director Médico", "Administrador"):
            raise ValueError("Solo un médico puede generar órdenes médicas.")

        return OrdenesService.crear_y_enviar(
            paciente_id=p["paciente_id"],
            profesional_id=p.get("profesional_id"),
            tipo=p.get("tipo_orden", "Otro"),
            descripcion=p.get("descripcion", ""),
            codigo_cups=p.get("codigo_cups", ""),
            historia_id=p.get("historia_id"),
            usuario_creacion=usuario_id,
        )

    if tipo == "firmar_planilla":
        return movil_service.firmar_planilla(
            p["planilla_id"], p.get("firmante", "Paciente"), p.get("nombre_acompanante", ""),
            p.get("firma_base64"), p.get("foto_base64"), p.get("lat"), p.get("lon"),
            p.get("marca_tiempo_offline"),
        )

    if tipo == "actualizar_ubicacion_paciente":
        return movil_service.actualizar_ubicacion_paciente(
            p["paciente_id"], p.get("lat"), p.get("lon"), usuario.get("rol"),
        )

    if tipo == "resultado_laboratorio":
        return movil_service.registrar_resultado_laboratorio(
            p["paciente_id"], p.get("nombre_examen"), p.get("laboratorio_realizo"),
            p.get("fecha_resultado"), p.get("resultado_texto"), p.get("foto_resultado_base64"),
            p.get("profesional_id"), usuario.get("id") if isinstance(usuario, dict) else None,
            items=p.get("items", []),
        )

    if tipo == "crear_orden_medica":
        return movil_service.crear_orden_medica(
            p["paciente_id"], p.get("profesional_id"), p.get("tipo_orden"),
            p.get("descripcion"), p.get("codigo_cups"),
            usuario.get("id") if isinstance(usuario, dict) else None,
        )

    raise ValueError(f"Tipo de acción desconocido: {tipo}")
