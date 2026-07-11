# Mapa de Módulos — HomeCare Enterprise (referencia técnica)

Documento de referencia para continuar el desarrollo. Cada módulo lista: tablas de base de datos, repositorio, servicio, router, y plantillas principales. La arquitectura sigue siempre el mismo patrón por capas:

```
Router (routers/*.py)        → recibe la petición HTTP, valida permisos, arma el contexto
    ↓
Service (services/*.py)      → lógica de negocio, validaciones, reglas
    ↓
Repository (repositories/*.py) → acceso puro a la base de datos (SQL)
    ↓
Database (database/*.py)     → conexión SQLite, esquema, migraciones
```

Al agregar un módulo nuevo, seguir siempre este mismo orden: 1) esquema + migración, 2) repositorio, 3) servicio, 4) router, 5) plantillas web, 6) equivalente en `static/pwa/app.js` si aplica a la app móvil.

---

## Pacientes
- **Tablas:** `pacientes`
- **Repositorio:** `repositories/pacientes_repository.py`
- **Servicio:** `services/pacientes_service.py` (auto-crea la "Visita de valoración médica inicial" al guardar)
- **Router:** `routers/pacientes.py` (filtra por profesional asignado según el rol)
- **Plantillas:** `templates/pacientes/`

## Usuario/Profesional (unificado)
- **Tablas:** `profesionales`, `usuarios`
- **Repositorios:** `repositories/profesionales_repository.py`, `repositories/usuarios_repository.py`
- **Servicio:** `services/profesionales_service.py` (`crear_con_cuenta_acceso`, `gestionar_cuenta_acceso`)
- **Router:** `routers/profesionales.py`
- **Plantillas:** `templates/profesionales/`

## Programas de Atención
- **Tablas:** `programas_atencion`, `paciente_programas`
- **Servicio:** `services/programas_atencion_service.py` (`asignar_programa_con_actividades`)
- **Router:** `routers/programas_atencion.py`

## Servicios Asignados / Gestión de Visitas
- **Tablas:** `servicios_paciente`, `planilla_visitas`, `programaciones`
- **Servicios:** `services/servicios_paciente_service.py`, `services/gestion_visitas_service.py` (`programar_visita`, `reprogramar_visita`, `cancelar_visita`), `services/programacion_service.py` (`crear_visita`, `registrar_ingreso`, `registrar_salida`, `crear_programacion_mensual`)
- **Routers:** `routers/servicios_paciente.py`, `routers/gestion_visitas.py`, `routers/programacion.py`
- **Importante:** `agenda_profesional()` en `programacion_repository.py` excluye visitas `Cancelada` de la verificación de choque de horario (no de la vista de calendario).

## Turnos (Cuidadores)
- **Tablas:** `catalogo_turnos`, `turnos_programados` (vinculada a `programaciones` vía `programacion_id`)
- **Servicio:** `services/turnos_service.py` (`asignar_turno_paciente` crea también la `programacion` real — no solo el turno)
- **Router:** `routers/turnos.py`

## Sugerencia de reparto entre médicos
- **Servicio:** `services/sugerencia_medico_service.py` (`sugerir_medicos` — ordena por carga actual, menos a más)

## Zonas de la ciudad
- **Catálogo fijo:** `core/zonas.py` (`ZONAS_CIUDAD`)
- Campo `zona_ciudad` en `pacientes`

## Historia Clínica (línea de tiempo consolidada)
- **Servicio:** `services/historia_clinica_service.py` (`obtener_linea_tiempo` — junta evoluciones, signos vitales, examen físico, recomendaciones, laboratorio, en orden de fecha)
- **Router:** `routers/historia_clinica.py`

## Evoluciones / Notas
- **Tablas:** `evoluciones`
- **Servicio:** `services/evoluciones_service.py`
- **Plantillas de nota predefinidas:** `services/plantillas_visita_service.py`, tabla `plantillas_visita`

## Signos Vitales y Tallas
- **Tablas:** `signos_vitales` (incluye peso, talla, IMC, temperatura — no solo signos vitales clásicos)
- **Router:** `routers/signos_vitales.py`

## Examen Físico
- **Tablas:** `examen_fisico` (columnas por sistema: cabeza, cara, boca, cuello, torax, abdomen, extremidades, vascular, neurologico, columna)
- **Servicio:** `services/examen_fisico_service.py`
- **Router:** `routers/examen_fisico.py`

## Recomendaciones / Plan Médico
- **Tablas:** `recomendaciones_medicas` (diagnóstico ppal + 3 relacionados vía CIE-10, tipo de consulta, incapacidad/nota aclaratoria/órdenes)
- **Servicio:** `services/recomendaciones_service.py`
- **Router:** `routers/recomendaciones.py`
- **Búsqueda CIE-10:** `GET /api/cie10?buscar=...` (`routers/api_cie10.py`)

## Alergias y Antecedentes
- **Tablas:** `alergias`, `antecedentes`
- **Servicios:** `services/alergias_service.py`, `services/antecedentes_service.py`
- **Routers:** `routers/alergias.py`, `routers/antecedentes.py`

## Laboratorio Clínico
- **Tablas:** `laboratorios_resultados`, `laboratorio_items`, `catalogo_examenes_laboratorio`, `catalogo_parametros_laboratorio`
- **Servicios:** `services/laboratorios_service.py`, `repositories/catalogo_examenes_laboratorio_repository.py` (interpretación automática Alto/Bajo/Normal en `agregar_item`)
- **Router:** `routers/laboratorios.py`

## Órdenes Médicas
- **Tablas:** `ordenes_medicas`
- **Servicio:** `services/ordenes_service.py` (`crear_y_enviar` — genera PDF y envía por WhatsApp/correo)
- **Router:** `routers/ordenes_medicas.py`

## Facturación
- **Tablas:** `facturas_electronicas` (incluye campos de cartera: `estado_cartera`, `fecha_vencimiento`, `fecha_pago`, `valor_pagado`)
- **Servicio:** `services/facturacion_service.py` (`generar_factura_servicio`, `marcar_pagada`, `anular_factura`, `pendientes_facturar`, `dashboard_facturacion`)
- **Router:** `routers/facturacion.py` (raíz = dashboard, `/listado`, `/cartera`, `/pendientes-facturar`, `/reportes`)
- **XML/PDF:** `core/facturacion_ubl.py` — CUFE es referencia LOCAL, no validado por la DIAN (ver `docs/FACTURACION_ELECTRONICA.md`)

## Nómina
- **Tablas:** `cargos`, `contratos`, `nomina`, `nomina_detalle`, `nomina_electronica`
- **Servicios:** `services/nomina_service.py` (liquidación con recargos legales), `services/contratos_service.py` (`liquidacion_prestacional`, `firmar_contrato`)
- **Parámetros legales:** `core/nomina/parametros_legales.py` — **revisar cada año** (SMLV, auxilio de transporte cambian)

## Calidad
- **Tablas:** `calidad_pqr`, `calidad_planificacion`, `calidad_evaluaciones`
- **Servicio:** `services/calidad_service.py`
- **Router:** `routers/calidad.py`

## Informes
- **Servicio:** `services/informes_service.py`, `services/informes_excel_service.py` (usa openpyxl)
- **Router:** `routers/informes.py` — panel central que enlaza a los reportes de cada módulo

## Firma remota por QR
- **Tablas:** `solicitudes_firma`
- **Servicio:** `services/solicitudes_firma_service.py` (`TIPOS_VALIDOS = ("planilla_visita", "consentimiento", "contrato")`)
- **Router:** `routers/firma_remota.py` — rutas públicas a propósito (sin sesión)
- **Componente reutilizable:** `templates/components/modal_firma_qr.html` (`abrirFirmaQR(tipo, referenciaId, callback)`)

## Catálogos (DIVIPOLA, CUPS, CUM, CIE-10, EPS, Bancos)
- **Repositorio central:** `repositories/catalogos_repository.py`
- **DIVIPOLA** tiene gestión completa (crear/editar código postal): `routers/catalogos.py` → `/catalogos/ciudades`
- **Desplegables en cascada Departamento→Municipio:** patrón usado en `pacientes/nuevo.html`, `pacientes/editar.html`, `profesionales/nuevo.html`, `profesionales/editar.html` — reutilizar este mismo patrón para cualquier formulario nuevo que necesite ubicación.

## Configuración de la Empresa
- **Tablas:** `configuracion_empresa`
- **Router:** `routers/configuracion_empresa.py` — incluye el botón de Reiniciar Base de Datos (`services/reinicio_service.py`), restringido al rol exacto "Administrador"

## App Móvil (PWA)
- **Frontend:** `static/pwa/app.js` (un solo archivo, todas las pantallas), `static/pwa/index.html`, `static/pwa/sw.js` (Service Worker — usa estrategia "red primero", con número de versión que hay que subir en cada actualización)
- **API:** `routers/api_movil.py` — TODAS las peticiones de paciente pasan por `verificar_acceso_paciente_movil()` (control de acceso)
- **Sincronización offline:** `_procesar_accion()` en `api_movil.py` despacha cada tipo de acción encolada desde el celular

## Seguridad
- **Clave de sesión:** generada por instalación en `core/config/settings.py` (`_obtener_o_generar_secret_key`), archivo `instancia_secret_key.txt` (nunca se versiona)
- **Bloqueo por intentos fallidos:** `services/auth_service.py` (5 intentos, 15 minutos)
- **Rate limiting:** `middleware/rate_limit.py`
- **Control de acceso a nivel de aplicación** (no hay RLS real — SQLite no lo soporta): filtros por profesional asignado en `routers/pacientes.py` y `verificar_acceso_paciente_movil()`

## Reinicio de Base de Datos
- **Script standalone (borra el archivo, requiere programa cerrado):** `reiniciar_base_datos.py`
- **Desde la web (con el servidor corriendo, vacía tablas por SQL):** `services/reinicio_service.py`
