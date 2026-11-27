import { h } from '../../../shared/dom';
import * as repo from '../../../core/storage/repo';
import { analyseKeyword } from '../../../core/summaries';
import { opportunityScore, Suggestion } from '../../../core/keywords';
import { histogram } from '../../../core/stats';
import { availablePeriods, filterPeriod, keywordSeries, Metric, PERIODS } from '../../../core/trends';
import { fmtDate, fmtMoney, fmtNum, fmtPct } from '../../../shared/format';
import type { KeywordRecord, ScoringWeights } from '../../../shared/types';
import { card, cardHead, empty, explain, histogramChart, kpi, lineChart, meter, prov, segmented, table, toast, confirmAction } from '../../components';
import { back, exportButtons, num, pageHead, date } from './common';
import type { Ctx } from '../main';

const WEIGHT_LABELS: Record<keyof ScoringWeights, string> = { demand: 'Demand signal', competition: 'Low competition', trend: 'Trend', specificity: 'Specificity' };

export function weightsEditor(ctx: Ctx, onChange: () => void) {
  const w = { ...ctx.settings.weights };
  return h('div', { class: 'stack-sm' },
    h('div', { class: 'weights' }, (Object.keys(WEIGHT_LABELS) as (keyof ScoringWeights)[]).map((k) => {
      const out = h('span', { class: 'mono' }, String(w[k]));
      return h('label', { class: 'field' }, h('span', { class: 'row between' }, WEIGHT_LABELS[k], out),
        h('input', { type: 'range', min: 0, max: 100, step: 5, value: String(w[k]), oninput: (e: Event) => { w[k] = Number((e.target as HTMLInputElement).value); out.textContent = String(w[k]); }, onchange: async () => { await ctx.updateSettings({ weights: { ...w } }); onChange(); } }));
    })),
    h('small', null, 'Weights are relative. Opportunity = 100 × data quality × Σ(weight × component) ÷ Σ weights.'),
  );
}

async function scoreFor(k: KeywordRecord, ctx: Ctx, ac: Set<string>) {
  if (!k.latest) return undefined;
  const snaps = await repo.keywordSnaps(k.term);
  return { o: opportunityScore(k.term, k.latest, snaps, ac.has(k.term), ctx.settings.weights), snaps: snaps.length };
}

export async function keywordsView(ctx: Ctx): Promise<Node> {
  const [all, ac] = await Promise.all([repo.keywords(), repo.autocompleteTerms()]);
  const scored = await Promise.all(all.map(async (k) => ({ k, s: await scoreFor(k, ctx, ac) })));
  const folders = [...new Set(all.map((k) => k.folder).filter(Boolean) as string[])].sort();
  let folder = '';
  let onlySaved = false;
  const selected = new Set<string>();
  const list = h('div');
  const addIn = h('input', { type: 'text', placeholder: 'Add a keyword to your list', 'aria-label': 'New keyword' });

  const draw = () => {
    const rows = scored.filter(({ k }) => (!folder || k.folder === folder) && (!onlySaved || k.saved));
    list.replaceChildren(rows.length ? table([
      { key: 'sel', label: '', render: (r) => h('input', { type: 'checkbox', 'aria-label': `Select ${r.k.term}`, checked: selected.has(r.k.term), onclick: (e: Event) => e.stopPropagation(), onchange: (e: Event) => { (e.target as HTMLInputElement).checked ? selected.add(r.k.term) : selected.delete(r.k.term); } }) },
      { key: 'term', label: 'Keyword', sort: (r) => r.k.term, render: (r) => h('span', { class: 'row' }, r.k.term, r.k.saved ? h('span', { class: 'badge neutral' }, r.k.folder ?? 'saved') : null, ac.has(r.k.term) ? h('span', { class: 'badge verified', title: 'Seen in Etsy autocomplete' }, 'autocomplete') : null) },
      { key: 'results', label: 'Results', num: true, sort: (r) => r.k.latest?.resultCount, render: (r) => (r.k.latest?.resultCount !== undefined ? `${r.k.latest.resultCountIsLowerBound ? '>' : ''}${fmtNum(r.k.latest.resultCount)}` : '—'), title: 'Verified: number shown by Etsy' },
      { key: 'opp', label: 'Opportunity', num: true, sort: (r) => r.s?.o.score, render: (r) => (r.s ? String(r.s.o.score) : '—') },
      { key: 'diff', label: 'Difficulty', num: true, sort: (r) => r.s?.o.difficulty.score, render: (r) => (r.s ? String(r.s.o.difficulty.score) : '—') },
      { key: 'badges', label: 'Demand badges', num: true, sort: (r) => (r.k.latest ? r.k.latest.bestsellerShare + r.k.latest.popularNowShare : undefined), render: (r) => (r.k.latest ? fmtPct(r.k.latest.bestsellerShare + r.k.latest.popularNowShare) : '—'), title: 'Share of results with "Bestseller" or "Popular now"' },
      { key: 'price', label: 'Median price', num: true, sort: (r) => r.k.latest?.medianPrice, render: (r) => fmtMoney(r.k.latest?.medianPrice, r.k.latest?.currency) },
      { key: 'checks', label: 'Checks', num: true, sort: (r) => r.s?.snaps, render: (r) => String(r.s?.snaps ?? 0) },
      { key: 'last', label: 'Last checked', num: true, sort: (r) => r.k.lastSeen, render: (r) => fmtDate(r.k.lastSeen) },
    ], rows, { onRow: (r) => ctx.go(`keywords/${encodeURIComponent(r.k.term)}`), sortKey: 'opp', caption: 'Keywords' }) : empty(all.length ? 'No keywords in this view.' : 'No keywords yet. Search on Etsy with page reading on, or add one above.'));
  };
  draw();

  return h('div', { class: 'stack' },
    pageHead('Keywords', 'Search terms you researched on Etsy. Etsy does not publish search volume, so demand is shown through indicators read from the result pages.',
      exportButtons('keywords', () => [{ name: 'Keywords', rows: [
        ['Keyword', 'Folder', 'Saved', 'Results (verified)', 'Results is lower bound', 'Sample size', 'Opportunity', 'Difficulty', 'Bestseller share', 'Popular now share', 'Ad share', 'Median price', 'P25 price', 'P75 price', 'Currency', 'Distinct shops', 'Shop concentration (HHI)', 'In autocomplete', 'Checks', 'First checked', 'Last checked', 'Notes'],
        ...scored.map(({ k, s }) => [k.term, k.folder, k.saved, k.latest?.resultCount, k.latest?.resultCountIsLowerBound ?? '', k.latest?.sampleSize, s?.o.score, s?.o.difficulty.score, num(k.latest?.bestsellerShare, 3), num(k.latest?.popularNowShare, 3), num(k.latest?.adShare, 3), num(k.latest?.medianPrice), num(k.latest?.p25Price), num(k.latest?.p75Price), k.latest?.currency, k.latest?.distinctShops, num(k.latest?.shopConcentration, 4), ac.has(k.term), s?.snaps ?? 0, date(k.firstSeen), date(k.lastSeen), k.notes]),
      ] }])),
    card(null, h('div', { class: 'row between' },
      h('form', { class: 'row', onsubmit: async (e: Event) => { e.preventDefault(); if (addIn.value.trim()) { await repo.saveKeyword(addIn.value); toast('Keyword saved. Search it on Etsy to collect data.'); ctx.rerender(); } } }, addIn, h('button', { class: 'btn', type: 'submit' }, 'Add')),
      h('div', { class: 'row' },
        h('select', { 'aria-label': 'Folder filter', onchange: (e: Event) => { folder = (e.target as HTMLSelectElement).value; draw(); } }, h('option', { value: '' }, 'All folders'), folders.map((f) => h('option', { value: f }, f))),
        h('label', { class: 'row', style: 'font-size:13px' }, h('input', { type: 'checkbox', onchange: (e: Event) => { onlySaved = (e.target as HTMLInputElement).checked; draw(); } }), 'Saved only'),
        h('button', { class: 'btn small', type: 'button', onclick: () => { if (selected.size < 2) toast('Select 2 to 6 keywords to compare'); else ctx.go(`keywords/compare?terms=${encodeURIComponent([...selected].slice(0, 6).join('|'))}`); } }, 'Compare selected'),
      ))),
    list,
    card('Opportunity score weights', weightsEditor(ctx, () => ctx.rerender())),
  );
}

const METRICS: { value: Metric; label: string }[] = [
  { value: 'demandShare', label: 'Demand badges %' },
  { value: 'resultCount', label: 'Results' },
  { value: 'medianPrice', label: 'Median price' },
  { value: 'adShare', label: 'Ads %' },
];

export async function keywordDetailView(term: string, ctx: Ctx): Promise<Node> {
  const a = await analyseKeyword(term, ctx.settings);
  if (!a) {
    return h('div', { class: 'stack' }, back('keywords', 'Keywords'), card(`“${term}”`, empty('No data for this keyword yet.', h('a', { class: 'btn primary', href: `https://www.etsy.com/search?q=${encodeURIComponent(term)}`, target: '_blank', rel: 'noopener' }, 'Search it on Etsy ↗'))));
  }
  const { record: k, opportunity: o } = a;
  const st = k.latest;
  let metric: Metric = 'demandShare';
  let period = availablePeriods(a.snaps[0]?.ts).filter((p) => p.available).pop()?.key ?? '30d';
  const chartBox = h('div');
  const drawChart = () => {
    const periods = availablePeriods(a.snaps[0]?.ts);
    const days = PERIODS.find((p) => p.key === period)!.days;
    const pts = filterPeriod(keywordSeries(a.snaps, metric), days);
    chartBox.replaceChildren(h('div', { class: 'stack-sm' },
      h('div', { class: 'row between' },
        segmented(METRICS, metric, (v) => { metric = v; drawChart(); }, 'Metric'),
        segmented(periods.map((p) => ({ value: p.key, label: p.label, disabled: !p.available, title: p.available ? undefined : 'Not enough history collected yet' })), period, (v) => { period = v; drawChart(); }, 'Period')),
      lineChart(pts, { label: `${term} ${metric}`, yFormat: metric === 'medianPrice' ? (n) => fmtMoney(n, st?.currency) : undefined }),
      h('small', null, a.snaps.length ? `${a.snaps.length} check(s) since ${fmtDate(a.snaps[0].ts)}. The history comes only from your own visits; nothing is backfilled.` : 'No history yet.')));
  };
  drawChart();

  let group: Suggestion['groups'][number] | 'all' = 'all';
  const sugBox = h('div');
  const drawSug = () => {
    const list = a.suggestions.filter((s) => group === 'all' || s.groups.includes(group));
    sugBox.replaceChildren(list.length ? table([
      { key: 'phrase', label: 'Phrase', sort: (s) => s.phrase, render: (s) => h('a', { href: `#keywords/${encodeURIComponent(s.phrase)}` }, s.phrase) },
      { key: 'docs', label: 'Titles using it', num: true, sort: (s) => s.docs, render: (s) => (s.docs ? `${s.docs} (${fmtPct(s.share)})` : '—') },
      { key: 'groups', label: 'Type', render: (s) => h('div', { class: 'chips' }, s.groups.map((g) => h('span', { class: 'chip' }, g))) },
      { key: 'save', label: '', render: (s) => h('button', { class: 'btn small', type: 'button', onclick: async (e: Event) => { e.stopPropagation(); await repo.saveKeyword(s.phrase); toast(`Saved “${s.phrase}”`); } }, 'Save') },
    ], list, { sortKey: 'docs', limit: 60, caption: 'Keyword suggestions' }) : empty('No phrases in this group.'));
  };
  drawSug();

  const notes = h('textarea', { 'aria-label': 'Notes', placeholder: 'Your notes', style: 'min-height:70px' }, k.notes ?? '');
  const folderIn = h('input', { type: 'text', value: k.folder ?? '', placeholder: 'Folder name', 'aria-label': 'Folder' });

  return h('div', { class: 'stack' },
    back('keywords', 'Keywords'),
    pageHead(`“${k.term}”`, `Last checked ${fmtDate(k.lastSeen)}. Figures come from the Etsy results page you opened.`,
      h('a', { class: 'btn small', href: `https://www.etsy.com/search?q=${encodeURIComponent(k.term)}`, target: '_blank', rel: 'noopener' }, 'Re-check on Etsy ↗'),
      h('a', { class: 'btn small', href: `https://trends.google.com/trends/explore?q=${encodeURIComponent(k.term)}`, target: '_blank', rel: 'noopener', title: 'Opens Google Trends in a new tab. Shoplens does not fetch it.' }, 'Google Trends ↗'),
      h('button', { class: 'btn small danger', type: 'button', onclick: async () => { if (confirmAction(`Delete “${k.term}” and its history?`)) { await repo.deleteKeyword(k.term); ctx.go('keywords'); } } }, 'Delete')),
    st ? h('div', { class: 'grid' },
      card(null, kpi('Results', st.resultCount !== undefined ? `${st.resultCountIsLowerBound ? '>' : ''}${fmtNum(st.resultCount)}` : '—', { prov: 'verified', sub: 'Supply: competing listings' })),
      card(null, kpi('Opportunity', o ? `${o.score}/100` : '—', { prov: 'estimated', sub: o?.quality.notes.join(' · ') })),
      card(null, kpi('Difficulty', o ? `${o.difficulty.score}/100` : '—', { prov: 'estimated' })),
      card(null, kpi('Demand badges', fmtPct(st.bestsellerShare + st.popularNowShare), { prov: 'verified', sub: `${fmtPct(st.bestsellerShare)} Bestseller · ${fmtPct(st.popularNowShare)} Popular now` })),
      card(null, kpi('Median price', fmtMoney(st.medianPrice, st.currency), { prov: 'verified', sub: `${fmtMoney(st.minPrice, st.currency)}–${fmtMoney(st.maxPrice, st.currency)}` })),
      card(null, kpi('Ads in sample', fmtPct(st.adShare), { prov: 'verified', sub: `${st.sampleSize} results read` })),
      card(null, kpi('Distinct shops', fmtNum(st.distinctShops), { prov: 'verified', sub: `HHI ${st.shopConcentration.toFixed(3)}` })),
      card(null, kpi('Autocomplete', a.inAutocomplete ? 'Seen' : 'Not seen', { prov: a.inAutocomplete ? 'verified' : 'unavailable', sub: 'Etsy suggested it while you typed' })),
    ) : h('div', { class: 'notice' }, 'Saved, but no results page has been read yet. Search it on Etsy.'),
    o ? card(cardHead('How the scores are calculated', prov('estimated')),
      h('div', { class: 'grid-2' },
        h('div', { class: 'stack-sm' }, h('h3', null, `Opportunity ${o.score}`), o.parts.map((p) => h('div', { class: 'stack-sm', style: 'gap:2px' }, h('div', { class: 'row between' }, h('span', null, `${p.label} (weight ${p.weight})`), h('span', { class: 'mono' }, p.value.toFixed(2))), meter(p.value, p.label), h('small', null, p.detail))), h('small', null, `${o.formula}. Data quality factor ${o.quality.factor.toFixed(2)}.`)),
        h('div', { class: 'stack-sm' }, h('h3', null, `Difficulty ${o.difficulty.score}`), o.difficulty.components.map((c) => h('div', { class: 'stack-sm', style: 'gap:2px' }, h('div', { class: 'row between' }, h('span', null, c.label), h('span', { class: 'mono' }, c.value.toFixed(2))), meter(c.value, c.label), h('small', null, c.detail))), h('small', null, 'Difficulty = 100 × (0.45 supply + 0.35 established competitors + 0.10 ads + 0.10 shop dominance).')),
      ),
      explain('Why there is no search volume', ['Etsy does not publish how often a term is searched. Tools that show “monthly searches” are modelling it.', 'Shoplens uses signals Etsy does show: the number of results, the share of “Bestseller” and “Popular now” badges, whether Etsy autocompletes the phrase, and how these change across your own checks.', 'Card review counts on Etsy search results usually belong to the shop, so “established competitors” measures shop strength.'])) : null,
    card('History', chartBox),
    h('div', { class: 'grid-2' },
      card('Price distribution', k.prices.length ? histogramChart(histogram(k.prices), { label: 'Price distribution', xFormat: (n) => fmtMoney(n, st?.currency, 0) }) : empty('No prices recorded.'), st ? h('small', null, `IQR ${fmtMoney(st.p25Price, st.currency)}–${fmtMoney(st.p75Price, st.currency)} · median ${fmtMoney(st.medianPrice, st.currency)}`) : null),
      card('Organise', h('div', { class: 'stack-sm' }, folderIn, notes, h('div', { class: 'row' }, h('button', { class: 'btn small primary', type: 'button', onclick: async () => { await repo.updateKeyword(k.term, { saved: true, folder: folderIn.value.trim() || undefined, notes: (notes as HTMLTextAreaElement).value }); toast('Saved'); } }, 'Save'), k.saved ? h('button', { class: 'btn small', type: 'button', onclick: async () => { await repo.updateKeyword(k.term, { saved: false }); ctx.rerender(); } }, 'Unsave') : null))),
    ),
    card(cardHead('Related phrases', segmented([{ value: 'all', label: 'All' }, { value: 'broad', label: 'Broad' }, { value: 'long-tail', label: 'Long-tail' }, { value: 'buyer-intent', label: 'Buyer intent' }, { value: 'seasonal', label: 'Seasonal' }, { value: 'autocomplete', label: 'Autocomplete' }] as { value: typeof group; label: string }[], group, (v) => { group = v; drawSug(); }, 'Phrase type')),
      h('small', { style: 'display:block;margin-bottom:8px' }, 'Phrases extracted from the titles of the results you opened (document frequency), plus suggestions Etsy showed in its search box. Extraction is lexical; nothing is generated.'),
      sugBox),
  );
}

export async function keywordCompareView(ctx: Ctx, q: URLSearchParams): Promise<Node> {
  const terms = (q.get('terms') ?? '').split('|').filter(Boolean).slice(0, 6);
  const analyses = (await Promise.all(terms.map((t) => analyseKeyword(t, ctx.settings)))).filter((a): a is NonNullable<typeof a> => !!a);
  if (analyses.length < 2) return h('div', { class: 'stack' }, back('keywords', 'Keywords'), empty('Select at least two keywords with data to compare.'));
  const row = (label: string, f: (a: (typeof analyses)[number]) => string, p?: 'verified' | 'estimated' | 'observed') =>
    h('tr', null, h('th', { scope: 'row' }, h('span', { class: 'row' }, label, p ? prov(p) : null)), analyses.map((a) => h('td', { class: 'num' }, f(a))));
  const best = [...analyses].sort((a, b) => (b.opportunity?.score ?? -1) - (a.opportunity?.score ?? -1))[0];
  return h('div', { class: 'stack' },
    back('keywords', 'Keywords'),
    pageHead('Keyword comparison', `Comparing ${analyses.length} keywords with your current weights. Highest opportunity: “${best.record.term}”.`),
    card(null, h('div', { class: 'table-wrap' }, h('table', { class: 'data' },
      h('thead', null, h('tr', null, h('th', null, 'Metric'), analyses.map((a) => h('th', { class: 'num' }, h('a', { href: `#keywords/${encodeURIComponent(a.record.term)}` }, a.record.term))))),
      h('tbody', null,
        row('Opportunity', (a) => (a.opportunity ? String(a.opportunity.score) : '—'), 'estimated'),
        row('Difficulty', (a) => (a.opportunity ? String(a.opportunity.difficulty.score) : '—'), 'estimated'),
        row('Results', (a) => fmtNum(a.record.latest?.resultCount), 'verified'),
        row('Demand badges', (a) => (a.record.latest ? fmtPct(a.record.latest.bestsellerShare + a.record.latest.popularNowShare) : '—'), 'verified'),
        row('Trend component', (a) => (a.opportunity ? a.opportunity.parts.find((p) => p.key === 'trend')!.value.toFixed(2) : '—'), 'observed'),
        row('Specificity', (a) => (a.opportunity ? a.opportunity.parts.find((p) => p.key === 'specificity')!.value.toFixed(2) : '—')),
        row('Median price', (a) => fmtMoney(a.record.latest?.medianPrice, a.record.latest?.currency), 'verified'),
        row('Ads in sample', (a) => fmtPct(a.record.latest?.adShare), 'verified'),
        row('Distinct shops', (a) => fmtNum(a.record.latest?.distinctShops), 'verified'),
        row('Autocomplete', (a) => (a.inAutocomplete ? 'yes' : 'no'), 'verified'),
        row('Checks recorded', (a) => String(a.snaps.length)),
        row('Data quality', (a) => (a.opportunity ? a.opportunity.quality.factor.toFixed(2) : '—')),
      )))),
    card('Weights', weightsEditor(ctx, () => ctx.rerender())),
  );
}
