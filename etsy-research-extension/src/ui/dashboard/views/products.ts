import { h } from '../../../shared/dom';
import * as repo from '../../../core/storage/repo';
import { analyseListing } from '../../../core/summaries';
import { estimateListingSales, peerRatiosFrom, SalesEstimate } from '../../../core/sales';
import { keywordDifficulty } from '../../../core/keywords';
import { DAY } from '../../../core/stats';
import { convert, fmtAge, fmtDate, fmtMoney, fmtNum, fmtRange } from '../../../shared/format';
import type { ListingRecord, Settings } from '../../../shared/types';
import { card, cardHead, empty, explain, grade, kpi, lineChart, prov, Column, table, toast, confirmAction } from '../../components';
import { back, date, exportButtons, field, num, pageHead, printButton } from './common';
import type { Ctx } from '../main';

interface Row {
  l: ListingRecord;
  est: SalesEstimate;
  monthly?: number;
  revenueMonth?: number;
  lifetimeRevenue?: number;
  currency?: string;
  ageDays?: number;
  competition?: number;
}

async function rows(settings: Settings): Promise<Row[]> {
  const b = await repo.bulk();
  const ratios = peerRatiosFrom(b.shopList, settings.minShopReviewsForCalibration);
  return b.listings.map((l) => {
    const shop = l.shopName ? b.shops.get(l.shopName) : undefined;
    const est = estimateListingSales(l, b.listingSnaps.get(l.listingId) ?? [], shop, l.shopName ? b.shopSnaps.get(l.shopName) ?? [] : [], {
      fallbackSalesPerReview: settings.fallbackSalesPerReview, minShopReviewsForCalibration: settings.minShopReviewsForCalibration, peerRatios: ratios,
    });
    const monthly = est.perDay ? est.perDay.mid * 30.44 : undefined;
    const price = convert(l.price, l.currency, settings);
    const disc = 1 - settings.defaultDiscountPct / 100;
    const kw = l.searchQueries.length ? b.keywords.get(l.searchQueries[l.searchQueries.length - 1]) : undefined;
    return {
      l, est, monthly,
      revenueMonth: monthly !== undefined && price.value !== undefined ? monthly * price.value * disc : undefined,
      lifetimeRevenue: est.lifetime && price.value !== undefined ? est.lifetime.mid * price.value * disc : undefined,
      currency: price.currency,
      ageDays: l.listedOn ? (Date.now() - l.listedOn) / DAY : undefined,
      competition: kw?.latest ? keywordDifficulty(kw.latest).score : undefined,
    };
  });
}

interface Filters {
  q: string; shop: string; category: string; type: 'all' | 'digital' | 'physical'; minPrice: string; maxPrice: string;
  minSales: string; minRevenue: string; minReviews: string; minRating: string; maxAge: string; competition: 'all' | 'low' | 'medium' | 'high'; detailedOnly: boolean;
}
const filters: Filters = { q: '', shop: '', category: '', type: 'all', minPrice: '', maxPrice: '', minSales: '', minRevenue: '', minReviews: '', minRating: '', maxAge: '', competition: 'all', detailedOnly: false };
let sort = { key: 'monthly', dir: -1 as 1 | -1 };

function apply(rs: Row[]): Row[] {
  const n = (s: string) => (s.trim() === '' ? undefined : Number(s));
  const q = filters.q.toLowerCase();
  return rs.filter(({ l, monthly, revenueMonth, ageDays, competition }) => {
    if (filters.detailedOnly && !l.detailed) return false;
    if (q && !`${l.title} ${l.searchQueries.join(' ')} ${l.relatedTerms.join(' ')}`.toLowerCase().includes(q)) return false;
    if (filters.shop && !(l.shopName ?? '').toLowerCase().includes(filters.shop.toLowerCase())) return false;
    if (filters.category && l.category[0] !== filters.category) return false;
    if (filters.type === 'digital' && !l.isDigital) return false;
    if (filters.type === 'physical' && l.isDigital) return false;
    const chk = (v: number | undefined, min?: number, max?: number) => (min === undefined || (v !== undefined && v >= min)) && (max === undefined || (v !== undefined && v <= max));
    if (!chk(l.price, n(filters.minPrice), n(filters.maxPrice))) return false;
    if (!chk(monthly, n(filters.minSales))) return false;
    if (!chk(revenueMonth, n(filters.minRevenue))) return false;
    if (!chk(l.listingReviewCount, n(filters.minReviews))) return false;
    if (!chk(l.rating, n(filters.minRating))) return false;
    if (!chk(ageDays, undefined, n(filters.maxAge))) return false;
    if (filters.competition !== 'all') {
      if (competition === undefined) return false;
      const lvl = competition < 40 ? 'low' : competition <= 65 ? 'medium' : 'high';
      if (lvl !== filters.competition) return false;
    }
    return true;
  });
}

export async function productsView(ctx: Ctx, query: URLSearchParams): Promise<Node> {
  if (query.get('q')) filters.q = query.get('q')!;
  if (query.get('shop')) filters.shop = query.get('shop')!;
  const all = await rows(ctx.settings);
  const categories = [...new Set(all.map((r) => r.l.category[0]).filter(Boolean))].sort();
  const results = h('div');

  const cols: Column<Row>[] = [
    { key: 'title', label: 'Product', sort: (r) => r.l.title.toLowerCase(), class: 'title-cell', render: (r) => h('div', { class: 'row', style: 'flex-wrap:nowrap' }, r.l.imageUrl ? h('img', { class: 'thumb', src: r.l.imageUrl, alt: '', loading: 'lazy' }) : null, h('div', { class: 'stack-sm', style: 'gap:2px;min-width:0' }, h('span', { class: 'clip' }, r.l.title || `#${r.l.listingId}`), h('small', null, r.l.shopName ?? '—', r.l.detailed ? '' : ' · seen in results only'))) },
    { key: 'price', label: 'Price', num: true, sort: (r) => r.l.price, render: (r) => fmtMoney(r.l.price, r.l.currency) },
    { key: 'reviews', label: 'Reviews', num: true, sort: (r) => r.l.listingReviewCount, render: (r) => fmtNum(r.l.listingReviewCount), title: 'Listing reviews (verified)' },
    { key: 'fav', label: 'Favourites', num: true, sort: (r) => r.l.favourites, render: (r) => fmtNum(r.l.favourites), title: 'Popularity indicator (verified)' },
    { key: 'rating', label: 'Rating', num: true, sort: (r) => r.l.rating, render: (r) => (r.l.rating ? r.l.rating.toFixed(2) : '—') },
    { key: 'lifetime', label: 'Est. total sales', num: true, sort: (r) => r.est.lifetime?.mid, render: (r) => (r.est.lifetime ? h('span', { class: 'row', style: 'justify-content:flex-end;flex-wrap:nowrap' }, fmtNum(r.est.lifetime.mid), grade(r.est.grade)) : '—') },
    { key: 'monthly', label: 'Est. sales/mo', num: true, sort: (r) => r.monthly, render: (r) => (r.monthly !== undefined ? fmtNum(r.monthly, r.monthly < 10 ? 1 : 0) : '—'), title: 'Estimated sales velocity' },
    { key: 'revenue', label: 'Est. revenue/mo', num: true, sort: (r) => r.revenueMonth, render: (r) => fmtMoney(r.revenueMonth, r.currency, 0) },
    { key: 'age', label: 'Listed on', num: true, sort: (r) => r.l.listedOn, render: (r) => (r.l.listedOn ? fmtAge(r.l.listedOn) : '—'), title: 'Time since the "Listed on" date (latest renewal)' },
    { key: 'comp', label: 'Competition', num: true, sort: (r) => r.competition, render: (r) => (r.competition !== undefined ? String(r.competition) : '—'), title: 'Difficulty of the last search this product appeared in' },
  ];

  const draw = () => {
    const list = apply(all);
    results.replaceChildren(
      h('div', { class: 'row between', style: 'margin-bottom:8px' }, h('small', null, `${list.length} of ${all.length} products`), h('small', null, 'Est. figures are modelled. Open a product to see its method and range.')),
      list.length ? table(cols, list, { onRow: (r) => ctx.go(`products/${r.l.listingId}`), sortKey: sort.key, sortDir: sort.dir, caption: 'Products' }) : empty(all.length ? 'No products match these filters.' : 'No products yet. Browse Etsy search results and listing pages with page reading turned on.'),
    );
  };

  const bind = (key: keyof Filters) => (e: Event) => { (filters as any)[key] = (e.target as HTMLInputElement).type === 'checkbox' ? (e.target as HTMLInputElement).checked : (e.target as HTMLInputElement).value; draw(); };
  const txt = (key: keyof Filters, ph = '', type = 'text') => h('input', { type, value: String(filters[key]), placeholder: ph, oninput: bind(key), step: type === 'number' ? 'any' : undefined, min: type === 'number' ? 0 : undefined });
  const sel = (key: keyof Filters, opts: [string, string][]) => h('select', { onchange: bind(key) }, opts.map(([v, l]) => h('option', { value: v, selected: filters[key] === v }, l)));

  const filterCard = card(cardHead('Filters', h('button', { class: 'btn small', type: 'button', onclick: () => { Object.assign(filters, { q: '', shop: '', category: '', type: 'all', minPrice: '', maxPrice: '', minSales: '', minRevenue: '', minReviews: '', minRating: '', maxAge: '', competition: 'all', detailedOnly: false }); ctx.rerender(); } }, 'Reset')),
    h('div', { class: 'filters' },
      field('Keyword', txt('q', 'title, search or term')),
      field('Shop', txt('shop', 'shop name')),
      field('Category', sel('category', [['', 'All categories'], ...categories.map((c) => [c, c] as [string, string])])),
      field('Product type', sel('type', [['all', 'All'], ['physical', 'Physical'], ['digital', 'Digital']])),
      h('label', { class: 'field' }, 'Price range', h('div', { class: 'range' }, txt('minPrice', 'min', 'number'), txt('maxPrice', 'max', 'number'))),
      field('Min est. sales / month', txt('minSales', '', 'number')),
      field('Min est. revenue / month', txt('minRevenue', '', 'number')),
      field('Min reviews', txt('minReviews', '', 'number')),
      field('Min rating', txt('minRating', 'e.g. 4.5', 'number')),
      field('Max days since listed', txt('maxAge', '', 'number')),
      field('Competition level', sel('competition', [['all', 'All'], ['low', 'Low (<40)'], ['medium', 'Medium (40–65)'], ['high', 'High (>65)']])),
      h('label', { class: 'row', style: 'font-size:13px' }, h('input', { type: 'checkbox', checked: filters.detailedOnly, onchange: bind('detailedOnly') }), 'Only products with full listing data'),
    ));

  draw();
  return h('div', { class: 'stack' },
    pageHead('Products', 'Every listing you have seen on Etsy. Open a listing page to collect its full data and enable sales estimates.',
      exportButtons('products', () => {
        const list = apply(all);
        return [{ name: 'Products', rows: [
          ['Listing ID', 'Title', 'URL', 'Shop', 'Price', 'Currency', 'Listing reviews', 'Rating', 'Favourites', 'Shop sales (verified)', 'Listed on', 'Category', 'Digital', 'Est. lifetime sales', 'Est. low', 'Est. high', 'Est. sales / month', 'Est. revenue / month', 'Revenue currency', 'Confidence grade', 'Velocity method'],
          ...list.map((r) => [r.l.listingId, r.l.title, r.l.url, r.l.shopName, r.l.price, r.l.currency, r.l.listingReviewCount, r.l.rating, r.l.favourites, r.l.shopSales, date(r.l.listedOn), r.l.category.join(' > '), r.l.isDigital ?? '', num(r.est.lifetime?.mid, 0), num(r.est.lifetime?.low, 0), num(r.est.lifetime?.high, 0), num(r.monthly, 1), num(r.revenueMonth, 0), r.currency, r.est.available ? r.est.grade : '', r.est.velocityMethod]),
        ] }];
      })),
    filterCard,
    results,
  );
}

export async function productDetailView(id: string, ctx: Ctx, overrides: { price?: number; discountPct?: number } = {}): Promise<Node> {
  const a = await analyseListing(id, ctx.settings, overrides);
  if (!a) return h('div', { class: 'stack' }, back('products', 'Products'), empty('This product is not in your data.'));
  const { listing: l, estimate: e } = a;
  const collections = (await repo.collections()).filter((c) => c.kind === 'products');
  const wrap = h('div', { class: 'stack' });

  const priceIn = h('input', { type: 'number', step: 'any', min: 0, value: String(a.revenue?.unitPrice ?? l.price ?? '') });
  const discIn = h('input', { type: 'number', step: 'any', min: 0, max: 100, value: String(a.revenue?.discountPct ?? ctx.settings.defaultDiscountPct) });
  const recalc = async () => {
    const node = await productDetailView(id, ctx, { price: priceIn.value === '' ? undefined : Number(priceIn.value), discountPct: Number(discIn.value) || 0 });
    wrap.replaceWith(node);
  };

  const periodsRows: [string, string, string][] = [
    ['Per day', fmtRange(a.periods?.day, (n) => fmtNum(n, 2)), a.revenue?.day ? fmtRange(a.revenue.day, (n) => fmtMoney(n, a.revenue!.currency)) : '—'],
    ['Per week', fmtRange(a.periods?.week, (n) => fmtNum(n, 1)), a.revenue?.week ? fmtRange(a.revenue.week, (n) => fmtMoney(n, a.revenue!.currency, 0)) : '—'],
    ['Per month', fmtRange(a.periods?.month, (n) => fmtNum(n, 1)), a.revenue?.month ? fmtRange(a.revenue.month, (n) => fmtMoney(n, a.revenue!.currency, 0)) : '—'],
    ['Per year', fmtRange(a.periods?.year), a.revenue?.year ? fmtRange(a.revenue.year, (n) => fmtMoney(n, a.revenue!.currency, 0)) : '—'],
    ['Lifetime', fmtRange(e.lifetime), a.revenue?.lifetime ? fmtRange(a.revenue.lifetime, (n) => fmtMoney(n, a.revenue!.currency, 0)) : '—'],
  ];

  const snaps = a.snaps;
  const series = (pick: (s: (typeof snaps)[number]) => number | undefined) => snaps.map((s) => ({ t: s.ts, v: pick(s) })).filter((p): p is { t: number; v: number } => p.v !== undefined);

  wrap.append(
    back('products', 'Products'),
    h('div', { class: 'page-head' },
      h('div', { class: 'listing-head' }, l.imageUrl ? h('img', { src: l.imageUrl, alt: '' }) : null,
        h('div', { class: 'stack-sm' }, h('h1', null, l.title || `Listing ${l.listingId}`),
          h('div', { class: 'row' }, l.shopName ? h('a', { href: `#competitors/${encodeURIComponent(l.shopName)}` }, l.shopName) : null, h('a', { href: l.url, target: '_blank', rel: 'noopener' }, 'View on Etsy ↗'), h('small', null, `First recorded ${fmtDate(l.firstSeen)} · last ${fmtDate(l.lastSeen)}`)),
          l.badges.length ? h('div', { class: 'chips' }, l.badges.map((b) => h('span', { class: 'chip' }, b))) : null)),
      h('div', { class: 'row no-print' },
        collections.length ? h('select', { 'aria-label': 'Add to collection', onchange: async (ev: Event) => { const v = (ev.target as HTMLSelectElement).value; if (v) { await repo.addToCollection(v, l.listingId); toast('Added to collection'); (ev.target as HTMLSelectElement).value = ''; } } }, h('option', { value: '' }, 'Add to collection…'), collections.map((c) => h('option', { value: c.id }, c.name))) : h('a', { class: 'btn small', href: '#saved' }, 'Create a collection'),
        h('a', { class: 'btn small', href: `#seo/audit/${l.listingId}` }, 'SEO audit'),
        printButton(),
        h('button', { class: 'btn small danger', type: 'button', onclick: async () => { if (confirmAction('Delete this product and its history?')) { await repo.deleteListing(l.listingId); ctx.go('products'); } } }, 'Delete'))),
    l.detailed ? '' : h('div', { class: 'notice info' }, 'This product was only seen in search results. Open its listing page on Etsy to collect reviews, sales counter and dates.'),
    h('div', { class: 'grid' },
      card(null, kpi('Price', fmtMoney(l.price, l.currency), { prov: 'verified', sub: l.originalPrice ? `was ${fmtMoney(l.originalPrice, l.currency)}` : l.isDigital ? 'Digital product' : 'Physical product' })),
      card(null, kpi('Listing reviews', fmtNum(l.listingReviewCount), { prov: 'verified', sub: l.rating ? `${l.rating.toFixed(2)} ★ average` : undefined })),
      card(null, kpi('Shop lifetime sales', fmtNum(l.shopSales), { prov: 'verified', sub: l.shopReviewCount ? `${fmtNum(l.shopReviewCount)} shop reviews` : undefined })),
      card(null, kpi('Favourites', fmtNum(l.favourites), { prov: 'verified', sub: l.basketCount ? `in ${l.basketCount}+ baskets` : undefined })),
      card(null, kpi('Listed on', fmtDate(l.listedOn), { prov: 'verified', sub: 'Latest renewal, not original creation' })),
      card(null, kpi('Category', l.category.length ? l.category[l.category.length - 1] : '—', { sub: l.category.slice(0, -1).join(' › ') || undefined })),
    ),
    card(cardHead('Sales & revenue estimate', prov('estimated'), e.available ? h('span', { class: 'row' }, 'Confidence', grade(e.grade)) : null),
      e.available ? h('div', { class: 'stack' },
        h('div', { class: 'table-wrap' }, h('table', { class: 'data' }, h('thead', null, h('tr', null, h('th', null, 'Period'), h('th', { class: 'num' }, 'Est. sales (90% range)'), h('th', { class: 'num' }, `Est. gross revenue${a.revenue?.currency ? ` (${a.revenue.currency})` : ''}`))),
          h('tbody', null, periodsRows.map(([p, s, r]) => h('tr', null, h('td', null, p), h('td', { class: 'num' }, s), h('td', { class: 'num' }, r)))))),
        e.velocityMethod === 'none' ? h('div', { class: 'notice' }, 'There is no velocity data yet, so only the lifetime estimate is shown. Revisit this listing in a few days, or visit the shop page to record its “On Etsy since” year.') : null,
        h('div', { class: 'row no-print' },
          h('label', { class: 'field' }, 'Price assumption', priceIn),
          h('label', { class: 'field' }, 'Average discount %', discIn),
          h('button', { class: 'btn small', type: 'button', onclick: recalc, style: 'align-self:flex-end' }, 'Recalculate')),
        h('small', null, 'Revenue is estimated gross revenue: sales × price × (1 − discount). It does not deduct Etsy fees, shipping, taxes or production costs.', a.revenue?.converted ? ` Converted to ${a.revenue.currency} with your manual rate.` : ''),
        explain('Method and confidence', [...e.steps, ...e.gradeReasons.map((g) => `Confidence: ${g}`), 'Limitations: review rates differ by category and buyer; multi-item orders, gifts and digital items leave fewer reviews; Etsy does not publish per-listing sales.']),
      ) : h('p', { class: 'muted' }, e.reason ?? 'Not enough data.'),
    ),
    card('Performance indicators', h('div', { class: 'table-wrap' }, h('table', { class: 'data' }, h('tbody', null, a.indicators.map((i) => h('tr', null, h('td', null, i.label), h('td', { class: 'num' }, i.display), h('td', null, prov(i.provenance)), h('td', null, h('small', null, i.note)))))))),
    h('div', { class: 'grid-2' },
      card('Price history', lineChart(series((s) => s.price), { label: 'Price history', yFormat: (n) => fmtMoney(n, l.currency), step: true })),
      card('Listing reviews over time', lineChart(series((s) => s.listingReviewCount), { label: 'Listing reviews' })),
      card('Favourites over time', lineChart(series((s) => s.favourites), { label: 'Favourites' })),
      card('Change log', a.changes.length ? h('div', { class: 'stack-sm' }, a.changes.map((c) => h('div', { class: 'row between' }, h('span', null, `${c.field}: ${c.before ?? ''} → ${c.after ?? ''}`), h('small', null, fmtDate(c.ts))))) : empty('No changes recorded yet. Each revisit is compared with the previous one.')),
    ),
    h('div', { class: 'grid-2' },
      card('Variations', l.variations.length ? h('div', { class: 'stack-sm' }, l.variations.map((v) => h('div', null, h('strong', null, v.name), h('div', { class: 'chips', style: 'margin-top:4px' }, v.options.map((o) => h('span', { class: 'chip' }, o)))))) : empty('No variation selectors were found on the page.')),
      card('Related search terms on the page', l.relatedTerms.length ? h('div', { class: 'stack-sm' }, h('div', { class: 'chips' }, l.relatedTerms.map((t) => h('span', { class: 'chip' }, t))), h('small', null, 'Etsy links these from the listing page. They often reflect the listing’s tags, but Etsy does not label them as tags.')) : empty('None found on the page.')),
      card('Shipping & details', h('div', { class: 'stack-sm' }, h('div', null, 'Ships from: ', l.shipsFrom ?? '—'), h('div', null, 'Free shipping shown: ', l.freeShipping ? 'yes' : 'no'), h('div', null, 'Images: ', fmtNum(l.imageCount)), h('div', null, 'Seen in searches: ', l.searchQueries.length ? l.searchQueries.map((q, i) => [i ? ', ' : '', h('a', { href: `#keywords/${encodeURIComponent(q)}` }, q)]) : '—'))),
      card(cardHead('SEO checks', h('a', { class: 'btn small', href: `#seo/audit/${l.listingId}` }, 'Full audit')), h('div', { class: 'stack-sm' }, h('div', { class: 'score-ring' }, `${a.audit.score}/100`), a.audit.results.filter((r) => r.severity !== 'pass').slice(0, 5).map((r) => h('div', { class: 'rule' }, h('span', { class: `sev ${r.severity}` }, r.severity), h('span', null, r.message))))),
    ),
  );
  return wrap;
}
