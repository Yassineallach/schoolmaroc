"""Whole-board previews of alternative layouts (the user: « I don't like how the scenes are arranged »).
    python tools/layout_options.py   ->  out/layout_A.png ... out/layout_D.png, and layouts/<X>.json
"""
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from make_layout import ROWS
import cutout

ORDER = [c for r in ROWS for c in r]
ACT = {c: i for i, r in enumerate(ROWS) for c in r}
SX, SY = 1930, 1400


def current():
    return json.load(open('layout.json'))


def snake():
    """Rows read alternately left-to-right and right-to-left: no long carriage return, every move is to a neighbour."""
    out, rnd = {}, random.Random(3)
    per = 8
    for i, c in enumerate(ORDER):
        r, k = divmod(i, per)
        x = k if r % 2 == 0 else per - 1 - k
        out[c] = (x * SX + rnd.uniform(-90, 90), r * SY + rnd.uniform(-70, 70))
    return out


def line():
    """One long timeline, left to right; each act a little apart; drawings alternate slightly up and down."""
    out, x = {}, 0
    for i, c in enumerate(ORDER):
        if i and ACT[c] != ACT[ORDER[i - 1]]:
            x += 700
        out[c] = (x, (i % 2) * 520 - 260)
        x += SX
    return out


def walk():
    """A compact random walk (L'histoire du sel, L'histoire de l'épée): each next drawing a free neighbour, any direction."""
    rnd = random.Random(1795)
    COLS, NR = 10, 6
    NB = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    def go(path, used):
        if len(path) == len(ORDER):
            return path
        x, y = path[-1]
        opts = [(x + a, y + b) for a, b in NB if 0 <= x + a < COLS and 0 <= y + b < NR and (x + a, y + b) not in used]
        rnd.shuffle(opts)
        opts.sort(key=lambda c: (sum((c[0] + a, c[1] + b) not in used and 0 <= c[0] + a < COLS and 0 <= c[1] + b < NR for a, b in NB) < 2,
                                 abs(c[0] - x) + abs(c[1] - y) > 1))
        for c in opts:
            r = go(path + [c], used | {c})
            if r:
                return r
    p = go([(0, 0)], {(0, 0)})
    return {c: (x * 1380 * 1.6 + rnd.uniform(-70, 70), y * 880 * 1.6 + rnd.uniform(-50, 50)) for c, (x, y) in zip(ORDER, p)}


def preview(lay, path, title):
    xs = [p[0] for p in lay.values()]; ys = [p[1] for p in lay.values()]
    x0, y0 = min(xs) - 1100, min(ys) - 800
    Wb, Hb = max(xs) - x0 + 1100, max(ys) - y0 + 800
    k = min(3600 / Wb, 2000 / Hb)
    im = Image.new('RGB', (int(Wb * k), int(Hb * k) + 90), (231, 214, 178))
    d = ImageDraw.Draw(im)
    pts = [((lay[c][0] - x0) * k, (lay[c][1] - y0) * k + 90) for c in ORDER]
    d.line(pts, fill=(170, 120, 100), width=3)
    f = ImageFont.truetype('/home/user/schoolmaroc/.claude/skills/paper-explainer-video/assets/fonts/Fraunces500i.ttf', 44)
    fs = ImageFont.truetype('/home/user/schoolmaroc/.claude/skills/paper-explainer-video/assets/fonts/Fraunces500i.ttf', 22)
    d.text((20, 20), title, font=f, fill=(40, 26, 16))
    for c, (px, py) in zip(ORDER, pts):
        src = f'assets/{c}.png'
        w = int(1500 * k * 0.9)
        if os.path.exists(src):
            g = cutout.ink_image(src, w)
            if g.height > 880 * k * 0.9:
                g = cutout.ink_image(src, int(w * 880 * k * 0.9 / g.height))
            im.paste(g, (int(px - g.width / 2), int(py - g.height / 2)), g)
        else:
            d.rectangle((px - w / 2, py - w * 0.29, px + w / 2, py + w * 0.29), outline=(150, 120, 90), width=2)
        d.text((px, py + w * 0.33), f'{c} · acte {ACT[c] + 1}', font=fs, fill=(126, 34, 25), anchor='mt')
    im.save(path)


if __name__ == '__main__':
    os.makedirs('layouts', exist_ok=True)
    for key, fn, title in [('A', current, 'A · actuel : une rangée par acte'),
                           ('B', snake, 'B · serpentin : aller-retour, toujours un voisin'),
                           ('C', line, 'C · une seule ligne du temps'),
                           ('D', walk, 'D · marche libre (sel, épée)')]:
        lay = fn()
        json.dump({c: [round(v) for v in p] for c, p in lay.items()}, open(f'layouts/{key}.json', 'w'))
        preview(lay, f'out/layout_{key}.png', title)
        print(key)
