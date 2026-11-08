"""Animated editorial maps from Natural Earth 1:110m data (assets/geo, public domain).

Printed-map look on the paper: beige land with a faint texture, fine ink coastlines, the sea is the
paper itself, a light graticule; countries the narration names fill with terracotta.

    M = WorldMap(box=(160, 120, 1760, 960))                  # where the map sits on screen
    view = M.zoom(t, [(0.0, M.WORLD), (2.0, M.around('United Kingdom', 1400))])   # timed views
    M.draw(s.mid, view, t, highlight={'GBR': w(cue(1, 'Britain'))})
    M.border(s.mid, view, 'GBR', t, start)                  # outline draws on, then fills
    M.route(s.mid, view, [M.city('London'), M.city('Geneva')], t, start)
    M.marker(s.mid, view, M.city('Geneva'), 'GENEVA', t, start)
    card = map_card(M, view, 900, 560)                       # a printed map as a paper object for presets

Views are (lon_min, lat_min, lon_max, lat_max). Use WorldMap.around(name_or_lonlat, km) to frame a place.
"""
import json, math, os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from vox import F_HEAD, F_TYPE, INK
from style import sfx
import presets as P
import annotate as A

HERE = os.path.dirname(os.path.abspath(__file__))
GEO = os.path.join(os.path.dirname(HERE), 'assets', 'geo')
from palette import ACTIVE as PAL, _mix
LAND = PAL.land
LAND_DARK = _mix(PAL.land, PAL.ink2, 0.08)
COAST = PAL.coast
BORDER = PAL.border
GRID = PAL.line
TERRA = ACCENT = PAL.accent


@lru_cache(maxsize=1)
def _data():
    countries = json.load(open(os.path.join(GEO, 'countries_110m.json')))
    for c in countries:
        xs = [p[0] for poly in c['polys'] for ring in poly for p in ring]
        ys = [p[1] for poly in c['polys'] for ring in poly for p in ring]
        c['bbox'] = (min(xs), min(ys), max(xs), max(ys))
    cities = json.load(open(os.path.join(GEO, 'cities_110m.json')))
    return countries, cities


def _merc(lat):
    lat = max(-84.0, min(84.0, lat))
    return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


def _eio(x):
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


class WorldMap:
    WORLD = (-170.0, -58.0, 190.0, 80.0)

    def __init__(self, box=(0, 0, 1920, 1080), mercator=True, graticule=15):
        self.box, self.mercator, self.graticule = box, mercator, graticule
        self.countries, self.cities = _data()
        self.by = {}
        for c in self.countries:
            for k in (c['iso'], c['name'], c.get('long')):
                if k:
                    self.by[k.lower()] = c

    # ---- lookup -------------------------------------------------------------
    def country(self, key):
        c = self.by.get(key.lower())
        if c is None:
            raise KeyError(f'no country {key!r}')
        return c

    def city(self, name):
        for c in self.cities:
            if c['name'].lower() == name.lower():
                return (c['lon'], c['lat'])
        raise KeyError(f'no city {name!r} in the 1:110m list; pass (lon, lat) instead')

    def around(self, where, km=1500, aspect=None):
        """A view centred on a country or (lon, lat), about `km` wide, matching the box aspect."""
        if isinstance(where, str):
            x0, y0, x1, y1 = self.country(where)['bbox']
            lon, lat = (x0 + x1) / 2, (y0 + y1) / 2
            km = max(km, (x1 - x0) * 111 * math.cos(math.radians(lat)) * 1.4)
        else:
            lon, lat = where
        aspect = aspect or (self.box[2] - self.box[0]) / (self.box[3] - self.box[1])
        dlon = km / (111.0 * max(0.2, math.cos(math.radians(lat))))
        dy = dlon / aspect
        if self.mercator:
            ym = _merc(lat)
            lat0 = math.degrees(2 * math.atan(math.exp(math.radians(ym - dy / 2))) - math.pi / 2)
            lat1 = math.degrees(2 * math.atan(math.exp(math.radians(ym + dy / 2))) - math.pi / 2)
        else:
            lat0, lat1 = lat - dy / 2, lat + dy / 2
        return (lon - dlon / 2, lat0, lon + dlon / 2, lat1)

    # ---- projection -----------------------------------------------------------
    def project(self, view, lon, lat):
        x0, y0, x1, y1 = self.box
        a, b, c, d = view
        fy = _merc if self.mercator else (lambda v: v)
        px = x0 + (lon - a) / (c - a) * (x1 - x0)
        py = y1 - (fy(lat) - fy(b)) / (fy(d) - fy(b)) * (y1 - y0)
        return px, py

    def zoom(self, t, keys):
        """keys: [(time, view), ...] -> the view at time t, eased and log-interpolated so the
        zoom feels like a camera, not a slide."""
        if t <= keys[0][0]:
            return keys[0][1]
        for (t0, v0), (t1, v1) in zip(keys[:-1], keys[1:]):
            if t <= t1:
                u = _eio((t - t0) / (t1 - t0))
                c0 = ((v0[0] + v0[2]) / 2, (v0[1] + v0[3]) / 2)
                c1 = ((v1[0] + v1[2]) / 2, (v1[1] + v1[3]) / 2)
                w0, w1 = v0[2] - v0[0], v1[2] - v1[0]
                h0, h1 = v0[3] - v0[1], v1[3] - v1[1]
                wl = math.exp(math.log(w0) + (math.log(w1) - math.log(w0)) * u)
                hl = math.exp(math.log(h0) + (math.log(h1) - math.log(h0)) * u)
                k = (w0 - wl) / (w0 - w1) if abs(w0 - w1) > 1e-6 else u   # centre follows the scale change
                cx, cy = c0[0] + (c1[0] - c0[0]) * k, c0[1] + (c1[1] - c0[1]) * k
                return (cx - wl / 2, cy - hl / 2, cx + wl / 2, cy + hl / 2)
        return keys[-1][1]

    # ---- drawing ----------------------------------------------------------------
    def _rings(self, view, c):
        a, b, cc, d = view
        bx = c['bbox']
        if bx[2] < a - 5 or bx[0] > cc + 5 or bx[3] < b - 5 or bx[1] > d + 5:
            return []
        out = []
        for poly in c['polys']:
            for ri, ring in enumerate(poly):
                out.append((ri, [self.project(view, x, y) for x, y in ring]))
        return out

    def draw(self, layer, view, t=0.0, start=-1.0, highlight=None, colour=TERRA, alpha=1.0):
        """Land, coastlines, borders and graticule for `view`; highlight = {iso_or_name: start_time}
        fills those countries with the accent from their cue."""
        if t < start:
            return
        op = alpha * min(1.0, (t - start) / 0.35) if start > -1 else alpha
        x0, y0, x1, y1 = [int(v) for v in self.box]
        hlk = tuple(sorted((self.country(k)['iso'], round(_eio((t - st) / 0.6), 2)) for k, st in (highlight or {}).items() if t >= st))
        key = (tuple(round(v, 4) for v in view), self.box, hlk, round(op, 2), colour)
        cache = self.__dict__.setdefault('_cache', {})
        if key in cache:
            A._comp(layer, cache[key], x0, y0)
            return
        if len(cache) > 6:
            cache.clear()
        w, h = x1 - x0, y1 - y0
        S = 2
        land = Image.new('L', (w * S, h * S), 0)
        lines = Image.new('L', (w * S, h * S), 0)
        borders = Image.new('L', (w * S, h * S), 0)
        dl, dc, db = ImageDraw.Draw(land), ImageDraw.Draw(lines), ImageDraw.Draw(borders)
        hl = {}
        for key, st in (highlight or {}).items():
            hl[self.country(key)['iso']] = st
        fills = []
        for c in self.countries:
            rings = self._rings(view, c)
            for ri, pts in rings:
                q = [((x - x0) * S, (y - y0) * S) for x, y in pts]
                if len(q) < 3:
                    continue
                dl.polygon(q, fill=0 if ri else 255)
                db.line(q + [q[0]], fill=255, width=S)
            if c['iso'] in hl and t >= hl[c['iso']]:
                fills.append((rings, _eio((t - hl[c['iso']]) / 0.6)))
        coast = land.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
        grid = Image.new('L', (w * S, h * S), 0)
        if self.graticule:
            dg = ImageDraw.Draw(grid)
            a, b, cc, d = view
            g = self.graticule
            for lon in range(int(math.floor(a / g) * g), int(cc) + g, g):
                px, _ = self.project(view, lon, 0)
                for yy in range(0, h * S, 14):
                    dg.line(((px - x0) * S, yy, (px - x0) * S, yy + 6), fill=255, width=1)
            for lat in range(int(math.floor(b / g) * g), int(d) + g, g):
                _, py = self.project(view, 0, lat)
                for xx in range(0, w * S, 14):
                    dg.line((xx, (py - y0) * S, xx + 6, (py - y0) * S), fill=255, width=1)
        tile = Image.new('RGBA', (w, h), (0, 0, 0, 0))

        def paint(mask, col, a_):
            m = mask.resize((w, h), Image.LANCZOS).point(lambda v: int(v * a_ * op))
            lay = Image.new('RGBA', (w, h), col + (0,))
            lay.putalpha(m)
            tile.alpha_composite(lay)
        paint(grid, GRID, 0.6)
        paint(land, LAND, 0.95)
        for rings, k in fills:
            fm = Image.new('L', (w * S, h * S), 0)
            df = ImageDraw.Draw(fm)
            for ri, pts in rings:
                q = [((x - x0) * S, (y - y0) * S) for x, y in pts]
                if len(q) >= 3:
                    df.polygon(q, fill=0 if ri else 255)
            paint(fm, colour, 0.9 * k)
        paint(Image.fromarray(np.minimum(np.asarray(borders), np.asarray(land))), BORDER, 0.55)
        paint(coast, COAST, 0.85)
        fe = 36                                          # feather the edges into the paper
        fm = Image.new('L', (w, h), 0)
        ImageDraw.Draw(fm).rectangle((fe, fe, w - fe, h - fe), fill=255)
        fm = fm.filter(ImageFilter.GaussianBlur(fe / 2))
        tile.putalpha(Image.fromarray((np.asarray(tile.getchannel('A')).astype(np.float32) * np.asarray(fm) / 255).astype(np.uint8)))
        cache[key] = tile
        A._comp(layer, tile, x0, y0)

    def border(self, layer, view, key, t, start, dur=1.4, colour=TERRA, width=5, fill=True, sound=True):
        """The country's outline draws on like a pen tracing the border, then it fills."""
        c = self.country(key)
        if sound:
            sfx('pencil', start, self.project(view, *((c['bbox'][0] + c['bbox'][2]) / 2, 0))[0], dur=dur)
        rings = [pts for ri, pts in self._rings(view, c) if ri == 0]
        if not rings:
            return
        big = max(rings, key=len)
        others = [r for r in rings if r is not big]
        A.stroke(layer, big + big[:1], A.pen((t - start) / dur), width, colour, 1.0, taper=False)
        for r in others:
            A.stroke(layer, r + r[:1], A.pen((t - start - dur * 0.6) / 0.4), width * 0.8, colour, 1.0, taper=False)
        if fill and t > start + dur:
            k = _eio((t - start - dur) / 0.5) * 0.35
            m = Image.new('L', layer.size, 0)
            d = ImageDraw.Draw(m)
            for r in rings:
                d.polygon(r, fill=int(255 * k))
            lay = Image.new('RGBA', layer.size, colour + (0,))
            lay.putalpha(m)
            layer.alpha_composite(lay)

    def route(self, layer, view, stops, t, start, dur=1.6, colour=TERRA, width=5, dashed=True, arc=0.18, head=True, sound=True):
        """A journey drawn stop to stop as gentle arcs, with a dot travelling at the pen tip."""
        pts = [self.project(view, *s) for s in stops]
        if sound:
            sfx('pencil', start, pts[-1][0], dur=dur)
        path = []
        for a, b in zip(pts[:-1], pts[1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            dx, dy = b[0] - a[0], b[1] - a[1]
            c = (mx + dy * arc, my - abs(dx) * arc)
            path += [((1 - u) ** 2 * a[0] + 2 * (1 - u) * u * c[0] + u * u * b[0],
                      (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * c[1] + u * u * b[1]) for u in np.linspace(0, 1, 40)]
        p = A.pen((t - start) / dur)
        if p <= 0:
            return
        if dashed:
            seg = A._resample(path, 4)
            n = len(seg)
            for i in range(0, int(n * p) - 1, 7):
                A.stroke(layer, seg[i:i + 4], 1.0, width, colour, 1.0, taper=False)
        else:
            A.stroke(layer, path, p, width, colour)
        d = ImageDraw.Draw(layer)
        for x, y in pts[:1]:
            d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=colour + (255,))
        if head and p < 1:
            seg = A._resample(path, 2)
            x, y = seg[min(len(seg) - 1, int(len(seg) * p))]
            d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=INK + (255,), outline=PAL.light + (255,), width=3)

    def marker(self, layer, view, lonlat, label, t, start, colour=TERRA, size=34, side='right', sound=True):
        """A map pin drops onto the place with its shadow, then a paper label slides out."""
        x, y = self.project(view, *lonlat)
        if sound:
            sfx('pin', start, x)
        if t < start - 0.15:
            return
        u = A.pop((t - start + 0.15) / 0.45, 0.1)
        drop = (1 - min(1.0, (t - start + 0.15) / 0.15)) * 60
        sh = Image.new('RGBA', (60, 24), (40, 26, 14, 0))
        ImageDraw.Draw(sh).ellipse((10, 4, 50, 20), fill=(40, 26, 14, int(70 * min(1, u))))
        A._comp(layer, sh.filter(ImageFilter.GaussianBlur(3)), x - 30, y - 12)
        S = 3
        n = int(size * 1.6)
        pin = Image.new('RGBA', (n * S, int(n * 1.5) * S), (0, 0, 0, 0))
        dp = ImageDraw.Draw(pin)
        r = n * S * 0.42
        cx = n * S / 2
        dp.ellipse((cx - r, 4 * S, cx + r, 4 * S + 2 * r), fill=colour + (255,))
        dp.polygon([(cx - r * 0.75, 4 * S + r * 1.55), (cx + r * 0.75, 4 * S + r * 1.55), (cx, pin.height - 2)], fill=colour + (255,))
        dp.ellipse((cx - r * 0.38, 4 * S + r * 0.62, cx + r * 0.38, 4 * S + r * 1.38), fill=PAL.light + (255,))
        pin = pin.resize((n, int(n * 1.5)), Image.LANCZOS)
        sc = max(0.05, u)
        pin = pin.resize((max(1, int(pin.width * sc)), max(1, int(pin.height * sc))), Image.BICUBIC)
        A._comp(layer, pin, x - pin.width / 2, y - pin.height - drop)
        if label and t > start + 0.25:
            k = A.pen((t - start - 0.25) / 0.35)
            f = F_HEAD(30)
            tw = ImageDraw.Draw(Image.new('L', (1, 1))).textlength(label, font=f)
            card = P.paper_card(int(tw + 36), 56, seed=len(label), colour=(246, 241, 229))
            ImageDraw.Draw(card).text((card.width / 2, 28), label, font=f, fill=INK + (255,), anchor='mm')
            lx = x + 26 if side == 'right' else x - 26 - card.width
            P.put(layer, P.fade_img(card, k), lx + card.width / 2 + (1 - k) * (-30 if side == 'right' else 30), y - n * 0.75, lift=0.1)


def map_card(M, view, w, h, seed=5, highlight=None, t=99.0):
    """A printed map as a paper object (torn edges, cream ground) for drop / slide / unfold."""
    card = P.paper_card(w, h, seed=seed, colour=PAL.cream)
    keep = M.box
    M.box = (18, 18, w - 18, h - 18)
    M.draw(card, view, t, highlight=highlight)
    M.box = keep
    card.putalpha(P.torn_mask(w, h, seed, amp=5, step=12))
    return card
