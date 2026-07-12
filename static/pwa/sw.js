/* =========================================================
   HomeCare Enterprise - Service Worker

   IMPORTANTE: la estrategia es "red primero, caché como
   respaldo" para el codigo de la app (app.js, index.html,
   estilos.css). Antes era "cache primero", lo que hacia que
   el celular seguiera usando una copia vieja del codigo para
   siempre, incluso despues de actualizar el servidor -- con
   "red primero" siempre se usa la version mas nueva cuando
   hay internet, y solo se cae a la copia guardada cuando de
   verdad no hay conexion (para que la app siga funcionando
   sin internet en el campo).
   ========================================================= */

// IMPORTANTE: cambiar este numero cada vez que se publique
// una actualizacion de la app movil, para que los celulares
// boten la cache vieja y descarguen la version nueva.
const VERSION_APP = "3";
const CACHE_NAME = "homecare-app-v" + VERSION_APP;

const ARCHIVOS_APP_SHELL = [
  "/app/",
  "/app/index.html",
  "/app/app.js",
  "/app/estilos.css",
  "/app/manifest.json",
  "/app/icons/icon-192.png",
  "/app/icons/icon-512.png",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ARCHIVOS_APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys().then((nombres) =>
      Promise.all(
        nombres
          .filter((n) => n !== CACHE_NAME)
          .map((n) => caches.delete(n))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (evento) => {
  const url = new URL(evento.request.url);

  // Las llamadas a la API nunca se sirven desde cache: si no
  // hay red, que fallen (app.js las encola en IndexedDB).
  if (url.pathname.startsWith("/api/movil/")) {
    return;
  }

  // Para el resto del app shell (el codigo de la app en si):
  // RED PRIMERO. Si hay internet, siempre trae la version mas
  // nueva del servidor y actualiza la copia guardada. Solo si
  // de verdad no hay conexion, usa la ultima copia guardada.
  evento.respondWith(
    fetch(evento.request)
      .then((respuestaRed) => {
        if (evento.request.method === "GET" && respuestaRed.ok) {
          const copia = respuestaRed.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(evento.request, copia));
        }
        return respuestaRed;
      })
      .catch(() =>
        caches.match(evento.request).then((respuestaCache) =>
          respuestaCache || caches.match("/app/index.html")
        )
      )
  );
});
