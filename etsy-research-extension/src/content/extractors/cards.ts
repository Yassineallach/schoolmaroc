import type { ListingCard } from '../../shared/types';
import { abs, badgesFrom, cleanText, currencyFromSymbol, leafTexts, listingIdFromUrl, parseCount, parsePrice, priceFromText, textOf } from './common';

/** Finds listing cards (search results, shop pages, category pages). */
export function extractCards(doc: Document, root: ParentNode = doc): ListingCard[] {
  const base = doc.location?.href || 'https://www.etsy.com/';
  const anchors = Array.from(root.querySelectorAll<HTMLAnchorElement>('a[href*="/listing/"]'));
  const seen = new Set<string>();
  const cards: ListingCard[] = [];
  for (const a of anchors) {
    const id = a.getAttribute('data-listing-id') || listingIdFromUrl(a.getAttribute('href') ?? '');
    if (!id || seen.has(id)) continue;
    const container = cardContainer(a, id);
    if (!container) continue;
    // ignore links inside reviews, "you may also like" in the buy box etc.: a card must contain a price or an image
    const img = container.querySelector('img');
    const leaves = leafTexts(container, 80);
    const text = textOf(container);
    const price = cardPrice(container, text);
    if (!img && price.price === undefined) continue;
    seen.add(id);

    const title = cleanText(
      a.getAttribute('title') ||
        container.querySelector('h3, h2, [class*="title"]')?.textContent ||
        img?.getAttribute('alt') ||
        a.textContent,
    );
    const shopLink = container.querySelector<HTMLAnchorElement>('a[href*="/shop/"]');
    let shopName = container.getAttribute('data-shop-name') || shopLink?.getAttribute('href')?.match(/\/shop\/([^/?#]+)/)?.[1] || undefined;
    const isAd = leaves.some((t) => /^(ad|ad by .+|sponsored|advertisement)$/i.test(t));
    if (!shopName) {
      for (const t of leaves) {
        const m = /^(?:ad by|from shop|by)\s+([A-Za-z0-9]{3,40})$/i.exec(t);
        if (m && !/^etsy seller$/i.test(m[1])) { shopName = m[1]; break; }
      }
    }
    const badges = badgesFrom(leaves);
    cards.push({
      listingId: id,
      title,
      url: abs(a.getAttribute('href'), base),
      imageUrl: img && (img.getAttribute('src') || img.getAttribute('data-src')) ? abs(img.getAttribute('src') || img.getAttribute('data-src'), base) : undefined,
      shopName,
      shopId: container.getAttribute('data-shop-id') || a.getAttribute('data-shop-id') || undefined,
      price: price.price,
      originalPrice: price.original,
      currency: price.currency,
      rating: cardRating(container, text),
      cardReviewCount: cardReviews(text),
      isAd,
      badges,
      freeShipping: badges.includes('Free shipping') || /free (shipping|delivery)/i.test(text),
      isDigital: badges.includes('Digital download') || /digital download|instant download/i.test(text),
      position: cards.length + 1,
    });
  }
  return cards;
}

function cardContainer(a: HTMLAnchorElement, id: string): Element | null {
  const byId = a.closest(`[data-listing-id="${id}"]`);
  if (byId && byId !== a) return byId;
  const li = a.closest('li, [data-search-results-item], .v2-listing-card, article');
  if (li) return li;
  let el: Element | null = a;
  for (let i = 0; i < 3 && el?.parentElement; i++) el = el.parentElement;
  return el ?? a;
}

function cardPrice(c: Element, text: string): { price?: number; original?: number; currency?: string } {
  const values = Array.from(c.querySelectorAll('.currency-value'));
  const symbols = Array.from(c.querySelectorAll('.currency-symbol'));
  if (values.length) {
    const sale = values.find((v) => !v.closest('[class*="strikethrough"], s, del, .wt-text-strikethrough'));
    const orig = values.find((v) => v.closest('[class*="strikethrough"], s, del, .wt-text-strikethrough'));
    return {
      price: parsePrice(sale?.textContent ?? values[0].textContent),
      original: orig ? parsePrice(orig.textContent) : undefined,
      currency: currencyFromSymbol(symbols[0]?.textContent) ?? priceFromText(text).currency,
    };
  }
  const p = priceFromText(text.replace(/original price[^\n]*/gi, ''));
  return { price: p.price, currency: p.currency };
}

function cardRating(c: Element, text: string): number | undefined {
  const input = c.querySelector<HTMLInputElement>('input[name="rating"]');
  const v = input?.getAttribute('value');
  if (v && !isNaN(+v)) return +v;
  const m = /(\d(?:[.,]\d+)?)\s*(?:out of 5 stars|star rating|stars)/i.exec(text);
  return m ? parseFloat(m[1].replace(',', '.')) : undefined;
}

function cardReviews(text: string): number | undefined {
  const m = /\((\d[\d,.]*\s?k?)\)/i.exec(text) || /(\d[\d,.]*k?)\s+reviews?/i.exec(text);
  return m ? parseCount(m[1]) : undefined;
}
