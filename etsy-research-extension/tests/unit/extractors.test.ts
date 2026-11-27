// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { JSDOM } from 'jsdom';
import { detectPageType, extractListing, extractPage, extractSearch, extractShop } from '../../src/content/extractors/pages';
import { parseCount, parseDate, parsePrice } from '../../src/content/extractors/common';

const load = (name: string, url: string) => new JSDOM(readFileSync(`tests/fixtures/${name}`, 'utf8'), { url }).window.document;

describe('number parsing', () => {
  it('parses counts', () => {
    expect(parseCount('12,345')).toBe(12345);
    expect(parseCount('1.2k')).toBe(1200);
    expect(parseCount('(2.3k)')).toBe(2300);
    expect(parseCount('12.345')).toBe(12345);
    expect(parseCount('1,5k')).toBe(1500);
    expect(parseCount('abc')).toBeUndefined();
  });
  it('parses prices in several locales', () => {
    expect(parsePrice('18.50')).toBe(18.5);
    expect(parsePrice('1,234.56')).toBe(1234.56);
    expect(parsePrice('1.234,56')).toBe(1234.56);
    expect(parsePrice('12,50')).toBe(12.5);
    expect(parsePrice('€ 1.200')).toBe(1200);
  });
  it('parses dates', () => {
    expect(parseDate('Nov 3, 2025')).toBe(Date.UTC(2025, 10, 3));
    expect(parseDate('3 Nov, 2025')).toBe(Date.UTC(2025, 10, 3));
    expect(parseDate('September 21 2024')).toBe(Date.UTC(2024, 8, 21));
    expect(parseDate('nonsense')).toBeUndefined();
  });
});

describe('page type', () => {
  it('detects Etsy pages, including locale prefixes', () => {
    expect(detectPageType('https://www.etsy.com/search?q=mug')).toBe('search');
    expect(detectPageType('https://www.etsy.com/uk/listing/123/x')).toBe('listing');
    expect(detectPageType('https://www.etsy.com/shop/Foo')).toBe('shop');
    expect(detectPageType('https://www.etsy.com/market/name_mug')).toBe('search');
    expect(detectPageType('https://www.etsy.com/c/home-and-living')).toBe('search');
    expect(detectPageType('https://www.etsy.com/cart')).toBe('other');
    expect(detectPageType('https://example.com/listing/1')).toBe('other');
  });
});

describe('search extraction', () => {
  const url = 'https://www.etsy.com/search?q=personalized+mug';
  const x = extractSearch(load('search.html', url), url);
  it('reads query and result count', () => {
    expect(x.query).toBe('personalized mug');
    expect(x.resultCount).toBe(1234);
  });
  it('reads every card once', () => {
    expect(x.cards.map((c) => c.listingId)).toEqual(['1001', '1002', '1003', '1004']);
  });
  it('reads card fields', () => {
    const [a, b, c, d] = x.cards;
    expect(a.price).toBe(18.5);
    expect(a.originalPrice).toBe(24);
    expect(a.currency).toBe('USD');
    expect(a.rating).toBe(4.9);
    expect(a.cardReviewCount).toBe(2300);
    expect(a.badges).toContain('Bestseller');
    expect(a.freeShipping).toBe(true);
    expect(a.shopName).toBe('MugMakerCo');
    expect(a.isAd).toBe(false);
    expect(a.url).toBe('https://www.etsy.com/listing/1001/custom-name-mug-personalized-gift');
    expect(b.isAd).toBe(true);
    expect(b.badges).toContain('Popular now');
    expect(b.cardReviewCount).toBe(812);
    expect(c.isAd).toBe(true);
    expect(c.shopName).toBe('CeramicCorner');
    expect(c.cardReviewCount).toBe(1045);
    expect(d.isDigital).toBe(true);
    expect(d.price).toBe(4.99);
  });
  it('reads visible autocomplete suggestions', () => {
    expect(x.autocomplete).toEqual(['personalized mug for mom', 'personalized mug with photo']);
  });
  it('derives query from /market/ URLs', () => {
    const u = 'https://www.etsy.com/market/name_mug';
    expect(extractSearch(load('search.html', u), u).query).toBe('name mug');
  });
});

describe('listing extraction', () => {
  const url = 'https://www.etsy.com/listing/1001/custom-name-mug?ref=hp';
  const x = extractListing(load('listing.html', url), url);
  it('reads structured data', () => {
    expect(x.listingId).toBe('1001');
    expect(x.title).toBe('Custom Name Mug, Personalized Gift for Mom, Coffee Mug');
    expect(x.price).toBe(18.5);
    expect(x.priceMax).toBe(26);
    expect(x.currency).toBe('USD');
    expect(x.rating).toBe(4.9);
    expect(x.shopName).toBe('MugMakerCo');
    expect(x.category).toEqual(['Home & Living', 'Kitchen & Dining', 'Mugs']);
  });
  it('prefers explicit item review count over JSON-LD', () => {
    expect(x.listingReviewCount).toBe(482);
    expect(x.shopReviewCount).toBe(3100);
  });
  it('reads counters and dates from text', () => {
    expect(x.shopSales).toBe(12345);
    expect(x.favourites).toBe(1820);
    expect(x.basketCount).toBe(20);
    expect(x.basketCountIsLowerBound).toBe(true);
    expect(x.listedOn).toBe(Date.UTC(2025, 10, 3));
    expect(x.shipsFrom).toBe('United States');
    expect(x.freeShipping).toBe(true);
    expect(x.originalPrice).toBe(24);
  });
  it('reads variations, images, description and related terms', () => {
    expect(x.variations).toEqual([{ name: 'Size', options: ['11 oz', '15 oz ($26.00)'] }, { name: 'Colour', options: ['White', 'Black'] }]);
    expect(x.imageUrls).toHaveLength(3);
    expect(x.imageAlts[0]).toBe('White mug with the name Anna in script');
    expect(x.description).toContain('Dishwasher and microwave safe');
    expect(x.relatedTerms).toEqual(['name mug', 'custom mug', 'gift for mom']);
    expect(x.badges).toContain('Star Seller');
    expect(x.isDigital).toBe(false);
  });
  it('produces a diagnostics report', () => {
    const r = extractPage(load('listing.html', url), url);
    expect(r.pageType).toBe('listing');
    expect(r.fields.find((f) => f.field === 'shop sales')?.found).toBe(true);
  });
});

describe('shop extraction', () => {
  const url = 'https://www.etsy.com/shop/MugMakerCo';
  const x = extractShop(load('shop.html', url), url);
  it('reads shop counters', () => {
    expect(x.shopName).toBe('MugMakerCo');
    expect(x.sales).toBe(12401);
    expect(x.onEtsySince).toBe(2017);
    expect(x.admirers).toBe(2050);
    expect(x.rating).toBe(4.9);
    expect(x.reviewCount).toBe(3120);
    expect(x.totalListings).toBe(86);
    expect(x.location).toBe('Columbus, Ohio');
    expect(x.sections).toEqual([{ name: 'Name mugs', count: 40 }, { name: 'Templates', count: 12 }]);
  });
  it('reads listing cards', () => {
    expect(x.cards.map((c) => [c.listingId, c.price])).toEqual([['1001', 18.5], ['1004', 4.99], ['1010', 16]]);
  });
});
