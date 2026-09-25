/**
 * @module evidence
 * Read evidence files in the browser and fingerprint them with SHA-256 before upload.
 */

import { ApiError, MAX_UPLOAD_BYTES, toBase64 } from './api.js';

/** Maximum number of evidence files per dossier (mirrors the server limit). */
export const MAX_EVIDENCE_FILES = 10;

/** Hex digits per byte. */
const HEX_WIDTH = 2;

/** Radix for hexadecimal output. */
const HEX_RADIX = 16;

/**
 * Compute the SHA-256 digest of bytes with the Web Crypto API.
 * @param {ArrayBuffer} buffer - File content.
 * @param {SubtleCrypto} subtle - The Web Crypto implementation.
 * @returns {Promise<string>} Lower-case hex digest.
 */
export async function sha256Hex(buffer, subtle) {
  const digest = new Uint8Array(await subtle.digest('SHA-256', buffer));
  return Array.from(digest, (byte) => byte.toString(HEX_RADIX).padStart(HEX_WIDTH, '0')).join('');
}

/**
 * Prepare one file: check its size, hash it and encode it.
 * @param {File} file - A selected file.
 * @param {SubtleCrypto} subtle - The Web Crypto implementation.
 * @returns {Promise<{name: string, content_base64: string, client_sha256: string}>} The upload payload.
 */
export async function prepareFile(file, subtle) {
  if (file.size === 0 || file.size > MAX_UPLOAD_BYTES) {
    throw new ApiError(`${file.name} must be between 1 byte and 5 MB.`, 0);
  }
  const buffer = await file.arrayBuffer();
  return { name: file.name, content_base64: toBase64(new Uint8Array(buffer)), client_sha256: await sha256Hex(buffer, subtle) };
}

/**
 * Prepare every selected file, enforcing the file-count limit.
 * @param {File[]} files - Selected files.
 * @param {SubtleCrypto} subtle - The Web Crypto implementation.
 * @returns {Promise<Array<{name: string, content_base64: string, client_sha256: string}>>} Upload payloads.
 */
export async function prepareFiles(files, subtle) {
  if (files.length === 0 || files.length > MAX_EVIDENCE_FILES) {
    throw new ApiError(`Choose between 1 and ${MAX_EVIDENCE_FILES} evidence files.`, 0);
  }
  return Promise.all(files.map((file) => prepareFile(file, subtle)));
}

/**
 * Turn the sample evidence texts into File objects, as if the user had chosen them.
 * @param {Record<string, string>} samples - File name to text.
 * @returns {File[]} The files.
 */
export function sampleFiles(samples) {
  return Object.entries(samples).map(([name, text]) => new File([text], name, { type: 'text/plain' }));
}
