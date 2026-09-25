import { test } from 'node:test';
import assert from 'node:assert/strict';
import { h, replaceChildren, setBusy, setMessage } from '../../static/js/dom.js';
import { loadPage } from './helpers.mjs';

test('h sets attributes and text safely', () => {
  const { document } = loadPage();
  const el = h(document, 'p', { class: 'x', hidden: true, open: false, 'data-n': 3 }, ['<b>not markup</b>', null]);
  assert.equal(el.className, 'x');
  assert.equal(el.getAttribute('hidden'), '');
  assert.equal(el.hasAttribute('open'), false);
  assert.equal(el.getAttribute('data-n'), '3');
  assert.equal(el.querySelector('b'), null);
  assert.equal(el.textContent, '<b>not markup</b>');
});

test('replaceChildren, setMessage and setBusy', () => {
  const { document } = loadPage();
  const box = h(document, 'div', {}, ['old']);
  replaceChildren(box, [h(document, 'span', {}, ['new'])]);
  assert.equal(box.textContent, 'new');
  setMessage(box, 'hello');
  assert.equal(box.textContent, 'hello');
  setMessage(null, 'ignored');
  const button = h(document, 'button');
  setBusy(button, box, true);
  assert.equal(button.disabled, true);
  assert.equal(box.getAttribute('aria-busy'), 'true');
  setBusy(null, null, false);
});
