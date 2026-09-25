import { test } from 'node:test';
import assert from 'node:assert/strict';
import { bindDossier, dossierBody, selectedFiles } from '../../static/js/dossier.js';
import { renderOptions } from '../../static/js/render.js';
import { fakeFetch, flush, loadPage } from './helpers.mjs';
import { createApi } from '../../static/js/api.js';
import { download, runAction } from '../../static/js/main.js';

const DOSSIER = { files: [], events: [], ledger: { deposit: null, deposit_source: 'not found', refunded: 0, deductions_claimed: 0, outstanding: null }, contradictions: [], limitation_deadline: null, checklist: [], next_steps: [] };

function page() {
  const { window, document } = loadPage();
  renderOptions(document, document.getElementById('language'), ['English', 'Hindi']);
  Object.defineProperty(window, 'crypto', { value: globalThis.crypto });
  window.URL.createObjectURL = () => 'blob:z';
  window.URL.revokeObjectURL = () => undefined;
  return { window, document };
}

test('selectedFiles prefers chosen files over samples', () => {
  const { document } = page();
  const state = { samples: [new File(['s'], 's.txt')] };
  assert.equal(selectedFiles(document, state)[0].name, 's.txt');
  Object.defineProperty(document.getElementById('evidence-files'), 'files', { value: [new File(['c'], 'c.txt')] });
  assert.equal(selectedFiles(document, state)[0].name, 'c.txt');
  assert.deepEqual(selectedFiles(page().document, { samples: null }), []);
});

test('dossierBody includes lease only when reviewed and ticked', async () => {
  const { document } = page();
  document.getElementById('tenant-name').value = ' Priya ';
  const state = { samples: [new File(['x'], 'x.txt')], current: { document: { text: 'lease' } } };
  const body = await dossierBody(document, state, globalThis.crypto.subtle);
  assert.deepEqual(body.lease, { text: 'lease' });
  assert.equal(body.parties.tenant, 'Priya');
  assert.equal(body.files[0].client_sha256.length, 64);
  document.getElementById('use-lease').checked = false;
  assert.equal((await dossierBody(document, state, globalThis.crypto.subtle)).lease, null);
});

test('sample, build and download flow', async () => {
  const { window, document } = page();
  const fetch = fakeFetch({
    '/api/sample': () => ({ body: { evidence: { 'chat.txt': 'hello' } } }),
    '/api/dossier': () => ({ body: DOSSIER }),
    '/api/dossier/pdf': () => ({ blob: new Blob(['%PDF-']) }),
  });
  const state = { current: null, samples: null, dossier: null };
  bindDossier(document, window, { api: createApi(fetch), state, run: runAction, download });
  document.getElementById('load-evidence-sample').click();
  await flush();
  assert.match(document.getElementById('evidence-help').textContent, /Sample loaded: chat.txt/);
  document.getElementById('dossier-form').dispatchEvent(new window.Event('submit', { cancelable: true }));
  await flush(); await flush();
  assert.equal(document.getElementById('dossier-pdf-button').hidden, false);
  document.getElementById('dossier-pdf-button').click();
  await flush(); await flush();
  assert.deepEqual(fetch.calls.map((c) => c.path), ['/api/sample', '/api/dossier', '/api/dossier/pdf']);
});

test('errors are announced', async () => {
  const { window, document } = page();
  bindDossier(document, window, { api: createApi(fakeFetch({})), state: { samples: null }, run: runAction, download });
  document.getElementById('dossier-form').dispatchEvent(new window.Event('submit', { cancelable: true }));
  await flush();
  assert.match(document.getElementById('dossier-error').textContent, /between 1 and 10/);
});
