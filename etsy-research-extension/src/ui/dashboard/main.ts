import { h, mount } from '../../shared/dom';
import { getSettings, onSettingsChanged, saveSettings } from '../../shared/settings';
import type { Settings } from '../../shared/types';
import * as repo from '../../core/storage/repo';
import { normalise } from '../../core/text';
import { overviewView, welcomeView } from './views/overview';
import { productDetailView, productsView } from './views/products';
import { keywordCompareView, keywordDetailView, keywordsView } from './views/keywords';
import { competitorCompareView, competitorDetailView, competitorsView } from './views/competitors';
import { seoView } from './views/seo';
import { trendsView } from './views/trends';
import { savedView } from './views/saved';
import { historyView } from './views/history';
import { diagnosticsView, settingsView } from './views/settings';

export interface Ctx {
  settings: Settings;
  go: (route: string) => void;
  rerender: () => void;
  updateSettings: (patch: Partial<Settings>) => Promise<void>;
}

type View = (params: string[], ctx: Ctx, query: URLSearchParams) => Promise<Node> | Node;

const ROUTES: { prefix: string; view: View; nav?: string }[] = [
  { prefix: 'welcome', view: welcomeView },
  { prefix: 'overview', view: overviewView, nav: 'Overview' },
  { prefix: 'products', view: (p, c, q) => (p[0] ? productDetailView(p[0], c) : productsView(c, q)), nav: 'Products' },
  { prefix: 'keywords/compare', view: (_p, c, q) => keywordCompareView(c, q) },
  { prefix: 'keywords', view: (p, c) => (p[0] ? keywordDetailView(p[0], c) : keywordsView(c)), nav: 'Keywords' },
  { prefix: 'competitors/compare', view: (_p, c, q) => competitorCompareView(c, q) },
  { prefix: 'competitors', view: (p, c) => (p[0] ? competitorDetailView(p[0], c) : competitorsView(c)), nav: 'Competitors' },
  { prefix: 'seo', view: (p, c) => seoView(p, c), nav: 'SEO tools' },
  { prefix: 'trends', view: (_p, c) => trendsView(c), nav: 'Trends & calendar' },
  { prefix: 'saved', view: (_p, c) => savedView(c), nav: 'Saved' },
  { prefix: 'history', view: (_p, c) => historyView(c), nav: 'History' },
  { prefix: 'settings', view: (_p, c) => settingsView(c), nav: 'Settings' },
  { prefix: 'diagnostics', view: (_p, c) => diagnosticsView(c), nav: 'Page diagnostics' },
];

const main = document.getElementById('main')!;
const nav = document.getElementById('nav')!;
let ctx: Ctx;

function applyTheme(s: Settings) {
  if (s.theme === 'system') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme', s.theme);
  (document.getElementById('theme') as HTMLSelectElement).value = s.theme;
}

function parse(): { route: (typeof ROUTES)[number]; params: string[]; query: URLSearchParams } {
  const raw = location.hash.slice(1) || 'overview';
  const [path, qs] = raw.split('?');
  const route = ROUTES.find((r) => path === r.prefix || path.startsWith(r.prefix + '/')) ?? ROUTES[1];
  const rest = path === route.prefix ? '' : path.slice(route.prefix.length + 1);
  const params = rest ? rest.split('/').map((x) => decodeURIComponent(x)) : [];
  return { route, params, query: new URLSearchParams(qs ?? '') };
}

async function renderNav(current: string) {
  const [l, k, s] = await Promise.all([repo.listings(), repo.keywords(), repo.shops()]);
  const counts: Record<string, number> = { Products: l.length, Keywords: k.length, Competitors: s.filter((x) => x.tracked).length };
  mount(nav, ROUTES.filter((r) => r.nav).map((r, i) => [
    i === 6 || i === 8 ? h('div', { class: 'sep', role: 'separator' }) : null,
    h('a', { href: `#${r.prefix}`, 'aria-current': current === r.prefix ? 'page' : undefined, onclick: () => closeNav() }, r.nav!, counts[r.nav!] !== undefined ? h('span', { class: 'count' }, String(counts[r.nav!])) : null),
  ]));
}

let renderSeq = 0;
async function render() {
  const seq = ++renderSeq;
  const { route, params, query } = parse();
  renderNav(route.prefix.split('/')[0]);
  try {
    const node = await route.view(params, ctx, query);
    if (seq !== renderSeq) return;
    mount(main, node);
  } catch (e) {
    console.warn(e);
    if (seq !== renderSeq) return;
    mount(main, h('div', { class: 'notice warn' }, `This view could not be displayed: ${String((e as Error).message ?? e)}`));
  }
  document.title = `${route.nav ?? 'Shoplens'} · Shoplens Research`;
}

function closeNav() {
  nav.classList.remove('open');
  document.querySelector('.nav-toggle')?.setAttribute('aria-expanded', 'false');
}

function setupSearch() {
  const form = document.querySelector('.global-search') as HTMLFormElement;
  const input = document.getElementById('q') as HTMLInputElement;
  let box: HTMLElement | undefined;
  const close = () => { box?.remove(); box = undefined; };
  input.addEventListener('input', async () => {
    const q = normalise(input.value);
    close();
    if (q.length < 2) return;
    const [l, k, s] = await Promise.all([repo.listings(), repo.keywords(), repo.shops()]);
    const hits = [
      ...k.filter((x) => x.term.includes(q)).slice(0, 6).map((x) => ({ label: `Keyword · ${x.term}`, route: `keywords/${encodeURIComponent(x.term)}` })),
      ...s.filter((x) => x.shopName.toLowerCase().includes(q)).slice(0, 6).map((x) => ({ label: `Shop · ${x.shopName}`, route: `competitors/${encodeURIComponent(x.shopName)}` })),
      ...l.filter((x) => normalise(x.title).includes(q)).slice(0, 10).map((x) => ({ label: `Product · ${x.title}`, route: `products/${x.listingId}` })),
    ];
    box = h('div', { class: 'search-results', role: 'listbox' }, hits.length ? hits.map((x) => h('a', { href: `#${x.route}`, role: 'option', onclick: () => { close(); input.value = ''; } }, x.label)) : h('div', { class: 'empty', style: 'border:0' }, 'No matches in your saved data'));
    form.appendChild(box);
  });
  form.addEventListener('submit', (e) => { e.preventDefault(); (box?.querySelector('a') as HTMLAnchorElement | null)?.click(); });
  document.addEventListener('click', (e) => { if (!form.contains(e.target as Node)) close(); });
  input.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
}

async function boot() {
  const settings = await getSettings();
  ctx = {
    settings,
    go: (r) => { location.hash = r; },
    rerender: () => render(),
    updateSettings: async (patch) => { ctx.settings = await saveSettings(patch); applyTheme(ctx.settings); },
  };
  applyTheme(settings);
  onSettingsChanged((s) => { ctx.settings = s; applyTheme(s); });
  (document.getElementById('theme') as HTMLSelectElement).addEventListener('change', (e) => ctx.updateSettings({ theme: (e.target as HTMLSelectElement).value as Settings['theme'] }));
  const toggle = document.querySelector('.nav-toggle')!;
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
  });
  if (!settings.onboardingDone && !location.hash.startsWith('#welcome')) location.hash = 'welcome';
  window.addEventListener('hashchange', () => { render(); main.focus({ preventScroll: true }); window.scrollTo(0, 0); });
  setupSearch();
  await render();
}

boot();
