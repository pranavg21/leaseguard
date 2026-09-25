/**
 * @module sw
 * Service worker: caches the app shell so the page opens offline, and shows an
 * offline page for navigations when the network is unavailable. API calls are
 * never cached, because agreements must not be stored.
 *
 * Only the code needed for the first screen is precached. The deposit-dossier
 * modules are loaded lazily by the page and cached the first time they are used.
 */

const CACHE_NAME = 'leaseguard-shell-v5';
const SHELL = Object.freeze([
  '/',
  '/offline.html',
  '/icon.svg',
  '/manifest.webmanifest',
  '/static/css/styles.css',
  '/static/js/main.js',
  '/static/js/api.js',
  '/static/js/dom.js',
  '/static/js/forms.js',
  '/static/js/render.js',
  '/static/js/view.js',
  '/static/js/lazy.js',
]);

/**
 * Decide how a request should be handled.
 * @param {Request} request - The intercepted request.
 * @returns {'network-only' | 'navigate' | 'stale-while-revalidate'} The strategy.
 */
function strategyFor(request) {
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/api/')) {
    return 'network-only';
  }
  return request.mode === 'navigate' ? 'navigate' : 'stale-while-revalidate';
}

/**
 * Fetch a page, falling back to the offline page.
 * @param {Request} request - A navigation request.
 * @returns {Promise<Response>} The page or the offline page.
 */
async function navigate(request) {
  try {
    return await fetch(request);
  } catch {
    return (await caches.match('/offline.html')) ?? Response.error();
  }
}

/**
 * Serve a static asset from the cache at once and refresh the cached copy in the
 * background; on a cache miss, fetch it and keep a copy for next time.
 * @param {FetchEvent} event - The fetch event for a static asset.
 * @returns {Promise<Response>} The asset.
 */
async function staleWhileRevalidate(event) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(event.request);
  const refresh = fetch(event.request).then(async (response) => {
    if (response.ok) {
      await cache.put(event.request, response.clone());
    }
    return response;
  });
  if (!cached) {
    return refresh;
  }
  event.waitUntil(refresh.catch(() => undefined));
  return cached;
}

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL)));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(
    keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)),
  )));
});

self.addEventListener('fetch', (event) => {
  const strategy = strategyFor(event.request);
  if (strategy === 'navigate') {
    event.respondWith(navigate(event.request));
  } else if (strategy === 'stale-while-revalidate') {
    event.respondWith(staleWhileRevalidate(event));
  }
});
