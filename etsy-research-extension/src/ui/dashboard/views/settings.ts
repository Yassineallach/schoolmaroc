import { h } from '../../../shared/dom';
import * as repo from '../../../core/storage/repo';
import { count, STORES } from '../../../core/storage/db';
import { fmtNum } from '../../../shared/format';
import { DEFAULT_SETTINGS, PageResult, Settings } from '../../../shared/types';
import { card, cardHead, download, empty, toast, confirmAction } from '../../components';
import { field, pageHead } from './common';
import { weightsEditor } from './keywords';
import type { Ctx } from '../main';

export async function settingsView(ctx: Ctx): Promise<Node> {
  const s = ctx.settings;
  const counts = await Promise.all(STORES.map(async (st) => [st.name, await count(st.name)] as const));
  const currencies = [...new Set((await repo.listings()).map((l) => l.currency).filter(Boolean) as string[])].sort();
  const set = (patch: Partial<Settings>) => ctx.updateSettings(patch).then(() => toast('Saved'));
  const numIn = (key: keyof Settings, attrs: Record<string, unknown> = {}) => h('input', { type: 'number', step: 'any', value: String(s[key]), onchange: (e: Event) => set({ [key]: Number((e.target as HTMLInputElement).value) } as Partial<Settings>), ...attrs });

  const fxBox = h('div', { class: 'stack-sm' });
  const drawFx = () => {
    const rates = { ...ctx.settings.fxRates };
    const disp = ctx.settings.displayCurrency;
    fxBox.replaceChildren(
      !disp ? h('small', null, 'Pick a display currency to enter conversion rates. Until then, values stay in the listing’s own currency.')
        : currencies.filter((c) => c !== disp).length ? h('div', { class: 'grid' }, currencies.filter((c) => c !== disp).map((c) =>
          field(`${c} per 1 ${disp}`, h('input', { type: 'number', step: 'any', min: 0, value: rates[c] ? String(rates[c]) : '', placeholder: 'rate', onchange: async (e: Event) => { const v = Number((e.target as HTMLInputElement).value); if (v > 0) rates[c] = v; else delete rates[c]; await set({ fxRates: rates }); } }))))
          : h('small', null, 'No other currencies in your data yet.'),
      h('small', null, 'Rates are entered by you and never fetched. Values without a rate are shown in their original currency.'),
    );
  };
  drawFx();

  const fileIn = h('input', { type: 'file', accept: 'application/json,.json', 'aria-label': 'Backup file' });
  const modeSel = h('select', { 'aria-label': 'Restore mode' }, h('option', { value: 'merge' }, 'Merge into current data'), h('option', { value: 'replace' }, 'Replace all current data'));

  return h('div', { class: 'stack', style: 'max-width:960px' },
    pageHead('Settings'),
    card('Data collection', h('div', { class: 'stack' },
      h('label', { class: 'row' }, h('input', { type: 'checkbox', checked: s.pageReading, onchange: (e: Event) => set({ pageReading: (e.target as HTMLInputElement).checked }) }), h('span', null, h('strong', null, 'Read Etsy pages I open'), h('br'), h('small', null, 'Passive and local. Only search, listing and shop pages you open yourself are read. Turning this off stops collection and removes the panel from Etsy.'))),
      h('label', { class: 'row' }, h('input', { type: 'checkbox', checked: s.inPageBadges, onchange: (e: Event) => set({ inPageBadges: (e.target as HTMLInputElement).checked }) }), h('span', null, 'Show estimate chips on search results for listings I have already analysed')),
    )),
    card('Appearance & currency', h('div', { class: 'filters' },
      field('Theme', h('select', { onchange: (e: Event) => set({ theme: (e.target as HTMLSelectElement).value as Settings['theme'] }) }, (['system', 'light', 'dark'] as const).map((t) => h('option', { value: t, selected: s.theme === t }, t)))),
      field('Display currency', h('select', { onchange: async (e: Event) => { await set({ displayCurrency: (e.target as HTMLSelectElement).value }); drawFx(); } }, h('option', { value: '' }, 'Keep original currency'), [...new Set([...currencies, 'USD', 'EUR', 'GBP', 'CAD', 'AUD', 'MAD'])].sort().map((c) => h('option', { value: c, selected: s.displayCurrency === c }, c)))),
      field('Calendar region', h('select', { onchange: (e: Event) => set({ country: (e.target as HTMLSelectElement).value as Settings['country'] }) }, (['US', 'UK', 'EU', 'CA', 'AU'] as const).map((c) => h('option', { value: c, selected: s.country === c }, c)))),
    ), h('div', { style: 'margin-top:12px' }, fxBox)),
    card('Estimate assumptions', h('div', { class: 'stack' },
      h('div', { class: 'filters' },
        field('Fallback sales per review', numIn('fallbackSalesPerReview', { min: 1, max: 100 }), 'Used only when a shop has too few reviews and fewer than 3 other shops are recorded.'),
        field('Min shop reviews to calibrate', numIn('minShopReviewsForCalibration', { min: 1 }), 'Below this, the shop’s own ratio is considered unreliable.'),
        field('Default discount %', numIn('defaultDiscountPct', { min: 0, max: 100 }), 'Applied to revenue estimates.'),
      ),
      h('button', { class: 'btn small', type: 'button', style: 'width:fit-content', onclick: async () => { await set({ fallbackSalesPerReview: DEFAULT_SETTINGS.fallbackSalesPerReview, minShopReviewsForCalibration: DEFAULT_SETTINGS.minShopReviewsForCalibration, defaultDiscountPct: 0, weights: DEFAULT_SETTINGS.weights }); ctx.rerender(); } }, 'Reset to defaults'),
    )),
    card('Keyword opportunity weights', weightsEditor(ctx, () => {})),
    card('Backup & restore', h('div', { class: 'stack' },
      h('div', { class: 'row' },
        h('button', { class: 'btn primary', type: 'button', onclick: async () => {
          const b = await repo.exportBackup(ctx.settings);
          download(`shoplens-backup-${new Date().toISOString().slice(0, 10)}.json`, JSON.stringify(b), 'application/json');
        } }, 'Download backup (JSON)')),
      h('div', { class: 'row' }, fileIn, modeSel,
        h('button', { class: 'btn', type: 'button', onclick: async () => {
          const f = (fileIn as HTMLInputElement).files?.[0];
          if (!f) { toast('Choose a backup file first'); return; }
          const mode = (modeSel as HTMLSelectElement).value as 'merge' | 'replace';
          if (mode === 'replace' && !confirmAction('Replace all current data with this backup?')) return;
          try {
            const b = JSON.parse(await f.text());
            await repo.importBackup(b, mode);
            if (b.settings && typeof b.settings === 'object') await ctx.updateSettings({ ...b.settings, onboardingDone: true });
            toast('Backup restored');
            ctx.rerender();
          } catch (e) {
            toast(`Restore failed: ${(e as Error).message}`);
          }
        } }, 'Restore')),
      h('div', { class: 'table-wrap' }, h('table', { class: 'data' }, h('tbody', null, counts.map(([n, c]) => h('tr', null, h('td', null, n), h('td', { class: 'num' }, fmtNum(c))))))),
      h('button', { class: 'btn danger', type: 'button', style: 'width:fit-content', onclick: async () => { if (confirmAction('Delete ALL research data on this device? This cannot be undone. Download a backup first.')) { await repo.clearAll(); toast('All data deleted'); ctx.rerender(); } } }, 'Delete all data'),
    )),
    card('About', h('div', { class: 'stack-sm' },
      h('p', null, 'Shoplens Research stores everything locally in this browser. It has no servers, no accounts, no AI and no external APIs.'),
      h('small', null, 'The term "Etsy" is a trademark of Etsy, Inc. This tool is not endorsed by, certified by or affiliated with Etsy, Inc.'))),
  );
}

export async function diagnosticsView(_ctx: Ctx): Promise<Node> {
  const tabs = await chrome.tabs.query({ url: ['https://www.etsy.com/*', 'https://etsy.com/*'] });
  const results = await Promise.all(tabs.map(async (t) => {
    try {
      const r = (await chrome.tabs.sendMessage(t.id!, { type: 'diagnostics' })) as PageResult;
      return { t, r };
    } catch {
      return { t, r: undefined };
    }
  }));
  const fieldsTable = (r: PageResult) => r.fields.length
    ? h('div', { class: 'table-wrap' }, h('table', { class: 'data' },
      h('thead', null, h('tr', null, h('th', null, 'Field'), h('th', null, 'Found'), h('th', null, 'Value'))),
      h('tbody', null, r.fields.map((f) => h('tr', null, h('td', null, f.field), h('td', null, h('span', { class: `badge ${f.found ? 'verified' : 'err'}` }, f.found ? 'yes' : 'no')), h('td', { class: 'mono' }, f.value ?? ''))))))
    : h('p', { class: 'muted' }, 'This is not a search, listing or shop page.');
  const tabCard = (t: chrome.tabs.Tab, r: PageResult | undefined) => card(
    cardHead(t.title ?? t.url ?? 'Etsy tab',
      r ? h('span', { class: 'badge neutral' }, r.pageType) : null,
      r ? h('button', { class: 'btn small', type: 'button', onclick: async () => { await chrome.tabs.sendMessage(t.id!, { type: 'reread' }); toast('Page re-read'); } }, 'Re-read page') : null),
    r ? fieldsTable(r) : h('p', { class: 'muted' }, 'The content script is not running in this tab. Reload the tab, and check that the extension has access to etsy.com.'));
  return h('div', { class: 'stack' },
    pageHead('Page diagnostics', 'Shows which fields the extension can read from your open Etsy tabs. Use it to check whether a change to Etsy’s page layout broke a field.'),
    results.length ? results.map(({ t, r }) => tabCard(t, r)) : empty('Open an Etsy search, listing or shop page in another tab, then reload this view.'),
  );
}
