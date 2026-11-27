/** High-level persistence: turns page extractions into records, snapshots and change logs. */
import { computeKeywordStats } from '../keywords';
import { diffListingSnapshots, diffShopSnapshots, shopDiffToChanges } from '../competitors';
import { hash, normalise } from '../text';
import { byIndex, clearAll, del, deleteByIndex, get, getAll, put, putMany, STORES, StoreName, tx } from './db';
import type {
  ChangeEntry, Collection, Extraction, HistoryEntry, KeywordRecord, KeywordSnapshot, ListingCard, ListingExtraction, ListingRecord,
  ListingSnapshot, SearchExtraction, ShopExtraction, ShopRecord, ShopSnapshot,
} from '../../shared/types';

/** Snapshots closer together than this replace each other, so a burst of reloads is one data point. */
export const SNAPSHOT_MERGE_MS = 60 * 60 * 1000;

export const termKey = (q: string) => normalise(q);

async function addOrMergeSnapshot<T extends { id?: number; ts: number }>(store: StoreName, index: string, key: string, snap: T): Promise<{ prev?: T; merged: boolean }> {
  const all = (await byIndex<T>(store, index, key)).sort((a, b) => a.ts - b.ts);
  const last = all[all.length - 1];
  if (last && snap.ts - last.ts < SNAPSHOT_MERGE_MS) {
    // keep fields the newer snapshot did not capture (e.g. a listing page has no shop listing list)
    const defined = Object.fromEntries(Object.entries(snap).filter(([, v]) => v !== undefined && !(Array.isArray(v) && v.length === 0)));
    await put(store, { ...last, ...defined, id: last.id });
    return { prev: all[all.length - 2], merged: true };
  }
  await put(store, snap);
  return { prev: last, merged: false };
}

async function addHistory(entry: HistoryEntry) {
  const recent = await tx('history', 'readonly', (t) =>
    new Promise<HistoryEntry | undefined>((res) => {
      const req = t.objectStore('history').index('ts').openCursor(null, 'prev');
      req.onsuccess = () => res(req.result?.value as HistoryEntry | undefined);
      req.onerror = () => res(undefined);
    }),
  );
  if (recent && recent.url === entry.url && entry.ts - recent.ts < 10 * 60 * 1000) return;
  await put('history', entry);
}

function cardToListing(c: ListingCard, existing: ListingRecord | undefined, ts: number, query?: string): ListingRecord {
  const base: ListingRecord = existing ?? {
    listingId: c.listingId, title: c.title, url: c.url, category: [], variations: [], relatedTerms: [], imageAlts: [], badges: [],
    detailed: false, firstSeen: ts, lastSeen: ts, searchQueries: [],
  };
  return {
    ...base,
    title: base.detailed ? base.title : c.title || base.title,
    url: base.url || c.url,
    imageUrl: base.imageUrl ?? c.imageUrl,
    shopName: base.shopName ?? c.shopName,
    price: c.price ?? base.price,
    originalPrice: c.originalPrice,
    currency: c.currency ?? base.currency,
    rating: base.detailed ? base.rating : c.rating ?? base.rating,
    isDigital: base.isDigital ?? c.isDigital,
    freeShipping: c.freeShipping || base.freeShipping,
    badges: [...new Set([...(base.detailed ? base.badges : []), ...c.badges])],
    lastSeen: ts,
    searchQueries: query && !base.searchQueries.includes(query) ? [...base.searchQueries, query].slice(-30) : base.searchQueries,
  };
}

export async function ingestSearch(x: SearchExtraction): Promise<{ term: string }> {
  const ts = x.capturedAt;
  const term = termKey(x.query);
  if (term) {
    const stats = computeKeywordStats(x);
    const existing = await get<KeywordRecord>('keywords', term);
    const rec: KeywordRecord = {
      term,
      folder: existing?.folder,
      notes: existing?.notes,
      saved: existing?.saved ?? false,
      firstSeen: existing?.firstSeen ?? ts,
      lastSeen: ts,
      latest: stats.sampleSize ? stats : existing?.latest,
      autocomplete: [...new Set([...(existing?.autocomplete ?? []), ...x.autocomplete.map(termKey)])].slice(0, 100),
      topTitles: x.cards.length ? x.cards.map((c) => c.title).filter(Boolean) : existing?.topTitles ?? [],
      prices: x.cards.length ? x.cards.map((c) => c.price).filter((p): p is number => p !== undefined) : existing?.prices ?? [],
    };
    await put('keywords', rec);
    if (stats.sampleSize) await addOrMergeSnapshot<KeywordSnapshot>('keywordSnapshots', 'term', term, { term, ts, stats });
    await addHistory({ ts, kind: 'search', label: x.query, url: x.url });
  }
  await recordAutocomplete(x.autocomplete);
  await upsertCards(x.cards, ts, term || undefined);
  return { term };
}

export async function recordAutocomplete(items: string[]) {
  if (!items.length) return;
  const meta = (await get<{ key: string; terms: string[] }>('meta', 'autocomplete')) ?? { key: 'autocomplete', terms: [] };
  const set = new Set(meta.terms);
  for (const i of items) set.add(termKey(i));
  await put('meta', { key: 'autocomplete', terms: [...set].slice(-5000) });
}

export async function autocompleteTerms(): Promise<Set<string>> {
  const meta = await get<{ key: string; terms: string[] }>('meta', 'autocomplete');
  return new Set(meta?.terms ?? []);
}

async function upsertCards(cards: ListingCard[], ts: number, query?: string) {
  if (!cards.length) return;
  const existing = await Promise.all(cards.map((c) => get<ListingRecord>('listings', c.listingId)));
  await putMany('listings', cards.map((c, i) => cardToListing(c, existing[i], ts, query)));
}

export async function ingestListing(x: ListingExtraction): Promise<{ changes: ChangeEntry[] }> {
  if (!x.listingId) return { changes: [] };
  const ts = x.capturedAt;
  const existing = await get<ListingRecord>('listings', x.listingId);
  const rec: ListingRecord = {
    listingId: x.listingId,
    title: x.title || existing?.title || '',
    url: x.url,
    imageUrl: x.imageUrls[0] ?? existing?.imageUrl,
    shopName: x.shopName ?? existing?.shopName,
    price: x.price ?? existing?.price,
    originalPrice: x.originalPrice,
    currency: x.currency ?? existing?.currency,
    rating: x.rating ?? existing?.rating,
    listingReviewCount: x.listingReviewCount ?? existing?.listingReviewCount,
    shopReviewCount: x.shopReviewCount ?? existing?.shopReviewCount,
    shopSales: x.shopSales ?? existing?.shopSales,
    favourites: x.favourites ?? existing?.favourites,
    basketCount: x.basketCount,
    listedOn: x.listedOn ?? existing?.listedOn,
    category: x.category.length ? x.category : existing?.category ?? [],
    isDigital: x.isDigital,
    variations: x.variations,
    shipsFrom: x.shipsFrom ?? existing?.shipsFrom,
    freeShipping: x.freeShipping,
    description: x.description ?? existing?.description,
    relatedTerms: x.relatedTerms.length ? x.relatedTerms : existing?.relatedTerms ?? [],
    imageCount: x.imageUrls.length || existing?.imageCount,
    imageAlts: x.imageAlts.length ? x.imageAlts : existing?.imageAlts ?? [],
    badges: x.badges,
    detailed: true,
    firstSeen: existing?.firstSeen ?? ts,
    lastSeen: ts,
    searchQueries: existing?.searchQueries ?? [],
  };
  await put('listings', rec);
  const snap: ListingSnapshot = {
    listingId: x.listingId, ts, price: x.price, listingReviewCount: x.listingReviewCount, shopReviewCount: x.shopReviewCount, shopSales: x.shopSales,
    favourites: x.favourites, basketCount: x.basketCount, title: x.title, termsHash: x.relatedTerms.length ? hash([...x.relatedTerms].sort().join('|')) : undefined,
    imageCount: x.imageUrls.length || undefined,
  };
  const { prev } = await addOrMergeSnapshot('listingSnapshots', 'listingId', x.listingId, snap);
  const changes = prev ? diffListingSnapshots(x.listingId, prev, snap) : [];
  await putMany('changes', changes);

  if (x.shopName) {
    const shop = await get<ShopRecord>('shops', x.shopName);
    await put('shops', {
      ...stripUndef(shop ?? {}),
      shopName: x.shopName, url: shop?.url ?? x.shopUrl ?? `https://www.etsy.com/shop/${x.shopName}`, sections: shop?.sections ?? [], tracked: shop?.tracked ?? false,
      firstSeen: shop?.firstSeen ?? ts, lastSeen: ts,
      sales: x.shopSales ?? shop?.sales, reviewCount: x.shopReviewCount ?? shop?.reviewCount,
    } as ShopRecord);
    if (x.shopSales !== undefined) {
      await addOrMergeSnapshot<ShopSnapshot>('shopSnapshots', 'shopName', x.shopName, { shopName: x.shopName, ts, sales: x.shopSales, reviewCount: x.shopReviewCount, listings: [] });
    }
  }
  await addHistory({ ts, kind: 'listing', label: x.title || `Listing ${x.listingId}`, url: x.url });
  return { changes };
}

function stripUndef<T extends object>(o: T): Partial<T> {
  return Object.fromEntries(Object.entries(o).filter(([, v]) => v !== undefined)) as Partial<T>;
}

export async function ingestShop(x: ShopExtraction): Promise<{ changes: ChangeEntry[] }> {
  const ts = x.capturedAt;
  const existing = await get<ShopRecord>('shops', x.shopName);
  const rec: ShopRecord = {
    shopName: x.shopName,
    url: `https://www.etsy.com/shop/${x.shopName}`,
    title: x.title ?? existing?.title,
    location: x.location ?? existing?.location,
    sales: x.sales ?? existing?.sales,
    onEtsySince: x.onEtsySince ?? existing?.onEtsySince,
    reviewCount: x.reviewCount ?? existing?.reviewCount,
    rating: x.rating ?? existing?.rating,
    admirers: x.admirers ?? existing?.admirers,
    totalListings: x.totalListings ?? existing?.totalListings,
    sections: x.sections.length ? x.sections : existing?.sections ?? [],
    tracked: existing?.tracked ?? false,
    firstSeen: existing?.firstSeen ?? ts,
    lastSeen: ts,
  };
  await put('shops', rec);
  const snap: ShopSnapshot = {
    shopName: x.shopName, ts, sales: x.sales, reviewCount: x.reviewCount, rating: x.rating, admirers: x.admirers, totalListings: x.totalListings,
    listings: x.cards.map((c) => ({ id: c.listingId, price: c.price, title: c.title })),
  };
  // compare against the last snapshot that captured listings (shop page), not listing-page counter snapshots
  const all = (await byIndex<ShopSnapshot>('shopSnapshots', 'shopName', x.shopName)).sort((a, b) => a.ts - b.ts);
  const prevWithListings = [...all].reverse().find((s) => s.listings.length && ts - s.ts >= SNAPSHOT_MERGE_MS);
  await addOrMergeSnapshot('shopSnapshots', 'shopName', x.shopName, snap);
  let changes: ChangeEntry[] = [];
  if (prevWithListings) changes = shopDiffToChanges(x.shopName, diffShopSnapshots(prevWithListings, snap), ts);
  await putMany('changes', changes);
  await upsertCards(x.cards.map((c) => ({ ...c, shopName: c.shopName ?? x.shopName })), ts);
  await addHistory({ ts, kind: 'shop', label: x.shopName, url: x.url });
  return { changes };
}

export async function ingest(x: Extraction) {
  if (x.type === 'search') return ingestSearch(x);
  if (x.type === 'listing') return ingestListing(x);
  return ingestShop(x);
}

/* ---------- queries used by the UI ---------- */

export const listings = () => getAll<ListingRecord>('listings');
export const shops = () => getAll<ShopRecord>('shops');
export const keywords = () => getAll<KeywordRecord>('keywords');
export const collections = () => getAll<Collection>('collections');
export const history = async () => (await getAll<HistoryEntry>('history')).sort((a, b) => b.ts - a.ts);
export const changes = async () => (await getAll<ChangeEntry>('changes')).sort((a, b) => b.ts - a.ts);
export const changesFor = async (key: string) => (await byIndex<ChangeEntry>('changes', 'key', key)).sort((a, b) => b.ts - a.ts);
export const listingSnaps = async (id: string) => (await byIndex<ListingSnapshot>('listingSnapshots', 'listingId', id)).sort((a, b) => a.ts - b.ts);
export const shopSnaps = async (name: string) => (await byIndex<ShopSnapshot>('shopSnapshots', 'shopName', name)).sort((a, b) => a.ts - b.ts);
export const keywordSnaps = async (term: string) => (await byIndex<KeywordSnapshot>('keywordSnapshots', 'term', term)).sort((a, b) => a.ts - b.ts);
export const allKeywordSnaps = () => getAll<KeywordSnapshot>('keywordSnapshots');
export const allShopSnaps = () => getAll<ShopSnapshot>('shopSnapshots');
export const listing = (id: string) => get<ListingRecord>('listings', id);
export const shop = (name: string) => get<ShopRecord>('shops', name);
export const keyword = (term: string) => get<KeywordRecord>('keywords', term);

export async function saveKeyword(term: string, patch: Partial<KeywordRecord> = {}) {
  const key = termKey(term);
  if (!key) return;
  const ex = await get<KeywordRecord>('keywords', key);
  const now = Date.now();
  await put('keywords', { term: key, saved: true, firstSeen: now, lastSeen: now, autocomplete: [], topTitles: [], prices: [], ...ex, ...patch } as KeywordRecord);
}

export async function updateKeyword(term: string, patch: Partial<KeywordRecord>) {
  const ex = await get<KeywordRecord>('keywords', term);
  if (ex) await put('keywords', { ...ex, ...patch });
}

export async function deleteKeyword(term: string) {
  await del('keywords', term);
  await deleteByIndex('keywordSnapshots', 'term', term);
}

export async function setShopTracked(name: string, tracked: boolean) {
  const s = await get<ShopRecord>('shops', name);
  const now = Date.now();
  await put('shops', s ? { ...s, tracked } : { shopName: name, url: `https://www.etsy.com/shop/${name}`, sections: [], tracked, firstSeen: now, lastSeen: now });
}

export async function deleteShop(name: string) {
  await del('shops', name);
  await deleteByIndex('shopSnapshots', 'shopName', name);
  await deleteByIndex('changes', 'key', name);
}

export async function deleteListing(id: string) {
  await del('listings', id);
  await deleteByIndex('listingSnapshots', 'listingId', id);
  await deleteByIndex('changes', 'key', id);
}

export async function saveCollection(c: Collection) {
  await put('collections', c);
}

export async function deleteCollection(id: string) {
  await del('collections', id);
}

export async function addToCollection(id: string, item: string) {
  const c = await get<Collection>('collections', id);
  if (c && !c.items.includes(item)) await put('collections', { ...c, items: [...c.items, item] });
}

export async function removeFromCollection(id: string, item: string) {
  const c = await get<Collection>('collections', id);
  if (c) await put('collections', { ...c, items: c.items.filter((i) => i !== item) });
}

export async function addToolHistory(label: string) {
  await put('history', { ts: Date.now(), kind: 'tool', label } as HistoryEntry);
}

export async function clearHistory() {
  await tx('history', 'readwrite', (t) => { t.objectStore('history').clear(); });
}

/* ---------- backup / restore ---------- */

export const BACKUP_FORMAT = 'shoplens-backup';
export const BACKUP_VERSION = 1;

export async function exportBackup(settings: unknown) {
  const data: Record<string, unknown[]> = {};
  for (const s of STORES) data[s.name] = await getAll(s.name);
  return { format: BACKUP_FORMAT, version: BACKUP_VERSION, exportedAt: new Date().toISOString(), settings, data };
}

export function validateBackup(b: any): string | undefined {
  if (!b || typeof b !== 'object') return 'The file is not a JSON object.';
  if (b.format !== BACKUP_FORMAT) return 'This file is not a Shoplens backup.';
  if (typeof b.version !== 'number' || b.version > BACKUP_VERSION) return 'This backup was made by a newer version.';
  if (!b.data || typeof b.data !== 'object') return 'The backup has no data section.';
  for (const s of STORES) if (b.data[s.name] !== undefined && !Array.isArray(b.data[s.name])) return `The section "${s.name}" is invalid.`;
  return undefined;
}

export async function importBackup(b: any, mode: 'replace' | 'merge') {
  const err = validateBackup(b);
  if (err) throw new Error(err);
  if (mode === 'replace') await clearAll();
  for (const s of STORES) {
    const rows = (b.data[s.name] ?? []) as Record<string, unknown>[];
    // in merge mode, auto-increment ids from another install would collide: drop them
    await putMany(s.name, mode === 'merge' && s.autoIncrement ? rows.map(({ id: _id, ...r }) => r) : rows);
  }
}

export { clearAll };

export const allListingSnaps = () => getAll<ListingSnapshot>('listingSnapshots');

function groupBy<T>(items: T[], key: (t: T) => string): Map<string, T[]> {
  const m = new Map<string, T[]>();
  for (const i of items) {
    const k = key(i);
    const arr = m.get(k);
    if (arr) arr.push(i);
    else m.set(k, [i]);
  }
  for (const arr of m.values()) (arr as { ts?: number }[]).sort((a, b) => (a.ts ?? 0) - (b.ts ?? 0));
  return m;
}

/** Everything needed to estimate many listings at once (one read per store). */
export async function bulk() {
  const [ls, lsn, sh, ssn, kw] = await Promise.all([listings(), allListingSnaps(), shops(), allShopSnaps(), keywords()]);
  return {
    listings: ls,
    listingSnaps: groupBy(lsn, (s) => s.listingId),
    shops: new Map(sh.map((s) => [s.shopName, s])),
    shopList: sh,
    shopSnaps: groupBy(ssn, (s) => s.shopName),
    keywords: new Map(kw.map((k) => [k.term, k])),
  };
}
