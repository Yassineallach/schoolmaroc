/**
 * Content script for etsy.com. When the user has turned page reading on, it
 * reads the page they already opened, sends the extracted fields to the
 * background worker, and shows a small panel in an isolated shadow root.
 * It never clicks, scrolls, submits, or loads other Etsy pages.
 */
import css from '../ui/styles/base.css';
import panelCss from './panel.css';
import { extractAutocomplete } from './extractors/pages';
import { extractPage } from './extractors/pages';
import { h, mount } from '../shared/dom';
import { getSettings, onSettingsChanged } from '../shared/settings';
import { send, LookupEntry, PageResponse } from '../shared/messages';
import { renderSummary } from '../ui/summary-view';
import { fmtNum } from '../shared/format';
import type { PageResult, Settings } from '../shared/types';

const HOST_ID = 'shoplens-research-root';
let settings: Settings;
let lastUrl = '';
let lastResult: PageResult | undefined;
let panelOpen = false;
let shadow: ShadowRoot | undefined;
let body: HTMLElement | undefined;

function applyTheme(hostEl: HTMLElement) {
  if (settings.theme === 'system') hostEl.removeAttribute('data-theme');
  else hostEl.setAttribute('data-theme', settings.theme);
}

function ensureHost() {
  let host = document.getElementById(HOST_ID);
  if (host && shadow) return;
  host = document.createElement('div');
  host.id = HOST_ID;
  // keep the host out of Etsy's layout entirely
  host.style.cssText = 'all: initial; position: fixed; z-index: 2147483000; right: 16px; bottom: 16px;';
  document.documentElement.appendChild(host);
  shadow = host.attachShadow({ mode: 'closed' });
  // Constructable stylesheets avoid conflicts with Etsy's CSS and inline-style CSP rules.
  try {
    const sheet = new CSSStyleSheet();
    sheet.replaceSync(css + panelCss);
    shadow.adoptedStyleSheets = [sheet];
  } catch {
    shadow.appendChild(h('style', null, css + panelCss));
  }
  applyTheme(host);
  const launcher = h('button', { class: 'launcher', type: 'button', 'aria-expanded': 'false', 'aria-controls': 'sl-panel', title: 'Shoplens Research' }, 'SL');
  body = h('div', { class: 'panel-body' });
  const panel = h('aside', { id: 'sl-panel', class: 'panel', hidden: true, 'aria-label': 'Shoplens Research' },
    h('header', { class: 'panel-head' },
      h('strong', null, 'Shoplens Research'),
      h('div', { class: 'row' },
        h('button', { class: 'btn small', type: 'button', onclick: () => send({ type: 'openDashboard' }) }, 'Dashboard'),
        h('button', { class: 'btn small', type: 'button', 'aria-label': 'Close panel', onclick: () => toggle(false) }, '✕'))),
    body,
    h('footer', { class: 'panel-foot' }, 'The term "Etsy" is a trademark of Etsy, Inc. This tool is not endorsed by or affiliated with Etsy, Inc.'),
  );
  launcher.addEventListener('click', () => toggle());
  shadow.append(panel, launcher);
  function toggleImpl(force?: boolean) {
    panelOpen = force ?? !panelOpen;
    panel.hidden = !panelOpen;
    launcher.setAttribute('aria-expanded', String(panelOpen));
    launcher.hidden = panelOpen;
  }
  toggle = toggleImpl;
  shadow.addEventListener('keydown', (e) => { if ((e as KeyboardEvent).key === 'Escape') toggle(false); });
}

let toggle: (force?: boolean) => void = () => {};

function removeHost() {
  document.getElementById(HOST_ID)?.remove();
  shadow = undefined;
  body = undefined;
  document.querySelectorAll('[data-shoplens-badge]').forEach((b) => b.remove());
}

async function process(force = false) {
  if (!settings.pageReading) return;
  const url = location.href;
  if (!force && url === lastUrl) return;
  lastUrl = url;
  const result = extractPage(document, url);
  lastResult = result;
  if (result.pageType === 'other' || !result.extraction) {
    removeHost();
    return;
  }
  ensureHost();
  mount(body!, h('p', { class: 'muted' }, 'Reading page…'));
  let resp: PageResponse | undefined;
  try {
    resp = await send<PageResponse>({ type: 'page', result });
  } catch (e) {
    mount(body!, h('p', { class: 'muted' }, `The extension could not save this page (${String((e as Error).message ?? e)}). Reload the page to try again.`));
    return;
  }
  if (!resp?.ok) {
    mount(body!, h('p', { class: 'muted' }, resp?.error ?? 'Nothing was saved.'));
    return;
  }
  mount(body!, renderSummary(resp.summary, settings, {
    open: (route) => send({ type: 'openDashboard', route }),
    track: async (shopName, tracked) => { await send({ type: 'track', shopName, tracked }); },
    saveKeyword: async (term) => { await send({ type: 'saveKeyword', term }); },
    saveListing: async (listingId) => { await send({ type: 'saveListing', listingId }); },
  }));
  if (settings.inPageBadges) await badges(result);
}

/** Small read-only chips on listing cards the user has already analysed. */
async function badges(result: PageResult) {
  const x = result.extraction;
  if (!x || (x.type !== 'search' && x.type !== 'shop')) return;
  const ids = x.cards.map((c) => c.listingId);
  if (!ids.length) return;
  const data = await send<Record<string, LookupEntry>>({ type: 'lookup', listingIds: ids }).catch(() => ({} as Record<string, LookupEntry>));
  document.querySelectorAll('[data-shoplens-badge]').forEach((b) => b.remove());
  for (const id of ids) {
    const info = data[id];
    if (!info) continue;
    const anchor = document.querySelector(`a[href*="/listing/${id}"]`);
    const card = anchor?.closest(`[data-listing-id="${id}"], li`) ?? anchor?.parentElement;
    if (!card) continue;
    const chip = document.createElement('span');
    chip.setAttribute('data-shoplens-badge', id);
    chip.style.cssText = 'all: initial; display: inline-block; margin: 4px 0; font: 600 11px/18px system-ui, sans-serif; padding: 0 7px; border-radius: 999px; background: #efe9fb; color: #5b3aa8; pointer-events: none;';
    chip.textContent = info.monthly !== undefined ? `≈ ${fmtNum(info.monthly, info.monthly < 10 ? 1 : 0)} sales/mo (est., grade ${info.grade})` : `Analysed · grade ${info.grade ?? '–'}`;
    chip.title = 'Shoplens estimate based on data you collected. Not an Etsy figure.';
    card.appendChild(chip);
  }
}

/* --- passive autocomplete capture: reads suggestions Etsy already shows the user --- */
let acTimer: number | undefined;
const acObserver = new MutationObserver(() => {
  if (!settings?.pageReading) return;
  clearTimeout(acTimer);
  acTimer = window.setTimeout(() => {
    const active = document.activeElement as HTMLInputElement | null;
    if (!active || active.tagName !== 'INPUT' || !/search/i.test(`${active.name} ${active.id} ${active.type} ${active.getAttribute('aria-label') ?? ''}`)) return;
    const items = extractAutocomplete(document);
    if (items.length) send({ type: 'autocomplete', items }).catch(() => {});
  }, 600);
});

async function init() {
  settings = await getSettings();
  onSettingsChanged((s) => {
    const wasOn = settings.pageReading;
    settings = s;
    const host = document.getElementById(HOST_ID);
    if (host) applyTheme(host);
    if (!s.pageReading) removeHost();
    else if (!wasOn) process(true);
  });
  await process(true);
  // Etsy sometimes updates the URL without a full reload (filters, pagination).
  setInterval(() => { if (location.href !== lastUrl) process(); }, 1500);
  acObserver.observe(document.documentElement, { childList: true, subtree: true });
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (sender.id !== chrome.runtime.id) return false;
  if (msg?.type === 'diagnostics') {
    sendResponse(lastResult ?? extractPage(document, location.href));
    return false;
  }
  if (msg?.type === 'reread') {
    process(true).then(() => sendResponse({ ok: true }));
    return true;
  }
  return false;
});

init();
