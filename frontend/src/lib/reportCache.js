// Persists the last analysis/clip report so a page reload can restore it instead of
// resetting to "no completed analysis". This used to be sessionStorage, but a report
// with several frame previews and evidence images can land in the low single-digit MB
// range — close enough to sessionStorage's ~5-10MB per-origin quota that writes were
// silently failing (QuotaExceededError, swallowed) and the report would vanish on
// reload. IndexedDB has no such practical ceiling for this use case.

const DB_NAME = 'peachcheck';
const STORE_NAME = 'reports';
const DB_VERSION = 1;

function openDb() {
  return new Promise((resolve, reject) => {
    if (!('indexedDB' in window)) {
      reject(new Error('IndexedDB unavailable'));
      return;
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(STORE_NAME)) {
        request.result.createObjectStore(STORE_NAME);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function saveReport(key, value) {
  try {
    const db = await openDb();
    await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      tx.objectStore(STORE_NAME).put(value, key);
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
    db.close();
  } catch {
    // Best-effort cache: the report is already on screen from in-memory navigation
    // state, so a failed write here only affects surviving a future reload.
  }
}

export async function loadReport(key) {
  try {
    const db = await openDb();
    const value = await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const request = tx.objectStore(STORE_NAME).get(key);
      request.onsuccess = () => resolve(request.result ?? null);
      request.onerror = () => reject(request.error);
    });
    db.close();
    return value;
  } catch {
    return null;
  }
}
