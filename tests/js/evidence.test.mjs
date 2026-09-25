import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { MAX_EVIDENCE_FILES, MAX_EVIDENCE_TOTAL_BYTES, prepareFile, prepareFiles, sampleFiles, sha256Hex } from '../../static/js/evidence.js';

const { subtle } = globalThis.crypto;

test('sha256Hex matches Node crypto', async () => {
  const bytes = new TextEncoder().encode('deposit');
  assert.equal(await sha256Hex(bytes.buffer, subtle), createHash('sha256').update('deposit').digest('hex'));
});

test('prepareFile hashes and encodes', async () => {
  const payload = await prepareFile(new File(['hello'], 'a.txt'), subtle);
  assert.equal(payload.name, 'a.txt');
  assert.equal(payload.content_base64, btoa('hello'));
  assert.equal(payload.client_sha256, createHash('sha256').update('hello').digest('hex'));
});

test('empty files and bad counts are rejected', async () => {
  await assert.rejects(prepareFile(new File([], 'empty.txt'), subtle), /between 1 byte and 5 MB/);
  await assert.rejects(prepareFiles([], subtle), /between 1 and 10/);
  const many = Array.from({ length: MAX_EVIDENCE_FILES + 1 }, (_, i) => new File(['x'], `${i}.txt`));
  await assert.rejects(prepareFiles(many, subtle), /between 1 and 10/);
  assert.equal((await prepareFiles([new File(['x'], 'x.txt')], subtle)).length, 1);
});

test('sampleFiles creates named text files', async () => {
  const [file] = sampleFiles({ 'chat.txt': 'hi' });
  assert.equal(file.name, 'chat.txt');
  assert.equal(await file.text(), 'hi');
});

test('files larger than the total limit are rejected before any is read', async () => {
  let read = false;
  const big = { name: 'big.pdf', size: MAX_EVIDENCE_TOTAL_BYTES / 2 + 1, arrayBuffer: async () => { read = true; return new ArrayBuffer(1); } };
  await assert.rejects(prepareFiles([big, { ...big }], subtle), /5 MB in total/);
  assert.equal(read, false);
});
