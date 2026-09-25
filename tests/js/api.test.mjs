import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ApiError, EXPIRED, MAX_REQUEST_BYTES, MAX_UPLOAD_BYTES, createApi, encodeFile, errorDetails, postReference } from '../../static/js/api.js';
import { fakeFetch } from './helpers.mjs';

test('postJson sends JSON and returns the body', async () => {
  const fetch = fakeFetch({ '/api/x': () => ({ body: { ok: 1 } }) });
  const api = createApi(fetch);
  assert.deepEqual(await api.postJson('/api/x', { a: 1 }), { ok: 1 });
  assert.equal(fetch.calls[0].init.headers['Content-Type'], 'application/json');
  assert.equal(fetch.calls[0].init.body, '{"a":1}');
  assert.deepEqual(await api.getJson('/api/x'), { ok: 1 });
  assert.ok((await api.postForBlob('/api/x', {})) instanceof Blob);
});

test('structured server errors become ApiError', async () => {
  const api = createApi(fakeFetch({ '/api/x': () => ({ status: 400, body: { error: { message: 'Bad file.', code: 'invalid_document' } } }) }));
  await assert.rejects(api.postJson('/api/x', {}), (error) => error instanceof ApiError
    && error.message === 'Bad file.' && error.status === 400 && error.code === 'invalid_document');
});

test('network failures and unreadable errors', async () => {
  await assert.rejects(createApi(fakeFetch({})).getJson('/api/none'), /offline/);
  const broken = { status: 502, json: async () => { throw new SyntaxError('x'); } };
  assert.deepEqual(await errorDetails(broken), { message: 'Request failed (502).', code: '' });
  assert.deepEqual(await errorDetails({ status: 500, json: async () => ({}) }), { message: 'Request failed (500).', code: '' });
  assert.deepEqual(await errorDetails({ status: 404, json: async () => ({ error: { message: 'Gone.' } }) }), { message: 'Gone.', code: '' });
});

test('encodeFile encodes and enforces the size limit', async () => {
  assert.equal(await encodeFile(new Blob(['hello'])), btoa('hello'));
  const big = { size: MAX_UPLOAD_BYTES + 1 };
  await assert.rejects(encodeFile(big), /5 MB/);
});

test('oversized bodies are refused before anything is sent', async () => {
  const fetch = fakeFetch({ '/api/x': () => ({ body: {} }) });
  await assert.rejects(createApi(fetch).postJson('/api/x', { data: 'a'.repeat(MAX_REQUEST_BYTES) }), /8 MB/);
  assert.equal(fetch.calls.length, 0);
});

test('postReference sends the ID, and the full body only if the server has expired it', async () => {
  let expired = false;
  const fetch = fakeFetch({
    '/api/r': (init) => (expired && init.body.includes('report_id')
      ? { status: 404, body: { error: { message: 'Expired.', code: EXPIRED } } }
      : { body: { sent: JSON.parse(init.body) } }),
  });
  const api = createApi(fetch);
  const full = () => ({ document: { text: 'long agreement' } });
  assert.deepEqual(await postReference(api.postJson, '/api/r', { report_id: 'a' }, full), { sent: { report_id: 'a' } });
  assert.deepEqual(await postReference(api.postJson, '/api/r', null, full), { sent: full() });
  expired = true;
  assert.deepEqual(await postReference(api.postJson, '/api/r', { report_id: 'a' }, full), { sent: full() });
  assert.equal(fetch.calls.length, 4);
});

test('postReference passes other errors through', async () => {
  const api = createApi(fakeFetch({ '/api/r': () => ({ status: 429, body: { error: { message: 'Slow down.', code: 'rate_limited' } } }) }));
  await assert.rejects(postReference(api.postJson, '/api/r', { report_id: 'a' }, () => ({})), /Slow down/);
});
