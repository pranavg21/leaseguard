/**
 * @module api
 * Thin client for the LeaseGuard JSON API with structured error handling.
 */

/** Largest upload the server accepts, in bytes (5 MB). */
export const MAX_UPLOAD_BYTES = 5_242_880;

/** Largest request body the server accepts, in bytes (8 MB); checked before anything is sent. */
export const MAX_REQUEST_BYTES = 8_388_608;

/** Error code the server returns when a report or dossier ID is no longer cached. */
export const EXPIRED = 'expired';

/** Bytes converted per chunk when base64-encoding, to avoid call-stack limits. */
const ENCODE_CHUNK_BYTES = 0x8000;

/** Error raised for any failed API call; `message` is safe to show to users. */
export class ApiError extends Error {
  /**
   * @param {string} message - User-facing message.
   * @param {number} status - HTTP status, or 0 for failures before or without a response.
   * @param {string} [code] - The server's machine-readable error code, if any.
   */
  constructor(message, status, code = '') {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

/**
 * Read the structured error from a failed response.
 * @param {Response} response - The failed response.
 * @returns {Promise<{message: string, code: string}>} The server's message and code, or generic ones.
 */
export async function errorDetails(response) {
  const fallback = { message: `Request failed (${response.status}).`, code: '' };
  try {
    const error = (await response.json())?.error;
    return error?.message ? { message: error.message, code: error.code ?? '' } : fallback;
  } catch {
    return fallback;
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
      const { message, code } = await errorDetails(response);
      throw new ApiError(message, response.status, code);
    }
    return response;
  }

  /**
   * Serialise a JSON body, refusing locally anything the server would reject as too large.
   * @param {object} body - The request body.
   * @returns {RequestInit} Fetch options.
   */
  const post = (body) => {
    const json = JSON.stringify(body);
    if (new Blob([json]).size > MAX_REQUEST_BYTES) {
      throw new ApiError('These files are too large to send together (8 MB limit). Please remove some.', 0);
    }
    return { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: json };
  };

  return {
    getJson: async (path) => (await send(path, { method: 'GET' })).json(),
    postJson: async (path, body) => (await send(path, post(body))).json(),
    postForBlob: async (path, body) => (await send(path, post(body))).blob(),
  };
}

/**
 * Send a small body that refers to a result the server already holds; if the server
 * no longer has it, send the full body once instead. With no reference, send the full body.
 * @template T
 * @param {(path: string, body: object) => Promise<T>} call - An API method such as postJson.
 * @param {string} path - API path.
 * @param {object | null} reference - A body with a report or dossier ID, or null.
 * @param {() => object} full - Builds the full request body.
 * @returns {Promise<T>} The response.
 */
export async function postReference(call, path, reference, full) {
  if (!reference) {
    return call(path, full());
  }
  try {
    return await call(path, reference);
  } catch (error) {
    if (error instanceof ApiError && error.code === EXPIRED) {
      return call(path, full());
    }
    throw error;
  }
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
