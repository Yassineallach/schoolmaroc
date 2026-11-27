/** Trend engine: time series from the user's own snapshots, plus a computed shopping calendar. */
import { DAY, slope } from './stats';
import type { KeywordSnapshot, Settings } from '../shared/types';

export const PERIODS = [
  { key: '7d', label: '7 days', days: 7 },
  { key: '30d', label: '30 days', days: 30 },
  { key: '90d', label: '90 days', days: 90 },
  { key: '6m', label: '6 months', days: 182 },
  { key: '12m', label: '12 months', days: 365 },
  { key: '24m', label: '24 months', days: 730 },
] as const;

export interface Point { t: number; v: number }

/** A period is "available" only when collected data actually covers at least half of it. */
export function availablePeriods(firstTs: number | undefined, now = Date.now()) {
  return PERIODS.map((p) => ({ ...p, available: firstTs !== undefined && now - firstTs >= p.days * DAY * 0.5 }));
}

export function filterPeriod(points: Point[], days: number, now = Date.now()): Point[] {
  return points.filter((p) => p.t >= now - days * DAY);
}

export type Metric = 'resultCount' | 'demandShare' | 'medianPrice' | 'adShare';

export function keywordSeries(snaps: KeywordSnapshot[], metric: Metric): Point[] {
  return snaps
    .map((s) => {
      const st = s.stats;
      const v = metric === 'resultCount' ? st.resultCount : metric === 'demandShare' ? (st.bestsellerShare + st.popularNowShare) * 100 : metric === 'medianPrice' ? st.medianPrice : st.adShare * 100;
      return v === undefined ? undefined : { t: s.ts, v };
    })
    .filter((p): p is Point => !!p)
    .sort((a, b) => a.t - b.t);
}

export interface Movement {
  term: string;
  checks: number;
  spanDays: number;
  demandChange: number;
  supplyChangePct?: number;
  direction: 'rising' | 'declining' | 'flat';
}

/** Rising / declining terms in the user's own tracked data (never presented as Etsy-wide). */
export function movements(byTerm: Map<string, KeywordSnapshot[]>, minSpanDays = 2): Movement[] {
  const out: Movement[] = [];
  for (const [term, snaps] of byTerm) {
    const s = [...snaps].sort((a, b) => a.ts - b.ts);
    if (s.length < 2) continue;
    const span = (s[s.length - 1].ts - s[0].ts) / DAY;
    if (span < minSpanDays) continue;
    const demand = keywordSeries(s, 'demandShare');
    const sl = slope(demand.map((p) => ({ x: p.t / (30 * DAY), y: p.v })));
    const first = s[0].stats.resultCount;
    const last = s[s.length - 1].stats.resultCount;
    const supply = first && last ? ((last - first) / first) * 100 : undefined;
    const ch = sl ?? 0;
    out.push({ term, checks: s.length, spanDays: span, demandChange: ch, supplyChangePct: supply, direction: ch > 1 ? 'rising' : ch < -1 ? 'declining' : 'flat' });
  }
  return out.sort((a, b) => b.demandChange - a.demandChange);
}

/* ---------- shopping calendar ---------- */

/** Anonymous Gregorian algorithm (Meeus/Jones/Butcher). */
export function easterSunday(year: number): Date {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31);
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(Date.UTC(year, month - 1, day));
}

/** n-th weekday (0=Sun) of month (0-based); n=-1 for last. */
export function nthWeekday(year: number, month: number, weekday: number, n: number): Date {
  if (n > 0) {
    const first = new Date(Date.UTC(year, month, 1));
    const offset = (weekday - first.getUTCDay() + 7) % 7;
    return new Date(Date.UTC(year, month, 1 + offset + (n - 1) * 7));
  }
  const last = new Date(Date.UTC(year, month + 1, 0));
  const offset = (last.getUTCDay() - weekday + 7) % 7;
  return new Date(Date.UTC(year, month, last.getUTCDate() - offset));
}

const addDays = (d: Date, n: number) => new Date(d.getTime() + n * DAY);

export interface ShoppingEvent {
  key: string;
  name: string;
  date: Date;
  /** recommended days before the event to have listings live */
  leadDays: number;
  keywords: string[];
}

export function shoppingEvents(year: number, country: Settings['country']): ShoppingEvent[] {
  const easter = easterSunday(year);
  const thanksgivingUS = nthWeekday(year, 10, 4, 4);
  const mothers =
    country === 'UK' ? addDays(easter, -21) // Mothering Sunday: 4th Sunday of Lent
      : country === 'EU' ? nthWeekday(year, 4, 0, -1) // last Sunday of May (e.g. France)
        : nthWeekday(year, 4, 0, 2); // US, CA, AU: second Sunday of May
  const fathers = country === 'AU' ? nthWeekday(year, 8, 0, 1) : nthWeekday(year, 5, 0, 3);
  const backToSchool =
    country === 'AU' ? new Date(Date.UTC(year, 0, 27)) : country === 'UK' || country === 'EU' ? new Date(Date.UTC(year, 8, 1)) : new Date(Date.UTC(year, 7, 15));
  const ev: ShoppingEvent[] = [
    { key: 'valentines', name: "Valentine's Day", date: new Date(Date.UTC(year, 1, 14)), leadDays: 45, keywords: ['valentine', 'valentines', 'love', 'couple', 'for him', 'for her'] },
    { key: 'easter', name: 'Easter', date: easter, leadDays: 45, keywords: ['easter', 'bunny', 'spring'] },
    { key: 'mothers', name: "Mother's Day", date: mothers, leadDays: 50, keywords: ['mothers day', 'mom', 'mum', 'for mom', 'for mum', 'grandma'] },
    { key: 'fathers', name: "Father's Day", date: fathers, leadDays: 50, keywords: ['fathers day', 'dad', 'for dad', 'grandpa'] },
    { key: 'backtoschool', name: 'Back to School', date: backToSchool, leadDays: 45, keywords: ['back to school', 'teacher', 'school', 'classroom'] },
    { key: 'halloween', name: 'Halloween', date: new Date(Date.UTC(year, 9, 31)), leadDays: 60, keywords: ['halloween', 'spooky', 'witch', 'pumpkin'] },
    { key: 'blackfriday', name: 'Black Friday', date: addDays(thanksgivingUS, 1), leadDays: 30, keywords: ['black friday', 'gift', 'gift for'] },
    { key: 'cybermonday', name: 'Cyber Monday', date: addDays(thanksgivingUS, 4), leadDays: 30, keywords: ['cyber monday', 'gift'] },
    { key: 'christmas', name: 'Christmas', date: new Date(Date.UTC(year, 11, 25)), leadDays: 75, keywords: ['christmas', 'xmas', 'holiday', 'ornament', 'stocking', 'advent'] },
  ];
  if (country === 'US' || country === 'CA') {
    const tg = country === 'CA' ? nthWeekday(year, 9, 1, 2) : thanksgivingUS;
    ev.push({ key: 'thanksgiving', name: 'Thanksgiving', date: tg, leadDays: 45, keywords: ['thanksgiving', 'fall', 'autumn', 'harvest'] });
  }
  return ev.sort((a, b) => a.date.getTime() - b.date.getTime());
}

export interface UpcomingEvent extends ShoppingEvent {
  daysUntil: number;
  listBy: Date;
  status: 'prepare-now' | 'upcoming' | 'too-late' | 'later';
}

export function upcomingEvents(now: Date, country: Settings['country']): UpcomingEvent[] {
  const y = now.getUTCFullYear();
  const all = [...shoppingEvents(y, country), ...shoppingEvents(y + 1, country)];
  const today = Date.UTC(y, now.getUTCMonth(), now.getUTCDate());
  return all
    .filter((e) => e.date.getTime() >= today)
    .slice(0, 12)
    .map((e) => {
      const daysUntil = Math.round((e.date.getTime() - today) / DAY);
      const listBy = addDays(e.date, -e.leadDays);
      const status = daysUntil < 7 ? 'too-late' : listBy.getTime() <= today ? 'prepare-now' : daysUntil <= e.leadDays + 30 ? 'upcoming' : 'later';
      return { ...e, daysUntil, listBy, status };
    });
}

/** Which saved keywords relate to an event (simple phrase containment). */
export function keywordsForEvent(event: ShoppingEvent, terms: string[]): string[] {
  return terms.filter((t) => event.keywords.some((k) => ` ${t.toLowerCase()} `.includes(` ${k} `)));
}
