/**
 * @module lazy
 * Load code only when the user is about to need it.
 */

/** Distance before the dossier section reaches the viewport at which its code starts loading. */
const PRELOAD_MARGIN = '400px';

/**
 * Wrap a loader so it runs at most once and every caller shares its promise.
 * If loading fails (for example, offline), the next call tries again.
 * @param {() => Promise<void>} load - The loader.
 * @returns {() => Promise<void>} The single-use loader.
 */
export function once(load) {
  /** @type {Promise<void> | null} */
  let pending = null;
  return () => {
    pending ??= load().catch((error) => {
      pending = null;
      throw error;
    });
    return pending;
  };
}

/**
 * Load code for a section just before it is needed: when it nears the viewport or receives focus.
 * Falls back to loading immediately where IntersectionObserver is unavailable.
 * @param {Window} win - The window.
 * @param {Element} section - The section that needs the code.
 * @param {() => Promise<void>} load - A single-use loader (see {@link once}).
 * @param {(error: unknown) => void} onError - Reports a failed load; a later interaction retries.
 * @returns {void}
 */
export function loadWhenNeeded(win, section, load, onError) {
  const attempt = () => load().catch(onError);
  replayEarlyActions(section, load, onError);
  section.addEventListener('focusin', attempt, { once: true });
  if (!('IntersectionObserver' in win)) {
    attempt();
    return;
  }
  const observer = new win.IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) {
      observer.disconnect();
      attempt();
    }
  }, { rootMargin: PRELOAD_MARGIN });
  observer.observe(section);
}

/**
 * Hold clicks and submits that arrive before the section's code has loaded, then replay them,
 * so no action is lost and an unbound form never falls back to a full-page submit.
 * @param {Element} section - The lazily loaded section.
 * If loading fails, the action is dropped, the error reported, and the next action tries again.
 * @param {() => Promise<void>} load - A single-use loader (see {@link once}).
 * @param {(error: unknown) => void} onError - Reports a failed load.
 * @returns {void}
 */
export function replayEarlyActions(section, load, onError) {
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
    }, onError);
  };
  section.addEventListener('click', hold, true);
  section.addEventListener('submit', hold, true);
}
