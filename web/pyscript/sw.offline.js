/*! pydisplay PWA — TEMPORARY cache-purge service worker (one deploy).
 * Clears all legacy caches (e.g. pydisplay-pwa-dev from pre-hash installs) so
 * clients can fetch the stamped offline worker on the following deploy.
 * MIGRATION: cache-purge — skip CACHE_NAME stamp; restore from sw.offline.js */
/* eslint-disable no-restricted-globals */

const RUNTIME_ORIGINS = [
  'pyscript.net',
  'cdn.jsdelivr.net',
  'pyodide.org',
  'pydevices.github.io',
];

function withCoiHeaders(response) {
  const { body, status, statusText } = response;
  if (!status || status > 399) {
    return response;
  }
  const headers = new Headers(response.headers);
  headers.set('Cross-Origin-Opener-Policy', 'same-origin');
  headers.set('Cross-Origin-Embedder-Policy', 'require-corp');
  headers.set('Cross-Origin-Resource-Policy', 'cross-origin');
  return new Response(status === 204 ? null : body, { status, statusText, headers });
}

function shouldAddCoi(url, request) {
  if (request.method !== 'GET') {
    return false;
  }
  if (url.origin === self.location.origin) {
    return true;
  }
  return RUNTIME_ORIGINS.some((origin) => url.hostname.includes(origin));
}

self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
      .then(() =>
        self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      )
      .then((clients) => {
        clients.forEach((client) => {
          client.navigate(client.url);
        });
      })
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  event.respondWith(
    fetch(request).then((response) => {
      if (shouldAddCoi(url, request)) {
        return withCoiHeaders(response);
      }
      return response;
    })
  );
});
