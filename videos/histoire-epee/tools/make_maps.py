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


def curves(path, Wd=1300, Hd=820):
    """C01: two hand-drawn trends crossing (illustrative, no numbers: the narration gives none):
    production rising, price falling, around the turn of the 20th century."""
    import numpy as np
    r = np.random.default_rng(1900)
    im = Image.new('RGB', (Wd, Hd), 'white')
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 110, 60, Wd - 60, Hd - 90
    d.line([(x0, y0), (x0, y1), (x1, y1)], fill='black', width=7)          # the two axes
    d.polygon([(x0 - 14, y0 + 22), (x0, y0 - 6), (x0 + 14, y0 + 22)], fill='black')
    d.polygon([(x1 - 22, y1 - 14), (x1 + 6, y1), (x1 - 22, y1 + 14)], fill='black')
    xs = np.linspace(x0 + 30, x1 - 40, 120)
    u = (xs - xs[0]) / (xs[-1] - xs[0])
    up = y1 - 40 - (y1 - y0 - 120) * (0.08 + 0.92 / (1 + np.exp(-(u - 0.55) * 11)))
    down = y0 + 70 + (y1 - y0 - 160) * (0.05 + 0.95 / (1 + np.exp(-(u - 0.5) * 10)))
    for ys, wd in ((up, 9), (down, 9)):
        ys = ys + r.normal(0, 1.4, len(ys))
        d.line(list(zip(xs, ys)), fill='black', width=wd, joint='curve')
    im.save(path)
    json.dump({'up_end': [float(xs[-1]) / Wd, float(up[-1]) / Hd], 'down_end': [float(xs[-1]) / Wd, float(down[-1]) / Hd]},
              open(path[:-4] + '.json', 'w'))
    print(path)


def country_map(path, iso, pin, Wd=1300, Hd=900, pad=60, min_ring=8, extra=(), lon_min=-999):
    """One country's outline (its larger rings only) with a pen pin; the pin's place is saved
    beside the image so the pen can write the label there."""
    rings = [r for poly in country(iso)['polys'] for r in poly if len(r) >= min_ring and min(x for x, _ in r) > lon_min]
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
    if pin:
        px, py = P(*pin)
        d.ellipse((px - 22, py - 70, px + 22, py - 26), outline='black', width=6)
        d.ellipse((px - 6, py - 54, px + 6, py - 42), fill='black')
        d.line((px, py - 26, px, py), fill='black', width=6)
    else:                                       # no pin: the narration names only the country
        px, py = Wd / 2, Hd / 2
    im.save(path)
    json.dump({'pin': [px / Wd, py / Hd], 'extra': [[P(*e)[0] / Wd, P(*e)[1] / Hd] for e in extra]},
              open(path[:-4] + '.json', 'w'))
    print(path)


def region_map(path, continent, box, pins, Wd=1400, Hd=1000, pad=40, waves=(), frame=False):
    """The coastline of a continent inside a lon/lat box (no inner borders: the countries are
    filled together and only the outer edge is kept), with pen pins at `pins`."""
    import numpy as np
    from scipy import ndimage
    lon0, lon1, lat0_, lat1 = box
    latm = math.radians((lat0_ + lat1) / 2)
    k = min((Wd - 2 * pad) / ((lon1 - lon0) * math.cos(latm)), (Hd - 2 * pad) / (lat1 - lat0_))

    def P(lon, lat):
        return (pad + (lon - lon0) * math.cos(latm) * k, pad + (lat1 - lat) * k)
    m = Image.new('L', (Wd, Hd), 0)
    dm = ImageDraw.Draw(m)
    for c in GEO:
        if continent and c['continent'] not in (continent if isinstance(continent, tuple) else (continent,)):
            continue
        for poly in c['polys']:
            for j, ring in enumerate(poly):
                dm.polygon([P(x, y) for x, y in ring], fill=0 if j else 255)
    a = np.asarray(m) > 0
    edge = a ^ ndimage.binary_erosion(a, iterations=3)
    if not frame:
        edge[:pad // 2 + 4, :] = edge[-pad // 2 - 4:, :] = False      # the box's own edge is not a coast
        edge[:, :pad // 2 + 4] = edge[:, -pad // 2 - 4:] = False
    else:
        edge[:pad // 2 + 3, :] = edge[-pad // 2 - 3:, :] = False
        edge[:, :pad // 2 + 3] = edge[:, -pad // 2 - 3:] = False
    im = Image.fromarray(np.where(edge, 0, 255).astype(np.uint8)).convert('RGB')
    d = ImageDraw.Draw(im)
    out = []
    for p in pins:
        lon, lat = p[0], p[1]
        px, py = P(lon, lat)
        out.append([px / Wd, py / Hd])
        if len(p) > 2 and not p[2]:                               # a route end with no pin
            continue
        d.ellipse((px - 22, py - 70, px + 22, py - 26), outline='black', width=6)
        d.ellipse((px - 6, py - 54, px + 6, py - 42), fill='black')
        d.line((px, py - 26, px, py), fill='black', width=6)
    if frame:                                                 # an inset frame closes the cut-off land
        im_a = np.asarray(im.convert('L')) < 128
        d.rectangle((pad // 2, pad // 2, Wd - pad // 2, Hd - pad // 2), outline='black', width=6)
    if waves:
        for wx, wy in waves:
            px, py = P(wx, wy)
            for k in range(3):
                d.arc((px - 40 + k * 30, py - 12, px - 10 + k * 30, py + 12), 200, 340, fill='black', width=4)
    im.save(path)
    json.dump({'pin': out[0], 'pins': out}, open(path[:-4] + '.json', 'w'))
    print(path)


def dashed_sword(path, Wd=1500, Hd=520):
    """C01: the sword that does not exist yet (« Il manquait une arme qui réunisse les deux »):
    a straight sword's outline in dashes, empty, drawn by the pen."""
    import numpy as np
    im = Image.new('RGB', (Wd, Hd), 'white')
    d = ImageDraw.Draw(im)
    cy = Hd / 2
    # outline: pommel, grip, guard, long straight blade, point (left to right)
    pts = [(70, cy - 34), (120, cy - 46), (150, cy - 22), (330, cy - 22), (330, cy - 80), (370, cy - 80),
           (370, cy - 34), (1300, cy - 30), (1440, cy), (1300, cy + 30), (370, cy + 34), (370, cy + 80),
           (330, cy + 80), (330, cy + 22), (150, cy + 22), (120, cy + 46), (70, cy + 34), (55, cy)]
    pts.append(pts[0])
    on, gap = 26, 18
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        k = 0.0
        while k < L:
            e = min(L, k + on)
            d.line([(x0 + (x1 - x0) * k / L, y0 + (y1 - y0) * k / L), (x0 + (x1 - x0) * e / L, y0 + (y1 - y0) * e / L)],
                   fill='black', width=7)
            k += on + gap
    im.save(path)
    print(path)


if __name__ == '__main__':
    A = lambda c: os.path.join(PROJ, 'assets', c + '.png')
    country_map(A('M01'), 'DEU', (10.95, 52.14), Wd=1000, Hd=1100)          # Schöningen, Lower Saxony
    country_map(A('M02'), 'TUR', (38.36, 38.38), Wd=1500, Hd=800)           # Arslantepe, near Malatya
    country_map(A('M03'), 'CHN', None, Wd=1400, Hd=1050)                    # « connue en Chine »: the country only
    country_map(A('M04'), 'CHE', (6.14, 46.20), Wd=1400, Hd=900)            # Geneva
    dashed_sword(A('C01'))
