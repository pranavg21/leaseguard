import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const SOURCE = readFileSync(new URL('../../static/sw.js', import.meta.url), 'utf8');
const ORIGIN = 'http://localhost';
const LAZY_MODULES = ['/static/js/evidence.js', '/static/js/dossier.js', '/static/js/dossier_render.js'];

const pathOf = (request) => (typeof request === 'string' ? request : new URL(request.url).pathname);

function response(body, ok = true) {
  return { body, ok, clone: () => response(body, ok) };
}

function loadWorker({ online = true, status = true } = {}) {
  const listeners = {};
  const store = new Map();
  const fetched = [];
  const cache = {
    addAll: async (urls) => urls.forEach((u) => store.set(u, response(`cached:${u}`))),
    match: async (request) => store.get(pathOf(request)),
    put: async (request, value) => { store.set(pathOf(request), value); },
  };
  const caches = {
    open: async () => cache,
    keys: async () => ['old-cache', 'leaseguard-shell-v5'],
    delete: async (key) => { caches.deleted.push(key); return true; },
    match: cache.match,
    deleted: [],
  };
  const fetch = async (request) => {
    fetched.push(request.url);
    if (!online) { throw new TypeError('offline'); }
    return response(`network:${request.url}`, status);
  };
  const self = { addEventListener: (type, fn) => { listeners[type] = fn; }, location: { origin: ORIGIN } };
  vm.runInNewContext(SOURCE, { self, caches, fetch, URL, Response: { error: () => 'error' }, Promise, Object });
  return { listeners, caches, store, fetched };
}

async function dispatch(listeners, type, request) {
  let result;
  const waited = [];
  listeners[type]({ request, respondWith: (p) => { result = p; }, waitUntil: (p) => { waited.push(p); } });
  const value = result ? await result : undefined;
  await Promise.all(waited);
  return value;
}

const req = (path, mode = 'no-cors', method = 'GET', origin = ORIGIN) => ({ url: `${origin}${path}`, mode, method });
const body = (value) => value?.body ?? value;

test('install precaches the first-screen shell but not the lazily loaded dossier modules', async () => {
  const { listeners, caches, store } = loadWorker();
  await dispatch(listeners, 'install');
  assert.ok(store.has('/offline.html') && store.has('/static/js/main.js') && store.has('/static/js/lazy.js'));
  LAZY_MODULES.forEach((path) => assert.equal(store.has(path), false, path));
  await dispatch(listeners, 'activate');
  assert.deepEqual(caches.deleted, ['old-cache']);
});

test('API, POST and cross-origin requests are never intercepted', async () => {
  const { listeners } = loadWorker();
  assert.equal(await dispatch(listeners, 'fetch', req('/api/analyze', 'cors', 'POST')), undefined);
  assert.equal(await dispatch(listeners, 'fetch', req('/api/meta')), undefined);
  assert.equal(await dispatch(listeners, 'fetch', req('/x.js', 'cors', 'GET', 'https://cdn.example')), undefined);
});

test('cached assets are served at once and refreshed in the background', async () => {
  const { listeners, store, fetched } = loadWorker();
  await dispatch(listeners, 'install');
  const served = await dispatch(listeners, 'fetch', req('/static/css/styles.css'));
  assert.equal(body(served), 'cached:/static/css/styles.css');
  assert.deepEqual(fetched, [`${ORIGIN}/static/css/styles.css`]);
  assert.equal(body(store.get('/static/css/styles.css')), `network:${ORIGIN}/static/css/styles.css`);
});

test('a lazily loaded module is fetched on first use and cached for offline use', async () => {
  const { listeners, store } = loadWorker();
  const served = await dispatch(listeners, 'fetch', req('/static/js/dossier.js'));
  assert.equal(body(served), `network:${ORIGIN}/static/js/dossier.js`);
  assert.ok(store.has('/static/js/dossier.js'));
});

test('failed responses are not cached, and a failed background refresh keeps the cached copy', async () => {
  const failing = loadWorker({ status: false });
  await dispatch(failing.listeners, 'fetch', req('/static/js/missing.js'));
  assert.equal(failing.store.has('/static/js/missing.js'), false);
  const offline = loadWorker({ online: false });
  offline.store.set('/static/css/styles.css', response('cached-css'));
  assert.equal(body(await dispatch(offline.listeners, 'fetch', req('/static/css/styles.css'))), 'cached-css');
});

test('navigations fall back to the offline page', async () => {
  const offline = loadWorker({ online: false });
  await dispatch(offline.listeners, 'install');
  assert.equal(body(await dispatch(offline.listeners, 'fetch', req('/', 'navigate'))), 'cached:/offline.html');
  const empty = loadWorker({ online: false });
  assert.equal(await dispatch(empty.listeners, 'fetch', req('/', 'navigate')), 'error');
  const online = loadWorker();
  assert.equal(body(await dispatch(online.listeners, 'fetch', req('/', 'navigate'))), `network:${ORIGIN}/`);
});
