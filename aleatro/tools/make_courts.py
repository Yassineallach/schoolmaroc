#!/usr/bin/env python3
"""Generate the court-card figures (scripts/court_art.gd).

Each J / Q / K of each suit is a half figure, 47 x 49 pixels, stored as
rows of palette letters. The game recolours it per suit and paints it
twice (the second time upside down) to make a double-ended 70 x 98 card.

The figures are built from shapes: a grey egg face in profile inside a
dark mass of hair, hood or beard; robes in wide sweeping bands or checks;
sashes, belts, crowns and staffs that run past the card's inner frame.
Hearts and diamonds face the other way.

Palette letters (colours are set per suit in deck_art.gd):
  .  empty      K  ink (the suit's dark)   D  dark mass (hair, hood, robe)
  M  main colour      m  its shade
  G  orange / gold    g  its shade
  B  light accent     b  its shade
  W  white            F  face    f  face shade

Usage:  python3 tools/make_courts.py
"""
import math
import os

CW, CH = 70, 98          # card
HW, HH = 47, 49          # half figure, centre column 23, placed at x 11.., y 0..48
X0 = (CW - HW) // 2      # 11
DROP = 4                 # rows the whole figure is moved down

class G:
    def __init__(s): s.g = [['.'] * HW for _ in range(HH)]
    def set(s, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < HW and 0 <= y < HH: s.g[y][x] = c
    def get(s, x, y):
        x, y = int(x), int(y)
        return s.g[y][x] if 0 <= x < HW and 0 <= y < HH else '.'
    def ellipse(s, cx, cy, rx, ry, c, only=None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1:
                    if only is None or s.get(x, y) in only: s.set(x, y, c)
    def poly(s, pts, c, only=None):
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            yc = y + .5; xs = []
            for i in range(len(pts)):
                (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
                if (y1 <= yc < y2) or (y2 <= yc < y1):
                    xs.append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b))):
                    if only is None or s.get(x, y) in only: s.set(x, y, c)
    def line(s, x0, y0, x1, y1, c, w=1, only=None):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(n, 1)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for dx in range(w):
                if only is None or s.get(x + dx, y) in only: s.set(x + dx, y, c)
    def outline(s, ink='K'):
        out = []
        for y in range(HH):
            for x in range(HW):
                if s.get(x, y) != '.': continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= x + dx < HW and 0 <= y + dy < HH and s.get(x + dx, y + dy) not in '.K':
                        out.append((x, y)); break
        for x, y in out: s.set(x, y, ink)

def face(g, cx, cy, facing=-1):
    """Grey egg in profile: light front, shaded back and jaw."""
    g.ellipse(cx, cy, 5.2, 7.2, 'F')
    g.ellipse(cx - facing * 2.2, cy + 2.5, 4, 5.5, 'f', only='F')
    g.ellipse(cx + facing * 0.8, cy - 1.5, 3.8, 5.2, 'F', only='f')

def bands(g, x0, x1, y0, y1, seq, tilt=0.0, bow=0.0, only=None):
    """Fill a region with wide bands; tilt slants them, bow curves them outward."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if only is not None and g.get(x, y) not in only: continue
            side = 1 if x >= 23 else -1
            u = x + tilt * side * (y - y0) + bow * ((x - 23) / 23) * (y - y0)
            g.set(x, y, seq[int(u) % len(seq)])

def checker(g, x0, x1, y0, y1, a, b, only=None):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if only is None or g.get(x, y) in only:
                g.set(x, y, a if (x + y) % 2 else b)

def curve(g, pts_fn, y0, y1, width, c, edge, only):
    """A thick band following x = pts_fn(y)."""
    for y in range(y0, y1 + 1):
        x = pts_fn(y)
        for dx in range(width):
            if g.get(x + dx, y) in only:
                g.set(x + dx, y, edge if dx in (0, width - 1) else c)


def staff(g, x, y0, y1, jewel):
    for y in range(y0, y1 + 1): g.set(x, y, 'G'); g.set(x + 1, y, 'g')
    for y in range(y0 + 7, y1 - 2, 8):
        for dx in (-1, 0, 1, 2): g.set(x + dx, y, 'G')
        g.set(x, y, jewel)
    g.ellipse(x + 1, y0 - 2, 2.2, 2.6, 'G')
    g.ellipse(x + 1, y0 - 2, 1.2, 1.5, jewel)
    g.set(x, y0 - 5, 'G'); g.set(x + 1, y0 - 5, 'G'); g.set(x, y0 - 6, jewel)

def crown(g, cx, top, half, jewel):
    """A crown about as wide as the head: five points, a jewelled band, a rim."""
    tips = (-half, -half // 2, 0, half // 2, half)
    for dx in tips:
        g.set(cx + dx, top, jewel)
        g.set(cx + dx, top + 1, 'G')
    for y in (top + 2, top + 3):
        for x in range(cx - half, cx + half + 1): g.set(x, y, 'G')
    for x in range(cx - half + 1, cx + half, 2): g.set(x, top + 3, jewel)
    for x in range(cx - half, cx + half + 1): g.set(x, top + 4, 'g')

def king(suit):
    """Kings: mantle in sweeping bands, belt, two staffs."""
    g = G()
    # robe: shoulders to hem, slight flare; sleeves bulge at the sides
    g.ellipse(23, 33, 17, 11, 'M')
    g.poly([(8, 33), (38, 33), (40, 48), (6, 48)], 'M')
    g.ellipse(8, 35, 5, 9, 'M'); g.ellipse(38, 35, 5, 9, 'M')
    seq = ['MMMWGGGW', 'MMWGGWBW', 'MMMWGGWW', 'MMWBBWGW'][suit]
    bands(g, 0, 46, 22, 48, seq, tilt=-0.55, bow=0.2, only='M')
    # dark beard/hair mass around the head, falling onto the chest
    g.ellipse(23, 16, 9.5, 11, 'D')
    g.poly([(15, 20), (31, 20), (28, 31), (18, 31)], 'D')
    face(g, 21, 15, facing=-1)
    # chest yoke: blue/white checks under the beard
    checker(g, 17, 29, 26, 29, 'B', 'W', only='D')
    # white front panel with ink buttons down the robe
    for y in range(30, 49):
        for x in (21, 22, 23, 24, 25): g.set(x, y, 'W')
        g.set(20, y, 'K'); g.set(26, y, 'K')
        if y % 3 == 0: g.set(23, y, 'K')
    # checkered blue belt across the robe
    for x in range(5, 42):
        g.set(x, 35, 'K'); g.set(x, 39, 'K')
        for y in (36, 37, 38): g.set(x, y, 'B' if (x + y) % 2 else 'W')
    crown(g, 22, 3, 5, 'B')
    # hands at the cuffs holding staffs on both sides
    g.ellipse(4, 40, 2, 1.8, 'F'); g.ellipse(42, 30, 2, 1.8, 'F')
    staff(g, 2, 8, 48, 'B'); staff(g, 43, 14, 48, 'M')
    g.outline()
    return g

def queen(suit):
    g = G()
    # long robe: dark centre with a lace front, main-colour side panels
    g.poly([(12, 22), (34, 22), (40, 34), (41, 48), (5, 48), (6, 34)], 'D')
    g.poly([(5, 30), (12, 24), (14, 48), (5, 48)], 'M')
    g.poly([(41, 30), (34, 24), (32, 48), (41, 48)], 'M')
    checker(g, 0, 46, 22, 48, 'M', 'W', only='M')
    for y in range(26, 49):
        for x in range(21, 26):
            if g.get(x, y) == 'D': g.set(x, y, 'W' if (x + y) % 2 == 0 else 'D')
    # orange trim lines in the dark robe
    for y in range(24, 49, 4):
        g.line(13, y, 33, y + 3, 'G', only='D')
    # a broad sash sweeping across the robe in an S
    amp = [9, -9, 8, -8][suit]
    curve(g, lambda y: int(21 + amp * math.sin((y - 22) / 26 * math.pi * 1.2)), 22, 48, 5, 'B', 'b', 'DMWG')
    # veil / hood: a dark mass framing the face and falling to the shoulders
    g.ellipse(23, 17, 10, 12, 'D')
    face(g, 23, 16, facing=1)
    crown(g, 23, 4, 4, 'B')
    g.ellipse(41, 30, 2, 1.8, 'F')
    staff(g, 42, 7, 48, 'B')
    for y in (14, 24, 34):
        g.ellipse(43, y, 2, 1.6, 'M')
    g.outline()
    return g

def jack(suit):
    g = G()
    # doublet with checkered side panels
    g.poly([(10, 24), (36, 24), (40, 30), (40, 48), (6, 48), (6, 30)], 'M')
    checker(g, 6, 13, 26, 48, 'M', 'W', only='M')
    checker(g, 33, 40, 26, 48, 'M', 'W', only='M')
    for y in range(26, 49): g.set(14, y, 'K'); g.set(32, y, 'K')
    bands(g, 15, 31, 24, 48, ['MMMWW', 'MMWBW', 'MMMWB', 'MMWWG'][suit], tilt=0.6, only='M')
    # ruff collar
    g.ellipse(23, 24, 11, 3, 'W')
    for x in range(13, 34, 3): g.set(x, 25, 'B')
    # orange sash from the right shoulder to the left hip
    if suit % 2 == 0:
        curve(g, lambda y: int(34 - (y - 24) * 1.05), 24, 48, 5, 'G', 'g', 'MWK')
    else:
        curve(g, lambda y: int(10 + (y - 24) * 1.05), 24, 48, 5, 'G', 'g', 'MWK')
    # belt with an oval buckle across the middle
    for x in range(5, 42):
        g.set(x, 38, 'K'); g.set(x, 39, 'W'); g.set(x, 40, 'W'); g.set(x, 41, 'K')
    g.ellipse(23, 39.5, 4, 2.6, 'G'); g.ellipse(23, 39.5, 2.2, 1.2, 'M')
    # hair and a big floppy hat with a white band
    g.ellipse(22, 17, 8, 9, 'D')
    for k in range(5): g.set(13 - k % 2, 13 + k * 2, 'D'); g.set(31 + k % 2, 14 + k * 2, 'D')
    face(g, 22, 16, facing=1)
    g.ellipse(23, 8, 8.5, 3.6, 'M')
    g.ellipse(20, 6.5, 4.5, 2.2, 'M')
    for x in range(15, 31): g.set(x, 10, 'W'); g.set(x, 11, 'K')
    g.ellipse(18, 6, 2, 1, 'W')
    g.ellipse(41, 30, 2, 1.8, 'F')
    staff(g, 42, 5, 30, 'B')
    g.outline()
    return g



def court(rank, suit):
    g = {"J": jack, "Q": queen, "K": king}[rank](suit)
    rows = ["".join(r) for r in g.g]
    # sit the figure a little lower so the head is about a quarter of the
    # way down the card; the hem it loses is under the upside-down half
    rows = ["." * HW] * DROP + rows[:-DROP]
    if suit in (1, 3):  # hearts and diamonds face the other way
        rows = [r[::-1] for r in rows]
    return rows


def write_gd(path):
    out = [
        "class_name CourtArt",
        "extends RefCounted",
        "",
        "## Generated by tools/make_courts.py - edit that, not this file.",
        "## Court half figures, %d x %d, keyed \"<rank letter><suit index>\"" % (HW, HH),
        "## (suits: 0 spade, 1 heart, 2 club, 3 diamond). Letters are palette",
        "## keys; see the tool for what each one means.",
        "",
        "const HALVES := {",
    ]
    for rank in "JQK":
        for suit in range(4):
            out.append('\t"%s%d": [' % (rank, suit))
            for r in court(rank, suit):
                assert len(r) == HW
                out.append('\t\t"%s",' % r)
            out.append("\t],")
    out.append("}")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    write_gd(os.path.join(root, "scripts", "court_art.gd"))
