# Guion de video 1: Instalación y configuración (8-10 minutos)

Dirigido a: la persona de sistemas/soporte de la IPS que instalará el servidor.

---

## Escena 1 — Introducción (0:00 - 0:30)
**Mostrar:** Pantalla de bienvenida / logo de HomeCare Enterprise.
**Narración:** "En este video vamos a instalar HomeCare Enterprise en un servidor Windows
(y luego mostraremos la misma instalación en macOS). Todo el proceso toma entre 5 y 10
minutos y no requiere conocimientos técnicos avanzados."

## Escena 2 — Requisitos (0:30 - 1:00)
**Mostrar:** Tabla de requisitos del Manual de Instalación (sección 1).
**Narración:** "Antes de empezar, confirme que el equipo cumple los requisitos mínimos:
4 GB de RAM, 10 GB libres, y Windows 10, 11 o Windows Server. No necesita instalar Python
ni nada más de forma manual — el instalador se encarga de todo."

## Escena 3 — Copiar los archivos (1:00 - 1:30)
**Mostrar:** Copiar la carpeta del proyecto desde un USB o descarga hacia el escritorio.
**Narración:** "Copie la carpeta completa del programa al servidor. Puede ir al escritorio
o a cualquier carpeta temporal; el instalador la moverá al lugar definitivo."

## Escena 4 — Ejecutar el instalador (1:30 - 3:30)
**Mostrar:** Doble clic en `Instalar_Windows.bat`, aceptar el permiso de Administrador,
y la consola mostrando el progreso paso a paso (Python, copiando archivos, instalando
dependencias, configurando el firewall, iniciando el servidor).
**Narración:** "Haga doble clic en Instalar_Windows.bat. Windows le va a pedir permiso de
Administrador — acepte. A partir de aquí, todo es automático: el instalador revisa si
Python está instalado, copia el programa a C:\HomeCareEnterprise, instala las librerías
necesarias, configura el inicio automático con Windows, abre el puerto en el firewall, y
finalmente enciende el servidor. Esto puede tardar varios minutos la primera vez."

## Escena 5 — Verificar que quedó funcionando (3:30 - 4:15)
**Mostrar:** La consola mostrando "El servidor está corriendo correctamente" y el resumen
final con la dirección de acceso.
**Narración:** "Cuando termina, la consola le muestra la dirección para entrar al sistema,
el usuario y contraseña inicial, y dónde quedó guardada la configuración. Guarde esta
información."

## Escena 6 — Primer ingreso (4:15 - 5:00)
**Mostrar:** Abrir un navegador, entrar a la URL, pantalla de login, iniciar sesión con
admin/admin123.
**Narración:** "Abrimos el navegador y entramos a la dirección indicada. Iniciamos sesión
con el usuario admin y la contraseña admin123 — que cambiaremos de inmediato por
seguridad."

## Escena 7 — Cambiar la contraseña (5:00 - 5:45)
**Mostrar:** Ir a Usuarios → editar admin → cambiar contraseña.
**Narración:** "Antes de cargar cualquier información real, vamos a Usuarios y cambiamos
la contraseña del administrador."

## Escena 8 — Configurar el archivo .env (5:45 - 7:30)
**Mostrar:** Abrir la carpeta de instalación, abrir el archivo .env con el Bloc de notas,
señalar las secciones de correo, WhatsApp y RIPS.
**Narración:** "Ahora vamos a configurar el archivo .env, que controla el envío de correos,
WhatsApp y los datos para el RIPS. Aquí completamos el NIT de la IPS, el código de
habilitación, y las credenciales de correo. Las credenciales de WhatsApp Business se
tramitan directamente con Meta — el manual escrito explica exactamente cómo obtenerlas.
Después de editar este archivo, hay que reiniciar el servidor para que tome los cambios."

## Escena 9 — Instalación en macOS (7:30 - 9:30)
**Mostrar:** Repetir el proceso en un Mac: doble clic en Instalar_macOS.command, ingresar
contraseña de administrador, ver el progreso, y la confirmación final.
**Narración:** "El proceso en Mac es prácticamente igual: doble clic en
Instalar_macOS.command, ingresamos la contraseña del Mac, y el instalador hace todo el
trabajo — incluyendo instalar Homebrew y Python si hacen falta."

## Escena 10 — Cierre (9:30 - 10:00)
**Mostrar:** Dashboard principal del sistema ya funcionando.
**Narración:** "Con esto, el servidor queda instalado y configurado para iniciar
automáticamente cada vez que se encienda el equipo. En el próximo video veremos cómo
usar el sistema en el día a día: pacientes, historias clínicas, agendas y nómina."
