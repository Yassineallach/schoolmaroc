/**
 * Shared, passive DOM helpers. Extractors only read the document that the
 * user already has open; they never fetch anything.
 */

export function parseCount(raw: string | null | undefined): number | undefined {
  if (!raw) return undefined;
  const s = raw.trim().replace(/\s/g, '').replace(/[()+]/g, '');
  const m = /^(\d+(?:[.,]\d+)*)(k|m)?$/i.exec(s);
  if (!m) return undefined;
  let num = m[1];
  const suffix = m[2]?.toLowerCase();
  if (suffix) {
    num = num.replace(',', '.');
    const v = parseFloat(num);
    return Number.isFinite(v) ? Math.round(v * (suffix === 'k' ? 1e3 : 1e6)) : undefined;
  }
  // thousands separators: 12,345 / 12.345 / 1,234,567
  if (/^\d{1,3}([.,]\d{3})+$/.test(num)) return parseInt(num.replace(/[.,]/g, ''), 10);
  const v = parseFloat(num.replace(',', '.'));
  return Number.isFinite(v) ? Math.round(v) : undefined;
}

export function parsePrice(raw: string | null | undefined): number | undefined {
  if (!raw) return undefined;
  const s = raw.replace(/[^\d.,]/g, '');
  if (!s) return undefined;
  const lastDot = s.lastIndexOf('.');
  const lastComma = s.lastIndexOf(',');
  let norm: string;
  if (lastDot >= 0 && lastComma >= 0) {
    norm = lastDot > lastComma ? s.replace(/,/g, '') : s.replace(/\./g, '').replace(',', '.');
  } else if (lastComma >= 0) {
    norm = /,\d{3}$/.test(s) && s.length > 4 ? s.replace(/,/g, '') : s.replace(',', '.');
  } else norm = /^\d{1,3}(\.\d{3})+$/.test(s) ? s.replace(/\./g, '') : s;
  const v = parseFloat(norm);
  return Number.isFinite(v) ? v : undefined;
}

const SYMBOLS: Record<string, string> = {
  '$': 'USD', 'US$': 'USD', 'USD': 'USD', 'CA$': 'CAD', 'C$': 'CAD', 'CAD': 'CAD', 'A$': 'AUD', 'AU$': 'AUD', 'AUD': 'AUD',
  'NZ$': 'NZD', '£': 'GBP', 'GBP': 'GBP', '€': 'EUR', 'EUR': 'EUR', '¥': 'JPY', 'JPY': 'JPY', '₹': 'INR', 'INR': 'INR',
  'MAD': 'MAD', 'DH': 'MAD', 'zł': 'PLN', 'PLN': 'PLN', 'CHF': 'CHF', 'kr': 'SEK', 'SEK': 'SEK', 'DKK': 'DKK', 'NOK': 'NOK',
  'R$': 'BRL', 'MX$': 'MXN', 'HK$': 'HKD', 'S$': 'SGD', '₪': 'ILS', 'TRY': 'TRY', '₺': 'TRY',
};

export function currencyFromSymbol(sym: string | null | undefined): string | undefined {
  if (!sym) return undefined;
  const s = sym.trim();
  return SYMBOLS[s] ?? SYMBOLS[s.toUpperCase()] ?? (/^[A-Z]{3}$/.test(s) ? s : undefined);
}

const PRICE_RE = /(US\$|CA\$|AU\$|NZ\$|HK\$|MX\$|R\$|A\$|C\$|S\$|[$£€¥₹₪₺]|MAD|USD|EUR|GBP|CAD|AUD|CHF|PLN|SEK|DKK|NOK|zł)\s?(\d[\d.,]*)/;

export function priceFromText(text: string): { price?: number; currency?: string } {
  const m = PRICE_RE.exec(text);
  if (!m) return {};
  return { price: parsePrice(m[2]), currency: currencyFromSymbol(m[1]) };
}

const SKIP = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'SVG']);

/** Visible-ish text of an element with line breaks between text nodes. */
export function textOf(root: Element | Document | null | undefined): string {
  if (!root) return '';
  const doc = (root as Document).nodeType === 9 ? (root as Document) : (root as Element).ownerDocument!;
  const start = (root as Document).nodeType === 9 ? (root as Document).body : (root as Element);
  if (!start) return '';
  const parts: string[] = [];
  const walker = doc.createTreeWalker(start, 4 /* SHOW_TEXT */, {
    acceptNode(n) {
      let p = n.parentElement;
      while (p && p !== start) {
        if (SKIP.has(p.tagName.toUpperCase()) || p.hidden) return 2;
        p = p.parentElement;
      }
      return n.nodeValue && n.nodeValue.trim() ? 1 : 2;
    },
  });
  let n: Node | null;
  while ((n = walker.nextNode())) parts.push(n.nodeValue!.replace(/\s+/g, ' ').trim());
  return parts.join('\n');
}

/** Short texts of leaf-ish elements (no element children) inside root. */
export function leafTexts(root: Element, maxLen = 60): string[] {
  const out: string[] = [];
  root.querySelectorAll('*').forEach((el) => {
    if (SKIP.has(el.tagName.toUpperCase())) return;
    if (el.children.length) return;
    const t = (el.textContent ?? '').replace(/\s+/g, ' ').trim();
    if (t && t.length <= maxLen) out.push(t);
  });
  return out;
}

export function firstMatch(text: string, res: RegExp[]): RegExpExecArray | undefined {
  for (const re of res) {
    const m = re.exec(text);
    if (m) return m;
  }
  return undefined;
}

export function jsonLd(doc: Document): unknown[] {
  const out: unknown[] = [];
  doc.querySelectorAll('script[type="application/ld+json"]').forEach((s) => {
    try {
      const v = JSON.parse(s.textContent ?? '');
      const push = (x: unknown) => {
        if (Array.isArray(x)) x.forEach(push);
        else if (x && typeof x === 'object') {
          out.push(x);
          const g = (x as Record<string, unknown>)['@graph'];
          if (g) push(g);
        }
      };
      push(v);
    } catch {
      /* malformed JSON-LD is ignored */
    }
  });
  return out;
}

export function ldOfType(doc: Document, type: string): Record<string, any> | undefined {
  return jsonLd(doc).find((x) => {
    const t = (x as Record<string, unknown>)['@type'];
    return t === type || (Array.isArray(t) && t.includes(type));
  }) as Record<string, any> | undefined;
}

export const MONTHS: Record<string, number> = {
  jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5, jul: 6, aug: 7, sep: 8, sept: 8, oct: 9, nov: 10, dec: 11,
};

/** Parses "Nov 3, 2025", "3 Nov, 2025", "November 3 2025", "3 November 2025". Returns UTC ms. */
export function parseDate(s: string): number | undefined {
  const t = s.replace(/[.,]/g, ' ').replace(/\s+/g, ' ').trim().toLowerCase();
  let m = /^([a-z]{3,9}) (\d{1,2}) (\d{4})$/.exec(t);
  let day: number, mon: number | undefined, year: number;
  if (m) { mon = MONTHS[m[1].slice(0, m[1] === 'sept' ? 4 : 3)]; day = +m[2]; year = +m[3]; }
  else {
    m = /^(\d{1,2}) ([a-z]{3,9}) (\d{4})$/.exec(t);
    if (!m) return undefined;
    day = +m[1]; mon = MONTHS[m[2].slice(0, 3)]; year = +m[3];
  }
  if (mon === undefined || day < 1 || day > 31) return undefined;
  return Date.UTC(year, mon, day);
}

export const BADGES: [RegExp, string][] = [
  [/^bestseller$/i, 'Bestseller'],
  [/^popular now$/i, 'Popular now'],
  [/^star seller$/i, 'Star Seller'],
  [/^etsy'?s pick$/i, "Etsy's Pick"],
  [/^(free (shipping|delivery))$/i, 'Free shipping'],
  [/^(digital download|instant download)$/i, 'Digital download'],
  [/^personali[sz]able$/i, 'Personalisable'],
];

export function badgesFrom(texts: string[]): string[] {
  const set = new Set<string>();
  for (const t of texts) for (const [re, label] of BADGES) if (re.test(t.trim())) set.add(label);
  return [...set];
}

export function cleanText(s: string | null | undefined): string {
  return (s ?? '').replace(/\s+/g, ' ').trim();
}

export function abs(href: string | null | undefined, base: string): string {
  try {
    const u = new URL(href ?? '', base);
    u.hash = '';
    // strip tracking parameters but keep the listing path
    ['ref', 'pro', 'frs', 'sts', 'plkey', 'logging_key', 'click_key', 'click_sum', 'pf_from', 'sr_prefetch', 'pop'].forEach((p) => u.searchParams.delete(p));
    return u.toString();
  } catch {
    return href ?? '';
  }
}

export function listingIdFromUrl(href: string): string | undefined {
  return /\/listing\/(\d+)/.exec(href)?.[1];
}
