/** Combines stored records with the engines. Used by the background worker, dashboard and sidebar. */
import * as repo from './storage/repo';
import { auditListing, Audit } from './seo';
import { estimateListingSales, observedShopVelocity, peerRatiosFrom, periods, PeriodFigures, revenue, SalesEstimate, Range } from './sales';
import { opportunityScore, Opportunity, suggestions, Suggestion } from './keywords';
import { diffShopSnapshots, ShopDiff } from './competitors';
import { DAY, median, nums, percentileRank, quantile } from './stats';
import { fxFactor } from '../shared/format';
import type { ChangeEntry, KeywordRecord, KeywordSnapshot, ListingRecord, ListingSnapshot, Settings, ShopRecord, ShopSnapshot } from '../shared/types';

export interface Indicator {
  key: string;
  label: string;
  value?: number;
  display: string;
  provenance: 'verified' | 'observed' | 'estimated' | 'unavailable';
  note: string;
}

export interface ListingAnalysis {
  listing: ListingRecord;
  snaps: ListingSnapshot[];
  shop?: ShopRecord;
  shopSnaps: ShopSnapshot[];
  estimate: SalesEstimate;
  periods?: PeriodFigures;
  revenue?: { day?: Range; week?: Range; month?: Range; year?: Range; lifetime?: Range; currency?: string; converted: boolean; unitPrice: number; discountPct: number };
  indicators: Indicator[];
  audit: Audit;
  changes: ChangeEntry[];
}

export async function peerRatios(settings: Settings) {
  return peerRatiosFrom(await repo.shops(), settings.minShopReviewsForCalibration);
}

export async function analyseListing(id: string, settings: Settings, overrides: { price?: number; discountPct?: number } = {}): Promise<ListingAnalysis | undefined> {
  const listing = await repo.listing(id);
  if (!listing) return undefined;
  const [snaps, shop, changes, ratios] = await Promise.all([
    repo.listingSnaps(id),
    listing.shopName ? repo.shop(listing.shopName) : Promise.resolve(undefined),
    repo.changesFor(id),
    peerRatios(settings),
  ]);
  const shopSnaps = listing.shopName ? await repo.shopSnaps(listing.shopName) : [];
  const estimate = estimateListingSales(listing, snaps, shop, shopSnaps, {
    fallbackSalesPerReview: settings.fallbackSalesPerReview,
    minShopReviewsForCalibration: settings.minShopReviewsForCalibration,
    peerRatios: ratios.filter((r) => !(shop?.sales && shop.reviewCount && Math.abs(r - shop.sales / shop.reviewCount) < 1e-9)),
  });
  const per = estimate.perDay ? periods(estimate.perDay) : undefined;
  const unitPrice = overrides.price ?? listing.price;
  const discountPct = overrides.discountPct ?? settings.defaultDiscountPct;
  let rev: ListingAnalysis['revenue'];
  if (unitPrice !== undefined && (per || estimate.lifetime)) {
    const fx = fxFactor(listing.currency, settings);
    const conv = (r: Range) => revenue(r, unitPrice, discountPct, fx.factor);
    rev = {
      day: per && conv(per.day), week: per && conv(per.week), month: per && conv(per.month), year: per && conv(per.year),
      lifetime: estimate.lifetime && conv(estimate.lifetime),
      currency: fx.currency, converted: fx.converted, unitPrice, discountPct,
    };
  }
  return {
    listing, snaps, shop, shopSnaps, estimate, periods: per, revenue: rev,
    indicators: await listingIndicators(listing, estimate),
    audit: auditListing({
      title: listing.title, tags: listing.relatedTerms, tagsAreRelatedTerms: true, description: listing.description ?? '',
      imageCount: listing.imageCount, imageAlts: listing.imageAlts, keywords: listing.searchQueries.slice(-1), category: listing.category,
    }),
    changes,
  };
}

async function listingIndicators(l: ListingRecord, est: SalesEstimate): Promise<Indicator[]> {
  const out: Indicator[] = [];
  const now = Date.now();
  if (est.k) {
    out.push({ key: 'reviewRate', label: 'Reviews per sale (shop)', value: 1 / est.k, display: `${(100 / est.k).toFixed(1)}%`, provenance: est.kSource === 'shop' ? 'verified' : 'estimated', note: est.kSource === 'shop' ? 'Shop reviews ÷ shop sales, both shown by Etsy. Applies to the whole shop, not this listing.' : 'Not enough shop data. Uses the calibration fallback.' });
  }
  out.push({ key: 'favToViews', label: 'Favourites-to-views', display: 'Not available', provenance: 'unavailable', note: 'Etsy does not show listing views publicly, so this ratio cannot be calculated honestly.' });
  out.push({ key: 'conversion', label: 'Conversion rate', display: 'Not available', provenance: 'unavailable', note: 'This needs views and sales for the listing. Etsy shows neither for other sellers.' });
  if (l.favourites !== undefined && l.listingReviewCount) {
    out.push({ key: 'favPerReview', label: 'Favourites per review', value: l.favourites / l.listingReviewCount, display: (l.favourites / l.listingReviewCount).toFixed(1), provenance: 'verified', note: 'Both counts are shown on the listing page. A high value means interest without many purchases (or a low review rate).' });
  }
  if (l.listedOn) {
    out.push({ key: 'age', label: 'Days since "Listed on"', value: (now - l.listedOn) / DAY, display: `${Math.round((now - l.listedOn) / DAY)} days`, provenance: 'verified', note: 'Etsy shows the latest renewal date. The listing may be older.' });
  }
  out.push({ key: 'tracked', label: 'First seen by you', value: (now - l.firstSeen) / DAY, display: `${Math.round((now - l.firstSeen) / DAY)} days ago`, provenance: 'observed', note: 'When this extension first recorded the listing.' });
  if (est.perDay) out.push({ key: 'velocity', label: 'Sales velocity', value: est.perDay.mid * 30.44, display: `≈ ${(est.perDay.mid * 30.44).toFixed(1)} / month`, provenance: 'estimated', note: est.velocityNote ?? '' });
  // price position against the latest search the listing was seen in
  const q = l.searchQueries[l.searchQueries.length - 1];
  if (q && l.price !== undefined) {
    const kw = await repo.keyword(q);
    const prices = kw?.prices ?? [];
    const pr = prices.length >= 5 ? percentileRank(prices, l.price) : undefined;
    if (pr !== undefined) out.push({ key: 'pricePos', label: `Price position in "${q}"`, value: pr, display: `${Math.round(pr)}th percentile`, provenance: 'verified', note: `Compared with ${prices.length} prices from that search page (median ${median(prices)?.toFixed(2)}).` });
  }
  if (l.basketCount !== undefined) out.push({ key: 'baskets', label: 'In baskets', value: l.basketCount, display: `${l.basketCount}+`, provenance: 'verified', note: 'Shown by Etsy on the listing page.' });
  if (l.badges.length) out.push({ key: 'badges', label: 'Etsy badges', display: l.badges.join(', '), provenance: 'verified', note: 'Badges Etsy displays (for example "Bestseller" or "Popular now").' });
  return out;
}

/* ---------------- keyword ---------------- */

export interface KeywordAnalysis {
  record: KeywordRecord;
  snaps: KeywordSnapshot[];
  opportunity?: Opportunity;
  suggestions: Suggestion[];
  inAutocomplete: boolean;
}

export async function analyseKeyword(term: string, settings: Settings): Promise<KeywordAnalysis | undefined> {
  const record = await repo.keyword(term);
  if (!record) return undefined;
  const [snaps, ac] = await Promise.all([repo.keywordSnaps(term), repo.autocompleteTerms()]);
  const inAutocomplete = ac.has(term);
  return {
    record,
    snaps,
    opportunity: record.latest ? opportunityScore(term, record.latest, snaps, inAutocomplete, settings.weights) : undefined,
    suggestions: suggestions(term, record.topTitles, [...new Set([...record.autocomplete, ...[...ac].filter((a) => a !== term && ` ${a} `.includes(` ${term} `))])].slice(0, 60)),
    inAutocomplete,
  };
}

/* ---------------- shop ---------------- */

export interface ShopAnalysis {
  shop: ShopRecord;
  snaps: ShopSnapshot[];
  observed?: ReturnType<typeof observedShopVelocity>;
  lastDiff?: ShopDiff;
  changes: ChangeEntry[];
  listings: ListingRecord[];
  priceStats: { median?: number; p25?: number; p75?: number; min?: number; max?: number; n: number; currency?: string };
}

export async function analyseShop(name: string): Promise<ShopAnalysis | undefined> {
  const shop = await repo.shop(name);
  if (!shop) return undefined;
  const [snaps, changes, all] = await Promise.all([repo.shopSnaps(name), repo.changesFor(name), repo.listings()]);
  const listings = all.filter((l) => l.shopName === name);
  const withListings = snaps.filter((s) => s.listings.length);
  const lastDiff = withListings.length >= 2 ? diffShopSnapshots(withListings[withListings.length - 2], withListings[withListings.length - 1]) : undefined;
  const prices = nums(listings.map((l) => l.price));
  return {
    shop, snaps, observed: observedShopVelocity(snaps), lastDiff, changes, listings,
    priceStats: { median: median(prices), p25: quantile(prices, 0.25), p75: quantile(prices, 0.75), min: prices.length ? Math.min(...prices) : undefined, max: prices.length ? Math.max(...prices) : undefined, n: prices.length, currency: listings.find((l) => l.currency)?.currency },
  };
}

/* ---------------- compact summary for the in-page panel / sidebar ---------------- */

export type PanelSummary =
  | { kind: 'search'; term: string; analysis?: KeywordAnalysis }
  | { kind: 'listing'; id: string; analysis?: ListingAnalysis }
  | { kind: 'shop'; name: string; analysis?: ShopAnalysis };
