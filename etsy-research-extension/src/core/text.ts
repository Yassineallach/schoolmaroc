/** Deterministic text utilities: tokenising, n-grams, readability. */

export const STOPWORDS = new Set(
  (
    'a an and are as at be but by for from has have i in into is it its of on or our so ' +
    'that the their this to was we with you your will can x & - | , / + etc'
  ).split(' '),
);

export function normalise(s: string): string {
  return s
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^\p{L}\p{N}'\s-]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function words(s: string): string[] {
  return normalise(s)
    .split(' ')
    .map((w) => w.replace(/^['-]+|['-]+$/g, ''))
    .filter(Boolean);
}

export function contentWords(s: string): string[] {
  return words(s).filter((w) => !STOPWORDS.has(w) && w.length > 1);
}

/** Split an Etsy title into its comma/pipe/dash-separated phrases. */
export function titlePhrases(title: string): string[] {
  return title
    .split(/\s*[,|•·]\s*|\s+[-–—]\s+/)
    .map((p) => normalise(p))
    .filter((p) => p.length > 1);
}

export function ngrams(tokens: string[], n: number): string[] {
  const out: string[] = [];
  for (let i = 0; i + n <= tokens.length; i++) {
    const g = tokens.slice(i, i + n);
    if (STOPWORDS.has(g[0]) || STOPWORDS.has(g[g.length - 1])) continue;
    out.push(g.join(' '));
  }
  return out;
}

export interface PhraseCount {
  phrase: string;
  /** number of documents (titles) containing the phrase */
  docs: number;
  words: number;
}

/**
 * Document-frequency ranking of 1–4 word phrases. Phrases are taken within
 * title segments so "mug, gift for dad" never yields "mug gift".
 */
export function phraseFrequencies(docs: string[], minDocs = 2): PhraseCount[] {
  const counts = new Map<string, number>();
  for (const doc of docs) {
    const seen = new Set<string>();
    for (const seg of titlePhrases(doc)) {
      const toks = words(seg);
      for (let n = 1; n <= 4; n++) for (const g of ngrams(toks, n)) seen.add(g);
    }
    for (const g of seen) counts.set(g, (counts.get(g) ?? 0) + 1);
  }
  const list = [...counts.entries()]
    .filter(([p, c]) => c >= minDocs && !(p.split(' ').length === 1 && STOPWORDS.has(p)))
    .map(([phrase, c]) => ({ phrase, docs: c, words: phrase.split(' ').length }));
  // drop a shorter phrase when a longer phrase containing it has the same frequency
  const result = list.filter(
    (p) => !list.some((q) => q.words > p.words && q.docs === p.docs && ` ${q.phrase} `.includes(` ${p.phrase} `)),
  );
  return result.sort((a, b) => b.docs - a.docs || b.words - a.words || a.phrase.localeCompare(b.phrase));
}

/** English syllable estimate (vowel-group heuristic). */
export function syllables(word: string): number {
  const w = word.toLowerCase().replace(/[^a-z]/g, '');
  if (!w) return 0;
  if (w.length <= 3) return 1;
  const stripped = w.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '').replace(/^y/, '');
  const groups = stripped.match(/[aeiouy]{1,2}/g);
  return Math.max(1, groups ? groups.length : 1);
}

export function sentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+|\n{2,}|\n(?=[-•*])/)
    .map((s) => s.trim())
    .filter((s) => /\p{L}/u.test(s));
}

/** Flesch Reading Ease (higher = easier, 60–70 ≈ plain English). */
export function fleschReadingEase(text: string): number | undefined {
  const sents = sentences(text);
  const ws = words(text).filter((w) => /\p{L}/u.test(w));
  if (!sents.length || ws.length < 10) return undefined;
  const syl = ws.reduce((a, w) => a + syllables(w), 0);
  return 206.835 - 1.015 * (ws.length / sents.length) - 84.6 * (syl / ws.length);
}

export function duplicates<T>(items: T[]): T[] {
  const seen = new Set<T>();
  const dup = new Set<T>();
  for (const i of items) (seen.has(i) ? dup : seen).add(i);
  return [...dup];
}

/** Simple, stable string hash (FNV-1a, 32-bit, hex). */
export function hash(s: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(16).padStart(8, '0');
}

export function containsPhrase(haystack: string, phrase: string): boolean {
  const h = ` ${words(haystack).join(' ')} `;
  const p = words(phrase).join(' ');
  return !!p && h.includes(` ${p} `);
}

/** Character index (in normalised words) of a phrase, or -1. */
export function phrasePosition(haystack: string, phrase: string): number {
  const h = words(haystack).join(' ');
  const p = words(phrase).join(' ');
  if (!p) return -1;
  const re = new RegExp(`(^| )${p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}( |$)`);
  const m = re.exec(h);
  return m ? m.index + (m[1] ? 1 : 0) : -1;
}

/** Simple English plural folding, used only for matching (never for display). */
export function stem(w: string): string {
  if (w.length > 4 && w.endsWith('ies')) return w.slice(0, -3) + 'y';
  if (w.length > 4 && /(ches|shes|sses|xes)$/.test(w)) return w.slice(0, -2);
  if (w.length > 3 && w.endsWith('s') && !w.endsWith('ss')) return w.slice(0, -1);
  return w;
}
