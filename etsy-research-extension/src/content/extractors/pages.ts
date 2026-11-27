import type { FieldReport, ListingExtraction, PageResult, PageType, SearchExtraction, ShopExtraction, Variation } from '../../shared/types';
import { extractCards } from './cards';
import {
  abs, badgesFrom, cleanText, currencyFromSymbol, firstMatch, leafTexts, ldOfType, listingIdFromUrl, parseCount, parseDate, parsePrice, priceFromText, textOf,
} from './common';

export function detectPageType(url: string): PageType {
  let u: URL;
  try { u = new URL(url); } catch { return 'other'; }
  if (!/(^|\.)etsy\.com$/.test(u.hostname)) return 'other';
  const p = u.pathname.replace(/^\/[a-z]{2}(-[a-z]{2})?(?=\/)/i, ''); // strip locale prefix like /uk/ or /fr/
  if (/^\/listing\/\d+/.test(p)) return 'listing';
  if (/^\/shop\/[^/]+\/?$/.test(p) || /^\/shop\/[^/]+\/(items|sold|reviews)?$/.test(p)) return 'shop';
  if (/^\/(search|market|c)(\/|$)/.test(p)) return 'search';
  return 'other';
}

const num = (re: RegExp[], text: string) => {
  const m = firstMatch(text, re);
  return m ? parseCount(m[1]) : undefined;
};

/* ---------------- search ---------------- */

export function searchQuery(url: string, doc: Document): string {
  const u = new URL(url);
  const q = u.searchParams.get('q');
  if (q) return q.trim();
  const p = u.pathname.replace(/^\/[a-z]{2}(-[a-z]{2})?(?=\/)/i, '');
  const market = /^\/market\/([^/?#]+)/.exec(p);
  if (market) return decodeURIComponent(market[1]).replace(/[_-]+/g, ' ').trim();
  const cat = /^\/c\/(.+)$/.exec(p);
  if (cat) return cleanText(doc.querySelector('h1')?.textContent) || decodeURIComponent(cat[1].split('/').pop() ?? '').replace(/-/g, ' ');
  return '';
}

export function extractAutocomplete(doc: Document): string[] {
  const opts = doc.querySelectorAll('[role="listbox"] [role="option"], [id*="suggestion" i] li, [data-search-suggestions] li');
  const out = new Set<string>();
  opts.forEach((o) => {
    const t = cleanText(o.textContent);
    if (t && t.length < 80 && !/^(search for|recent searches?|clear)/i.test(t)) out.add(t.toLowerCase());
  });
  return [...out];
}

export function extractSearch(doc: Document, url: string): SearchExtraction {
  const text = textOf(doc);
  const over = /(?:over|more than)\s+(\d[\d,.]*k?)\s+(?:relevant\s+)?results/i.exec(text);
  const exact = /(\d[\d,.]*k?)\s+(?:relevant\s+)?results/i.exec(text) || /\((\d[\d,.]*)\s+relevant results\)/i.exec(text);
  const main = doc.querySelector('main, #content, [data-search-results]') ?? doc;
  return {
    type: 'search',
    url,
    query: searchQuery(url, doc),
    resultCount: parseCount((over ?? exact)?.[1]),
    resultCountIsLowerBound: !!over,
    cards: extractCards(doc, main),
    autocomplete: extractAutocomplete(doc),
    capturedAt: Date.now(),
  };
}

/* ---------------- listing ---------------- */

function variations(doc: Document): Variation[] {
  const out: Variation[] = [];
  doc.querySelectorAll<HTMLSelectElement>('select[id^="variation-selector"], select[name^="variation"], select[data-variation-number], select[data-selector="listing-page-variation-select"]').forEach((sel) => {
    const label = cleanText((sel.id && doc.querySelector(`label[for="${sel.id.replace(/["\\]/g, '\\$&')}"]`)?.textContent) || sel.getAttribute('aria-label') || sel.closest('div')?.querySelector('label, legend')?.textContent || 'Option');
    const options = Array.from(sel.options)
      .filter((o) => o.value && !/^select( an)? /i.test(o.textContent ?? '') && !/^(choose|please select)/i.test(o.textContent ?? ''))
      .map((o) => cleanText(o.textContent));
    if (options.length) out.push({ name: label.replace(/\s*\*$/, ''), options });
  });
  return out;
}

function relatedTerms(doc: Document): string[] {
  const out = new Set<string>();
  doc.querySelectorAll('h2, h3, h4').forEach((h) => {
    if (!/related searches|related to this item|explore (more )?related|explore related/i.test(h.textContent ?? '')) return;
    const scope = h.closest('section') ?? h.parentElement?.parentElement ?? h.parentElement;
    scope?.querySelectorAll('a').forEach((a) => {
      const t = cleanText(a.textContent);
      if (t && t.length <= 60 && /\/(market|search|c)\b/.test(a.getAttribute('href') ?? '')) out.add(t);
    });
  });
  doc.querySelectorAll('[data-appears-component-name*="tags" i] a, .tags-section-container a').forEach((a) => {
    const t = cleanText(a.textContent);
    if (t && t.length <= 60) out.add(t);
  });
  return [...out];
}

function description(doc: Document): string | undefined {
  const el = doc.querySelector('[data-product-details-description-text-content], [data-id="description-text"], #wt-content-toggle-product-details-read-more');
  if (el) return textOf(el).trim();
  const meta = doc.querySelector('meta[name="description"]')?.getAttribute('content');
  return meta?.trim() || undefined;
}

function images(doc: Document, ld?: Record<string, any>): { urls: string[]; alts: string[] } {
  const imgs = Array.from(doc.querySelectorAll<HTMLImageElement>('[data-carousel-pane] img, ul[data-carousel-pane-list] img, .listing-page-image-carousel-component img, [data-component="listing-page-image-carousel"] img'));
  const urls = new Set<string>();
  const alts: string[] = [];
  for (const i of imgs) {
    const u = i.getAttribute('data-src-zoom-image') || i.getAttribute('src') || i.getAttribute('data-src');
    if (u && !urls.has(abs(u, doc.location?.href || 'https://www.etsy.com/'))) { urls.add(abs(u, doc.location?.href || 'https://www.etsy.com/')); alts.push(i.getAttribute('alt') ?? ''); }
  }
  if (!urls.size && ld?.image) {
    const list = Array.isArray(ld.image) ? ld.image : [ld.image];
    for (const x of list) {
      const u = typeof x === 'string' ? x : x?.contentURL || x?.url;
      if (u) urls.add(u);
    }
  }
  return { urls: [...urls], alts };
}

export function extractListing(doc: Document, url: string): ListingExtraction {
  const ld = ldOfType(doc, 'Product');
  const crumbs = ldOfType(doc, 'BreadcrumbList');
  const text = textOf(doc);
  const leaves = leafTexts(doc.body, 80);
  const offers = Array.isArray(ld?.offers) ? ld?.offers[0] : ld?.offers;

  let price = parsePrice(String(offers?.price ?? offers?.lowPrice ?? ''));
  let priceMax = offers?.highPrice !== undefined ? parsePrice(String(offers.highPrice)) : undefined;
  let currency: string | undefined = offers?.priceCurrency;
  const buyBox = doc.querySelector('[data-buy-box-region], #listing-page-cart, [data-selector="price-only"]');
  if (price === undefined) {
    const p = priceFromText(textOf(buyBox) || text);
    price = p.price;
    currency = currency ?? p.currency;
  }
  if (priceMax === price) priceMax = undefined;
  const origEl = buyBox?.querySelector('.wt-text-strikethrough, [class*="strikethrough"], s, del');
  const originalPrice = origEl ? parsePrice(origEl.textContent) : undefined;

  const shopLink = doc.querySelector<HTMLAnchorElement>('[data-shop-name] a, a[href*="/shop/"][data-shop-id], a[href*="/shop/"]');
  const shopName = cleanText(ld?.brand?.name ?? ld?.brand) || shopLink?.getAttribute('href')?.match(/\/shop\/([^/?#]+)/)?.[1] || undefined;

  const listingReviews = num([/reviews for this item\s*\(?(\d[\d,.]*k?)\)?/i, /item reviews\s*\(?(\d[\d,.]*k?)\)?/i, /(\d[\d,.]*k?)\s+item reviews/i], text);
  const shopReviews = num([/(\d[\d,.]*k?)\s+shop reviews/i, /reviews for this shop\s*\(?(\d[\d,.]*k?)\)?/i, /shop reviews\s*\(?(\d[\d,.]*k?)\)?/i], text);
  const basket = firstMatch(text, [/in\s+(\d+)(\+)?\s+(?:baskets|carts)/i, /(?:over\s+)?(\d+)(\+)?\s+people have this in their (?:baskets?|carts?)/i]);
  const listed = firstMatch(text, [/listed on\s+([A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})/i, /listed on\s+(\d{1,2}\s+[A-Za-z]{3,9}\.?,?\s+\d{4})/i]);
  const ships = leaves.map((t) => /^(?:ships|dispatches|sent) from\s+(.+?)\.?$/i.exec(t)).find(Boolean);
  const category: string[] = crumbs?.itemListElement
    ? (crumbs.itemListElement as any[]).sort((a, b) => (a.position ?? 0) - (b.position ?? 0)).map((x) => cleanText(x.name ?? x.item?.name)).filter((x) => x && !/^(home|homepage|etsy|all categories)$/i.test(x))
    : Array.from(doc.querySelectorAll('nav[aria-label*="readcrumb" i] a, [data-breadcrumbs] a')).map((a) => cleanText(a.textContent)).filter((x) => x && !/^(home|homepage|etsy|all categories)$/i.test(x));
  if (!category.length && typeof ld?.category === 'string') category.push(...ld.category.split(/\s*[>/]\s*/).filter(Boolean));
  const img = images(doc, ld);
  const badges = badgesFrom(leaves);
  const isDigital = badges.includes('Digital download') || /\b(digital download|instant download|digital file)\b/i.test(text);

  return {
    type: 'listing',
    url: abs(url, url),
    listingId: listingIdFromUrl(url) ?? String(ld?.sku ?? ld?.productID ?? ''),
    title: cleanText(ld?.name) || cleanText(doc.querySelector('h1')?.textContent),
    imageUrls: img.urls,
    imageAlts: img.alts,
    shopName,
    shopUrl: shopName ? `https://www.etsy.com/shop/${shopName}` : undefined,
    price,
    priceMax,
    originalPrice: originalPrice && price && originalPrice > price ? originalPrice : undefined,
    currency: currencyFromSymbol(currency) ?? currency,
    listingReviewCount: listingReviews ?? (ld?.aggregateRating?.reviewCount !== undefined ? parseCount(String(ld.aggregateRating.reviewCount)) : undefined),
    shopReviewCount: shopReviews,
    rating: ld?.aggregateRating?.ratingValue !== undefined ? parseFloat(String(ld.aggregateRating.ratingValue)) : undefined,
    shopSales: num([/(\d[\d,.]*k?)\s+sales\b/i], text),
    favourites: num([/(\d[\d,.]*k?)\s+favou?rites\b/i, /favou?rited by\s+(\d[\d,.]*k?)/i], text),
    basketCount: basket ? parseCount(basket[1]) : undefined,
    basketCountIsLowerBound: basket ? !!basket[2] || /over/i.test(basket[0]) : undefined,
    recentPurchases24h: num([/(\d+)\s+(?:people\s+)?bought (?:this )?in the (?:past|last) 24 hours/i], text),
    listedOn: listed ? parseDate(listed[1]) : undefined,
    category,
    isDigital,
    variations: variations(doc),
    shipsFrom: ships?.[1],
    freeShipping: /free (shipping|delivery)/i.test(textOf(buyBox) || text),
    description: description(doc),
    relatedTerms: relatedTerms(doc),
    badges,
    capturedAt: Date.now(),
  };
}

/* ---------------- shop ---------------- */

export function extractShop(doc: Document, url: string): ShopExtraction {
  const text = textOf(doc);
  const name = /\/shop\/([^/?#]+)/.exec(new URL(url).pathname)?.[1] ?? cleanText(doc.querySelector('h1')?.textContent);
  const org = ldOfType(doc, 'Organization') ?? ldOfType(doc, 'Store');
  const ratingM = /(\d(?:[.,]\d+)?)\s*out of 5 stars?\s*\(?(\d[\d,.]*k?)?\)?/i.exec(text);
  const sections: { name: string; count?: number }[] = [];
  doc.querySelectorAll('[data-section-id]').forEach((el) => {
    const t = cleanText(el.textContent);
    const m = /^(.*?)\s*\(?(\d[\d,]*)\)?$/.exec(t);
    if (m && m[1]) sections.push({ name: m[1], count: parseCount(m[2]) });
    else if (t) sections.push({ name: t });
  });
  const allSec = sections.find((s) => /^all( items)?$/i.test(s.name));
  const totalFromText = num([/all items\s*\(?(\d[\d,]*)\)?/i, /\ball\s*\n\s*(\d[\d,]*)\b/i, /(\d[\d,]*)\s+items?\b/i], text);
  return {
    type: 'shop',
    url,
    shopName: decodeURIComponent(name),
    title: cleanText(doc.querySelector('[data-in-modal-editable-text="title"], .shop-name-and-title-container p, h1 + p')?.textContent) || undefined,
    location: cleanText(doc.querySelector('[data-key="user_location"], .shop-location, [data-shop-location]')?.textContent) || undefined,
    sales: num([/(\d[\d,.]*k?)\s+sales\b/i], text),
    onEtsySince: (() => {
      const m = /on etsy since\s+(\d{4})/i.exec(text);
      return m ? +m[1] : undefined;
    })(),
    reviewCount: org?.aggregateRating?.reviewCount !== undefined ? parseCount(String(org.aggregateRating.reviewCount)) : ratingM?.[2] ? parseCount(ratingM[2]) : num([/reviews\s*\(?(\d[\d,.]*k?)\)/i], text),
    rating: org?.aggregateRating?.ratingValue !== undefined ? parseFloat(String(org.aggregateRating.ratingValue)) : ratingM ? parseFloat(ratingM[1].replace(',', '.')) : undefined,
    admirers: num([/(\d[\d,.]*k?)\s+admirers/i], text),
    totalListings: allSec?.count ?? totalFromText,
    sections: sections.filter((s) => !/^all( items)?$/i.test(s.name)),
    cards: extractCards(doc, doc.querySelector('[data-listings-container], #items, main') ?? doc),
    capturedAt: Date.now(),
  };
}

/* ---------------- dispatcher ---------------- */

function report(field: string, v: unknown): FieldReport {
  const found = !(v === undefined || v === null || v === '' || (Array.isArray(v) && v.length === 0));
  const value = found ? (Array.isArray(v) ? `${v.length} item(s)` : String(v).slice(0, 80)) : undefined;
  return { field, found, value };
}

export function extractPage(doc: Document, url: string): PageResult {
  const pageType = detectPageType(url);
  const base = { pageType, url, capturedAt: Date.now() };
  if (pageType === 'search') {
    const x = extractSearch(doc, url);
    return { ...base, extraction: x, fields: [report('query', x.query), report('result count', x.resultCount), report('listing cards', x.cards), report('card prices', x.cards.filter((c) => c.price !== undefined)), report('card shop names', x.cards.filter((c) => c.shopName)), report('ads detected', x.cards.filter((c) => c.isAd)), report('autocomplete', x.autocomplete)] };
  }
  if (pageType === 'listing') {
    const x = extractListing(doc, url);
    return {
      ...base,
      extraction: x,
      fields: [
        report('listing id', x.listingId), report('title', x.title), report('price', x.price), report('currency', x.currency), report('shop', x.shopName),
        report('shop sales', x.shopSales), report('listing reviews', x.listingReviewCount), report('shop reviews', x.shopReviewCount), report('rating', x.rating),
        report('favourites', x.favourites), report('in baskets', x.basketCount), report('listed on', x.listedOn ? new Date(x.listedOn).toISOString().slice(0, 10) : undefined),
        report('category', x.category.join(' › ')), report('variations', x.variations), report('images', x.imageUrls), report('description', x.description ? `${x.description.length} chars` : undefined),
        report('related terms', x.relatedTerms), report('ships from', x.shipsFrom),
      ],
    };
  }
  if (pageType === 'shop') {
    const x = extractShop(doc, url);
    return { ...base, extraction: x, fields: [report('shop', x.shopName), report('sales', x.sales), report('on Etsy since', x.onEtsySince), report('reviews', x.reviewCount), report('rating', x.rating), report('admirers', x.admirers), report('total listings', x.totalListings), report('sections', x.sections), report('listing cards', x.cards)] };
  }
  return { ...base, fields: [] };
}
