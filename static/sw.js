/**
 * @module sw
 * Service worker: caches the app shell so the page opens offline, and shows an
 * offline page for navigations when the network is unavailable. API calls are
 * never cached, because agreements must not be stored.
 */

const CACHE_NAME = 'leaseguard-shell-v3';
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
  '/static/js/evidence.js',
  '/static/js/dossier.js',
  '/static/js/dossier_render.js',
]);

/**
 * Decide how a request should be handled.
 * @param {Request} request - The intercepted request.
 * @returns {'network-only' | 'navigate' | 'cache-first'} The strategy.
 */
function strategyFor(request) {
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.pathname.startsWith('/api/')) {
    return 'network-only';
  }
  return request.mode === 'navigate' ? 'navigate' : 'cache-first';
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
 * Serve from cache, then network.
 * @param {Request} request - A static-asset request.
 * @returns {Promise<Response>} The asset.
 */
async function cacheFirst(request) {
  return (await caches.match(request)) ?? fetch(request);
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
  } else if (strategy === 'cache-first') {
    event.respondWith(cacheFirst(event.request));
  }
});
