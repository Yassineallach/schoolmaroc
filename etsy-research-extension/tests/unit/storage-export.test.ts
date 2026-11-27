import 'fake-indexeddb/auto';
import { beforeEach, describe, expect, it } from 'vitest';
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { JSDOM } from 'jsdom';
import * as repo from '../../src/core/storage/repo';
import { clearAll } from '../../src/core/storage/db';
import { extractListing, extractSearch, extractShop } from '../../src/content/extractors/pages';
import { crc32, toCSV, toXLSX } from '../../src/core/export';
import { analyseKeyword, analyseListing, analyseShop } from '../../src/core/summaries';
import { DEFAULT_SETTINGS } from '../../src/shared/types';

const doc = (name: string, url: string) => new JSDOM(readFileSync(`tests/fixtures/${name}`, 'utf8'), { url }).window.document;
const DAY = 86_400_000;

describe('export', () => {
  it('crc32 of a known string', () => {
    expect(crc32(new TextEncoder().encode('The quick brown fox jumps over the lazy dog'))).toBe(0x414fa339);
  });
  it('CSV escapes quotes, commas, newlines and formula prefixes', () => {
    const csv = toCSV([['a', 'b'], ['x,y', 'he said "hi"'], ['=SUM(A1)', 'line\nbreak']]);
    expect(csv).toContain('"x,y"');
    expect(csv).toContain('"he said ""hi"""');
    expect(csv).toContain("'=SUM(A1)");
    expect(csv).toContain('"line\nbreak"');
  });
  it('XLSX opens in openpyxl with the right values', () => {
    const bytes = toXLSX([{ name: 'Products', rows: [['Title', 'Price', 'Digital'], ['Mug <&> "x"', 18.5, true], ['Tea', 4, false]] }, { name: 'Second', rows: [['k'], ['v']] }]);
    const dir = mkdtempSync(join(tmpdir(), 'xlsx-'));
    const f = join(dir, 't.xlsx');
    writeFileSync(f, bytes);
    const out = execFileSync('python3', ['-I', '-c', `import openpyxl,sys,json; wb=openpyxl.load_workbook(sys.argv[1]); print(json.dumps({ws.title:[[c for c in r] for r in ws.iter_rows(values_only=True)] for ws in wb}))`, f]).toString();
    const data = JSON.parse(out);
    expect(data.Products[1]).toEqual(['Mug <&> "x"', 18.5, true]);
    expect(data.Second[1]).toEqual(['v']);
  });
});

describe('repository ingestion', () => {
  beforeEach(async () => { await clearAll(); });

  it('ingests a search into keyword, snapshot and products', async () => {
    const url = 'https://www.etsy.com/search?q=personalized+mug';
    await repo.ingest(extractSearch(doc('search.html', url), url));
    const k = await repo.keyword('personalized mug');
    expect(k?.latest?.resultCount).toBe(1234);
    expect(k?.topTitles).toHaveLength(4);
    expect(await repo.keywordSnaps('personalized mug')).toHaveLength(1);
    expect((await repo.listings()).length).toBe(4);
    expect((await repo.autocompleteTerms()).has('personalized mug for mom')).toBe(true);
    const a = await analyseKeyword('personalized mug', DEFAULT_SETTINGS);
    expect(a?.opportunity?.score).toBeTypeOf('number');
    expect(a?.suggestions.some((s) => s.groups.includes('autocomplete'))).toBe(true);
  });

  it('merges snapshots within an hour and diffs across visits', async () => {
    const url = 'https://www.etsy.com/listing/1001/custom-name-mug';
    const x1 = extractListing(doc('listing.html', url), url);
    x1.capturedAt = Date.now() - 10 * DAY;
    await repo.ingest(x1);
    const x2 = { ...x1, capturedAt: x1.capturedAt + 10 * 60 * 1000 };
    await repo.ingest(x2);
    expect(await repo.listingSnaps('1001')).toHaveLength(1);
    const x3 = { ...x1, capturedAt: Date.now(), price: 20, listingReviewCount: 492, shopSales: 12445 };
    const r = await repo.ingestListing(x3);
    expect(r.changes.map((c) => c.field).sort()).toEqual(['listing reviews', 'price', 'shop sales']);
    expect(await repo.listingSnaps('1001')).toHaveLength(2);
    const a = await analyseListing('1001', DEFAULT_SETTINGS);
    expect(a?.estimate.velocityMethod).toBe('review-delta');
    expect(a?.estimate.k).toBeCloseTo(12445 / 3100);
    expect(a?.revenue?.month?.mid).toBeGreaterThan(0);
    expect(a?.indicators.find((i) => i.key === 'conversion')?.provenance).toBe('unavailable');
  });

  it('tracks a shop across visits', async () => {
    const url = 'https://www.etsy.com/shop/MugMakerCo';
    const s1 = extractShop(doc('shop.html', url), url);
    s1.capturedAt = Date.now() - 5 * DAY;
    await repo.ingest(s1);
    const s2 = { ...s1, capturedAt: Date.now(), sales: 12451, cards: [...s1.cards.slice(1), { ...s1.cards[0], listingId: '1020', title: 'New mug' }] };
    const r = await repo.ingestShop(s2);
    expect(r.changes.some((c) => c.field === 'new listing')).toBe(true);
    expect(r.changes.some((c) => c.field === 'no longer visible')).toBe(true);
    const a = await analyseShop('MugMakerCo');
    expect(a?.observed?.delta).toBe(50);
    expect(a?.observed?.perDay).toBeCloseTo(10, 0);
  });

  it('backs up and restores', async () => {
    await repo.saveKeyword('tea cup');
    await repo.saveCollection({ id: 'c1', name: 'Ideas', kind: 'products', items: ['1'], createdAt: 1 });
    const b = await repo.exportBackup({ theme: 'dark' });
    expect(repo.validateBackup({})).toBeTruthy();
    await clearAll();
    expect(await repo.keywords()).toHaveLength(0);
    await repo.importBackup(JSON.parse(JSON.stringify(b)), 'replace');
    expect((await repo.keywords())[0].term).toBe('tea cup');
    expect((await repo.collections())[0].name).toBe('Ideas');
    await repo.importBackup(JSON.parse(JSON.stringify(b)), 'merge');
    expect(await repo.keywords()).toHaveLength(1);
  });
});

describe('snapshot merging', () => {
  beforeEach(async () => { await clearAll(); });
  it('a listing visit right after a shop visit keeps the shop listing list', async () => {
    const shopUrl = 'https://www.etsy.com/shop/MugMakerCo';
    const s = extractShop(doc('shop.html', shopUrl), shopUrl);
    await repo.ingest(s);
    const lUrl = 'https://www.etsy.com/listing/1001/custom-name-mug';
    const l = extractListing(doc('listing.html', lUrl), lUrl);
    l.capturedAt = s.capturedAt + 60_000;
    await repo.ingest(l);
    const snaps = await repo.shopSnaps('MugMakerCo');
    expect(snaps).toHaveLength(1);
    expect(snaps[0].listings).toHaveLength(3);
    expect(snaps[0].sales).toBe(12345);
  });
});
