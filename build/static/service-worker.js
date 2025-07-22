const CACHE_NAME = 'finanz-cache-v1';
const ASSETS = [
  '/',
  '/static/style.css',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  // ggf. weitere Ressourcen
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
});

self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request))
  );
});
