import { test } from 'node:test';
import assert from 'node:assert/strict';
import { download, init, runAction } from '../../static/js/main.js';
import { fakeFetch, flush, loadPage } from './helpers.mjs';

const LEASE = 'x'.repeat(600);
const REPORT = { counts: { HIGH: 0, MEDIUM: 0, FAIR: 1 }, findings: [], gaps: [], coverage_complete: true, context_notes: [], key_terms: [], next_steps: [] };
const META = { roles: ['tenant', 'landlord'], states: ['Maharashtra'], languages: ['English'], ai_mode: 'offline' };

function routes() {
  return fakeFetch({
    '/api/meta': () => ({ body: META }),
    '/api/sample': () => ({ body: { original: LEASE, revised: LEASE } }),
    '/api/analyze': () => ({ body: REPORT }),
    '/api/ask': () => ({ body: { answer: 'Yes.', grounded: false } }),
    '/api/compare': () => ({ body: { changes: [] } }),
    '/api/packet': () => ({ blob: new Blob(['%PDF-']) }),
  });
}

async function boot() {
  const { window, document } = loadPage();
  const registered = [];
  Object.defineProperty(window.navigator, 'serviceWorker', { value: { register: async (p) => registered.push(p) } });
  window.URL.createObjectURL = () => 'blob:x';
  window.URL.revokeObjectURL = () => undefined;
  const fetch = routes();
  await init(document, window, fetch);
  return { window, document, fetch, registered };
}

const submit = (document, id) => document.getElementById(id).dispatchEvent(new document.defaultView.Event('submit', { cancelable: true }));

test('init loads options, mode and service worker', async () => {
  const { document, registered } = await boot();
  assert.equal(document.querySelectorAll('#state option').length, 1);
  assert.match(document.getElementById('ai-mode').textContent, /offline/);
  assert.deepEqual(registered, ['/sw.js']);
});

test('full flow: sample, analyse, ask, compare, packet', async () => {
  const { document, fetch } = await boot();
  document.getElementById('load-sample').click();
  document.getElementById('load-compare-sample').click();
  await flush();
  submit(document, 'analyze-form');
  await flush(); await flush();
  assert.equal(document.getElementById('results-section').hidden, false);
  document.getElementById('question').value = 'Can I leave?';
  submit(document, 'ask-form');
  submit(document, 'compare-form');
  document.getElementById('packet-button').click();
  await flush(); await flush();
  const paths = fetch.calls.map((call) => call.path);
  for (const path of ['/api/analyze', '/api/ask', '/api/compare', '/api/packet']) {
    assert.ok(paths.includes(path), path);
  }
  assert.match(document.getElementById('answer').textContent, /Yes\./);
});

test('errors are announced and buttons re-enabled', async () => {
  const { document } = await boot();
  submit(document, 'analyze-form');
  await flush();
  assert.match(document.getElementById('analyze-error').textContent, /500 characters/);
  assert.equal(document.getElementById('analyze-button').disabled, false);
});

test('meta failure is reported', async () => {
  const { window, document } = loadPage();
  Object.defineProperty(window.navigator, 'serviceWorker', { value: undefined, configurable: true });
  delete window.navigator.serviceWorker;
  await init(document, window, fakeFetch({}));
  assert.match(document.getElementById('analyze-error').textContent, /offline/);
});

test('runAction and download helpers', async () => {
  const { window, document } = loadPage();
  await runAction(document, { button: 'analyze-button', region: 'results', error: 'analyze-error' }, async () => {
    throw new Error('boom');
  });
  assert.equal(document.getElementById('analyze-error').textContent, 'boom');
  let revoked = '';
  window.URL.createObjectURL = () => 'blob:y';
  window.URL.revokeObjectURL = (url) => { revoked = url; };
  download(document, window, new Blob(['x']), 'a.pdf');
  assert.equal(revoked, 'blob:y');
});
