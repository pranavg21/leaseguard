import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const SOURCE = readFileSync(new URL('../../static/sw.js', import.meta.url), 'utf8');

function loadWorker({ online = true } = {}) {
  const listeners = {};
  const store = new Map();
  const caches = {
    open: async () => ({ addAll: async (urls) => urls.forEach((u) => store.set(u, `cached:${u}`)) }),
    keys: async () => ['old-cache', 'leaseguard-shell-v4'],
    delete: async (key) => { caches.deleted.push(key); return true; },
    match: async (request) => store.get(typeof request === 'string' ? request : new URL(request.url).pathname),
    deleted: [],
  };
  const fetch = async (request) => {
    if (!online) { throw new TypeError('offline'); }
    return `network:${request.url}`;
  };
  const context = { self: { addEventListener: (type, fn) => { listeners[type] = fn; } }, caches, fetch, URL, Response: { error: () => 'error' }, Promise, Object };
  vm.runInNewContext(SOURCE, context);
  return { listeners, caches, store };
}

async function dispatch(listeners, type, request) {
  let result;
  let waited;
  listeners[type]({ request, respondWith: (p) => { result = p; }, waitUntil: (p) => { waited = p; } });
  await waited;
  return result ? await result : undefined;
}

const req = (path, mode = 'no-cors', method = 'GET') => ({ url: `http://localhost${path}`, mode, method });

test('install caches the shell and activate removes old caches', async () => {
  const { listeners, caches, store } = loadWorker();
  await dispatch(listeners, 'install');
  assert.ok(store.has('/offline.html') && store.has('/static/js/main.js'));
  await dispatch(listeners, 'activate');
  assert.deepEqual(caches.deleted, ['old-cache']);
});

test('API and POST requests are never intercepted', async () => {
  const { listeners } = loadWorker();
  assert.equal(await dispatch(listeners, 'fetch', req('/api/analyze', 'cors', 'POST')), undefined);
  assert.equal(await dispatch(listeners, 'fetch', req('/api/meta')), undefined);
});

test('static assets are cache-first', async () => {
  const { listeners } = loadWorker();
  await dispatch(listeners, 'install');
  assert.equal(await dispatch(listeners, 'fetch', req('/static/css/styles.css')), 'cached:/static/css/styles.css');
  assert.equal(await dispatch(listeners, 'fetch', req('/static/new.js')), 'network:http://localhost/static/new.js');
});

test('navigations fall back to the offline page', async () => {
  const offline = loadWorker({ online: false });
  await dispatch(offline.listeners, 'install');
  assert.equal(await dispatch(offline.listeners, 'fetch', req('/', 'navigate')), 'cached:/offline.html');
  const empty = loadWorker({ online: false });
  assert.equal(await dispatch(empty.listeners, 'fetch', req('/', 'navigate')), 'error');
  const online = loadWorker();
  assert.equal(await dispatch(online.listeners, 'fetch', req('/', 'navigate')), 'network:http://localhost/');
});
