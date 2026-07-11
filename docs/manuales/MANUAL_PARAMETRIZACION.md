# Manual de Parametrización — HomeCare Enterprise

**Objetivo de este manual:** dejar el sistema listo para trabajar, paso a paso, **en el orden correcto**. Cada paso depende del anterior — si se salta uno, los siguientes van a fallar o van a quedar incompletos. Este manual está pensado para hacerse **una sola vez**, al empezar a usar el sistema en una IPS nueva (o al reiniciar la base de datos antes de lanzar a producción real).

> **Regla de oro:** no se puede crear un paciente sin que existan los catálogos (EPS, ciudades, actividades). No se puede asignar un servicio sin que existan profesionales. No se puede facturar sin que la empresa esté configurada. Por eso el orden importa.

---

## PASO 1 — Configuración de la Empresa

**Dónde:** Menú lateral → **Configuración de la Empresa**
**Por qué va primero:** el nombre, NIT y logo de la IPS se usan en TODOS los documentos que el sistema genera después (historias clínicas, facturas, órdenes médicas, planillas de visita). Si se deja para después, hay que volver a generar todo lo que ya se haya creado.

Qué llenar:
1. **Razón social** (nombre legal completo de la IPS).
2. **NIT** (sin dígito de verificación separado, o como lo maneje la DIAN — este campo alimenta las facturas electrónicas).
3. **Resolución de habilitación** (el número que la Secretaría de Salud le dio a la IPS).
4. **Dirección, teléfono, correo, ciudad, departamento.**
5. **Representante legal.**
6. **Logo** (una imagen cuadrada o rectangular, PNG con fondo transparente si es posible — aparece en la barra lateral y en los documentos impresos).

✅ **Verificación:** al guardar, el logo debe verse en la esquina superior de la barra lateral.

---

## PASO 2 — Catálogo de Ciudades y Departamentos (DIVIPOLA)

**Dónde:** Menú lateral → **Catálogos** → **Gestionar ciudades / código postal**
**Por qué va aquí:** el catálogo de los 1.122 municipios de Colombia ya viene cargado de fábrica — normalmente **no hay que hacer nada en este paso**. Solo entre aquí si:
- Necesita agregar un corregimiento o vereda que no aparezca en el catálogo oficial.
- Quiere completar los códigos postales de los municipios donde la IPS realmente opera (útil para RIPS y factura electrónica, pero no obligatorio para empezar a trabajar).

✅ **Verificación:** busque el municipio principal de la IPS (ej. "Armenia") y confirme que aparece con su departamento correcto.

---

## PASO 3 — Catálogos base del negocio

**Dónde:** Menú lateral → **Catálogos**
**Por qué va aquí:** estos catálogos alimentan los formularios de Pacientes, Profesionales, Programas y Facturación. Si un dato no está en el catálogo, no se va a poder elegir en los formularios de más adelante.

En orden:

### 3.1 EPS
Verifique que estén las EPS con las que la IPS tiene convenio o atiende regularmente. Si falta alguna, agréguela (nombre + código si lo maneja).

### 3.2 Bancos
Para la nómina — verifique que estén los bancos donde los profesionales reciben su pago.

### 3.3 Catálogo de Actividades
Revise que estén las actividades/servicios que la IPS realmente presta (Cuidador, Enfermería, Terapia Física, Terapia Respiratoria, Psicología, Nutrición, Visita de valoración médica inicial, Curaciones, etc.). Agregue las que falten, desactive las que no apliquen.

### 3.4 Catálogo de Turnos
Revise los turnos predefinidos (Turno 1 partido, Turno 2 continuo, Día completo, Noche, Medio día). Ajuste los horarios si no coinciden con cómo trabaja la IPS.

### 3.5 Catálogo de Exámenes de Laboratorio
Ya viene con 11 exámenes comunes (Hemograma, Parcial de orina, Perfil lipídico, etc.) con sus parámetros y rangos normales. Solo entre aquí si necesita agregar un examen que la IPS pida seguido y no esté en la lista.

✅ **Verificación:** al ir a crear un paciente de prueba más adelante, el desplegable de EPS y el de zona deben mostrar datos.

---

## PASO 4 — Programas de Atención

**Dónde:** Menú lateral → **Programas de Atención**
**Por qué va aquí:** cada paciente se asigna a un programa (ej. "Programa Crónico Baja Complejidad"). Sin al menos un programa creado, no se puede completar la ficha de un paciente nuevo correctamente.

Cree los programas que maneje la IPS, con su nombre y una breve descripción.

---

## PASO 5 — Roles y Permisos (entender antes de crear usuarios)

**Dónde:** no se configura en pantalla — es un tema para entender antes del Paso 6.

Los roles disponibles son: **Administrador**, **Director Médico**, **Coordinador**, **Médico**, **Enfermero**, **Fisioterapeuta**, **Terapeuta Respiratorio**, **Psicólogo**, **Salud Ocupacional**, **Terapeuta**, **Nutricionista**, **Cuidador**, **Administrativo**, **Auditor**.

- **Administrador** y **Director Médico**: ven y pueden hacer todo, incluyendo el botón de Reiniciar Base de Datos (solo el Administrador exacto).
- **Coordinador** y **Administrativo**: manejan pacientes, programación, profesionales — ven TODOS los pacientes, no solo los suyos.
- Los roles clínicos (Médico, Enfermero, Cuidador, Terapeutas, etc.): solo ven los pacientes que tienen asignados.

Decida, antes de crear cuentas, quién de su equipo va a tener cada rol.

---

## PASO 6 — Crear Profesionales (con su cuenta de acceso)

**Dónde:** Menú lateral → **Usuario/Profesional** → Nuevo Profesional
**Por qué va aquí:** ya con los catálogos y los roles claros, ahora sí se crea cada persona del equipo — en un solo paso queda su ficha profesional Y su cuenta de acceso al sistema (usuario, contraseña, rol).

Para cada profesional, decida y registre:
1. **Datos personales y de contacto.**
2. **Municipio** (con el buscador en cascada Departamento → Municipio).
3. **Vinculación**: Laboral (con prestaciones sociales) o Prestación de Servicios (contratista) — esto es importante, define si la nómina le calcula cesantías/prima/vacaciones o no.
4. **Nivel de riesgo ARL** (para atención domiciliaria, generalmente nivel IV).
5. **Tipo de contrato**: Por horas o Fijo (salario mensual) — y el valor correspondiente.
6. **Cuenta de acceso**: usuario, contraseña, y el rol del sistema (ver Paso 5).

✅ **Verificación:** cierre sesión e inicie sesión con la cuenta nueva, confirmando que entra y ve el menú que le corresponde a su rol.

---

## PASO 7 — Crear Pacientes

**Dónde:** Menú lateral → **Pacientes** → Nuevo Paciente
**Por qué va aquí:** ya existen los catálogos (EPS, ciudades) y los profesionales — ahora sí se pueden crear pacientes con toda su información completa desde el principio.

Para cada paciente:
1. **Datos de identificación** completos.
2. **EPS y régimen.**
3. **Tipo de cuidado**: Ventilado (requiere Auxiliar de Enfermería) o No Ventilado (puede atenderlo un Cuidador) — esto determina qué profesional se le puede asignar después.
4. **Zona de la ciudad** — para poder programar visitas eficientemente por sector.
5. **Municipio** (buscador en cascada).
6. **Dirección y ubicación GPS** (si la conoce; si no, la primera visita del médico la registra desde la app).

> Al guardar, el sistema crea automáticamente la primera "Visita de valoración médica inicial" pendiente de programar — no hay que crearla a mano.

---

## PASO 8 — Asignar Programa y Servicios al paciente

**Dónde:** Ficha del paciente → **Programa de Atención**, y → **Servicios Asignados**
**Por qué va aquí:** después de la valoración médica inicial (que define diagnóstico, plan y servicios), se asigna el programa formal y los servicios recurrentes (terapias, curaciones, cuidador, etc.) con su frecuencia.

1. El médico, en su primera visita (desde la app o la web), asigna el **Programa de Atención** y las actividades/servicios que el paciente va a tener.
2. Desde **Servicios Asignados**, se pueden ajustar o agregar servicios manualmente si hace falta.
3. Desde **Programar Visitas** (o **Programación Mensual** para cuidadores con horario variable), se le pone fecha a cada sesión.

---

## PASO 9 — Configurar Facturación

**Dónde:** ya quedó lista en el Paso 1 (NIT, razón social) — este paso es solo para revisar antes de facturar de verdad.

Antes de generar la primera factura real, revise:
- Que el NIT y la razón social en Configuración de la Empresa sean los correctos (aparecen en cada factura).
- Que cada paciente tenga su EPS bien registrada (de ahí sale el "responsable de pago" de la cartera).

> **Importante:** las facturas que genera este sistema tienen la estructura técnica correcta (UBL 2.1), pero el CUFE es una referencia local — no están validadas por la DIAN todavía. Ver `docs/FACTURACION_ELECTRONICA.md` para lo que falta si se necesita facturación electrónica 100% oficial.

---

## PASO 10 — Nómina

**Dónde:** Menú lateral → **Nómina** → **Cargos**, luego **Contratos**
**Por qué va al final de la parametrización inicial:** depende de que los profesionales ya existan (Paso 6) con su tipo de vinculación definido.

1. Cree los **Cargos** que existan en la IPS (Fisioterapeuta, Enfermero, Auxiliar, etc.) con su salario base de referencia.
2. Cree el **Contrato** de cada profesional vinculado laboralmente, con su tipo de contrato, salario y demás datos legales.

---

## PASO 11 — Módulo de Calidad (cuando el equipo esté listo)

**Dónde:** Menú lateral → **Calidad**
No requiere parametrización previa — se puede empezar a usar (PQR, planificación de trabajo, evaluación de atención) en cualquier momento, aunque tiene más sentido activarlo cuando ya hay pacientes y operación real corriendo.

---

## PASO 12 — Antes de lanzar a producción real (últimO, no antes)

**Dónde:** Configuración de la Empresa → sección de Administrador maestro
Cuando ya terminaron todas las pruebas y van a empezar a recibir pacientes reales:

1. Use el botón **"Reiniciar base de datos ahora"** (solo visible para el Administrador maestro) — esto borra todos los pacientes, profesionales y visitas **de prueba**, pero **conserva todas las cuentas de usuario** y vuelve a sembrar los catálogos.
2. Vuelva a hacer los Pasos 6 en adelante (crear los profesionales y pacientes REALES esta vez).

⚠️ **Esta acción no se puede deshacer** — asegúrese de que de verdad terminaron las pruebas antes de usarla.

---

## Resumen del orden (para tener a la mano)

| # | Paso | Depende de |
|---|------|-----------|
| 1 | Configuración de la Empresa | — |
| 2 | Ciudades/Departamentos (revisar) | — |
| 3 | Catálogos base (EPS, bancos, actividades, turnos, exámenes) | — |
| 4 | Programas de Atención | — |
| 5 | Entender roles y permisos | — |
| 6 | Crear Profesionales + cuentas de acceso | Pasos 3, 5 |
| 7 | Crear Pacientes | Pasos 3, 6 |
| 8 | Asignar Programa y Servicios | Pasos 4, 6, 7 |
| 9 | Revisar Facturación | Paso 1, 7 |
| 10 | Nómina (Cargos + Contratos) | Paso 6 |
| 11 | Calidad (opcional) | — |
| 12 | Reiniciar BD antes de producción real | Todo lo anterior, al terminar las pruebas |
