/**
 * @module view
 * Pure presentation helpers: turn API values into accessible text.
 * Risk and change are always described in words with an icon, never by colour alone.
 */

/** @type {Readonly<Record<string, string>>} */
export const RISK_ICONS = Object.freeze({ HIGH: '⛔', MEDIUM: '⚠️', FAIR: '✅' });

/** @type {Readonly<Record<string, string>>} */
export const RISK_LABELS = Object.freeze({ HIGH: 'High risk', MEDIUM: 'Medium risk', FAIR: 'Fair' });

/** @type {Readonly<Record<string, string>>} */
export const DIRECTION_TEXT = Object.freeze({
  worse: '⬇️ Worse',
  removed: '✖️ Removed',
  added: '➕ Added',
  better: '⬆️ Better',
  same: '➖ Unchanged',
});

/** Display order for risk counts. */
export const RISK_ORDER = Object.freeze(['HIGH', 'MEDIUM', 'FAIR']);

/**
 * Describe a risk level with an icon and words.
 * @param {string | null} risk - "HIGH", "MEDIUM", "FAIR" or null.
 * @returns {string} Text such as "⛔ High risk", or "Not present" for null.
 */
export function riskText(risk) {
  if (!risk || !(risk in RISK_LABELS)) {
    return 'Not present';
  }
  return `${RISK_ICONS[risk]} ${RISK_LABELS[risk]}`;
}

/**
 * Describe how a category changed between drafts.
 * @param {string} direction - One of the API direction values.
 * @returns {string} Accessible text for the direction.
 */
export function directionText(direction) {
  return DIRECTION_TEXT[direction] ?? direction;
}

/**
 * Describe whether a quote was verified against the document.
 * @param {boolean} verified - Result of the grounding check.
 * @returns {string} A short status sentence.
 */
export function verificationText(verified) {
  return verified ? '✔ Quote verified in your document' : '✖ Quote could not be verified';
}

/**
 * Summarise risk counts for screen-reader announcements.
 * @param {Record<string, number>} counts - Counts keyed by risk level.
 * @returns {string} For example "2 high risk, 1 medium risk and 5 fair clauses".
 */
export function countsSummary(counts) {
  const [high, medium, fair] = RISK_ORDER.map((risk) => counts[risk] ?? 0);
  return `${high} high risk, ${medium} medium risk and ${fair} fair clauses`;
}

/**
 * Describe the active AI mode.
 * @param {string} mode - "gemini" or "offline".
 * @returns {string} Status text for the header.
 */
export function modeText(mode) {
  return mode === 'gemini'
    ? 'AI mode: Google Gemini'
    : 'AI mode: offline rules only (explanations in English)';
}

/**
 * Parse the optional rent field.
 * @param {string} raw - The input's value.
 * @returns {number | null} A positive whole number of rupees, or null.
 */
export function parseRent(raw) {
  const value = Number.parseInt(raw, 10);
  return Number.isFinite(value) && value > 0 ? value : null;
}

/**
 * Turn any thrown value into a message that is safe to show.
 * @param {unknown} error - The thrown value.
 * @returns {string} The error's message, or a generic message.
 */
export function errorText(error) {
  return error instanceof Error && error.message ? error.message : 'Something went wrong. Please try again.';
}
