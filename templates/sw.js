const CACHE_NAME = 'quizfall-v3';
const STATIC_ASSETS = [
  '/manifest.json',
  '/static/css/style.css',
  '/static/js/game.js',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// Install: cache static shell assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME)
          .map(name => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch: network-first for navigation/API, cache-first for static assets
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // For same-origin navigation requests and API calls, use network-first
  if (event.request.mode === 'navigate' || url.pathname.startsWith('/quiz/') || url.pathname.startsWith('/game/')) {
    event.respondWith(
      fetch(event.request)
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // For static assets, use cache-first
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request).then(fetchResponse => {
          // Cache new static assets on the fly
          if (fetchResponse.ok && url.origin === self.location.origin) {
            const clone = fetchResponse.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return fetchResponse;
        });
      })
  );
});
