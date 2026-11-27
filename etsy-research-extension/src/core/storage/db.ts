/** Minimal promise wrapper around IndexedDB. Works in the service worker and extension pages. */

export const DB_NAME = 'shoplens';
export const DB_VERSION = 1;

export type StoreName =
  | 'listings' | 'listingSnapshots' | 'shops' | 'shopSnapshots' | 'keywords' | 'keywordSnapshots'
  | 'changes' | 'collections' | 'history' | 'meta';

export const STORES: { name: StoreName; keyPath?: string; autoIncrement?: boolean; indexes?: [string, string][] }[] = [
  { name: 'listings', keyPath: 'listingId', indexes: [['shopName', 'shopName'], ['lastSeen', 'lastSeen']] },
  { name: 'listingSnapshots', keyPath: 'id', autoIncrement: true, indexes: [['listingId', 'listingId']] },
  { name: 'shops', keyPath: 'shopName' },
  { name: 'shopSnapshots', keyPath: 'id', autoIncrement: true, indexes: [['shopName', 'shopName']] },
  { name: 'keywords', keyPath: 'term' },
  { name: 'keywordSnapshots', keyPath: 'id', autoIncrement: true, indexes: [['term', 'term']] },
  { name: 'changes', keyPath: 'id', autoIncrement: true, indexes: [['key', 'key'], ['ts', 'ts']] },
  { name: 'collections', keyPath: 'id' },
  { name: 'history', keyPath: 'id', autoIncrement: true, indexes: [['ts', 'ts']] },
  { name: 'meta', keyPath: 'key' },
];

let dbPromise: Promise<IDBDatabase> | undefined;

export function openDb(factory: IDBFactory = indexedDB): Promise<IDBDatabase> {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    const req = factory.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      for (const s of STORES) {
        if (db.objectStoreNames.contains(s.name)) continue;
        const os = db.createObjectStore(s.name, { keyPath: s.keyPath, autoIncrement: s.autoIncrement });
        for (const [n, k] of s.indexes ?? []) os.createIndex(n, k);
      }
    };
    req.onsuccess = () => {
      const db = req.result;
      db.onversionchange = () => { db.close(); dbPromise = undefined; };
      resolve(db);
    };
    req.onerror = () => { dbPromise = undefined; reject(req.error); };
  });
  return dbPromise;
}

/** For tests: forget the cached connection. */
export function resetDbCache() {
  dbPromise = undefined;
}

function wrap<T>(req: IDBRequest<T>): Promise<T> {
  return new Promise((res, rej) => {
    req.onsuccess = () => res(req.result);
    req.onerror = () => rej(req.error);
  });
}

export async function tx<T>(stores: StoreName | StoreName[], mode: IDBTransactionMode, fn: (t: IDBTransaction) => Promise<T> | T): Promise<T> {
  const db = await openDb();
  const t = db.transaction(stores, mode);
  const done = new Promise<void>((res, rej) => {
    t.oncomplete = () => res();
    t.onerror = () => rej(t.error);
    t.onabort = () => rej(t.error ?? new Error('Transaction aborted'));
  });
  const result = await fn(t);
  await done;
  return result;
}

export async function get<T>(store: StoreName, key: IDBValidKey): Promise<T | undefined> {
  return tx(store, 'readonly', (t) => wrap(t.objectStore(store).get(key)) as Promise<T | undefined>);
}

export async function getAll<T>(store: StoreName): Promise<T[]> {
  return tx(store, 'readonly', (t) => wrap(t.objectStore(store).getAll()) as Promise<T[]>);
}

export async function byIndex<T>(store: StoreName, index: string, key: IDBValidKey): Promise<T[]> {
  return tx(store, 'readonly', (t) => wrap(t.objectStore(store).index(index).getAll(key)) as Promise<T[]>);
}

export async function put<T>(store: StoreName, value: T): Promise<IDBValidKey> {
  return tx(store, 'readwrite', (t) => wrap(t.objectStore(store).put(value)));
}

export async function putMany<T>(store: StoreName, values: T[]): Promise<void> {
  if (!values.length) return;
  await tx(store, 'readwrite', (t) => {
    const os = t.objectStore(store);
    for (const v of values) os.put(v);
  });
}

export async function del(store: StoreName, key: IDBValidKey): Promise<void> {
  await tx(store, 'readwrite', (t) => wrap(t.objectStore(store).delete(key)));
}

export async function deleteByIndex(store: StoreName, index: string, key: IDBValidKey): Promise<void> {
  await tx(store, 'readwrite', async (t) => {
    const os = t.objectStore(store);
    const keys = await wrap(os.index(index).getAllKeys(key));
    for (const k of keys) os.delete(k);
  });
}

export async function clearAll(): Promise<void> {
  await tx(STORES.map((s) => s.name), 'readwrite', (t) => {
    for (const s of STORES) t.objectStore(s.name).clear();
  });
}

export async function count(store: StoreName): Promise<number> {
  return tx(store, 'readonly', (t) => wrap(t.objectStore(store).count()));
}
