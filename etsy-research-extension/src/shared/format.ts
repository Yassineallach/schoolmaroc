import type { Settings } from './types';

export function fmtNum(v: number | undefined | null, digits = 0): string {
  if (v === undefined || v === null || !Number.isFinite(v)) return '—';
  return v.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 });
}

export function fmtCompact(v: number | undefined | null): string {
  if (v === undefined || v === null || !Number.isFinite(v)) return '—';
  if (Math.abs(v) >= 1e6) return `${(v / 1e6).toFixed(1).replace(/\.0$/, '')}M`;
  if (Math.abs(v) >= 1e4) return `${Math.round(v / 1e3)}k`;
  if (Math.abs(v) >= 1e3) return `${(v / 1e3).toFixed(1).replace(/\.0$/, '')}k`;
  return fmtNum(v, v < 10 ? 1 : 0);
}

export function fmtMoney(v: number | undefined | null, currency?: string, digits = 2): string {
  if (v === undefined || v === null || !Number.isFinite(v)) return '—';
  if (currency && /^[A-Z]{3}$/.test(currency)) {
    try {
      return v.toLocaleString(undefined, { style: 'currency', currency, maximumFractionDigits: digits, minimumFractionDigits: Math.min(digits, v >= 1000 ? 0 : digits) });
    } catch {
      /* unknown code: fall through */
    }
  }
  return `${currency ? currency + ' ' : ''}${fmtNum(v, digits)}`;
}

export function fmtPct(v: number | undefined | null, digits = 0): string {
  if (v === undefined || v === null || !Number.isFinite(v)) return '—';
  return `${(v * 100).toFixed(digits)}%`;
}

export function fmtDate(ts: number | undefined | null): string {
  if (!ts) return '—';
  return new Date(ts).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

export function fmtDateTime(ts: number | undefined | null): string {
  if (!ts) return '—';
  return new Date(ts).toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export function fmtAge(ts: number | undefined, now = Date.now()): string {
  if (!ts) return '—';
  const d = Math.floor((now - ts) / 86_400_000);
  if (d < 1) return 'today';
  if (d < 60) return `${d} d`;
  if (d < 730) return `${Math.round(d / 30.44)} mo`;
  return `${(d / 365.25).toFixed(1)} y`;
}

export function fmtRange(r: { low: number; mid: number; high: number } | undefined, f: (n: number) => string = (n) => fmtNum(n, n < 10 ? 1 : 0)): string {
  if (!r) return '—';
  return `${f(r.mid)} (${f(r.low)}–${f(r.high)})`;
}

/**
 * Converts an amount into the display currency using user-entered rates.
 * fxRates[X] = how many units of X equal 1 unit of the display currency.
 */
export function convert(amount: number | undefined, from: string | undefined, s: Pick<Settings, 'displayCurrency' | 'fxRates'>): { value?: number; currency?: string; converted: boolean } {
  if (amount === undefined) return { converted: false };
  const to = s.displayCurrency;
  if (!to || !from || from === to) return { value: amount, currency: from, converted: false };
  const rate = s.fxRates[from];
  if (!rate || rate <= 0) return { value: amount, currency: from, converted: false };
  return { value: amount / rate, currency: to, converted: true };
}

export function fxFactor(from: string | undefined, s: Pick<Settings, 'displayCurrency' | 'fxRates'>): { factor: number; currency?: string; converted: boolean } {
  const c = convert(1, from, s);
  return { factor: c.value ?? 1, currency: c.currency ?? from, converted: c.converted };
}
