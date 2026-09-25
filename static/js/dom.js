/**
 * @module dom
 * Safe DOM construction helpers. Text is always set with textContent, never
 * innerHTML, so document content can never be interpreted as markup.
 */

/**
 * @typedef {Object<string, string | boolean | number>} Attributes
 * @typedef {Node | string | null | undefined} Child
 */

/**
 * Create an element with attributes and children.
 * @param {Document} doc - The document that owns the element.
 * @param {string} tag - Tag name, such as "p".
 * @param {Attributes} [attributes] - Attributes; `false` values are skipped, `true` sets an empty attribute.
 * @param {Child[]} [children] - Child nodes or strings (strings become text nodes).
 * @returns {HTMLElement} The new element.
 */
export function h(doc, tag, attributes = {}, children = []) {
  const element = doc.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (value !== false) {
      element.setAttribute(name, value === true ? '' : String(value));
    }
  }
  for (const child of children) {
    if (child !== null && child !== undefined) {
      element.append(typeof child === 'string' ? doc.createTextNode(child) : child);
    }
  }
  return element;
}

/**
 * Replace every child of a container.
 * @param {Element} container - The element to fill.
 * @param {Node[]} nodes - The new children.
 * @returns {void}
 */
export function replaceChildren(container, nodes) {
  container.replaceChildren(...nodes);
}

/**
 * Show a message in an alert region, or clear it with an empty string.
 * @param {Element | null} region - An element with role="alert".
 * @param {string} message - The message to show.
 * @returns {void}
 */
export function setMessage(region, message) {
  if (region) {
    region.textContent = message;
  }
}

/**
 * Mark a button and a live region as busy while work is in progress.
 * @param {HTMLButtonElement | null} button - The button that started the work.
 * @param {Element | null} region - The live region that will receive results.
 * @param {boolean} busy - Whether work is in progress.
 * @returns {void}
 */
export function setBusy(button, region, busy) {
  if (button) {
    button.disabled = busy;
  }
  if (region) {
    region.setAttribute('aria-busy', String(busy));
  }
}

/**
 * Build an accessible, keyboard-scrollable table region with caption and column headers.
 * @param {Document} doc - The owning document.
 * @param {string} caption - Table caption.
 * @param {string[]} headers - Column headers.
 * @param {Array<Array<string | Node>>} rows - Cell contents.
 * @returns {HTMLElement} The scrollable container with role="region".
 */
export function dataTable(doc, caption, headers, rows) {
  const head = h(doc, 'tr', {}, headers.map((text) => h(doc, 'th', { scope: 'col' }, [text])));
  const body = rows.map((cells) => h(doc, 'tr', {}, cells.map((cell) => {
    if (cell && typeof cell === 'object' && 'tagName' in cell && cell.tagName.toLowerCase() === 'th') {
      return cell;
    }
    return h(doc, 'td', {}, [cell]);
  })));
  const table = h(doc, 'table', {}, [
    h(doc, 'caption', {}, [caption]),
    h(doc, 'thead', {}, [head]),
    h(doc, 'tbody', {}, body),
  ]);
  return h(doc, 'div', {
    class: 'table-wrap',
    role: 'region',
    tabindex: '0',
    'aria-label': caption,
  }, [table]);
}

