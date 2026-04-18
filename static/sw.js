const CACHE = 'thinkos-v1';
const STATIC = [
  '/',
  '/static/index.html',
  '/static/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png'
];

// Install — cache core shell
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(STATIC)).then(() => self.skipWaiting())
  );
});

// Activate — clean old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Fetch — network-first for API, cache-first for static assets
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Always go network for API calls
  if (url.pathname.startsWith('/api/')) return;

  // Network-first with cache fallback for everything else
  e.respondWith(
    fetch(e.request)
      .then(res => {
        if (res && res.status === 200 && e.request.method === 'GET') {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});
