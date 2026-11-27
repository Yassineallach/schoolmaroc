/**
 * Deterministic listing SEO rules. Every rule has an id, a severity and a
 * plain explanation. Nothing here generates text; it only checks text.
 */
import { containsPhrase, contentWords, duplicates, fleschReadingEase, ngrams, normalise, phrasePosition, stem, words } from './text';

export const LIMITS = { titleMax: 140, tagsMax: 13, tagMaxChars: 20, imagesMax: 20 };

export type Severity = 'error' | 'warning' | 'info' | 'pass';

export interface RuleResult {
  id: string;
  area: 'title' | 'tags' | 'description' | 'images' | 'listing' | 'keywords';
  severity: Severity;
  message: string;
  detail?: string;
}

export interface ListingInput {
  title: string;
  tags: string[];
  description: string;
  imageCount?: number;
  imageAlts?: string[];
  keywords: string[];
  category?: string[];
  variationsCount?: number;
  price?: number;
  tagsAreRelatedTerms?: boolean;
}

export interface TitleAnalysis {
  chars: number;
  words: number;
  duplicateWords: string[];
  allCapsWords: string[];
  segments: string[];
  first40: string;
  keywordPositions: { keyword: string; index: number; inFirst40: boolean }[];
  specialChars: Record<string, number>;
  avgWordLength: number;
}

export function analyseTitle(title: string, keywords: string[] = []): TitleAnalysis {
  const raw = title.trim();
  const toks = raw.split(/\s+/).filter(Boolean);
  const cw = contentWords(raw).map(stem);
  const special: Record<string, number> = {};
  for (const ch of ['&', '%', ':', '|', '!', '$', '^']) {
    const c = raw.split(ch).length - 1;
    if (c) special[ch] = c;
  }
  const first40 = raw.slice(0, 40);
  return {
    chars: raw.length,
    words: toks.length,
    duplicateWords: duplicates(cw),
    allCapsWords: toks.filter((t) => t.length > 2 && /^[A-Z0-9]+$/.test(t) && /[A-Z]/.test(t)),
    segments: raw.split(/\s*[,|]\s*|\s+[-–—]\s+/).filter(Boolean),
    first40,
    keywordPositions: keywords.filter(Boolean).map((k) => {
      const idx = phrasePosition(raw, k);
      return { keyword: k, index: idx, inFirst40: idx >= 0 && idx < 40 };
    }),
    specialChars: special,
    avgWordLength: toks.length ? toks.reduce((a, t) => a + t.length, 0) / toks.length : 0,
  };
}

export interface TagAnalysis {
  tags: { tag: string; chars: number; tooLong: boolean; words: number; duplicate: boolean; inTitle: boolean }[];
  duplicateTags: string[];
  repeatedWords: { word: string; count: number }[];
  emptySlots: number;
  singleWordTags: number;
  missingKeywords: string[];
  coveredKeywords: string[];
}

export function analyseTags(tags: string[], title = '', keywords: string[] = []): TagAnalysis {
  const clean = tags.map((t) => t.trim()).filter(Boolean);
  const norm = clean.map((t) => normalise(t));
  const dupTags = duplicates(norm);
  const wordCounts = new Map<string, number>();
  for (const t of norm) for (const w of new Set(contentWords(t).map(stem))) wordCounts.set(w, (wordCounts.get(w) ?? 0) + 1);
  const all = [...clean, title].join(' , ');
  const covered: string[] = [];
  const missing: string[] = [];
  for (const k of keywords.filter(Boolean)) {
    const inTag = norm.some((t) => t === normalise(k) || containsPhrase(t, k));
    (inTag || containsPhrase(all, k) ? covered : missing).push(k);
  }
  const seen = new Set<string>();
  return {
    tags: clean.map((tag, i) => {
      const n = norm[i];
      const dup = seen.has(n);
      seen.add(n);
      return { tag, chars: tag.length, tooLong: tag.length > LIMITS.tagMaxChars, words: words(tag).length, duplicate: dup, inTitle: !!title && containsPhrase(title, tag) };
    }),
    duplicateTags: dupTags,
    repeatedWords: [...wordCounts.entries()].filter(([, c]) => c >= 3).map(([word, count]) => ({ word, count })).sort((a, b) => b.count - a.count),
    emptySlots: Math.max(0, LIMITS.tagsMax - clean.length),
    singleWordTags: norm.filter((t) => words(t).length === 1).length,
    missingKeywords: missing,
    coveredKeywords: covered,
  };
}

const INFO_CHECKS: { key: string; label: string; re: RegExp }[] = [
  { key: 'size', label: 'Size or dimensions', re: /\b(\d+(\.\d+)?\s?(cm|mm|in|inch|inches|"|ft|oz|ml|l|kg|g|lb)s?\b|dimension|size|measure)/i },
  { key: 'materials', label: 'Materials', re: /\b(material|made (of|from|with)|cotton|wood|ceramic|silver|gold|leather|linen|wool|resin|paper|vinyl|polyester|steel|glass|clay)\b/i },
  { key: 'care', label: 'Care instructions', re: /\b(care|wash|clean|dishwasher|microwave|hand wash|machine wash)\b/i },
  { key: 'shipping', label: 'Processing / shipping time', re: /\b(ship|dispatch|processing|deliver|business days)\b/i },
  { key: 'howto', label: 'How to order / personalise', re: /\b(how to order|personali[sz]ation|add your|enter your|include your|note to seller)\b/i },
];

export interface DescriptionAnalysis {
  chars: number;
  words: number;
  paragraphs: number;
  bullets: number;
  flesch?: number;
  first160: string;
  keywordsInFirst160: string[];
  keywordsMissing: string[];
  repeatedPhrases: { phrase: string; count: number }[];
  info: { key: string; label: string; present: boolean }[];
}

export function analyseDescription(desc: string, keywords: string[] = []): DescriptionAnalysis {
  const text = desc.trim();
  const toks = words(text);
  const tri = new Map<string, number>();
  for (const g of ngrams(toks, 3)) tri.set(g, (tri.get(g) ?? 0) + 1);
  const first160 = text.slice(0, 160);
  return {
    chars: text.length,
    words: toks.length,
    paragraphs: text ? text.split(/\n\s*\n/).filter((p) => p.trim()).length : 0,
    bullets: (text.match(/^\s*([-•*✔✓►▪]|\d+[.)])\s+/gm) ?? []).length,
    flesch: fleschReadingEase(text),
    first160,
    keywordsInFirst160: keywords.filter((k) => k && containsPhrase(first160, k)),
    keywordsMissing: keywords.filter((k) => k && !containsPhrase(text, k)),
    repeatedPhrases: [...tri.entries()].filter(([, c]) => c >= 3).map(([phrase, count]) => ({ phrase, count })).sort((a, b) => b.count - a.count).slice(0, 15),
    info: INFO_CHECKS.map((c) => ({ key: c.key, label: c.label, present: c.re.test(text) })),
  };
}

export interface Audit {
  score: number;
  results: RuleResult[];
  title: TitleAnalysis;
  tags: TagAnalysis;
  description: DescriptionAnalysis;
}

const WEIGHT: Record<Severity, number> = { error: 3, warning: 2, info: 1, pass: 0 };

export function auditListing(input: ListingInput): Audit {
  const res: RuleResult[] = [];
  const add = (r: RuleResult) => res.push(r);
  const primary = input.keywords[0];
  const t = analyseTitle(input.title, input.keywords);
  const g = analyseTags(input.tags, input.title, input.keywords);
  const d = analyseDescription(input.description, input.keywords);

  // ---- title
  if (!t.chars) add({ id: 'T1', area: 'title', severity: 'error', message: 'Title is empty' });
  else if (t.chars > LIMITS.titleMax) add({ id: 'T1', area: 'title', severity: 'error', message: `Title is ${t.chars} characters; Etsy's limit is ${LIMITS.titleMax}` });
  else if (t.chars > 100) add({ id: 'T1', area: 'title', severity: 'warning', message: `Title is long (${t.chars} characters)`, detail: 'Etsy recommends short, readable titles. Move secondary phrases into tags.' });
  else if (t.chars < 20) add({ id: 'T1', area: 'title', severity: 'warning', message: `Title is very short (${t.chars} characters)`, detail: 'Describe what the item is, plus key attributes such as material, style or recipient.' });
  else add({ id: 'T1', area: 'title', severity: 'pass', message: `Title length is fine (${t.chars} characters)` });

  if (t.duplicateWords.length) add({ id: 'T2', area: 'title', severity: 'warning', message: `Repeated words in title: ${t.duplicateWords.join(', ')}`, detail: 'Repeating a word does not add search relevance; use the space for new terms.' });
  else if (t.chars) add({ id: 'T2', area: 'title', severity: 'pass', message: 'No repeated words in title' });

  if (primary) {
    const p = t.keywordPositions[0];
    if (p.index < 0) add({ id: 'T3', area: 'title', severity: 'error', message: `Primary keyword "${primary}" is not in the title` });
    else if (!p.inFirst40) add({ id: 'T3', area: 'title', severity: 'warning', message: `Primary keyword "${primary}" starts at character ${p.index}`, detail: 'Shoppers and search results see the start of the title first; place the main phrase in the first 40 characters.' });
    else add({ id: 'T3', area: 'title', severity: 'pass', message: `Primary keyword appears in the first 40 characters` });
  } else {
    add({ id: 'T3', area: 'keywords', severity: 'info', message: 'Add a target keyword to check where it sits in the title' });
  }
  if (t.allCapsWords.length > 2) add({ id: 'T4', area: 'title', severity: 'warning', message: `${t.allCapsWords.length} words in ALL CAPS`, detail: 'Etsy may limit titles with excessive capitalisation.' });
  const sc = Object.entries(t.specialChars).filter(([ch, c]) => ['&', '%', ':'].includes(ch) && c > 1);
  if (sc.length) add({ id: 'T5', area: 'title', severity: 'warning', message: `Special characters used more than once: ${sc.map(([c]) => c).join(' ')}`, detail: 'Etsy allows &, % and : only once each in a title.' });
  if (t.words > 15) add({ id: 'T6', area: 'title', severity: 'info', message: `Title has ${t.words} words`, detail: 'Long keyword lists read poorly. Consider whether each phrase belongs in tags instead.' });

  // ---- tags
  const tagLabel = input.tagsAreRelatedTerms ? 'related search terms shown on the page (used here in place of tags)' : 'tags';
  if (!input.tags.length) add({ id: 'G1', area: 'tags', severity: input.tagsAreRelatedTerms ? 'info' : 'error', message: input.tagsAreRelatedTerms ? 'No related search terms were found on this listing page' : 'No tags entered' });
  else if (g.emptySlots > 0 && !input.tagsAreRelatedTerms) add({ id: 'G1', area: 'tags', severity: 'warning', message: `${g.emptySlots} of 13 tag slots unused`, detail: 'Every tag is an extra way to match a search.' });
  else add({ id: 'G1', area: 'tags', severity: 'pass', message: `${input.tags.length} ${tagLabel}` });
  const tooLong = g.tags.filter((x) => x.tooLong);
  if (tooLong.length && !input.tagsAreRelatedTerms) add({ id: 'G2', area: 'tags', severity: 'error', message: `${tooLong.length} tag(s) longer than 20 characters`, detail: tooLong.map((x) => x.tag).join(', ') });
  if (g.duplicateTags.length) add({ id: 'G3', area: 'tags', severity: 'warning', message: `Duplicate tags: ${g.duplicateTags.join(', ')}` });
  if (g.singleWordTags > 4 && !input.tagsAreRelatedTerms) add({ id: 'G4', area: 'tags', severity: 'warning', message: `${g.singleWordTags} single-word tags`, detail: 'Multi-word tags match more specific searches.' });
  if (g.repeatedWords.length && !input.tagsAreRelatedTerms) add({ id: 'G5', area: 'tags', severity: 'info', message: `Words repeated across 3+ tags: ${g.repeatedWords.map((w) => `${w.word} (${w.count})`).join(', ')}`, detail: 'Some repetition is natural; heavy repetition uses up tag space.' });

  // ---- keyword coverage
  if (input.keywords.length) {
    if (g.missingKeywords.length) add({ id: 'K1', area: 'keywords', severity: 'warning', message: `Keywords not in title or ${tagLabel}: ${g.missingKeywords.join(', ')}` });
    else add({ id: 'K1', area: 'keywords', severity: 'pass', message: 'All target keywords appear in the title or tags' });
  }

  // ---- description
  if (!d.chars) add({ id: 'D1', area: 'description', severity: 'warning', message: 'Description is empty or was not captured' });
  else if (d.chars < 300) add({ id: 'D1', area: 'description', severity: 'warning', message: `Short description (${d.chars} characters)`, detail: 'Buyers look for size, materials, care and delivery details.' });
  else add({ id: 'D1', area: 'description', severity: 'pass', message: `Description length ${d.chars} characters` });
  if (d.chars && primary) {
    if (d.keywordsInFirst160.includes(primary)) add({ id: 'D2', area: 'description', severity: 'pass', message: 'Primary keyword is in the first 160 characters' });
    else add({ id: 'D2', area: 'description', severity: 'info', message: 'Primary keyword is not in the opening 160 characters', detail: 'The opening lines can appear in search engine snippets.' });
  }
  if (d.flesch !== undefined && d.flesch < 40) add({ id: 'D3', area: 'description', severity: 'info', message: `Hard to read (Flesch ${Math.round(d.flesch)})`, detail: 'Shorter sentences and simpler words make it easier to read.' });
  if (d.repeatedPhrases.length) add({ id: 'D4', area: 'description', severity: 'info', message: `Repeated phrases: ${d.repeatedPhrases.slice(0, 4).map((p) => `"${p.phrase}" ×${p.count}`).join(', ')}` });
  if (d.chars) {
    const missing = d.info.filter((i) => !i.present);
    if (missing.length) add({ id: 'D5', area: 'description', severity: missing.length >= 3 ? 'warning' : 'info', message: `Possibly missing: ${missing.map((m) => m.label.toLowerCase()).join(', ')}`, detail: 'Based on keyword patterns; check the description manually.' });
    else add({ id: 'D5', area: 'description', severity: 'pass', message: 'Covers size, materials, care, shipping and ordering' });
    if (d.chars > 600 && d.paragraphs < 2 && d.bullets === 0) add({ id: 'D6', area: 'description', severity: 'info', message: 'Long description with no paragraphs or bullet points' });
  }

  // ---- images
  if (input.imageCount !== undefined) {
    if (input.imageCount < 5) add({ id: 'I1', area: 'images', severity: 'warning', message: `${input.imageCount} image(s)`, detail: `Etsy allows up to ${LIMITS.imagesMax}. Show scale, detail, variations and context.` });
    else if (input.imageCount < 10) add({ id: 'I1', area: 'images', severity: 'info', message: `${input.imageCount} images; up to ${LIMITS.imagesMax} are allowed` });
    else add({ id: 'I1', area: 'images', severity: 'pass', message: `${input.imageCount} images` });
    if (input.imageAlts && input.imageAlts.length) {
      const generic = input.imageAlts.filter((a) => !a.trim() || normalise(a) === normalise(input.title)).length;
      if (generic === input.imageAlts.length) add({ id: 'I2', area: 'images', severity: 'info', message: 'Image alt text is empty or repeats the title', detail: 'Describing each photo helps buyers who use screen readers.' });
      else add({ id: 'I2', area: 'images', severity: 'pass', message: `${input.imageAlts.length - generic} image(s) have their own alt text` });
    }
  }

  // ---- listing completeness
  if (input.category !== undefined) {
    if (!input.category.length) add({ id: 'L1', area: 'listing', severity: 'info', message: 'Category was not detected' });
    else add({ id: 'L1', area: 'listing', severity: 'pass', message: `Category: ${input.category.join(' › ')}` });
  }

  // Each rule can lose at most WEIGHT.error points; info items cost 1, warnings 2, errors 3.
  const max = res.length * WEIGHT.error || 1;
  const lost = res.reduce((a, r) => a + WEIGHT[r.severity], 0);
  const score = Math.round(100 * (1 - lost / max));
  return { score, results: res, title: t, tags: g, description: d };
}
