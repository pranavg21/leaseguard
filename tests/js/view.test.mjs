import { test } from 'node:test';
import assert from 'node:assert/strict';
import { countsSummary, directionText, errorText, modeText, parseRent, riskText, verificationText } from '../../static/js/view.js';

test('risk and direction are described in words', () => {
  assert.equal(riskText('HIGH'), '⛔ High risk');
  assert.equal(riskText(null), 'Not present');
  assert.equal(riskText('bogus'), 'Not present');
  assert.equal(directionText('better'), '⬆️ Better');
  assert.equal(directionText('unknown'), 'unknown');
});

test('summaries and status text', () => {
  assert.equal(countsSummary({ HIGH: 2, MEDIUM: 1 }), '2 high risk, 1 medium risk and 0 fair clauses');
  assert.match(verificationText(true), /verified/);
  assert.match(verificationText(false), /could not/);
  assert.match(modeText('gemini'), /Gemini/);
  assert.match(modeText('offline'), /offline/);
});

test('parseRent and errorText', () => {
  assert.equal(parseRent('25000'), 25000);
  assert.equal(parseRent(''), null);
  assert.equal(parseRent('-5'), null);
  assert.equal(errorText(new Error('boom')), 'boom');
  assert.match(errorText('string'), /Something went wrong/);
});
