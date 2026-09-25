import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ApiError, MAX_UPLOAD_BYTES, createApi, encodeFile, errorMessage } from '../../static/js/api.js';
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
  const api = createApi(fakeFetch({ '/api/x': () => ({ status: 400, body: { error: { message: 'Bad file.' } } }) }));
  await assert.rejects(api.postJson('/api/x', {}), (error) => error instanceof ApiError && error.message === 'Bad file.' && error.status === 400);
});

test('network failures and unreadable errors', async () => {
  await assert.rejects(createApi(fakeFetch({})).getJson('/api/none'), /offline/);
  const broken = { status: 502, json: async () => { throw new SyntaxError('x'); } };
  assert.equal(await errorMessage(broken), 'Request failed (502).');
  assert.equal(await errorMessage({ status: 500, json: async () => ({}) }), 'Request failed (500).');
});

test('encodeFile encodes and enforces the size limit', async () => {
  assert.equal(await encodeFile(new Blob(['hello'])), btoa('hello'));
  const big = { size: MAX_UPLOAD_BYTES + 1 };
  await assert.rejects(encodeFile(big), /5 MB/);
});
