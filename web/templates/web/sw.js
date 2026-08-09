{% load static %}// Swatchbook service worker.
//
// Rendered by web.views.ServiceWorkerView (not a plain static file) for two reasons:
// the precache URLs below need the prod content-hash the static tag adds, and the
// cache name is stamped with the deployed version so every release drops the old cache.
// Served from the site root so its scope is "/" without a Service-Worker-Allowed header.

const VERSION = '{{ version }}';
const CACHE = `swatchbook-${VERSION}`;
const OFFLINE_URL = '{% url "offline" %}';

// The app shell: enough to render *something* offline. The hashed JS/CSS bundle and the
// bottle photos are picked up at runtime (see fetch handler) rather than listed here,
// because their names change every build.
const PRECACHE = [
  OFFLINE_URL,
  '{% static "icons/icon-192.png" %}',
  '{% static "icons/icon-512.png" %}',
  '{% static "icons/favicon.svg" %}',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Cache-first, but refresh in the background — for versioned static assets and photos.
async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE);
  const cached = await cache.match(request);
  const network = fetch(request)
    .then((response) => {
      if (response.ok) cache.put(request, response.clone());
      return response;
    })
    .catch(() => cached);
  return cached || network;
}

// Network-first for pages, so you always see fresh data online but still get a
// last-seen copy (or the offline page) when the network is gone.
async function networkFirst(request) {
  const cache = await caches.open(CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (err) {
    const cached = await cache.match(request);
    return cached || cache.match(OFFLINE_URL);
  }
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  // Only GET, only our own origin — never touch POSTs (log/polish saves) or third
  // parties (Google Fonts). Let those go straight to the network.
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request));
    return;
  }

  if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
    event.respondWith(staleWhileRevalidate(request));
  }
});
