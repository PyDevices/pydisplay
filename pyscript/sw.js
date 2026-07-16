/*! pydisplay PWA service worker — offline cache + COI headers for PyScript */
/* CACHE_NAME is stamped at Pages deploy from a hash of STATIC_ASSETS + this
 * file (see scripts/pyscript_stamp_pwa_cache.py). Git keeps -dev for local serve. */
const CACHE_NAME = 'pydisplay-pwa-62a38fcf654e';

const STATIC_ASSETS = [
  './index.html',
  './micropython.html',
  './pyodide.html',
  './simple.html',
  './repl.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './site.css',
  './demo.css',
  './pwa.css',
  './pwa.js',
  './loader-ready.js',
  './mini-coi-fd.js',
  './micropython.toml',
  './pyodide.toml',
];

// Loader HTML changes often; fetch network-first so fixes are not masked by cache.
const NETWORK_FIRST_ASSETS = [
  './micropython.html',
  './pyodide.html',
  './run.html',
  './run-pyodide.html',
];

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

function isRuntimeOrigin(hostname) {
  return RUNTIME_ORIGINS.some((origin) => hostname.includes(origin));
}

function isStaticAssetPath(pathname) {
  return STATIC_ASSETS.some((asset) => {
    const name = asset.replace(/^\.\//, '');
    return pathname.endsWith('/' + name) || pathname.endsWith(name);
  });
}

function isNetworkFirstPath(pathname) {
  return NETWORK_FIRST_ASSETS.some((asset) => {
    const name = asset.replace(/^\.\//, '');
    return pathname.endsWith('/' + name) || pathname.endsWith(name);
  });
}

function shouldCache(url, request) {
  if (request.method !== 'GET') {
    return false;
  }
  if (request.cache === 'only-if-cached' && request.mode !== 'same-origin') {
    return false;
  }
  if (url.origin === self.location.origin) {
    return true;
  }
  return isRuntimeOrigin(url.hostname);
}

function networkFirstStaleWhileRevalidate(request) {
  return fetch(request)
    .then((networkResponse) => {
      if (
        networkResponse &&
        networkResponse.status === 200 &&
        networkResponse.type !== 'error'
      ) {
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, responseToCache));
      }
      return networkResponse;
    })
    .catch(() => caches.match(request));
}

function cacheFirstStaleWhileRevalidate(request) {
  return caches.match(request).then((cachedResponse) => {
    const networkFetch = fetch(request)
      .then((networkResponse) => {
        if (
          networkResponse &&
          networkResponse.status === 200 &&
          networkResponse.type !== 'error'
        ) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, responseToCache));
        }
        return networkResponse;
      })
      .catch(() => null);

    if (cachedResponse) {
      networkFetch.catch(() => {});
      return cachedResponse;
    }

    return networkFetch.then((networkResponse) => {
      if (networkResponse) {
        return networkResponse;
      }
      return caches.match(request);
    });
  });
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.map((key) => {
            if (key !== CACHE_NAME) {
              return caches.delete(key);
            }
          })
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (!shouldCache(url, request)) {
    event.respondWith(
      fetch(request).then((response) => withCoiHeaders(response))
    );
    return;
  }

  event.respondWith(
    (url.origin === self.location.origin && isNetworkFirstPath(url.pathname)
      ? networkFirstStaleWhileRevalidate(request)
      : cacheFirstStaleWhileRevalidate(request)
    ).then((response) => {
      if (!response) {
        return fetch(request).then((networkResponse) => withCoiHeaders(networkResponse));
      }
      if (url.origin === self.location.origin || isStaticAssetPath(url.pathname)) {
        return withCoiHeaders(response);
      }
      return response;
    })
  );
});
