# Interoperabilidad de la Historia Clínica Electrónica (IHCE)

Marco normativo: Ley 2015 de 2020, Resolución 866 de 2021 (conjunto de
datos clínicos relevantes) y Resolución 1888 de 2025 (adopción del
Resumen Digital de Atención en Salud — RDA — y su mecanismo de
implementación mediante HL7 FHIR R4).

## Qué implementa HomeCare Enterprise hoy

1. **Modelo de datos ampliado** (`database/migrations.py`,
   `migrar_pacientes_866`): la tabla `pacientes` incorpora los
   elementos adicionales exigidos por el anexo técnico: hora de
   nacimiento, identidad de género, pertenencia y comunidad étnica,
   país de nacimiento/residencia, zona de residencia e indicador de
   alergias. La migración es aditiva: no borra ni reemplaza datos
   existentes.

2. **Codificación de datos clínicos**: se agregaron columnas de
   codificación (`codigo_cum` en medicamentos, `codigo_alergeno` en
   alergias) para que los datos puedan representarse con
   terminologías estándar en FHIR, además del catálogo CIE-10 que
   ya existía para diagnósticos.

3. **Mapeador HL7 FHIR R4** (`core/interoperability/fhir_mapper.py`):
   convierte los registros de HomeCare a los recursos FHIR
   correspondientes: `Patient`, `Practitioner`, `Condition`
   (diagnóstico, CIE-10), `AllergyIntolerance`, `MedicationStatement`
   (CUM) y `Observation` (signos vitales, codificados en LOINC).

4. **Generador del RDA** (`services/interoperabilidad_service.py`,
   `InteroperabilidadService.generar_rda`): ensambla un `Bundle` FHIR
   con todos los recursos de un paciente. Expuesto en
   `GET /interoperabilidad/rda/{paciente_id}`.

5. **Verificación de completitud**
   (`InteroperabilidadService.verificar_completitud`): indica qué
   porcentaje del conjunto mínimo de datos clínicos relevantes tiene
   diligenciado un paciente, y qué campos obligatorios/recomendados
   faltan. Expuesto en `GET /interoperabilidad/completitud/{paciente_id}`.

## Qué queda pendiente (fuera del alcance de esta IPS)

- **Envío al mecanismo nacional de interoperabilidad**: la
  Resolución 1888 de 2025 define que el RDA se transmite a la
  plataforma del Ministerio de Salud mediante un API Gateway con
  autenticación API Key + Subscription Key. Esas credenciales las
  emite el Ministerio por solicitud formal de la IPS; el sistema ya
  genera el documento en el formato correcto, pero el "envío" en sí
  es un paso de integración que depende de que la IPS gestione el
  acceso ante el Ministerio.
- **Perfiles FHIR oficiales completos**: los recursos generados
  siguen la estructura general de FHIR R4 y el anexo técnico de la
  Resolución 866; para una validación formal contra los perfiles
  publicados por HL7 Colombia se recomienda validar el `Bundle` con
  el validador oficial cuando el Ministerio lo publique en el
  micrositio de IHCE.
- **Firma digital del profesional**: la ley exige historia clínica
  refrendada con firma digital; el sistema ya captura firma de
  profesional/paciente en algunos módulos (agenda), pero no está
  aún vinculada como firma electrónica cualificada dentro del RDA.

## Nota sobre RIPS

El RDA (HL7 FHIR, para interoperabilidad de la historia clínica) y
el RIPS en formato JSON (Resolución 2275 de 2023, para el reporte
transaccional a EPS/SISPRO) son mecanismos distintos con objetivos
distintos. Este documento cubre el primero; el RIPS JSON quedó
identificado como pendiente separado en el backlog original del
proyecto.
