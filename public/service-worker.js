importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.5.4/workbox-sw.js');

const CACHE_VERSION = 'v1';

const CORE_ASSETS = [
  { url: '/', revision: null },
  { url: '/index.html', revision: null },
  { url: '/manifest.json', revision: null }
];

workbox.precaching.precacheAndRoute(CORE_ASSETS);

const apiStrategy = new workbox.strategies.NetworkFirst({
  cacheName: `api-cache-${CACHE_VERSION}`,
  plugins: [
    new workbox.cacheableResponse.CacheableResponsePlugin({ statuses: [0, 200] }),
    new workbox.expiration.ExpirationPlugin({ maxEntries: 50, maxAgeSeconds: 5 * 60 })
  ]
});

const staticStrategy = new workbox.strategies.StaleWhileRevalidate({
  cacheName: `static-cache-${CACHE_VERSION}`
});

const DB_NAME = 'offline-store';
const ACTION_STORE = 'actionQueue';

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(ACTION_STORE)) {
        db.createObjectStore(ACTION_STORE, { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function enqueueFailedRequest(req) {
  const db = await openDB();
  const tx = db.transaction(ACTION_STORE, 'readwrite');
  const store = tx.objectStore(ACTION_STORE);

  const headers = {};
  for (const [key, value] of req.headers.entries()) {
    headers[key] = value;
  }

  let body;
  try {
    body = await req.clone().json();
  } catch (e) {
    body = await req.clone().text();
  }

  store.add({
    url: req.url,
    method: req.method,
    headers,
    body
  });
}

async function flushQueuedActions() {
  const db = await openDB();
  const tx = db.transaction(ACTION_STORE, 'readwrite');
  const store = tx.objectStore(ACTION_STORE);
  const getAllRequest = store.getAll();
  const actions = await new Promise((resolve, reject) => {
    getAllRequest.onsuccess = () => resolve(getAllRequest.result);
    getAllRequest.onerror = () => reject(getAllRequest.error);
  });
  for (const action of actions) {
    try {
      await fetch(action.url, {
        method: action.method,
        headers: action.headers,
        body: JSON.stringify(action.body)
      });
      store.delete(action.id);
    } catch (err) {
      console.error('Action sync failed', err);
    }
  }
}

self.addEventListener('sync', (event) => {
  if (event.tag === 'flush-actions') {
    event.waitUntil(flushQueuedActions());
  }
});

self.addEventListener('fetch', (event) => {
  const { request } = event;

  if (['POST', 'PUT'].includes(request.method)) {
    event.respondWith(
      fetch(request.clone()).catch(async () => {
        await enqueueFailedRequest(request);
        return new Response(JSON.stringify({ error: 'offline' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }

  if (request.method === 'GET') {
    if (request.url.includes('/api/')) {
      event.respondWith(apiStrategy.handle({ request }));
    } else {
      event.respondWith(
        staticStrategy
          .handle({ request })
          .catch(() => caches.match(request))
      );
    }
  }
});
