import { openDB, IDBPDatabase } from 'idb';

const DB_NAME = 'offline-store';
const DB_VERSION = 1;
const ACTION_STORE = 'actionQueue';
const CACHE_STORE = 'cachedData';

let dbPromise: Promise<IDBPDatabase<any>> | null = null;

function getDB() {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains(ACTION_STORE)) {
          db.createObjectStore(ACTION_STORE, { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains(CACHE_STORE)) {
          db.createObjectStore(CACHE_STORE);
        }
      }
    });
  }
  return dbPromise;
}

export async function queueAction(action: any) {
  const db = await getDB();
  await db.add(ACTION_STORE, action);
  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    try {
      const reg = await navigator.serviceWorker.ready;
      await reg.sync.register('flush-actions');
    } catch (e) {
      console.error('Failed to register sync', e);
    }
  }
}

export async function getQueuedActions() {
  const db = await getDB();
  return db.getAll(ACTION_STORE);
}

export async function clearQueuedActions() {
  const db = await getDB();
  await db.clear(ACTION_STORE);
}

export async function cacheData(key: string, data: any) {
  const db = await getDB();
  await db.put(CACHE_STORE, data, key);
}

export async function getCachedData<T = any>(key: string): Promise<T | undefined> {
  const db = await getDB();
  return db.get(CACHE_STORE, key);
}
