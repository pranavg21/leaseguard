/**
 * @module api
 * Thin client for the LeaseGuard JSON API with structured error handling.
 */

/** Largest upload the server accepts, in bytes (5 MB). */
export const MAX_UPLOAD_BYTES = 5_242_880;

/** Bytes converted per chunk when base64-encoding, to avoid call-stack limits. */
const ENCODE_CHUNK_BYTES = 0x8000;

/** Error raised for any failed API call; `message` is safe to show to users. */
export class ApiError extends Error {
  /**
   * @param {string} message - User-facing message.
   * @param {number} status - HTTP status, or 0 for network failures.
   */
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/**
 * Read the structured error message from a failed response.
 * @param {Response} response - The failed response.
 * @returns {Promise<string>} The server's message, or a generic one.
 */
export async function errorMessage(response) {
  try {
    const body = await response.json();
    return body?.error?.message ?? `Request failed (${response.status}).`;
  } catch {
    return `Request failed (${response.status}).`;
  }
}

/**
 * Create an API client.
 * @param {typeof fetch} fetchFn - The fetch implementation to use.
 * @returns {{ getJson: (path: string) => Promise<any>, postJson: (path: string, body: object) => Promise<any>, postForBlob: (path: string, body: object) => Promise<Blob> }} The client.
 */
export function createApi(fetchFn) {
  /**
   * @param {string} path - API path.
   * @param {RequestInit} init - Fetch options.
   * @returns {Promise<Response>} A successful response.
   */
  async function send(path, init) {
    let response;
    try {
      response = await fetchFn(path, init);
    } catch {
      throw new ApiError('You appear to be offline. Please reconnect and try again.', 0);
    }
    if (!response.ok) {
      throw new ApiError(await errorMessage(response), response.status);
    }
    return response;
  }

  /** @param {object} body @returns {RequestInit} */
  const post = (body) => ({
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  return {
    getJson: async (path) => (await send(path, { method: 'GET' })).json(),
    postJson: async (path, body) => (await send(path, post(body))).json(),
    postForBlob: async (path, body) => (await send(path, post(body))).blob(),
  };
}

/**
 * Base64-encode bytes in chunks.
 * @param {Uint8Array} bytes - File content.
 * @returns {string} Base64 text.
 */
export function toBase64(bytes) {
  let binary = '';
  for (let start = 0; start < bytes.length; start += ENCODE_CHUNK_BYTES) {
    binary += String.fromCharCode(...bytes.subarray(start, start + ENCODE_CHUNK_BYTES));
  }
  return btoa(binary);
}

/**
 * Base64-encode an uploaded file after checking its size.
 * @param {Blob} file - The selected file.
 * @returns {Promise<string>} Base64 content.
 */
export async function encodeFile(file) {
  if (file.size > MAX_UPLOAD_BYTES) {
    throw new ApiError('The file is larger than 5 MB. Please upload a smaller file.', 0);
  }
  return toBase64(new Uint8Array(await file.arrayBuffer()));
}
