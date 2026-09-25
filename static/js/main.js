/**
 * @module main
 * Wire the page: load options, handle forms, and register the offline service worker.
 */

import { createApi, postReference } from './api.js';
import { loadWhenNeeded, once } from './lazy.js';
import { setBusy, setMessage } from './dom.js';
import { byId, readContext, readDocument, textDocument } from './forms.js';
import { renderAnswer, renderComparison, renderOptions, renderReport, renderRoles } from './render.js';
import { errorText, modeText } from './view.js';

/** Shown when the deposit-recovery code cannot be downloaded; the next click retries. */
export const DOSSIER_LOAD_ERROR = 'The deposit-recovery tools could not load. Check your connection and try again.';

/**
 * Build the handler that reports a failed download of the deposit-recovery code.
 * @param {Document} doc - The document.
 * @returns {() => void} The handler.
 */
export function dossierLoadFailed(doc) {
  return () => setMessage(byId(doc, 'dossier-error'), DOSSIER_LOAD_ERROR);
}

/**
 * Run an async form action with busy state and error reporting.
 * @param {Document} doc - The document.
 * @param {{button: string, region: string, error: string}} ids - Element ids.
 * @param {() => Promise<void>} action - The work to do.
 * @returns {Promise<void>}
 */
export async function runAction(doc, ids, action) {
  const button = byId(doc, ids.button);
  const region = byId(doc, ids.region);
  setMessage(byId(doc, ids.error), '');
  setBusy(button, region, true);
  try {
    await action();
  } catch (error) {
    setMessage(byId(doc, ids.error), errorText(error));
  } finally {
    setBusy(button, region, false);
  }
}

/**
 * Save a blob as a file download.
 * @param {Document} doc - The document.
 * @param {Window} win - The window (for URL APIs).
 * @param {Blob} blob - The file content.
 * @param {string} name - The file name.
 * @returns {void}
 */
export function download(doc, win, blob, name) {
  const url = win.URL.createObjectURL(blob);
  const link = doc.createElement('a');
  link.href = url;
  link.download = name;
  link.click();
  win.URL.revokeObjectURL(url);
}

/**
 * Attach every form handler.
 * @param {Document} doc - The document.
 * @param {Window} win - The window.
 * @param {ReturnType<typeof createApi>} api - The API client.
 * @param {{ current: any, reportId: string | null }} state - Shared page state: the reviewed agreement and,
 *   once reviewed, the server's `report_id`, so follow-ups send the ID instead of the whole document.
 * @returns {void}
 */
export function bindForms(doc, win, api, state) {
  const submit = (id, handler) => byId(doc, id).addEventListener('submit', (event) => {
    event.preventDefault();
    handler();
  });

  submit('analyze-form', () => runAction(doc, { button: 'analyze-button', region: 'results', error: 'analyze-error' }, async () => {
    state.current = { document: await readDocument(doc), context: readContext(doc) };
    const report = await api.postJson('/api/analyze', state.current);
    state.reportId = report.report_id ?? null;
    renderReport(doc, byId(doc, 'results'), report);
    byId(doc, 'results-section').hidden = false;
    byId(doc, 'ask-section').hidden = false;
    byId(doc, 'results-heading').focus();
  }));

  submit('ask-form', () => runAction(doc, { button: 'ask-button', region: 'answer', error: 'ask-error' }, async () => {
    const question = byId(doc, 'question').value.trim();
    const reference = state.reportId && { report_id: state.reportId, question };
    renderAnswer(doc, byId(doc, 'answer'), await postReference(api.postJson, '/api/ask', reference, () => ({ ...state.current, question })));
  }));

  submit('compare-form', () => runAction(doc, { button: 'compare-button', region: 'comparison', error: 'compare-error' }, async () => {
    const body = {
      original: textDocument(byId(doc, 'original-text').value),
      revised: textDocument(byId(doc, 'revised-text').value),
      context: readContext(doc),
    };
    renderComparison(doc, byId(doc, 'comparison'), (await api.postJson('/api/compare', body)).changes);
  }));

  bindPacket(doc, win, api, state);
}

/**
 * Attach the consultation-packet download, which sends only the report ID when it has one.
 * @param {Document} doc - The document.
 * @param {Window} win - The window.
 * @param {ReturnType<typeof createApi>} api - The API client.
 * @param {{ current: any, reportId: string | null }} state - Shared page state.
 * @returns {void}
 */
export function bindPacket(doc, win, api, state) {
  byId(doc, 'packet-button').addEventListener('click', () => runAction(doc, { button: 'packet-button', region: 'results', error: 'analyze-error' }, async () => {
    const reference = state.reportId && { report_id: state.reportId };
    download(doc, win, await postReference(api.postForBlob, '/api/packet', reference, () => state.current), 'leaseguard-packet.pdf');
  }));
}

/**
 * Attach the sample-loading buttons.
 * @param {Document} doc - The document.
 * @param {ReturnType<typeof createApi>} api - The API client.
 * @returns {void}
 */
export function bindSamples(doc, api) {
  byId(doc, 'load-sample').addEventListener('click', async () => {
    const sample = await api.getJson('/api/sample');
    byId(doc, 'document-text').value = sample.original;
    byId(doc, 'document-file').value = '';
  });
  byId(doc, 'load-compare-sample').addEventListener('click', async () => {
    const sample = await api.getJson('/api/sample');
    byId(doc, 'original-text').value = sample.original;
    byId(doc, 'revised-text').value = sample.revised;
  });
}

/**
 * Dynamically import and bind the deposit-recovery dossier (three modules the review never needs).
 * @param {Document} doc - The document.
 * @param {Window} win - The window.
 * @param {object} deps - Shared helpers passed to bindDossier.
 * @returns {Promise<void>}
 */
export async function loadDossier(doc, win, deps) {
  const { bindDossier } = await import('./dossier.js');
  bindDossier(doc, win, deps);
}

/**
 * Initialise the page.
 * @param {Document} doc - The document.
 * @param {Window} win - The window.
 * @param {typeof fetch} fetchFn - The fetch implementation.
 * @returns {Promise<void>}
 */
export async function init(doc, win, fetchFn) {
  const api = createApi(fetchFn);
  const state = { current: null, reportId: null, samples: null, dossier: null, dossierId: null, loadDossier: null };
  bindForms(doc, win, api, state);
  state.loadDossier = once(() => loadDossier(doc, win, { api, state, run: runAction, download }));
  loadWhenNeeded(win, byId(doc, 'dossier-section'), state.loadDossier, dossierLoadFailed(doc));
  bindSamples(doc, api);
  try {
    const meta = await api.getJson('/api/meta');
    renderRoles(doc, byId(doc, 'role-options'), meta.roles);
    renderOptions(doc, byId(doc, 'state'), meta.states);
    renderOptions(doc, byId(doc, 'language'), meta.languages);
    setMessage(byId(doc, 'ai-mode'), modeText(meta.ai_mode));
  } catch (error) {
    setMessage(byId(doc, 'analyze-error'), errorText(error));
  }
  if ('serviceWorker' in win.navigator) {
    win.navigator.serviceWorker.register('/sw.js').catch(() => undefined);
  }
}

if (globalThis.document && globalThis.window && !globalThis.window.LEASEGUARD_NO_AUTOSTART) {
  init(globalThis.document, globalThis.window, globalThis.fetch.bind(globalThis));
}
