import { test } from 'node:test';
import assert from 'node:assert/strict';
import { findingElement, gapsElements, renderAnswer, renderComparison, renderOptions, renderReport, renderRoles } from '../../static/js/render.js';
import { loadPage } from './helpers.mjs';

const FINDING = {
  risk: 'HIGH', heading: '6. Entry', category_title: 'Privacy and entry', reason: 'Enter <b>any</b> time.',
  quote: 'may enter at any time', quote_verified: true, baseline: '24 hours notice', question_for_lawyer: 'Is this fair?',
};
const REPORT = {
  counts: { HIGH: 1, MEDIUM: 0, FAIR: 0 }, findings: [FINDING], gaps: [], coverage_complete: true, context_notes: ['Register it.'],
  key_terms: [{ label: 'Monthly rent', value: 'Rs. 25,000', quote: 'rent of Rs. 25,000' }, { label: 'Lock-in', value: 'Not stated', quote: '' }],
  next_steps: [{ title: 'Negotiate before you sign', detail: 'Ask for the fair baseline.' }],
};

test('options and role radios', () => {
  const { document } = loadPage();
  const select = document.getElementById('state');
  renderOptions(document, select, ['A', 'B']);
  assert.equal(select.options.length, 2);
  const box = document.getElementById('role-options');
  renderRoles(document, box, ['tenant', 'landlord']);
  assert.equal(box.querySelector('#role-tenant').checked, true);
  assert.equal(box.querySelector('label[for="role-landlord"]').textContent, 'Landlord');
});

test('finding shows risk in words and never renders markup', () => {
  const { document } = loadPage();
  const el = findingElement(document, FINDING);
  assert.equal(el.hasAttribute('open'), true);
  assert.match(el.querySelector('summary').textContent, /High risk 6\. Entry/);
  assert.equal(el.querySelector('b'), null);
  assert.match(el.textContent, /verified/);
});

test('report includes counts summary, notes and gaps', () => {
  const { document } = loadPage();
  const box = document.getElementById('results');
  renderReport(document, box, REPORT);
  assert.match(box.querySelector('.counts').getAttribute('aria-label'), /1 high risk/);
  assert.match(box.textContent, /Register it\./);
  assert.match(box.textContent, /Every protection/);
});

test('gap states', () => {
  const { document } = loadPage();
  const text = (report) => gapsElements(document, report).map((n) => n.textContent).join(' ');
  assert.match(text({ coverage_complete: false, gaps: [] }), /skipped/);
  assert.match(text({ coverage_complete: true, gaps: [{ message: 'No deposit clause.' }] }), /No deposit clause/);
});

test('answers show quote only when grounded', () => {
  const { document } = loadPage();
  const box = document.getElementById('answer');
  renderAnswer(document, box, { answer: 'Yes.', grounded: true, heading: '6. Entry', quote: 'may enter' });
  assert.equal(box.querySelector('blockquote').textContent, 'may enter');
  renderAnswer(document, box, { answer: 'Not stated.', grounded: false });
  assert.equal(box.querySelector('blockquote'), null);
});

test('comparison table has caption and header scopes', () => {
  const { document } = loadPage();
  const box = document.getElementById('comparison');
  renderComparison(document, box, [{ category_title: 'Security deposit', direction: 'better', before: 'HIGH', after: null }]);
  const wrap = box.querySelector('.table-wrap');
  assert.ok(wrap);
  assert.equal(wrap.getAttribute('role'), 'region');
  assert.equal(wrap.getAttribute('tabindex'), '0');
  assert.equal(wrap.getAttribute('aria-label'), 'How each topic changed, worst changes first');
  assert.ok(box.querySelector('caption'));
  assert.equal(box.querySelectorAll('th[scope="col"]').length, 4);
  assert.match(box.querySelector('tbody').textContent, /Better.*High risk.*Not present/);
});

test('report shows key terms first and next steps last', () => {
  const { document } = loadPage();
  const box = document.getElementById('results');
  renderReport(document, box, REPORT);
  const terms = box.querySelector('[aria-label="Key terms at a glance"]');
  assert.ok(terms);
  assert.match(terms.textContent, /Monthly rent.*Rs\. 25,000/);
  assert.equal(terms.querySelector('q').textContent, 'rent of Rs. 25,000');
  const steps = box.querySelector('ol.steps');
  assert.equal(steps.children.length, 1);
  assert.match(steps.textContent, /Negotiate before you sign\. Ask for the fair baseline\./);
  assert.equal(box.lastElementChild, steps);
});
