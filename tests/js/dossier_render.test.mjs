import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dataTable, eventsTable, filesTable, findingsElements, hashStatus, renderDossier, rupees } from '../../static/js/dossier_render.js';
import { loadPage } from './helpers.mjs';

const DOSSIER = {
  files: [{ annexure: 'A-1', name: 'chat.txt', sha256: 'ab'.repeat(32), hash_matches: true }],
  events: [
    { date: '2026-03-12', title: 'Refund promised', actor: 'Ravi', quote: 'I will <b>return</b> it', annexure: 'A-1' },
    { date: null, title: 'Move-out / handover', actor: '', quote: 'vacated', annexure: 'A-1' },
  ],
  ledger: { deposit: 250000, deposit_source: 'rental agreement', refunded: 0, deductions_claimed: 60000, outstanding: 250000 },
  contradictions: ['Ravi promised a refund, then later claimed deductions.'],
  limitation_deadline: '2029-08-31',
  checklist: ['Add proof of move-out.'],
};

test('rupees and hash status', () => {
  assert.equal(rupees(250000), 'Rs. 2,50,000');
  assert.equal(rupees(null), 'Not found');
  assert.equal(hashStatus(true), '✔ Matches your browser');
  assert.equal(hashStatus(false), '✖ Changed during upload');
  assert.equal(hashStatus(null), 'Not checked');
});

test('tables have captions, scoped headers and safe text', () => {
  const { document } = loadPage();
  const table = eventsTable(document, DOSSIER.events);
  assert.equal(table.className, 'table-wrap');
  assert.equal(table.getAttribute('role'), 'region');
  assert.equal(table.getAttribute('tabindex'), '0');
  assert.equal(table.getAttribute('aria-label'), 'List of dates and events (quotes are verbatim)');
  assert.ok(table.querySelector('caption'));
  assert.equal(table.querySelectorAll('th[scope="col"]').length, 5);
  assert.equal(table.querySelector('b'), null);
  assert.match(table.textContent, /Date needed/);
  const files = filesTable(document, DOSSIER.files);
  assert.equal(files.getAttribute('role'), 'region');
  assert.equal(files.getAttribute('tabindex'), '0');
  assert.equal(files.getAttribute('aria-label'), 'Index of evidence (SHA-256 fingerprints)');
  assert.match(files.textContent, /Matches your browser/);
  assert.equal(dataTable(document, 'c', ['a'], []).querySelectorAll('tbody tr').length, 0);
});

test('findings list ledger, contradictions, limitation and checklist', () => {
  const { document } = loadPage();
  const text = findingsElements(document, DOSSIER).map((n) => n.textContent).join(' ');
  for (const expected of ['Rs. 2,50,000', 'promised a refund', '2029-08-31', 'Add proof of move-out']) {
    assert.ok(text.includes(expected), expected);
  }
  const clean = findingsElements(document, { ...DOSSIER, contradictions: [], limitation_deadline: null, checklist: [] });
  assert.match(clean.map((n) => n.textContent).join(' '), /No gaps found/);
});

test('renderDossier handles an empty timeline', () => {
  const { document } = loadPage();
  const box = document.getElementById('dossier');
  renderDossier(document, box, DOSSIER);
  assert.equal(box.querySelectorAll('table').length, 2);
  renderDossier(document, box, { ...DOSSIER, events: [] });
  assert.match(box.textContent, /No dated events/);
});
