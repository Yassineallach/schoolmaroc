import { describe, expect, it } from 'vitest';
import { herfindahl, histogram, jaccard, median, percentileRank, poissonInterval, quantile, slope } from '../../src/core/stats';
import { fleschReadingEase, phraseFrequencies, titlePhrases, words } from '../../src/core/text';
import { calibrationRatio, estimateListingSales, observedShopVelocity, periods, revenue } from '../../src/core/sales';
import { computeKeywordStats, keywordDifficulty, opportunityScore, specificity, suggestions } from '../../src/core/keywords';
import { analyseTags, analyseTitle, auditListing } from '../../src/core/seo';
import { diffShopSnapshots, keywordOverlap, termGaps } from '../../src/core/competitors';
import { availablePeriods, easterSunday, movements, nthWeekday, shoppingEvents, upcomingEvents } from '../../src/core/trends';
import { convert } from '../../src/shared/format';
import type { ListingCard, ListingRecord, SearchExtraction } from '../../src/shared/types';

const DAY = 86_400_000;

describe('stats', () => {
  it('quantiles match PERCENTILE.INC', () => {
    expect(quantile([1, 2, 3, 4], 0.25)).toBeCloseTo(1.75);
    expect(median([5, 1, 3])).toBe(3);
    expect(quantile([], 0.5)).toBeUndefined();
  });
  it('herfindahl and jaccard', () => {
    expect(herfindahl(['a', 'a', 'a', 'a'])).toBe(1);
    expect(herfindahl(['a', 'b', 'c', 'd'])).toBeCloseTo(0.25);
    expect(jaccard(['a', 'b'], ['b', 'c'])).toBeCloseTo(1 / 3);
  });
  it('poisson interval brackets the count', () => {
    const [lo, hi] = poissonInterval(100);
    expect(lo).toBeLessThan(100);
    expect(hi).toBeGreaterThan(100);
    expect(lo).toBeCloseTo(100 - 16.45, 1);
  });
  it('slope, histogram, percentile rank', () => {
    expect(slope([{ x: 0, y: 1 }, { x: 1, y: 3 }, { x: 2, y: 5 }])).toBeCloseTo(2);
    const bins = histogram([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    expect(bins.reduce((a, b) => a + b.count, 0)).toBe(10);
    expect(percentileRank([1, 2, 3, 4], 4)).toBeCloseTo(87.5);
  });
});

describe('text', () => {
  it('splits titles into phrases and words', () => {
    expect(titlePhrases('Custom Mug, Gift for Mom | Coffee Cup')).toEqual(['custom mug', 'gift for mom', 'coffee cup']);
    expect(words("Mom's Café Mug!")).toEqual(["mom's", 'cafe', 'mug']);
  });
  it('counts phrases by document, within title segments', () => {
    const p = phraseFrequencies(['Custom Mug, Gift for Mom', 'Custom Mug, Coffee', 'Gift for Mom, Tea Cup'], 2);
    const names = p.map((x) => x.phrase);
    expect(names).toContain('custom mug');
    expect(names).toContain('gift for mom');
    expect(names).not.toContain('mug gift');
  });
  it('flesch reading ease is higher for simple text', () => {
    const simple = fleschReadingEase('The cat sat on the mat. It was a good cat. The mat was red and soft.')!;
    const hard = fleschReadingEase('Notwithstanding considerable organisational complexity, interdepartmental communication necessitates comprehensive documentation procedures.')!;
    expect(simple).toBeGreaterThan(hard);
  });
});

const baseListing = (o: Partial<ListingRecord> = {}): ListingRecord => ({
  listingId: '1', title: 't', url: 'u', category: [], variations: [], relatedTerms: [], imageAlts: [], badges: [], detailed: true,
  firstSeen: 0, lastSeen: 0, searchQueries: [], ...o,
});
const opts = { fallbackSalesPerReview: 4, minShopReviewsForCalibration: 20, peerRatios: [] as number[], now: Date.UTC(2026, 10, 27) };

describe('sales estimation', () => {
  it('calibrates on the shop when it has enough reviews', () => {
    expect(calibrationRatio(1000, 200, opts)).toEqual({ k: 5, source: 'shop' });
    expect(calibrationRatio(1000, 5, opts).source).toBe('default');
    expect(calibrationRatio(1000, 5, { ...opts, peerRatios: [3, 4, 5] })).toEqual({ k: 4, source: 'peer-median' });
  });
  it('needs a listing review count', () => {
    const e = estimateListingSales(baseListing(), [], undefined, [], opts);
    expect(e.available).toBe(false);
    expect(e.reason).toMatch(/review count/);
  });
  it('estimates lifetime sales with a band', () => {
    const e = estimateListingSales(baseListing({ listingReviewCount: 100, shopSales: 5000, shopReviewCount: 1000 }), [], undefined, [], opts);
    expect(e.k).toBe(5);
    expect(e.lifetime!.mid).toBe(500);
    expect(e.lifetime!.low).toBeLessThan(500);
    expect(e.lifetime!.high).toBeGreaterThan(500);
    expect(e.velocityMethod).toBe('none');
  });
  it('prefers review-delta velocity from snapshots', () => {
    const now = opts.now;
    const snaps = [{ listingId: '1', ts: now - 10 * DAY, listingReviewCount: 90 }, { listingId: '1', ts: now, listingReviewCount: 100 }];
    const e = estimateListingSales(baseListing({ listingReviewCount: 100, shopSales: 5000, shopReviewCount: 1000 }), snaps, undefined, [], opts);
    expect(e.velocityMethod).toBe('review-delta');
    expect(e.perDay!.mid).toBeCloseTo(5); // 10 reviews × 5 ÷ 10 days
    expect(e.grade).toBe('A');
  });
  it('falls back to shop-delta then shop-lifetime', () => {
    const now = opts.now;
    const l = baseListing({ listingReviewCount: 100, shopSales: 5000, shopReviewCount: 1000 });
    const shopSnaps = [{ shopName: 's', ts: now - 20 * DAY, sales: 4800, listings: [] }, { shopName: 's', ts: now, sales: 5000, listings: [] }];
    const e = estimateListingSales(l, [], undefined, shopSnaps, opts);
    expect(e.velocityMethod).toBe('shop-delta');
    expect(e.perDay!.mid).toBeCloseTo((200 / 20) * 0.1);
    const shop = { shopName: 's', url: '', sections: [], tracked: false, firstSeen: 0, lastSeen: 0, onEtsySince: 2020 };
    const e2 = estimateListingSales(l, [], shop, [], opts);
    expect(e2.velocityMethod).toBe('shop-lifetime');
  });
  it('periods and revenue scale correctly', () => {
    const p = periods({ low: 1, mid: 2, high: 3 });
    expect(p.week.mid).toBe(14);
    expect(revenue({ low: 1, mid: 2, high: 3 }, 10, 20).mid).toBe(16);
  });
  it('observed shop velocity is a plain difference', () => {
    const v = observedShopVelocity([{ shopName: 's', ts: 0, sales: 100, listings: [] }, { shopName: 's', ts: 4 * DAY, sales: 120, listings: [] }]);
    expect(v!.perDay).toBe(5);
  });
});

const card = (i: number, o: Partial<ListingCard> = {}): ListingCard => ({ listingId: String(i), title: `Custom name mug gift ${i}`, url: '', isAd: false, badges: [], freeShipping: false, position: i, price: 10 + i, shopName: `shop${i % 5}`, cardReviewCount: 100, ...o });
const search = (cards: ListingCard[], resultCount = 5000): SearchExtraction => ({ type: 'search', url: '', query: 'custom name mug', resultCount, cards, autocomplete: [], capturedAt: 0 });

describe('keywords', () => {
  const cards = Array.from({ length: 40 }, (_, i) => card(i, { isAd: i < 4, badges: i < 8 ? ['Bestseller'] : [] }));
  const st = computeKeywordStats(search(cards));
  it('computes sample stats', () => {
    expect(st.sampleSize).toBe(40);
    expect(st.adShare).toBeCloseTo(0.1);
    expect(st.bestsellerShare).toBeCloseTo(0.2);
    expect(st.distinctShops).toBe(5);
    expect(st.medianPrice).toBeCloseTo(29.5);
  });
  it('difficulty grows with supply', () => {
    const small = keywordDifficulty(computeKeywordStats(search(cards, 200))).score;
    const big = keywordDifficulty(computeKeywordStats(search(cards, 400000))).score;
    expect(big).toBeGreaterThan(small);
  });
  it('opportunity respects weights and stays in range', () => {
    const o = opportunityScore('custom name mug', st, [], true, { demand: 50, competition: 50, trend: 0, specificity: 0 });
    expect(o.score).toBeGreaterThanOrEqual(0);
    expect(o.score).toBeLessThanOrEqual(100);
    const onlySpec = opportunityScore('custom name mug', st, [], false, { demand: 0, competition: 0, trend: 0, specificity: 1 });
    expect(onlySpec.score).toBe(Math.round(specificity('custom name mug').value * onlySpec.quality.factor * 100));
  });
  it('suggestions are lexical and classified', () => {
    const s = suggestions('mug', ['Personalized Mug, Gift for Mom', 'Personalized Mug, Christmas Gift', 'Christmas Gift, Mug'], ['mug for dad']);
    const p = s.map((x) => x.phrase);
    expect(p).toContain('personalized mug');
    expect(s.find((x) => x.phrase === 'christmas gift')!.groups).toContain('seasonal');
    expect(s.find((x) => x.phrase === 'personalized mug')!.groups).toContain('buyer-intent');
    expect(s.find((x) => x.phrase === 'mug for dad')!.groups).toContain('autocomplete');
  });
});

describe('seo', () => {
  it('flags title problems', () => {
    const t = analyseTitle('Mug Mug Gift, COFFEE MUG FOR DAD & MOM & KIDS', ['coffee mug']);
    expect(t.duplicateWords).toContain('mug');
    expect(t.allCapsWords.length).toBeGreaterThan(2);
    expect(t.keywordPositions[0].index).toBeGreaterThan(0);
  });
  it('analyses tags', () => {
    const g = analyseTags(['mug', 'Mug', 'this tag is far too long for etsy', 'gift for dad'], 'Coffee mug', ['gift for dad', 'tea cup']);
    expect(g.duplicateTags).toEqual(['mug']);
    expect(g.tags[2].tooLong).toBe(true);
    expect(g.coveredKeywords).toEqual(['gift for dad']);
    expect(g.missingKeywords).toEqual(['tea cup']);
    expect(g.emptySlots).toBe(9);
  });
  it('audit produces deterministic rule results and a score', () => {
    const a = auditListing({ title: 'Personalized coffee mug, gift for dad', tags: ['coffee mug'], description: '', keywords: ['personalized coffee mug'], imageCount: 2 });
    const ids = a.results.map((r) => `${r.id}:${r.severity}`);
    expect(ids).toContain('T3:pass');
    expect(ids).toContain('G1:warning');
    expect(ids).toContain('I1:warning');
    expect(a.score).toBeGreaterThanOrEqual(0);
    expect(a.score).toBeLessThanOrEqual(100);
    expect(auditListing({ title: 'Personalized coffee mug, gift for dad', tags: ['coffee mug'], description: '', keywords: ['personalized coffee mug'], imageCount: 2 }).score).toBe(a.score);
  });
});

describe('competitors', () => {
  it('diffs shop snapshots', () => {
    const d = diffShopSnapshots(
      { shopName: 's', ts: 0, sales: 10, listings: [{ id: '1', price: 10, title: 'a' }, { id: '2', price: 5, title: 'b' }] },
      { shopName: 's', ts: 2 * DAY, sales: 15, listings: [{ id: '1', price: 12, title: 'a' }, { id: '3', price: 7, title: 'c' }] },
    );
    expect(d.newListings.map((x) => x.id)).toEqual(['3']);
    expect(d.removedListings.map((x) => x.id)).toEqual(['2']);
    expect(d.priceChanges).toEqual([{ id: '1', title: 'a', before: 10, after: 12 }]);
    expect(d.salesDelta).toBe(5);
    expect(d.days).toBe(2);
  });
  it('overlap and gaps', () => {
    const m = new Map([
      ['A', [baseListing({ title: 'Custom mug', relatedTerms: ['name mug'] })]],
      ['B', [baseListing({ title: 'Custom cup', relatedTerms: ['name mug'] })]],
    ]);
    const o = keywordOverlap(m);
    expect(o.matrix[0][1]).toBeGreaterThan(0);
    expect(termGaps(new Set(['a']), [new Set(['a', 'b']), new Set(['b', 'c'])])[0]).toEqual({ term: 'b', shops: 2 });
  });
});

describe('trends & calendar', () => {
  it('computes Easter correctly', () => {
    expect(easterSunday(2024).toISOString().slice(0, 10)).toBe('2024-03-31');
    expect(easterSunday(2025).toISOString().slice(0, 10)).toBe('2025-04-20');
    expect(easterSunday(2026).toISOString().slice(0, 10)).toBe('2026-04-05');
  });
  it('computes weekday-based holidays', () => {
    expect(nthWeekday(2026, 4, 0, 2).toISOString().slice(0, 10)).toBe('2026-05-10'); // US Mother's Day
    expect(nthWeekday(2026, 10, 4, 4).toISOString().slice(0, 10)).toBe('2026-11-26'); // Thanksgiving
    const bf = shoppingEvents(2026, 'US').find((e) => e.key === 'blackfriday')!;
    expect(bf.date.toISOString().slice(0, 10)).toBe('2026-11-27');
    const uk = shoppingEvents(2026, 'UK').find((e) => e.key === 'mothers')!;
    expect(uk.date.toISOString().slice(0, 10)).toBe('2026-03-15');
  });
  it('upcoming events are in the future and sorted', () => {
    const ev = upcomingEvents(new Date(Date.UTC(2026, 10, 27)), 'US');
    expect(ev[0].daysUntil).toBeGreaterThanOrEqual(0);
    for (let i = 1; i < ev.length; i++) expect(ev[i].daysUntil).toBeGreaterThanOrEqual(ev[i - 1].daysUntil);
  });
  it('only offers periods covered by data', () => {
    const now = Date.UTC(2026, 10, 27);
    const p = availablePeriods(now - 40 * DAY, now);
    expect(p.find((x) => x.key === '30d')!.available).toBe(true);
    expect(p.find((x) => x.key === '90d')!.available).toBe(false);
    expect(availablePeriods(undefined, now).every((x) => !x.available)).toBe(true);
  });
  it('movements classify direction', () => {
    const mk = (ts: number, share: number) => ({ term: 'x', ts, stats: { ...computeKeywordStats(search([card(1)])), bestsellerShare: share, popularNowShare: 0 } });
    const m = movements(new Map([['x', [mk(0, 0.1), mk(30 * DAY, 0.3)]]]));
    expect(m[0].direction).toBe('rising');
  });
});

describe('currency', () => {
  it('converts with user rates only', () => {
    const s = { displayCurrency: 'USD', fxRates: { EUR: 0.9 } };
    expect(convert(9, 'EUR', s)).toEqual({ value: 10, currency: 'USD', converted: true });
    expect(convert(9, 'GBP', s)).toEqual({ value: 9, currency: 'GBP', converted: false });
  });
});
