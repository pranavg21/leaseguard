/**
 * @module forms
 * Read and validate form input before anything is sent to the server.
 */

import { ApiError, encodeFile } from './api.js';
import { parseRent } from './view.js';

/** Minimum agreement length the server accepts, mirrored for instant feedback. */
export const MIN_TEXT_CHARS = 500;

/**
 * Get a form control by id.
 * @param {Document} doc - The document.
 * @param {string} id - Element id.
 * @returns {any} The element (inputs, selects and textareas are used by value).
 */
export function byId(doc, id) {
  return doc.getElementById(id);
}

/**
 * Read the user's situation from the form.
 * @param {Document} doc - The document.
 * @returns {{role: string, state: string, monthly_rent: number | null, language: string}} The context payload.
 */
export function readContext(doc) {
  const checked = doc.querySelector('input[name="role"]:checked');
  return {
    role: checked ? checked.value : 'tenant',
    state: byId(doc, 'state').value,
    monthly_rent: parseRent(byId(doc, 'rent').value),
    language: byId(doc, 'language').value,
  };
}

/**
 * Build a document payload from pasted text.
 * @param {string} text - The pasted agreement.
 * @returns {{text: string}} The payload.
 */
export function textDocument(text) {
  const trimmed = text.trim();
  if (trimmed.length < MIN_TEXT_CHARS) {
    throw new ApiError('Please paste the full agreement (at least 500 characters) or upload a file.', 0);
  }
  return { text: trimmed };
}

/**
 * Read the agreement from the upload field or the text area (upload wins).
 * @param {Document} doc - The document.
 * @returns {Promise<{text: string} | {file_base64: string}>} The payload.
 */
export async function readDocument(doc) {
  const file = byId(doc, 'document-file').files?.[0];
  if (file) {
    return { file_base64: await encodeFile(file) };
  }
  return textDocument(byId(doc, 'document-text').value);
}
