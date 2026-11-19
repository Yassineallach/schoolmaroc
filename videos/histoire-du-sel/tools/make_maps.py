"""Pen-drawn maps for the board, as black line drawings on white (assets/Mxx.png), so they go
through the same pen as the ChatGPT drawings. Natural Earth 1:110m (public domain, bundled).

    python tools/make_maps.py
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
SK = os.path.join(PROJ, '..', '..', '.claude', 'skills', 'paper-explainer-video')
GEO = json.load(open(os.path.join(SK, 'assets', 'geo', 'countries_110m.json')))
FONT = os.path.join(SK, 'assets', 'fonts', 'Fraunces500i.ttf')


def country(iso):
    return next(c for c in GEO if c['iso'] == iso)


def us_map(path, pin=(-123.6, 47.8), label='Parc national Olympic'):
    Wd, Hd, pad = 1500, 900, 70
    lat0 = math.radians(39)
    rings = []
    for poly in country('USA')['polys']:
        for ring in poly:
            if all(-128 < x < -65 and 24 < y < 50 for x, y in ring):
                rings.append(ring)
    xs = [x * math.cos(lat0) for r in rings for x, _ in r]
    ys = [y for r in rings for _, y in r]
    k = min((Wd - 2 * pad) / (max(xs) - min(xs)), (Hd - 2 * pad - 120) / (max(ys) - min(ys)))
    ox, oy = min(xs), max(ys)

    def P(lon, lat):
        return (pad + (lon * math.cos(lat0) - ox) * k, pad + 120 + (oy - lat) * k)
    im = Image.new('RGB', (Wd, Hd), 'white')
    d = ImageDraw.Draw(im)
    for r in rings:
        d.line([P(x, y) for x, y in r] + [P(*r[0])], fill='black', width=6, joint='curve')
    px, py = P(*pin)
    # a hand-drawn pin: a ring with a dot, on a short stem
    d.ellipse((px - 22, py - 70, px + 22, py - 26), outline='black', width=6)
    d.ellipse((px - 6, py - 54, px + 6, py - 42), fill='black')
    d.line((px, py - 26, px, py), fill='black', width=6)
    # the label is not drawn here: the pen writes it on the board, left to right (board.write)
    im.save(path)
    json.dump({'pin': [px / Wd, py / Hd]}, open(path[:-4] + '.json', 'w'))
    print(path)


def country_map(path, iso, pin, Wd=1300, Hd=900, pad=60, min_ring=8):
    """One country's outline (its larger rings only) with a pen pin; the pin's place is saved
    beside the image so the pen can write the label there."""
    rings = [r for poly in country(iso)['polys'] for r in poly if len(r) >= min_ring]
    lat0 = math.radians(sum(y for r in rings for _, y in r) / sum(len(r) for r in rings))
    xs = [x * math.cos(lat0) for r in rings for x, _ in r]
    ys = [y for r in rings for _, y in r]
    k = min((Wd - 2 * pad) / (max(xs) - min(xs)), (Hd - 2 * pad) / (max(ys) - min(ys)))
    ox, oy = min(xs), max(ys)
    w_, h_ = (max(xs) - min(xs)) * k, (max(ys) - min(ys)) * k
    sx, sy = (Wd - w_) / 2, (Hd - h_) / 2

    def P(lon, lat):
        return (sx + (lon * math.cos(lat0) - ox) * k, sy + (oy - lat) * k)
    im = Image.new('RGB', (Wd, Hd), 'white')
    d = ImageDraw.Draw(im)
    for r in rings:
        d.line([P(x, y) for x, y in r] + [P(*r[0])], fill='black', width=6, joint='curve')
    px, py = P(*pin)
    d.ellipse((px - 22, py - 70, px + 22, py - 26), outline='black', width=6)
    d.ellipse((px - 6, py - 54, px + 6, py - 42), fill='black')
    d.line((px, py - 26, px, py), fill='black', width=6)
    im.save(path)
    json.dump({'pin': [px / Wd, py / Hd]}, open(path[:-4] + '.json', 'w'))
    print(path)


if __name__ == '__main__':
    us_map(os.path.join(PROJ, 'assets', 'M01.png'))
    country_map(os.path.join(PROJ, 'assets', 'M02.png'), 'CHN', (104.78, 29.35))     # Zigong, Sichuan: the salt river
    country_map(os.path.join(PROJ, 'assets', 'M03.png'), 'AUT', (13.65, 47.56))      # Hallstatt
