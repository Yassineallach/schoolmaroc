/**
 * Keyword research engine.
 *
 * Etsy does not publish search volume, so no "searches per month" figure is
 * produced. Instead, indicators are computed from the search results page the
 * user opened, and every one is labelled with what it actually measures.
 */
import { DAY, clamp, herfindahl, isNum, logScale, mean, median, nums, quantile, slope } from './stats';
import { phraseFrequencies, words } from './text';
import type { KeywordSnapshot, KeywordStats, ScoringWeights, SearchExtraction } from '../shared/types';

export function computeKeywordStats(x: SearchExtraction): KeywordStats {
  const organic = x.cards.filter((c) => !c.isAd);
  const all = x.cards;
  const n = all.length || 1;
  const share = (pred: (c: (typeof all)[number]) => boolean) => all.filter(pred).length / n;
  const prices = nums(all.map((c) => c.price));
  const currencies = all.map((c) => c.currency).filter(Boolean) as string[];
  const shopKeys = organic.map((c) => c.shopName || c.shopId || '').filter(Boolean);
  return {
    resultCount: x.resultCount,
    resultCountIsLowerBound: x.resultCountIsLowerBound,
    sampleSize: all.length,
    adShare: all.length ? share((c) => c.isAd) : 0,
    bestsellerShare: all.length ? share((c) => c.badges.includes('Bestseller')) : 0,
    popularNowShare: all.length ? share((c) => c.badges.includes('Popular now')) : 0,
    starSellerShare: all.length ? share((c) => c.badges.includes('Star Seller')) : 0,
    freeShippingShare: all.length ? share((c) => c.freeShipping) : 0,
    digitalShare: all.length ? share((c) => !!c.isDigital) : 0,
    medianPrice: median(prices),
    p25Price: quantile(prices, 0.25),
    p75Price: quantile(prices, 0.75),
    minPrice: prices.length ? Math.min(...prices) : undefined,
    maxPrice: prices.length ? Math.max(...prices) : undefined,
    medianCardReviews: median(nums(all.map((c) => c.cardReviewCount))),
    meanRating: mean(nums(all.map((c) => c.rating))),
    shopConcentration: herfindahl(shopKeys),
    distinctShops: new Set(shopKeys).size,
    currency: mostCommon(currencies),
  };
}

function mostCommon(xs: string[]): string | undefined {
  const m = new Map<string, number>();
  for (const x of xs) m.set(x, (m.get(x) ?? 0) + 1);
  let best: string | undefined;
  let bc = 0;
  for (const [k, c] of m) if (c > bc) { best = k; bc = c; }
  return best;
}

export interface Component {
  key: string;
  label: string;
  value: number;
  detail: string;
}

export interface Difficulty {
  score: number;
  components: Component[];
}

/** Keyword difficulty 0–100 (higher = harder to rank). */
export function keywordDifficulty(s: KeywordStats): Difficulty {
  const supply = isNum(s.resultCount) ? logScale(s.resultCount, 100, 500_000) : 0.5;
  const depth = isNum(s.medianCardReviews) ? logScale(s.medianCardReviews, 10, 20_000) : 0.5;
  const ads = clamp(s.adShare * 2);
  const conc = clamp(s.shopConcentration * 5);
  const components: Component[] = [
    { key: 'supply', label: 'Competing listings', value: supply, detail: isNum(s.resultCount) ? `${s.resultCount.toLocaleString()} results, log scale from 100 to 500k` : 'Result count not captured (neutral 0.5)' },
    { key: 'depth', label: 'Established competitors', value: depth, detail: isNum(s.medianCardReviews) ? `Median review count on result cards: ${Math.round(s.medianCardReviews)}, log scale from 10 to 20k` : 'No review counts on cards (neutral 0.5)' },
    { key: 'ads', label: 'Ad pressure', value: ads, detail: `${Math.round(s.adShare * 100)}% of sampled results are ads (×2, capped at 1)` },
    { key: 'concentration', label: 'Shop dominance', value: conc, detail: `Herfindahl index ${s.shopConcentration.toFixed(3)} across ${s.distinctShops} shops (×5, capped at 1)` },
  ];
  const score = 100 * (0.45 * supply + 0.35 * depth + 0.1 * ads + 0.1 * conc);
  return { score: Math.round(score), components };
}

/** Demand signal 0–1 from Etsy's own badges and autocomplete presence. */
export function demandSignal(s: KeywordStats, inAutocomplete: boolean): Component[] {
  const badge = clamp((s.bestsellerShare + s.popularNowShare) * 2.5);
  return [
    { key: 'badges', label: 'Etsy demand badges', value: badge, detail: `${Math.round(s.bestsellerShare * 100)}% "Bestseller" + ${Math.round(s.popularNowShare * 100)}% "Popular now" in the sample (×2.5, capped at 1)` },
    { key: 'autocomplete', label: 'Etsy autocomplete', value: inAutocomplete ? 1 : 0, detail: inAutocomplete ? 'Etsy suggested this phrase in the search box while you browsed' : 'Not yet seen as an Etsy autocomplete suggestion' },
  ];
}

export function trendSignal(snaps: KeywordSnapshot[]): Component {
  const pts = snaps
    .filter((s) => s.stats.sampleSize > 0)
    .map((s) => ({ x: s.ts / (30 * DAY), y: s.stats.bestsellerShare + s.stats.popularNowShare }));
  const sl = pts.length >= 2 && (snaps[snaps.length - 1].ts - snaps[0].ts) >= 2 * DAY ? slope(pts) : undefined;
  if (sl === undefined) {
    return { key: 'trend', label: 'Trend (your history)', value: 0.5, detail: 'You need at least two checks two or more days apart. Shown as neutral 0.5.' };
  }
  const v = clamp(0.5 + sl * 2.5);
  return { key: 'trend', label: 'Trend (your history)', value: v, detail: `Demand-badge share changes by ${(sl * 100).toFixed(1)} points per 30 days across ${pts.length} checks` };
}

export function specificity(term: string): Component {
  const n = words(term).length;
  const v = n <= 1 ? 0.2 : n === 2 ? 0.5 : n === 3 ? 0.8 : 1;
  return { key: 'specificity', label: 'Specificity', value: v, detail: `${n} word${n === 1 ? '' : 's'}. Long-tail phrases usually match buyer intent more closely.` };
}

export function dataQuality(s: KeywordStats | undefined, snapCount: number): { factor: number; notes: string[] } {
  const notes: string[] = [];
  if (!s) return { factor: 0.5, notes: ['No search captured yet'] };
  let f = 1;
  if (s.sampleSize < 20) { f *= 0.7; notes.push(`Small sample (${s.sampleSize} results)`); }
  else if (s.sampleSize < 40) { f *= 0.85; notes.push(`Partial sample (${s.sampleSize} results)`); }
  if (!isNum(s.resultCount)) { f *= 0.9; notes.push('Result count not found on page'); }
  if (snapCount < 2) notes.push('Only one check, so there is no trend data');
  if (!notes.length) notes.push('Good data coverage');
  return { factor: f, notes };
}

export interface Opportunity {
  score: number;
  difficulty: Difficulty;
  parts: (Component & { weight: number })[];
  quality: { factor: number; notes: string[] };
  formula: string;
}

export function opportunityScore(
  term: string,
  s: KeywordStats,
  snaps: KeywordSnapshot[],
  inAutocomplete: boolean,
  w: ScoringWeights,
): Opportunity {
  const difficulty = keywordDifficulty(s);
  const dem = demandSignal(s, inAutocomplete);
  const demand = 0.6 * dem[0].value + 0.4 * dem[1].value;
  const trend = trendSignal(snaps);
  const spec = specificity(term);
  const parts = [
    { key: 'demand', label: 'Demand signal', value: demand, detail: `0.6 × badges ${dem[0].value.toFixed(2)} + 0.4 × autocomplete ${dem[1].value}`, weight: w.demand },
    { key: 'competition', label: 'Low competition', value: 1 - difficulty.score / 100, detail: `1 − difficulty ${difficulty.score}/100`, weight: w.competition },
    { ...trend, weight: w.trend },
    { ...spec, weight: w.specificity },
  ];
  const totalW = parts.reduce((a, p) => a + p.weight, 0) || 1;
  const raw = parts.reduce((a, p) => a + p.value * p.weight, 0) / totalW;
  const quality = dataQuality(s, snaps.length);
  return {
    score: Math.round(raw * quality.factor * 100),
    difficulty,
    parts,
    quality,
    formula: 'Opportunity = 100 × data-quality × Σ(weight × component) ÷ Σ weights',
  };
}

/* ---------- suggestions ---------- */

export const BUYER_INTENT = [
  'personalized', 'personalised', 'custom', 'customized', 'gift', 'gifts', 'for her', 'for him', 'for mom', 'for dad',
  'for women', 'for men', 'for kids', 'set', 'bundle', 'handmade', 'name', 'monogram', 'engraved', 'printable',
  'instant download', 'wedding', 'bridesmaid', 'birthday', 'anniversary', 'baby shower', 'teacher', 'unique',
];

export const SEASONAL = [
  'christmas', 'xmas', 'holiday', 'halloween', 'thanksgiving', 'valentine', 'valentines', 'easter', 'mothers day',
  "mother's day", 'fathers day', "father's day", 'back to school', 'graduation', 'summer', 'winter', 'spring',
  'autumn', 'fall', 'new year', 'black friday', 'st patricks', 'hanukkah', 'diwali', 'ramadan', 'eid', 'lunar new year',
];

export interface Suggestion {
  phrase: string;
  docs: number;
  share: number;
  groups: ('broad' | 'long-tail' | 'buyer-intent' | 'seasonal' | 'autocomplete')[];
}

export function suggestions(term: string, titles: string[], autocomplete: string[]): Suggestion[] {
  const termNorm = words(term).join(' ');
  const freq = phraseFrequencies(titles, Math.max(2, Math.ceil(titles.length * 0.04)));
  const out = new Map<string, Suggestion>();
  const classify = (p: string): Suggestion['groups'] => {
    const g: Suggestion['groups'] = [];
    const n = p.split(' ').length;
    g.push(n >= 3 ? 'long-tail' : 'broad');
    const padded = ` ${p} `;
    if (BUYER_INTENT.some((b) => padded.includes(` ${b} `))) g.push('buyer-intent');
    if (SEASONAL.some((b) => padded.includes(` ${b} `))) g.push('seasonal');
    return g;
  };
  for (const f of freq) {
    if (f.phrase === termNorm) continue;
    out.set(f.phrase, { phrase: f.phrase, docs: f.docs, share: titles.length ? f.docs / titles.length : 0, groups: classify(f.phrase) });
  }
  for (const a of autocomplete) {
    const p = words(a).join(' ');
    if (!p || p === termNorm) continue;
    const ex = out.get(p);
    if (ex) ex.groups.push('autocomplete');
    else out.set(p, { phrase: p, docs: 0, share: 0, groups: [...classify(p), 'autocomplete'] });
  }
  return [...out.values()].sort((a, b) => b.docs - a.docs || a.phrase.localeCompare(b.phrase)).slice(0, 150);
}
