# Manual de Configuración Legal — HomeCare Enterprise

**Para quién es este manual:** el Administrador de la IPS, para dejar todos los trámites legales configurados en el sistema **antes de operar con pacientes reales**.

**Dónde se configura:** Menú lateral → **Configuración Legal** (`/configuracion-legal`). Es una sola pantalla, dividida en secciones por cada entidad del gobierno. Cada sección tiene un semáforo (Completo/Pendiente) para saber de un vistazo qué falta.

> **Importante:** diligenciar estos campos en el sistema **no tramita nada automáticamente ante el gobierno**. Cada entidad tiene su propio proceso de solicitud (presencial, en línea, o a través de un proveedor autorizado) — este manual le dice **dónde conseguir cada dato**, y la pantalla del sistema es donde **guarda esos datos** una vez los tenga, para que el sistema los use correctamente en los documentos que genera (facturas, RIPS, nómina).

---

## 1. REPS — Habilitación en Salud

**Quién lo exige:** la Secretaría de Salud Departamental o Distrital (delegada por el Ministerio de Salud).
**Qué es:** el Registro Especial de Prestadores de Servicios de Salud — es el permiso legal para operar como IPS. Sin este registro, la IPS no puede prestar servicios de salud legalmente, sin importar qué tan bien funcione el software.

**Cómo se obtiene:**
1. Se radica en el aplicativo REPS (`reps.minsalud.gov.co`) o directamente en la Secretaría de Salud de su departamento.
2. Se presentan los documentos de la IPS (cámara de comercio, infraestructura, talento humano, etc. — el checklist completo lo da la Secretaría de Salud).
3. Al aprobarse, entregan un **código de habilitación** y una **resolución de habilitación**.

**Qué diligenciar en el sistema:**
- Código de habilitación (REPS).
- Número de la resolución de habilitación.
- Fecha de habilitación.
- Fecha de vigencia (si aplica renovación periódica).

---

## 2. RIPS — Registro Individual de Prestación de Servicios de Salud

**Quién lo exige:** el Ministerio de Salud, a través de SISPRO — y cada EPS con la que la IPS tenga contrato.
**Qué es:** el reporte técnico de cada servicio prestado (consulta, medicamento, procedimiento) que se le envía a la EPS para poder cobrarle, y al Ministerio para las estadísticas nacionales de salud.

**Cómo se obtiene:**
- El **código de prestador** y el **NIT** salen del mismo proceso de habilitación REPS (numeral 1) — no es un trámite aparte.
- Cada EPS, además, puede pedir un usuario/clave propios para subir los RIPS a su portal (esto varía por EPS, y no es un dato único a nivel nacional — pregúntele al área de facturación de cada EPS con la que trabaje).

**Qué diligencia en el sistema:**
- NIT del prestador.
- Código del prestador (el mismo del REPS).
- Razón social exacta (como aparece registrada en el REPS — debe coincidir exactamente).

⚠️ Ver `docs/RIPS.md` para el detalle técnico de qué genera el sistema hoy y qué falta para transmitir de verdad (spoiler: hoy genera el archivo con la estructura correcta, pero la transmisión real todavía no está conectada).

---

## 3. DIAN — Facturación Electrónica

**Quién lo exige:** la DIAN (Dirección de Impuestos y Aduanas Nacionales) — es obligatorio para poder facturar legalmente en Colombia.
**Qué es:** cada factura debe generarse en un formato XML específico (UBL 2.1), firmarse digitalmente, y ser validada por la DIAN antes de entregársela al cliente.

**Cómo se obtiene cada dato:**

| Dato | Dónde se consigue |
|------|---------|
| NIT y dígito de verificación | Es el mismo NIT de la IPS (Cámara de Comercio / RUT) |
| Resolución de facturación (número, prefijo, rango, vigencia) | Se solicita en el portal de la DIAN (`dian.gov.co` → Facturación Electrónica → Solicitud de numeración) |
| Software ID y Software PIN | Los asigna la DIAN al momento de inscribir el software de facturación (si usan un proveedor tecnológico autorizado, ese proveedor se los entrega; si la IPS factura directamente, se generan en el portal de la DIAN) |
| Certificado digital (.p12/.pfx) y su contraseña | Se compra con una entidad certificadora autorizada en Colombia (Certicámara, GSE, Andes SCD, etc.) — es el mismo tipo de certificado que se usa para firmar digitalmente cualquier documento electrónico |
| Test Set ID | Lo entrega la DIAN cuando se hace el proceso de "habilitación" (pruebas técnicas) antes de pasar a producción |
| Ambiente | "Habilitación" mientras se hacen las pruebas con la DIAN; se cambia a "Producción" solo cuando la DIAN ya aprobó las pruebas |

**Qué diligenciar en el sistema:** todos los campos de la sección "DIAN — Facturación Electrónica" en Configuración Legal.

⚠️ Ver `docs/FACTURACION_ELECTRONICA.md` — hoy el sistema genera la estructura XML correcta pero el CUFE es una referencia local, no validada por la DIAN. Diligenciar estos datos es el primer paso, pero falta la integración técnica real con los servicios web de la DIAN para transmitir de verdad.

---

## 4. DIAN — Nómina Electrónica

**Quién lo exige:** la DIAN — es obligatorio para cualquier empresa con empleados vinculados laboralmente (no aplica a quienes solo tienen contratistas por prestación de servicios).
**Qué es:** cada pago de nómina a un empleado vinculado debe reportarse a la DIAN en formato electrónico, similar a la factura de venta.

**Cómo se obtiene:** el mismo proceso que la Facturación Electrónica (numeral 3), pero es una inscripción separada — se hace también en el portal de la DIAN, sección Nómina Electrónica. Usa el mismo certificado digital que ya compró para facturación.

**Qué diligenciar en el sistema:** Software ID, Software PIN, Test Set ID y Ambiente — específicos de Nómina Electrónica (son distintos a los de Facturación, aunque el certificado digital se reutiliza).

---

## 5. UGPP / Operador PILA — Seguridad Social

**Quién lo exige:** la UGPP (Unidad de Gestión Pensional y Parafiscales), a través del sistema PILA (Planilla Integrada de Liquidación de Aportes).
**Qué es:** el pago mensual de salud, pensión, ARL y parafiscales de cada empleado vinculado laboralmente se hace a través de un "operador" autorizado (no directamente al gobierno).

**Cómo se obtiene:**
1. Se elige un operador PILA (algunos comunes: Aportes en Línea, SOI, MiPlanilla, Simple).
2. Se crea una cuenta empresarial con ese operador — ellos entregan usuario y contraseña.

**Qué diligenciar en el sistema:** el nombre del operador, usuario, y contraseña — esto es opcional y solo aplica si quiere que el sistema quede preparado para una futura integración directa con el operador (hoy el sistema calcula correctamente cuánto se debe pagar de aportes en el módulo de Nómina, pero el pago mismo se hace todavía desde el portal del operador).

---

## 6. SIC — Protección de Datos (Habeas Data)

**Quién lo exige:** la Superintendencia de Industria y Comercio, bajo la Ley 1581 de 2012.
**Qué es:** toda empresa que maneje datos sensibles (y los datos de salud SIEMPRE son sensibles) debe registrar sus bases de datos en el RNBD (Registro Nacional de Bases de Datos), y tener una política de tratamiento de datos publicada.

**Cómo se obtiene:**
1. Se registra en `rnbd.sic.gov.co`.
2. Se declara qué bases de datos maneja la IPS (pacientes, empleados, proveedores) y su finalidad.
3. La SIC entrega un número de registro.

**Qué diligenciar en el sistema:** número de registro RNBD y fecha de registro.

⚠️ Este es un trámite que conviene hacer con acompañamiento de un abogado — el sistema ya tiene el módulo de Consentimiento Informado, que es parte de lo que exige la ley, pero el registro formal ante la SIC es un trámite legal aparte que no reemplaza este software.

---

## 7. ARL — Administradora de Riesgos Laborales

**Quién lo exige:** la ley laboral colombiana — todo empleado vinculado debe estar afiliado a una ARL.
**Qué es:** el seguro de accidentes y enfermedades laborales.

**Cómo se obtiene:** se contrata directamente con una ARL (Sura, Positiva, Colmena, Bolívar, etc.) — no es un trámite ante el gobierno, sino una contratación comercial, pero es obligatoria por ley.

**Qué diligenciar en el sistema:** NIT y nombre de la ARL contratada — esto es informativo, para tenerlo a la mano en los reportes de nómina (el nivel de riesgo de cada profesional ya se configura individualmente en su ficha, en Usuario/Profesional).

---

## Resumen: orden recomendado para diligenciar todo

1. **REPS** (es el primer requisito legal — sin esto no se puede operar).
2. **RIPS** (usa los mismos datos del REPS).
3. **ARL** (contratación comercial, rápida).
4. **DIAN — Facturación Electrónica** (requiere comprar el certificado digital primero).
5. **DIAN — Nómina Electrónica** (si hay empleados vinculados laboralmente).
6. **SIC — Protección de Datos** (recomendado hacerlo con un abogado en paralelo).
7. **UGPP / Operador PILA** (solo si van a integrar el pago de seguridad social directamente).

## Aviso importante

Este software **no reemplaza asesoría legal ni contable**. Ayuda a organizar y centralizar la información que cada trámite requiere, y a generar los documentos técnicos (facturas, RIPS, nómina) con la estructura correcta — pero la responsabilidad de tramitar cada registro ante la entidad correspondiente, y de verificar que la IPS cumple con toda la normativa vigente, sigue siendo de la IPS y sus asesores legales/contables.
