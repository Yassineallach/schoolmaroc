import { h } from '../../../shared/dom';
import { toCSV, toXLSX, Cell, Sheet } from '../../../core/export';
import { download } from '../../components';

export function pageHead(title: string, desc?: string, ...actions: (Node | null)[]) {
  return h('div', { class: 'page-head' }, h('div', null, h('h1', null, title), desc ? h('p', null, desc) : null), h('div', { class: 'row no-print' }, ...actions));
}

export function back(route: string, label = 'Back') {
  return h('a', { class: 'back no-print', href: `#${route}` }, `← ${label}`);
}

const stamp = () => new Date().toISOString().slice(0, 10);

export function exportButtons(name: string, sheets: () => Promise<Sheet[]> | Sheet[]) {
  return h('div', { class: 'row' },
    h('button', { type: 'button', class: 'btn small', onclick: async () => {
      const s = await sheets();
      download(`${name}-${stamp()}.csv`, toCSV(s[0].rows), 'text/csv;charset=utf-8');
    } }, 'Export CSV'),
    h('button', { type: 'button', class: 'btn small', onclick: async () => {
      const s = await sheets();
      download(`${name}-${stamp()}.xlsx`, toXLSX(s) as BlobPart, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    } }, 'Export Excel'),
  );
}

export function printButton() {
  return h('button', { type: 'button', class: 'btn small', title: 'Print or save as PDF', onclick: () => window.print() }, 'Print report');
}

export const num = (v: number | undefined, d = 2): Cell => (v === undefined || !Number.isFinite(v) ? '' : Math.round(v * 10 ** d) / 10 ** d);
export const date = (ts?: number): Cell => (ts ? new Date(ts).toISOString().slice(0, 10) : '');

export function field(label: string, input: HTMLElement, hint?: string) {
  return h('label', { class: 'field' }, label, input, hint ? h('small', null, hint) : null);
}

export function input(attrs: Record<string, unknown>) {
  return h('input', { type: 'text', ...attrs });
}
