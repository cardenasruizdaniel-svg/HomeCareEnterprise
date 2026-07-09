/* =========================================================
   HomeCare Enterprise - Service Worker
   Cachea el "app shell" (HTML/CSS/JS/iconos) para que la app
   abra sin internet, y deja que las llamadas a /api/movil/*
   fallen limpiamente cuando no hay red (las maneja app.js
   guardándolas en la cola local de IndexedDB).
   ========================================================= */

const CACHE_NAME = "homecare-app-v1";

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

  // Para el resto del app shell: cache-first, con red como respaldo.
  evento.respondWith(
    caches.match(evento.request).then((respuestaCache) => {
      if (respuestaCache) return respuestaCache;

      return fetch(evento.request)
        .then((respuestaRed) => {
          if (evento.request.method === "GET" && respuestaRed.ok) {
            const copia = respuestaRed.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(evento.request, copia));
          }
          return respuestaRed;
        })
        .catch(() => caches.match("/app/index.html"));
    })
  );
});
