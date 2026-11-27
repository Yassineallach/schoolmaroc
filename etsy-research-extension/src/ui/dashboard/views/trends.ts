import { h } from '../../../shared/dom';
import * as repo from '../../../core/storage/repo';
import { keywordsForEvent, movements, upcomingEvents, keywordSeries, filterPeriod, availablePeriods, PERIODS } from '../../../core/trends';
import { fmtDate, fmtNum } from '../../../shared/format';
import type { KeywordSnapshot, ListingRecord, Settings } from '../../../shared/types';
import { card, cardHead, empty, lineChart, prov, segmented, table } from '../../components';
import { pageHead } from './common';
import type { Ctx } from '../main';
import { DAY } from '../../../core/stats';

export async function trendsView(ctx: Ctx): Promise<Node> {
  const [snaps, keywords, listings] = await Promise.all([repo.allKeywordSnaps(), repo.keywords(), repo.listings()]);
  const byTerm = new Map<string, KeywordSnapshot[]>();
  for (const s of snaps) byTerm.set(s.term, [...(byTerm.get(s.term) ?? []), s]);
  const moves = movements(byTerm);
  const rising = moves.filter((m) => m.direction === 'rising');
  const declining = moves.filter((m) => m.direction === 'declining').reverse();
  const terms = keywords.map((k) => k.term);

  // category trend: products first recorded per category (your own discovery stream)
  const catCount = new Map<string, { recent: number; total: number }>();
  const now = Date.now();
  for (const l of listings) {
    const c = l.category[0];
    if (!c) continue;
    const v = catCount.get(c) ?? { recent: 0, total: 0 };
    v.total++;
    if (now - l.firstSeen < 30 * DAY) v.recent++;
    catCount.set(c, v);
  }
  const emerging = listings.filter((l) => l.listedOn && now - l.listedOn < 60 * DAY && (l.listingReviewCount ?? 0) >= 5).sort((a, b) => (b.listingReviewCount ?? 0) / Math.max(1, (now - b.listedOn!) / DAY) - (a.listingReviewCount ?? 0) / Math.max(1, (now - a.listedOn!) / DAY)).slice(0, 15);
  const popular = listings.filter((l) => l.badges.includes('Popular now') || l.badges.includes('Bestseller')).sort((a, b) => b.lastSeen - a.lastSeen).slice(0, 15);

  let country = ctx.settings.country;
  const calBox = h('div');
  const drawCal = () => {
    const evs = upcomingEvents(new Date(), country);
    calBox.replaceChildren(h('div', null, evs.map((e) => {
      const kws = keywordsForEvent(e, terms);
      return h('div', { class: 'cal-item' },
        h('div', null, h('strong', null, fmtDate(e.date.getTime())), h('div', null, h('small', null, `in ${e.daysUntil} days`))),
        h('div', { class: 'stack-sm', style: 'gap:2px' }, h('span', null, e.name), h('small', null, `List by ${fmtDate(e.listBy.getTime())} (${e.leadDays}-day lead time)`),
          kws.length ? h('div', { class: 'chips' }, kws.slice(0, 8).map((k) => h('a', { class: 'chip', href: `#keywords/${encodeURIComponent(k)}` }, k))) : h('small', null, `Related terms: ${e.keywords.slice(0, 4).join(', ')}`)),
        h('span', { class: `badge ${e.status === 'prepare-now' ? 'warn' : e.status === 'too-late' ? 'err' : e.status === 'upcoming' ? 'observed' : 'neutral'}` }, e.status === 'prepare-now' ? 'List now' : e.status === 'too-late' ? 'Very close' : e.status === 'upcoming' ? 'Prepare soon' : 'Later'));
    })));
  };
  drawCal();

  // history chart for one term
  const withHistory = [...byTerm.entries()].filter(([, s]) => s.length >= 2).map(([t]) => t).sort();
  let chosen = withHistory[0] ?? '';
  let period = '90d';
  const histBox = h('div');
  const drawHist = () => {
    if (!chosen) { histBox.replaceChildren(empty('Check a keyword on Etsy on two different days to start a history.')); return; }
    const s = (byTerm.get(chosen) ?? []).sort((a, b) => a.ts - b.ts);
    const periods = availablePeriods(s[0]?.ts);
    const days = PERIODS.find((p) => p.key === period)!.days;
    histBox.replaceChildren(h('div', { class: 'stack-sm' },
      h('div', { class: 'row between' },
        h('select', { 'aria-label': 'Keyword', onchange: (e: Event) => { chosen = (e.target as HTMLSelectElement).value; drawHist(); } }, withHistory.map((t) => h('option', { value: t, selected: t === chosen }, t))),
        segmented(periods.map((p) => ({ value: p.key, label: p.label, disabled: !p.available, title: p.available ? undefined : 'Not enough collected history' })), period, (v) => { period = v; drawHist(); }, 'Period')),
      lineChart(filterPeriod(keywordSeries(s, 'demandShare'), days), { label: `${chosen} demand badges`, yFormat: (n) => `${n.toFixed(0)}%` }),
      h('small', null, `Share of results with “Bestseller” or “Popular now” badges. History starts ${fmtDate(s[0]?.ts)}. Unavailable periods are greyed out; no data is invented.`)));
  };
  drawHist();

  const moveTable = (list: typeof moves) => list.length ? table([
    { key: 'term', label: 'Keyword', sort: (m) => m.term, render: (m) => h('a', { href: `#keywords/${encodeURIComponent(m.term)}` }, m.term) },
    { key: 'ch', label: 'Badge share Δ / 30 d', num: true, sort: (m) => m.demandChange, render: (m) => `${m.demandChange > 0 ? '+' : ''}${m.demandChange.toFixed(1)} pts` },
    { key: 'sup', label: 'Results Δ', num: true, sort: (m) => m.supplyChangePct, render: (m) => (m.supplyChangePct !== undefined ? `${m.supplyChangePct > 0 ? '+' : ''}${m.supplyChangePct.toFixed(0)}%` : '—') },
    { key: 'n', label: 'Checks', num: true, sort: (m) => m.checks, render: (m) => `${m.checks} over ${Math.round(m.spanDays)} d` },
  ], list, { sortKey: 'ch', sortDir: list === declining ? 1 : -1, limit: 15 }) : empty('No movement detected yet in your tracked keywords.');

  const listingList = (ls: ListingRecord[], note: (l: ListingRecord) => string) => ls.length ? h('div', { class: 'stack-sm' }, ls.map((l) => h('div', { class: 'row between' }, h('a', { class: 'grow clip', href: `#products/${l.listingId}` }, l.title), h('small', null, note(l))))) : empty('Nothing recorded yet.');

  return h('div', { class: 'stack' },
    pageHead('Trends & calendar', 'Trends are calculated only from data you collected. They describe your tracked keywords and products, not all of Etsy.'),
    h('div', { class: 'grid-2' },
      card(cardHead('Rising in your data', prov('observed')), moveTable(rising)),
      card(cardHead('Declining in your data', prov('observed')), moveTable(declining)),
    ),
    card('Keyword history', histBox),
    h('div', { class: 'grid-2' },
      card(cardHead('Recently emerging products', prov('verified')), h('small', { style: 'display:block;margin-bottom:6px' }, 'Listed or renewed in the last 60 days with 5+ reviews, ranked by reviews per day since “Listed on”.'), listingList(emerging, (l) => `${l.listingReviewCount} reviews · ${Math.round((now - l.listedOn!) / DAY)} d`)),
      card(cardHead('Popular products (Etsy badges)', prov('verified')), listingList(popular, (l) => l.badges.filter((b) => b === 'Popular now' || b === 'Bestseller').join(', '))),
      card('Categories in your research', catCount.size ? h('div', { class: 'stack-sm' }, [...catCount.entries()].sort((a, b) => b[1].recent - a[1].recent || b[1].total - a[1].total).slice(0, 12).map(([c, v]) => h('div', { class: 'row between' }, h('span', null, c), h('small', null, `${fmtNum(v.recent)} new in 30 d · ${fmtNum(v.total)} total`)))) : empty('Open listing pages to record categories.')),
      card(cardHead('Shopping calendar', h('select', { 'aria-label': 'Region', onchange: async (e: Event) => { country = (e.target as HTMLSelectElement).value as Settings['country']; await ctx.updateSettings({ country }); drawCal(); } }, (['US', 'UK', 'EU', 'CA', 'AU'] as const).map((c) => h('option', { value: c, selected: c === country }, c)))),
        h('small', { style: 'display:block;margin-bottom:6px' }, 'Dates are computed (Easter uses the Gregorian computus; Mother’s and Father’s Day follow the selected region). Lead times are typical planning windows that you can use as a guide.'), calBox),
    ),
  );
}
