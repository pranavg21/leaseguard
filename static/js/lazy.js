/**
 * @module lazy
 * Load code only when the user is about to need it.
 */

/** Distance before the dossier section reaches the viewport at which its code starts loading. */
const PRELOAD_MARGIN = '400px';

/**
 * Wrap a loader so it runs at most once and every caller shares its promise.
 * @param {() => Promise<void>} load - The loader.
 * @returns {() => Promise<void>} The single-use loader.
 */
export function once(load) {
  /** @type {Promise<void> | null} */
  let pending = null;
  return () => {
    pending ??= load();
    return pending;
  };
}

/**
 * Load code for a section just before it is needed: when it nears the viewport or receives focus.
 * Falls back to loading immediately where IntersectionObserver is unavailable.
 * @param {Window} win - The window.
 * @param {Element} section - The section that needs the code.
 * @param {() => Promise<void>} load - A single-use loader (see {@link once}).
 * @returns {void}
 */
export function loadWhenNeeded(win, section, load) {
  replayEarlyActions(section, load);
  section.addEventListener('focusin', () => load(), { once: true });
  if (!('IntersectionObserver' in win)) {
    load();
    return;
  }
  const observer = new win.IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) {
      observer.disconnect();
      load();
    }
  }, { rootMargin: PRELOAD_MARGIN });
  observer.observe(section);
}

/**
 * Hold clicks and submits that arrive before the section's code has loaded, then replay them,
 * so no action is lost and an unbound form never falls back to a full-page submit.
 * @param {Element} section - The lazily loaded section.
 * @param {() => Promise<void>} load - A single-use loader (see {@link once}).
 * @returns {void}
 */
export function replayEarlyActions(section, load) {
  let ready = false;
  const hold = (event) => {
    if (ready) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    const { target, type } = event;
    load().then(() => {
      ready = true;
      return type === 'submit' ? target.requestSubmit() : target.click();
    });
  };
  section.addEventListener('click', hold, true);
  section.addEventListener('submit', hold, true);
}
