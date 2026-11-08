"""Visual identity guide: a reference board per identity, an overview of all of them, and a
board showing how the topic changes the identity.

    python identity_board.py --all <out_dir>          # every page + identities_overview.png + identities_context.png
    python identity_board.py --page <identity> <out.png>
    python identity_board.py --topic "<topic>" <out.png>   # the identity the engine derives for a topic

Every tile is drawn by the engine itself (scenes.py grounds and textures, typo.py roles, charts,
annotations, palette.treat), so the board shows what a video will really look like.
"""
import os, sys, json, subprocess, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
F = 2                                         # pages are drawn at 2x for a crisp guide

PAGE_W, PAGE_H = 1920, 1080


# ===================================================================== child: draws one identity
def _setup():
    sys.path.insert(0, HERE)
    global Image, ImageDraw, ImageFont, vox, W, H, st, Shot, tag, S, TY, Text, C, A, PL, PAL, IDN, typo
    from PIL import Image, ImageDraw, ImageFont
    import vox
    from vox import W, H
    import style as st
    from style import Shot, tag
    import scenes as S
    import typo as TY
    from typo import Text
    import charts as C
    import annotate as A
    import palette as PL
    import typo
    PAL, IDN = PL.ACTIVE, PL.IDENTITY
    st.KICKER_XY = (620, 1000)


def font(role, size):
    f = typo.ROLES[role][0][0]
    return ImageFont.truetype(os.path.join(vox.FONTS, f), int(size * F))


def ui(size, bold=True):
    return ImageFont.truetype(os.path.join(vox.FONTS, 'Inter600.ttf' if bold else 'Inter400.ttf'), int(size * F))


def readable(bg):
    return PAL.ink if PL.contrast(PAL.ink, bg) >= PL.contrast(PAL.light, bg) else PAL.light


def wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if d.textlength(t, font=f) <= width * F:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def _compose(fn):
    s = Shot(6.0, 8.0)
    fn(s, 6.0)
    return Image.fromarray(st.compose(s, 6.0)).convert('RGB')


# ---------------------------------------------------------------- example scenes per identity
def example_scene():
    """A real shot in the identity's signature treatment."""
    b = IDN.base
    pal = PAL
    o = json.loads(os.environ.get('VOX_BOARD_SCENE', '{}'))     # topic boards: their own words
    hd, tg = o.get('headline'), o.get('tag')

    def editorial(s, t):
        S.env(s, 'paper')
        T = Text(hd or 'WHY WE FORGET', 'headline', size=150)
        xy = (W / 2, 330)
        A.sweep(s.top, T.box((hd or 'WHY WE FORGET').split()[-1], xy, anchor='m'), t, 0.2, sound=False)
        T.draw(s.top, xy, t, 0.0, anim='words', anchor='m', sound=False)
        Text('half of what we learn is gone in a day', 'caption', size=50).draw(s.hud, (W / 2, 600), t, 0.0, anim='words', anchor='m', sound=False)
        tag(s.hud, (W / 2, 760), tg or 'THE FORGETTING CURVE', 50, t, 0.3)

    def history(s, t):
        S.env(s, 'archive')
        TY.press(s.mid, (220, 230), hd or 'The treaty is signed', t, 0.0, width=1480, dateline=o.get('dateline', 'Versailles · 28 June 1919'), size=120, sound=False)
        tag(s.hud, (W / 2, 820), tg or 'THE END OF A WAR', 50, t, 0.2)

    def science(s, t):
        S.env(s, 'archive' if IDN.signature == 'archive' else 'charcoal', mood='wonder')
        S.type_page(s, hd or 'Nothing escapes a black hole.', t, 0.0, role='statement', size=110, accent={w_: 0.1 for w_ in o.get('accent', ['black', 'hole.'])}, xy=(W / 2, 380))
        Text(tg or 'NOT EVEN LIGHT', 'label', size=40, colour=S.ink(s)).draw(s.hud, (W / 2, 680), t, 0.0, anim='words', anchor='m', sound=False)

    def manga(s, t):
        S.env(s, 'halftone', mood='tense')
        Text(hd or 'THE ECLIPSE', 'headline', size=210 if len(hd or 'THE ECLIPSE') < 12 else 170).draw(s.top, (W / 2, 330), t, 0.0, anim='words', anchor='m', sound=False)
        tag(s.hud, (W / 2, 720), tg or 'VOLUME 13', 56, t, 0.2)

    def crime(s, t):
        S.env(s, 'charcoal', mood='mystery')
        S.type_page(s, 'Who was she?', t, 0.0, role='statement', size=150, accent={'she?': 0.1}, xy=(W / 2, 330))
        tag(s.hud, (W / 2, 700), 'CASE FILE 1947-03', 52, t, 0.2, bg=pal.highlight, fg=pal.ink)

    def tech(s, t):
        S.env(s, 'grid')
        Text(hd or 'COMPUTE USED TO TRAIN AI', 'label', size=36).draw(s.hud, (360, 300), t, 0.0, anim='words', sound=False)
        C.compare(s.mid, (360, 400), [tuple(x) for x in o.get('bars', [('2012', 1), ('2018', 30), ('2024', 100)])], t, 0.0, width=1100, height=90, highlight=2, unit=o.get('unit', 'x'))

    def philosophy(s, t):
        S.env(s, 'cream', mood='calm')
        q = Text('“The unexamined life is not worth living.”', 'quote', size=96, max_w=1400, align='m')
        xy = (W / 2, 340)
        A.sweep(s.top, q.box('unexamined', xy, anchor='m'), t, 0.2, sound=False)
        q.draw(s.top, xy, t, 0.0, anim='words', anchor='m', sound=False)
        Text('SOCRATES · 399 BC', 'label', size=36).draw(s.hud, (W / 2, 720), t, 0.0, anim='words', anchor='m', sound=False)

    def nature(s, t):
        S.env(s, 'paper')
        TY.big_number(s.top, (W / 2, 200), hd or '69%', t, 0.0, role='stat', label='OF WILDLIFE LOST SINCE 1970', sound=False)
        tag(s.hud, (W / 2, 800), tg or 'LIVING PLANET INDEX', 54, t, 0.2)

    def culture(s, t):
        S.env(s, 'geometric')
        TY.name_card(s.top, (240, 360), 'The House of Tiles', 'ARCHITECTURE · FES, 14TH CENTURY', t, 0.0)
        tag(s.hud, (1400, 760), 'ZELLIGE', 56, t, 0.2)

    def economics(s, t):
        S.env(s, 'grid')
        C.line_chart(s.mid, (300, 260, 1600, 820), [(2000, 20), (2004, 34), (2007, 52), (2008, 21), (2012, 38), (2020, 61)], t, 0.0,
                     colour=pal.accent, axis=pal.ink2, mark=(2007, 'THE PEAK'), ylabel='MARKET INDEX')
        tag(s.hud, (1350, 860), tg or 'SEPTEMBER 2008', 50, t, 0.2)

    fn = dict(editorial=editorial, history_archive=history, science_space=science, manga_ink=manga, crime=crime, technology=tech,
              philosophy=philosophy, nature=nature, culture=culture, economics=economics)[b]
    return _compose(fn)


# ---------------------------------------------------------------- tiles
def ground_tile(env, w, h, mood=None):
    s = Shot(6.0, 8.0)
    S.env(s, env, mood=mood)
    g = Image.fromarray(st.compose(s, 6.0)).convert('RGB')
    return g.resize((int(w * F), int(h * F)), Image.LANCZOS)


def type_tile(w, h):
    """Primary ground with the typographic hierarchy and a marker highlight."""
    im = ground_tile('paper', w, h)
    d = ImageDraw.Draw(im, 'RGBA')
    x, y = 26, 24
    d.text((x * F, y * F), 'PRIMARY GROUND · TYPE', font=ui(12), fill=PAL.muted)
    f = font('headline', 46)
    word = 'HEADLINE'
    tw = d.textlength(word, font=f)
    d.rounded_rectangle(((x - 4) * F, (y + 34) * F, x * F + tw + 8 * F, (y + 86) * F), radius=6 * F, fill=PAL.highlight + (150,))
    d.text((x * F, (y + 34) * F), word, font=f, fill=PAL.ink)
    d.text((x * F, (y + 100) * F), 'A statement that explains', font=font('statement', 25), fill=PAL.ink)
    d.text((x * F, (y + 140) * F), 'a caption under an image, set quietly', font=font('caption', 17), fill=PAL.ink2)
    d.text((x * F, (y + 172) * F), 'LABEL · 1919', font=font('label', 13), fill=PAL.ink2)
    d.text((x * F, (y + 196) * F), 'accent word', font=font('statement', 25), fill=PAL.accent)
    return im


def doc_tile(w, h):
    """Secondary ground: a document with an accent stamp and a supporting rule."""
    im = ground_tile('archive', w, h)
    d = ImageDraw.Draw(im, 'RGBA')
    d.text((26 * F, 24 * F), 'SECONDARY GROUND · DOCUMENT', font=ui(12), fill=PAL.muted)
    cx0, cy0, cx1, cy1 = 40, 60, w - 70, h - 30
    d.rectangle((cx0 * F + 6 * F, cy0 * F + 8 * F, cx1 * F + 6 * F, cy1 * F + 8 * F), fill=(0, 0, 0, 40))
    d.rectangle((cx0 * F, cy0 * F, cx1 * F, cy1 * F), fill=PAL.cream, outline=PAL.line, width=2 * F)
    d.line(((cx0 + 18) * F, (cy0 + 40) * F, (cx1 - 18) * F, (cy0 + 40) * F), fill=PAL.accent2, width=3 * F)
    d.text(((cx0 + 18) * F, (cy0 + 12) * F), 'RECORD No. 47', font=font('label', 13), fill=PAL.ink2)
    for k in range(5):
        yy = cy0 + 60 + k * 22
        d.line(((cx0 + 18) * F, yy * F, (cx0 + 18 + (180 - 30 * (k % 3))) * F, yy * F), fill=PAL.divider, width=3 * F)
    sx, sy = cx1 - 70, cy1 - 60
    d.ellipse(((sx - 44) * F, (sy - 44) * F, (sx + 44) * F, (sy + 44) * F), outline=PAL.accent, width=4 * F)
    d.text((sx * F, sy * F), 'FILED', font=font('label', 15), fill=PAL.accent, anchor='mm')
    return im


def dark_tile(w, h):
    im = ground_tile('charcoal', w, h)
    d = ImageDraw.Draw(im, 'RGBA')
    d.text((26 * F, 24 * F), 'DARK GROUND', font=ui(12), fill=_soft(PAL.light))
    d.text((26 * F, 70 * F), 'The turning', font=font('statement', 38), fill=PAL.light)
    d.text((26 * F, 116 * F), 'point.', font=font('statement', 38), fill=PAL.accent_dark)
    d.text((26 * F, 180 * F), 'ACCENT ON DARK', font=font('label', 13), fill=_soft(PAL.light))
    return im


def solid_tile(w, h):
    im = ground_tile('accent', w, h)
    d = ImageDraw.Draw(im, 'RGBA')
    d.text((26 * F, 24 * F), 'SOLID GROUND · ONE NUMBER', font=ui(12), fill=_soft(PAL.light))
    d.text((w / 2 * F, h * 0.52 * F), '70M', font=font('stat', 96), fill=PAL.light, anchor='mm')
    d.text((w / 2 * F, (h * 0.52 + 64) * F), 'COPIES SOLD', font=font('label', 14), fill=PAL.light, anchor='mm')
    return im


def chart_tile(w, h):
    im = ground_tile('grid', w, h)
    d = ImageDraw.Draw(im, 'RGBA')
    d.text((26 * F, 24 * F), 'CHARTS · HIGHLIGHT · LABELS', font=ui(12), fill=PAL.muted)
    vals = [0.42, 0.66, 0.9, 0.55, 0.3]
    bx0, by1, bw = 30, h - 40, 30
    for i, v in enumerate(vals):
        x = bx0 + i * (bw + 10)
        d.rectangle((x * F, (by1 - v * 150) * F, (x + bw) * F, by1 * F), fill=PAL.chart[i % len(PAL.chart)])
    d.line((24 * F, by1 * F, (bx0 + 5 * (bw + 10)) * F, by1 * F), fill=PAL.divider, width=2 * F)
    x0 = bx0 + 5 * (bw + 10) + 24
    d.rectangle((x0 * F, 70 * F, (x0 + 100) * F, 100 * F), fill=PAL.accent)
    d.text(((x0 + 50) * F, 85 * F), 'ACCENT TAG', font=font('label', 11), fill=PAL.light, anchor='mm')
    f = font('caption', 15)
    d.rounded_rectangle(((x0 - 3) * F, 122 * F, (x0 + 100) * F, 148 * F), radius=4 * F, fill=PAL.highlight + (170,))
    d.text((x0 * F, 124 * F), 'highlighted', font=f, fill=PAL.ink)
    d.ellipse(((x0 + 2) * F, 170 * F, (x0 + 98) * F, 214 * F), outline=PAL.accent, width=3 * F)
    d.text(((x0 + 50) * F, 192 * F), 'ringed', font=f, fill=PAL.ink, anchor='mm')
    return im


def _soft(c):
    return tuple(int(v * 0.72 + 70 * 0.28) for v in c)


def swatch(d, x, y, w, h, colour, role, hx):
    d.rectangle((x * F, y * F, (x + w) * F, (y + h) * F), fill=colour, outline=_edge(colour), width=1 * F)
    d.text((x * F, (y + h + 8) * F), role, font=ui(11.5), fill=PAL.ink2)
    d.text((x * F, (y + h + 24) * F), hx, font=ui(13), fill=PAL.ink)


def _edge(c):
    return tuple(max(0, v - 28) for v in c)


ROLE_ROWS = [
    ('GROUNDS', ['bg_primary', 'bg_secondary', 'bg_minimal', 'bg_dark', 'bg_solid']),
    ('TEXT', ['text_primary', 'text_secondary', 'text_muted', 'text_on_dark']),
    ('ACCENTS', ['accent_primary', 'accent_secondary', 'accent_on_dark', 'highlight']),
    ('LINES & FILLS', ['border', 'divider', 'fill_soft', 'texture_tint']),
]
SHORT = {'bg_primary': 'primary', 'bg_secondary': 'secondary', 'bg_minimal': 'minimal', 'bg_dark': 'dark', 'bg_solid': 'solid',
         'text_primary': 'primary', 'text_secondary': 'secondary', 'text_muted': 'muted', 'text_on_dark': 'on dark',
         'accent_primary': 'primary', 'accent_secondary': 'secondary', 'accent_on_dark': 'on dark', 'highlight': 'highlight',
         'border': 'border', 'divider': 'divider', 'fill_soft': 'soft fill', 'texture_tint': 'texture'}


def page(out, number=None, total=None, topic=None):
    """The full reference page for the active identity."""
    _setup()
    tok = PAL.tokens()
    im = Image.new('RGB', (PAGE_W * F, PAGE_H * F), PAL.cream)
    d = ImageDraw.Draw(im, 'RGBA')
    # left column: name, description, type and material
    x = 72
    d.rectangle((0, 0, 14 * F, PAGE_H * F), fill=PAL.accent)
    top = f'VISUAL IDENTITY  {number:02d} / {total:02d}' if number else 'VISUAL IDENTITY'
    d.text((x * F, 64 * F), top, font=ui(14), fill=PAL.muted)
    if topic:
        d.text((x * F, 88 * F), ('TOPIC  ·  ' + topic.upper())[:70], font=ui(14), fill=PAL.accent)
    y = 116
    for ln in wrap(d, IDN.label.upper() if IDN.base != 'culture' else IDN.label.upper(), font('headline', 66), 560):
        d.text((x * F, y * F), ln, font=font('headline', 66), fill=PAL.ink)
        y += 74
    y += 10
    d.line((x * F, y * F, (x + 80) * F, y * F), fill=PAL.accent, width=5 * F)
    y += 26
    for ln in wrap(d, IDN.description, font('caption', 22), 540):
        d.text((x * F, y * F), ln, font=font('caption', 22), fill=PAL.ink2)
        y += 32
    y += 10
    d.text((x * F, y * F), 'FOR', font=ui(12), fill=PAL.muted)
    from identities import IDENTITIES
    for ln in wrap(d, IDENTITIES[IDN.base]['use'], ui(16, False), 540):
        y += 22
        d.text((x * F, y * F), ln, font=ui(16, False), fill=PAL.ink2)
    if IDN.name != IDN.base:
        y += 34
        d.text((x * F, y * F), 'THIS VIDEO', font=ui(12), fill=PAL.muted)
        for w_ in IDN.why[1:4]:
            for ln in wrap(d, '· ' + w_.split(' (')[0], ui(14, False), 540)[:2]:
                y += 20
                d.text((x * F, y * F), ln, font=ui(14, False), fill=PAL.ink2)
    # type specimen
    y = 700
    d.text((x * F, y * F), 'TYPE', font=ui(12), fill=PAL.muted)
    d.text((x * F, (y + 18) * F), 'Aa', font=font('headline', 104), fill=PAL.ink)
    names = {f: f.split('.')[0].replace('700', ' Bold').replace('600', ' Semibold').replace('400', '').replace('500i', ' Italic').replace('ArchivoBlack', 'Archivo Black').replace('SpecialElite', 'Special Elite').replace('PTSerif', 'PT Serif').replace('Playfair', 'Playfair Display') for f in os.listdir(vox.FONTS)}
    yy = y + 22
    for role in ('headline', 'statement', 'caption', 'label'):
        d.text(((x + 190) * F, yy * F), role.upper(), font=ui(11), fill=PAL.muted)
        d.text(((x + 190) * F, (yy + 15) * F), names.get(typo.ROLES[role][0][0], typo.ROLES[role][0][0]), font=ui(15, False), fill=PAL.ink)
        yy += 40
    y = 900
    d.text((x * F, y * F), 'MATERIAL', font=ui(12), fill=PAL.muted)
    tx = IDN.texture
    kind_name = {'fibre': 'fibre paper', 'foxing': 'foxed parchment, burnt edge', 'stars': 'smooth stock, star field in the dark',
                 'screentone': 'manuscript paper, screentone', 'photocopy': 'photocopy toner and banding', 'dotgrid': 'smooth, precise dot grid',
                 'marble': 'ivory with marble veins', 'deckle': 'deckle paper, fibre clouds', 'canvas': 'woven canvas', 'ledger': 'ledger rules and margin'}
    img_name = {'none': 'natural colour', 'sepia': 'sepia duotone', 'cold': 'cold duotone', 'cool': 'cool balance', 'warm': 'warm balance', 'ink': 'ink, black and white'}
    d.text((x * F, (y + 20) * F), 'Texture  ' + kind_name.get(tx['kind'], tx['kind']), font=ui(15, False), fill=PAL.ink)
    d.text((x * F, (y + 44) * F), f"Images  {img_name.get(IDN.image[0], IDN.image[0])}" + (f" · {int(IDN.image[1] * 100)} %" if IDN.image[1] else ''), font=ui(15, False), fill=PAL.ink)
    d.text((x * F, (y + 68) * F), 'Opens on  ' + IDN.signature + ' · favours ' + ', '.join(k for k, v in sorted(IDN.bias.items(), key=lambda kv: -kv[1]) if v > 1.1)[:60], font=ui(15, False), fill=PAL.ink)

    # right: swatches
    rx = 700
    y = 64
    for title, roles in ROLE_ROWS:
        d.text((rx * F, y * F), title, font=ui(12), fill=PAL.muted)
        for i, role in enumerate(roles):
            swatch(d, rx + 120 + i * 208, y - 4, 190, 40, PL.rgb(tok[role]), SHORT[role], tok[role])
        y += 84
    d.text((rx * F, y * F), 'CHART', font=ui(12), fill=PAL.muted)
    for i, c in enumerate(PAL.chart):
        swatch(d, rx + 120 + i * 166, y - 4, 150, 40, c, f'series {i + 1}', PL.hexs(c))
    # right: example tiles
    ty0, tw, th, gap = 492, 366, 252, 21
    tiles = [type_tile(tw, th), doc_tile(tw, th), dark_tile(tw, th), solid_tile(tw, th), chart_tile(tw, th)]
    scene = example_scene().resize((tw * F, th * F), Image.LANCZOS)
    tiles.append(scene)
    for i, t_ in enumerate(tiles):
        cx, cy = rx + (i % 3) * (tw + gap), ty0 + (i // 3) * (th + gap + 22)
        im.paste(t_, (cx * F, cy * F))
        d.rectangle((cx * F, cy * F, (cx + tw) * F - 1, (cy + th) * F - 1), outline=_edge(PAL.cream), width=1 * F)
    d.text(((rx + 2 * (tw + gap)) * F, (ty0 + 2 * th + gap + 22 + 6) * F), 'IN A SCENE · rendered by the engine', font=ui(12), fill=PAL.muted)
    im.save(out)


def card(out, topic=None):
    """A compact identity card (overview and context boards)."""
    _setup()
    cw, ch = 720, 640
    im = Image.new('RGB', (cw * F, ch * F), PAL.cream)
    d = ImageDraw.Draw(im, 'RGBA')
    sc = example_scene().resize(((cw - 48) * F, int((cw - 48) * 9 / 16) * F), Image.LANCZOS)
    im.paste(sc, (24 * F, 24 * F))
    y = 24 + int((cw - 48) * 9 / 16) + 26
    if topic:
        for ln in wrap(d, topic, font('statement', 30), cw - 48)[:2]:
            d.text((24 * F, y * F), ln, font=font('statement', 30), fill=PAL.ink)
            y += 38
        d.text((24 * F, (y + 4) * F), IDN.name.replace('_', ' ').upper(), font=ui(15), fill=PAL.accent)
        y += 34
        for w_ in IDN.why[1:3]:
            for ln in wrap(d, '· ' + w_, ui(14, False), cw - 48)[:2]:
                d.text((24 * F, y * F), ln, font=ui(14, False), fill=PAL.ink2)
                y += 19
    else:
        d.text((24 * F, y * F), IDN.label.upper(), font=font('headline', 40), fill=PAL.ink)
        y += 52
        for ln in wrap(d, IDN.description, font('caption', 18), cw - 48)[:2]:
            d.text((24 * F, y * F), ln, font=font('caption', 18), fill=PAL.ink2)
            y += 25
    y = ch - 96
    keys = ['bg_primary', 'bg_secondary', 'bg_dark', 'bg_solid', 'accent_primary', 'accent_secondary', 'accent_on_dark', 'highlight']
    tok = PAL.tokens()
    sw = (cw - 48) / len(keys)
    for i, k in enumerate(keys):
        x = 24 + i * sw
        d.rectangle((x * F, y * F, (x + sw - 6) * F, (y + 44) * F), fill=PL.rgb(tok[k]), outline=_edge(PL.rgb(tok[k])), width=F)
        d.text((x * F, (y + 54) * F), tok[k], font=ui(11.5), fill=PAL.ink2)
    d.rectangle((0, 0, cw * F, 8 * F), fill=PAL.accent)
    im.save(out)


# ===================================================================== parent: runs each identity in its own process
def _child(args, palette_spec, scene=None):
    proj = tempfile.mkdtemp()
    env = dict(os.environ, VOX_PROJECT=proj, VOX_PALETTE=palette_spec, PYTHONPATH=HERE, VOX_BOARD_SCENE=json.dumps(scene or {}))
    subprocess.run([sys.executable, __file__] + args, check=True, env=env)


def _grid(paths, cols, out, title, bg=(236, 233, 226), ink=(24, 22, 20), sub=''):
    from PIL import Image, ImageDraw, ImageFont
    sys.path.insert(0, HERE)
    import vox
    ims = [Image.open(p) for p in paths]
    w, h = ims[0].size
    gap, head = 28 * F, 150 * F
    rows = (len(ims) + cols - 1) // cols
    board = Image.new('RGB', (cols * w + (cols + 1) * gap, head + rows * h + (rows + 1) * gap), bg)
    for i, im in enumerate(ims):
        board.paste(im, (gap + (i % cols) * (w + gap), head + gap + (i // cols) * (h + gap)))
    d = ImageDraw.Draw(board)
    d.text((gap, 46 * F), title, font=ImageFont.truetype(os.path.join(vox.FONTS, 'ArchivoBlack.ttf'), 44 * F), fill=ink)
    d.text((gap, 104 * F), sub, font=ImageFont.truetype(os.path.join(vox.FONTS, 'Inter400.ttf'), 20 * F), fill=(90, 86, 80))
    board.save(out)


TOPICS = [
    ('The history of Japan', 'The history of Japan: from the samurai and the shogun of Edo to the Meiji emperor and the empire, Kyoto and Tokyo across the centuries',
     dict(headline='The shogun steps down', dateline='Kyoto · 9 November 1867', tag='THE MEIJI RESTORATION')),
    ('World War II', 'World War II: the Nazi invasion, Pearl Harbor, the Allied landings on D-Day, Hiroshima; a war and battle from 1939 to 1945',
     dict(headline='Allies land in Normandy', dateline='6 June 1944', tag='D-DAY')),
    ('Black holes', 'Black holes: the event horizon, a supernova collapsing, the black hole at the centre of the galaxy, light years across the universe', {}),
    ('The history of physics', 'The history of physics: four centuries of history, Newton and Einstein, every physicist, theory of gravity and the universe, an era of discovery',
     dict(headline='Gravity bends light.', accent=['bends', 'light.'], tag='EINSTEIN · 1915')),
    ('Berserk, a dark manga', 'Berserk: a dark seinen manga of violence, despair and revenge, the Eclipse massacre, demon and betrayal, chapter by chapter', {}),
    ('One Piece, an adventure manga', 'One Piece: a shonen adventure manga about friendship, a pirate crew, a treasure and a dream, volume after volume',
     dict(headline='THE GRAND LINE', tag='CHAPTER 100')),
    ('Artificial intelligence', 'Artificial intelligence: how a neural network and machine learning learn from data, algorithms and software, AI today', {}),
    ('The history of computers', 'The history of computers: ENIAC, punch card, the first computer, the vacuum tube, Turing and the IBM mainframe, computer history',
     dict(headline='CALCULATIONS PER SECOND', bars=[['ENIAC 1946', 5], ['IBM 704 1954', 40], ['CRAY-1 1976', 100]], unit='')),
    ('The 2008 financial crash', 'The 2008 financial crash: a housing bubble, a bank collapse, recession and debt, the stock market and the economy', {}),
    ('Moroccan architecture', 'The architecture of Moroccan riads in Marrakech and Fes: zellige craft, tradition and heritage of Morocco, palace and mosque', {}),
]


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == '--page':
        if os.environ.get('VOX_PALETTE'):
            page(a[2], *(int(v) for v in a[3:5]))
        else:
            _child(a, a[1])
    elif a[0] == '--card':
        page_topic = a[2] if len(a) > 2 and a[2] != '-' else None
        card(a[1], topic=page_topic)
    elif a[0] == '--topic':
        _child(['--card', a[2], a[1]], json.dumps({'palette': 'auto', 'text': a[1], 'subject': a[1]}))
    elif a[0] == '--all':
        sys.path.insert(0, HERE)
        from identities import IDENTITIES
        outd = a[1]
        os.makedirs(outd, exist_ok=True)
        names = list(IDENTITIES)
        cards = []
        for i, n in enumerate(names):
            _child(['--page', n, os.path.join(outd, f'identity_{i + 1:02d}_{n}.png'), str(i + 1), str(len(names))], n)
            cp = os.path.join(outd, f'card_{n}.png')
            _child(['--card', cp, '-'], n)
            cards.append(cp)
        _grid(cards, 5, os.path.join(outd, 'identities_overview.png'), 'VISUAL IDENTITIES',
              sub='Ten art-directed starting points. The engine analyses each topic and builds the final identity from them.')
        tc = []
        for i, (title, text, scene) in enumerate(TOPICS):
            cp = os.path.join(outd, f'topic_{i + 1:02d}.png')
            _child(['--card', cp, title], json.dumps({'palette': 'auto', 'text': text, 'subject': title}), scene)
            tc.append(cp)
        _grid(tc, 5, os.path.join(outd, 'identities_context.png'), 'SAME CATEGORY, DIFFERENT FILM',
              sub='Identities derived by the engine from each topic: sub-genre, second subject, region, period and tone change the result.')
