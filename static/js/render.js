/**
 * @module render
 * Render API results into accessible DOM using the safe helpers in dom.js.
 */

import { h, replaceChildren } from './dom.js';
import { RISK_ORDER, countsSummary, directionText, riskText, verificationText } from './view.js';

/**
 * Fill a select element with options.
 * @param {Document} doc - The owning document.
 * @param {HTMLSelectElement} select - The select to fill.
 * @param {string[]} values - Option values (also used as labels).
 * @returns {void}
 */
export function renderOptions(doc, select, values) {
  replaceChildren(select, values.map((value) => h(doc, 'option', { value }, [value])));
}

/**
 * Render the role radio buttons.
 * @param {Document} doc - The owning document.
 * @param {Element} container - Where to put the radios.
 * @param {string[]} roles - Role values, the first is selected.
 * @returns {void}
 */
export function renderRoles(doc, container, roles) {
  const radios = roles.map((role, index) => {
    const id = `role-${role}`;
    const input = h(doc, 'input', { type: 'radio', name: 'role', id, value: role, checked: index === 0 });
    const label = h(doc, 'label', { for: id }, [role.charAt(0).toUpperCase() + role.slice(1)]);
    return h(doc, 'span', {}, [input, ' ', label]);
  });
  replaceChildren(container, radios);
}

/**
 * Build one collapsible finding.
 * @param {Document} doc - The owning document.
 * @param {any} finding - A finding from the API.
 * @returns {HTMLElement} The finding element.
 */
export function findingElement(doc, finding) {
  const badge = h(doc, 'span', { class: `badge risk-${finding.risk}` }, [riskText(finding.risk)]);
  const summary = h(doc, 'summary', {}, [badge, ` ${finding.heading} (${finding.category_title})`]);
  return h(doc, 'details', { class: 'finding', open: finding.risk === 'HIGH' }, [
    summary,
    h(doc, 'p', {}, [h(doc, 'strong', {}, ['What it means: ']), finding.reason]),
    h(doc, 'blockquote', {}, [finding.quote]),
    h(doc, 'p', { class: 'help' }, [verificationText(finding.quote_verified)]),
    h(doc, 'p', {}, [h(doc, 'strong', {}, ['Fair baseline: ']), finding.baseline]),
    h(doc, 'p', {}, [h(doc, 'strong', {}, ['Ask a lawyer: ']), finding.question_for_lawyer]),
  ]);
}

/**
 * Build the missing-protections section.
 * @param {Document} doc - The owning document.
 * @param {any} report - The report from the API.
 * @returns {HTMLElement[]} Heading and list or message.
 */
export function gapsElements(doc, report) {
  const heading = h(doc, 'h3', {}, ['Missing protections']);
  if (!report.coverage_complete) {
    return [heading, h(doc, 'p', { class: 'note' }, ['⚠️ Coverage check skipped: some clauses could not be evaluated.'])];
  }
  if (report.gaps.length === 0) {
    return [heading, h(doc, 'p', {}, ['✅ Every protection in the baseline is addressed.'])];
  }
  return [heading, h(doc, 'ul', {}, report.gaps.map((gap) => h(doc, 'li', {}, [`⚠️ ${gap.message}`])))];
}

/**
 * Render a full analysis report.
 * @param {Document} doc - The owning document.
 * @param {Element} container - Where to render.
 * @param {any} report - The report from the API.
 * @returns {void}
 */
export function renderReport(doc, container, report) {
  const counts = h(doc, 'ul', { class: 'counts', 'aria-label': countsSummary(report.counts) },
    RISK_ORDER.map((risk) => h(doc, 'li', { class: `risk-${risk}` }, [`${riskText(risk)}: ${report.counts[risk]}`])));
  const notes = report.context_notes.map((note) => h(doc, 'p', { class: 'note' }, [`ℹ️ ${note}`]));
  replaceChildren(container, [
    counts,
    ...notes,
    h(doc, 'h3', {}, ['Clause-by-clause review']),
    ...report.findings.map((finding) => findingElement(doc, finding)),
    ...gapsElements(doc, report),
  ]);
}

/**
 * Render a grounded answer.
 * @param {Document} doc - The owning document.
 * @param {Element} container - Where to render.
 * @param {any} answer - The answer from the API.
 * @returns {void}
 */
export function renderAnswer(doc, container, answer) {
  const parts = [h(doc, 'p', {}, [h(doc, 'strong', {}, ['Answer: ']), answer.answer])];
  if (answer.grounded) {
    parts.push(h(doc, 'p', {}, [`From ${answer.heading}:`]), h(doc, 'blockquote', {}, [answer.quote]),
      h(doc, 'p', { class: 'help' }, [verificationText(true)]));
  }
  replaceChildren(container, parts);
}

/**
 * Render the draft comparison as an accessible table.
 * @param {Document} doc - The owning document.
 * @param {Element} container - Where to render.
 * @param {any[]} changes - Rows from the API.
 * @returns {void}
 */
export function renderComparison(doc, container, changes) {
  const head = h(doc, 'tr', {}, ['Topic', 'Change', 'Original', 'Revised'].map((text) => h(doc, 'th', { scope: 'col' }, [text])));
  const rows = changes.map((change) => h(doc, 'tr', {}, [
    h(doc, 'th', { scope: 'row' }, [change.category_title]),
    h(doc, 'td', {}, [directionText(change.direction)]),
    h(doc, 'td', {}, [riskText(change.before)]),
    h(doc, 'td', {}, [riskText(change.after)]),
  ]));
  const table = h(doc, 'table', {}, [
    h(doc, 'caption', {}, ['How each topic changed, worst changes first']),
    h(doc, 'thead', {}, [head]),
    h(doc, 'tbody', {}, rows),
  ]);
  replaceChildren(container, [table]);
}
