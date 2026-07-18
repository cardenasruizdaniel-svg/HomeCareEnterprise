// HomeCare Enterprise - App Gerencial - Service Worker
//
// Esta app es de solo lectura y siempre necesita datos
// actualizados (indicadores en vivo), así que usa una
// estrategia "network-first" simple: siempre intenta pedir
// datos frescos al servidor primero, y solo si no hay
// conexión, se apoya en lo que haya quedado en caché (para
// que al menos abra, aunque los números no estén al minuto).

const VERSION_APP = "1";
const CACHE_APP_SHELL = `gerencial-shell-v${VERSION_APP}`;

const ARCHIVOS_APP_SHELL = [
  "/gerencial/",
  "/gerencial/index.html",
  "/gerencial/app.js",
  "/gerencial/estilos.css",
  "/gerencial/manifest.json",
  "/gerencial/icons/icon-192.png",
  "/gerencial/icons/icon-512.png",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches.open(CACHE_APP_SHELL).then((cache) => cache.addAll(ARCHIVOS_APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys().then((claves) =>
      Promise.all(claves.filter((clave) => clave !== CACHE_APP_SHELL).map((clave) => caches.delete(clave)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (evento) => {
  const url = new URL(evento.request.url);

  // Las llamadas a la API nunca se sirven desde caché -- los
  // indicadores gerenciales siempre deben ser los reales del
  // momento, no unos guardados de antes.
  if (url.pathname.startsWith("/api/gerencial/")) {
    evento.respondWith(fetch(evento.request));
    return;
  }

  if (url.origin !== location.origin) return;

  evento.respondWith(
    fetch(evento.request)
      .then((respuesta) => {
        const copia = respuesta.clone();
        caches.open(CACHE_APP_SHELL).then((cache) => cache.put(evento.request, copia));
        return respuesta;
      })
      .catch(() => caches.match(evento.request))
  );
});
