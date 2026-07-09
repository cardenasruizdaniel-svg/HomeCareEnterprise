# Integración con Google Calendar

## Qué implementa HomeCare Enterprise hoy

Cada vez que se programa una visita, el sistema genera automáticamente un
archivo de calendario estándar (**.ics**) y lo envía por correo tanto al
paciente como al profesional, junto con el aviso de WhatsApp. Al abrir ese
archivo adjunto, el evento se agrega solo al calendario que la persona ya
use — Google Calendar, Outlook, Apple Calendar — sin que la IPS necesite
pedir ningún permiso especial.

Esto **no requiere ningún trámite**: funciona en cuanto el correo (SMTP)
esté configurado en el `.env`.

## Qué sería un paso adicional (opcional)

Que HomeCare Enterprise **escriba directamente** en el Google Calendar de
cada profesional (sin que él tenga que abrir ningún archivo), requeriría
que cada profesional autorice el acceso una vez, mediante el proceso
oficial de Google llamado OAuth 2.0. Esto es exactamente el mismo tipo de
trámite que ya se hizo para WhatsApp Business — lo debe gestionar
directamente la IPS, no depende del software:

1. Crear un proyecto en **Google Cloud Console** (console.cloud.google.com).
2. Activar la **Google Calendar API** para ese proyecto.
3. Crear credenciales de tipo **OAuth 2.0 Client ID** (tipo "Aplicación web").
4. Configurar la URL de redirección autorizada (por ejemplo,
   `https://su-servidor.com/profesionales/autorizar-calendario/callback`).
5. Copiar el **Client ID** y **Client Secret** al archivo `.env`.

Con esas credenciales, cada profesional entraría una sola vez a un enlace
"Conectar mi Google Calendar" desde su perfil, aceptaría el permiso en la
pantalla de Google, y desde ese momento el sistema podría crear, mover o
cancelar directamente los eventos en su calendario cuando se programe,
reprograme o cancele una visita.

## Por qué no se hace lo mismo para los pacientes

Pedirle a cada paciente que autorice el acceso a su cuenta de Google es
poco práctico para una IPS (implicaría que cada paciente cree una sesión
OAuth, algo que la mayoría no haría). Por eso, para los pacientes, el
archivo .ics por correo es la solución correcta: logra el mismo resultado
(el evento queda en su calendario) sin fricción ni necesidad de que
autoricen nada.

## Si más adelante se quiere implementar el paso OAuth para profesionales

El código quedaría en un nuevo módulo `services/google_calendar_service.py`,
usando la librería oficial `google-api-python-client`, y una tabla para
guardar el `refresh_token` de cada profesional que autorice el acceso.
Aviso si se quiere avanzar en esto una vez la IPS tenga las credenciales
de Google Cloud.
