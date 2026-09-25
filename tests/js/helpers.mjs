/**
 * @module helpers
 * Shared test utilities: a jsdom document loaded from the real index.html.
 */
import { readFileSync } from 'node:fs';
import { JSDOM } from 'jsdom';

const INDEX = readFileSync(new URL('../../static/index.html', import.meta.url), 'utf8');

/**
 * Create a DOM from the real page markup, with scripts disabled.
 * @returns {{ window: Window, document: Document }} The DOM.
 */
export function loadPage() {
  const dom = new JSDOM(INDEX, { url: 'http://localhost/' });
  return { window: dom.window, document: dom.window.document };
}

/**
 * Build a fake fetch that answers from a route table and records calls.
 * @param {Record<string, (init: RequestInit) => {status?: number, body?: unknown, blob?: Blob}>} routes - Handlers by path.
 * @returns {typeof fetch & { calls: Array<{path: string, init: RequestInit}> }} The fake.
 */
export function fakeFetch(routes) {
  const calls = [];
  const fn = async (path, init = {}) => {
    calls.push({ path, init });
    const handler = routes[path];
    if (!handler) {
      throw new TypeError('network down');
    }
    const { status = 200, body = {}, blob } = handler(init);
    return {
      ok: status < 400,
      status,
      json: async () => body,
      blob: async () => blob ?? new Blob(['%PDF-']),
    };
  };
  fn.calls = calls;
  return fn;
}

/** Let pending promise callbacks run. */
export const flush = () => new Promise((resolve) => setTimeout(resolve, 0));
