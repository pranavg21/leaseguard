/**
 * @module main
 * Wire the page: load options, handle forms, and register the offline service worker.
 */

import { createApi } from './api.js';
import { loadWhenNeeded, once } from './lazy.js';
import { setBusy, setMessage } from './dom.js';
import { byId, readContext, readDocument, textDocument } from './forms.js';
import { renderAnswer, renderComparison, renderOptions, renderReport, renderRoles } from './render.js';
import { errorText, modeText } from './view.js';

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
 * @param {{ current: any }} state - Shared page state; `current` holds the reviewed agreement.
 * @returns {void}
 */
export function bindForms(doc, win, api, state) {
  const submit = (id, handler) => byId(doc, id).addEventListener('submit', (event) => {
    event.preventDefault();
    handler();
  });

  submit('analyze-form', () => runAction(doc, { button: 'analyze-button', region: 'results', error: 'analyze-error' }, async () => {
    state.current = { document: await readDocument(doc), context: readContext(doc) };
    renderReport(doc, byId(doc, 'results'), await api.postJson('/api/analyze', state.current));
    byId(doc, 'results-section').hidden = false;
    byId(doc, 'ask-section').hidden = false;
    byId(doc, 'results-heading').focus();
  }));

  submit('ask-form', () => runAction(doc, { button: 'ask-button', region: 'answer', error: 'ask-error' }, async () => {
    const body = { ...state.current, question: byId(doc, 'question').value.trim() };
    renderAnswer(doc, byId(doc, 'answer'), await api.postJson('/api/ask', body));
  }));

  submit('compare-form', () => runAction(doc, { button: 'compare-button', region: 'comparison', error: 'compare-error' }, async () => {
    const body = {
      original: textDocument(byId(doc, 'original-text').value),
      revised: textDocument(byId(doc, 'revised-text').value),
      context: readContext(doc),
    };
    renderComparison(doc, byId(doc, 'comparison'), (await api.postJson('/api/compare', body)).changes);
  }));

  byId(doc, 'packet-button').addEventListener('click', () => runAction(doc, { button: 'packet-button', region: 'results', error: 'analyze-error' }, async () => {
    download(doc, win, await api.postForBlob('/api/packet', state.current), 'leaseguard-packet.pdf');
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
  const state = { current: null, samples: null, dossier: null, loadDossier: null };
  bindForms(doc, win, api, state);
  state.loadDossier = once(() => loadDossier(doc, win, { api, state, run: runAction, download }));
  loadWhenNeeded(win, byId(doc, 'dossier-section'), state.loadDossier);
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
