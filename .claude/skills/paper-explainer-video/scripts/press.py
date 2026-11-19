"""Press material for history and current-affairs films: real articles as paper clippings.

    from press import article, highlight, typed_quote, sync

article()      a captured web article (headline + paragraph, scripts/capture_article.js) printed on a
               torn paper card, with the boxes of its quoted phrases in card pixels.
highlight()    marker ink over one phrase, line by line, on its spoken cue (multiply blend so the
               printed words stay readable; dark=True for white-on-black pages).
typed_quote()  a quotation typed letter by letter on a paper strip (every quote in the film).
sync(globals())  at the end of an act: words() and tag() never show a word before the narrator
               says it (labels wait for their last spoken word). Check with check_sync.py.

First used on « L'histoire de GTA » (videos/histoire-gta), where the user chose clippings over
whole scrolling web pages and wanted every claim shown in its source article.
"""
import json
import re as _re
import unicodedata as _ud
import numpy as np
from PIL import Image, ImageDraw
from vox import asset, font, PAL, INK, CREAM, torn_mask
import vox as _vox
import style as _st
import presets as P
import annotate as A


def article(head, body, outlet, date, width=1180, seed=21, pad=46):
    """A press article as a printed web page on the desk: outlet and date, the real headline and
    the real paragraph (Playwright captures in assets/), torn edges. Returns (card, boxes): the
    boxes of the captured phrases (A0x_*.json) in card pixels, for annotate.sweep."""
    hd, bd = Image.open(asset(head)).convert('RGB'), Image.open(asset(body)).convert('RGB')
    inner = width - 2 * pad
    k_h = min(1.0, inner / hd.width)
    hd = hd.resize((int(hd.width * k_h), int(hd.height * k_h)), Image.LANCZOS)
    k_b = inner / bd.width
    bd = bd.resize((inner, int(bd.height * k_b)), Image.LANCZOS)
    y_top = pad + 40
    y_rule = y_top + hd.height + 18
    y_body = y_rule + 24
    h = y_body + bd.height + pad
    card = Image.new('RGBA', (width, h), (255, 255, 255, 255))     # the captures' own white
    d = ImageDraw.Draw(card)
    d.text((pad, pad), f'{outlet.upper()}   ·   {date}', font=font('Inter600.ttf', 24), fill=PAL.muted + (255,))
    card.paste(hd, (pad, y_top))
    d.line((pad, y_rule, width - pad, y_rule), fill=(205, 205, 200, 255), width=2)
    card.paste(bd, (pad, y_body))
    a = np.asarray(card).astype(np.float32)
    a[..., :3] += np.random.default_rng(seed).normal(0, 2.2, (h, width, 1))
    card = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    card.putalpha(torn_mask(width, h, seed, amp=5, step=12))
    boxes = {}
    meta = asset(body.rsplit('.', 1)[0] + '.json')
    try:
        for ph, rects in json.load(open(meta))['boxes'].items():
            boxes[ph] = [(pad + x0 * k_b, y_body + y0 * k_b, pad + x1 * k_b, y_body + y1 * k_b) for x0, y0, x1, y1 in rects or []]
    except FileNotFoundError:
        pass
    return card, boxes


def highlight(layer, card_xy, boxes, t, start, gap=0.35, until=None, colour=None, strength=0.85, dark=False):
    """Highlighter over one phrase of an article placed with its top-left at card_xy, line by
    line, as the narration reaches it. Multiplied into the page like real marker ink, so the
    printed words stay dark and readable on top of the colour."""
    x, y = card_xy
    tmp = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        A.sweep(tmp, (x + x0, y + y0, x + x1, y + y1), t, start + i * gap, until=until, sound=(i == 0), seed=7 + i,
                colour=colour or PAL.highlight, alpha=1.0)
    a = np.asarray(tmp).astype(np.float32)
    k = a[..., 3:4] / 255.0 * strength
    if k.max() <= 0:
        return
    base = np.asarray(layer).astype(np.float32)
    c = a[..., :3] / 255.0
    if dark:                                   # white-on-black page: screen the colour in, the text stays white
        bb = base[..., :3] / 255.0
        base[..., :3] = 255.0 * (bb + k * (1 - bb) * c * 0.75)
    else:
        mul = 1 - k + k * c
        base[..., :3] *= mul
    layer.paste(Image.fromarray(base.clip(0, 255).astype(np.uint8), 'RGBA'))


# ---- typed quotes
_TYPED = {}


def typed_quote(layer, xy, text, t, start, size=40, width=1500, cps=24, paper=True, colour=None):
    """A quotation typed letter by letter (typewriter, with key sounds) on a strip of paper,
    centred on xy. Used for every quote and every translated quote in the film."""
    import typo as TY
    key = (text, size, width)
    if key not in _TYPED:
        _TYPED[key] = TY.Text(text, 'caption', size=size, colour=colour or INK, max_w=width, align='m')
    T = _TYPED[key]
    if t < start - 0.25:
        return
    x, y = xy
    if paper:
        k = P.clamp01((t - start + 0.25) / 0.25)
        strip = P.paper_card(int(T.w + 70), int(T.h + 40), seed=91, colour=CREAM)
        P.put(layer, P.fade_img(strip, k), x, y + T.h / 2, sh_op=0.25)
    T.draw(layer, (x, y), t, start, anim='type', anchor='m', stagger=1.0 / cps)


# ---- words never before the narration
_STOP = {'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et', 'a', 'au', 'aux', 'en', 'l', 'd', 'dans',
         'par', 'sur', 'pour', 'son', 'sa', 'ses', 'qui', 'que'}


def _norm(s):
    s = _ud.normalize('NFKD', s.lower().replace('’', "'"))
    s = ''.join(c for c in s if not _ud.combining(c))
    return _re.sub(r"[^a-z0-9]", '', s)


def _same(a, b):
    if not a or not b:
        return False
    if a == b:
        return True
    n = min(len(a), len(b))
    return n >= 4 and a[:max(4, n - 2)] == b[:max(4, n - 2)]


class _NS:
    """Attribute view of an act's globals() (render_all loads acts without sys.modules)."""
    def __init__(self, g):
        object.__setattr__(self, 'g', g)

    def __getattr__(self, k):
        return self.g[k]

    def __setattr__(self, k, v):
        self.g[k] = v


def sync(mod):
    if isinstance(mod, dict):
        mod = _NS(mod)
    """Make the act's words() and tag() wait for the narration: each on-screen word that the
    narration says in this shot appears no earlier than it is spoken (a label appears once its
    last spoken word is said). Paraphrased words follow the word before them."""
    said, off = [], 0.0
    for c in mod.CLIPS:
        for wd in _vox._WORDS[c]:
            for part in _re.split(r"[\s'’\-]+", wd['w']):
                if _norm(part):
                    said.append((_norm(part), off + wd['s']))
        off += _vox._DUR[c]
    cache = {}

    def window():
        s0 = _vox._SCENE_START
        starts = [x[0] for x in mod.SHOTS] + [mod.END]
        nxt = min([x for x in starts if x > s0 + 1e-6] or [mod.END])
        return s0, nxt

    def spoken_times(text):
        s0, s1 = window()
        key = (s0, text)
        if key not in cache:
            out, last = [], s0 - 0.3
            for word in text.split():
                nw = _norm(word)
                hit = None
                if nw and nw not in _STOP and not (nw.isdigit() and len(nw) < 3):
                    hit = next((tt for (sw, tt) in said if last - 0.05 <= tt < s1 - 0.25 and _same(nw, sw)), None)
                if hit is not None:
                    last = hit
                out.append(hit)
            cache[key] = out
        return cache[key]

    def words_synced(layer, xy, s, size, t, times, *a, **k):
        n = len(s.split())
        ts = list(times) if isinstance(times, (list, tuple)) else [times] * n
        ts += [ts[-1]] * (n - len(ts))
        sp = spoken_times(s)
        s0 = _vox._SCENE_START
        out, floor = [], -1e9
        for given, hit in zip(ts, sp):
            v = given if hit is None else max(given, hit - s0)
            v = max(v, floor)                         # never ahead of the word before it
            out.append(v)
            floor = v
        return _st.words(layer, xy, s, size, t, out, *a, **k)

    def tag_synced(layer, xy, s, size, t, start, *a, **k):
        sp = [h for h in spoken_times(s) if h is not None]
        if sp:
            start = max(start, max(sp) - _vox._SCENE_START)
        return _st.tag(layer, xy, s, size, t, start, *a, **k)

    mod.words, mod.tag = words_synced, tag_synced
