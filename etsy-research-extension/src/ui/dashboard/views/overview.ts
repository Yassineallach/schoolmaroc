import { h } from '../../../shared/dom';
import * as repo from '../../../core/storage/repo';
import { observedShopVelocity } from '../../../core/sales';
import { upcomingEvents } from '../../../core/trends';
import { fmtDate, fmtDateTime, fmtNum } from '../../../shared/format';
import { card, cardHead, empty, kpi, prov } from '../../components';
import { pageHead } from './common';
import type { Ctx } from '../main';

export async function welcomeView(_p: string[], ctx: Ctx): Promise<Node> {
  const on = ctx.settings.pageReading;
  return h('div', { class: 'stack', style: 'max-width:760px' },
    pageHead('Welcome to Shoplens Research', 'A local research workspace for Etsy sellers. No account, no subscription, no AI and no external APIs.'),
    card('How it collects data',
      h('div', { class: 'stack' },
        h('p', null, 'Shoplens reads only the Etsy pages you open yourself: search results, listing pages and shop pages. It never loads Etsy pages in the background, never crawls, and never sends your data anywhere. Everything is stored in this browser.'),
        h('p', null, 'Every figure carries a label:'),
        h('div', { class: 'stack-sm' },
          h('div', { class: 'row' }, prov('verified'), h('span', null, 'Etsy displays it on a page you opened (for example a shop’s sales counter).')),
          h('div', { class: 'row' }, prov('observed'), h('span', null, 'The difference between two of your own visits (for example sales made between them).')),
          h('div', { class: 'row' }, prov('estimated'), h('span', null, 'A documented statistical model. Each estimate shows its method, range and confidence grade.')),
        ),
        h('div', { class: 'notice warn' }, 'Etsy’s terms limit automated collection of its data. Page reading is passive: it only reads what your browser already shows. You decide whether to turn it on, and you can turn it off at any time in Settings.'),
      ),
    ),
    card('Turn on page reading',
      h('div', { class: 'stack' },
        h('label', { class: 'row' },
          h('input', { type: 'checkbox', checked: on, id: 'pr', onchange: async (e: Event) => ctx.updateSettings({ pageReading: (e.target as HTMLInputElement).checked }) }),
          h('span', null, 'Read the Etsy pages I open and save the data locally')),
        h('div', { class: 'row' },
          h('button', { class: 'btn primary', type: 'button', onclick: async () => {
            const cb = document.getElementById('pr') as HTMLInputElement;
            await ctx.updateSettings({ onboardingDone: true, pageReading: cb.checked });
            ctx.go('overview');
          } }, 'Continue'),
          h('small', null, 'Afterwards, open etsy.com and search as usual. A small “SL” button appears in the bottom-right corner.')),
      ),
    ),
    h('small', null, 'The term "Etsy" is a trademark of Etsy, Inc. Shoplens Research is not endorsed by or affiliated with Etsy, Inc.'),
  );
}

export async function overviewView(_p: string[], ctx: Ctx): Promise<Node> {
  const [listings, keywords, shops, changes, history, shopSnaps] = await Promise.all([repo.listings(), repo.keywords(), repo.shops(), repo.changes(), repo.history(), repo.allShopSnaps()]);
  const tracked = shops.filter((s) => s.tracked);
  const events = upcomingEvents(new Date(), ctx.settings.country).filter((e) => e.status !== 'later').slice(0, 4);
  const snapsBy = new Map<string, typeof shopSnaps>();
  for (const s of shopSnaps) snapsBy.set(s.shopName, [...(snapsBy.get(s.shopName) ?? []), s]);

  return h('div', { class: 'stack' },
    pageHead('Overview', 'A summary of the research you have collected on this device.'),
    !ctx.settings.pageReading ? h('div', { class: 'notice warn' }, 'Page reading is off, so nothing new is being collected. ', h('a', { href: '#settings' }, 'Turn it on in Settings.')) : null,
    h('div', { class: 'grid' },
      card(null, kpi('Products recorded', fmtNum(listings.length), { sub: `${listings.filter((l) => l.detailed).length} with full listing data` })),
      card(null, kpi('Keywords researched', fmtNum(keywords.length), { sub: `${keywords.filter((k) => k.saved).length} saved` })),
      card(null, kpi('Shops recorded', fmtNum(shops.length), { sub: `${tracked.length} tracked` })),
      card(null, kpi('Changes detected', fmtNum(changes.length), { sub: changes[0] ? `latest ${fmtDate(changes[0].ts)}` : 'none yet' })),
    ),
    !listings.length && !keywords.length ? card('Getting started', h('ol', { style: 'margin:0;padding-left:18px' },
      h('li', null, 'Open etsy.com and search for a product idea. Shoplens records the results page.'),
      h('li', null, 'Open a few listings. Shoplens records reviews, the shop sales counter, favourites and the dates shown.'),
      h('li', null, 'Open competitor shop pages and click “Track shop”. Visit again later to measure their sales and see listing changes.'),
    )) : null,
    h('div', { class: 'grid-2' },
      card(cardHead('Tracked shops', h('a', { href: '#competitors', class: 'btn small' }, 'All shops')),
        tracked.length ? h('div', { class: 'stack-sm' }, tracked.slice(0, 8).map((s) => {
          const v = observedShopVelocity(snapsBy.get(s.shopName) ?? []);
          return h('div', { class: 'row between' }, h('a', { href: `#competitors/${encodeURIComponent(s.shopName)}` }, s.shopName),
            h('span', { class: 'row' }, v ? [h('span', { class: 'mono' }, `${fmtNum(v.perDay, 1)} sales/day`), prov('observed')] : h('small', null, `${fmtNum(s.sales)} lifetime sales · last visit ${fmtDate(s.lastSeen)}`)));
        })) : empty('No tracked shops. Open a shop page on Etsy and click “Track shop”.')),
      card(cardHead('Shopping calendar', h('a', { href: '#trends', class: 'btn small' }, 'Calendar')),
        events.length ? h('div', { class: 'stack-sm' }, events.map((e) => h('div', { class: 'row between' }, h('span', null, `${e.name} · ${fmtDate(e.date.getTime())}`), h('span', { class: `badge ${e.status === 'prepare-now' ? 'warn' : e.status === 'too-late' ? 'err' : 'neutral'}` }, e.status === 'prepare-now' ? 'List now' : e.status === 'too-late' ? 'Very close' : `in ${e.daysUntil} days`)))) : empty('No events within the planning window.')),
      card(cardHead('Recent changes', h('a', { href: '#history', class: 'btn small' }, 'History')),
        changes.length ? h('div', { class: 'stack-sm' }, changes.slice(0, 8).map((c) => h('div', { class: 'row between' }, h('span', { class: 'grow', style: 'font-size:13px' }, `${c.entity === 'shop' ? c.key : `#${c.key}`}: ${c.field} ${c.before ? `${c.before} → ` : ''}${c.after ?? ''}`), h('small', null, fmtDate(c.ts))))) : empty('Changes appear when you revisit shops and listings.')),
      card(cardHead('Recently viewed'),
        history.length ? h('div', { class: 'stack-sm' }, history.slice(0, 8).map((x) => h('div', { class: 'row between' }, h('span', { class: 'grow', style: 'font-size:13px' }, `${x.kind}: ${x.label}`), h('small', null, fmtDateTime(x.ts))))) : empty('Nothing yet.')),
    ),
  );
}
