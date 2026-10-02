const DATABASE_NAME = "tools-workspace-database-mapper";
const LEGACY_STORE_NAME = "autosave";
const PROJECT_STORE_NAME = "projects";
const SESSION_STORE_NAME = "project-sessions";
const LEGACY_SESSION_KEY = "current-session";

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, 2);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(LEGACY_STORE_NAME)) {
        database.createObjectStore(LEGACY_STORE_NAME);
      }
      if (!database.objectStoreNames.contains(PROJECT_STORE_NAME)) {
        database.createObjectStore(PROJECT_STORE_NAME, { keyPath: "id" });
      }
      if (!database.objectStoreNames.contains(SESSION_STORE_NAME)) {
        database.createObjectStore(SESSION_STORE_NAME, { keyPath: "projectId" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function runTransaction(storeName, mode, operation) {
  const database = await openDatabase();
  try {
    return await new Promise((resolve, reject) => {
      const transaction = database.transaction(storeName, mode);
      const store = transaction.objectStore(storeName);
      const request = operation(store);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
      transaction.onerror = () => reject(transaction.error);
    });
  } finally {
    database.close();
  }
}

export function loadLegacyAutosave() {
  return runTransaction(LEGACY_STORE_NAME, "readonly", (store) =>
    store.get(LEGACY_SESSION_KEY),
  );
}

export function clearLegacyAutosave() {
  return runTransaction(LEGACY_STORE_NAME, "readwrite", (store) =>
    store.delete(LEGACY_SESSION_KEY),
  );
}

export async function listProjects() {
  const projects = await runTransaction(PROJECT_STORE_NAME, "readonly", (store) =>
    store.getAll(),
  );
  return projects.sort((a, b) =>
    String(b.updatedAt || "").localeCompare(String(a.updatedAt || "")),
  );
}

export function createProject(project) {
  return runTransaction(PROJECT_STORE_NAME, "readwrite", (store) => store.add(project));
}

export function updateProject(project) {
  return runTransaction(PROJECT_STORE_NAME, "readwrite", (store) => store.put(project));
}

export function loadProjectSession(projectId) {
  return runTransaction(SESSION_STORE_NAME, "readonly", (store) => store.get(projectId));
}

export function saveProjectSession(session) {
  return runTransaction(SESSION_STORE_NAME, "readwrite", (store) => store.put(session));
}

export async function deleteProject(projectId) {
  const database = await openDatabase();
  try {
    await new Promise((resolve, reject) => {
      const transaction = database.transaction(
        [PROJECT_STORE_NAME, SESSION_STORE_NAME],
        "readwrite",
      );
      transaction.objectStore(PROJECT_STORE_NAME).delete(projectId);
      transaction.objectStore(SESSION_STORE_NAME).delete(projectId);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  } finally {
    database.close();
  }
}
