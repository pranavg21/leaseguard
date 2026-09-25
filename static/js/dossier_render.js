/**
 * @module dossier_render
 * Render the deposit-recovery dossier as accessible tables and lists.
 */

import { dataTable, h, replaceChildren } from './dom.js';

export { dataTable } from './dom.js';

/** Indian digit grouping for rupee amounts. */
const RUPEES = new Intl.NumberFormat('en-IN');

/**
 * Format a rupee amount, or say it is unknown.
 * @param {number | null} amount - Whole rupees.
 * @returns {string} For example "Rs. 2,50,000".
 */
export function rupees(amount) {
  return amount === null || amount === undefined ? 'Not found' : `Rs. ${RUPEES.format(amount)}`;
}

/**
 * Describe whether the browser and server hashes agree.
 * @param {boolean | null} matches - Comparison result, or null if the browser sent no hash.
 * @returns {string} Accessible status text.
 */
export function hashStatus(matches) {
  if (matches === null || matches === undefined) {
    return 'Not checked';
  }
  return matches ? '✔ Matches your browser' : '✖ Changed during upload';
}

/**
 * Evidence index with fingerprints.
 * @param {Document} doc - The owning document.
 * @param {any[]} files - Files from the API.
 * @returns {HTMLElement} The table region.
 */
export function filesTable(doc, files) {
  const rows = files.map((f) => [f.annexure, f.name, h(doc, 'span', { class: 'hash' }, [f.sha256]), hashStatus(f.hash_matches)]);
  return dataTable(doc, 'Index of evidence (SHA-256 fingerprints)', ['Annexure', 'File', 'SHA-256', 'Integrity'], rows);
}

/**
 * Chronological list of dates and events.
 * @param {Document} doc - The owning document.
 * @param {any[]} events - Events from the API.
 * @returns {HTMLElement} The table region.
 */
export function eventsTable(doc, events) {
  const rows = events.map((e) => [e.date ?? '⚠️ Date needed', e.title, e.actor || '-', h(doc, 'q', {}, [e.quote]), e.annexure]);
  return dataTable(doc, 'List of dates and events (quotes are verbatim)', ['Date', 'Event', 'By', 'Evidence', 'Annexure'], rows);
}

/**
 * Ledger, contradictions, limitation reminder and checklist.
 * @param {Document} doc - The owning document.
 * @param {any} data - The dossier from the API.
 * @returns {HTMLElement[]} The elements.
 */
export function findingsElements(doc, data) {
  const { ledger } = data;
  const items = [
    `Deposit: ${rupees(ledger.deposit)} (source: ${ledger.deposit_source})`,
    `Refunded: ${rupees(ledger.refunded)}`,
    `Deductions claimed: ${rupees(ledger.deductions_claimed)}`,
    `Outstanding before disputed deductions: ${rupees(ledger.outstanding)}`,
  ];
  const notes = [
    ...data.contradictions.map((text) => `⚠️ ${text}`),
    ...(data.limitation_deadline ? [`ℹ️ Money claims generally must be filed within three years; that is about ${data.limitation_deadline}. Confirm with a lawyer.`] : []),
    ...data.checklist.map((text) => `☐ ${text}`),
  ];
  return [
    h(doc, 'h3', {}, ['Deposit ledger']),
    h(doc, 'ul', {}, items.map((text) => h(doc, 'li', {}, [text]))),
    h(doc, 'h3', {}, ['Findings and to-do']),
    notes.length ? h(doc, 'ul', {}, notes.map((text) => h(doc, 'li', {}, [text]))) : h(doc, 'p', {}, ['✅ No gaps found.']),
  ];
}

/**
 * Render the full dossier.
 * @param {Document} doc - The owning document.
 * @param {Element} container - Where to render.
 * @param {any} data - The dossier from the API.
 * @returns {void}
 */
export function renderDossier(doc, container, data) {
  replaceChildren(container, [
    filesTable(doc, data.files),
    h(doc, 'h3', {}, ['Timeline']),
    data.events.length ? eventsTable(doc, data.events) : h(doc, 'p', {}, ['No dated events were found in the evidence.']),
    ...findingsElements(doc, data),
  ]);
}
