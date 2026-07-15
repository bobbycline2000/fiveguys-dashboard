// Five Guys 2065 Ops — service worker
// Cache-first for app shell, network-first for data so live numbers stay fresh.

const VERSION = 'fg-2065-ops-e715806198-2026-07-15';
const SCOPE = '/fiveguys-dashboard';

// App-shell files we want available offline.
const SHELL = [
  `${SCOPE}/dashboard.html`,
  `${SCOPE}/safe_drawer.html`,
  `${SCOPE}/bread.html`,
  `${SCOPE}/synopsis.html`,
  `${SCOPE}/portfolio.html`,
  `${SCOPE}/manifest.json`,
  `${SCOPE}/icons/icon-192.png`,
  `${SCOPE}/icons/icon-512.png`,
  `${SCOPE}/icons/apple-touch-icon.png`,
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(VERSION).then((cache) =>
      cache.addAll(SHELL).catch(() => {
        // If any shell file fails (e.g. on first visit before GH Pages
        // serves the new file), don't break install — they'll be cached
        // lazily on first fetch.
      })
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Cross-origin data (Cloudflare worker, GitHub raw): network-first, no cache.
  // Live numbers must stay fresh.
  if (url.origin !== self.location.origin) {
    return; // let the browser handle it directly
  }

  // Data JSONs in /data/ — network-first so the page always sees today's run.
  if (url.pathname.includes(`${SCOPE}/data/`)) {
    event.respondWith(
      fetch(req).then((resp) => {
        const copy = resp.clone();
        caches.open(VERSION).then((c) => c.put(req, copy));
        return resp;
      }).catch(() => caches.match(req))
    );
    return;
  }

  // App shell + everything else under our scope: cache-first, fall back to network.
  event.respondWith(
    caches.match(req).then((cached) => cached || fetch(req).then((resp) => {
      if (resp.ok && resp.type === 'basic') {
        const copy = resp.clone();
        caches.open(VERSION).then((c) => c.put(req, copy));
      }
      return resp;
    }).catch(() => cached))
  );
});
