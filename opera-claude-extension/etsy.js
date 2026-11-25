// Etsy page extraction. extractEtsyPage() is injected into an Etsy tab with
// chrome.scripting.executeScript, so it must be fully self-contained.
// It only reads the page the user already has open; it never crawls.

export function extractEtsyPage() {
  const clean = (s) => (s || "").replace(/\s+/g, " ").trim();
  const abs = (u) => {
    try {
      const url = new URL(u, location.href);
      url.search = "";
      url.hash = "";
      return url.href;
    } catch {
      return "";
    }
  };
  const num = (s) => {
    const m = String(s ?? "").replace(/,/g, "").match(/\d+(\.\d+)?/);
    return m ? Number(m[0]) : "";
  };

  // ---------- structured data (JSON-LD) ----------
  const ld = [];
  for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
    try {
      const data = JSON.parse(s.textContent);
      const items = Array.isArray(data) ? data : data["@graph"] || [data];
      ld.push(...items);
    } catch {}
  }
  const ofType = (t) =>
    ld.filter((x) => [].concat(x?.["@type"] || []).some((y) => String(y).toLowerCase() === t));

  const path = location.pathname;
  const pageType = /\/listing\/\d+/.test(path)
    ? "listing"
    : /^\/(\w{2}\/)?shop\//.test(path)
    ? "shop"
    : /\/search/.test(path)
    ? "search"
    : /\/c\//.test(path)
    ? "category"
    : "other";

  const result = {
    pageType,
    url: location.href,
    title: document.title,
    listings: [],
    product: null,
    reviews: [],
    shop: null,
    pageText: clean(document.body?.innerText || "").slice(0, 60000),
  };

  // ---------- single listing page ----------
  if (pageType === "listing") {
    const p = ofType("product")[0] || {};
    const offer = [].concat(p.offers || [])[0] || {};
    const rating = p.aggregateRating || {};
    const h1 = document.querySelector("h1");
    const shopLink = document.querySelector('a[href*="/shop/"]');
    result.product = {
      id: path.match(/\/listing\/(\d+)/)?.[1] || "",
      title: clean(p.name || h1?.textContent),
      price: offer.price ?? offer.lowPrice ?? "",
      highPrice: offer.highPrice ?? "",
      currency: offer.priceCurrency || "",
      availability: String(offer.availability || "").split("/").pop(),
      rating: rating.ratingValue ?? "",
      reviewCount: rating.reviewCount ?? rating.ratingCount ?? "",
      shop: clean(p.brand?.name || shopLink?.textContent),
      shopUrl: shopLink ? abs(shopLink.href) : "",
      category: clean(p.category),
      description: clean(p.description).slice(0, 3000),
      images: [].concat(p.image || []).map((i) => (typeof i === "string" ? i : i?.url)).filter(Boolean).slice(0, 10),
      url: abs(location.href),
    };
    const ldReviews = [].concat(p.review || []);
    result.reviews = ldReviews.map((r) => ({
      rating: r.reviewRating?.ratingValue ?? "",
      author: clean(r.author?.name || r.author),
      date: r.datePublished || "",
      text: clean(r.reviewBody || r.description),
    }));
    // Visible reviews on the page, if JSON-LD had none.
    if (!result.reviews.length) {
      document.querySelectorAll('[data-review-region], [id^="review-preview"]').forEach((el) => {
        const text = clean(el.querySelector("p, [id*='review-text']")?.textContent || el.textContent);
        if (text) result.reviews.push({ rating: "", author: "", date: "", text: text.slice(0, 1000) });
      });
    }
  }

  // ---------- shop info ----------
  if (pageType === "shop") {
    const org = ofType("organization")[0] || ofType("store")[0] || {};
    const text = document.body.innerText;
    result.shop = {
      name: clean(org.name || document.querySelector("h1")?.textContent),
      sales: num(text.match(/([\d,]+)\s+Sales/i)?.[1]),
      rating: org.aggregateRating?.ratingValue ?? "",
      reviewCount: org.aggregateRating?.reviewCount ?? "",
      location: clean(org.address?.addressLocality || ""),
      url: abs(location.href),
    };
  }

  // ---------- listing cards (search, category, shop, related items) ----------
  const seen = new Set();
  const ldItems = ofType("itemlist").flatMap((l) => l.itemListElement || []);
  const ldByUrl = new Map();
  for (const it of ldItems) {
    const prod = it.item || it;
    const u = abs(prod.url || it.url || "");
    if (u) ldByUrl.set(u, prod);
  }

  const links = document.querySelectorAll('a[href*="/listing/"]');
  for (const a of links) {
    const id = a.href.match(/\/listing\/(\d+)/)?.[1];
    if (!id || seen.has(id)) continue;
    if (pageType === "listing" && location.pathname.includes(`/listing/${id}`)) continue;

    const card =
      a.closest("[data-listing-id]") ||
      a.closest("li") ||
      a.closest("div.v2-listing-card, div[class*='listing-card']") ||
      a.parentElement;
    if (!card) continue;

    const title = clean(
      card.querySelector("h2, h3, [data-listing-card-title]")?.textContent ||
        a.getAttribute("title") ||
        a.getAttribute("aria-label") ||
        a.textContent
    );
    if (!title) continue;
    seen.add(id);

    const priceEls = card.querySelectorAll(".currency-value");
    const symbol = clean(card.querySelector(".currency-symbol")?.textContent);
    const cardText = clean(card.innerText);
    let price = priceEls[0] ? clean(priceEls[0].textContent) : "";
    if (!price) price = cardText.match(/(?:[$€£¥]|MAD|USD|EUR|GBP)\s?[\d.,]+/)?.[0] || "";
    const originalPrice = priceEls[1] ? clean(priceEls[1].textContent) : "";

    const ratingEl = card.querySelector('[aria-label*="star" i], input[name="rating"]');
    const rating = num(ratingEl?.getAttribute("aria-label") || ratingEl?.value) || "";
    const reviewCount = num(cardText.match(/\(([\d,.]+k?)\)/i)?.[1]?.replace(/k$/i, "000")) || "";

    let shop = clean(card.querySelector("[data-shop-name], .wt-text-truncate.wt-text-caption, p[class*='shop']")?.textContent);
    shop = shop.replace(/^(Ad by|From shop|by)\s+/i, "");

    const img = card.querySelector("img");
    const ldProd = ldByUrl.get(abs(a.href));

    result.listings.push({
      id,
      title: clean(ldProd?.name) || title,
      price: price || ldProd?.offers?.price || "",
      currency: symbol || ldProd?.offers?.priceCurrency || "",
      originalPrice,
      onSale: !!originalPrice || /% off/i.test(cardText),
      rating,
      reviewCount,
      shop,
      ad: /\bAd\b/.test(cardText.slice(0, 80)) || /Ad by/i.test(cardText),
      freeShipping: /free (shipping|delivery)/i.test(cardText),
      bestseller: /bestseller/i.test(cardText),
      starSeller: /star seller/i.test(cardText),
      image: img?.currentSrc || img?.src || "",
      url: abs(a.href),
    });
  }

  return result;
}

// ---------- helpers used by the extension page ----------

export const LISTING_COLUMNS = [
  "title", "price", "currency", "originalPrice", "onSale", "rating", "reviewCount",
  "shop", "ad", "freeShipping", "bestseller", "starSeller", "url", "image", "id",
];

export function toCSV(rows, columns) {
  const esc = (v) => {
    const s = v == null ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [columns.join(","), ...rows.map((r) => columns.map((c) => esc(r[c])).join(","))].join("\n");
}

/** Plain-text version of the extracted data, compact enough to paste into Claude. */
export function toPromptText(pages) {
  const out = [];
  for (const p of pages) {
    out.push(`### Etsy page: ${p.title}\nURL: ${p.url}\nPage type: ${p.pageType}`);
    if (p.product) {
      const { images, ...prod } = p.product;
      out.push("Product:\n" + Object.entries(prod).filter(([, v]) => v !== "").map(([k, v]) => `- ${k}: ${v}`).join("\n"));
    }
    if (p.shop) {
      out.push("Shop:\n" + Object.entries(p.shop).filter(([, v]) => v !== "").map(([k, v]) => `- ${k}: ${v}`).join("\n"));
    }
    if (p.reviews.length) {
      out.push(
        `Reviews (${p.reviews.length}):\n` +
          p.reviews.map((r) => `- ${r.rating ? r.rating + "★ " : ""}${r.text}`).join("\n")
      );
    }
    if (p.listings.length) {
      const cols = ["title", "price", "currency", "originalPrice", "rating", "reviewCount", "shop", "freeShipping", "bestseller", "ad", "url"];
      out.push(
        `Listings (${p.listings.length}) — tab-separated:\n` +
          cols.join("\t") + "\n" +
          p.listings.map((l) => cols.map((c) => String(l[c] ?? "").replace(/\t/g, " ")).join("\t")).join("\n")
      );
    }
    // If structured extraction found little, include the visible page text.
    if (!p.product && !p.listings.length) out.push("Visible page text:\n" + p.pageText.slice(0, 30000));
  }
  return out.join("\n\n");
}
