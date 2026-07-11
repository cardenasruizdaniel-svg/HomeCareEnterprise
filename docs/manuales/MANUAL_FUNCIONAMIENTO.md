# Manual de Funcionamiento — HomeCare Enterprise

**Para quién es este manual:** cualquier persona del equipo, sin importar qué tanto sepa de computadores. Cada módulo se explica con palabras simples, con ejemplos de la vida diaria de la IPS.

**Cómo está organizado:** los módulos aparecen en el orden en el que normalmente se usan día a día — desde que llega un paciente nuevo, hasta que se le factura el servicio.

> Antes de usar el sistema por primera vez, alguien debe haber hecho el **Manual de Parametrización** (catálogos, empresa, usuarios). Este manual asume que eso ya está hecho.

---

## 1. Iniciar sesión

Al abrir el programa (en el navegador o en el acceso directo del escritorio), va a pedir **usuario** y **contraseña**. Cada persona del equipo tiene su propia cuenta — nunca compartan usuario, porque el sistema registra quién hizo cada cosa (quién programó una visita, quién registró una nota, etc.) y eso es importante para la trazabilidad de la historia clínica.

Si se equivoca la contraseña 5 veces seguidas, la cuenta se bloquea por 15 minutos por seguridad — es normal, solo hay que esperar.

---

## 2. El Dashboard (pantalla de inicio)

Es la primera pantalla que se ve al entrar. Muestra un resumen general: cuántos pacientes hay activos, visitas del día, alertas importantes. Es solo para "ver de un vistazo" — no se edita nada aquí.

---

## 3. Pacientes

**Qué es:** la lista de todas las personas que la IPS atiende (o atendió) en su casa.

**Cómo se usa:**
- **Nuevo Paciente**: se llena la ficha completa (documento, EPS, dirección, zona de la ciudad, tipo de cuidado). Al guardar, automáticamente queda pendiente su primera visita de valoración médica.
- **Buscar un paciente**: use la barra de búsqueda (por nombre o documento).
- **Ficha del paciente**: al hacer clic en un paciente, se abre su ficha completa con botones de acceso rápido a: Historia Clínica, Signos Vitales, Examen Físico, Recomendaciones, Alergias, Antecedentes, Laboratorio, Servicios Asignados, Programa de Atención.

> **Importante:** si usted tiene un rol clínico (médico, enfermero, cuidador, terapeuta), solo va a ver los pacientes que tiene asignados — no toda la lista. Esto es intencional, para proteger la privacidad de los pacientes de otros profesionales.

**Pendientes de Agendar**: dentro del menú de Pacientes hay un enlace a esta pantalla, que muestra quién todavía no tiene su primera visita programada, y quién tiene sesiones sin programar — organizado también por zona de la ciudad, para agendar juntos a los pacientes de un mismo sector.

---

## 4. Programas de Atención

**Qué es:** el "paquete" de servicios que un paciente va a recibir (ej. Programa Crónico con Terapias). Se asigna generalmente en la primera visita médica, junto con las actividades específicas (cuántas sesiones de terapia al mes, etc.).

---

## 5. Servicios Asignados y Programación de Visitas

**Qué es:** una vez el paciente tiene su programa, aquí se ve el detalle de cada servicio (frecuencia, profesional asignado, cuántas sesiones ya están programadas y cuántas faltan).

- **Programar Visitas**: le pone fecha y hora a cada sesión pendiente. Si el servicio es médico, el sistema sugiere a qué médico asignarle (repartiendo la carga entre todos, no siempre al mismo).
- **Programación Mensual**: para cuidadores con horario variable (pueden trabajar días y horas distintas, con distintos pacientes) — se arma de una vez el mes completo, y automáticamente queda reflejado en Servicios Asignados y en la agenda de la app.
- Al programar, revise la **zona de la ciudad** del paciente — trate de agrupar en el mismo día visitas de la misma zona, para no cruzar la ciudad de un lado a otro.

---

## 6. Agenda / Calendario

Vista de calendario de todas las visitas programadas, por profesional o general. Aquí también se puede **cancelar** o **reprogramar** una visita si el paciente no puede recibirla ese día.

---

## 7. La App Móvil (para el personal de campo)

El personal que visita pacientes en su casa (médicos, enfermeros, terapeutas, cuidadores) usa la app desde su celular, no la web.

**Cómo entra:** con el mismo usuario y contraseña del sistema.

**Su agenda del día:** puede ver su agenda por Día, Semana o Mes, con flechas para navegar.

**Al llegar donde el paciente:**
1. **Registrar ingreso** — toma una foto (que queda con la ubicación GPS marcada encima) y el sistema verifica que de verdad está en la casa del paciente. Si el paciente no tiene ubicación registrada todavía (primera visita), no bloquea — el médico la registra ahí mismo.
2. Mientras el turno está abierto, la app vigila la ubicación — si el profesional se aleja mucho de la casa, cierra el turno solo.
3. Al terminar: **Finalizar labores**, con otra foto/ubicación.

**Qué puede hacer un Cuidador en la app** (menú simplificado a propósito): registrar entrada/salida, ver historia clínica y alergias del paciente, registrar su informe de cuidador, firmar la planilla de visita, y programar su propia agenda.

**Qué puede hacer un profesional de la salud (médico, enfermero, terapeuta, etc.):** todo lo del cuidador, más: signos vitales y tallas, examen físico, recomendaciones/plan médico, alergias, antecedentes, órdenes médicas, resultados de laboratorio, última nota médica, y asignar el Programa de Atención.

---

## 8. Historia Clínica

Cada visita/nota que se registra (desde la web o desde la app) queda reflejada en una sola **línea de tiempo** por paciente, ordenada de la más reciente a la más antigua. Ahí se ven juntos: notas de evolución, signos vitales, examen físico, recomendaciones, resultados de laboratorio, alergias y antecedentes — todo en un solo lugar, para que cualquier profesional que atienda al paciente entienda su historia completa.

- **Signos Vitales y Tallas**: presión, frecuencia cardíaca/respiratoria, saturación, glucemia, peso, talla (con IMC calculado solo), temperatura.
- **Examen Físico**: por sistemas — cabeza, cara, boca, cuello, tórax, abdomen, extremidades, vascular, neurológico, columna (igual al formato que ya manejaba la IPS en papel/PDF).
- **Recomendaciones / Plan médico**: diagnóstico principal + hasta 3 relacionados (buscados del catálogo oficial CIE-10), tipo de consulta, y las casillas de incapacidad/nota aclaratoria/orden de medicamentos/orden de procedimientos.
- **Laboratorio**: elija el examen de un catálogo con parámetros y rangos normales ya listos (Hemograma, Parcial de orina, etc.) — solo hay que escribir el valor obtenido, y el sistema dice solo si quedó alto, bajo o normal.

---

## 9. Órdenes Médicas

El médico genera una orden (medicamento, examen, remisión, procedimiento) y el sistema la envía automáticamente al paciente por WhatsApp/correo con el PDF adjunto — desde la web o desde la app en la misma visita.

---

## 10. Facturación

**Dashboard de Facturación** (pantalla principal del módulo): muestra de un vistazo cuánto se ha facturado, cuánto se ha cobrado, cuánto está pendiente y cuánto está vencido, con un gráfico por mes.

- **Pendientes de Facturar**: lista automática de servicios ya prestados (con ingreso y salida reales) que todavía no se han facturado — para no dejar nada sin cobrar.
- **Cartera**: cada factura queda con estado Pendiente de pago, Vencida (automático, a los 30 días) o Pagada. Desde aquí se registra cuándo y cómo pagó el paciente/EPS, o se anula una factura si hubo un error.
- **Reportes**: facturado por paciente, por EPS, y por rango de fechas — todos exportables a Excel.

---

## 11. Nómina

Se liquida por periodo (quincenal/mensual), calculando automáticamente horas trabajadas (con sus recargos nocturnos/dominicales/festivos según la ley), y — para quienes tienen vinculación Laboral — también las prestaciones sociales (cesantías, prima, vacaciones) y los aportes patronales, mostrando el costo total real para la empresa antes de generar la nómina electrónica para la DIAN.

---

## 12. Calidad

- **PQR / Solicitudes**: quejas, peticiones, reclamos, con responsable asignado y respuesta.
- **Planificación de trabajo**: tareas del equipo con fecha límite.
- **Evaluación de la atención**: calificación de 1 a 5 de la atención recibida por cada paciente.

---

## 13. Informes

Panel central con todos los reportes del sistema: Caracterización de Pacientes, Resumen por Zona/Municipio/EPS, Equipo Profesional, Facturación, Nómina, Calidad, Pendientes de Agendar, Cronograma Mensual. Todos se pueden ver en pantalla, imprimir, y descargar en Excel.

---

## 14. Catálogos y Configuración

Para uso ocasional — agregar una EPS nueva, un municipio que falte, ajustar un turno, o cambiar los datos de la empresa. Ver el **Manual de Parametrización** para el detalle de cada catálogo.
