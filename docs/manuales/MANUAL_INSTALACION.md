# Manual de Instalación — HomeCare Enterprise

Este manual cubre las **dos formas** de tener el sistema funcionando:

- **Instalación Local (Windows)** — el programa corre en un computador de la IPS, y todos se conectan a él desde la misma red local. Es la forma en la que se ha usado el sistema hasta ahora.
- **Instalación en la Nube / Dominio propio** — para cuando la IPS esté lista para que el sistema se use desde cualquier lugar con internet, con su propio dominio (ej. `sistema.homecarequindio.com`). Esta sección explica el camino a seguir cuando llegue ese momento — **todavía no está activada**, es la ruta a futuro.

---

# PARTE 1 — Instalación Local (Windows)

## Requisitos previos

- Windows 10 u 11.
- Permisos de Administrador en el computador.
- Al menos 2 GB de espacio libre en disco.
- Conexión a internet **solo la primera vez** (para instalar Python y las dependencias) — después el sistema funciona sin internet en la red local (aunque WhatsApp, correo y las notificaciones sí necesitan internet para salir).

## Pasos de instalación

1. Copie la carpeta completa del programa al computador donde va a quedar el servidor (ej. `D:\HomeCareEnterprise`).
2. Haga **doble clic en `Instalar_Windows.bat`**.
3. El instalador va a pedir permisos de Administrador — acepte.
4. Espera mientras instala Python (si no está) y todas las librerías necesarias — la primera vez puede tardar varios minutos.
5. Al terminar, se crea automáticamente un **acceso directo en el escritorio**.
6. El servidor arranca solo y se abre el navegador mostrando la pantalla de inicio de sesión.

## Uso diario

- Para **abrir el programa**: doble clic en el acceso directo del escritorio (`Abrir_HomeCareEnterprise.bat`) — si el servidor no está corriendo, lo arranca solo; si ya está corriendo, solo abre el navegador.
- Para que **otros computadores de la red** se conecten: en cada uno, abran el navegador y entren a `http://[IP-del-servidor]:8088` (reemplace por la dirección IP real del computador donde quedó instalado el programa).
- El servidor debe quedar **prendido** mientras el equipo esté trabajando — si se apaga el computador servidor, nadie más se puede conectar.

## Respaldo de la información

La base de datos es un solo archivo (`database.db`) dentro de la carpeta del programa. **Haga copia de este archivo regularmente** (a un disco externo, USB, o carpeta en la nube tipo Google Drive/OneDrive) — si el computador falla y no hay copia, se pierde toda la información.

## Actualizar el programa

Cuando reciba una versión nueva:
1. Cierre el servidor (o simplemente cierre la ventana negra/consola donde está corriendo).
2. Reemplace TODOS los archivos de la carpeta del programa con los nuevos, **excepto** el archivo `database.db` (esa es la información real, no se toca).
3. Vuelva a abrir el programa con el acceso directo — las migraciones de base de datos se aplican solas al arrancar.
4. Haga **Ctrl+Shift+R** en el navegador para que cargue los archivos nuevos (no los que tenía guardados).

## Desinstalar

Ejecute `deploy/windows/desinstalar_windows.ps1`, o simplemente borre la carpeta del programa (después de hacer respaldo de `database.db` si quiere conservar la información).

---

# PARTE 2 — Instalación en la Nube / Dominio propio (a futuro)

> **Estado actual:** el sistema NO está preparado hoy para este tipo de instalación sin trabajo adicional. Esta sección es la **hoja de ruta** de lo que hay que hacer cuando llegue el momento de lanzar el sistema para que varias sedes, o el público en general, lo usen desde internet.

## Por qué no es un paso automático

El sistema hoy usa **SQLite** (un solo archivo de base de datos) — perfecto para un servidor local con pocos usuarios simultáneos, pero no aguanta bien muchos usuarios escribiendo al mismo tiempo desde internet, ni tiene los controles de seguridad de base de datos (usuarios, permisos, cifrado) que se esperan en un sistema en la nube con datos de salud.

## Los pasos, en orden, cuando llegue el momento

1. **Migrar la base de datos a PostgreSQL.** Es el cambio más importante — de un archivo local a un motor de base de datos real, con control de acceso a nivel de base de datos (RLS — Row Level Security), respaldos automáticos, y capacidad de manejar muchos usuarios a la vez. El código ya está organizado en capas (repositorios separados de la lógica del negocio), lo que hace este cambio más manejable, pero sigue siendo un trabajo dedicado, no algo que se resuelve en una tarde.

2. **Contratar un servidor en la nube.** Opciones típicas: DigitalOcean, AWS, Azure, o similar. Se necesita un servidor con Python instalado (o, mejor, empaquetar el programa en un contenedor Docker para que el despliegue sea repetible).

3. **Configurar HTTPS real** con un certificado (gratis con Let's Encrypt, por ejemplo) — hoy las cookies de sesión están configuradas para funcionar en `http://localhost`; para producción real hay que activar `COOKIE_SECURE=True` y servir todo por `https://`.

4. **Comprar y apuntar el dominio propio** (ej. `sistema.homecarequindio.com`) al servidor de la nube.

5. **Configurar respaldos automáticos** de la base de datos en la nube (la mayoría de proveedores de PostgreSQL gestionado, como Amazon RDS o DigitalOcean Managed Databases, lo hacen automático).

6. **Revisar el cumplimiento legal** de datos sensibles de salud (Ley 1581 de 2012 / Habeas Data) con un asesor legal, en paralelo a la parte técnica.

## Qué NO hay que rehacer

La lógica del negocio (los módulos: pacientes, facturación, nómina, etc.) **no hay que reescribirla** — está en `services/` y `repositories/`, separada de cómo se conecta a la base de datos. El cambio de infraestructura es principalmente en la capa de base de datos y en cómo se despliega el servidor, no en cómo funciona el programa por dentro.

---

## Resumen: ¿cuál instalación usar hoy?

**Local (Windows)** — es la que deben seguir usando mientras están probando módulos y validando que el negocio funciona como esperan. La instalación en la nube es un proyecto aparte, para cuando estén listos para lanzar el sistema al público o a varias sedes a la vez.
