/** Compact view of the current page's analysis. Shared by the in-page panel and the browser sidebar. */
import { h } from '../shared/dom';
import { fmtDate, fmtMoney, fmtNum, fmtPct, fmtRange } from '../shared/format';
import type { PanelSummary } from '../core/summaries';
import type { Settings } from '../shared/types';
import { explain, grade, kpi, prov } from './components';

export interface SummaryActions {
  open: (route: string) => void;
  track: (shop: string, on: boolean) => Promise<void>;
  saveKeyword: (term: string) => Promise<void>;
  saveListing: (id: string) => Promise<void>;
}

const btn = (label: string, onclick: () => void, primary = false) => h('button', { type: 'button', class: `btn small${primary ? ' primary' : ''}`, onclick }, label);

function flash(b: HTMLButtonElement, text: string) {
  const old = b.textContent;
  b.textContent = text;
  b.disabled = true;
  setTimeout(() => { b.textContent = old; b.disabled = false; }, 1500);
}

export function renderSummary(s: PanelSummary | undefined, settings: Settings, act: SummaryActions): Node {
  if (!s) return h('p', { class: 'muted' }, 'This page is not an Etsy search, listing or shop page.');

  if (s.kind === 'listing') {
    const a = s.analysis;
    if (!a) return h('p', { class: 'muted' }, 'No data could be read from this listing page.');
    const l = a.listing;
    const e = a.estimate;
    const save = btn('Save product', () => act.saveListing(l.listingId).then(() => flash(save, 'Saved')));
    const issues = a.audit.results.filter((r) => r.severity === 'error' || r.severity === 'warning').slice(0, 3);
    return h('div', { class: 'stack' },
      h('h3', { class: 'clip' }, l.title || `Listing ${l.listingId}`),
      h('div', { class: 'grid', style: 'grid-template-columns:repeat(2,minmax(0,1fr))' },
        kpi('Price', fmtMoney(l.price, l.currency), { prov: 'verified' }),
        kpi('Shop sales (lifetime)', fmtNum(l.shopSales), { prov: 'verified' }),
        kpi('Listing reviews', fmtNum(l.listingReviewCount), { prov: 'verified' }),
        kpi('Favourites', fmtNum(l.favourites), { prov: 'verified' }),
        kpi('Est. lifetime sales', e.lifetime ? fmtRange(e.lifetime, (n) => fmtNum(n)) : '—', { prov: 'estimated', sub: e.available ? h('span', { class: 'row' }, 'Confidence', grade(e.grade)) : e.reason }),
        kpi('Est. sales / month', a.periods ? fmtRange(a.periods.month) : '—', { prov: 'estimated', sub: e.velocityMethod !== 'none' ? `method: ${e.velocityMethod}` : 'No velocity data yet' }),
        kpi('Est. gross revenue / month', a.revenue?.month ? fmtMoney(a.revenue.month.mid, a.revenue.currency, 0) : '—', { prov: 'estimated', sub: 'Gross, before fees and costs' }),
        kpi('Listed on', fmtDate(l.listedOn), { prov: 'verified', sub: 'Latest renewal date' }),
      ),
      explain('How the estimate is calculated', e.steps.length ? e.steps : ['Open this listing page to collect review and sales counts.']),
      h('div', { class: 'stack-sm' },
        h('div', { class: 'row between' }, h('strong', null, `SEO checks: ${a.audit.score}/100`), a.changes.length ? h('span', { class: 'badge observed' }, `${a.changes.length} change(s) recorded`) : null),
        issues.length ? h('ul', { style: 'margin:0;padding-left:18px;font-size:12px' }, issues.map((i) => h('li', null, i.message))) : h('small', null, 'No warnings from the rule set.'),
      ),
      h('div', { class: 'row' }, btn('Open full analysis', () => act.open(`products/${l.listingId}`), true), save, btn('Audit in SEO tools', () => act.open(`seo/audit/${l.listingId}`))),
    );
  }

  if (s.kind === 'search') {
    const a = s.analysis;
    if (!a?.record.latest) return h('p', { class: 'muted' }, 'No search results were read on this page.');
    const st = a.record.latest;
    const o = a.opportunity;
    const save = btn('Save keyword', () => act.saveKeyword(s.term).then(() => flash(save, 'Saved')));
    return h('div', { class: 'stack' },
      h('h3', null, `“${s.term}”`),
      h('div', { class: 'grid', style: 'grid-template-columns:repeat(2,minmax(0,1fr))' },
        kpi('Results', st.resultCount !== undefined ? `${st.resultCountIsLowerBound ? '>' : ''}${fmtNum(st.resultCount)}` : '—', { prov: 'verified' }),
        kpi('Opportunity', o ? `${o.score}/100` : '—', { prov: 'estimated', sub: 'Your weights, see Keywords' }),
        kpi('Difficulty', o ? `${o.difficulty.score}/100` : '—', { prov: 'estimated' }),
        kpi('Median price', fmtMoney(st.medianPrice, st.currency), { prov: 'verified', sub: `IQR ${fmtMoney(st.p25Price, st.currency)}–${fmtMoney(st.p75Price, st.currency)}` }),
        kpi('Ads in sample', fmtPct(st.adShare), { prov: 'verified', sub: `${st.sampleSize} results read` }),
        kpi('Bestseller / Popular now', `${fmtPct(st.bestsellerShare)} / ${fmtPct(st.popularNowShare)}`, { prov: 'verified' }),
      ),
      h('div', { class: 'stack-sm' }, h('strong', null, 'Frequent phrases in result titles'),
        a.suggestions.length ? h('div', { class: 'chips' }, a.suggestions.slice(0, 10).map((x) => h('span', { class: 'chip', title: `${x.docs} of ${st.sampleSize} titles` }, x.phrase))) : h('small', null, 'Not enough titles yet.')),
      h('small', null, 'Etsy does not publish search volume. These figures come from the results page you opened.'),
      h('div', { class: 'row' }, btn('Open keyword analysis', () => act.open(`keywords/${encodeURIComponent(s.term)}`), true), save),
    );
  }

  const a = s.analysis;
  if (!a) return h('p', { class: 'muted' }, 'No shop data could be read from this page.');
  const sh = a.shop;
  let tracked = sh.tracked;
  const trackBtn = btn(tracked ? 'Stop tracking' : 'Track shop', async () => {
    tracked = !tracked;
    await act.track(sh.shopName, tracked);
    trackBtn.textContent = tracked ? 'Stop tracking' : 'Track shop';
  });
  const d = a.lastDiff;
  return h('div', { class: 'stack' },
    h('h3', null, sh.shopName),
    h('div', { class: 'grid', style: 'grid-template-columns:repeat(2,minmax(0,1fr))' },
      kpi('Sales (lifetime)', fmtNum(sh.sales), { prov: 'verified' }),
      kpi('Reviews', fmtNum(sh.reviewCount), { prov: 'verified', sub: sh.rating ? `${sh.rating.toFixed(2)} ★` : undefined }),
      kpi('On Etsy since', sh.onEtsySince ? String(sh.onEtsySince) : '—', { prov: 'verified' }),
      kpi('Listings', fmtNum(sh.totalListings), { prov: 'verified' }),
      kpi('Sales per day', a.observed ? fmtNum(a.observed.perDay, 1) : '—', { prov: 'observed', sub: a.observed ? `+${a.observed.delta} over ${a.observed.days.toFixed(1)} days` : 'Visit again later to measure' }),
      kpi('Median price', fmtMoney(a.priceStats.median, a.priceStats.currency), { prov: 'verified', sub: `${a.priceStats.n} listings seen` }),
    ),
    d ? h('div', { class: 'notice' }, `Since your previous visit: ${d.newListings.length} new, ${d.comparable ? d.removedListings.length : 0} no longer visible, ${d.priceChanges.length} price change(s).`) : h('small', null, 'Changes appear from your second visit to this shop page onwards.'),
    h('div', { class: 'row' }, btn('Open shop analysis', () => act.open(`competitors/${encodeURIComponent(sh.shopName)}`), true), trackBtn),
  );
}

export { prov };
