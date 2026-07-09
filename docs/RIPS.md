# RIPS (Registro Individual de Prestación de Servicios de Salud)

Marco normativo vigente: **Resolución 948 de 2026** (14 de mayo de 2026),
que deroga la Resolución 2275 de 2023 y sus modificatorias (558 y 1884 de
2024). La arquitectura de datos (transacción → usuarios → servicios) se
mantiene igual a la introducida en 2023; lo que cambia son las reglas de
validación (más estrictas desde el 1 de junio y el 1 de julio de 2026) y
la incorporación del CUCON (Código Único de Contrato).

## Qué genera HomeCare Enterprise hoy

`services/rips_service.py` (`RIPSService.generar`) consolida, para un
rango de fechas:

- Las visitas domiciliarias completadas (`programaciones` con
  `estado='Completada'`) → objeto `consultas`.
- El diagnóstico más reciente de cada paciente → `codDiagnosticoPrincipal`.
- Los medicamentos activos o formulados en el periodo → objeto
  `medicamentos`.

Y arma el archivo `transacción` completo en JSON, descargable desde
`/rips`. El sistema también **detecta y lista los campos obligatorios
que falten** (código CUPS, código CUM, código DIVIPOLA del municipio,
etc.) antes de que el usuario intente radicar el archivo.

## Qué NO hace (y por qué)

1. **No transmite el RIPS al Ministerio.** La radicación real requiere:
   - Una **Factura Electrónica de Venta (FEV)** en XML/UBL, validada
     previamente por la DIAN.
   - El contrato con cada pagador (EPS, ARL, etc.) registrado en el
     **SIIFA**, que genera el **CUCON** (Código Único de Contrato, 64
     caracteres SHA-256) exigido por la Resolución 948 de 2026.
   - Credenciales del prestador ante el **Mecanismo Único de
     Validación (MUV)** del Ministerio.

   Ninguno de estos tres requisitos es algo que el software pueda
   resolver por sí solo: son trámites que la IPS debe adelantar
   (registro de contratos, habilitación como facturador electrónico,
   etc.). El sistema deja el archivo listo para ese paso.

2. **No incluye módulo de facturación.** El proyecto no tenía ningún
   desarrollo de facturación (`routers/facturacion.py` y
   `repositories/facturacion_repository.py` estaban vacíos). Por eso
   `numFactura` y los valores monetarios de cada servicio deben
   diligenciarse manualmente por ahora (`valor_servicio` en la
   programación de cada visita).

3. **Los catálogos de códigos (tipoUsuario, finalidad de consulta, tipo
   de diagnóstico, causa externa, etc.) están en
   `core/rips/catalogos.py` con los valores históricamente publicados
   por el Ministerio, pero marcados explícitamente como
   "⚠ VERIFICAR".** Desde la Resolución 948 de 2026, estas tablas se
   publican como *Documentos Técnicos* en el micrositio de facturación
   electrónica del SISPRO y pueden cambiar sin una nueva resolución.
   **Antes de usar este generador en producción, se debe contrastar
   cada catálogo contra la versión vigente publicada allí.**

4. **CIE-11**: se agregó la columna `codigo_cie11` en `diagnosticos`
   para cuando el Ministerio active su exigibilidad (prevista, según
   la resolución, a partir del 1 de julio de 2026), pero el sistema
   sigue capturando y reportando CIE-10 como código principal.

## Catálogos oficiales (actualización)

- **DIVIPOLA**: cargado **completo y real** (1.122 municipios, 33
  departamentos), descargado directamente de la fuente oficial del DANE
  (`datos.gov.co`, dataset "DIVIPOLA - Códigos municipios"). Se siembra
  automáticamente al iniciar el sistema (`core/bootstrap.py`) y queda
  disponible para autocompletado en el formulario de pacientes.
- **CUPS**: solo se incluyó un **lote inicial ilustrativo** (26 códigos
  comunes en atención domiciliaria), marcado explícitamente como no
  verificado contra el listado vigente (Resolución 2706 de 2025). Use
  el panel `/catalogos` para importar el archivo oficial completo en
  CSV.
- **CUM**: se incluyó un lote inicial de medicamentos frecuentes **sin
  número de CUM** (con marcadores `PENDIENTE-CUM-NNN`), porque no hay
  forma de verificar códigos reales del INVIMA sin acceso a su
  registro. Cárguelo completo desde `/catalogos`.

Las búsquedas (DIVIPOLA, CUPS, CUM) son insensibles a tildes y a orden
de palabras (buscar "consulta enfermeria" encuentra "Consulta de
primera vez por enfermería").

## Qué datos hay que empezar a diligenciar ahora
Para que el RIPS generado no tenga campos vacíos, cada visita
domiciliaria y cada medicamento formulado deberían incluir:

- **Código CUPS** de la visita/procedimiento (`programaciones.codigo_cups`).
- **Valor del servicio** (`programaciones.valor_servicio`).
- **Finalidad de la tecnología en salud** (`programaciones.finalidad_tecnologia_salud`).
- **Código CUM** de cada medicamento (`medicamentos.codigo_cum`).
- **Código DIVIPOLA** del municipio de residencia de cada paciente
  (`pacientes.codigo_municipio_divipola`) — hoy solo se guarda el
  nombre del municipio, no el código oficial de 5 dígitos.

El panel `/rips` avisa exactamente qué le falta a cada registro antes
de generar el archivo.
