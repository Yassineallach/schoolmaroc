/** Popup and sidebar (Opera sidebar_action / Chrome side panel) share this script. */
import { h, mount } from '../../shared/dom';
import { getSettings, onSettingsChanged, saveSettings } from '../../shared/settings';
import { send, TabState } from '../../shared/messages';
import { renderSummary } from '../summary-view';
import type { Settings } from '../../shared/types';

const mode = document.body.dataset.mode;
const body = document.getElementById('body')!;
const status = document.getElementById('status')!;
let settings: Settings;

function theme() {
  if (settings.theme === 'system') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme', settings.theme);
}

const open = (route?: string) => {
  send({ type: 'openDashboard', route });
  if (mode === 'popup') window.close();
};

function drawStatus() {
  mount(status, h('label', { class: 'row' },
    h('input', { type: 'checkbox', checked: settings.pageReading, onchange: async (e: Event) => { settings = await saveSettings({ pageReading: (e.target as HTMLInputElement).checked, onboardingDone: true }); drawStatus(); draw(); } }),
    h('span', null, settings.pageReading ? 'Reading the Etsy pages you open' : 'Page reading is off')));
}

async function draw() {
  if (!settings.pageReading) {
    mount(body, h('div', { class: 'stack' }, h('p', { class: 'muted' }, 'Turn on page reading above to analyse Etsy search, listing and shop pages as you browse. Data stays in this browser.'),
      h('div', { class: 'row' }, h('button', { class: 'btn small', type: 'button', onclick: () => open('welcome') }, 'How it works'))));
    return;
  }
  const state = await send<TabState>({ type: 'tabState' }).catch(() => ({} as TabState));
  if (!state.result) {
    mount(body, h('div', { class: 'stack' },
      h('p', { class: 'muted' }, 'Open an Etsy search, listing or shop page. Its analysis will appear here.'),
      h('div', { class: 'row' },
        h('button', { class: 'btn small', type: 'button', onclick: () => open('keywords') }, 'Keywords'),
        h('button', { class: 'btn small', type: 'button', onclick: () => open('products') }, 'Products'),
        h('button', { class: 'btn small', type: 'button', onclick: () => open('competitors') }, 'Competitors'),
        h('button', { class: 'btn small', type: 'button', onclick: () => open('seo') }, 'SEO tools'))));
    return;
  }
  mount(body, renderSummary(state.summary, settings, {
    open,
    track: async (shopName, tracked) => { await send({ type: 'track', shopName, tracked }); },
    saveKeyword: async (term) => { await send({ type: 'saveKeyword', term }); },
    saveListing: async (listingId) => { await send({ type: 'saveListing', listingId }); },
  }));
}

async function boot() {
  settings = await getSettings();
  theme();
  onSettingsChanged((s) => { settings = s; theme(); });
  document.getElementById('open')!.addEventListener('click', () => open());
  drawStatus();
  await draw();
  if (mode === 'sidebar') {
    // follow the active tab and fresh page reads
    chrome.tabs.onActivated.addListener(() => draw());
    chrome.storage.onChanged.addListener((_c, area) => { if (area === 'session') draw(); });
  }
}

boot();
