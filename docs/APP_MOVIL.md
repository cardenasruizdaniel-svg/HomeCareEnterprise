# App Móvil de Campo (PWA offline-first)

## Qué es y cómo se instala

Es una **Progressive Web App (PWA)**: no pasa por Google Play ni App Store.
Se abre una vez desde el navegador del celular (Chrome en Android, Safari
en iPhone) en la dirección:

```
https://tu-dominio.com/app/
```

y luego se instala con "Agregar a pantalla de inicio" (Android/Chrome) o
"Compartir → Agregar a inicio" (iPhone/Safari). Queda con ícono propio,
pantalla completa, y funciona igual que una app nativa.

## A quién está dirigida

Cuidadores, enfermeros, terapeutas, médicos y aplicadores de medicamentos
que atienden pacientes en el domicilio.

## Qué hace offline (sin datos ni wifi)

- Ver la agenda del día (ya cargada previamente).
- Ver la ficha del paciente: alergias, medicamentos activos, diagnósticos
  (de los pacientes que ya se consultaron con internet).
- Registrar **ingreso a labores** y **finalización de labores** en cada
  visita (con geolocalización si el celular la tiene activada) — esta
  marcación es la que alimenta la nómina.
- Registrar **signos vitales**.
- Registrar **medicamento administrado**.
- Registrar una **nota de evolución** clínica.
- (Médicos) Generar una **orden médica** (fórmula, examen, remisión).

Todo esto se guarda en el propio celular (IndexedDB) mientras no hay
conexión, en una cola visible en la pestaña "Por enviar".

## Qué pasa cuando vuelve la conexión

La app sincroniza automáticamente (cada 20 segundos revisa si hay
conexión, y también al detectar el evento "online" del sistema
operativo). También se puede forzar con el botón "Sincronizar ahora".

**Importante, tal como se pidió**: si lo que se sincroniza es una
**orden médica** (fórmula, medicamento o examen de laboratorio), el
servidor —al recibirla— dispara automáticamente el mismo mecanismo ya
construido para la web: genera el PDF y lo envía al paciente por
**WhatsApp y correo electrónico**, para que pueda reclamarlo. Esto no es
código nuevo: la app móvil reutiliza `OrdenesService.crear_y_enviar`,
el mismo servicio que usa el panel web.

## Requisito para que un profesional pueda usar la app

Su cuenta de usuario debe estar **vinculada** a su registro de
profesional. Esto se hace desde `/profesionales/editar/{id}` → sección
"Acceso a la app móvil" → seleccionar la cuenta de usuario
correspondiente. (Antes de esta vinculación, la app no tenía forma de
saber qué agenda mostrarle a quién — era un vacío real del sistema que
se corrigió como parte de esta funcionalidad.)

## Arquitectura (para el equipo técnico)

- `static/pwa/` — la app: `index.html`, `app.js`, `estilos.css`,
  `manifest.json`, `sw.js` (service worker), `icons/`.
- `routers/api_movil.py` — API JSON que usa la app (login, agenda,
  ficha de paciente, y el endpoint clave `POST /api/movil/sync` que
  procesa en lote las acciones registradas sin conexión).
- `services/movil_service.py` — lógica de negocio de cada acción.
- La autenticación usa la **misma cookie de sesión** que el sitio web:
  el profesional inicia sesión una vez con internet y desde ahí puede
  seguir trabajando sin conexión.

## Limitaciones conocidas

- No es una app nativa (no aparece en Play Store/App Store). Si más
  adelante se requiere presencia oficial en las tiendas, el código de
  `routers/api_movil.py` puede reutilizarse tal cual como backend de una
  app en React Native o Flutter — lo que cambiaría es solo la capa de
  interfaz, no la lógica de sincronización.
- La cola offline vive en el navegador (IndexedDB). Si el usuario borra
  los datos del navegador o desinstala la PWA antes de sincronizar,
  se perderían las acciones pendientes. Se recomienda sincronizar apenas
  se recupere señal y no acumular muchos días de trabajo sin conexión.
- El primer ingreso siempre requiere internet (para autenticar). Después
  de eso, la sesión queda activa en el dispositivo.
