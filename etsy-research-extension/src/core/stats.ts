/** Pure statistical helpers. No browser APIs. */

export function isNum(v: unknown): v is number {
  return typeof v === 'number' && Number.isFinite(v);
}

export function nums(values: (number | undefined | null)[]): number[] {
  return values.filter(isNum);
}

export function sum(values: number[]): number {
  return values.reduce((a, b) => a + b, 0);
}

export function mean(values: number[]): number | undefined {
  return values.length ? sum(values) / values.length : undefined;
}

/** Linear-interpolated quantile (type 7, same as Excel PERCENTILE.INC). */
export function quantile(values: number[], q: number): number | undefined {
  if (!values.length) return undefined;
  const s = [...values].sort((a, b) => a - b);
  const pos = (s.length - 1) * Math.min(1, Math.max(0, q));
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  return s[lo] + (s[hi] - s[lo]) * (pos - lo);
}

export const median = (v: number[]) => quantile(v, 0.5);

export function stdev(values: number[]): number | undefined {
  const m = mean(values);
  if (m === undefined || values.length < 2) return undefined;
  return Math.sqrt(sum(values.map((v) => (v - m) ** 2)) / (values.length - 1));
}

/** Herfindahl–Hirschman index of shares, 0..1 (1 = one shop owns every result). */
export function herfindahl(keys: string[]): number {
  if (!keys.length) return 0;
  const counts = new Map<string, number>();
  for (const k of keys) counts.set(k, (counts.get(k) ?? 0) + 1);
  let h = 0;
  for (const c of counts.values()) h += (c / keys.length) ** 2;
  return h;
}

export function jaccard<T>(a: Iterable<T>, b: Iterable<T>): number {
  const A = new Set(a);
  const B = new Set(b);
  if (!A.size && !B.size) return 0;
  let inter = 0;
  for (const x of A) if (B.has(x)) inter++;
  return inter / (A.size + B.size - inter);
}

/** Approximate 90% interval for a Poisson count (normal approximation with continuity floor). */
export function poissonInterval(count: number, z = 1.645): [number, number] {
  if (count <= 0) return [0, z * z];
  const sd = Math.sqrt(count);
  return [Math.max(0, count - z * sd), count + z * sd];
}

/** Ordinary least squares slope of y over x. */
export function slope(points: { x: number; y: number }[]): number | undefined {
  if (points.length < 2) return undefined;
  const mx = mean(points.map((p) => p.x))!;
  const my = mean(points.map((p) => p.y))!;
  let num = 0;
  let den = 0;
  for (const p of points) {
    num += (p.x - mx) * (p.y - my);
    den += (p.x - mx) ** 2;
  }
  return den === 0 ? undefined : num / den;
}

export interface HistogramBin {
  from: number;
  to: number;
  count: number;
}

/** Equal-width histogram; bin count from the Freedman–Diaconis rule, clamped to [4, 20]. */
export function histogram(values: number[], forcedBins?: number): HistogramBin[] {
  if (!values.length) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) return [{ from: min, to: max, count: values.length }];
  let bins = forcedBins;
  if (!bins) {
    const iqr = (quantile(values, 0.75) ?? 0) - (quantile(values, 0.25) ?? 0);
    const width = iqr > 0 ? (2 * iqr) / Math.cbrt(values.length) : (max - min) / 8;
    bins = Math.round((max - min) / width);
  }
  bins = Math.min(20, Math.max(4, bins));
  const width = (max - min) / bins;
  const out: HistogramBin[] = Array.from({ length: bins }, (_, i) => ({
    from: min + i * width,
    to: min + (i + 1) * width,
    count: 0,
  }));
  for (const v of values) {
    const idx = Math.min(bins - 1, Math.floor((v - min) / width));
    out[idx].count++;
  }
  return out;
}

/** Percentile rank of value within values, 0..100. */
export function percentileRank(values: number[], value: number): number | undefined {
  if (!values.length) return undefined;
  const below = values.filter((v) => v < value).length;
  const equal = values.filter((v) => v === value).length;
  return ((below + equal / 2) / values.length) * 100;
}

export function clamp(v: number, lo = 0, hi = 1): number {
  return Math.min(hi, Math.max(lo, v));
}

/** Map x onto 0..1 with a log scale between lo and hi. */
export function logScale(x: number, lo: number, hi: number): number {
  if (x <= lo) return 0;
  if (x >= hi) return 1;
  return (Math.log10(x) - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo));
}

export const DAY = 86_400_000;
