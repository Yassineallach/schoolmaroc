/**
 * Every number shown to the user carries a provenance:
 *  - verified:  displayed by Etsy on a page the user opened
 *  - observed:  derived from differences between the user's own snapshots
 *  - estimated: produced by a documented statistical model
 */
export type Provenance = 'verified' | 'observed' | 'estimated';

export type PageType = 'search' | 'listing' | 'shop' | 'other';

/** A listing card as it appears in search results or on a shop page. */
export interface ListingCard {
  listingId: string;
  title: string;
  url: string;
  imageUrl?: string;
  shopName?: string;
  shopId?: string;
  price?: number;
  originalPrice?: number;
  currency?: string;
  rating?: number;
  /** On Etsy cards this count is usually the shop's review count, not the listing's. */
  cardReviewCount?: number;
  isAd: boolean;
  badges: string[];
  freeShipping: boolean;
  isDigital?: boolean;
  position: number;
}

export interface SearchExtraction {
  type: 'search';
  url: string;
  query: string;
  resultCount?: number;
  resultCountIsLowerBound?: boolean;
  cards: ListingCard[];
  autocomplete: string[];
  capturedAt: number;
}

export interface Variation {
  name: string;
  options: string[];
}

export interface ListingExtraction {
  type: 'listing';
  url: string;
  listingId: string;
  title: string;
  imageUrls: string[];
  imageAlts: string[];
  shopName?: string;
  shopUrl?: string;
  price?: number;
  priceMax?: number;
  originalPrice?: number;
  currency?: string;
  listingReviewCount?: number;
  shopReviewCount?: number;
  rating?: number;
  shopSales?: number;
  favourites?: number;
  basketCount?: number;
  basketCountIsLowerBound?: boolean;
  recentPurchases24h?: number;
  listedOn?: number;
  category: string[];
  isDigital: boolean;
  variations: Variation[];
  shipsFrom?: string;
  freeShipping: boolean;
  description?: string;
  relatedTerms: string[];
  badges: string[];
  capturedAt: number;
}

export interface ShopExtraction {
  type: 'shop';
  url: string;
  shopName: string;
  title?: string;
  location?: string;
  sales?: number;
  onEtsySince?: number;
  reviewCount?: number;
  rating?: number;
  admirers?: number;
  totalListings?: number;
  sections: { name: string; count?: number }[];
  cards: ListingCard[];
  capturedAt: number;
}

export type Extraction = SearchExtraction | ListingExtraction | ShopExtraction;

export interface FieldReport {
  field: string;
  found: boolean;
  value?: string;
}

export interface PageResult {
  pageType: PageType;
  extraction?: Extraction;
  fields: FieldReport[];
  url: string;
  capturedAt: number;
}

/* ---------- stored records ---------- */

export interface ListingRecord {
  listingId: string;
  title: string;
  url: string;
  imageUrl?: string;
  shopName?: string;
  price?: number;
  originalPrice?: number;
  currency?: string;
  rating?: number;
  listingReviewCount?: number;
  shopReviewCount?: number;
  shopSales?: number;
  favourites?: number;
  basketCount?: number;
  listedOn?: number;
  category: string[];
  isDigital?: boolean;
  variations: Variation[];
  shipsFrom?: string;
  freeShipping?: boolean;
  description?: string;
  relatedTerms: string[];
  imageCount?: number;
  imageAlts: string[];
  badges: string[];
  /** true once the listing page itself was opened (not only seen as a card). */
  detailed: boolean;
  firstSeen: number;
  lastSeen: number;
  searchQueries: string[];
}

export interface ListingSnapshot {
  id?: number;
  listingId: string;
  ts: number;
  price?: number;
  listingReviewCount?: number;
  shopReviewCount?: number;
  shopSales?: number;
  favourites?: number;
  basketCount?: number;
  title?: string;
  termsHash?: string;
  imageCount?: number;
}

export interface ShopRecord {
  shopName: string;
  url: string;
  title?: string;
  location?: string;
  sales?: number;
  onEtsySince?: number;
  reviewCount?: number;
  rating?: number;
  admirers?: number;
  totalListings?: number;
  sections: { name: string; count?: number }[];
  tracked: boolean;
  firstSeen: number;
  lastSeen: number;
}

export interface ShopSnapshot {
  id?: number;
  shopName: string;
  ts: number;
  sales?: number;
  reviewCount?: number;
  rating?: number;
  admirers?: number;
  totalListings?: number;
  /** listing ids visible on the captured page with their prices */
  listings: { id: string; price?: number; title: string }[];
}

export interface KeywordStats {
  resultCount?: number;
  resultCountIsLowerBound?: boolean;
  sampleSize: number;
  adShare: number;
  bestsellerShare: number;
  popularNowShare: number;
  starSellerShare: number;
  freeShippingShare: number;
  digitalShare: number;
  medianPrice?: number;
  p25Price?: number;
  p75Price?: number;
  minPrice?: number;
  maxPrice?: number;
  medianCardReviews?: number;
  meanRating?: number;
  shopConcentration: number;
  distinctShops: number;
  currency?: string;
}

export interface KeywordRecord {
  term: string;
  folder?: string;
  notes?: string;
  saved: boolean;
  firstSeen: number;
  lastSeen: number;
  latest?: KeywordStats;
  autocomplete: string[];
  topTitles: string[];
  prices: number[];
}

export interface KeywordSnapshot {
  id?: number;
  term: string;
  ts: number;
  stats: KeywordStats;
}

export interface ChangeEntry {
  id?: number;
  entity: 'listing' | 'shop';
  key: string;
  ts: number;
  field: string;
  before?: string;
  after?: string;
}

export interface Collection {
  id: string;
  name: string;
  kind: 'products' | 'keywords' | 'tags';
  items: string[];
  createdAt: number;
}

export interface HistoryEntry {
  id?: number;
  ts: number;
  kind: PageType | 'tool';
  label: string;
  url?: string;
}

export interface ScoringWeights {
  demand: number;
  competition: number;
  trend: number;
  specificity: number;
}

export interface Settings {
  theme: 'system' | 'light' | 'dark';
  pageReading: boolean;
  onboardingDone: boolean;
  inPageBadges: boolean;
  displayCurrency: string;
  /** units of currency per 1 unit of displayCurrency, entered by user */
  fxRates: Record<string, number>;
  fallbackSalesPerReview: number;
  minShopReviewsForCalibration: number;
  defaultDiscountPct: number;
  weights: ScoringWeights;
  country: 'US' | 'UK' | 'EU' | 'AU' | 'CA';
}

export const DEFAULT_SETTINGS: Settings = {
  theme: 'system',
  pageReading: false,
  onboardingDone: false,
  inPageBadges: true,
  displayCurrency: '',
  fxRates: {},
  fallbackSalesPerReview: 4,
  minShopReviewsForCalibration: 20,
  defaultDiscountPct: 0,
  weights: { demand: 35, competition: 35, trend: 15, specificity: 15 },
  country: 'US',
};
