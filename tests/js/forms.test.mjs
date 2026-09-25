import { test } from 'node:test';
import assert from 'node:assert/strict';
import { MIN_TEXT_CHARS, byId, readContext, readDocument, textDocument } from '../../static/js/forms.js';
import { renderOptions, renderRoles } from '../../static/js/render.js';
import { loadPage } from './helpers.mjs';

function page() {
  const { document } = loadPage();
  renderRoles(document, byId(document, 'role-options'), ['tenant', 'landlord']);
  renderOptions(document, byId(document, 'state'), ['Maharashtra', 'Other']);
  renderOptions(document, byId(document, 'language'), ['English', 'Hindi']);
  return document;
}

test('readContext reads every field', () => {
  const document = page();
  byId(document, 'role-landlord').checked = true;
  byId(document, 'rent').value = '30000';
  byId(document, 'language').value = 'Hindi';
  assert.deepEqual(readContext(document), { role: 'landlord', state: 'Maharashtra', monthly_rent: 30000, language: 'Hindi' });
});

test('readContext defaults when nothing is checked', () => {
  const document = page();
  byId(document, 'role-tenant').checked = false;
  assert.equal(readContext(document).role, 'tenant');
  assert.equal(readContext(document).monthly_rent, null);
});

test('textDocument enforces minimum length', () => {
  assert.throws(() => textDocument('short'), /500 characters/);
  assert.deepEqual(textDocument(`  ${'a'.repeat(MIN_TEXT_CHARS)}  `), { text: 'a'.repeat(MIN_TEXT_CHARS) });
});

test('readDocument uses text when no file is chosen', async () => {
  const document = page();
  byId(document, 'document-text').value = 'x'.repeat(MIN_TEXT_CHARS);
  assert.deepEqual(await readDocument(document), { text: 'x'.repeat(MIN_TEXT_CHARS) });
});

test('readDocument prefers an uploaded file', async () => {
  const document = page();
  const file = new Blob(['hi']);
  Object.defineProperty(byId(document, 'document-file'), 'files', { value: [file] });
  assert.deepEqual(await readDocument(document), { file_base64: btoa('hi') });
});
