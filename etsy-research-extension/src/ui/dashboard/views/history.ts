import { h } from '../../../shared/dom';
import * as repo from '../../../core/storage/repo';
import { fmtDateTime } from '../../../shared/format';
import { card, cardHead, empty, segmented, table, confirmAction } from '../../components';
import { date, exportButtons, pageHead } from './common';
import type { Ctx } from '../main';
import type { HistoryEntry } from '../../../shared/types';

function routeFor(e: HistoryEntry): string | undefined {
  if (!e.url) return undefined;
  if (e.kind === 'search') return `keywords/${encodeURIComponent(repo.termKey(e.label))}`;
  const id = /\/listing\/(\d+)/.exec(e.url)?.[1];
  if (e.kind === 'listing' && id) return `products/${id}`;
  if (e.kind === 'shop') return `competitors/${encodeURIComponent(e.label)}`;
  return undefined;
}

export async function historyView(ctx: Ctx): Promise<Node> {
  const [hist, changes] = await Promise.all([repo.history(), repo.changes()]);
  let kind = 'all';
  const box = h('div');
  const draw = () => {
    const rows = hist.filter((x) => kind === 'all' || x.kind === kind);
    box.replaceChildren(rows.length ? table([
      { key: 'ts', label: 'When', sort: (x) => x.ts, render: (x) => fmtDateTime(x.ts) },
      { key: 'kind', label: 'Type', sort: (x) => x.kind, render: (x) => x.kind },
      { key: 'label', label: 'Item', sort: (x) => x.label, render: (x) => { const r = routeFor(x); return r ? h('a', { href: `#${r}` }, x.label) : x.label; } },
      { key: 'url', label: '', render: (x) => (x.url ? h('a', { href: x.url, target: '_blank', rel: 'noopener' }, 'Etsy ↗') : '') },
    ], rows, { sortKey: 'ts', caption: 'Research history' }) : empty('No history.'));
  };
  draw();
  return h('div', { class: 'stack' },
    pageHead('History', 'Pages you researched and the changes detected between visits.',
      exportButtons('history', () => [
        { name: 'History', rows: [['Date', 'Type', 'Item', 'URL'], ...hist.map((x) => [new Date(x.ts).toISOString(), x.kind, x.label, x.url])] },
        { name: 'Changes', rows: [['Date', 'Entity', 'Key', 'Field', 'Before', 'After'], ...changes.map((c) => [date(c.ts), c.entity, c.key, c.field, c.before, c.after])] },
      ]),
      h('button', { class: 'btn small danger', type: 'button', onclick: async () => { if (confirmAction('Clear research history? Products, keywords and shops are kept.')) { await repo.clearHistory(); ctx.rerender(); } } }, 'Clear history')),
    card(cardHead('Research history', segmented([{ value: 'all', label: 'All' }, { value: 'search', label: 'Searches' }, { value: 'listing', label: 'Listings' }, { value: 'shop', label: 'Shops' }], kind, (v) => { kind = v; draw(); }, 'Type')), box),
    card('Detected changes', changes.length ? table([
      { key: 'ts', label: 'When', sort: (c) => c.ts, render: (c) => fmtDateTime(c.ts) },
      { key: 'e', label: 'Item', sort: (c) => c.key, render: (c) => h('a', { href: c.entity === 'shop' ? `#competitors/${encodeURIComponent(c.key)}` : `#products/${c.key}` }, c.entity === 'shop' ? c.key : `Listing ${c.key}`) },
      { key: 'f', label: 'Field', sort: (c) => c.field, render: (c) => c.field },
      { key: 'b', label: 'Before', render: (c) => c.before ?? '' },
      { key: 'a', label: 'After', render: (c) => c.after ?? '' },
    ], changes, { sortKey: 'ts', limit: 100, caption: 'Changes' }) : empty('No changes detected yet.')),
  );
}
