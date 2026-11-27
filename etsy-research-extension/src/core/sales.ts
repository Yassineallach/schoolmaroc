/**
 * Sales and revenue estimation (deterministic, documented).
 *
 * Etsy publicly shows: a shop's lifetime sales counter, shop review count,
 * listing review count and price. It does NOT show per-listing sales.
 *
 * 1. Calibration k = shopSales / shopReviews (this shop's own sales per review).
 *    Falls back to the median k of other shops the user observed, then to a
 *    user-set default, when the shop has too few reviews.
 * 2. Listing lifetime sales ≈ listingReviews × k, with a 90% Poisson band on
 *    the review count.
 * 3. Sales velocity, best available method first:
 *    a. review-delta: Δ listing reviews between the user's snapshots × k
 *    b. shop-delta:   Δ shop sales counter between snapshots × listing review share
 *    c. shop-lifetime: shop sales / shop age × listing review share
 *    d. listed-on:    listing lifetime sales / days since "Listed on" (upper bound,
 *       because Etsy's date is the latest renewal, not the original creation)
 */
import { DAY, isNum, median, poissonInterval } from './stats';
import type { ListingRecord, ListingSnapshot, ShopRecord, ShopSnapshot } from '../shared/types';

export type VelocityMethod = 'review-delta' | 'shop-delta' | 'shop-lifetime' | 'listed-on' | 'none';
export type Grade = 'A' | 'B' | 'C' | 'D';

export interface Range {
  low: number;
  mid: number;
  high: number;
}

export interface SalesEstimate {
  available: boolean;
  reason?: string;
  k?: number;
  kSource?: 'shop' | 'peer-median' | 'default';
  lifetime?: Range;
  perDay?: Range;
  velocityMethod: VelocityMethod;
  velocityNote?: string;
  grade: Grade;
  gradeReasons: string[];
  steps: string[];
}

export interface EstimateOptions {
  fallbackSalesPerReview: number;
  minShopReviewsForCalibration: number;
  peerRatios: number[];
  now?: number;
}

const r = (n: number) => Math.round(n * 100) / 100;

function shopAgeDays(shop: ShopRecord | undefined, now: number): number | undefined {
  if (!shop?.onEtsySince) return undefined;
  // "On Etsy since 2019" is a year; assume mid-year to halve the worst-case error.
  const start = Date.UTC(shop.onEtsySince, 6, 1);
  const d = (now - start) / DAY;
  return d > 30 ? d : undefined;
}

export function calibrationRatio(
  shopSales: number | undefined,
  shopReviews: number | undefined,
  opts: EstimateOptions,
): { k: number; source: 'shop' | 'peer-median' | 'default' } {
  if (isNum(shopSales) && isNum(shopReviews) && shopReviews >= opts.minShopReviewsForCalibration && shopSales >= shopReviews) {
    return { k: shopSales / shopReviews, source: 'shop' };
  }
  const peer = median(opts.peerRatios.filter((x) => x >= 1 && x < 200));
  if (peer !== undefined && opts.peerRatios.length >= 3) return { k: peer, source: 'peer-median' };
  return { k: opts.fallbackSalesPerReview, source: 'default' };
}

/** Sales-per-review ratios of every observed shop with enough data (for peer calibration). */
export function peerRatiosFrom(shops: { sales?: number; reviewCount?: number }[], minReviews: number): number[] {
  return shops
    .filter((s) => isNum(s.sales) && isNum(s.reviewCount) && s.reviewCount! >= minReviews && s.sales! >= s.reviewCount!)
    .map((s) => s.sales! / s.reviewCount!);
}

function pairDelta<T extends { ts: number }>(snaps: T[], pick: (s: T) => number | undefined, minDays = 3) {
  const valid = snaps.filter((s) => isNum(pick(s))).sort((a, b) => a.ts - b.ts);
  if (valid.length < 2) return undefined;
  const first = valid[0];
  const last = valid[valid.length - 1];
  const days = (last.ts - first.ts) / DAY;
  const delta = pick(last)! - pick(first)!;
  if (days < minDays || delta < 0) return undefined;
  return { delta, days, from: first.ts, to: last.ts };
}

export function estimateListingSales(
  listing: ListingRecord,
  snaps: ListingSnapshot[],
  shop: ShopRecord | undefined,
  shopSnaps: ShopSnapshot[],
  opts: EstimateOptions,
): SalesEstimate {
  const now = opts.now ?? Date.now();
  const steps: string[] = [];
  const gradeReasons: string[] = [];
  const R = listing.listingReviewCount;
  const shopSales = listing.shopSales ?? shop?.sales;
  const shopReviews = listing.shopReviewCount ?? shop?.reviewCount;

  if (!isNum(R)) {
    return {
      available: false,
      reason: 'The listing review count has not been captured. Open the listing page to collect it.',
      velocityMethod: 'none',
      grade: 'D',
      gradeReasons: ['No listing review count'],
      steps,
    };
  }

  const { k, source } = calibrationRatio(shopSales, shopReviews, opts);
  if (source === 'shop') steps.push(`k = shop sales ${shopSales} ÷ shop reviews ${shopReviews} = ${r(k)} sales per review`);
  else if (source === 'peer-median') steps.push(`k = ${r(k)} (median of ${opts.peerRatios.length} other shops you observed; this shop has too few reviews)`);
  else steps.push(`k = ${r(k)} (your default from Settings; not enough shop data to calibrate)`);

  const [rLo, rHi] = poissonInterval(R);
  const widen = source === 'shop' ? [1, 1] : source === 'peer-median' ? [0.7, 1.4] : [0.5, 2];
  const lifetime: Range = { low: rLo * k * widen[0], mid: R * k, high: rHi * k * widen[1] };
  steps.push(`Lifetime ≈ listing reviews ${R} × k = ${Math.round(lifetime.mid)} (90% band ${Math.round(lifetime.low)}–${Math.round(lifetime.high)})`);

  let perDay: Range | undefined;
  let method: VelocityMethod = 'none';
  let note: string | undefined;
  const share = isNum(shopReviews) && shopReviews > 0 ? Math.min(1, R / shopReviews) : undefined;

  const rd = pairDelta(snaps, (s) => s.listingReviewCount);
  const sd = pairDelta(shopSnaps, (s) => s.sales);
  const shopAge = shopAgeDays(shop, now);

  if (rd && rd.delta > 0) {
    const [lo, hi] = poissonInterval(rd.delta);
    perDay = { low: (lo * k * widen[0]) / rd.days, mid: (rd.delta * k) / rd.days, high: (hi * k * widen[1]) / rd.days };
    method = 'review-delta';
    note = `${rd.delta} new reviews observed over ${r(rd.days)} days`;
  } else if (sd && share !== undefined) {
    const daily = sd.delta / sd.days;
    perDay = { low: daily * share * 0.5, mid: daily * share, high: daily * Math.min(1, share * 2) };
    method = 'shop-delta';
    note = `Shop counter grew by ${sd.delta} over ${r(sd.days)} days (observed); listing share of reviews ${r(share * 100)}%`;
  } else if (isNum(shopSales) && shopAge && share !== undefined) {
    const daily = shopSales / shopAge;
    perDay = { low: daily * share * 0.5, mid: daily * share, high: daily * Math.min(1, share * 2) };
    method = 'shop-lifetime';
    note = `Shop lifetime average ${r(daily)} sales/day × listing review share ${r(share * 100)}%`;
  } else if (listing.listedOn && now - listing.listedOn > 7 * DAY) {
    const days = (now - listing.listedOn) / DAY;
    perDay = { low: lifetime.low / days / 3, mid: lifetime.mid / days, high: lifetime.high / days };
    method = 'listed-on';
    note = `Lifetime estimate ÷ ${Math.round(days)} days since "Listed on". Treat this as an upper bound: Etsy's date is the latest renewal.`;
  }
  if (note) steps.push(`Velocity (${method}): ${note}`);

  let score = 0;
  if (R >= 50) { score += 2; gradeReasons.push(`${R} listing reviews (good sample)`); }
  else if (R >= 10) { score += 1; gradeReasons.push(`${R} listing reviews (small sample)`); }
  else gradeReasons.push(`Only ${R} listing reviews`);
  if (source === 'shop') { score += 1; gradeReasons.push('Calibrated on this shop'); }
  else gradeReasons.push('Not calibrated on this shop');
  if (method === 'review-delta' || method === 'shop-delta') { score += 2; gradeReasons.push('Velocity from your own snapshots'); }
  else if (method === 'shop-lifetime') { score += 1; gradeReasons.push('Velocity assumes steady shop sales'); }
  else gradeReasons.push(method === 'listed-on' ? 'Velocity is an upper bound' : 'No velocity data');
  // an upper-bound velocity cannot support a high-confidence estimate
  if (method === 'listed-on') score = Math.min(score, 2);
  const grade: Grade = score >= 5 ? 'A' : score >= 3 ? 'B' : score >= 2 ? 'C' : 'D';

  return { available: true, k, kSource: source, lifetime, perDay, velocityMethod: method, velocityNote: note, grade, gradeReasons, steps };
}

export interface PeriodFigures {
  day: Range;
  week: Range;
  month: Range;
  year: Range;
}

export function periods(perDay: Range): PeriodFigures {
  const m = (f: number): Range => ({ low: perDay.low * f, mid: perDay.mid * f, high: perDay.high * f });
  return { day: m(1), week: m(7), month: m(30.44), year: m(365.25) };
}

export function revenue(range: Range, price: number, discountPct: number, fx = 1): Range {
  const p = price * (1 - Math.min(100, Math.max(0, discountPct)) / 100) * fx;
  return { low: range.low * p, mid: range.mid * p, high: range.high * p };
}

/** Observed shop sales per day from counter snapshots (not an estimate). */
export function observedShopVelocity(snaps: ShopSnapshot[]) {
  const d = pairDelta(snaps, (s) => s.sales, 1);
  if (!d) return undefined;
  return { perDay: d.delta / d.days, delta: d.delta, days: d.days, from: d.from, to: d.to };
}
