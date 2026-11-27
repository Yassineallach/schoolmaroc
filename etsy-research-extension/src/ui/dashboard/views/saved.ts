import { h } from '../../../shared/dom';
import * as repo from '../../../core/storage/repo';
import { fmtDate, fmtMoney, fmtNum } from '../../../shared/format';
import type { Collection } from '../../../shared/types';
import { card, cardHead, empty, toast, confirmAction } from '../../components';
import { exportButtons, pageHead } from './common';
import type { Ctx } from '../main';

export async function savedView(ctx: Ctx): Promise<Node> {
  const [cols, listings, keywords] = await Promise.all([repo.collections(), repo.listings(), repo.keywords()]);
  const byId = new Map(listings.map((l) => [l.listingId, l]));
  const savedKw = keywords.filter((k) => k.saved);
  const folders = new Map<string, typeof savedKw>();
  for (const k of savedKw) folders.set(k.folder ?? 'Unfiled', [...(folders.get(k.folder ?? 'Unfiled') ?? []), k]);
  const nameIn = h('input', { type: 'text', placeholder: 'New collection name', 'aria-label': 'Collection name' });
  const kindSel = h('select', { 'aria-label': 'Collection type' }, h('option', { value: 'products' }, 'Products'), h('option', { value: 'tags' }, 'Tag set'));

  const colCard = (c: Collection) => card(cardHead(c.name,
      h('small', null, `${c.kind} · ${c.items.length} · ${fmtDate(c.createdAt)}`),
      exportButtons(`collection-${c.name.replace(/\W+/g, '-').toLowerCase()}`, () => [{ name: c.name, rows: c.kind === 'products'
        ? [['Listing ID', 'Title', 'Shop', 'Price', 'Currency', 'Reviews', 'Favourites', 'URL'], ...c.items.map((id) => { const l = byId.get(id); return [id, l?.title, l?.shopName, l?.price, l?.currency, l?.listingReviewCount, l?.favourites, l?.url]; })]
        : [['Tag'], ...c.items.map((t) => [t])] }]),
      h('button', { class: 'btn small danger', type: 'button', onclick: async () => { if (confirmAction(`Delete collection “${c.name}”?`)) { await repo.deleteCollection(c.id); ctx.rerender(); } } }, 'Delete')),
    c.items.length ? (c.kind === 'products'
      ? h('div', { class: 'stack-sm' }, c.items.map((id) => {
        const l = byId.get(id);
        return h('div', { class: 'row between' },
          h('div', { class: 'row grow', style: 'flex-wrap:nowrap' }, l?.imageUrl ? h('img', { class: 'thumb', src: l.imageUrl, alt: '' }) : null, h('a', { class: 'clip', href: `#products/${id}` }, l?.title ?? `Listing ${id} (no longer in your data)`)),
          h('small', null, l ? `${fmtMoney(l.price, l.currency)} · ${fmtNum(l.listingReviewCount)} reviews` : ''),
          h('button', { class: 'btn small', type: 'button', 'aria-label': 'Remove from collection', onclick: async () => { await repo.removeFromCollection(c.id, id); ctx.rerender(); } }, '✕'));
      }))
      : h('div', { class: 'chips' }, c.items.map((t) => h('span', { class: 'chip' }, t))))
      : empty(c.kind === 'products' ? 'Empty. Add products from their detail page or with “Save product” in the Etsy panel.' : 'Empty.'));

  return h('div', { class: 'stack' },
    pageHead('Saved', 'Collections of products, saved tag sets, and keyword folders.'),
    card(null, h('form', { class: 'row', onsubmit: async (e: Event) => {
      e.preventDefault();
      const name = (nameIn as HTMLInputElement).value.trim();
      if (!name) return;
      await repo.saveCollection({ id: `c-${Date.now()}`, name, kind: (kindSel as HTMLSelectElement).value as Collection['kind'], items: [], createdAt: Date.now() });
      toast('Collection created');
      ctx.rerender();
    } }, nameIn, kindSel, h('button', { class: 'btn', type: 'submit' }, 'Create collection'))),
    cols.length ? h('div', { class: 'grid-2' }, cols.sort((a, b) => b.createdAt - a.createdAt).map(colCard)) : empty('No collections yet.'),
    card(cardHead('Keyword folders', h('a', { class: 'btn small', href: '#keywords' }, 'Manage keywords')),
      folders.size ? h('div', { class: 'stack' }, [...folders.entries()].sort().map(([f, ks]) => h('div', { class: 'stack-sm' }, h('h3', null, `${f} (${ks.length})`), h('div', { class: 'chips' }, ks.map((k) => h('a', { class: 'chip', href: `#keywords/${encodeURIComponent(k.term)}` }, k.term))),
        ks.length >= 2 ? h('a', { class: 'btn small', style: 'width:fit-content', href: `#keywords/compare?terms=${encodeURIComponent(ks.slice(0, 6).map((k) => k.term).join('|'))}` }, 'Compare folder') : null)))
        : empty('Save keywords and give them a folder on the keyword page.')),
  );
}
