import { h, svg } from '../shared/dom';
import type { HistogramBin } from '../core/stats';
import { fmtCompact, fmtDate } from '../shared/format';

export type Prov = 'verified' | 'observed' | 'estimated' | 'unavailable';

const PROV_TEXT: Record<Prov, [string, string]> = {
  verified: ['Verified', 'Shown by Etsy on a page you opened'],
  observed: ['Observed', 'Calculated from differences between your own recorded snapshots'],
  estimated: ['≈ Estimated', 'Produced by a statistical model. Not an Etsy figure.'],
  unavailable: ['Not available', 'Etsy does not show this publicly'],
};

export function prov(p: Prov) {
  const [t, title] = PROV_TEXT[p];
  return h('span', { class: `badge ${p}`, title }, t);
}

export function grade(g?: string) {
  if (!g) return null;
  return h('span', { class: `grade ${g}`, title: `Confidence grade ${g} (A = best data, D = weakest)` }, g);
}

export function kpi(label: string, value: string | Node, opts: { sub?: string | Node; prov?: Prov; title?: string } = {}) {
  return h('div', { class: 'kpi', title: opts.title }, h('span', { class: 'label' }, label, opts.prov ? prov(opts.prov) : null), h('span', { class: 'value' }, value), opts.sub ? h('span', { class: 'sub' }, opts.sub) : null);
}

export function explain(summary: string, lines: (string | Node)[]) {
  return h('details', { class: 'explain' }, h('summary', null, summary), h('div', null, h('ul', null, lines.map((l) => h('li', null, l)))));
}

export function empty(text: string, action?: Node) {
  return h('div', { class: 'empty' }, h('p', null, text), action ? h('div', { style: 'margin-top:8px' }, action) : null);
}

export function card(title: string | Node | null, ...children: (Node | null | undefined | false)[]) {
  return h('section', { class: 'card' }, title ? (typeof title === 'string' ? h('h2', null, title) : title) : null, ...children);
}

export function cardHead(title: string, ...right: (Node | null)[]) {
  return h('div', { class: 'card-head' }, h('h2', null, title), h('div', { class: 'row' }, ...right));
}

export function meter(v: number, label: string) {
  const pct = Math.max(0, Math.min(100, v * 100));
  return h('div', { class: 'meter', role: 'meter', 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-valuenow': Math.round(pct), 'aria-label': label }, h('span', { style: `width:${pct}%` }));
}

let toastTimer: number | undefined;
export function toast(msg: string) {
  document.querySelectorAll('.toast').forEach((t) => t.remove());
  const t = h('div', { class: 'toast', role: 'status' }, msg);
  document.body.appendChild(t);
  clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => t.remove(), 2600);
}

export function download(filename: string, data: BlobPart, mime: string) {
  const url = URL.createObjectURL(new Blob([data], { type: mime }));
  const a = h('a', { href: url, download: filename });
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

export function segmented<T extends string>(options: { value: T; label: string; disabled?: boolean; title?: string }[], current: T, onChange: (v: T) => void, label: string) {
  const g = h('div', { class: 'btn-group', role: 'group', 'aria-label': label });
  for (const o of options) {
    g.appendChild(h('button', { type: 'button', 'aria-pressed': String(o.value === current), disabled: o.disabled, title: o.title, onclick: () => onChange(o.value) }, o.label));
  }
  return g;
}

/* ---------------- sortable table ---------------- */

export interface Column<T> {
  key: string;
  label: string;
  num?: boolean;
  sort?: (row: T) => number | string | undefined;
  render: (row: T) => Node | string;
  title?: string;
  class?: string;
}

export function table<T>(cols: Column<T>[], rows: T[], opts: { onRow?: (r: T) => void; sortKey?: string; sortDir?: 1 | -1; limit?: number; caption?: string } = {}) {
  let sortKey = opts.sortKey;
  let dir: 1 | -1 = opts.sortDir ?? -1;
  let limit = opts.limit ?? 200;
  const wrap = h('div', { class: 'stack-sm' });
  const draw = () => {
    const col = cols.find((c) => c.key === sortKey);
    const sorted = col?.sort
      ? [...rows].sort((a, b) => {
          const x = col.sort!(a);
          const y = col.sort!(b);
          if (x === undefined && y === undefined) return 0;
          if (x === undefined) return 1;
          if (y === undefined) return -1;
          return (x < y ? -1 : x > y ? 1 : 0) * dir;
        })
      : rows;
    const thead = h('thead', null, h('tr', null, cols.map((c) => {
      const active = c.key === sortKey;
      const ariaSort = active ? (dir === 1 ? 'ascending' : 'descending') : 'none';
      return h('th', { class: c.num ? 'num' : '', title: c.title, 'aria-sort': c.sort ? ariaSort : undefined, scope: 'col' },
        c.sort ? h('button', { type: 'button', onclick: () => { if (sortKey === c.key) dir = (dir * -1) as 1 | -1; else { sortKey = c.key; dir = c.num ? -1 : 1; } draw(); } }, c.label, active ? (dir === 1 ? ' ▲' : ' ▼') : '') : c.label);
    })));
    const tbody = h('tbody', null, sorted.slice(0, limit).map((r) =>
      h('tr', { class: opts.onRow ? 'clickable' : '', tabindex: opts.onRow ? 0 : undefined, onclick: opts.onRow ? () => opts.onRow!(r) : undefined, onkeydown: opts.onRow ? (e: KeyboardEvent) => { if (e.key === 'Enter') opts.onRow!(r); } : undefined },
        cols.map((c) => h('td', { class: [c.num ? 'num' : '', c.class ?? ''].join(' ').trim() }, c.render(r))))));
    wrap.replaceChildren(...([
      h('div', { class: 'table-wrap' }, h('table', { class: 'data' }, opts.caption ? h('caption', { class: 'sr-only' }, opts.caption) : null, thead, tbody)),
      sorted.length > limit ? h('div', { class: 'row' }, h('small', null, `Showing ${limit} of ${sorted.length}`), h('button', { class: 'btn small', type: 'button', onclick: () => { limit += 200; draw(); } }, 'Show more')) : null,
    ].filter(Boolean) as Node[]));
  };
  draw();
  return wrap;
}

/* ---------------- charts (plain SVG) ---------------- */

export interface Pt { t: number; v: number }

export function lineChart(points: Pt[], opts: { height?: number; label: string; yFormat?: (n: number) => string; step?: boolean } = { label: 'chart' }) {
  const W = 600;
  const H = opts.height ?? 180;
  const pad = { l: 44, r: 10, t: 10, b: 22 };
  const yf = opts.yFormat ?? fmtCompact;
  if (points.length === 0) return empty('No data recorded for this period yet.');
  const xs = points.map((p) => p.t);
  const ys = points.map((p) => p.v);
  const firstT = Math.min(...xs);
  const lastT = Math.max(...xs);
  let x0 = firstT;
  let x1 = lastT;
  if (x0 === x1) { x0 -= 43_200_000; x1 += 43_200_000; }
  let y0 = Math.min(...ys);
  let y1 = Math.max(...ys);
  if (y0 === y1) { y0 = y0 === 0 ? 0 : y0 * 0.9; y1 = y1 === 0 ? 1 : y1 * 1.1; }
  const X = (t: number) => pad.l + ((t - x0) / (x1 - x0)) * (W - pad.l - pad.r);
  const Y = (v: number) => pad.t + (1 - (v - y0) / (y1 - y0)) * (H - pad.t - pad.b);
  const ticks = [y0, (y0 + y1) / 2, y1];
  let d = '';
  points.forEach((p, i) => {
    if (i === 0) d += `M${X(p.t)},${Y(p.v)}`;
    else if (opts.step) d += `H${X(p.t)}V${Y(p.v)}`;
    else d += `L${X(p.t)},${Y(p.v)}`;
  });
  const s = svg('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': `${opts.label}: ${points.length} data points from ${fmtDate(firstT)} to ${fmtDate(lastT)}` },
    ...ticks.map((t) => svg('g', {}, svg('line', { class: 'grid-line', x1: pad.l, x2: W - pad.r, y1: Y(t), y2: Y(t) }), svg('text', { x: pad.l - 6, y: Y(t) + 3, 'text-anchor': 'end' }, yf(t)))),
    svg('text', { x: pad.l, y: H - 4 }, fmtDate(firstT)),
    firstT === lastT ? svg('text', { x: W - pad.r, y: H - 4, 'text-anchor': 'end' }, '1 data point so far') : svg('text', { x: W - pad.r, y: H - 4, 'text-anchor': 'end' }, fmtDate(lastT)),
    svg('path', { class: 'line', d }),
    ...points.map((p) => svg('circle', { class: 'dot', cx: X(p.t), cy: Y(p.v), r: points.length > 60 ? 1.5 : 3 }, svg('title', {}, `${fmtDate(p.t)}: ${yf(p.v)}`))),
  );
  return h('div', { class: 'chart' }, s);
}

export function histogramChart(bins: HistogramBin[], opts: { label: string; highlight?: number; xFormat?: (n: number) => string; height?: number }) {
  if (!bins.length) return empty('Not enough values for a distribution.');
  const W = 600;
  const H = opts.height ?? 160;
  const pad = { l: 30, r: 10, t: 8, b: 22 };
  const xf = opts.xFormat ?? ((n: number) => n.toFixed(0));
  const max = Math.max(...bins.map((b) => b.count));
  const bw = (W - pad.l - pad.r) / bins.length;
  const s = svg('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': `${opts.label}: ${bins.length} bins` },
    svg('line', { class: 'grid-line', x1: pad.l, x2: W - pad.r, y1: H - pad.b, y2: H - pad.b }),
    svg('text', { x: pad.l - 4, y: pad.t + 8, 'text-anchor': 'end' }, String(max)),
    ...bins.map((b, i) => {
      const bh = max ? (b.count / max) * (H - pad.t - pad.b) : 0;
      const hl = opts.highlight !== undefined && opts.highlight >= b.from && (opts.highlight < b.to || i === bins.length - 1);
      return svg('rect', { class: `bar${hl ? ' hl' : ''}`, x: pad.l + i * bw + 1, y: H - pad.b - bh, width: Math.max(1, bw - 2), height: bh, rx: 2 }, svg('title', {}, `${xf(b.from)}–${xf(b.to)}: ${b.count}`));
    }),
    svg('text', { x: pad.l, y: H - 6 }, xf(bins[0].from)),
    svg('text', { x: W - pad.r, y: H - 6, 'text-anchor': 'end' }, xf(bins[bins.length - 1].to)),
  );
  return h('div', { class: 'chart' }, s);
}

export function barList(items: { label: string; value: number; display?: string }[], label: string) {
  const max = Math.max(1, ...items.map((i) => i.value));
  return h('div', { class: 'stack-sm', role: 'list', 'aria-label': label }, items.map((i) =>
    h('div', { role: 'listitem', class: 'stack-sm', style: 'gap:2px' }, h('div', { class: 'row between' }, h('span', { class: 'text-2', style: 'font-size:12px' }, i.label), h('span', { class: 'mono' }, i.display ?? String(i.value))), meter(i.value / max, i.label))));
}

export function confirmAction(message: string): boolean {
  return window.confirm(message);
}
