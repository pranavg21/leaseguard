/**
 * @module dossier
 * Wire the deposit-recovery form: hash files in the browser, build the dossier, download the PDF.
 */

import { postReference } from './api.js';
import { renderDossier } from './dossier_render.js';
import { byId } from './forms.js';
import { prepareFiles, sampleFiles } from './evidence.js';

/**
 * Read the selected (or sample) evidence files.
 * @param {Document} doc - The document.
 * @param {{ samples: File[] | null }} state - Shared page state.
 * @returns {File[]} The files.
 */
export function selectedFiles(doc, state) {
  const chosen = Array.from(byId(doc, 'evidence-files').files ?? []);
  return chosen.length ? chosen : state.samples ?? [];
}

/**
 * Build the dossier request body.
 * @param {Document} doc - The document.
 * @param {{ samples: File[] | null, current: any }} state - Shared page state.
 * @param {SubtleCrypto} subtle - Web Crypto.
 * @returns {Promise<object>} The request body.
 */
export async function dossierBody(doc, state, subtle) {
  const useLease = byId(doc, 'use-lease').checked && state.current?.document;
  return {
    files: await prepareFiles(selectedFiles(doc, state), subtle),
    lease: useLease ? state.current.document : null,
    parties: {
      tenant: byId(doc, 'tenant-name').value.trim(),
      landlord: byId(doc, 'landlord-name').value.trim(),
      property_address: byId(doc, 'property-address').value.trim(),
    },
    language: byId(doc, 'language').value || 'English',
  };
}

/**
 * Attach the dossier handlers.
 * @param {Document} doc - The document.
 * @param {Window} win - The window.
 * @param {{ api: any, state: any, run: Function, download: Function }} deps - Shared helpers.
 * @returns {void}
 */
export function bindDossier(doc, win, deps) {
  const { api, state, run, download } = deps;
  const ids = { button: 'dossier-button', region: 'dossier', error: 'dossier-error' };
  byId(doc, 'load-evidence-sample').addEventListener('click', async () => {
    state.samples = sampleFiles((await api.getJson('/api/sample')).evidence);
    byId(doc, 'evidence-files').value = '';
    byId(doc, 'evidence-help').textContent = `Sample loaded: ${state.samples.map((f) => f.name).join(', ')}.`;
  });
  byId(doc, 'dossier-form').addEventListener('submit', (event) => {
    event.preventDefault();
    run(doc, ids, async () => {
      state.dossier = await dossierBody(doc, state, win.crypto.subtle);
      const dossier = await api.postJson('/api/dossier', state.dossier);
      state.dossierId = dossier.dossier_id ?? null;
      renderDossier(doc, byId(doc, 'dossier'), dossier);
      byId(doc, 'dossier-pdf-button').hidden = false;
    });
  });
  byId(doc, 'dossier-pdf-button').addEventListener('click', () => run(doc, { ...ids, button: 'dossier-pdf-button' }, async () => {
    const reference = state.dossierId && { dossier_id: state.dossierId };
    const pdf = await postReference(api.postForBlob, '/api/dossier/pdf', reference, () => state.dossier);
    download(doc, win, pdf, 'leaseguard-dossier.pdf');
  }));
}
