import { test } from 'node:test';
import assert from 'node:assert/strict';
import { loadWhenNeeded, once, replayEarlyActions } from '../../static/js/lazy.js';
import { loadPage } from './helpers.mjs';

test('once runs the loader a single time and shares its promise', async () => {
  let calls = 0;
  const load = once(async () => { calls += 1; });
  const [a, b] = [load(), load()];
  assert.equal(a, b);
  await a;
  assert.equal(calls, 1);
});

test('loads immediately when IntersectionObserver is unavailable', () => {
  const { window, document } = loadPage();
  let calls = 0;
  loadWhenNeeded(window, document.getElementById('dossier-section'), () => { calls += 1; return Promise.resolve(); });
  assert.equal(calls, 1);
});

test('waits for the section to approach the viewport, then disconnects', () => {
  const { window, document } = loadPage();
  const observers = [];
  window.IntersectionObserver = class {
    constructor(callback, options) { this.callback = callback; this.options = options; this.disconnected = false; observers.push(this); }
    observe(target) { this.target = target; }
    disconnect() { this.disconnected = true; }
  };
  let calls = 0;
  const section = document.getElementById('dossier-section');
  loadWhenNeeded(window, section, () => { calls += 1; return Promise.resolve(); });
  const [observer] = observers;
  assert.equal(observer.target, section);
  assert.equal(observer.options.rootMargin, '400px');
  observer.callback([{ isIntersecting: false }]);
  assert.equal(calls, 0);
  observer.callback([{ isIntersecting: true }]);
  assert.equal(calls, 1);
  assert.equal(observer.disconnected, true);
});

test('focus entering the section also triggers loading', () => {
  const { window, document } = loadPage();
  window.IntersectionObserver = class { observe() {} disconnect() {} };
  let calls = 0;
  const section = document.getElementById('dossier-section');
  loadWhenNeeded(window, section, () => { calls += 1; return Promise.resolve(); });
  section.dispatchEvent(new window.FocusEvent('focusin'));
  assert.equal(calls, 1);
});

test('early clicks and submits are held, the code is loaded, then the action is replayed once', async () => {
  const { window, document } = loadPage();
  const section = document.getElementById('dossier-section');
  const clicks = [];
  let loads = 0;
  const load = once(async () => {
    loads += 1;
    document.getElementById('load-evidence-sample').addEventListener('click', () => clicks.push('bound'));
  });
  replayEarlyActions(section, load);
  assert.equal(loads, 0, 'installing the guard must not load the code');
  const button = document.getElementById('load-evidence-sample');
  button.click();
  assert.deepEqual(clicks, []);
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(loads, 1);
  assert.deepEqual(clicks, ['bound']);
  button.click();
  assert.deepEqual(clicks, ['bound', 'bound']);
  const form = document.getElementById('dossier-form');
  let submitted = 0;
  form.addEventListener('submit', (event) => { event.preventDefault(); submitted += 1; });
  form.dispatchEvent(new window.Event('submit', { cancelable: true }));
  assert.equal(submitted, 1, 'after loading, submits pass straight through');
});

test('an early submit is prevented and replayed with requestSubmit', async () => {
  const { window, document } = loadPage();
  const section = document.getElementById('dossier-section');
  const form = document.getElementById('dossier-form');
  let replayed = 0;
  form.requestSubmit = () => { replayed += 1; };
  replayEarlyActions(section, once(async () => undefined));
  const event = new window.Event('submit', { cancelable: true, bubbles: true });
  form.dispatchEvent(event);
  assert.equal(event.defaultPrevented, true);
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(replayed, 1);
});

test('a failed load is reported, not lost, and the next action retries', async () => {
  const { document } = loadPage();
  const section = document.getElementById('dossier-section');
  const errors = [];
  let attempts = 0;
  const load = once(async () => {
    attempts += 1;
    if (attempts === 1) { throw new TypeError('offline'); }
  });
  let replayed = 0;
  const button = document.getElementById('load-evidence-sample');
  replayEarlyActions(section, load, (error) => errors.push(error.message));
  button.click();
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.deepEqual(errors, ['offline']);
  button.addEventListener('click', () => { replayed += 1; });
  button.click();
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(attempts, 2);
  assert.equal(replayed, 1);
});

test('observer and focus loads report failures instead of rejecting unhandled', async () => {
  const { window, document } = loadPage();
  const errors = [];
  loadWhenNeeded(window, document.getElementById('dossier-section'), () => Promise.reject(new Error('no network')), (e) => errors.push(e.message));
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.deepEqual(errors, ['no network']);
});
