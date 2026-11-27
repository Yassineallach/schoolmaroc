/** Competitor engine: snapshot diffs, shop comparison, keyword overlap. */
import { jaccard, median, nums, quantile } from './stats';
import { contentWords, normalise, stem } from './text';
import type { ChangeEntry, ListingRecord, ListingSnapshot, ShopRecord, ShopSnapshot } from '../shared/types';

export interface ShopDiff {
  newListings: { id: string; title: string; price?: number }[];
  removedListings: { id: string; title: string; price?: number }[];
  priceChanges: { id: string; title: string; before?: number; after?: number }[];
  titleChanges: { id: string; before: string; after: string }[];
  salesDelta?: number;
  reviewDelta?: number;
  listingCountDelta?: number;
  days: number;
  /** removed/new are only reliable if both snapshots captured the same page scope */
  comparable: boolean;
}

export function diffShopSnapshots(prev: ShopSnapshot, next: ShopSnapshot): ShopDiff {
  const a = new Map(prev.listings.map((l) => [l.id, l]));
  const b = new Map(next.listings.map((l) => [l.id, l]));
  const d = (x?: number, y?: number) => (x !== undefined && y !== undefined ? y - x : undefined);
  const out: ShopDiff = {
    newListings: [],
    removedListings: [],
    priceChanges: [],
    titleChanges: [],
    salesDelta: d(prev.sales, next.sales),
    reviewDelta: d(prev.reviewCount, next.reviewCount),
    listingCountDelta: d(prev.totalListings, next.totalListings),
    days: (next.ts - prev.ts) / 86_400_000,
    comparable: prev.listings.length > 0 && next.listings.length > 0,
  };
  for (const [id, l] of b) {
    const old = a.get(id);
    if (!old) out.newListings.push(l);
    else {
      if (old.price !== undefined && l.price !== undefined && Math.abs(old.price - l.price) > 0.004) out.priceChanges.push({ id, title: l.title, before: old.price, after: l.price });
      if (old.title && l.title && old.title !== l.title) out.titleChanges.push({ id, before: old.title, after: l.title });
    }
  }
  for (const [id, l] of a) if (!b.has(id)) out.removedListings.push(l);
  return out;
}

export function shopDiffToChanges(shopName: string, diff: ShopDiff, ts: number): ChangeEntry[] {
  const ch: ChangeEntry[] = [];
  const push = (field: string, before?: unknown, after?: unknown) =>
    ch.push({ entity: 'shop', key: shopName, ts, field, before: before === undefined ? undefined : String(before), after: after === undefined ? undefined : String(after) });
  if (diff.salesDelta) push('sales', undefined, `${diff.salesDelta > 0 ? '+' : ''}${diff.salesDelta}`);
  if (diff.reviewDelta) push('reviews', undefined, `${diff.reviewDelta > 0 ? '+' : ''}${diff.reviewDelta}`);
  if (diff.listingCountDelta) push('listing count', undefined, `${diff.listingCountDelta > 0 ? '+' : ''}${diff.listingCountDelta}`);
  for (const l of diff.newListings) push('new listing', undefined, `${l.title} (#${l.id})`);
  if (diff.comparable) for (const l of diff.removedListings) push('no longer visible', `${l.title} (#${l.id})`, undefined);
  for (const p of diff.priceChanges) push(`price #${p.id}`, p.before, p.after);
  for (const t of diff.titleChanges) push(`title #${t.id}`, t.before, t.after);
  return ch;
}

const FIELDS: (keyof ListingSnapshot)[] = ['price', 'title', 'termsHash', 'imageCount', 'listingReviewCount', 'favourites', 'shopSales'];

export function diffListingSnapshots(listingId: string, prev: ListingSnapshot, next: ListingSnapshot): ChangeEntry[] {
  const out: ChangeEntry[] = [];
  for (const f of FIELDS) {
    const a = prev[f];
    const b = next[f];
    if (a === undefined || b === undefined || a === b) continue;
    const label = f === 'termsHash' ? 'related terms / tags' : f === 'listingReviewCount' ? 'listing reviews' : f === 'shopSales' ? 'shop sales' : String(f);
    out.push({ entity: 'listing', key: listingId, ts: next.ts, field: label, before: f === 'termsHash' ? 'previous set' : String(a), after: f === 'termsHash' ? 'changed' : String(b) });
  }
  return out;
}

export interface ShopComparisonRow {
  shopName: string;
  sales?: number;
  reviewCount?: number;
  rating?: number;
  totalListings?: number;
  onEtsySince?: number;
  salesPerReview?: number;
  salesPerListing?: number;
  medianPrice?: number;
  p25Price?: number;
  p75Price?: number;
  observedListings: number;
  categories: number;
  topWords: string[];
  newListings30d: number;
}

export function compareShops(
  shops: ShopRecord[],
  listingsByShop: Map<string, ListingRecord[]>,
  latestSnaps: Map<string, ShopSnapshot[]>,
): ShopComparisonRow[] {
  const now = Date.now();
  return shops.map((s) => {
    const ls = listingsByShop.get(s.shopName) ?? [];
    const prices = nums(ls.map((l) => l.price));
    const cats = new Set(ls.map((l) => l.category.join('>')).filter(Boolean));
    const snaps = latestSnaps.get(s.shopName) ?? [];
    const seenIds = new Set<string>();
    let newCount = 0;
    for (const snap of [...snaps].sort((a, b) => a.ts - b.ts)) {
      for (const l of snap.listings) {
        if (!seenIds.has(l.id) && seenIds.size > 0 && now - snap.ts < 30 * 86_400_000) newCount++;
        seenIds.add(l.id);
      }
    }
    return {
      shopName: s.shopName,
      sales: s.sales,
      reviewCount: s.reviewCount,
      rating: s.rating,
      totalListings: s.totalListings,
      onEtsySince: s.onEtsySince,
      salesPerReview: s.sales && s.reviewCount ? s.sales / s.reviewCount : undefined,
      salesPerListing: s.sales && s.totalListings ? s.sales / s.totalListings : undefined,
      medianPrice: median(prices),
      p25Price: quantile(prices, 0.25),
      p75Price: quantile(prices, 0.75),
      observedListings: ls.length,
      categories: cats.size,
      topWords: topTerms(ls.map((l) => [l.title, ...l.relatedTerms].join(' ')), 8),
      newListings30d: newCount,
    };
  });
}

export function topTerms(docs: string[], n: number): string[] {
  const c = new Map<string, number>();
  for (const d of docs) for (const w of new Set(contentWords(d).map(stem))) c.set(w, (c.get(w) ?? 0) + 1);
  return [...c.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, n).map(([w]) => w);
}

/** Vocabulary per shop: normalised related terms/tags plus title phrases. */
export function shopVocabulary(listings: ListingRecord[]): Set<string> {
  const v = new Set<string>();
  for (const l of listings) {
    for (const t of l.relatedTerms) v.add(normalise(t));
    for (const w of contentWords(l.title)) v.add(stem(w));
  }
  return v;
}

export interface OverlapMatrix {
  shops: string[];
  matrix: number[][];
  shared: Map<string, string[]>;
}

export function keywordOverlap(listingsByShop: Map<string, ListingRecord[]>): OverlapMatrix {
  const shops = [...listingsByShop.keys()];
  const vocab = shops.map((s) => shopVocabulary(listingsByShop.get(s)!));
  const matrix = shops.map((_, i) => shops.map((__, j) => (i === j ? 1 : jaccard(vocab[i], vocab[j]))));
  const shared = new Map<string, string[]>();
  for (let i = 0; i < shops.length; i++)
    for (let j = i + 1; j < shops.length; j++) {
      shared.set(`${shops[i]}|${shops[j]}`, [...vocab[i]].filter((x) => vocab[j].has(x)).slice(0, 40));
    }
  return { shops, matrix, shared };
}

/** Terms competitors use that the user's own vocabulary lacks, ranked by number of competitors using them. */
export function termGaps(mine: Set<string>, competitors: Set<string>[]): { term: string; shops: number }[] {
  const c = new Map<string, number>();
  for (const v of competitors) for (const t of v) if (!mine.has(t)) c.set(t, (c.get(t) ?? 0) + 1);
  return [...c.entries()].map(([term, shops]) => ({ term, shops })).sort((a, b) => b.shops - a.shops || a.term.localeCompare(b.term));
}
