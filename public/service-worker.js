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
        method: action.method || 'POST',
        headers: action.headers || { 'Content-Type': 'application/json' },
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
