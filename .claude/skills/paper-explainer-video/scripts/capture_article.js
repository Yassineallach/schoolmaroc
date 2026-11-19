// Capture one paragraph of a web article for press.article(), with the boxes of the phrases to highlight.
//   node SK/scripts/capture_article.js URL OUT.png "anchor text" "phrase 1|phrase 2" [pad]
// Writes OUT.png (2x crop of the block holding the anchor) and OUT.png.json (phrase boxes in crop px).
// Measures three times after scrolling, so ads and lazy images that load late do not shift the crop
// (a one-shot measure caught the wrong paragraph on GamesBeat). Capture the headline the same way.
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const [url, out, anchor, phrases, padArg] = process.argv.slice(2); const pad = +(padArg || 40);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1100, height: 1300 }, deviceScaleFactor: 2,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36' });
  await p.goto(url, { waitUntil: 'load', timeout: 60000 }); await p.waitForTimeout(4000);
  const measure = () => p.evaluate(([anchor, phrases]) => {
    const find = (txt) => { const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, { acceptNode: n =>
        (/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(n.parentElement?.tagName) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT) });
      let n; while ((n = w.nextNode())) { const i = n.textContent.indexOf(txt); if (i >= 0 && n.parentElement.getBoundingClientRect().height > 0) return [n, i]; } return null; };
    const h = find(anchor); if (!h) return null;
    let el = h[0].parentElement.closest('p,blockquote,li,h1,h2,h3,dd,td,font,div') || h[0].parentElement; while (el.parentElement && el.getBoundingClientRect().width < 400) el = el.parentElement;
    el.scrollIntoView({ block: 'center' });
    for (const e of document.querySelectorAll('body *')) { const s = getComputedStyle(e); if (s.position === 'fixed' || s.position === 'sticky') e.style.visibility = 'hidden'; }
    const boxes = {};
    for (const ph of phrases.split('|').filter(Boolean)) { const f = find(ph); if (!f) { boxes[ph] = null; continue; }
      const r = document.createRange(); r.setStart(f[0], f[1]); r.setEnd(f[0], f[1] + ph.length);
      boxes[ph] = [...r.getClientRects()].map(q => [q.left + scrollX, q.top + scrollY, q.right + scrollX, q.bottom + scrollY]); }
    const q = el.getBoundingClientRect(); return { block: [q.left + scrollX, q.top + scrollY, q.right + scrollX, q.bottom + scrollY], boxes, title: document.title };
  }, [anchor, phrases || '']);
  let info = await measure(); await p.waitForTimeout(3500); info = await measure(); await p.waitForTimeout(1500); info = await measure();
  if (!info) { console.log('anchor not found'); process.exit(1); }
  let [x0, y0, x1, y1] = info.block;
  const all = Object.values(info.boxes).filter(Boolean).flat();
  if (all.length && (y1 - y0 > 1200 || y1 <= y0)) {      // block too tall or off-screen: frame the phrase itself
    y0 = Math.min(...all.map(r => r[1])) - 120; y1 = Math.max(...all.map(r => r[3])) + 120;
    x0 = Math.max(0, Math.min(x0, ...all.map(r => r[0])) ); x1 = Math.min(1100, Math.max(x1, ...all.map(r => r[2])));
    if (x1 - x0 > 900) { x0 = Math.max(0, x0); }
  }
  const clip = { x: Math.max(0, x0 - pad), y: Math.max(0, y0 - pad), width: x1 - x0 + 2 * pad, height: Math.min(1300, y1 - y0 + 2 * pad) };
  await p.screenshot({ path: out, clip, fullPage: true });
  const rel = {}; for (const [k, v] of Object.entries(info.boxes)) rel[k] = v && v.map(([a, bb, c, d]) => [(a - clip.x) * 2, (bb - clip.y) * 2, (c - clip.x) * 2, (d - clip.y) * 2]);
  fs.writeFileSync(out + '.json', JSON.stringify({ url, title: info.title, boxes: rel }, null, 1)); console.log(JSON.stringify(rel));
  await b.close();
})();
