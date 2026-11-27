import { h } from '../../../shared/dom';
import * as repo from '../../../core/storage/repo';
import { analyseDescription, analyseTags, analyseTitle, auditListing, Audit, LIMITS } from '../../../core/seo';
import { normalise } from '../../../core/text';
import { fmtNum } from '../../../shared/format';
import type { Collection, ListingRecord } from '../../../shared/types';
import { card, cardHead, empty, segmented, toast } from '../../components';
import { pageHead } from './common';
import type { Ctx } from '../main';

type Tab = 'audit' | 'title' | 'tags' | 'description' | 'compare';
const TABS: { value: Tab; label: string }[] = [
  { value: 'audit', label: 'Listing audit' }, { value: 'title', label: 'Title' }, { value: 'tags', label: 'Tags' },
  { value: 'description', label: 'Description' }, { value: 'compare', label: 'Compare listings' },
];

/** Working draft shared by the tools while the dashboard is open. */
const draft = { title: '', tags: Array<string>(13).fill(''), description: '', keywords: '', imageCount: '' };

const kwList = () => draft.keywords.split(',').map((k) => k.trim()).filter(Boolean);

function loadListing(l: ListingRecord) {
  draft.title = l.title;
  draft.tags = [...l.relatedTerms.slice(0, 13), ...Array(13).fill('')].slice(0, 13);
  draft.description = l.description ?? '';
  draft.imageCount = l.imageCount !== undefined ? String(l.imageCount) : '';
  if (!draft.keywords && l.searchQueries.length) draft.keywords = l.searchQueries[l.searchQueries.length - 1];
}

function rules(a: Audit) {
  const order = { error: 0, warning: 1, info: 2, pass: 3 };
  return h('div', null, [...a.results].sort((x, y) => order[x.severity] - order[y.severity]).map((r) =>
    h('div', { class: 'rule' }, h('span', { class: `sev ${r.severity}` }, r.severity), h('div', null, h('div', null, h('span', { class: 'mono muted' }, `${r.id} `), r.message), r.detail ? h('small', null, r.detail) : null))));
}

function listingPicker(listings: ListingRecord[], onPick: (l: ListingRecord) => void, label = 'Load a recorded listing…') {
  return h('select', { 'aria-label': label, onchange: (e: Event) => { const l = listings.find((x) => x.listingId === (e.target as HTMLSelectElement).value); if (l) onPick(l); } },
    h('option', { value: '' }, label), listings.filter((l) => l.detailed).sort((a, b) => b.lastSeen - a.lastSeen).slice(0, 300).map((l) => h('option', { value: l.listingId }, `${l.title.slice(0, 70)}${l.shopName ? ` · ${l.shopName}` : ''}`)));
}

function keywordsField(onInput: () => void) {
  return h('label', { class: 'field grow' }, 'Target keywords (comma-separated, most important first)',
    h('input', { type: 'text', value: draft.keywords, placeholder: 'e.g. personalized mug, gift for dad', oninput: (e: Event) => { draft.keywords = (e.target as HTMLInputElement).value; onInput(); } }));
}

export async function seoView(params: string[], ctx: Ctx): Promise<Node> {
  const tab = (TABS.find((t) => t.value === params[0])?.value ?? 'audit') as Tab;
  const listings = await repo.listings();
  if (tab === 'audit' && params[1]) {
    const l = listings.find((x) => x.listingId === params[1]);
    if (l) loadListing(l);
  }
  const body = tab === 'audit' ? auditTab(listings, ctx) : tab === 'title' ? titleTab() : tab === 'tags' ? await tagsTab(listings) : tab === 'description' ? descriptionTab() : compareTab(listings);
  return h('div', { class: 'stack' },
    pageHead('SEO tools', 'Rule-based checks for titles, tags and descriptions. Every rule is deterministic and explained. Nothing is written for you.'),
    segmented(TABS, tab, (v) => ctx.go(`seo/${v}`), 'SEO tool'),
    body,
  );
}

function auditTab(listings: ListingRecord[], _ctx: Ctx): Node {
  const out = h('div');
  const run = () => {
    const a = auditListing({
      title: draft.title, tags: draft.tags.filter((t) => t.trim()), description: draft.description, keywords: kwList(),
      imageCount: draft.imageCount === '' ? undefined : Number(draft.imageCount),
    });
    out.replaceChildren(card(cardHead('Result', h('span', { class: 'score-ring' }, `${a.score}/100`)),
      h('small', { style: 'display:block;margin-bottom:6px' }, 'Score = 100 × (1 − points lost ÷ maximum). An error costs 3 points, a warning 2, an info 1.'),
      rules(a)));
  };
  const titleIn = h('input', { type: 'text', value: draft.title, style: 'width:100%', oninput: (e: Event) => { draft.title = (e.target as HTMLInputElement).value; run(); } });
  const tagsIn = h('textarea', { style: 'min-height:70px', oninput: (e: Event) => { draft.tags = (e.target as HTMLTextAreaElement).value.split(',').map((x) => x.trim()); run(); } }, draft.tags.filter(Boolean).join(', '));
  const descIn = h('textarea', { oninput: (e: Event) => { draft.description = (e.target as HTMLTextAreaElement).value; run(); } }, draft.description);
  const imgIn = h('input', { type: 'number', min: 0, max: 20, value: draft.imageCount, oninput: (e: Event) => { draft.imageCount = (e.target as HTMLInputElement).value; run(); } });
  run();
  return h('div', { class: 'grid-2' },
    card(cardHead('Listing', listingPicker(listings, (l) => { loadListing(l); (titleIn as HTMLInputElement).value = draft.title; (tagsIn as HTMLTextAreaElement).value = draft.tags.filter(Boolean).join(', '); (descIn as HTMLTextAreaElement).value = draft.description; (imgIn as HTMLInputElement).value = draft.imageCount; run(); })),
      h('div', { class: 'stack' },
        keywordsField(run),
        h('label', { class: 'field' }, 'Title', titleIn),
        h('label', { class: 'field' }, 'Tags (comma-separated)', tagsIn, h('small', null, 'For a competitor’s listing, the related search terms from the page are loaded here. For your own listing, paste your exact 13 tags.')),
        h('label', { class: 'field' }, 'Description', descIn),
        h('label', { class: 'field' }, 'Number of images', imgIn))),
    out,
  );
}

function titleTab(): Node {
  const out = h('div', { class: 'stack' });
  const counter = h('span', { class: 'mono' });
  const run = () => {
    const t = analyseTitle(draft.title, kwList());
    counter.textContent = `${t.chars}/${LIMITS.titleMax}`;
    counter.style.color = t.chars > LIMITS.titleMax ? 'var(--err)' : t.chars > 100 ? 'var(--warn)' : '';
    out.replaceChildren(
      h('div', { class: 'grid' },
        card(null, h('div', { class: 'kpi' }, h('span', { class: 'label' }, 'Characters'), h('span', { class: 'value' }, String(t.chars)))),
        card(null, h('div', { class: 'kpi' }, h('span', { class: 'label' }, 'Words'), h('span', { class: 'value' }, String(t.words)))),
        card(null, h('div', { class: 'kpi' }, h('span', { class: 'label' }, 'Avg word length'), h('span', { class: 'value' }, t.avgWordLength.toFixed(1)))),
        card(null, h('div', { class: 'kpi' }, h('span', { class: 'label' }, 'Phrases'), h('span', { class: 'value' }, String(t.segments.length))))),
      card('First 40 characters (what shoppers see first)', h('p', { class: 'mono' }, t.first40 || '—')),
      card('Keyword placement', t.keywordPositions.length ? h('div', { class: 'stack-sm' }, t.keywordPositions.map((k) => h('div', { class: 'row between' }, h('span', null, k.keyword), h('span', { class: `badge ${k.index < 0 ? 'err' : k.inFirst40 ? 'verified' : 'warn'}` }, k.index < 0 ? 'missing' : k.inFirst40 ? `at ${k.index} (front)` : `at ${k.index}`)))) : h('small', null, 'Add target keywords above.')),
      card('Repetition & style', h('div', { class: 'stack-sm' },
        h('div', null, 'Repeated words: ', t.duplicateWords.length ? t.duplicateWords.join(', ') : 'none'),
        h('div', null, 'ALL CAPS words: ', t.allCapsWords.length ? t.allCapsWords.join(', ') : 'none'),
        h('div', null, 'Special characters: ', Object.keys(t.specialChars).length ? Object.entries(t.specialChars).map(([c, n]) => `${c}×${n}`).join(' ') : 'none'),
        h('div', null, 'Phrases: ', h('div', { class: 'chips' }, t.segments.map((s) => h('span', { class: 'chip' }, s)))))),
    );
  };
  run();
  return h('div', { class: 'stack' },
    card(null, h('div', { class: 'stack' }, keywordsField(run),
      h('label', { class: 'field' }, h('span', { class: 'row between' }, 'Title', counter), h('input', { type: 'text', value: draft.title, style: 'width:100%', oninput: (e: Event) => { draft.title = (e.target as HTMLInputElement).value; run(); } })))),
    out);
}

async function tagsTab(listings: ListingRecord[]): Promise<Node> {
  const out = h('div', { class: 'stack' });
  const saved = await repo.keywords();
  const comp = new Set<string>();
  const compBox = h('div');
  const inputs = draft.tags.map((t, i) => h('input', { type: 'text', value: t, maxlength: 40, 'aria-label': `Tag ${i + 1}`, placeholder: `Tag ${i + 1}`, oninput: (e: Event) => { draft.tags[i] = (e.target as HTMLInputElement).value; run(); } }));
  const run = () => {
    const g = analyseTags(draft.tags, draft.title, kwList());
    inputs.forEach((inp, i) => inp.classList.toggle('over', (draft.tags[i] ?? '').length > LIMITS.tagMaxChars));
    out.replaceChildren(
      card('Tag analysis', h('div', { class: 'stack-sm' },
        h('div', null, `${13 - g.emptySlots}/13 tags used · ${g.singleWordTags} single-word`),
        g.tags.length ? h('div', { class: 'table-wrap' }, h('table', { class: 'data' }, h('thead', null, h('tr', null, h('th', null, 'Tag'), h('th', { class: 'num' }, 'Chars'), h('th', { class: 'num' }, 'Words'), h('th', null, 'Notes'))),
          h('tbody', null, g.tags.map((t) => h('tr', null, h('td', null, t.tag), h('td', { class: 'num', style: t.tooLong ? 'color:var(--err)' : '' }, `${t.chars}/20`), h('td', { class: 'num' }, String(t.words)), h('td', null, [t.duplicate ? 'duplicate' : '', t.inTitle ? 'also in title' : ''].filter(Boolean).join(', ')))))))
          : h('small', null, 'Enter tags above.'),
        g.repeatedWords.length ? h('div', null, 'Words in 3+ tags: ', g.repeatedWords.map((w) => `${w.word} (${w.count})`).join(', ')) : null,
        kwList().length ? h('div', null, h('div', null, 'Keyword coverage (title + tags):'), h('div', { class: 'chips' }, [...g.coveredKeywords.map((k) => h('span', { class: 'chip on' }, `✓ ${k}`)), ...g.missingKeywords.map((k) => h('span', { class: 'chip' }, `✗ ${k}`))])) : null,
      )),
    );
    drawComp();
  };
  const drawComp = () => {
    const mine = new Set(draft.tags.map((t) => normalise(t)).filter(Boolean));
    const freq = new Map<string, number>();
    for (const id of comp) {
      const l = listings.find((x) => x.listingId === id);
      for (const t of new Set((l?.relatedTerms ?? []).map(normalise))) freq.set(t, (freq.get(t) ?? 0) + 1);
    }
    const list = [...freq.entries()].sort((a, b) => b[1] - a[1]);
    compBox.replaceChildren(comp.size ? h('div', { class: 'stack-sm' },
      h('small', null, `${comp.size} competitor listing(s). The terms below come from their pages; ✓ means you already use the term.`),
      h('div', { class: 'chips' }, list.slice(0, 60).map(([t, n]) => h('button', { type: 'button', class: `chip${mine.has(t) ? ' on' : ''}`, title: `Used by ${n} listing(s). Click to copy into an empty tag slot.`, onclick: () => {
        const i = draft.tags.findIndex((x) => !x.trim());
        if (i < 0) { toast('All 13 tag slots are filled'); return; }
        draft.tags[i] = t; (inputs[i] as HTMLInputElement).value = t; run();
      } }, `${mine.has(t) ? '✓ ' : ''}${t} · ${n}`))),
    ) : h('small', null, 'Add competitor listings to compare their terms with your tags.'));
  };
  run();
  const tagCollections = (await repo.collections()).filter((c) => c.kind === 'tags');
  return h('div', { class: 'grid-2' },
    h('div', { class: 'stack' },
      card(cardHead('Your tags', listingPicker(listings, (l) => { loadListing(l); inputs.forEach((inp, i) => ((inp as HTMLInputElement).value = draft.tags[i] ?? '')); run(); })),
        h('div', { class: 'stack' }, keywordsField(run),
          saved.length ? h('select', { 'aria-label': 'Add saved keyword to targets', onchange: (e: Event) => { const v = (e.target as HTMLSelectElement).value; if (v) { draft.keywords = [...kwList(), v].join(', '); (e.target as HTMLSelectElement).value = ''; run(); toast(`Added “${v}” to target keywords`); } } }, h('option', { value: '' }, 'Add a saved keyword to targets…'), saved.map((k) => h('option', { value: k.term }, k.term))) : null,
          h('div', { class: 'tag-inputs' }, inputs),
          h('div', { class: 'row' },
            h('button', { class: 'btn small', type: 'button', onclick: async () => {
              const name = window.prompt('Name for this tag set');
              if (!name) return;
              const c: Collection = { id: `tags-${Date.now()}`, name, kind: 'tags', items: draft.tags.map((t) => t.trim()).filter(Boolean), createdAt: Date.now() };
              await repo.saveCollection(c);
              toast('Tag set saved');
            } }, 'Save tag set'),
            tagCollections.length ? h('select', { 'aria-label': 'Load tag set', onchange: (e: Event) => { const c = tagCollections.find((x) => x.id === (e.target as HTMLSelectElement).value); if (c) { draft.tags = [...c.items, ...Array(13).fill('')].slice(0, 13); inputs.forEach((inp, i) => ((inp as HTMLInputElement).value = draft.tags[i])); run(); } } }, h('option', { value: '' }, 'Load tag set…'), tagCollections.map((c) => h('option', { value: c.id }, c.name))) : null,
            h('button', { class: 'btn small', type: 'button', onclick: () => { navigator.clipboard.writeText(draft.tags.filter((t) => t.trim()).join(', ')).then(() => toast('Copied')); } }, 'Copy tags')))),
      out),
    card(cardHead('Competitor terms', listingPicker(listings, (l) => { comp.add(l.listingId); drawComp(); }, 'Add a competitor listing…'), h('button', { class: 'btn small', type: 'button', onclick: () => { comp.clear(); drawComp(); } }, 'Clear')), compBox),
  );
}

function descriptionTab(): Node {
  const out = h('div');
  const run = () => {
    const d = analyseDescription(draft.description, kwList());
    out.replaceChildren(card('Analysis', h('div', { class: 'stack' },
      h('div', { class: 'grid' },
        h('div', { class: 'kpi' }, h('span', { class: 'label' }, 'Characters'), h('span', { class: 'value' }, fmtNum(d.chars))),
        h('div', { class: 'kpi' }, h('span', { class: 'label' }, 'Words'), h('span', { class: 'value' }, fmtNum(d.words))),
        h('div', { class: 'kpi' }, h('span', { class: 'label' }, 'Paragraphs / bullets'), h('span', { class: 'value' }, `${d.paragraphs} / ${d.bullets}`)),
        h('div', { class: 'kpi', title: 'Flesch Reading Ease: 60–70 is plain English; higher is easier' }, h('span', { class: 'label' }, 'Readability (Flesch)'), h('span', { class: 'value' }, d.flesch !== undefined ? String(Math.round(d.flesch)) : '—'))),
      h('div', null, h('strong', null, 'Opening 160 characters'), h('p', { class: 'mono', style: 'margin-top:4px' }, d.first160 || '—')),
      kwList().length ? h('div', null, h('strong', null, 'Keywords'), h('div', { class: 'chips', style: 'margin-top:4px' }, kwList().map((k) => h('span', { class: `chip${d.keywordsInFirst160.includes(k) ? ' on' : ''}` }, `${k}: ${d.keywordsMissing.includes(k) ? 'missing' : d.keywordsInFirst160.includes(k) ? 'in opening' : 'present'}`)))) : null,
      h('div', null, h('strong', null, 'Product information checklist'), h('small', { style: 'display:block' }, 'Detected by keyword patterns, so verify manually.'), h('div', { class: 'chips', style: 'margin-top:4px' }, d.info.map((i) => h('span', { class: `chip${i.present ? ' on' : ''}` }, `${i.present ? '✓' : '✗'} ${i.label}`)))),
      d.repeatedPhrases.length ? h('div', null, h('strong', null, 'Repeated 3-word phrases'), h('div', { class: 'chips', style: 'margin-top:4px' }, d.repeatedPhrases.map((p) => h('span', { class: 'chip' }, `${p.phrase} ×${p.count}`)))) : null,
    )));
  };
  run();
  return h('div', { class: 'grid-2' },
    card(null, h('div', { class: 'stack' }, keywordsField(run), h('label', { class: 'field' }, 'Description', h('textarea', { style: 'min-height:320px', oninput: (e: Event) => { draft.description = (e.target as HTMLTextAreaElement).value; run(); } }, draft.description)))),
    out);
}

function compareTab(listings: ListingRecord[]): Node {
  const chosen: string[] = [];
  const out = h('div');
  const draw = () => {
    const ls = chosen.map((id) => listings.find((l) => l.listingId === id)!).filter(Boolean);
    if (!ls.length) { out.replaceChildren(empty('Add two to four recorded listings to compare them side by side.')); return; }
    const audits = ls.map((l) => auditListing({ title: l.title, tags: l.relatedTerms, tagsAreRelatedTerms: true, description: l.description ?? '', imageCount: l.imageCount, imageAlts: l.imageAlts, keywords: kwList(), category: l.category }));
    const sets = ls.map((l) => new Set(l.relatedTerms.map(normalise)));
    const shared = [...(sets[0] ?? [])].filter((t) => sets.every((s) => s.has(t)));
    const row = (label: string, f: (l: ListingRecord, a: Audit) => Node | string) => h('tr', null, h('th', { scope: 'row' }, label), ls.map((l, i) => h('td', null, f(l, audits[i]))));
    out.replaceChildren(card(null, h('div', { class: 'table-wrap' }, h('table', { class: 'data' },
      h('thead', null, h('tr', null, h('th', null, ''), ls.map((l) => h('th', null, h('span', { class: 'row' }, l.shopName ?? `#${l.listingId}`, h('button', { class: 'btn small', type: 'button', 'aria-label': 'Remove', onclick: () => { chosen.splice(chosen.indexOf(l.listingId), 1); draw(); } }, '✕')))))),
      h('tbody', null,
        row('SEO score', (_l, a) => `${a.score}/100`),
        row('Title', (l) => h('span', { class: 'clip', title: l.title }, l.title)),
        row('Title length', (_l, a) => `${a.title.chars} chars · ${a.title.words} words`),
        row('Repeated title words', (_l, a) => a.title.duplicateWords.join(', ') || 'none'),
        row('Keyword in first 40', (_l, a) => (a.title.keywordPositions[0] ? (a.title.keywordPositions[0].inFirst40 ? 'yes' : a.title.keywordPositions[0].index < 0 ? 'missing' : 'later') : '—')),
        row('Related terms', (l) => `${l.relatedTerms.length}`),
        row('Unique terms', (l, _a) => h('div', { class: 'chips' }, l.relatedTerms.filter((t) => !shared.includes(normalise(t))).slice(0, 12).map((t) => h('span', { class: 'chip' }, t)))),
        row('Description', (_l, a) => `${a.description.chars} chars · Flesch ${a.description.flesch !== undefined ? Math.round(a.description.flesch) : '—'}`),
        row('Images', (l) => fmtNum(l.imageCount)),
        row('Variations', (l) => l.variations.map((v) => `${v.name} (${v.options.length})`).join(', ') || 'none'),
        row('Price', (l) => (l.price !== undefined ? `${l.price} ${l.currency ?? ''}` : '—')),
        row('Warnings', (_l, a) => String(a.results.filter((r) => r.severity === 'warning' || r.severity === 'error').length)),
      ))),
      shared.length ? h('div', { style: 'margin-top:10px' }, h('strong', null, 'Terms shared by all: '), h('div', { class: 'chips', style: 'margin-top:4px' }, shared.map((t) => h('span', { class: 'chip on' }, t)))) : null,
    ));
  };
  draw();
  return h('div', { class: 'stack' },
    card(null, h('div', { class: 'row' }, keywordsField(draw), listingPicker(listings, (l) => { if (!chosen.includes(l.listingId) && chosen.length < 4) chosen.push(l.listingId); draw(); }, 'Add a listing to compare…'))),
    out);
}
