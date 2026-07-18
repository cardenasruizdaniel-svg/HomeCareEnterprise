"""
=========================================================
HomeCare Enterprise - Generador de datos de prueba

Crea una base de datos nueva (database.db) con:
- Usuarios de prueba (uno por profesional + un administrador)
- Profesionales de distintos perfiles, con firma capturada
- Pacientes con alergias, antecedentes, diagnósticos
- Programas de atención asignados
- Servicios/actividades con sesiones programadas y algunas
  ya completadas (con informe firmado en la historia clínica)
- Plantillas de nota de ejemplo por rol
- Signos vitales, consentimientos informados, fotos

USO: python3 generar_datos_prueba.py
(ejecutar desde la raíz del proyecto, con el entorno virtual activado)
=========================================================
"""

import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Empezar desde una base de datos limpia
if os.path.exists("database.db"):
    os.remove("database.db")
    print("[OK] Base de datos anterior eliminada")

from database.database import crear_tablas, ejecutar
from database.migrations import ejecutar_migraciones

crear_tablas()
ejecutar_migraciones()
print("[OK] Esquema creado y migrado")

# Sembrar catálogos base (programas, actividades, EPS, bancos, DIVIPOLA, CUPS, CUM, CIE10)
from repositories.programas_atencion_repository import ProgramasAtencionRepository
from repositories.catalogo_actividades_repository import CatalogoActividadesRepository
from repositories.catalogo_eps_repository import CatalogoEPSRepository
from repositories.catalogo_bancos_repository import CatalogoBancosRepository
from repositories.catalogos_repository import DivipolaRepository, CUPSRepository, CUMRepository
from repositories import cie10_repository

ProgramasAtencionRepository.sembrar_si_vacio()
CatalogoActividadesRepository.sembrar_si_vacio()
CatalogoEPSRepository.sembrar_si_vacio()
CatalogoBancosRepository.sembrar_si_vacio()
DivipolaRepository.sembrar_si_vacio()
CUPSRepository.sembrar_si_vacio()
CUMRepository.sembrar_si_vacio()
cie10_repository.sembrar_si_vacio()
print("[OK] Catálogos sembrados (programas, actividades, EPS, bancos, DIVIPOLA, CUPS, CUM, CIE-10)")

# ==========================================
# FIRMA DE EJEMPLO (un garabato simple en base64,
# solo para que se vea algo en las pruebas)
# ==========================================

FIRMA_EJEMPLO = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgAAAA8CAIAAACsOWLGAAAAp0lEQVR42u3awQkAIQxFwVRi/yWqJ4tQMYZZ5v4hvJNs9DHhuHAChIWwEBYIC2EhLBAWwkJYICyEhbBAWAgLYYGwKBpW2/js1t4Vll1h2RWWQwvLoe0mCws8NyAshAXCQlgIC4SFsBAWCAthISwQFsLi37Ce/Otjt/ausOwKy66wHFpYDm33TljguQFhISwQFsJCWCAshIWwQFgIC2GBsBAWwgJhkdQCgdsI02fcQc8AAAAASUVORK5CYII="

FOTO_EJEMPLO = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAUAAAADwCAIAAAD+Tyo8AAACD0lEQVR42u3TQQkAAAgEwQtrJWPawQ7+hIFJsLCpHuCpSAAGBgwMGBgMDBgYMDBgYDAwYGDAwGBgwMCAgQEDg4EBAwMGBgwMBgYMDBgYDAwYGDAwYGAwMGBgwMCAgcHAgIEBA4OBAQMDBgYMDAYGDAwYGAysAhgYMDBgYDAwYGDAwICBwcCAgQEDg4EBAwMGBgwMBgYMDBgYMDAYGDAwYGAwMGBgwMCAgcHAgIEBAwMGBgMDBgYMDAYGDAwYGDAwGBgwMGBgMDBgYMDAgIHBwICBAQMDBgYDAwYGDAwGBgwMGBgwMBgYMDBgYMDAYGDAwICBwcCAgQEDAwYGAwMGBgwMGBgMDBgYMDAYGDAwYGDAwGBgwMCAgcHAgIEBAwMGBgMDBgYMDBgYDAwYGDAwGBgwMGBgwMBgYMDAgIEBA4OBAQMDBgYDAwYGDAwYGAwMGBgwMBhYBTAwYGDAwGBgwMCAgQEDg4EBAwMGBgMDBgYMDBgYDAwYGDAwYGAwMGBgwMBgYMDAgIEBA4OBAQMDBgYMDAYGDAwYGAwMGBgwMGBgMDBgYMDAYGDAwICBAQODgQEDAwYGDAwGBgwMGBgMDBgYMDBgYDAwYGDAwICBwcCAgQEDg4EBAwMGBgwMBgYMDBgYMDAYGDAwYGAwMGBgwMCAgcHAgIEBA4OBAQMDBgYMDAYGDAwYGDAwGBgwMHC3tSqpWEG3oGkAAAAASUVORK5CYII="

# ==========================================
# USUARIOS Y PROFESIONALES DE PRUEBA
# ==========================================

from services.auth_service import AuthService
from services import profesionales_service
from database.database import consultar_uno

def crear_usuario(nombre, usuario, rol):
    password_cifrada = AuthService.generar_hash("prueba123")
    return ejecutar(
        "INSERT INTO usuarios(nombre, usuario, password, rol, activo) VALUES (?, ?, ?, ?, 1)",
        (nombre, usuario, password_cifrada, rol),
    )

# Administrador
crear_usuario("Administradora de Prueba", "admin", "Administrador")
print("[OK] Usuario admin / prueba123 (Administrador)")

# Usuario administrativo (no clínico): crea pacientes y agenda
# visitas, pero no hace notas clínicas ni ve órdenes/facturación.
crear_usuario("Diana Castaño", "dcastano", "Administrativo")
print("[OK] Usuario dcastano / prueba123 (Administrativo)")

PROFESIONALES_PRUEBA = [
    {
        "documento": "1094111111", "primer_nombre": "Andrés", "primer_apellido": "Pérez",
        "especialidad_principal": "Médico General", "celular": "3001111111",
        "correo": "andres.perez@homecare.test", "usuario": "amperez", "rol": "Médico",
        "banco": "Bancolombia", "tipo_cuenta": "Ahorros", "numero_cuenta": "10023456789",
    },
    {
        "documento": "1094222222", "primer_nombre": "Laura", "primer_apellido": "Gómez",
        "especialidad_principal": "Enfermero", "celular": "3002222222",
        "correo": "laura.gomez@homecare.test", "usuario": "lgomez", "rol": "Enfermero",
        "banco": "Davivienda", "tipo_cuenta": "Ahorros", "numero_cuenta": "20034567890",
    },
    {
        "documento": "1094333333", "primer_nombre": "Julián", "primer_apellido": "Díaz",
        "especialidad_principal": "Fisioterapeuta", "celular": "3003333333",
        "correo": "julian.diaz@homecare.test", "usuario": "jdiaz", "rol": "Fisioterapeuta",
        "banco": "Banco de Bogotá", "tipo_cuenta": "Ahorros", "numero_cuenta": "30045678901",
    },
    {
        "documento": "1094444444", "primer_nombre": "Marta", "primer_apellido": "Ruiz",
        "especialidad_principal": "Cuidador", "celular": "3004444444",
        "correo": "marta.ruiz@homecare.test", "usuario": "mruiz", "rol": "Cuidador",
        "banco": "Nequi", "tipo_cuenta": "Ahorros", "numero_cuenta": "3004444444",
    },
    {
        "documento": "1094555555", "primer_nombre": "Sara", "primer_apellido": "López",
        "especialidad_principal": "Psicóloga", "celular": "3005555555",
        "correo": "sara.lopez@homecare.test", "usuario": "slopez", "rol": "Psicólogo",
        "banco": "BBVA Colombia", "tipo_cuenta": "Ahorros", "numero_cuenta": "40056789012",
    },
    {
        "documento": "1094666666", "primer_nombre": "Diego", "primer_apellido": "Rincón",
        "especialidad_principal": "Nutricionista", "celular": "3006666666",
        "correo": "diego.rincon@homecare.test", "usuario": "drincon", "rol": "Nutricionista",
        "banco": "Banco Caja Social", "tipo_cuenta": "Ahorros", "numero_cuenta": "50067890123",
    },
]

profesionales_ids = {}

for p in PROFESIONALES_PRUEBA:
    usuario_id = crear_usuario(f"{p['primer_nombre']} {p['primer_apellido']}", p["usuario"], p["rol"])

    profesional_id = profesionales_service.crear(
        {
            "tipo_documento": "CC", "documento": p["documento"],
            "registro_profesional": f"RM-{p['documento'][-6:]}",
            "profesion": p["especialidad_principal"], "especialidad_principal": p["especialidad_principal"],
            "primer_nombre": p["primer_nombre"], "segundo_nombre": "", "primer_apellido": p["primer_apellido"],
            "segundo_apellido": "", "telefono": "", "celular": p["celular"], "correo": p["correo"],
            "direccion": "Cll 10 # 5-20", "municipio": "Armenia", "departamento": "Quindío",
            "capacidad_diaria": 8, "acepta_urgencias": 0, "radio_cobertura_km": 15,
            "tiempo_promedio_visita": 60, "observaciones": "Profesional de prueba",
            "tipo_contrato": "POR_HORAS", "valor_hora": 18000, "salario_fijo": 0,
            "banco": p["banco"], "tipo_cuenta": p["tipo_cuenta"], "numero_cuenta": p["numero_cuenta"],
            "firma_base64": FIRMA_EJEMPLO,
        },
        usuario_id=usuario_id,
    )

    # Vincular la cuenta de usuario al profesional para que pueda iniciar sesión y ver "Mi Agenda"
    ejecutar("UPDATE profesionales SET usuario_id=?, estado='ACTIVO' WHERE id=?", (usuario_id, profesional_id))

    profesionales_ids[p["primer_nombre"]] = profesional_id
    print(f"[OK] Profesional creado: {p['primer_nombre']} {p['primer_apellido']} ({p['especialidad_principal']}) — usuario: {p['usuario']} / prueba123")

print(f"\n[OK] {len(PROFESIONALES_PRUEBA)} profesionales creados con firma digital de prueba")

# ==========================================
# PACIENTES DE PRUEBA
# ==========================================

from services.pacientes_service import PacientesService

PACIENTES_PRUEBA = [
    {
        "tipo_documento": "CC", "documento": "1094777001", "primer_nombre": "Carlos",
        "primer_apellido": "Ramírez", "fecha_nacimiento": "1975-03-12", "sexo": "M",
        "eps": "Nueva EPS", "regimen": "Contributivo", "celular": "3007770001",
        "correo": "carlos.ramirez.prueba@example.com",
        "direccion": "Cra 12 # 15-30", "barrio": "Centro", "municipio": "Armenia", "departamento": "Quindío",
        "latitud": 4.5339, "longitud": -75.6811,
    },
    {
        "tipo_documento": "TI", "documento": "1094777002", "primer_nombre": "Sofía",
        "primer_apellido": "Martínez", "fecha_nacimiento": "2012-06-20", "sexo": "F",
        "eps": "EPS Sanitas", "regimen": "Contributivo", "celular": "3007770002",
        "correo": "", "direccion": "Cll 20 # 8-15", "barrio": "La Castellana", "municipio": "Armenia",
        "departamento": "Quindío", "latitud": 4.5280, "longitud": -75.6750,
    },
    {
        "tipo_documento": "CC", "documento": "1094777003", "primer_nombre": "Ana",
        "primer_apellido": "Torres", "fecha_nacimiento": "1950-11-05", "sexo": "F",
        "eps": "Salud Total EPS", "regimen": "Contributivo", "celular": "3007770003",
        "correo": "ana.torres.prueba@example.com",
        "direccion": "Cra 8 # 22-10", "barrio": "El Bosque", "municipio": "Armenia", "departamento": "Quindío",
        "latitud": 4.5400, "longitud": -75.6900,
    },
    {
        "tipo_documento": "CC", "documento": "1094777004", "primer_nombre": "Luis",
        "primer_apellido": "Pérez", "fecha_nacimiento": "1968-02-28", "sexo": "M",
        "eps": "Coosalud EPS", "regimen": "Subsidiado", "celular": "3007770004",
        "correo": "", "direccion": "Cll 30 # 12-05", "barrio": "Alfonso López", "municipio": "Armenia",
        "departamento": "Quindío", "latitud": 4.5250, "longitud": -75.6820,
    },
    {
        "tipo_documento": "CC", "documento": "1094777005", "primer_nombre": "María",
        "primer_apellido": "González", "fecha_nacimiento": "1982-09-15", "sexo": "F",
        "eps": "Famisanar EPS", "regimen": "Contributivo", "celular": "3007770005",
        "correo": "maria.gonzalez.prueba@example.com",
        "direccion": "Cra 15 # 30-40", "barrio": "Los Ángeles", "municipio": "Calarcá", "departamento": "Quindío",
        "latitud": 4.5225, "longitud": -75.6435,
    },
    {
        "tipo_documento": "CC", "documento": "1094777006", "primer_nombre": "Jorge",
        "primer_apellido": "Salazar", "fecha_nacimiento": "1945-07-22", "sexo": "M",
        "eps": "Nueva EPS", "regimen": "Contributivo", "celular": "3007770006",
        "correo": "", "direccion": "Cll 5 # 10-18", "barrio": "San José", "municipio": "Armenia",
        "departamento": "Quindío", "latitud": 4.5360, "longitud": -75.6780,
    },
]

pacientes_ids = {}

for p in PACIENTES_PRUEBA:
    paciente_id = PacientesService.guardar(p)
    pacientes_ids[p["primer_nombre"]] = paciente_id
    print(f"[OK] Paciente creado: {p['primer_nombre']} {p['primer_apellido']} ({p['tipo_documento']} {p['documento']})")

print(f"\n[OK] {len(PACIENTES_PRUEBA)} pacientes creados")

# ==========================================
# ALERGIAS, ANTECEDENTES Y ACUDIENTES
# ==========================================

from services.alergias_service import crear_alergia
from services.antecedentes_service import crear_antecedente
from services.acudientes_service import crear_acudiente
from services.diagnosticos_service import DiagnosticosService

# Carlos Ramírez: alergia grave a la dipirona + hipertensión
crear_alergia(pacientes_ids["Carlos"], "MED", "Dipirona", "Grave", "Activa",
              "Urticaria y dificultad respiratoria", "Confirmada por el paciente y la familia",
              date.today().isoformat(), 1)
crear_antecedente(pacientes_ids["Carlos"], "AP", "Hipertensión arterial diagnosticada hace 10 años",
                   "En tratamiento con losartán", 1)
DiagnosticosService.asignar(pacientes_ids["Carlos"], "I10X", "Hipertensión esencial (primaria)",
                              "CONFIRMADO", date.today().isoformat(), "Dr. Andrés Pérez", "Medicina General",
                              "<b>Paciente con HTA controlada.</b><ul><li>Continuar manejo farmacológico</li><li>Control en 30 días</li></ul>",
                              1)
crear_acudiente(pacientes_ids["Carlos"], "María Ramírez", "CC", "1000111222", "Hija",
                "3009998877", "", "maria.hija@example.com", "Cra 12 # 15-30", "Centro",
                "Armenia", "Quindío", "Armenia", "Enfermera", "", 1, 1, 1)

# Sofía Martínez (menor de edad): alergia a alimentos, traqueostomía
crear_alergia(pacientes_ids["Sofía"], "ALI", "Maní", "Moderada", "Activa",
              "Hinchazón y picazón", "Evitar frutos secos por completo", date.today().isoformat(), 1)
crear_antecedente(pacientes_ids["Sofía"], "AQ", "Traqueostomía realizada en 2024",
                   "Requiere manejo y cuidado permanente de la vía aérea", 1)
DiagnosticosService.asignar(pacientes_ids["Sofía"], "Z930", "Traqueostomía", "CONFIRMADO",
                              date.today().isoformat(), "Dr. Andrés Pérez", "Medicina General",
                              "<b>Paciente pediátrica con traqueostomía permanente.</b><br>Requiere cuidados de enfermería especializados.",
                              1)
crear_acudiente(pacientes_ids["Sofía"], "Patricia Martínez", "CC", "1000222333", "Madre",
                "3007770002", "", "patricia.madre@example.com", "Cll 20 # 8-15", "La Castellana",
                "Armenia", "Quindío", "Armenia", "Ama de casa", "", 1, 1, 1)

# Ana Torres: paciente geriátrica, EPOC
crear_antecedente(pacientes_ids["Ana"], "AP", "EPOC diagnosticado hace 5 años", "Oxígeno domiciliario intermitente", 1)
DiagnosticosService.asignar(pacientes_ids["Ana"], "J449", "Enfermedad pulmonar obstructiva crónica, no especificada",
                              "CONFIRMADO", date.today().isoformat(), "Dr. Andrés Pérez", "Medicina General",
                              "Paciente con EPOC estadio moderado. Requiere terapia respiratoria periódica.", 1)

# Luis Pérez: úlcera por presión
crear_antecedente(pacientes_ids["Luis"], "AP", "Paciente postrado por secuela de ACV", "Requiere cambios posturales frecuentes", 1)
DiagnosticosService.asignar(pacientes_ids["Luis"], "L89X", "Úlcera de decúbito", "CONFIRMADO",
                              date.today().isoformat(), "Laura Gómez", "Enfermería",
                              "<b>Úlcera en talón derecho, estadio II.</b><ul><li>Curación diaria</li><li>Cambios posturales cada 2 horas</li></ul>", 1)

print("[OK] Alergias, antecedentes, acudientes y diagnósticos creados para varios pacientes")

# ==========================================
# PROGRAMAS DE ATENCIÓN
# ==========================================

from services.programas_atencion_service import listar_programas_activos, asignar_programa

programas = listar_programas_activos()
programa_alta_traqueo = next(p for p in programas if "Traqueostomía" in p["nombre"])
programa_baja_terapias = next(p for p in programas if "Con Terapias" in p["nombre"])
programa_baja_sin_terapias = next(p for p in programas if "Sin Terapias" in p["nombre"])

asignar_programa(pacientes_ids["Sofía"], programa_alta_traqueo["id"], profesionales_ids["Andrés"],
                  "Valoración inicial: paciente pediátrica con traqueostomía permanente.", 1)
asignar_programa(pacientes_ids["Ana"], programa_baja_terapias["id"], profesionales_ids["Andrés"],
                  "Valoración inicial: requiere terapia respiratoria periódica.", 1)
asignar_programa(pacientes_ids["Carlos"], programa_baja_sin_terapias["id"], profesionales_ids["Andrés"],
                  "Valoración inicial: control de hipertensión, sin requerir terapias.", 1)

print("[OK] Programas de atención asignados a 3 pacientes")

# ==========================================
# SERVICIOS/ACTIVIDADES CON SESIONES
# (mezcla de: sin programar, programadas a futuro,
# y ya completadas con informe firmado)
# ==========================================

from repositories.catalogo_actividades_repository import CatalogoActividadesRepository as CAR
from services.servicios_paciente_service import asignar_servicio
from services.gestion_visitas_service import listar_visitas_de_servicio, programar_visita
from services.planilla_visitas_service import firmar_visita
from services.evoluciones_service import registrar_evolucion
from services import programacion_service

actividades = [dict(a) for a in CAR.listar_activas()]
act = {a["nombre"]: a["id"] for a in actividades}

hoy = date.today()
ayer = (hoy - timedelta(days=1)).isoformat()
hace_3_dias = (hoy - timedelta(days=3)).isoformat()
manana = (hoy + timedelta(days=1)).isoformat()
en_3_dias = (hoy + timedelta(days=3)).isoformat()

# --- Curaciones para Luis: 5 sesiones, 2 ya completadas con informe, resto pendiente ---
resultado_curaciones = asignar_servicio(
    pacientes_ids["Luis"], None, None, profesionales_ids["Laura"], "Diaria",
    hace_3_dias, None, "08:00", "09:00", "Curación de úlcera en talón derecho",
    usuario=1, actividad_id=act["Curaciones"], numero_sesiones=5,
)
visitas_curaciones = listar_visitas_de_servicio(resultado_curaciones["servicio_id"])

# Programar y completar las primeras 2 (ya serían del pasado)
for i in range(2):
    r = programar_visita(visitas_curaciones[i]["id"], visitas_curaciones[i]["fecha"], "08:00", "09:00",
                          profesionales_ids["Laura"], usuario_id=1)
    programacion_service.registrar_ingreso(r["programacion_id"], 4.5250, -75.6820, FOTO_EJEMPLO)
    programacion_service.registrar_salida(r["programacion_id"], 4.5250, -75.6820, FOTO_EJEMPLO)
    registrar_evolucion(pacientes_ids["Luis"], r["programacion_id"], profesionales_ids["Laura"],
                         "Nota de Curaciones",
                         f"Curación N.° {i+1} realizada sin complicaciones. Herida en proceso de granulación, "
                         f"sin signos de infección. Se aplicó apósito hidrocoloide.", usuario_id=1)
    firmar_visita(visitas_curaciones[i]["id"], "Acompañante", "Familiar a cargo",
                  FIRMA_EJEMPLO, FOTO_EJEMPLO)

# Programar 1 sesión a futuro (tentativa, sin hora obligatoria)
programar_visita(visitas_curaciones[2]["id"], manana, "", "", profesionales_ids["Laura"], usuario_id=1)

# Nota aclaratoria de ejemplo: corrige el primer informe de curación
# (para poder probar la Historia Clínica con informe + aclaratoria,
# y la impresión individual de cada uno)
registrar_evolucion(pacientes_ids["Luis"], None, profesionales_ids["Laura"], "Nota de Curaciones",
                     "En el informe N.° 1 se indicó por error que la curación fue en el talón derecho; "
                     "la úlcera tratada corresponde al talón izquierdo. Se deja esta aclaración para "
                     "corregir el registro sin modificar el informe original.",
                     usuario_id=1, tipo_registro="NOTA_ACLARATORIA", nota_aclaratoria_de=1)

# Las 2 restantes quedan PENDIENTES de programar (para probar el panel de alertas del dashboard)
print(f"[OK] Curaciones para Luis: {len(visitas_curaciones)} sesiones "
      f"(2 completadas con informe y firma, 1 programada a futuro, 2 pendientes de programar)")
print("[OK] Nota aclaratoria de ejemplo registrada sobre el informe N.° 1 de Luis")

# --- Terapia respiratoria para Ana: 3 sesiones ---
resultado_terapia = asignar_servicio(
    pacientes_ids["Ana"], None, None, profesionales_ids["Julián"], "Interdiaria",
    hoy.isoformat(), None, "10:00", "11:00", "Terapia respiratoria por EPOC",
    usuario=1, actividad_id=act["Terapia Respiratoria"], numero_sesiones=3,
)
visitas_terapia = listar_visitas_de_servicio(resultado_terapia["servicio_id"])
programar_visita(visitas_terapia[0]["id"], hoy.isoformat(), "10:00", "11:00", profesionales_ids["Julián"], usuario_id=1)
print(f"[OK] Terapia respiratoria para Ana: {len(visitas_terapia)} sesiones (1 programada para hoy)")

# --- Enfermería para Sofía (traqueostomía): 4 sesiones, renovación automática activada ---
resultado_enfermeria = asignar_servicio(
    pacientes_ids["Sofía"], None, None, profesionales_ids["Laura"], "Diaria",
    hoy.isoformat(), None, "07:00", "08:00", "Cuidado y aseo de traqueostomía",
    usuario=1, actividad_id=act["Visita de enfermería profesional"], numero_sesiones=4,
    renovacion_automatica=True,
)
visitas_enfermeria = listar_visitas_de_servicio(resultado_enfermeria["servicio_id"])
programar_visita(visitas_enfermeria[0]["id"], hoy.isoformat(), "07:00", "08:00", profesionales_ids["Laura"], usuario_id=1)
print(f"[OK] Enfermería para Sofía: {len(visitas_enfermeria)} sesiones (1 programada para hoy, renovación automática activada)")

# --- Cuidado básico para María: 3 sesiones, ninguna programada aún (para el panel de alertas) ---
resultado_cuidado = asignar_servicio(
    pacientes_ids["María"], None, None, profesionales_ids["Marta"], "Diaria",
    manana, None, "08:00", "16:00", "Acompañamiento y cuidado básico",
    usuario=1, actividad_id=act["Curaciones"], numero_sesiones=3,
)
print(f"[OK] Cuidado básico para María: 3 sesiones creadas, TODAS pendientes de programar (para el panel de alertas)")

# ==========================================
# PLANTILLAS DE NOTA DE EJEMPLO (por rol)
# ==========================================

from services.plantillas_visita_service import crear_plantilla

crear_plantilla("Nota estándar de enfermería", "General", "", "Enfermero",
                 "Paciente consciente, orientado, signos vitales dentro de rango normal. "
                 "Sin novedades durante la visita. Se brindan recomendaciones de cuidado.",
                 None, True, 1)
crear_plantilla("Nota estándar de curación", "General", "", "Curaciones",
                 "Se realiza curación con técnica estéril. Herida en buen proceso de cicatrización, "
                 "sin signos de infección (eritema, calor, secreción purulenta). Se aplica apósito.",
                 None, True, 1)
crear_plantilla("Nota de cuidador - turno completo", "General", "", "Cuidador",
                 "Turno de (00:00) a (00:00). Paciente en compañía de acompañante. "
                 "Se administró alimentación por vía oral, cambios de posición cada 2 horas, "
                 "higiene y cambio de pañal según necesidad. Sin novedades.",
                 None, True, 1)
crear_plantilla("Nota de aplicador - medicamento IV", "General", "", "Aplicador",
                 "Se administra medicamento según orden médica, vía intravenosa, sin reacciones adversas. "
                 "Se verifica identificación del paciente y medicamento antes de la aplicación.",
                 None, True, 1)
crear_plantilla("Nota de terapia respiratoria", "General", "", "Terapeuta",
                 "Se realizan ejercicios de terapia respiratoria: nebulización, ejercicios de expansión "
                 "torácica y drenaje postural. Paciente con buena tolerancia, saturación estable durante la sesión.",
                 None, True, 1)
crear_plantilla("Nota médica de control", "General", "", "Médico",
                 "Paciente en control por consulta domiciliaria. Signos vitales estables. "
                 "Se revisa adherencia al tratamiento farmacológico y evolución clínica. Se ajusta plan de manejo.",
                 None, True, 1)

print("[OK] 6 plantillas de nota predefinidas creadas (una por perfil)")

# ==========================================
# SIGNOS VITALES DE EJEMPLO
# ==========================================

from services.signos_vitales_service import crear_signos_vitales

crear_signos_vitales(pacientes_ids["Carlos"], "Laura Gómez", hoy.isoformat(), "09:00",
                       36.7, 138, 88, 78, 18, 97, 105, 78, 1.72, 1, "Paciente estable", 1)
crear_signos_vitales(pacientes_ids["Ana"], "Julián Díaz", ayer, "10:30",
                       36.5, 125, 82, 82, 22, 93, 90, 60, 1.55, 2, "Saturación ligeramente baja por EPOC, dentro de lo esperado", 1)

print("[OK] Signos vitales de ejemplo registrados")

# ==========================================
# CONSENTIMIENTO INFORMADO DE EJEMPLO
# ==========================================

from services.consentimientos_service import generar_texto_ingreso_programa, crear_consentimiento, firmar_consentimiento
from database.database import consultar_uno as _consultar_uno

paciente_sofia = dict(_consultar_uno("SELECT * FROM pacientes WHERE id=?", (pacientes_ids["Sofía"],)))
texto_consentimiento = generar_texto_ingreso_programa(paciente_sofia, programa_alta_traqueo["nombre"])
consentimiento_id = crear_consentimiento(pacientes_ids["Sofía"],
                                           "Ingreso al Programa de Atención Domiciliaria",
                                           texto_consentimiento, 1)
firmar_consentimiento(consentimiento_id, "Acudiente/Responsable", "Patricia Martínez",
                        "1000222333", "Madre", FIRMA_EJEMPLO)

print("[OK] Consentimiento informado de ejemplo generado y firmado")

# ==========================================
# FOTO DE PROCEDIMIENTO DE EJEMPLO
# ==========================================

from services.fotos_procedimientos_service import subir_foto

subir_foto(pacientes_ids["Luis"], "Úlcera en talón derecho - antes de la curación",
           FOTO_EJEMPLO, profesionales_ids["Laura"], 1)

print("[OK] Foto de procedimiento de ejemplo subida")

# ==========================================
# INSUMOS E INVENTARIO DE EJEMPLO
# ==========================================

from services import inventario_service as inv

proveedor_id = inv.crear_proveedor("Distribuidora Médica del Quindío S.A.S.", "900123456-7",
                                     "Pedro Gómez", "3001112233", "ventas@dmq-prueba.test", "Cll 10 # 5-20, Armenia")
gasas_id = inv.crear_insumo("Gasas estériles", "Curación", "Paquete", 10)
guantes_id = inv.crear_insumo("Guantes de nitrilo", "Protección personal (EPP)", "Caja", 5)
sueros_id = inv.crear_insumo("Solución salina 0.9% 500ml", "Sueros y soluciones", "Bolsa", 8)

inv.registrar_entrada(gasas_id, 50, proveedor_id, "FAC-0001", 3500, "Compra inicial de prueba", 1)
inv.registrar_entrada(guantes_id, 20, proveedor_id, "FAC-0001", 25000, "Compra inicial de prueba", 1)
inv.registrar_entrada(sueros_id, 15, proveedor_id, "FAC-0002", 4200, "Compra inicial de prueba", 1)
inv.registrar_salida(gasas_id, 15, pacientes_ids["Luis"], profesionales_ids["Laura"],
                       "Curación de úlcera en talón", 1)

print("[OK] Proveedor, 3 insumos y movimientos de inventario de ejemplo creados")

# ==========================================================
# CONFIGURACIÓN DE LA EMPRESA (para que los reportes
# impresos ya salgan con datos de ejemplo)
# ==========================================================

from services import configuracion_empresa_service

configuracion_empresa_service.guardar({
    "razon_social": "HomeCare del Quindío I.P.S. S.A.S.",
    "nit": "901540816-1",
    "resolucion_habilitacion": "Resolución 001234 de 2024 - Habilitación de Servicios de Salud",
    "direccion": "Cra 14 # 20-35, Oficina 302",
    "ciudad": "Armenia", "departamento": "Quindío",
    "telefono": "(6) 6001122", "correo": "contacto@homecaredelquindio.test",
    "representante_legal": "Sandra Milena Osorio",
})

print("[OK] Configuración de la empresa de ejemplo guardada (aparece en los reportes impresos)")

print("\n" + "=" * 60)
print("BASE DE DATOS DE PRUEBA GENERADA CORRECTAMENTE")
print("=" * 60)

print("""
CREDENCIALES PARA INICIAR SESIÓN (todas con contraseña: prueba123)

  admin      -> Administrador (acceso total)
  dcastano   -> Administrativo (crea pacientes, agenda visitas)
  amperez    -> Andrés Pérez (Médico General)
  lgomez     -> Laura Gómez (Enfermero)
  jdiaz      -> Julián Díaz (Fisioterapeuta)
  mruiz      -> Marta Ruiz (Cuidador)
  slopez     -> Sara López (Psicólogo)
  drincon    -> Diego Rincón (Nutricionista)

PACIENTES CREADOS (con distintos escenarios para probar cada pantalla):

  Carlos Ramírez  (CC 1094777001) - alergia grave, diagnóstico de HTA, con acudiente
  Sofía Martínez  (TI 1094777002) - menor de edad, traqueostomía, programa Alta Complejidad,
                                    enfermería programada para HOY con renovación automática
  Ana Torres      (CC 1094777003) - EPOC, terapia respiratoria programada para HOY
  Luis Pérez      (CC 1094777004) - úlcera, 5 sesiones de curación:
                                    2 YA COMPLETADAS con informe y firma (revisar Historia Clínica),
                                    1 nota aclaratoria de ejemplo (corrige el informe N.° 1 —
                                    pruebe "Imprimir este informe" en ambos),
                                    1 programada a futuro, 2 SIN PROGRAMAR (para ver la alerta
                                    del dashboard), con foto de procedimiento subida
  María González  (CC 1094777005) - 3 sesiones de cuidado, TODAS sin programar
                                    (para ver la alerta del dashboard)
  Jorge Salazar   (CC 1094777006) - paciente sin servicios asignados aún (para probar
                                    la asignación desde cero)

Además: 6 plantillas de nota (una por perfil), 1 consentimiento informado firmado,
1 proveedor con 3 insumos y movimientos de inventario de ejemplo.
""")
