import { h } from '../../../shared/dom';
import * as repo from '../../../core/storage/repo';
import { analyseShop } from '../../../core/summaries';
import { compareShops, keywordOverlap, shopVocabulary, termGaps } from '../../../core/competitors';
import { observedShopVelocity } from '../../../core/sales';
import { histogram } from '../../../core/stats';
import { fmtDate, fmtMoney, fmtNum } from '../../../shared/format';
import type { ListingRecord, ShopSnapshot } from '../../../shared/types';
import { card, cardHead, empty, histogramChart, kpi, lineChart, prov, table, toast, confirmAction } from '../../components';
import { back, exportButtons, num, pageHead, printButton, date } from './common';
import type { Ctx } from '../main';

export async function competitorsView(ctx: Ctx): Promise<Node> {
  const [shops, snaps, listings] = await Promise.all([repo.shops(), repo.allShopSnaps(), repo.listings()]);
  const snapsBy = new Map<string, ShopSnapshot[]>();
  for (const s of snaps) snapsBy.set(s.shopName, [...(snapsBy.get(s.shopName) ?? []), s]);
  const listingsBy = new Map<string, ListingRecord[]>();
  for (const l of listings) if (l.shopName) listingsBy.set(l.shopName, [...(listingsBy.get(l.shopName) ?? []), l]);
  const selected = new Set<string>();
  let onlyTracked = shops.some((s) => s.tracked);
  const box = h('div');
  const draw = () => {
    const rows = shops.filter((s) => !onlyTracked || s.tracked).map((s) => ({ s, v: observedShopVelocity(snapsBy.get(s.shopName) ?? []), n: listingsBy.get(s.shopName)?.length ?? 0 }));
    box.replaceChildren(rows.length ? table([
      { key: 'sel', label: '', render: (r) => h('input', { type: 'checkbox', 'aria-label': `Select ${r.s.shopName}`, checked: selected.has(r.s.shopName), onclick: (e: Event) => e.stopPropagation(), onchange: (e: Event) => { (e.target as HTMLInputElement).checked ? selected.add(r.s.shopName) : selected.delete(r.s.shopName); } }) },
      { key: 'name', label: 'Shop', sort: (r) => r.s.shopName.toLowerCase(), render: (r) => h('span', { class: 'row' }, r.s.shopName, r.s.tracked ? h('span', { class: 'badge observed' }, 'tracked') : null) },
      { key: 'sales', label: 'Sales', num: true, sort: (r) => r.s.sales, render: (r) => fmtNum(r.s.sales), title: 'Lifetime sales counter (verified)' },
      { key: 'vel', label: 'Sales/day', num: true, sort: (r) => r.v?.perDay, render: (r) => (r.v ? fmtNum(r.v.perDay, 1) : '—'), title: 'Observed between your visits' },
      { key: 'reviews', label: 'Reviews', num: true, sort: (r) => r.s.reviewCount, render: (r) => fmtNum(r.s.reviewCount) },
      { key: 'rating', label: 'Rating', num: true, sort: (r) => r.s.rating, render: (r) => (r.s.rating ? r.s.rating.toFixed(2) : '—') },
      { key: 'since', label: 'Since', num: true, sort: (r) => r.s.onEtsySince, render: (r) => (r.s.onEtsySince ? String(r.s.onEtsySince) : '—') },
      { key: 'listings', label: 'Listings', num: true, sort: (r) => r.s.totalListings, render: (r) => fmtNum(r.s.totalListings) },
      { key: 'seen', label: 'Products seen', num: true, sort: (r) => r.n, render: (r) => String(r.n) },
      { key: 'last', label: 'Last visit', num: true, sort: (r) => r.s.lastSeen, render: (r) => fmtDate(r.s.lastSeen) },
    ], rows, { onRow: (r) => ctx.go(`competitors/${encodeURIComponent(r.s.shopName)}`), sortKey: 'sales', caption: 'Shops' }) : empty(shops.length ? 'No tracked shops. Untick “Tracked only” to see every shop you visited.' : 'No shops yet. Visit a shop page or a listing page on Etsy.'));
  };
  draw();

  const tracked = shops.filter((s) => s.tracked && (listingsBy.get(s.shopName)?.length ?? 0) > 0);
  const overlap = tracked.length >= 2 ? keywordOverlap(new Map(tracked.slice(0, 10).map((s) => [s.shopName, listingsBy.get(s.shopName)!]))) : undefined;
  const gapBox = h('div');
  const mineSel = h('select', { 'aria-label': 'Your shop', onchange: () => drawGaps() }, h('option', { value: '' }, 'Choose your shop…'), shops.map((s) => h('option', { value: s.shopName }, s.shopName)));
  const drawGaps = () => {
    const mine = (mineSel as HTMLSelectElement).value;
    if (!mine) { gapBox.replaceChildren(h('small', null, 'Pick your own shop to find terms that tracked competitors use and you do not.')); return; }
    const myVocab = shopVocabulary(listingsBy.get(mine) ?? []);
    const comps = tracked.filter((s) => s.shopName !== mine).map((s) => shopVocabulary(listingsBy.get(s.shopName)!));
    const gaps = termGaps(myVocab, comps).filter((g) => g.shops >= Math.min(2, comps.length)).slice(0, 40);
    gapBox.replaceChildren(gaps.length ? h('div', { class: 'chips' }, gaps.map((g) => h('span', { class: 'chip', title: `Used by ${g.shops} competitor(s)` }, `${g.term} · ${g.shops}`))) : empty(comps.length ? 'No shared gaps found.' : 'Track at least one competitor with recorded products.'));
  };
  drawGaps();

  return h('div', { class: 'stack' },
    pageHead('Competitors', 'Shops you visited. Track a shop to monitor its sales counter and listings each time you open its page.',
      exportButtons('shops', async () => {
        const rows = compareShops(shops, listingsBy, snapsBy);
        return [{ name: 'Shops', rows: [
          ['Shop', 'Tracked', 'Sales (verified)', 'Observed sales/day', 'Reviews', 'Rating', 'On Etsy since', 'Listings', 'Admirers', 'Sales per review', 'Median price seen', 'Products seen', 'Last visit'],
          ...shops.map((s, i) => [s.shopName, s.tracked, s.sales, num(observedShopVelocity(snapsBy.get(s.shopName) ?? [])?.perDay, 2), s.reviewCount, s.rating, s.onEtsySince, s.totalListings, s.admirers, num(rows[i].salesPerReview, 2), num(rows[i].medianPrice), rows[i].observedListings, date(s.lastSeen)]),
        ] }];
      })),
    card(null, h('div', { class: 'row between' },
      h('label', { class: 'row', style: 'font-size:13px' }, h('input', { type: 'checkbox', checked: onlyTracked, onchange: (e: Event) => { onlyTracked = (e.target as HTMLInputElement).checked; draw(); } }), 'Tracked only'),
      h('form', { class: 'row', onsubmit: async (e: Event) => { e.preventDefault(); const v = ((e.target as HTMLFormElement).elements.namedItem('shop') as HTMLInputElement).value.trim(); if (v) { await repo.setShopTracked(v, true); toast(`Tracking ${v}. Visit its Etsy page to collect data.`); ctx.rerender(); } } },
        h('input', { name: 'shop', type: 'text', placeholder: 'Shop name to track', 'aria-label': 'Shop name to track' }), h('button', { class: 'btn small', type: 'submit' }, 'Track')),
      h('button', { class: 'btn small', type: 'button', onclick: () => { if (selected.size < 2) toast('Select 2 to 6 shops'); else ctx.go(`competitors/compare?shops=${encodeURIComponent([...selected].slice(0, 6).join('|'))}`); } }, 'Compare selected'))),
    box,
    h('div', { class: 'grid-2' },
      card(cardHead('Keyword overlap (tracked shops)', h('small', null, 'Jaccard similarity')),
        overlap ? h('div', { class: 'table-wrap' }, h('table', { class: 'data heat' },
          h('thead', null, h('tr', null, h('th', null, ''), overlap.shops.map((s) => h('th', null, s)))),
          h('tbody', null, overlap.shops.map((s, i) => h('tr', null, h('th', { scope: 'row' }, s), overlap.matrix[i].map((v, j) => h('td', { style: i === j ? '' : `background: color-mix(in srgb, var(--accent) ${Math.round(v * 70)}%, transparent)`, title: i === j ? '' : (overlap.shared.get(`${overlap.shops[Math.min(i, j)]}|${overlap.shops[Math.max(i, j)]}`) ?? []).slice(0, 20).join(', ') }, i === j ? '—' : `${Math.round(v * 100)}%`))))))) : empty('Track two or more shops and open some of their listings to compare vocabularies.'),
        h('small', null, 'Vocabulary = title words plus related search terms of the products you recorded for each shop.')),
      card(cardHead('Term gaps', mineSel), gapBox),
    ),
  );
}

export async function competitorDetailView(name: string, ctx: Ctx): Promise<Node> {
  const a = await analyseShop(name);
  if (!a) {
    return h('div', { class: 'stack' }, back('competitors', 'Competitors'), card(name, empty('No data for this shop yet.', h('a', { class: 'btn primary', href: `https://www.etsy.com/shop/${encodeURIComponent(name)}`, target: '_blank', rel: 'noopener' }, 'Open shop on Etsy ↗'))));
  }
  const s = a.shop;
  const sales = a.snaps.filter((x) => x.sales !== undefined).map((x) => ({ t: x.ts, v: x.sales! }));
  const reviews = a.snaps.filter((x) => x.reviewCount !== undefined).map((x) => ({ t: x.ts, v: x.reviewCount! }));
  const d = a.lastDiff;
  const prices = a.listings.map((l) => l.price).filter((p): p is number => p !== undefined);
  const cats = new Map<string, number>();
  for (const l of a.listings) if (l.category.length) cats.set(l.category[l.category.length - 1], (cats.get(l.category[l.category.length - 1]) ?? 0) + 1);

  return h('div', { class: 'stack' },
    back('competitors', 'Competitors'),
    pageHead(s.shopName, s.title ?? undefined,
      h('a', { class: 'btn small', href: s.url, target: '_blank', rel: 'noopener' }, 'Open on Etsy ↗'),
      h('button', { class: 'btn small', type: 'button', onclick: async () => { await repo.setShopTracked(s.shopName, !s.tracked); ctx.rerender(); } }, s.tracked ? 'Stop tracking' : 'Track shop'),
      h('a', { class: 'btn small', href: `#products?shop=${encodeURIComponent(s.shopName)}` }, 'Products'),
      printButton(),
      h('button', { class: 'btn small danger', type: 'button', onclick: async () => { if (confirmAction('Delete this shop and its history?')) { await repo.deleteShop(s.shopName); ctx.go('competitors'); } } }, 'Delete')),
    h('div', { class: 'grid' },
      card(null, kpi('Lifetime sales', fmtNum(s.sales), { prov: 'verified', sub: 'Etsy’s public counter' })),
      card(null, kpi('Sales per day', a.observed ? fmtNum(a.observed.perDay, 2) : '—', { prov: 'observed', sub: a.observed ? `+${fmtNum(a.observed.delta)} between ${fmtDate(a.observed.from)} and ${fmtDate(a.observed.to)}` : 'Needs two visits at least a day apart' })),
      card(null, kpi('Est. sales / month', a.observed ? fmtNum(a.observed.perDay * 30.44, 0) : '—', { prov: 'estimated', sub: 'Observed rate × 30.44, assumes the pace continues' })),
      card(null, kpi('Reviews', fmtNum(s.reviewCount), { prov: 'verified', sub: s.rating ? `${s.rating.toFixed(2)} ★` : undefined })),
      card(null, kpi('Sales per review', s.sales && s.reviewCount ? (s.sales / s.reviewCount).toFixed(1) : '—', { prov: 'verified', sub: 'Used to calibrate listing estimates' })),
      card(null, kpi('On Etsy since', s.onEtsySince ? String(s.onEtsySince) : '—', { prov: 'verified', sub: s.location })),
      card(null, kpi('Active listings', fmtNum(s.totalListings), { prov: 'verified', sub: s.admirers ? `${fmtNum(s.admirers)} admirers` : undefined })),
      card(null, kpi('Median price', fmtMoney(a.priceStats.median, a.priceStats.currency), { prov: 'verified', sub: `${a.priceStats.n} products seen · ${fmtMoney(a.priceStats.min, a.priceStats.currency)}–${fmtMoney(a.priceStats.max, a.priceStats.currency)}` })),
    ),
    d ? card(cardHead('Since your previous shop-page visit', prov('observed'), h('small', null, `${d.days.toFixed(1)} days`)),
      h('div', { class: 'grid' },
        kpi('New listings', String(d.newListings.length)),
        kpi('No longer visible', d.comparable ? String(d.removedListings.length) : '—', { sub: 'Only listings on the captured page are compared' }),
        kpi('Price changes', String(d.priceChanges.length)),
        kpi('Sales added', d.salesDelta !== undefined ? fmtNum(d.salesDelta) : '—')),
      d.priceChanges.length ? h('ul', { style: 'margin:10px 0 0;padding-left:18px;font-size:13px' }, d.priceChanges.map((p) => h('li', null, `${p.title}: ${fmtMoney(p.before, a.priceStats.currency)} → ${fmtMoney(p.after, a.priceStats.currency)}`))) : null,
    ) : h('div', { class: 'notice' }, 'Open this shop’s page again on a later day to see new or removed listings and price changes.'),
    h('div', { class: 'grid-2' },
      card('Sales counter over time', lineChart(sales, { label: 'Shop sales counter' }), h('small', null, 'Each point is a visit to this shop or one of its listings.')),
      card('Reviews over time', lineChart(reviews, { label: 'Shop reviews' })),
      card('Price distribution (products seen)', prices.length ? histogramChart(histogram(prices), { label: 'Prices', xFormat: (n) => fmtMoney(n, a.priceStats.currency, 0) }) : empty('No prices recorded.')),
      card('Categories & sections', h('div', { class: 'stack-sm' },
        cats.size ? h('div', { class: 'chips' }, [...cats.entries()].sort((x, y) => y[1] - x[1]).map(([c, n]) => h('span', { class: 'chip' }, `${c} · ${n}`))) : h('small', null, 'Open listings to record their categories.'),
        s.sections.length ? h('div', { class: 'chips' }, s.sections.map((x) => h('span', { class: 'chip' }, `${x.name}${x.count !== undefined ? ` · ${x.count}` : ''}`))) : null)),
    ),
    card('Change log', a.changes.length ? table([
      { key: 'ts', label: 'Date', sort: (c) => c.ts, render: (c) => fmtDate(c.ts) },
      { key: 'field', label: 'Change', sort: (c) => c.field, render: (c) => c.field },
      { key: 'before', label: 'Before', render: (c) => c.before ?? '' },
      { key: 'after', label: 'After', render: (c) => c.after ?? '' },
    ], a.changes, { sortKey: 'ts', limit: 100, caption: 'Shop changes' }) : empty('No changes recorded yet.')),
    card('Products seen from this shop', a.listings.length ? table([
      { key: 't', label: 'Product', sort: (l) => l.title, class: 'title-cell', render: (l) => h('span', { class: 'clip' }, l.title) },
      { key: 'p', label: 'Price', num: true, sort: (l) => l.price, render: (l) => fmtMoney(l.price, l.currency) },
      { key: 'r', label: 'Reviews', num: true, sort: (l) => l.listingReviewCount, render: (l) => fmtNum(l.listingReviewCount) },
      { key: 'f', label: 'Favourites', num: true, sort: (l) => l.favourites, render: (l) => fmtNum(l.favourites) },
      { key: 'd', label: 'First seen', num: true, sort: (l) => l.firstSeen, render: (l) => fmtDate(l.firstSeen) },
    ], a.listings, { onRow: (l) => ctx.go(`products/${l.listingId}`), sortKey: 'r', caption: 'Shop products' }) : empty('No products recorded yet.')),
  );
}

export async function competitorCompareView(_ctx: Ctx, q: URLSearchParams): Promise<Node> {
  const names = (q.get('shops') ?? '').split('|').filter(Boolean).slice(0, 6);
  const [all, listings, snaps] = await Promise.all([repo.shops(), repo.listings(), repo.allShopSnaps()]);
  const shops = all.filter((s) => names.includes(s.shopName));
  if (shops.length < 2) return h('div', { class: 'stack' }, back('competitors', 'Competitors'), empty('Select at least two shops with data.'));
  const lb = new Map<string, ListingRecord[]>();
  for (const l of listings) if (l.shopName && names.includes(l.shopName)) lb.set(l.shopName, [...(lb.get(l.shopName) ?? []), l]);
  const sb = new Map<string, ShopSnapshot[]>();
  for (const s of snaps) if (names.includes(s.shopName)) sb.set(s.shopName, [...(sb.get(s.shopName) ?? []), s]);
  const rows = compareShops(shops, lb, sb);
  const vel = new Map(shops.map((s) => [s.shopName, observedShopVelocity(sb.get(s.shopName) ?? [])]));
  const r = (label: string, f: (x: (typeof rows)[number]) => string, p?: 'verified' | 'observed') => h('tr', null, h('th', { scope: 'row' }, h('span', { class: 'row' }, label, p ? prov(p) : null)), rows.map((x) => h('td', { class: 'num' }, f(x))));
  return h('div', { class: 'stack' },
    back('competitors', 'Competitors'),
    pageHead('Shop comparison', 'Side-by-side view of public shop figures and the products you recorded.'),
    card(null, h('div', { class: 'table-wrap' }, h('table', { class: 'data' },
      h('thead', null, h('tr', null, h('th', null, 'Metric'), rows.map((x) => h('th', { class: 'num' }, h('a', { href: `#competitors/${encodeURIComponent(x.shopName)}` }, x.shopName))))),
      h('tbody', null,
        r('Lifetime sales', (x) => fmtNum(x.sales), 'verified'),
        r('Sales per day', (x) => (vel.get(x.shopName) ? fmtNum(vel.get(x.shopName)!.perDay, 2) : '—'), 'observed'),
        r('Reviews', (x) => fmtNum(x.reviewCount), 'verified'),
        r('Rating', (x) => (x.rating ? x.rating.toFixed(2) : '—'), 'verified'),
        r('On Etsy since', (x) => (x.onEtsySince ? String(x.onEtsySince) : '—'), 'verified'),
        r('Active listings', (x) => fmtNum(x.totalListings), 'verified'),
        r('Sales per review', (x) => (x.salesPerReview ? x.salesPerReview.toFixed(1) : '—')),
        r('Sales per listing', (x) => (x.salesPerListing ? x.salesPerListing.toFixed(1) : '—')),
        r('Median price (seen)', (x) => (x.medianPrice !== undefined ? x.medianPrice.toFixed(2) : '—')),
        r('Price IQR (seen)', (x) => (x.p25Price !== undefined ? `${x.p25Price.toFixed(2)}–${x.p75Price!.toFixed(2)}` : '—')),
        r('Products recorded', (x) => String(x.observedListings)),
        r('Categories (diversity)', (x) => String(x.categories)),
        r('New listings, last 30 days', (x) => String(x.newListings30d), 'observed'),
        h('tr', null, h('th', { scope: 'row' }, 'Top terms'), rows.map((x) => h('td', null, h('div', { class: 'chips' }, x.topWords.map((w) => h('span', { class: 'chip' }, w)))))),
      )))),
  );
}
