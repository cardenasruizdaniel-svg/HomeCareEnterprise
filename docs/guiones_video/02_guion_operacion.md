# Guion de video 2: Operación diaria con ejemplos reales (12-15 minutos)

Dirigido a: coordinadores, médicos, enfermeros, cuidadores y personal administrativo de la IPS.

---

## Escena 1 — Introducción (0:00 - 0:30)
**Mostrar:** Dashboard principal.
**Narración:** "En este video vamos a recorrer el uso diario de HomeCare Enterprise con
ejemplos reales: crear un paciente, registrar su historia clínica, crear un profesional,
programar una visita, marcar el ingreso y la salida, generar una orden médica, y ver cómo
se calcula la nómina."

## Escena 2 — Crear un usuario (0:30 - 1:30)
**Mostrar:** Usuarios → Nuevo Usuario → llenar formulario con rol "Enfermero" → guardar.
**Narración:** "Empezamos creando la cuenta de acceso de una enfermera. Le asignamos el
rol Enfermero, que le dará acceso a historia clínica, pacientes, signos vitales,
medicamentos y agenda."

## Escena 3 — Crear un profesional y vincularlo (1:30 - 3:00)
**Mostrar:** Profesionales → Nuevo Profesional → llenar datos, incluida la sección de
Contratación (Por horas, valor $18.000/hora) → guardar → Editar → vincular la cuenta de
usuario creada en la escena anterior.
**Narración:** "Ahora registramos a esa misma enfermera como profesional del sistema.
Aquí es donde definimos cómo se le va a pagar: en este ejemplo, por horas, a $18.000 la
hora. Por último, la vinculamos con su cuenta de usuario para que pueda usar la app
móvil."

## Escena 4 — Crear un paciente (3:00 - 5:00)
**Mostrar:** Pacientes → Nuevo Paciente → llenar identificación, nombre, EPS, contacto
(celular y correo reales), y buscar el municipio en DIVIPOLA escribiendo "Armenia".
**Narración:** "Registramos un paciente nuevo. Prestemos especial atención al celular y
correo: son los datos que el sistema usará para enviarle automáticamente sus órdenes
médicas. Y aquí, en el buscador de municipio, escribimos 'Armenia' y seleccionamos el
municipio correcto — esto es clave para poder incluir después a este paciente en el
RIPS."

## Escena 5 — Registrar una alergia (5:00 - 6:00)
**Mostrar:** Ficha del paciente → Alergias → Nueva alergia → Medicamento, "Penicilina",
severidad "Grave".
**Narración:** "Registramos que este paciente es alérgico a la penicilina, con severidad
grave. Vean cómo, apenas guardamos, aparece de inmediato en la ficha del paciente un
aviso en rojo — esta alerta la va a ver cualquiera que entre a este paciente, sin
excepción."

## Escena 6 — Programar una visita (6:00 - 8:00)
**Mostrar:** Programación → Nueva Visita → buscar el paciente creado, seleccionar la
enfermera, buscar el procedimiento CUPS "consulta enfermería", indicar valor del
servicio, fecha y hora → guardar.
**Narración:** "Programamos una visita domiciliaria: seleccionamos el paciente, la
profesional, buscamos el procedimiento por su código CUPS, indicamos el valor del
servicio, y la fecha y hora. Esta visita ya queda visible en la agenda del día."

## Escena 7 — Marcar ingreso y salida (8:00 - 9:30)
**Mostrar:** Abrir el detalle de la visita, presionar "Registrar ingreso a labores"
(mostrar el permiso de ubicación del navegador), esperar unos segundos, luego "Finalizar
labores".
**Narración:** "El día de la visita, la profesional abre la visita y presiona 'Registrar
ingreso a labores' al llegar donde el paciente. El sistema pide permiso de ubicación y
guarda la hora exacta. Al terminar, presiona 'Finalizar labores'. Este tiempo real
trabajado es el que se va a usar para calcular su pago — no el horario que se programó."

## Escena 8 — Generar una orden médica (9:30 - 11:00)
**Mostrar:** Ficha del paciente → Órdenes Médicas → Nueva Orden → tipo "Medicamento",
descripción "Acetaminofén 500mg cada 8 horas por 5 días" → Generar y enviar → mostrar
el mensaje de confirmación de envío.
**Narración:** "Ahora, como si fuéramos el médico, generamos una orden de un
medicamento. Al presionar 'Generar y enviar', el sistema arma el PDF de la orden y lo
envía automáticamente al celular y correo del paciente que registramos al principio —
así el paciente puede reclamar su medicamento sin tener que venir a recogerlo en
papel."

## Escena 9 — Consultar la nómina (11:00 - 13:00)
**Mostrar:** Nómina → seleccionar fechas del periodo → Consultar tiempo y valor a pagar
→ mostrar la tabla resultante con las horas trabajadas por la enfermera y el valor
calculado.
**Narración:** "Al cierre de la quincena o del mes, entramos a Nómina, seleccionamos el
periodo, y consultamos. El sistema nos muestra, para cada profesional, cuántas horas
trabajó realmente (según lo que marcó en cada visita) y cuánto hay que pagarle,
incluyendo automáticamente los recargos nocturnos, dominicales o festivos si aplican.
Esta consulta se puede repetir todas las veces que se quiera antes de generar la nómina
en firme."

## Escena 10 — Generar la nómina (13:00 - 14:00)
**Mostrar:** Presionar "Generar nómina de este periodo", confirmar, ver el detalle
generado, marcar un pago como "Pagado".
**Narración:** "Cuando estamos de acuerdo con los valores, presionamos 'Generar nómina
de este periodo'. Esto deja la nómina guardada oficialmente, y las visitas de ese
periodo quedan marcadas como liquidadas para que no se paguen dos veces. A medida que se
hacen las transferencias, marcamos cada pago como 'Pagado'."

## Escena 11 — Cierre (14:00 - 15:00)
**Mostrar:** Recorrido rápido por el menú completo (RIPS, Interoperabilidad, Catálogos,
Turnos, app móvil).
**Narración:** "Y con esto completamos el recorrido de lo esencial. El sistema también
incluye generación de RIPS, interoperabilidad de historia clínica, catálogos oficiales,
calendario de turnos, y una app móvil para que el personal de campo trabaje incluso sin
conexión a internet. Cada uno de estos módulos está explicado en detalle en el manual de
funcionamiento escrito."
