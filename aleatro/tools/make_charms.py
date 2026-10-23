#!/usr/bin/env python3
"""Generate the charm card art (scripts/charm_art.gd).

Every charm is a 60 x 75 pixel card (shown at 2x): a white face with an
edge in the charm's rarity colour, the word CHARM stacked down the top-left
corner and again upside down in the bottom-right, and Aleatro's jester
(floppy belled hat, white face, harlequin diamonds, ruff collar) dressed and
posed for what the charm does. Some charms are full-art scenes.

Each card is stored as rows of palette letters plus that card's palette
(letter -> "rrggbb"), so the game only has to paint pixels. The card
edge uses the letter "Z", which the game recolours by rarity.

Usage:  python3 tools/make_charms.py [preview.png]
"""
import math
import os
import sys

W, H = 60, 75
INK = "2b2d42"

# ------------------------------------------------------------------ canvas


class Canvas:
    def __init__(self, pal):
        self.g = [["."] * W for _ in range(H)]
        self.pal = {"K": INK, "w": "ffffff"}
        self.pal.update(pal)

    def set(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H:
            self.g[y][x] = c

    def get(self, x, y):
        x, y = int(round(x)), int(round(y))
        return self.g[y][x] if 0 <= x < W and 0 <= y < H else "."

    def rect(self, x0, y0, x1, y1, c, only=None):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                if only is None or self.get(x, y) in only:
                    self.set(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c, only=None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    if only is None or self.get(x, y) in only:
                        self.set(x, y, c)

    def ring(self, cx, cy, rx, ry, t, c):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
                di = ((x + 0.5 - cx) / max(rx - t, 0.5)) ** 2 + ((y + 0.5 - cy) / max(ry - t, 0.5)) ** 2
                if d <= 1 < di:
                    self.set(x, y, c)

    def poly(self, pts, c, only=None):
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            yc = y + 0.5
            xs = []
            for i in range(len(pts)):
                (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
                if (y1 <= yc < y2) or (y2 <= yc < y1):
                    xs.append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b))):
                    if only is None or self.get(x, y) in only:
                        self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c, w=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(n, 1)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for dx in range(w):
                for dy in range(w):
                    self.set(x + dx - w // 2, y + dy - w // 2, c)

    def outline(self, keep="."):
        """Ink around the art (not around the background)."""
        out = []
        for y in range(H):
            for x in range(W):
                if self.get(x, y) not in keep:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = self.get(x + dx, y + dy)
                    if n not in keep and n != "K":
                        out.append((x, y))
                        break
        for x, y in out:
            self.set(x, y, "K")

    def rows(self):
        return ["".join(r) for r in self.g]


def background(c, fill):
    c.rect(1, 1, W - 2, H - 2, fill)


def card_edge(c):
    """A two-pixel edge: the outer ring is "Z", which the game paints in the
    charm's rarity colour."""
    c.pal["Z"] = "4a6fa5"
    for x in range(W):
        c.set(x, 0, "Z"), c.set(x, H - 1, "Z"), c.set(x, 1, "Z"), c.set(x, H - 2, "Z")
    for y in range(H):
        c.set(0, y, "Z"), c.set(W - 1, y, "Z"), c.set(1, y, "Z"), c.set(W - 2, y, "Z")
    for x, y in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)):
        c.set(x, y, ".")


# ------------------------------------------------------------------ helpers

CX, CY = 30, 39  # centre of the illustration area


def suit_shape(c, suit, cx, cy, s, col):
    """A suit symbol of size s (pixels) centred at (cx, cy)."""
    for y in range(int(cy - s), int(cy + s) + 1):
        for x in range(int(cx - s), int(cx + s) + 1):
            px, py = (x + 0.5 - cx) / (2 * s), (y + 0.5 - cy) / (2 * s)
            inside = False
            if suit == "heart":
                inside = (px + 0.24) ** 2 + (py + 0.14) ** 2 < 0.068 or (px - 0.24) ** 2 + (py + 0.14) ** 2 < 0.068 \
                    or (py > -0.04 and abs(px) < 0.49 * (0.5 - py) / 0.54)
            elif suit == "diamond":
                inside = abs(px) / 0.4 + abs(py) / 0.5 <= 1
            elif suit == "spade":
                inside = (px + 0.23) ** 2 + (py - 0.1) ** 2 < 0.0625 or (px - 0.23) ** 2 + (py - 0.1) ** 2 < 0.0625 \
                    or (py < 0.06 and abs(px) < 0.48 * (py + 0.5) / 0.56) or (py > 0.1 and abs(px) < 0.17 * (py - 0.1) / 0.4)
            else:
                inside = px ** 2 + (py + 0.24) ** 2 < 0.048 or (px + 0.24) ** 2 + (py - 0.08) ** 2 < 0.048 \
                    or (px - 0.24) ** 2 + (py - 0.08) ** 2 < 0.048 or (py > -0.05 and abs(px) < 0.17 * (py + 0.05) / 0.55)
            if inside:
                c.set(x, y, col)


def gem_ring(c, gem, suit):
    """A gold ring with a large faceted gem showing a suit."""
    c.ring(CX, CY + 9, 19, 16, 5, "G")
    c.ring(CX, CY + 9, 19, 16, 1.5, "g")
    c.ellipse(CX, CY + 13, 11, 2.5, ".", only="G")
    c.poly([(CX - 13, CY - 7), (CX + 13, CY - 7), (CX + 9, CY - 18), (CX - 9, CY - 18)], "G")
    c.poly([(CX - 12, CY - 8), (CX + 12, CY - 8), (CX, CY + 7)], "E")
    c.poly([(CX - 12, CY - 8), (CX + 12, CY - 8), (CX + 8, CY - 17), (CX - 8, CY - 17)], "e")
    c.poly([(CX - 4, CY - 17), (CX + 4, CY - 17), (CX + 6, CY - 8), (CX - 6, CY - 8)], "E")
    for x, y in ((CX - 6, CY - 15), (CX - 5, CY - 15), (CX - 6, CY - 14)):
        c.set(x, y, "w")
    suit_shape(c, suit, CX, CY - 4, 4.4, "w")
    c.outline()
    c.pal.update({"G": "f5b82e", "g": "b8801a", "E": gem[0], "e": gem[1]})

def mask(c, mx, my, s, col, shade):
    """A theatre mask with eye holes and a smile."""
    c.ellipse(mx, my, 7 * s, 8 * s, col)
    c.ellipse(mx + 2 * s, my + 2 * s, 5 * s, 6 * s, shade, only=col)
    c.ellipse(mx, my - 1 * s, 6 * s, 6.5 * s, col, only=shade)
    for dx in (-3, 3):
        c.ellipse(mx + dx * s, my - 1.5 * s, 1.6 * s, 1.2 * s, "K")
    c.line(mx - 3 * s, my + 3.5 * s, mx, my + 4.5 * s, "K")
    c.line(mx, my + 4.5 * s, mx + 3 * s, my + 3.5 * s, "K")


# ------------------------------------------------------------------ the jester

def jester(c, cx=30, top=10, s=0.88, hat=("e63946", "a02030"), flaps=("1d6fd1", "13478a"),
           collar=("f5b82e", "b8801a"), face="fdf8f0", key="", grin=False, crown=False, hat_only=False):
    """Aleatro's jester: a floppy hat with bells, a white face with closed
    happy eyes and harlequin diamonds, and a ruff collar. `key` suffixes the
    palette letters so several jesters on one card can differ in colour."""
    H, h, J, j, C, cc, F = ("H" + key, "h" + key, "J" + key, "j" + key, "C" + key, "c" + key, "F" + key)
    # single-letter keys are required: map suffixed names onto spare letters
    names = {"": "HhJjCcF", "2": "NnOoPpU", "3": "SsTtVvX"}[key]
    H, h, J, j, C, cc, F = names
    c.pal.update({H: hat[0], h: hat[1], J: flaps[0], j: flaps[1], C: collar[0], cc: collar[1], F: face,
                  "f": "dcd3c3", "B": "f5d742", "b": "c9a520", "E": "2b2d42", "R": "f07a8a", "r": "c94a5a"})

    def P(x, y):
        return (cx + x * s, top + y * s)

    def poly(pts, col, only=None):
        c.poly([P(x, y) for x, y in pts], col, only)

    def ell(x, y, rx, ry, col, only=None):
        px, py = P(x, y)
        c.ellipse(px, py, rx * s, ry * s, col, only)

    def dot(x, y, col):
        px, py = P(x, y)
        c.set(px, py, col)

    if hat_only:
        _hat(c, P, poly, ell, dot, H, h, J, j, C)
        c.outline(keep=".w")
        return
    # ruff collar
    for k in range(9):
        a = math.pi * (k / 8)
        ell(-13 * math.cos(a), 37 + 4 * math.sin(a), 4.2, 4.6, C if k % 2 == 0 else cc)
    ell(0, 36, 11, 4, C)
    for k in (0, 4, 8):
        a = math.pi * (k / 8)
        ell(-15 * math.cos(a), 39 + 7 * math.sin(a), 1.8, 1.8, "B")
    # face
    ell(0, 24, 9.5, 10, F)
    ell(4, 27, 7, 7.5, "f", only=F)
    ell(-1, 24, 8.5, 9, F, only="f")
    for ex in (-4, 4):
        for dx, dy in ((-2, -2), (-1, -3), (0, -3), (1, -3), (2, -2)):
            dot(ex + dx, 24 + dy, "E")
        poly([(ex, 24), (ex + 1.8, 26.2), (ex, 28.4), (ex - 1.8, 26.2)], J)
    for ex in (-7, 7):
        ell(ex, 27, 1.7, 1.2, "R")
    if grin:
        poly([(-5, 29), (5, 29), (3, 33), (-3, 33)], "E")
        for dx in (-3, -1, 1, 3):
            dot(dx, 30, "w" if dx != 1 else "B")
    else:
        for dx in range(-3, 4):
            dot(dx, 30 + (1 if abs(dx) < 2 else 0), "r")
        dot(-4, 29, "r"), dot(4, 29, "r")
    if crown:
        poly([(-10, 16), (-11, 6), (-6, 11), (0, 3), (6, 11), (11, 6), (10, 16)], "B")
        poly([(-10, 13), (10, 13), (10, 16), (-10, 16)], "b")
        for x, col in ((-6, "R"), (0, J), (6, "R")):
            ell(x, 14.5, 1.3, 1.3, col)
        c.outline(keep=".w")
        return
    _hat(c, P, poly, ell, dot, H, h, J, j, C)
    c.outline(keep=".w")


def _hat(c, P, poly, ell, dot, H, h, J, j, C):
    """The hat: a band, two flaps drooping beside the face, a centre point
    flopping over, gold bells on every tip."""
    poly([(-10, 16), (-16, 13), (-20, 19), (-19, 27), (-14, 20), (-9, 17)], J)
    poly([(10, 16), (16, 13), (20, 19), (19, 27), (14, 20), (9, 17)], J)
    poly([(-17, 15), (-20, 19), (-19, 27), (-16, 19)], j)
    poly([(17, 15), (20, 19), (19, 27), (16, 19)], j)
    poly([(-10, 16), (-8, 6), (-2, -2), (7, -3), (12, 1), (8, 9), (10, 16)], H)
    poly([(2, 11), (7, -3), (12, 1), (8, 9), (10, 16), (3, 16)], h)
    poly([(-10, 15), (10, 15), (10, 17.5), (-10, 17.5)], C)
    for x in (-8, -4, 0, 4, 8):
        dot(x, 16, "B")
    for bx, by in ((-19, 28), (13, 2), (19, 28)):
        ell(bx, by, 2.3, 2.3, "B")
        dot(bx + 1, by + 1, "b")


# ------------------------------------------------------------------ props (drawn below the collar)

def small_ring(c, x, y, gem, suit):
    c.pal.update({"G": "f5b82e", "g": "b8801a", "Y": gem[0], "y": gem[1]})
    c.ring(x, y + 3, 6, 5, 1.8, "G")
    c.poly([(x - 5, y - 2), (x + 5, y - 2), (x + 3, y - 7), (x - 3, y - 7)], "Y")
    c.poly([(x - 5, y - 2), (x + 5, y - 2), (x, y + 3)], "y")
    suit_shape(c, suit, x, y - 3, 1.6, "w")


def mini_mask(c, x, y, col, shade):
    c.ellipse(x, y, 4.2, 4.8, col)
    c.ellipse(x + 1.2, y + 1.2, 3, 3.6, shade, only=col)
    c.ellipse(x, y - 0.5, 3.6, 3.9, col, only=shade)
    c.set(x - 2, y - 1, "K"), c.set(x + 2, y - 1, "K")
    for dx in (-2, -1, 0, 1, 2):
        c.set(x + dx, y + 2 + (1 if abs(dx) < 2 else 0), "K")


def coin(c, x, y):
    c.pal.update({"G": "f5b82e", "g": "b8801a"})
    c.ellipse(x, y, 3.2, 3.2, "G")
    c.ellipse(x + 0.6, y + 0.6, 1.4, 1.4, "g")


def note(c, x, y, col):
    c.ellipse(x, y, 2.4, 1.8, col)
    c.rect(x + 1, y - 7, x + 2, y, col)
    c.rect(x + 2, y - 7, x + 4, y - 6, col)


# ------------------------------------------------------------------ charms

PALETTES = {
    "red": ("e63946", "a02030"), "blue": ("1d6fd1", "13478a"), "gold": ("f5b82e", "b8801a"),
    "green": ("3fb97a", "2a8a58"), "purple": ("9b5de5", "6a3fa0"), "sky": ("42aaf0", "1d6fd1"),
    "orange": ("f08a24", "b05a10"), "dark": ("3a3d5c", "22243a"), "pink": ("f07a9a", "c04a6a"),
    "teal": ("2ec4b6", "1a8a80"), "white": ("f4f1ea", "c9c2b0"),
}
P_ = PALETTES


def jester_card(c):
    jester(c)


def ring_card(gem, suit, hat):
    def f(c):
        jester(c, hat=P_[hat], flaps=P_["gold"], collar=P_[hat])
        c.outline(keep=".w")
        small_ring(c, 30, 60, gem, suit)
        c.outline(keep=".w")
    return f


def masks_card(n, hat, flaps, collar):
    def f(c):
        jester(c, top=6, hat=P_[hat], flaps=P_[flaps], collar=P_[collar])
        c.pal.update({"M": "f4f1ea", "m": "c9c2b0"})
        xs = {2: (24, 36), 3: (20, 30, 40), 4: (18, 26, 34, 42)}[n]
        for x in xs:
            mini_mask(c, x, 59, "M", "m")
        c.outline(keep=".w")
    return f


def ladder(c):
    c.pal.update({"L": "c08a4a", "l": "7a5230"})
    for x in (10, 18):
        c.rect(x, 22, x + 1, 70, "L")
    for y in range(25, 70, 6):
        c.rect(11, y, 18, y, "l")
    jester(c, cx=33, top=12, hat=P_["orange"], flaps=P_["green"], collar=P_["green"])
    c.outline(keep=".w")


def tide(c):
    c.pal.update({"Z1": "bfe6ff"})
    c.pal["Q"] = "bfe6ff"
    background(c, "Q")
    jester(c, top=12, hat=P_["blue"], flaps=P_["sky"], collar=P_["white"])
    c.pal.update({"A": "42aaf0", "a": "1d6fd1", "W": "ffffff"})
    for band, y0 in enumerate(range(44, 75, 7)):
        for x in range(1, W - 1):
            y = y0 + 2.5 * math.sin((x + band * 9) / 5.0)
            for yy in range(int(y), H - 1):
                c.set(x, yy, "A" if band % 2 == 0 else "a")
            c.set(x, int(y), "W")


def mint(c):
    jester(c, top=5, hat=P_["green"], flaps=P_["white"], collar=P_["green"])
    c.pal.update({"G": "3fb97a", "g": "2a8a58"})
    c.ellipse(32, 60, 8, 8, "w")
    for k in range(6):
        a = k * math.pi / 3
        c.poly([(32, 60), (32 + 9 * math.cos(a), 60 + 9 * math.sin(a)), (32 + 9 * math.cos(a + 0.5), 60 + 9 * math.sin(a + 0.5))], "G", only="w")
    for side in (-1, 1):
        c.poly([(32 + side * 8, 60), (32 + side * 13, 56), (32 + side * 13, 64)], "G")
    c.outline(keep=".w")


def flag(c):
    c.pal.update({"S": "8a96a3", "Y": "f5b82e"})
    c.rect(43, 16, 44, 70, "S")
    for x in range(45, 51):
        w = 1.5 * math.sin(x / 2.0)
        for y in range(int(17 + w), int(28 + w)):
            c.set(x, y, "N" if (x // 2) % 2 else "n")
    jester(c, cx=26, top=12, hat=P_["red"], flaps=P_["white"], collar=P_["red"])
    c.pal.update({"N": "e63946", "n": "a02030"})
    c.outline(keep=".w")


def glitch(c):
    c.pal["Q"] = "1b1c2e"
    background(c, "Q")
    jester(c, top=12, hat=("ff3b5c", "a02030"), flaps=("2ee6d6", "1a8a80"), collar=("f5e642", "c9a520"), face="e8e8ff")
    import random
    rnd = random.Random(11)
    for _ in range(12):
        y = rnd.randrange(8, 64)
        shift = rnd.choice((-4, -3, 3, 4))
        row = [c.get(x, y) for x in range(W)]
        for x in range(2, W - 2):
            if 1 <= x - shift < W - 1:
                c.set(x, y, row[x - shift])
    c.pal.update({"y": "ff3b5c", "Y": "2ee6d6"})
    for _ in range(10):
        y = rnd.randrange(4, H - 4)
        x = rnd.randrange(2, W - 14)
        c.rect(x, y, min(x + rnd.randrange(4, 12), W - 3), y, rnd.choice("yY"))


def even(c):
    c.pal["Q"] = "dff2ff"
    background(c, "Q")
    jester(c, top=6, hat=P_["sky"], flaps=P_["white"], collar=P_["sky"])
    c.pal.update({"W": "c06a3a", "V": "7a3f20", "A": "42aaf0", "a": "1d6fd1"})
    c.poly([(10, 52), (54, 52), (48, 60), (16, 60)], "W")
    c.rect(14, 55, 50, 55, "V")
    for y in range(61, H - 1):
        for x in range(1, W - 1):
            c.set(x, y, "A" if (y // 3) % 2 == 0 else "a")


def odd(c):
    # a duck wearing the jester's hat
    c.pal.update({"Y": "f5d742", "y": "c9a520", "O": "f08a24"})
    c.ellipse(32, 54, 15, 10, "Y")
    c.ellipse(23, 39, 8, 8, "Y")
    c.ellipse(35, 53, 9, 5, "y")
    c.poly([(15, 40), (9, 43), (15, 45)], "O")
    c.ellipse(21, 37, 1.3, 1.5, "K")
    c.poly([(43, 48), (50, 44), (47, 54)], "Y")
    c.outline(keep=".w")
    jester(c, cx=24, top=19, s=0.6, hat=P_["purple"], flaps=P_["gold"], collar=P_["purple"], hat_only=True)


def scribe(c):
    jester(c, top=5, hat=P_["dark"], flaps=P_["white"], collar=P_["white"])
    c.pal.update({"Y": "f4e7c4", "y": "cdb98a", "I": "1d6fd1"})
    c.rect(18, 54, 44, 68, "Y")
    for yy in range(57, 67, 3):
        c.rect(22, yy, 40, yy, "y")
    c.line(40, 66, 52, 46, "w", 2)
    c.line(40, 66, 50, 48, "f")
    c.outline(keep=".w")


def well(c):
    c.pal.update({"S": "a8aaaf", "s": "6d7078", "Y": "c06a3a", "y": "7a3f20", "A": "1d3c6e"})
    c.poly([(10, 30), (32, 16), (54, 30)], "Y")
    c.rect(13, 30, 15, 50, "y"), c.rect(49, 30, 51, 50, "y")
    jester(c, top=24, s=0.8, hat=P_["teal"], flaps=P_["gold"], collar=P_["teal"])
    c.ellipse(32, 52, 21, 4, "A")
    c.rect(11, 52, 53, 70, "S")
    for y in range(55, 70, 4):
        c.rect(11, y, 53, y, "s")
        for x in range(11 + (y // 4) % 2 * 4, 53, 8):
            c.rect(x, y, x, y + 3, "s")
    c.outline(keep=".w")


def crowd(c):
    cols = [("red", "blue"), ("green", "gold"), ("purple", "sky"), ("orange", "teal"), ("blue", "red")]
    spots = [(18, 32), (46, 32), (32, 26), (22, 46), (42, 46)]
    for i, ((hx, hy), (hat, fl)) in enumerate(zip(spots, cols)):
        jester(c, cx=hx, top=hy - 18, s=0.52, hat=P_[hat], flaps=P_[fl], collar=P_[fl],
               key=("", "2", "3")[i % 3])
        c.pal.update({"H": P_[hat][0]})


def laststand(c):
    jester(c, cx=27, top=8, hat=P_["red"], flaps=P_["dark"], collar=P_["dark"])
    c.pal.update({"Y": "c9d3dc", "y": "8a96a3", "G": "f5b82e"})
    c.poly([(36, 46), (50, 46), (50, 58), (43, 67), (36, 58)], "Y")
    c.poly([(43, 46), (50, 46), (50, 58), (43, 67)], "y")
    c.poly([(40, 50), (46, 50), (46, 56), (43, 60), (40, 56)], "G")
    c.outline(keep=".w")


def court(c):
    jester(c, top=6, hat=P_["purple"], flaps=P_["gold"], collar=P_["purple"])
    c.pal.update({"Y": "f5b82e", "y": "b8801a", "I": "e63946"})
    for x in (20, 32, 44):
        c.poly([(x - 5, 63), (x - 6, 55), (x - 2, 59), (x, 53), (x + 2, 59), (x + 6, 55), (x + 5, 63)], "Y")
        c.rect(x - 5, 61, x + 5, 63, "y")
        c.set(x, 59, "I")
    c.outline(keep=".w")


def spiral(c):
    c.pal.update({"Q": "13478a", "Y": "f5b82e"})
    background(c, "Q")
    a, b, t = 1.6, 0.18, 0.0
    while t < 4.6 * math.pi:
        r = a * math.exp(b * t)
        c.ellipse(32 + r * math.cos(t), 40 + r * math.sin(t), 1.2 + r / 10, 1.2 + r / 10, "Y")
        t += 0.04
    jester(c, top=18, s=0.62, hat=P_["red"], flaps=P_["gold"], collar=P_["gold"])


def gold(c):
    jester(c, hat=P_["gold"], flaps=P_["orange"], collar=P_["gold"], grin=True)


def snowball(c):
    c.pal.update({"Q": "a9d6f5", "q": "d8eefc", "Y": "c6dcec", "O": "f08a24"})
    background(c, "Q")
    c.poly([(1, 58), (W - 2, 46), (W - 2, H - 2), (1, H - 2)], "q")
    c.ellipse(32, 58, 13, 11, "w")
    c.ellipse(36, 61, 9, 7, "Y", only="w")
    c.ellipse(31, 57, 10, 9, "w", only="Y")
    jester(c, top=10, s=0.8, hat=P_["red"], flaps=P_["green"], collar=P_["green"], face="ffffff")
    c.poly([(33, 32), (40, 34), (33, 35)], "O")
    for k in range(26):
        c.set((k * 17) % (W - 4) + 2, (k * 29) % 24 + 3, "w")


def treasury(c):
    jester(c, top=5, hat=P_["green"], flaps=P_["gold"], collar=P_["gold"])
    for i in range(11):
        coin(c, 16 + (i % 6) * 6, 66 - (i // 6) * 5)
    c.outline(keep=".w")


def hollow(c):
    c.pal.update({"Q": "15142a", "q": "2a2850", "Y": "c9c2ff"})
    background(c, "Q")
    c.ellipse(32, 40, 22, 26, "q")
    c.ellipse(32, 40, 16, 20, "Q")
    tmp = Canvas({})
    jester(tmp)
    for y in range(H):
        for x in range(W):
            ch = tmp.get(x, y)
            if ch == "K" and (x + y) % 2 == 0:
                c.set(x, y, "Y")
    for k in range(12):
        c.set((k * 19) % 40 + 12, (k * 31) % 60 + 8, "Y")


def prism(c):
    c.pal["Q"] = "1b1c2e"
    background(c, "Q")
    rainbow = ["e63946", "f08a24", "f5d742", "3fb97a", "42aaf0", "9b5de5"]
    for i, col in enumerate(rainbow):
        key = "123456"[i]
        c.pal[key] = col
        c.line(2, 70 - i * 2, W - 3, 56 - i * 4, key, 2)
    jester(c, top=6, hat=("9b5de5", "6a3fa0"), flaps=("42aaf0", "1d6fd1"), collar=("f5d742", "c9a520"))


def warden(c):
    jester(c, cx=26, top=8, hat=P_["dark"], flaps=("8a96a3", "5d6675"), collar=("8a96a3", "5d6675"))
    c.pal.update({"Y": "f5b82e", "y": "b8801a", "S": "c9d3dc"})
    c.ring(43, 51, 5, 5, 1.8, "S")
    c.rect(37, 55, 49, 66, "Y")
    c.rect(43, 55, 49, 66, "y")
    c.rect(42, 59, 43, 62, "K")
    c.outline(keep=".w")


def duet(c):
    jester(c, cx=21, top=16, s=0.66, hat=P_["pink"], flaps=P_["sky"], collar=P_["sky"])
    jester(c, cx=39, top=26, s=0.66, hat=P_["sky"], flaps=P_["pink"], collar=P_["pink"], key="2")
    c.pal.update({"V": "9b5de5"})
    note(c, 31, 16, "V")
    note(c, 40, 12, "V")
    c.outline(keep=".w")


# ------------------------------------------------------------------ more props

def chip_stack(c, x, y, n, col, edge, r=5.5):
    """A stack of n poker chips, its top chip at y."""
    c.pal.update({"A": col, "a": edge})
    for k in range(n - 1, -1, -1):
        yy = y + k * 3
        c.ellipse(x, yy + 1, r, 2.4, "a")
        c.ellipse(x, yy, r, 2.4, "A")
    for dx in (-3, 0, 3):
        c.set(x + dx, y, "w")


def mini_crown(c, x, y, s=1.0):
    c.pal.update({"Y": "f5b82e", "y": "b8801a", "I": "e63946"})
    c.poly([(x - 5 * s, y + 4 * s), (x - 6 * s, y - 4 * s), (x - 2 * s, y), (x, y - 6 * s), (x + 2 * s, y),
            (x + 6 * s, y - 4 * s), (x + 5 * s, y + 4 * s)], "Y")
    c.rect(x - 5 * s, y + 2 * s, x + 5 * s, y + 4 * s, "y")
    c.set(x, y + 1, "I")


def waves(c, y0, cols=("A", "a"), x0=9, x1=50):
    for band, yb in enumerate(range(y0, H - 1, 6)):
        for x in range(x0, x1):
            y = yb + 2 * math.sin((x + band * 7) / 4.0)
            for yy in range(int(y), H - 2):
                c.set(x, yy, cols[band % 2])


def veil_card(n, hat, chip, rising=False, flush=False):
    def f(c):
        jester(c, top=5, hat=P_[hat], flaps=P_["white"], collar=P_[hat])
        if flush:
            c.pal.update({"D": "bfe6ff", "d": "42aaf0"})
            waves(c, 63, ("D", "d"))
        gap = 12 if n < 4 else 10
        xs = [29 + (i - (n - 1) / 2) * gap for i in range(n)]
        for i, x in enumerate(xs):
            h = 2 + i if rising else 3
            chip_stack(c, x, 66 - h * 3, h, chip[0], chip[1], 5.5 if n < 4 else 4.5)
        c.outline(keep=".wDd")
    return f


def crown_card(hat, prop):
    def f(c):
        jester(c, top=4, hat=P_[hat], flaps=P_["gold"], collar=P_[hat], crown=True)
        prop(c)
        c.outline(keep=".w")
    return f


def _crowns(n):
    def f(c):
        gap = 12 if n < 4 else 10
        for i in range(n):
            mini_crown(c, 29 + (i - (n - 1) / 2) * gap, 59, 1.0 if n < 4 else 0.8)
    return f


def _rail(c):
    c.pal.update({"S": "8a96a3", "s": "5d6675"})
    for i in range(5):
        x = 10 + i * 8
        c.rect(x, 66 - i * 4, x + 6, 68, "S")
        c.rect(x, 66 - i * 4, x + 6, 66 - i * 4, "s")


def _flushwave(c):
    c.pal.update({"A": "42aaf0", "a": "1d6fd1"})
    waves(c, 56)


def grin(c):
    jester(c, top=10, hat=P_["purple"], flaps=P_["green"], collar=P_["purple"], grin=True)
    c.pal.update({"M": "f4f1ea", "m": "c9c2b0"})
    for x in (16, 44):
        mini_mask(c, x, 61, "M", "m")
    c.outline(keep=".w")


def radio(c):
    jester(c, top=4, hat=P_["orange"], flaps=P_["teal"], collar=P_["orange"])
    c.pal.update({"D": "c06a3a", "d": "7a3f20", "S": "c9d3dc", "V": "9b5de5"})
    c.rect(16, 52, 42, 68, "D")
    c.rect(18, 54, 30, 66, "S")
    for y in range(55, 66, 2):
        c.rect(18, y, 30, y, "d")
    c.ellipse(36, 58, 3, 3, "d"), c.ellipse(36, 64, 2, 2, "S")
    c.line(40, 52, 47, 45, "S")
    note(c, 49, 60, "V")
    c.outline(keep=".w")


def spearhead(c):
    jester(c, cx=24, top=6, hat=P_["dark"], flaps=P_["sky"], collar=P_["dark"])
    c.pal.update({"D": "c06a3a", "S": "c9d3dc", "s": "8a96a3"})
    c.line(43, 70, 43, 30, "D", 2)
    suit_shape(c, "spade", 43, 26, 6, "S")
    suit_shape(c, "spade", 44, 27, 3.5, "s")
    c.outline(keep=".w")


def clover(c):
    jester(c, top=4, hat=P_["green"], flaps=P_["gold"], collar=P_["green"])
    c.pal.update({"G": "3fb97a", "g": "2a8a58"})
    for dx, dy in ((-5, -4), (5, -4), (-5, 4), (5, 4)):
        c.ellipse(30 + dx, 59 + dy, 5, 5, "G")
        c.ellipse(30 + dx * 1.2, 59 + dy * 1.2, 2, 2, "g")
    c.line(30, 60, 36, 72, "g", 2)
    c.outline(keep=".w")


def rawgem(c):
    jester(c, top=4, hat=P_["orange"], flaps=P_["dark"], collar=P_["orange"])
    c.pal.update({"O": "f08a24", "o": "b05a10", "Y": "ffc078"})
    c.poly([(22, 58), (27, 49), (36, 48), (41, 56), (36, 69), (25, 67)], "O")
    c.poly([(30, 58), (36, 48), (41, 56), (36, 69)], "o")
    c.poly([(25, 56), (29, 51), (31, 57)], "Y")
    c.outline(keep=".w")


def heartstone(c):
    jester(c, top=4, hat=P_["red"], flaps=P_["dark"], collar=P_["red"])
    c.pal.update({"I": "e63946", "i": "a02030", "Y": "ff8a8a"})
    suit_shape(c, "heart", 30, 59, 10, "I")
    c.poly([(30, 50), (40, 56), (30, 70)], "i", only="I")
    c.ellipse(25, 55, 2, 1.5, "Y")
    c.outline(keep=".w")


def portrait(c):
    c.pal.update({"Y": "f5b82e", "y": "b8801a", "Q": "f4e7c4"})
    c.rect(9, 9, 51, 68, "Y")
    c.rect(12, 12, 48, 65, "Q")
    c.rect(9, 66, 51, 68, "y")
    jester(c, top=12, s=0.78, hat=P_["red"], flaps=P_["blue"], collar=P_["gold"])
    c.outline(keep=".w")


def tightrope(c):
    c.pal.update({"Q": "dff2ff", "D": "c06a3a", "S": "8a96a3"})
    background(c, "Q")
    c.line(1, 52, W - 2, 46, "D", 2)
    jester(c, top=6, s=0.78, hat=P_["red"], flaps=P_["gold"], collar=P_["red"])
    c.line(6, 34, 54, 30, "S", 1)
    c.ellipse(6, 34, 2, 2, "S"), c.ellipse(54, 30, 2, 2, "S")


def fist(c):
    jester(c, top=3, hat=P_["dark"], flaps=P_["red"], collar=P_["dark"])
    c.pal.update({"S": "f2c9a0", "s": "c99a70"})
    c.rect(18, 50, 42, 66, "S")
    c.rect(18, 62, 42, 66, "s")
    for x in (24, 30, 36):
        c.rect(x, 50, x, 58, "s")
    c.rect(14, 54, 19, 62, "S")
    c.outline(keep=".w")


def regent(c):
    jester(c, top=4, hat=P_["purple"], flaps=P_["gold"], collar=("9b2240", "6e1530"), crown=True)
    c.pal.update({"Y": "f5b82e", "I": "e63946", "M": "9b5de5"})
    c.line(46, 70, 40, 46, "Y", 2)
    c.ellipse(40, 45, 3, 3, "I")
    c.rect(12, 54, 24, 68, "M")
    c.rect(16, 58, 20, 64, "Y")
    c.outline(keep=".w")


def moonrise(c):
    c.pal.update({"Q": "1d1f3a", "Y": "f5e6a8", "y": "c9b46a"})
    background(c, "Q")
    c.ellipse(30, 54, 14, 14, "Y")
    c.ellipse(36, 50, 12, 12, "Q", only="Y")
    jester(c, top=8, s=0.7, hat=P_["sky"], flaps=P_["purple"], collar=P_["sky"])
    for k in range(18):
        c.set((k * 23) % (W - 6) + 3, (k * 37) % 30 + 4, "Y")


def encore(c):
    c.pal.update({"I": "b8334a", "i": "7a1a2e", "Y": "f5b82e"})
    jester(c, top=8, hat=P_["gold"], flaps=P_["red"], collar=P_["gold"], grin=True)
    for side in (0, 1):
        for x in range(9, 15):
            xx = x if side == 0 else W - 1 - x
            for y in range(2, H - 2):
                if (x - 9) < 6 - y * 0.05:
                    c.set(xx, y, "I" if (x // 2) % 2 else "i")
    c.rect(9, 2, W - 10, 5, "Y")


def masquerade(c):
    jester(c, top=4, hat=P_["dark"], flaps=P_["gold"], collar=P_["dark"])
    c.pal.update({"M": "f4f1ea", "m": "c9c2b0", "I": "e63946", "i": "a02030"})
    mask(c, 20, 59, 1.0, "M", "m")
    mask(c, 40, 59, 1.0, "I", "i")
    c.outline(keep=".w")


def punchcard(c):
    jester(c, top=3, hat=P_["sky"], flaps=P_["white"], collar=P_["sky"])
    c.pal.update({"Q": "f4e7c4", "q": "cdb98a"})
    c.rect(12, 50, 48, 70, "Q")
    c.poly([(12, 50), (17, 50), (12, 55)], ".")
    for x in range(16, 46, 4):
        for y in range(54, 68, 4):
            c.set(x, y, "q" if (x * 7 + y) % 3 else "K")
    c.outline(keep=".w")


def twilight(c):
    c.pal.update({"1": "f08a24", "2": "e0566a", "3": "9b5de5", "4": "4b3a8a", "Y": "f5d742"})
    for y in range(1, H - 1):
        c.rect(1, y, W - 2, y, "4321"[min(3, y * 4 // 52)] if y < 52 else "1")
    c.ellipse(30, 58, 10, 10, "Y")
    c.rect(1, 60, W - 2, H - 2, "4")
    jester(c, top=6, s=0.78, hat=P_["dark"], flaps=P_["orange"], collar=P_["dark"])


def callingcard(c):
    jester(c, top=4, hat=P_["dark"], flaps=P_["white"], collar=P_["dark"])
    c.pal.update({"Q": "f4f1ea", "q": "8a96a3"})
    c.rect(14, 52, 46, 68, "Q")
    c.rect(18, 56, 34, 57, "q")
    for y in (61, 64):
        c.rect(18, y, 42, y, "q")
    coin(c, 46, 66)
    c.outline(keep=".w")


def ticket(c):
    jester(c, top=4, hat=P_["gold"], flaps=P_["red"], collar=P_["gold"])
    c.pal.update({"Y": "f5d742", "y": "c9a520"})
    c.poly([(11, 54), (47, 50), (49, 66), (13, 70)], "Y")
    for y in range(52, 70, 3):
        c.set(18, y + (0 if y < 60 else -1), "y")
    c.rect(24, 58, 44, 59, "y")
    c.outline(keep=".w")


def patience(c):
    jester(c, cx=24, top=6, hat=P_["teal"], flaps=P_["gold"], collar=P_["teal"])
    c.pal.update({"D": "c06a3a", "Q": "dff2ff", "Y": "f5d742"})
    c.rect(34, 44, 48, 46, "D"), c.rect(34, 68, 48, 70, "D")
    c.poly([(36, 47), (46, 47), (42, 57), (40, 57)], "Q")
    c.poly([(40, 57), (42, 57), (46, 67), (36, 67)], "Q")
    c.poly([(38, 61), (44, 61), (46, 67), (36, 67)], "Y")
    c.outline(keep=".w")


def corsair(c):
    jester(c, top=4, hat=P_["dark"], flaps=P_["red"], collar=P_["red"])
    c.pal.update({"S": "c9d3dc", "Y": "f5b82e"})
    c.line(16, 68, 44, 50, "S", 2)
    c.line(44, 68, 16, 50, "S", 2)
    c.rect(20, 62, 24, 64, "Y"), c.rect(36, 62, 40, 64, "Y")
    c.rect(20, 24, 26, 25, "K")
    c.outline(keep=".w")


def fame(c):
    c.pal.update({"Y": "f5d742", "y": "c9a520"})
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = 22 if k % 2 == 0 else 10
        pts.append((30 + r * math.cos(a), 34 + r * math.sin(a)))
    c.poly(pts, "Y")
    jester(c, top=12, s=0.8, hat=P_["pink"], flaps=P_["gold"], collar=P_["pink"], grin=True)
    for x in range(14, 48, 6):
        c.set(x, 66, "y"), c.set(x + 1, 67, "y")


def commuter(c):
    jester(c, top=3, hat=P_["orange"], flaps=P_["blue"], collar=P_["orange"])
    c.pal.update({"Y": "f5b82e", "y": "b8801a", "Q": "bfe6ff", "S": "3a3d5c"})
    c.rect(10, 50, 48, 66, "Y")
    c.rect(10, 63, 48, 66, "y")
    for x in range(13, 44, 8):
        c.rect(x, 53, x + 6, 58, "Q")
    c.ellipse(17, 67, 3.5, 3.5, "S"), c.ellipse(43, 67, 3.5, 3.5, "S")
    c.outline(keep=".w")


def sprinter(c):
    c.pal.update({"S": "a8aaaf"})
    for y in (24, 31, 38, 45):
        c.rect(10, y, 18 + (y % 3) * 2, y, "S")
    jester(c, cx=34, top=8, hat=P_["green"], flaps=P_["orange"], collar=P_["green"])
    c.pal.update({"I": "e63946", "i": "a02030"})
    c.poly([(22, 60), (40, 58), (46, 64), (22, 66)], "I")
    c.rect(22, 64, 46, 66, "i")
    c.outline(keep=".w")


def foursquare(c):
    jester(c, top=3, hat=P_["blue"], flaps=P_["gold"], collar=P_["blue"])
    c.pal.update({"1": "e63946", "2": "f5b82e", "3": "3fb97a", "4": "42aaf0"})
    for i, (dx, dy) in enumerate(((0, 0), (11, 0), (0, 11), (11, 11))):
        c.rect(19 + dx, 49 + dy, 28 + dx, 58 + dy, "1234"[i])
    c.outline(keep=".w")


def sorbet(c):
    jester(c, cx=24, top=6, hat=P_["pink"], flaps=P_["white"], collar=P_["pink"])
    c.pal.update({"D": "e0a35a", "d": "a8743a", "M": "f9c6d8", "m": "a8e6cf"})
    c.poly([(35, 52), (49, 52), (42, 72)], "D")
    for k in range(4):
        c.line(36 + k * 3, 53, 42, 70, "d")
    c.ellipse(42, 47, 7, 6, "M")
    c.ellipse(42, 40, 5.5, 5, "m")
    c.outline(keep=".w")


def kettle(c):
    jester(c, top=3, hat=P_["red"], flaps=P_["white"], collar=P_["red"])
    c.pal.update({"I": "e63946", "M": "f4f1ea", "Y": "f5d742"})
    c.poly([(16, 54), (44, 54), (40, 72), (20, 72)], "M")
    for x in range(18, 44, 6):
        c.poly([(x, 54), (x + 3, 54), (x + 2.5, 72), (x + 1, 72)], "I")
    for x in range(17, 45, 5):
        c.ellipse(x, 52, 3, 2.5, "M")
        c.set(x, 51, "Y")
    c.outline(keep=".w")


def _banana(c, spots):
    c.pal.update({"Y": "f5d742", "y": "c9a520", "D": "6e4a20"})
    for k in range(40):
        t = k / 39
        x = 15 + 30 * t
        y = 58 + 9 * math.sin(math.pi * t)
        c.ellipse(x, y, 3.5, 3.5, "Y")
    for k in range(40):
        t = k / 39
        c.set(15 + 30 * t, 61 + 9 * math.sin(math.pi * t), "y")
    c.rect(12, 55, 14, 58, "D"), c.rect(45, 55, 47, 58, "D")
    if spots:
        for x, y in ((21, 63), (27, 66), (33, 66), (39, 63), (24, 64), (36, 64)):
            c.set(x, y, "D"), c.set(x + 1, y, "D")


def plantain(c):
    jester(c, top=3, hat=P_["green"], flaps=P_["gold"], collar=P_["green"])
    _banana(c, False)
    c.outline(keep=".w")


def ripe(c):
    jester(c, top=3, hat=P_["gold"], flaps=P_["green"], collar=P_["gold"], grin=True)
    _banana(c, True)
    c.outline(keep=".w")


def fizz(c):
    jester(c, cx=24, top=6, hat=P_["sky"], flaps=P_["teal"], collar=P_["sky"])
    c.pal.update({"Q": "bfe6ff", "G": "3fb97a", "g": "2a8a58"})
    c.rect(36, 50, 48, 72, "G")
    c.rect(39, 40, 45, 50, "G")
    c.rect(44, 52, 47, 70, "g")
    c.rect(38, 58, 46, 64, "Q")
    for k, (x, y) in enumerate(((41, 34), (44, 28), (40, 22), (43, 16))):
        c.ring(x, y, 2, 2, 0.8, "Q")
    c.outline(keep=".wQ")


def cardshark(c):
    c.pal.update({"A": "42aaf0", "a": "1d6fd1", "S": "5d6675", "s": "3a3d5c", "Q": "f4f1ea"})
    jester(c, top=3, hat=P_["dark"], flaps=P_["sky"], collar=P_["dark"])
    c.rect(9, 58, 49, H - 3, "A")
    waves(c, 62)
    c.poly([(30, 58), (38, 44), (42, 58)], "S")
    c.poly([(37, 50), (38, 44), (42, 58), (39, 58)], "s")
    c.rect(10, 48, 18, 60, "Q"), c.set(14, 54, "I")
    c.pal["I"] = "e63946"
    c.outline(keep=".wAa")


def loyal(c):
    jester(c, top=3, hat=P_["red"], flaps=P_["gold"], collar=P_["red"])
    c.pal.update({"Q": "f4e7c4", "I": "e63946"})
    c.rect(10, 52, 50, 70, "Q")
    for i in range(6):
        x, y = 16 + (i % 3) * 14, 57 + (i // 3) * 8
        c.ring(x, y, 3, 3, 1, "K" if i < 5 else "I")
        if i < 5:
            c.ellipse(x, y, 1.5, 1.5, "I")
    c.outline(keep=".w")


def slate(c):
    c.pal.update({"Q": "2a4a3a", "D": "8a5a30", "M": "f4f1ea"})
    background(c, "Q")
    c.rect(1, 1, W - 2, 3, "D"), c.rect(1, H - 4, W - 2, H - 2, "D")
    jester(c, top=6, s=0.8, hat=P_["dark"], flaps=P_["white"], collar=P_["dark"])
    suit_shape(c, "spade", 18, 60, 6, "M")
    suit_shape(c, "club", 42, 60, 6, "M")


# ------------------------------------------------------------------ helpers for the later charms

FONT3 = {
    "0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["##.", "..#", ".#.", "#..", "###"], "3": ["##.", "..#", ".#.", "..#", "##."],
    "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "##.", "..#", "##."],
    "6": [".##", "#..", "###", "#.#", "###"], "8": ["###", "#.#", "###", "#.#", "###"],
    "9": ["###", "#.#", "###", "..#", "##."], "$": [".##", "##.", ".#.", ".##", "##."],
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "E": ["###", "#..", "##.", "#..", "###"],
    "I": ["###", ".#.", ".#.", ".#.", "###"], "J": ["..#", "..#", "..#", "#.#", ".#."],
    "K": ["#.#", "#.#", "##.", "#.#", "#.#"], "N": ["#.#", "###", "###", "#.#", "#.#"],
    "O": [".#.", "#.#", "#.#", "#.#", ".#."], "P": ["##.", "#.#", "##.", "#..", "#.."],
    "Q": [".#.", "#.#", "#.#", "##.", ".##"], "S": [".##", "#..", ".#.", "..#", "##."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"], "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
}
BIG_DOLLAR = ["..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."]


def text(c, s, x, y, col, scale=1):
    """Tiny 3x5 lettering (each glyph scaled by `scale`)."""
    for ch in s:
        for j, row in enumerate(FONT3[ch]):
            for i, px in enumerate(row):
                if px == "#":
                    c.rect(x + i * scale, y + j * scale, x + i * scale + scale - 1, y + j * scale + scale - 1, col)
        x += 4 * scale


def dollar(c, x, y, col):
    for j, row in enumerate(BIG_DOLLAR):
        for i, px in enumerate(row):
            if px == "#":
                c.set(x + i, y + j, col)


def sparkle(c, x, y, col, r=2):
    for k in range(-r, r + 1):
        c.set(x + k, y, col)
        c.set(x, y + k, col)


def flame(c, cx, base, w, h, col):
    pts = [(cx - w, base), (cx - w * 0.9, base - h * 0.45), (cx - w * 0.45, base - h * 0.75),
           (cx - w * 0.2, base - h * 0.5), (cx, base - h), (cx + w * 0.3, base - h * 0.55),
           (cx + w * 0.55, base - h * 0.8), (cx + w * 0.85, base - h * 0.4), (cx + w, base)]
    c.poly(pts, col)
    c.ellipse(cx, base, w, h * 0.15 + 1, col)


def rot_pts(pts, a, ox, oy):
    ca, sa = math.cos(a), math.sin(a)
    return [(ox + (x - ox) * ca - (y - oy) * sa, oy + (x - ox) * sa + (y - oy) * ca) for x, y in pts]


def stamp(c, src, remap=None, dx=0, dy=0, rot=0.0, pivot=(30, 39), flip=False, src_clip=None, dst_clip=None):
    """Copy another canvas onto this one: shifted, rotated (radians, about
    `pivot`), mirrored, and with letters remapped (dict, or a function of
    (letter, x, y) returning a letter or None to skip)."""
    ca, sa = math.cos(rot), math.sin(rot)
    for y in range(H):
        for x in range(W):
            u, v = x - dx - pivot[0], y - dy - pivot[1]
            sx, sy = ca * u + sa * v + pivot[0], -sa * u + ca * v + pivot[1]
            if flip:
                sx = 2 * pivot[0] - sx
            sx, sy = int(math.floor(sx + 0.5)), int(math.floor(sy + 0.5))
            ch = src.get(sx, sy)
            if ch == ".":
                continue
            if src_clip and not src_clip(sx, sy):
                continue
            if dst_clip and not dst_clip(x, y):
                continue
            if callable(remap):
                new = remap(ch, x, y)
            else:
                new = (remap or {}).get(ch, ch)
            if new is None:
                continue
            c.set(x, y, new)
            if new == ch and ch in src.pal:
                c.pal[ch] = src.pal[ch]


def J(c, hat, flaps="gold", collar=None, **kw):
    jester(c, hat=P_[hat], flaps=P_[flaps], collar=P_[collar or hat], **kw)


def TJ(hat, flaps="gold", collar=None, **kw):
    t = Canvas({})
    J(t, hat, flaps, collar, **kw)
    return t


def layer(c, fn, **kw):
    """Draw `fn` on its own transparent canvas, ink-outline it, stamp it."""
    t = Canvas({})
    fn(t)
    t.outline()
    stamp(c, t, **kw)


def gradient(c, stops, y0=1, y1=H - 2):
    """Vertical bands of the given letters."""
    n = len(stops)
    for y in range(y0, y1 + 1):
        c.rect(1, y, W - 2, y, stops[min(n - 1, (y - y0) * n // (y1 - y0 + 1))])


def stars(c, n, col, seed, x0=9, x1=50, y0=3, y1=72):
    import random
    rnd = random.Random(seed)
    for _ in range(n):
        c.set(rnd.randint(x0, x1), rnd.randint(y0, y1), col)


# ------------------------------------------------------------------ the later charms

def spread(c):
    J(c, "blue", "gold", top=2)
    c.pal.update({"D": "f2c9a0", "d": "c99a70"})
    c.rect(25, 66, 35, 72, "D")
    for ang in (-160, -118, -82, -42):
        a = math.radians(ang)
        c.line(30 + 6 * math.cos(a), 62 + 4 * math.sin(a), 30 + 15 * math.cos(a), 62 + 13 * math.sin(a), "D", 3)
        c.ellipse(30 + 15.5 * math.cos(a), 62 + 13.5 * math.sin(a), 1.8, 1.8, "D")
    c.ellipse(30, 63, 9, 6.5, "D")
    c.ellipse(33, 66, 6, 3.5, "d", only="D")
    c.ellipse(29, 62, 6, 4, "D", only="d")
    c.line(26, 61, 31, 64, "d")
    c.outline(keep=".w")


def hopscotch(c):
    J(c, "pink", "teal", top=2)
    c.pal.update({"A": "9aa0a8", "a": "868c95", "M": "f4f1ea", "I": "e63946"})
    c.rect(9, 47, 49, 72, "A")
    for k in range(40):
        c.set(9 + (k * 13) % 41, 47 + (k * 7) % 26, "a")
    boxes = [(65, 71, [(24, 35)]), (59, 65, [(18, 29), (29, 40)]), (53, 59, [(24, 35)]), (47, 53, [(18, 29), (29, 40)])]
    n = 1
    for y0, y1, xs in boxes:
        for x0, x1 in xs:
            c.rect(x0, y0, x1, y0, "M"), c.rect(x0, y1, x1, y1, "M")
            c.rect(x0, y0, x0, y1, "M"), c.rect(x1, y0, x1, y1, "M")
            n += 1
    c.ellipse(34, 50, 1.6, 1.3, "I")
    c.outline(keep=".w")


def blot(c):
    import random
    J(c, "dark", "red", "dark", top=2)
    c.pal.update({"I": "d62839", "A": "3a3d5c", "D": "6a2a5a", "M": "f4f1ea"})
    rnd = random.Random(7)
    t1, t2 = Canvas({}), Canvas({})
    for t, cx in ((t1, 21), (t2, 38)):
        t.ellipse(cx, 60, 10, 8, "x")
        for _ in range(7):
            a = rnd.uniform(0, 2 * math.pi)
            r = rnd.uniform(7, 10)
            t.ellipse(cx + r * math.cos(a), 60 + r * 0.8 * math.sin(a), rnd.uniform(1.5, 3), rnd.uniform(1.5, 3), "x")
        for _ in range(3):
            a = rnd.uniform(0, 2 * math.pi)
            t.ellipse(cx + 13 * math.cos(a), 60 + 10 * math.sin(a), 1, 1, "x")
        dx = rnd.randint(-4, 4)
        t.rect(cx + dx, 66, cx + dx + 1, 71, "x")
    for y in range(46, 73):
        for x in range(9, 50):
            a, b = t1.get(x, y) == "x", t2.get(x, y) == "x"
            if a and b:
                c.set(x, y, "D")
            elif a:
                c.set(x, y, "I")
            elif b:
                c.set(x, y, "A")
    suit_shape(c, "heart", 17, 58, 4, "M")
    suit_shape(c, "diamond", 24, 62, 4, "M")
    suit_shape(c, "spade", 35, 58, 4, "M")
    suit_shape(c, "club", 42, 62, 4, "M")
    c.outline(keep=".w")


def mirage(c):
    c.pal.update({"1": "fde7b0", "2": "f9d08a", "3": "f5b870", "4": "e8b060", "5": "c98a40", "6": "fff1cc",
                  "7": "fff8e0"})
    gradient(c, "1123", 1, 46)
    c.ellipse(47, 9, 4.5, 4.5, "7")
    for x in range(1, W - 1):
        yb = 46 + 2.5 * math.sin(x / 7.0)
        c.rect(x, int(yb), x, H - 2, "4")
        yb2 = 58 + 3 * math.sin(x / 5.0 + 1)
        c.rect(x, int(yb2), x, H - 2, "5")
    t = TJ("orange", "sky", top=7, s=0.78)
    for y in range(H):
        sh = int(round(1.3 * math.sin(y * 0.9)))
        for x in range(2, W - 2):
            ch = t.get(x - sh, y)
            if ch != ".":
                c.set(x, y, ch)
                c.pal[ch] = t.pal[ch]
    for y in range(47, 62):
        if y % 2:
            continue
        sh = int(round(2 * math.sin(y * 0.7)))
        for x in range(9, 51):
            if t.get(x - sh, 89 - y) not in ".":
                c.set(x, y, "6")
    for y in range(5, 44, 4):
        x0 = 10 + (y * 7) % 9
        c.rect(x0, y, x0 + 3, y, "6") if y < 30 or x0 > 44 else None


def puddle(c):
    J(c, "sky", "green", top=2)
    c.pal.update({"A": "42aaf0", "a": "1d6fd1", "D": "bfe6ff"})
    c.ellipse(30, 66, 19, 5.5, "A")
    c.ellipse(30, 67.5, 15, 3.5, "a", only="A")
    c.ring(30, 66, 11, 3, 1, "D")
    c.poly([(19, 64), (17, 54), (22, 60), (24, 50), (27, 59), (30, 48), (33, 59), (36, 50), (38, 60),
            (43, 54), (41, 64)], "D")
    for x, y in ((14, 52), (46, 52), (20, 47), (40, 47), (11, 58), (49, 59)):
        c.ellipse(x, y, 1.4, 1.8, "A")
    c.outline(keep=".w")


def mimic(c):
    c.pal.update({"G": "f5b82e", "g": "b8801a", "Q": "dff2ff", "q": "b8e0f5"})
    c.rect(32, 10, 49, 71, "G")
    c.rect(34, 12, 47, 69, "Q")
    c.rect(32, 69, 49, 71, "g")
    for k in range(3):
        c.line(36 + k * 5, 30, 46, 20 + k * 5, "q") if k < 2 else None
    c.line(35, 62, 46, 51, "q")
    t = Canvas({})
    J(t, "red", "blue", "gold", cx=20, top=22, s=0.5)
    t.pal.update({"I": "e63946", "M": "f4f1ea"})
    for i, x in enumerate((13, 19, 25)):
        t.rect(x - 3, 50 - (i == 1) * 2, x + 3, 59 - (i == 1) * 2, "M")
        suit_shape(t, "heart" if i != 1 else "diamond", x, 54 - (i == 1) * 2, 2.2, "I")
    t.outline(keep=".w")
    stamp(c, t)
    stamp(c, t, flip=True, pivot=(30.5, 39), dst_clip=lambda x, y: 34 <= x <= 47 and 12 <= y <= 68)
    c.outline(keep=".w")


def ironwill(c):
    J(c, "dark", "sky", "dark", top=2)
    c.pal.update({"A": "7a8494", "a": "4a5262", "D": "b4bcc8", "Y": "f5d742"})
    c.poly([(9, 50), (20, 48), (47, 48), (47, 55), (38, 56), (35, 62), (40, 65), (42, 71), (17, 71), (19, 65),
            (25, 62), (22, 56), (16, 54)], "A")
    c.rect(20, 48, 47, 49, "D")
    c.poly([(35, 56), (38, 56), (35, 62), (40, 65), (42, 71), (36, 71)], "a")
    c.rect(17, 69, 42, 71, "a")
    for x, y in ((12, 46), (47, 45), (44, 43)):
        sparkle(c, x, y, "Y", 1)
    c.outline(keep=".w")


def quarry(c):
    J(c, "orange", "dark", top=2)
    c.pal.update({"A": "a8aaaf", "a": "6d7078", "D": "c08a4a", "Q": "c9d3dc", "q": "8a96a3"})
    for x0, y0 in ((10, 63), (22, 63), (16, 55)):
        c.rect(x0, y0, x0 + 11, y0 + 8, "A")
        c.rect(x0 + 9, y0, x0 + 11, y0 + 8, "a")
        c.rect(x0, y0 + 7, x0 + 11, y0 + 8, "a")
        c.set(x0 + 3, y0 + 3, "a"), c.set(x0 + 6, y0 + 5, "a"), c.set(x0 + 4, y0 + 2, "a")
    c.line(46, 71, 37, 51, "D", 2)
    c.line(26, 55, 36, 48, "Q", 3)
    c.line(36, 48, 48, 47, "Q", 3)
    c.line(26, 55, 36, 49, "q")
    c.outline(keep=".w")


def mason(c):
    J(c, "red", "gold", top=2)
    c.pal.update({"D": "c0603a", "M": "e8dcc8", "A": "a8aaaf", "a": "6d7078", "Q": "c9d3dc", "d": "8a5a30"})
    c.rect(10, 58, 48, 71, "M")
    for row, y in enumerate(range(59, 71, 4)):
        off = (row % 2) * 4
        for x in range(10 - off, 48, 8):
            c.rect(max(10, x), y, min(48, x + 6), y + 2, "D")
    c.rect(22, 51, 33, 57, "A")
    c.rect(31, 51, 33, 57, "a")
    c.set(25, 53, "a"), c.set(28, 55, "a")
    c.poly([(36, 56), (47, 50), (49, 55), (40, 58)], "Q")
    c.line(45, 52, 48, 46, "d", 2)
    c.outline(keep=".w")


def midas(c):
    J(c, "gold", "orange", top=1, s=0.78)
    c.pal.update({"G": "f5b82e", "g": "b8801a", "Y": "fff3a0"})
    for x, top in ((21, 44), (25, 41), (29, 40), (33, 42)):
        c.rect(x, top, x + 2, 56, "G")
        c.ellipse(x + 1.5, top, 1.5, 1.5, "G")
    c.rect(20, 54, 37, 66, "G")
    c.ellipse(28.5, 66, 8.5, 3, "G")
    c.line(37, 62, 44, 53, "G", 3)
    c.rect(24, 66, 33, 72, "G")
    for x in (24, 28, 32):
        c.rect(x, 46, x, 55, "g")
    c.rect(34, 56, 37, 66, "g")
    c.rect(22, 47, 22, 52, "Y"), c.rect(26, 44, 26, 50, "Y")
    c.outline(keep=".w")
    for x, y, r in ((13, 50, 2), (47, 44, 2), (14, 65, 1), (46, 64, 2), (40, 70, 1)):
        sparkle(c, x, y, "Y" if r == 1 else "G", r)
    c.outline(keep=".w")


def leech(c):
    J(c, "green", "purple", top=2)
    c.pal.update({"A": "9b5de5", "a": "6a3fa0", "M": "f4f1ea", "I": "e63946", "Q": "42aaf0"})
    c.rect(10, 50, 21, 67, "M")
    c.rect(10, 50, 21, 52, "Q")
    suit_shape(c, "heart", 15, 59, 3, "I")
    for k in range(60):
        t = k / 59
        x = 23 + 24 * t
        y = 60 + 4 * math.sin(2 * math.pi * t * 0.9)
        r = 3 + 2.2 * math.sin(math.pi * min(1, t * 1.2))
        c.ellipse(x, y, r, r, "A")
    for k in range(60):
        t = k / 59
        x = 23 + 24 * t
        y = 60 + 4 * math.sin(2 * math.pi * t * 0.9)
        r = 3 + 2.2 * math.sin(math.pi * min(1, t * 1.2))
        c.set(x, y + r - 1, "a")
        if k % 8 == 4:
            c.line(x, y - r + 1, x, y + r - 1, "a")
    c.ellipse(22, 59, 2, 2.5, "a")
    c.set(25, 56, "K"), c.set(27, 55, "K")
    c.outline(keep=".w")


def rambler(c):
    J(c, "green", "orange", top=2)
    c.pal.update({"D": "a8743a", "d": "6e4a20", "A": "3a3d5c", "M": "f4f1ea"})
    c.rect(15, 49, 26, 63, "D")
    c.rect(15, 49, 26, 50, "d")
    c.poly([(15, 62), (32, 61), (37, 64), (38, 68), (15, 68)], "D")
    c.rect(14, 68, 39, 70, "A")
    for y in range(52, 62, 3):
        c.line(18, y, 23, y + 2, "M"), c.line(23, y, 18, y + 2, "M")
    c.line(44, 72, 46, 47, "d", 2)
    c.ellipse(46, 46, 2.5, 2.5, "D")
    c.outline(keep=".w")


def relic(c):
    J(c, "purple", "gold", top=2)
    c.pal.update({"D": "c9733a", "d": "8a4a20", "a": "3a2a20", "M": "f4e7c4", "I": "e63946"})
    c.ring(16, 57, 3.5, 3.5, 1.3, "D"), c.ring(44, 57, 3.5, 3.5, 1.3, "D")
    c.rect(25, 48, 35, 54, "D")
    c.ellipse(30, 61, 13.5, 9, "D")
    c.rect(26, 68, 34, 70, "D")
    c.rect(23, 70, 37, 72, "d")
    c.rect(23, 47, 37, 48, "d")
    c.ellipse(36, 64, 8, 6, "d", only="D")
    c.ellipse(28, 60, 11, 7.5, "D", only="d")
    c.rect(16, 57, 44, 64, "a", only="Dd")
    for i, (x, s) in enumerate(zip((20, 26.5, 33.5, 40), ("spade", "heart", "club", "diamond"))):
        suit_shape(c, s, x, 60.5, 2.8, "I" if s == "heart" else "M")
    c.outline(keep=".w")


def keep(c):
    J(c, "teal", "gold", cx=30, top=8, s=0.6)
    c.pal.update({"A": "a8aaaf", "a": "7d8088", "D": "6e4a20", "I": "e63946", "M": "f4f1ea", "d": "4a3020"})
    c.rect(43, 10, 43, 30, "a")
    c.poly([(44, 10), (51, 13), (44, 17)], "I")
    c.rect(15, 30, 45, 36, "A")
    for x in range(15, 46, 6):
        c.rect(x + 3, 28, x + 5, 30, "A") if x + 5 <= 45 else None
    c.rect(15, 28, 17, 30, "A")
    c.rect(18, 36, 42, 72, "A")
    for row, y in enumerate(range(39, 72, 4)):
        c.rect(18, y, 42, y, "a")
        for x in range(18 + (row % 2) * 3, 42, 6):
            c.rect(x, y - 3, x, y - 1, "a")
    c.rect(15, 35, 45, 36, "a")
    c.ellipse(30, 63, 5, 5, "D")
    c.rect(25, 63, 35, 72, "D")
    c.rect(30, 58, 30, 72, "d")
    c.rect(29, 44, 31, 50, "d")
    c.outline(keep=".w")


def idol(c):
    c.pal.update({"A": "a8aaaf", "a": "6d7078", "M": "f4f1ea", "I": "e63946", "Y": "fff3a0"})
    jester(c, top=5, s=0.72, hat=("f5b82e", "b8801a"), flaps=("e0a020", "9a6a10"),
           collar=("f5b82e", "b8801a"), face="ffe07a")
    c.pal.update({"f": "e8c050", "R": "f5b82e", "r": "9a6a10", "J": "c08a20"})
    c.rect(15, 41, 45, 45, "A")
    c.rect(19, 46, 41, 65, "A")
    c.rect(37, 46, 41, 65, "a")
    c.rect(15, 66, 45, 71, "A")
    c.rect(15, 70, 45, 71, "a")
    c.rect(24, 49, 33, 62, "M")
    c.set(25, 50, "I"), c.set(32, 61, "I")
    suit_shape(c, "heart", 28.5, 55.5, 3, "I")
    c.outline(keep=".w")
    for x, y, r in ((12, 18, 2), (48, 14, 2), (11, 34, 1), (49, 30, 1)):
        sparkle(c, x, y, "Y" if r == 1 else "G", r)
    c.pal["G"] = "f5b82e"


def rebate(c):
    J(c, "green", "white", top=2)
    c.pal.update({"M": "f4f1ea", "m": "c9c2b0", "G": "9fe0b0", "g": "2a8a58"})
    c.poly(rot_pts([(28, 47), (48, 47), (48, 59), (28, 59)], -0.25, 38, 53), "G")
    for k, (x, y) in enumerate(rot_pts([(29 + i, 48) for i in range(0, 19, 2)] + [(29 + i, 58) for i in range(0, 19, 2)], -0.25, 38, 53)):
        c.set(x, y, "g")
    dollar(c, 36, 49, "g")
    c.rect(11, 56, 39, 71, "M")
    c.line(11, 56, 25, 65, "m"), c.line(25, 65, 39, 56, "m")
    c.line(11, 71, 21, 63, "m"), c.line(39, 71, 29, 63, "m")
    c.outline(keep=".w")


def errand(c):
    J(c, "orange", "green", top=2)
    c.pal.update({"D": "c08a4a", "M": "f4f1ea", "m": "c9c2b0", "A": "8a96a3", "G": "3fb97a", "Y": "f5e642"})
    c.rect(13, 48, 45, 72, "D")
    c.rect(15, 51, 43, 70, "M")
    c.rect(24, 46, 34, 50, "A")
    for i, y in enumerate((54, 58, 62, 66)):
        if i == 2:
            c.rect(16, y - 1, 42, y + 2, "Y")
        c.rect(17, y - 1, 19, y + 1, "m")
        c.set(18, y, "M" if i != 2 else "Y")
        c.rect(22, y, 39 - (i % 2) * 5, y, "m")
        if i < 2:
            c.set(17, y, "G"), c.set(18, y + 1, "G"), c.set(19, y, "G"), c.set(20, y - 1, "G")
    c.outline(keep=".w")


def trousers(c):
    J(c, "purple", "teal", top=2)
    c.pal.update({"A": "4a6fa5", "a": "2f4a75", "I": "e63946", "Y": "f5d742", "M": "f4f1ea"})
    c.poly([(17, 51), (43, 51), (46, 72), (32, 72), (30, 59), (28, 72), (14, 72)], "A")
    c.rect(17, 48, 43, 51, "a")
    for x in (20, 30, 40):
        c.rect(x, 48, x, 52, "A")
    c.set(30, 49, "Y")
    c.line(30, 52, 30, 58, "a")
    c.line(14, 72, 17, 52, "a")
    c.rect(18, 56, 24, 61, "I")
    c.rect(36, 62, 42, 67, "Y")
    for x0, y0 in ((18, 56), (36, 62)):
        for k in range(0, 7, 2):
            c.set(x0 + k, y0, "M"), c.set(x0 + k, y0 + 5, "M")
        c.set(x0, y0 + 2, "M"), c.set(x0 + 6, y0 + 2, "M"), c.set(x0, y0 + 4, "M"), c.set(x0 + 6, y0 + 4, "M")
    c.outline(keep=".w")


def flashcard(c):
    J(c, "sky", "gold", top=2)
    c.pal.update({"Q": "e8dcc4", "q": "cfe3f5", "M": "fffaf0", "I": "e63946", "Y": "f5d742", "y": "c9a520"})
    c.poly(rot_pts([(16, 52), (46, 52), (46, 69), (16, 69)], 0.18, 31, 60), "Q")
    c.poly(rot_pts([(15, 52), (45, 52), (45, 69), (15, 69)], 0.08, 30, 60), "q")
    c.rect(13, 53, 43, 71, "M")
    c.rect(13, 56, 43, 56, "I")
    c.poly([(30, 57), (22, 65), (27, 65), (24, 71), (34, 62), (29, 62), (33, 57)], "Y")
    c.line(29, 62, 25, 70, "y")
    c.outline(keep=".w")


def monolith(c):
    c.pal.update({"1": "1d1838", "2": "2e2450", "3": "4a2f62", "4": "221c34", "5": "30283f", "A": "0c0b14",
                  "a": "4a4a6a", "G": "7af0d0", "Y": "c9c2ff", "q": "3a2f70"})
    gradient(c, "11223", 1, 58)
    stars(c, 22, "Y", 3, 2, 57, 3, 50)
    c.rect(1, 58, W - 2, H - 2, "4")
    for k in range(18):
        c.rect((k * 11) % 54 + 2, 60 + (k * 5) % 12, (k * 11) % 54 + 4, 60 + (k * 5) % 12, "5")
    c.ellipse(30, 36, 15, 30, "q", only="123")
    c.rect(22, 10, 38, 62, "A")
    c.rect(22, 10, 23, 62, "a")
    c.rect(22, 10, 38, 10, "a")
    for y in range(16, 56, 6):
        c.rect(28, y, 32, y, "G")
        c.set(30, y + 2, "G")
    c.ellipse(30, 63, 12, 2, "4")
    t = TJ("purple", "teal", cx=13, top=46, s=0.45)
    stamp(c, t)


def frenzy(c):
    J(c, "red", "purple", "red", top=2, grin=True)
    c.pal.update({"A": "4a6fa5", "M": "f4f1ea", "I": "e63946", "Y": "f5d742"})
    for ex in (26.5, 33.5):
        c.ellipse(ex, 23, 2.6, 2.6, "w")
        c.ring(ex, 23, 2.6, 2.6, 1, "E")
        c.set(ex, 23, "E")
        c.set(ex + 1, 22, "E")
    for x, y in ((10, 12), (48, 8), (11, 30), (49, 26)):
        c.line(x, y, x + 2, y + 2, "Y"), c.line(x + 2, y + 2, x, y + 4, "Y")
    t = Canvas({})
    t.pal.update({"A": "4a6fa5", "M": "f4f1ea", "I": "e63946"})
    t.rect(16, 50, 44, 71, "A")
    t.rect(18, 52, 42, 69, "M")
    suit_shape(t, "spade", 30, 60, 6, "I")

    def zig(y):
        return 30 + (2 if (y // 3) % 2 else -2)
    stamp(c, t, dx=-3, dy=1, rot=-0.08, src_clip=lambda x, y: x < zig(y))
    stamp(c, t, dx=3, dy=-1, rot=0.1, src_clip=lambda x, y: x >= zig(y))
    for x, y in ((31, 46), (28, 72), (47, 52)):
        c.set(x, y, "A"), c.set(x + 1, y, "M")
    c.outline(keep=".w")


def dagger(c):
    J(c, "dark", "red", top=2)
    c.pal.update({"D": "6a3fa0", "d": "4a2a70", "G": "f5b82e", "g": "b8801a", "I": "e63946", "Q": "dfe6ee",
                  "q": "8a96a3"})
    c.rect(12, 57, 21, 62, "D")
    for x in range(13, 21, 2):
        c.rect(x, 57, x, 62, "d")
    c.ellipse(10.5, 59.5, 2.5, 2.5, "G")
    c.rect(22, 52, 24, 67, "G")
    c.ellipse(23, 52, 2, 2, "G"), c.ellipse(23, 67, 2, 2, "G")
    c.ellipse(23.5, 59.5, 1.5, 1.5, "I")
    c.poly([(25, 56), (40, 56), (44, 57), (49, 60), (44, 63), (25, 63)], "Q")
    c.rect(26, 59, 41, 60, "q")
    c.rect(25, 62, 44, 63, "q")
    c.outline(keep=".w")


def hologram(c):
    c.pal.update({"A": "3a3d5c", "a": "5d6675", "D": "7ff0ff", "q": "e4fcff",
                  "1": "7fe8ff", "2": "2ec4d6", "3": "b8f6ff", "4": "eafeff", "5": "1a8a9a"})
    c.ellipse(30, 68, 12, 3.5, "A")
    c.ellipse(30, 66.5, 10, 2.5, "a")
    c.ellipse(30, 66, 3, 1, "D")
    c.outline(keep=".w")
    c.poly([(26, 66), (34, 66), (49, 12), (11, 12)], "q", only="w")
    t = TJ("red", top=12, s=0.84)
    m = {"H": "1", "h": "2", "J": "3", "j": "2", "C": "1", "c": "2", "F": "4", "f": "3", "B": "3", "b": "2",
         "E": "5", "R": "1", "r": "5", "K": "5", "w": "4"}

    def rm(ch, x, y):
        col = m.get(ch, "3")
        if y % 3 == 0 and col in "14":
            col = "3"
        return col
    stamp(c, t, remap=rm, dx=0)
    for y in (24, 37):
        row = [c.get(x, y) for x in range(W)]
        for x in range(10, 50):
            if row[x - 2] in "12345":
                c.set(x, y, row[x - 2])


def starmap(c):
    c.pal.update({"Q": "14204a", "q": "26346a", "g": "3e5090", "s": "a0b8ff", "Y": "f5e6a8", "y": "c9b46a"})
    background(c, "Q")
    c.ring(30, 38, 24, 24, 1, "q")
    c.ring(30, 38, 16, 16, 1, "q")
    c.rect(6, 38, 54, 38, "q"), c.rect(30, 14, 30, 62, "q")
    stars(c, 40, "g", 9, 9, 52, 3, 72)
    stars(c, 14, "y", 4, 9, 52, 3, 72)
    pts = [(17, 50), (12, 34), (22, 22), (33, 15), (44, 24), (46, 40), (41, 50)]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        c.line(a[0], a[1], b[0], b[1], "s")
    c.line(22, 22, 25, 40, "s"), c.line(25, 40, 33, 15, "s")
    for x, y in pts + [(25, 40)]:
        sparkle(c, x, y, "Y", 1)
        c.set(x, y, "w")
    c.ring(30, 38, 24, 24, 0.9, "q")
    c.pal["w"] = "ffffff"


def bonfire(c):
    J(c, "red", "orange", top=2)
    c.pal.update({"D": "8a5a30", "d": "c08a4a", "A": "8a96a3", "I": "e63946", "G": "f08a24", "Y": "f5d742"})
    flame(c, 30, 64, 12, 20, "I")
    flame(c, 30, 64, 8, 15, "G")
    flame(c, 30, 65, 4.5, 9, "Y")
    c.line(14, 70, 44, 63, "D", 3)
    c.line(16, 63, 46, 70, "D", 3)
    c.ellipse(14, 70, 1.6, 1.6, "d"), c.ellipse(46, 70, 1.6, 1.6, "d")
    for x in range(12, 50, 6):
        c.ellipse(x, 71, 2.6, 1.6, "A")
    c.outline(keep=".w")
    for x, y in ((18, 48), (42, 50), (36, 47), (13, 56)):
        c.set(x, y, "Y")


def maneki(c):
    c.pal.update({"M": "f4f1ea", "m": "d8d0c0", "G": "f08a24", "D": "e63946", "Y": "f5d742", "y": "c9a520",
                  "I": "f07a9a"})
    c.ellipse(30, 61, 14, 11, "M")
    c.rect(16, 61, 44, 71, "M")
    c.ellipse(36, 64, 8, 7, "m", only="M")
    c.ellipse(30, 38, 12.5, 10, "M")
    c.ellipse(24, 35, 4, 3, "G")
    c.ellipse(17, 47, 3.5, 6, "M")
    c.ellipse(15.5, 39, 4, 4, "M")
    c.ellipse(40, 62, 4.5, 6, "Y")
    c.rect(38, 59, 42, 59, "y"), c.rect(38, 62, 42, 62, "y"), c.rect(38, 65, 42, 65, "y")
    c.outline(keep=".w")
    jester(c, cx=30, top=18, s=0.66, hat=P_["purple"], flaps=P_["gold"], collar=P_["purple"], hat_only=True)
    c.rect(19, 47, 41, 48, "D")
    c.ellipse(30, 50, 2.2, 2.2, "Y")
    for ex in (25, 35):
        c.set(ex - 1, 39, "K"), c.set(ex, 40, "K"), c.set(ex + 1, 39, "K")
    c.set(30, 42, "I")
    c.set(29, 44, "K"), c.set(31, 44, "K")
    c.line(13, 41, 19, 42, "m"), c.line(41, 42, 47, 41, "m")
    c.rect(14, 37, 17, 37, "m")
    c.outline(keep=".w")


def glazier(c):
    J(c, "teal", "white", top=2)
    c.pal.update({"D": "c08a4a", "Q": "cfeaf8", "M": "f6fcff", "a": "5d7a90"})
    c.rect(13, 48, 45, 71, "D")
    c.rect(15, 50, 43, 69, "Q")
    c.line(17, 60, 25, 52, "M"), c.line(18, 63, 28, 53, "M")
    for ex, ey in ((43, 50), (43, 62), (34, 69), (20, 69), (15, 56), (28, 50)):
        mx, my = (34 + ex) / 2 + (1 if ey > 58 else -1), (58 + ey) / 2
        c.line(34, 58, mx, my, "a"), c.line(mx, my, ex, ey, "a")
    c.poly([(46, 52), (49, 56), (46, 58)], "Q")
    c.poly([(46, 63), (49, 66), (47, 70)], "Q")
    c.outline(keep=".w")


def iou(c):
    J(c, "gold", "green", top=2)
    c.pal.update({"M": "f4f1ea", "m": "c9c2b0", "A": "1d3c8a", "I": "e63946"})
    c.rect(11, 50, 47, 71, "M")
    for x in range(11, 48):
        if x % 3 == 0:
            c.set(x, 71, "w")
    text(c, "IOU", 14, 53, "A", 2)
    text(c, "$20", 37, 56, "I")
    for k in range(40):
        t = k / 39
        c.set(16 + 22 * t, 66 + 2 * math.sin(t * 14), "A")
    c.rect(15, 69, 42, 69, "m")
    c.outline(keep=".w")


def nestegg(c):
    J(c, "gold", "teal", top=2)
    c.pal.update({"D": "a8743a", "d": "6e4a20", "G": "f5b82e", "g": "b8801a", "Y": "fff3a0"})
    c.ellipse(30, 63, 15, 4, "d")
    c.ellipse(30, 56, 7.5, 9.5, "G")
    c.ellipse(32, 59, 5, 6.5, "g", only="G")
    c.ellipse(29, 55, 5.5, 7.5, "G", only="g")
    c.ellipse(27, 52, 1.5, 2.5, "Y")
    for y in range(63, 72):
        for x in range(10, 51):
            if ((x - 30) / 19.5) ** 2 + ((y - 65) / 6.5) ** 2 <= 1 and y >= 63 + (1 - ((x - 30) / 15) ** 2) * 0:
                if ((x - 30) / 15) ** 2 + ((y - 63) / 4) ** 2 > 1 or y > 64:
                    c.set(x, y, "D" if (x + 2 * y) % 5 else "d")
    for x0, y0, x1, y1 in ((10, 64, 16, 60), (44, 60, 50, 65), (14, 70, 22, 66), (38, 68, 46, 70)):
        c.line(x0, y0, x1, y1, "d")
    c.outline(keep=".w")
    sparkle(c, 42, 50, "G", 2)
    sparkle(c, 17, 51, "G", 1)


def giftwrap(c):
    J(c, "pink", "green", top=2)
    c.pal.update({"I": "e63946", "i": "a02030", "G": "f5d742", "g": "c9a520", "M": "f4f1ea"})
    c.rect(15, 56, 43, 71, "I")
    c.rect(35, 57, 43, 71, "i")
    c.rect(13, 51, 45, 56, "I")
    c.rect(13, 56, 45, 56, "i")
    c.rect(27, 51, 31, 71, "G")
    c.rect(15, 62, 43, 64, "G")
    c.ellipse(23, 47.5, 5, 3.5, "G"), c.ellipse(35, 47.5, 5, 3.5, "G")
    c.ellipse(23, 47.5, 2, 1.3, "g"), c.ellipse(35, 47.5, 2, 1.3, "g")
    c.ellipse(29, 49, 2.5, 2.5, "g")
    c.line(43, 63, 47, 66, "g")
    c.poly([(45, 65), (49, 64), (49, 71), (45, 71)], "M")
    c.set(47, 68, "g"), c.set(47, 67, "g"), c.set(46, 69, "g")
    c.outline(keep=".w")


def skyrocket(c):
    J(c, "blue", "gold", cx=25, top=8, s=0.72)
    c.pal.update({"I": "e63946", "M": "f4f1ea", "D": "1d6fd1", "Y": "f5d742", "G": "f08a24", "g": "b8801a"})
    for k in range(8):
        a = k * math.pi / 4 + 0.2
        c.line(44 + 3 * math.cos(a), 12 + 3 * math.sin(a), 44 + 7 * math.cos(a), 12 + 7 * math.sin(a), "IY"[k % 2])
        c.ellipse(44 + 8.5 * math.cos(a), 12 + 8.5 * math.sin(a), 1, 1, "YI"[k % 2])
    c.ellipse(44, 12, 2.4, 2.4, "Y")
    c.set(44, 12, "g")
    c.rect(42, 32, 47, 48, "I")
    c.rect(42, 36, 47, 37, "M"), c.rect(42, 42, 47, 43, "M")
    c.poly([(42, 32), (44.5, 25), (48, 32)], "D")
    c.poly([(42, 44), (39, 50), (42, 49)], "D"), c.poly([(47, 44), (50, 50), (47, 49)], "D")
    flame(c, 44.5, 49, 2, -6, "Y")
    for k, y in enumerate(range(56, 72, 3)):
        c.set(44 + (k % 2) * 2 - 1, y, "G"), c.set(44 - (k % 2) * 2 + 1, y + 1, "Y")
    c.outline(keep=".w")


def ninelives(c):
    J(c, "dark", "gold", "dark", top=1)
    c.pal.update({"A": "4a4d6a", "a": "33354d", "I": "f07a9a", "G": "c8f060", "D": "e63946", "Y": "f5d742",
                  "M": "d8dce8"})
    c.poly([(18, 52), (20, 42), (27, 50)], "A"), c.poly([(42, 52), (40, 42), (33, 50)], "A")
    c.poly([(20, 50), (21, 45), (25, 50)], "I"), c.poly([(40, 50), (39, 45), (35, 50)], "I")
    c.ellipse(30, 57, 13, 9, "A")
    c.ellipse(34, 60, 9, 6, "a", only="A")
    c.ellipse(29, 56, 11, 7, "A", only="a")
    for ex in (24, 36):
        c.ellipse(ex, 55, 2.6, 2.2, "G")
        c.rect(ex, 53, ex, 57, "K")
    c.set(30, 59, "I"), c.set(29, 60, "K"), c.set(31, 60, "K")
    for dy in (-1, 1):
        c.line(12, 59 + dy * 2, 20, 59 + dy, "M"), c.line(40, 59 + dy, 48, 59 + dy * 2, "M")
    c.rect(20, 64, 40, 66, "D")
    c.ellipse(30, 68.5, 4, 4, "Y")
    text(c, "9", 29, 66, "K")
    c.outline(keep=".w")


def moonshot(c):
    c.pal.update({"Q": "141633", "M": "f5e6a8", "m": "d4c27e", "W": "e8eef5", "I": "e63946", "D": "42aaf0",
                  "Y": "f5d742", "G": "f08a24", "g": "b8801a", "s": "8a90b8"})
    background(c, "Q")
    stars(c, 30, "s", 12, 2, 57, 2, 72)
    c.ellipse(43, 15, 11, 11, "M")
    for x, y, r in ((40, 11, 2.5), (47, 18, 2), (38, 20, 1.5), (48, 10, 1.2)):
        c.ellipse(x, y, r, r, "m")
    c.ellipse(46, 18, 9, 9, "m", only="M")
    c.ellipse(41, 13, 9, 9, "M", only="m")
    for x, y, r in ((40, 11, 2.5), (38, 20, 1.5)):
        c.ellipse(x, y, r, r, "m")

    def rocket(t):
        t.pal.update(c.pal)
        flame(t, 30, 50, 3.5, -10, "G")
        flame(t, 30, 50, 2, -6, "Y")
        t.poly([(26, 40), (22, 50), (26, 48)], "I"), t.poly([(34, 40), (38, 50), (34, 48)], "I")
        t.rect(26, 28, 34, 49, "W")
        t.poly([(26, 28), (30, 18), (34, 28)], "I")
        t.rect(26, 43, 34, 44, "I")
        t.ellipse(30, 34, 2.6, 2.6, "D")
    layer(c, rocket, rot=0.6, dx=-10, dy=15)
    for x, y in ((24, 10), (13, 50)):
        c.ellipse(x, y, 3, 3, "Y")
        c.ellipse(x + 0.6, y + 0.6, 1.3, 1.3, "g")
    for k in range(5):
        c.ellipse(9 - k * 0 + k * 2, 70 - k * 3, 1.5 + k * 0.3, 1.5 + k * 0.3, "s")


def satellite(c):
    c.pal.update({"Q": "10122a", "D": "2a6fd1", "G": "3fb97a", "q": "7fc8ff", "A": "2a4a9a", "a": "7a9ae0",
                  "Y": "f5b82e", "y": "b8801a", "M": "e8eef5", "x": "9bf0ff", "s": "8a90b8"})
    background(c, "Q")
    stars(c, 26, "s", 21, 2, 57, 2, 50)
    c.ellipse(30, 95, 42, 38, "q")
    c.ellipse(30, 96, 40, 37, "D")
    for x, y, rx, ry in ((14, 64, 6, 3), (34, 62, 8, 2.5), (46, 70, 6, 3), (24, 71, 5, 2)):
        c.ellipse(x, y, rx, ry, "G", only="D")
    for r in (6, 9, 12):
        for k in range(30):
            a = math.pi * (0.25 + 0.5 * k / 29)
            c.set(30 + r * math.cos(a), 39 + r * math.sin(a), "x")

    def sat(t):
        t.pal.update(c.pal)
        t.rect(9, 29, 23, 36, "A"), t.rect(37, 29, 51, 36, "A")
        for x in (12, 16, 20, 40, 44, 48):
            t.rect(x, 29, x, 36, "a")
        t.rect(9, 32, 23, 32, "a"), t.rect(37, 32, 51, 32, "a")
        t.rect(23, 32, 37, 33, "M")
        t.rect(25, 27, 35, 38, "Y")
        for y in (29, 32, 35):
            t.rect(25, y, 35, y, "y")
        t.ellipse(30, 24, 7, 2.5, "M")
        t.line(30, 24, 30, 18, "M")
        t.ellipse(30, 18, 1.2, 1.2, "Y")
    layer(c, sat)


def valet(c):
    J(c, "red", "dark", top=2)
    c.pal.update({"A": "8a96a3", "D": "1d6fd1", "M": "f4f1ea", "Y": "f5b82e", "y": "b8801a", "I": "e63946"})
    c.rect(19, 62, 20, 72, "A")
    c.rect(11, 47, 28, 63, "M")
    c.rect(12, 48, 27, 62, "D")
    c.rect(16, 50, 18, 60, "M")
    c.rect(18, 50, 22, 51, "M"), c.rect(22, 51, 24, 55, "M"), c.rect(18, 55, 22, 56, "M")
    c.ring(36, 58, 4.5, 4.5, 2, "Y")
    c.rect(40, 57, 49, 59, "Y")
    c.rect(43, 60, 44, 62, "Y"), c.rect(46, 60, 47, 61, "Y")
    c.rect(40, 59, 49, 59, "y")
    c.line(34, 62, 33, 66, "y")
    c.poly([(30, 66), (36, 66), (36, 72), (30, 72)], "I")
    c.set(33, 68, "M")
    c.outline(keep=".w")


def bootstraps(c):
    J(c, "orange", "green", top=2)
    c.pal.update({"D": "a8743a", "d": "6e4a20", "A": "3a3d5c", "G": "f5b82e", "g": "b8801a"})
    for x0 in (11, 30):
        c.ring(x0 + 2, 50, 2.6, 3, 1, "d")
        c.ring(x0 + 8, 50, 2.6, 3, 1, "d")
        c.rect(x0, 51, x0 + 9, 64, "D")
        c.rect(x0, 51, x0 + 9, 52, "d")
        c.poly([(x0, 63), (x0 + 14, 63), (x0 + 17, 66), (x0 + 17, 69), (x0, 69)], "D")
        c.rect(x0 - 1, 69, x0 + 18, 71, "A")
        c.rect(x0 + 7, 55, x0 + 9, 63, "d")
    c.outline(keep=".w")


def toreador(c):
    J(c, "red", "gold", "dark", top=2)
    c.pal.update({"I": "d62839", "i": "9a1a28", "Y": "f5d742", "D": "8a5a30"})
    c.line(10, 48, 49, 46, "D", 2)
    pts = [(11, 49), (48, 47), (49, 60), (45, 66), (40, 62), (35, 71), (28, 64), (22, 71), (16, 64), (10, 69)]
    c.poly(pts, "I")
    for x0, x1 in ((18, 16), (27, 28), (37, 35), (45, 45)):
        c.line(x0, 50, x1, 64, "i")
    c.poly([(40, 62), (35, 71), (38, 64)], "Y")
    c.poly([(10, 69), (16, 64), (13, 66)], "Y")
    c.outline(keep=".w")


def wanderer(c):
    J(c, "teal", "orange", top=2)
    c.pal.update({"D": "a8743a", "I": "e63946", "M": "f4f1ea", "A": "9b5de5", "Y": "f5d742"})
    c.poly(rot_pts([(29, 50), (36, 50), (36, 60), (29, 60)], -0.35, 33, 55), "A")
    sparkle(c, 32, 55, "Y", 1)
    c.line(11, 72, 47, 49, "D", 2)
    c.ellipse(41, 60, 8.5, 7.5, "I")
    c.poly([(37, 52), (41, 49), (40, 55)], "I"), c.poly([(45, 52), (42, 49), (42, 55)], "I")
    for x, y in ((37, 59), (43, 57), (40, 64), (46, 63), (35, 64)):
        c.set(x, y, "M"), c.set(x + 1, y, "M"), c.set(x, y + 1, "M"), c.set(x + 1, y + 1, "M")
    c.outline(keep=".w")


def trader(c):
    J(c, "green", "gold", top=2)
    c.pal.update({"M": "f4f1ea", "I": "e63946", "D": "f2c9a0", "d": "c99a70", "G": "f5b82e", "g": "b8801a",
                  "Q": "2a8a58"})
    c.rect(12, 48, 25, 65, "M")
    suit_shape(c, "heart", 18.5, 56, 4, "I")
    c.ellipse(18, 67, 7, 4.5, "D")
    c.ellipse(24, 63, 2, 3, "D")
    c.rect(13, 65, 22, 65, "d")
    c.ellipse(41, 58, 6.5, 6.5, "G")
    c.ring(41, 58, 6.5, 6.5, 1.2, "g")
    text(c, "$", 40, 56, "g")
    c.rect(28, 54, 34, 54, "Q"), c.line(32, 52, 34, 54, "Q"), c.line(32, 56, 34, 54, "Q")
    c.rect(29, 62, 35, 62, "Q"), c.line(31, 60, 29, 62, "Q"), c.line(31, 64, 29, 62, "Q")
    c.outline(keep=".w")


def burglar(c):
    J(c, "dark", "white", top=2, collar=None)
    jester(c, top=2, hat=P_["dark"], flaps=P_["white"], collar=("f4f1ea", "3a3d5c"))
    c.pal.update({"A": "1b1c2e", "D": "b8a888", "d": "8a7a5a"})
    c.rect(21, 21, 39, 25, "A")
    c.poly([(39, 21), (45, 19), (43, 23), (46, 26), (39, 25)], "A")
    for ex in (26, 33):
        c.rect(ex, 23, ex + 1, 23, "F")
    c.ellipse(37, 61, 11, 9.5, "D")
    c.ellipse(40, 64, 7, 6, "d", only="D")
    c.ellipse(36, 60, 8, 7, "D", only="d")
    c.poly([(30, 53), (27, 47), (33, 49), (35, 53)], "D")
    c.rect(29, 52, 35, 53, "d")
    dollar(c, 35, 58, "d")
    c.outline(keep=".w")


def tipsy(c):
    c.pal.update({"Q": "bfe6ff", "q": "42aaf0", "M": "e8f4ff", "Y": "f5d742"})
    t = TJ("pink", "sky", top=8)
    stamp(c, t, rot=0.28, pivot=(30, 30), dx=-1)
    c.pal["R"] = "f05a6a"

    def glass(t2):
        t2.pal.update(c.pal)
        t2.ellipse(30, 40, 8, 5, "M")
        t2.rect(22, 34, 38, 39, ".")
        t2.ellipse(30, 40, 8, 2, "Y")
        t2.rect(22, 34, 38, 38, ".")
        t2.rect(29, 45, 30, 51, "M")
        t2.ellipse(30, 52, 5, 1.5, "M")
    layer(c, glass, rot=-0.45, pivot=(30, 45), dx=-2, dy=17)
    for x, y, r in ((40, 52, 1.6), (44, 46, 1.2), (47, 40, 2), (42, 36, 1.3), (48, 30, 1.5), (13, 50, 1.4)):
        c.ring(x, y, r + 0.5, r + 0.5, 0.8, "q")
    c.outline(keep=".w")


def juggler(c):
    J(c, "orange", "purple", top=22, s=0.72)
    cols = {"1": "e63946", "2": "f5b82e", "3": "3fb97a", "4": "42aaf0", "5": "9b5de5"}
    c.pal.update(cols)
    for i in range(5):
        a = math.pi * (1.1 + 0.8 * i / 4)
        x, y = 30 + 20 * math.cos(a), 44 + 34 * math.sin(a)
        c.ellipse(x, y, 3.2, 3.2, "12345"[i])
        c.set(x - 1, y - 1, "w")
    for k in range(30):
        a = math.pi * (1.15 + 0.7 * k / 29)
        if k % 3 == 0:
            c.set(30 + 20 * math.cos(a), 44 + 34 * math.sin(a), "f")
    c.outline(keep=".w")


def minstrel(c):
    J(c, "green", "red", top=2, cx=28)
    c.pal.update({"D": "c08a4a", "d": "8a5a30", "M": "f4f1ea", "A": "9b5de5"})
    c.line(27, 59, 43, 48, "d", 3)
    c.line(43, 48, 47, 52, "d", 3)
    for x, y in ((44, 50), (46, 52)):
        c.set(x, y - 2, "M")
    c.ellipse(22, 62, 10, 8, "D")
    c.ellipse(25, 65, 6, 5, "d", only="D")
    c.ellipse(21, 61, 7, 6, "D", only="d")
    c.ellipse(23, 61, 2.5, 2.5, "K")
    c.rect(16, 64, 20, 65, "d")
    c.line(18, 64, 43, 48, "M")
    c.line(19, 65, 44, 49, "M")
    note(c, 12, 52, "A")
    c.outline(keep=".w")


def merry(c):
    import random
    rnd = random.Random(4)
    cols = {"1": "e63946", "2": "f5b82e", "3": "3fb97a", "4": "42aaf0", "5": "9b5de5"}
    c.pal.update(cols)
    for _ in range(46):
        x, y = rnd.randint(10, 49), rnd.randint(3, 72)
        if 52 <= x and y >= 30:
            continue
        col = rnd.choice("12345")
        if rnd.random() < 0.5:
            c.rect(x, y, x + 1, y, col)
        else:
            c.rect(x, y, x, y + 1, col)
    J(c, "pink", "gold", top=8, grin=True)
    for k in range(30):
        t = k / 29
        c.set(12 + 34 * t, 62 + 4 * math.sin(t * 9), "5" if k < 15 else "4")
        c.set(14 + 32 * t, 68 + 3 * math.sin(t * 7 + 2), "1")
    c.outline(keep=".w")


def daredevil(c):
    c.pal.update({"A": "8a96a3", "D": "3a3d5c", "Y": "f5d742", "y": "c08a4a", "I": "e63946"})
    c.poly([(30, 72), (49, 72), (49, 56)], "y")
    c.line(31, 71, 49, 57, "Y")
    for k in range(3):
        c.line(36 + k * 5, 71, 36 + k * 5, 71 - (k + 1) * 4 + 1, "Y")
    c.line(22, 36, 22, 58, "A", 2)
    c.ellipse(22, 37, 4.5, 1.5, "D")
    c.ring(22, 63, 8, 8, 2, "D")
    for k in range(4):
        a = k * math.pi / 4
        c.line(22 - 6 * math.cos(a), 63 - 6 * math.sin(a), 22 + 6 * math.cos(a), 63 + 6 * math.sin(a), "A")
    c.ellipse(22, 63, 1.5, 1.5, "D")
    c.outline(keep=".w")
    t = TJ("red", "gold", cx=22, top=7, s=0.66)
    stamp(c, t, rot=-0.15, pivot=(22, 30))
    for x, y in ((40, 14), (46, 26), (36, 30)):
        sparkle(c, x, y, "Y", 2)
    c.pal["I"] = "e63946"


def sprout(c):
    J(c, "green", "orange", top=1, s=0.8)
    c.pal.update({"D": "c9733a", "d": "8a4a20", "k": "4a3020", "G": "3fb97a", "g": "2a8a58", "Y": "c9c040"})
    c.rect(29, 46, 30, 60, "G")
    for i, (x, y, side) in enumerate(((30, 48, -1), (30, 48, 1), (30, 52, -1), (30, 55, 1), (30, 57, -1))):
        c.ellipse(x + side * 4, y, 3.5, 1.8, "G")
        c.set(x + side * 4, y, "g")
    c.ellipse(43, 53, 2.5, 1.5, "Y")
    c.rect(18, 59, 42, 62, "D")
    c.poly([(20, 62), (40, 62), (37, 72), (23, 72)], "D")
    c.poly([(33, 62), (40, 62), (37, 72), (32, 72)], "d")
    c.rect(19, 59, 41, 59, "k")
    c.outline(keep=".w")


def noodles(c):
    J(c, "orange", "red", top=2)
    c.pal.update({"D": "e8eef5", "A": "1d6fd1", "Y": "e8b060", "M": "f5e08a", "d": "c08a4a", "q": "c9d3dc"})
    c.line(33, 60, 47, 45, "d", 2)
    c.line(35, 61, 49, 48, "d", 2)
    c.ellipse(30, 59, 17, 12, "D")
    c.rect(12, 46, 48, 58, "w", only="D")
    c.ellipse(30, 59, 17, 3, "Y")
    for k in range(4):
        for x in range(16, 44):
            c.set(x, 58 + (k % 2) + int(1.3 * math.sin(x * 0.9 + k * 2)), "M") if k < 2 else None
    for x in range(14, 47, 4):
        c.line(x, 64, x + 2, 66, "A"), c.line(x + 2, 66, x + 4, 64, "A")
    for k in range(3):
        x = 39 + k
        c.line(x, 58, x + 2, 50 + k, "M")
    c.outline(keep=".w")
    for x0 in (16, 21):
        for y in range(46, 54):
            c.set(x0 + int(1.5 * math.sin(y * 0.8)), y, "q")


def chaos(c):
    cols = ["e63946", "f08a24", "f5d742", "3fb97a", "42aaf0", "9b5de5"]
    for i, col in enumerate(cols):
        c.pal["123456"[i]] = col
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            dx, dy = x + 0.5 - 30, y + 0.5 - 36
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx) + r * 0.13
            c.set(x, y, "123456"[int((a / (2 * math.pi)) * 6 + 60) % 6])
    t = TJ("purple", "teal", top=12, s=0.7, grin=True)
    stamp(c, t)

    def die(t2):
        t2.pal.update({"M": "f4f1ea", "m": "c9c2b0"})
        t2.rect(24, 54, 36, 66, "M")
        t2.rect(35, 54, 36, 66, "m"), t2.rect(24, 65, 36, 66, "m")
        for px, py in ((27, 57), (33, 63), (30, 60), (27, 63), (33, 57)):
            t2.rect(px - 1, py - 1, px, py, "K")
    layer(c, die, rot=0.25, pivot=(30, 60), dy=2)


def stargazer(c):
    J(c, "dark", "sky", "dark", cx=27, top=3, s=0.8)
    c.pal.update({"A": "1d3c8a", "G": "f5b82e", "g": "b8801a", "d": "6e4a20", "Y": "f5d742"})
    c.line(33, 61, 22, 72, "d"), c.line(33, 61, 33, 72, "d"), c.line(33, 61, 44, 72, "d")
    c.line(22, 66, 46, 50, "A", 4)
    c.line(44, 51, 48, 48, "A", 5)
    for x, y in ((28, 62), (37, 56)):
        c.line(x - 1, y - 2, x + 1, y + 2, "G", 2)
    c.ellipse(33, 60, 2, 2, "g")
    c.outline(keep=".w")
    sparkle(c, 46, 39, "Y", 3)
    sparkle(c, 40, 46, "G", 1)
    c.pal["Y"] = "f5d742"


def license(c):
    c.pal.update({"M": "eef4ff", "A": "4a6fa5", "a": "a8b8d0", "G": "f5b82e", "g": "b8801a", "Q": "cfe3f5"})
    c.rect(9, 48, 49, 71, "M")
    c.rect(9, 48, 49, 52, "A")
    c.rect(12, 55, 24, 69, "Q")
    for y in (57, 61, 65):
        c.rect(27, y, 45 - (y % 3) * 4, y, "a")
    c.ellipse(43, 66, 3.5, 3.5, "G")
    c.ring(43, 66, 3.5, 3.5, 1, "g")
    c.rect(41, 69, 41, 71, "I"), c.rect(45, 69, 45, 71, "I")
    c.pal["I"] = "e63946"
    c.outline(keep=".w")
    J(c, "red", "blue", "gold", top=2)
    jester(c, cx=18, top=55, s=0.29, hat=P_["red"], flaps=P_["blue"], collar=P_["gold"], key="2")
    for x in range(12, 25):
        for y in range(55, 70):
            if c.get(x, y) == "w":
                c.set(x, y, "Q")
    c.outline(keep=".w")


def pennant(c):
    J(c, "green", "white", top=2)
    c.pal.update({"D": "8a5a30", "G": "3fb97a", "g": "2a8a58", "Y": "f5d742", "M": "f4f1ea"})
    c.rect(13, 46, 14, 72, "D")
    c.ellipse(13.5, 46, 1.8, 1.8, "Y")
    c.poly([(15, 49), (48, 57), (15, 66)], "G")
    c.poly([(15, 58), (48, 57), (15, 66)], "g")
    c.poly([(15, 53), (34, 57), (15, 62)], "Y", only="Gg")
    suit_shape(c, "diamond", 22, 57.5, 3, "M")
    c.outline(keep=".w")


def tracing(c):
    c.pal.update({"Q": "d6e8f8", "q": "c2daf0", "A": "1d6fd1", "Y": "f5d742", "y": "c9a520", "D": "f2c9a0",
                  "k": "3a3d5c"})
    background(c, "Q")
    for k in range(1, 12):
        c.rect(1, k * 6, W - 2, k * 6, "q")
        c.rect(k * 6 - 1, 1, k * 6 - 1, H - 2, "q")
    t = TJ("red", top=10)
    c.pal["W"] = "eef5fd"
    for y in range(H):
        for x in range(W):
            if t.get(x, y) == "K":
                if (x + y) % 4 != 0:
                    c.set(x, y, "A")
            elif t.get(x, y) in "EJj":
                c.set(x, y, "A")
            elif t.get(x, y) != ".":
                c.set(x, y, "W")
    c.line(40, 66, 50, 56, "Y", 3)
    c.line(41, 67, 50, 58, "y")
    c.poly([(38, 70), (37, 65), (42, 68)], "D")
    c.set(37, 70, "k")
    for x in range(12, 33, 2):
        c.set(x, 66, "A")
    c.poly([(33, 63), (37, 66), (33, 69)], "A")


def brainwave(c):
    J(c, "purple", "sky", top=2)
    c.pal.update({"I": "f4a6c0", "i": "d0708f", "Y": "f5d742", "y": "c9a520", "A": "42aaf0"})
    c.ellipse(34, 60, 13, 9.5, "I")
    c.ellipse(37, 63, 9, 6, "i", only="I")
    c.ellipse(33, 59, 10, 7.5, "I", only="i")
    c.line(34, 51, 34, 66, "i")
    for x0, y0 in ((26, 56), (40, 55), (28, 63), (40, 63), (31, 58), (37, 59)):
        for k in range(5):
            c.set(x0 + k, y0 + (1 if k % 2 else 0), "i")
    c.poly([(23, 56), (16, 60), (20, 61), (11, 67), (22, 62), (18, 61), (24, 58)], "Y")
    c.outline(keep=".w")
    for r in (3, 6):
        for k in range(10):
            a = -0.7 + 1.4 * k / 9
            c.set(47 + r * math.cos(a) - 2, 60 + r * math.sin(a), "A") if 47 + r * math.cos(a) - 2 <= 50 else None


def phantom(c):
    c.pal.update({"1": "1c1530", "2": "2a1f45", "3": "c9c2ff", "4": "8a80c8", "5": "eef0ff", "6": "2a2050",
                  "7": "3e3270", "8": "5a4c96"})
    background(c, "1")
    c.ellipse(30, 38, 24, 30, "2")
    t = TJ("purple", "white", top=8, s=0.84)
    m = {"H": "3", "h": "4", "J": "5", "j": "3", "C": "3", "c": "4", "F": "5", "f": "3", "B": "5", "b": "3",
         "E": "6", "R": "3", "r": "6", "K": "8", "w": "5"}
    stamp(c, t, remap=lambda ch, x, y: "7", dx=7, dy=-3)
    for y in range(40, 70):
        half = 14 - (y - 40) * 0.1
        for x in range(int(30 - half), int(30 + half) + 1):
            if y < 64 + 3 * math.sin(x * 0.8) and (y < 56 or (x + y) % 2 == 0 or y < 60):
                c.set(x, y, "3" if x > 30 + half - 4 else "5" if y < 50 else "3")
    stamp(c, t, remap=lambda ch, x, y: m.get(ch, "3"))
    for x, y in ((12, 50), (47, 14), (14, 20), (46, 60), (11, 66)):
        c.set(x, y, "4"), c.set(x + 1, y + 1, "3")


def loaded(c):
    J(c, "red", "white", top=2)
    c.pal.update({"M": "f4f1ea", "m": "c9c2b0", "I": "e63946"})

    def die(t, x0, y0, pips):
        t.pal.update(c.pal)
        t.rect(x0, y0, x0 + 13, y0 + 13, "M")
        t.rect(x0 + 12, y0, x0 + 13, y0 + 13, "m"), t.rect(x0, y0 + 12, x0 + 13, y0 + 13, "m")
        for px, py in pips:
            t.rect(x0 + px - 1, y0 + py - 1, x0 + px, y0 + py, "I")
        t.set(x0, y0, "."), t.set(x0 + 13, y0, "."), t.set(x0, y0 + 13, "."), t.set(x0 + 13, y0 + 13, ".")
    six = [(4, 3), (4, 7), (4, 11), (9, 3), (9, 7), (9, 11)]
    layer(c, lambda t: die(t, 12, 52, six), rot=-0.2, pivot=(19, 59))
    layer(c, lambda t: die(t, 32, 51, six), rot=0.25, pivot=(39, 58))
    c.outline(keep=".w")


def crystal(c):
    J(c, "purple", "teal", top=2)
    c.pal.update({"A": "8fd8f0", "a": "9b5de5", "M": "f4fbff", "G": "f5b82e", "g": "b8801a", "D": "6a3fa0"})
    c.ellipse(30, 57, 10.5, 10.5, "A")
    c.ellipse(34, 61, 8, 7, "a", only="A")
    c.ellipse(29, 56, 8, 8, "A", only="a")
    c.ring(30, 54, 2.6, 2.4, 1, "D")
    c.ring(30, 59, 3, 2.6, 1, "D")
    c.ellipse(25, 52, 2, 1.3, "M")
    c.ellipse(30, 67, 8, 2.5, "G")
    c.poly([(22, 67), (38, 67), (42, 72), (18, 72)], "G")
    c.rect(18, 71, 42, 72, "g")
    c.outline(keep=".w")


def secondsight(c):
    J(c, "teal", "purple", top=2)
    c.pal.update({"M": "f4f1ea", "A": "9b5de5", "a": "6a3fa0", "Y": "f5d742"})
    pts_top = [(12 + k, 60 - 9 * math.sin(math.pi * k / 36)) for k in range(37)]
    pts_bot = [(48 - k, 60 + 8 * math.sin(math.pi * k / 36)) for k in range(37)]
    c.poly(pts_top + pts_bot, "M")
    c.ellipse(30, 60, 6.5, 6.5, "A", only="M")
    c.ring(30, 60, 6.5, 6.5, 1.3, "a")
    c.ellipse(30, 60, 2.6, 2.6, "K")
    c.set(28, 57, "M"), c.set(27, 58, "M")
    c.outline(keep=".w")
    for k in range(7):
        a = math.pi * (1.15 + 0.7 * k / 6)
        c.line(30 + 15 * math.cos(a), 60 + 10 * math.sin(a), 30 + 18 * math.cos(a), 60 + 13 * math.sin(a), "K")
    c.set(30, 19, "Y"), c.set(29, 20, "Y"), c.set(31, 20, "Y"), c.set(30, 21, "Y")


def ouija(c):
    J(c, "dark", "gold", "dark", top=2)
    c.pal.update({"D": "8a5a30", "d": "5a3a20", "Y": "e8d8a0", "M": "f4f1ea"})
    c.rect(9, 48, 49, 72, "D")
    c.rect(9, 48, 49, 49, "d"), c.rect(9, 71, 49, 72, "d")
    text(c, "YES", 11, 51, "Y")
    text(c, "NO", 41, 51, "Y")
    for k in range(13):
        a = math.pi * (1.15 + 0.7 * k / 12)
        x, y = 30 + 17 * math.cos(a), 72 + 15 * math.sin(a)
        c.set(x, y, "Y"), c.set(x, y + 1, "Y"), c.set(x + 1, y + (k % 2), "Y")
    c.poly([(30, 59), (37, 66), (36, 70), (24, 70), (23, 66)], "M")
    c.ellipse(30, 66, 1.6, 1.6, "D")
    c.outline(keep=".w")


def quantum(c):
    J(c, "sky", "white", top=2)
    c.pal.update({"A": "42aaf0", "Y": "f5d742", "I": "e63946", "D": "1d6fd1"})
    rx, ry, cx, cy = 15, 4.5, 30, 59
    for th in (0, math.pi / 3, -math.pi / 3):
        for k in range(160):
            t = 2 * math.pi * k / 160
            x = cx + rx * math.cos(t) * math.cos(th) - ry * math.sin(t) * math.sin(th)
            y = cy + rx * math.cos(t) * math.sin(th) + ry * math.sin(t) * math.cos(th)
            c.set(x, y, "A")
    for i, (dx, dy) in enumerate(((-1.5, -1), (1.5, -1), (0, 1.5), (-2, 1.5), (2, 1.5))):
        c.ellipse(cx + dx, cy + dy, 2, 2, "ID"[i % 2])
    for th, t in ((0, 0.3), (math.pi / 3, 2.4), (-math.pi / 3, 4.2)):
        x = cx + rx * math.cos(t) * math.cos(th) - ry * math.sin(t) * math.sin(th)
        y = cy + rx * math.cos(t) * math.sin(th) + ry * math.sin(t) * math.cos(th)
        c.ellipse(x, y, 1.8, 1.8, "Y")
    c.outline(keep=".wA")


def diviner(c):
    J(c, "purple", "gold", top=1, s=0.8)
    c.pal.update({"G": "f5b82e", "A": "4b3a8a", "M": "f4e7c4", "Y": "f5d742", "I": "e63946"})
    for a in (-0.62, 0.62, -0.31, 0.31, 0.0):
        card = rot_pts([(-6, -20), (6, -20), (6, 0), (-6, 0)], a, 0, 0)
        inner = rot_pts([(-4.5, -18.5), (4.5, -18.5), (4.5, -1.5), (-4.5, -1.5)], a, 0, 0)
        def one(t, a=a, card=card, inner=inner):
            t.pal.update(c.pal)
            t.poly([(30 + x, 72 + y) for x, y in card], "G")
            t.poly([(30 + x, 72 + y) for x, y in inner], "A" if a else "M")
            mx, my = 30 + 10 * math.sin(a), 72 - 10 * math.cos(a)
            if a:
                sparkle(t, mx, my, "Y", 1)
            else:
                t.ellipse(mx, my, 2.5, 2.5, "Y")
                for k in range(8):
                    b = k * math.pi / 4
                    t.set(mx + 4 * math.cos(b), my + 4 * math.sin(b), "I")
        layer(c, one)
    c.outline(keep=".w")


def notary(c):
    J(c, "dark", "red", "dark", top=2)
    c.pal.update({"M": "f4f1ea", "m": "c9c2b0", "I": "c0283a", "i": "8a1a28", "D": "8a5a30", "d": "c08a4a"})
    c.rect(10, 50, 31, 71, "M")
    for y in (54, 57, 60):
        c.rect(13, y, 28, y, "m")
    for k in range(12):
        a = k * math.pi / 6
        c.ellipse(24 + 5.5 * math.cos(a), 65 + 5.5 * math.sin(a), 1.4, 1.4, "I")
    c.ellipse(24, 65, 5, 5, "I")
    c.ring(24, 65, 3, 3, 1, "i")
    c.ellipse(41, 49, 3.5, 3, "d")
    c.rect(39, 51, 43, 59, "D")
    c.rect(34, 59, 48, 64, "d")
    c.rect(34, 64, 48, 66, "I")
    c.rect(34, 69, 48, 70, "I")
    c.outline(keep=".w")


def clone(c):
    J(c, "teal", "pink", top=2)
    c.pal.update({"M": "f4f1ea", "I": "e63946", "G": "3fb97a", "D": "42aaf0", "m": "c9c2b0"})
    for x0 in (10, 37):
        c.rect(x0, 51, x0 + 12, 70, "M")
        suit_shape(c, "heart", x0 + 6, 61, 4, "I")
        text(c, "A", x0 + 1, 52, "I")
    for x in range(23, 37):
        p = (x - 23) / 13 * 2 * math.pi
        y1, y2 = 61 + 4 * math.sin(p), 61 - 4 * math.sin(p)
        if x % 3 == 0:
            c.line(x, y1, x, y2, "m")
        c.set(x, y1, "G"), c.set(x, y1 + 1, "G")
        c.set(x, y2, "D"), c.set(x, y2 + 1, "D")
    c.outline(keep=".w")


def rabble(c):
    pals = {"red": ("1", "2"), "blue": ("3", "4"), "gold": ("5", "6"), "green": ("7", "8"), "purple": ("9", "0"),
            "orange": ("A", "a"), "teal": ("D", "d")}
    for name, (a, b) in pals.items():
        c.pal[a], c.pal[b] = P_[name]
    c.pal.update({"B": "f5d742", "b": "c9a520"})
    spots = [(20, 10, "red", "gold"), (40, 10, "green", "purple"), (30, 22, "blue", "orange"),
             (20, 33, "orange", "teal"), (40, 33, "purple", "gold"), (24, 46, "teal", "red"),
             (38, 47, "gold", "blue"), (30, 58, "red", "green")]
    for x, y, hat, fl in spots:
        t = Canvas({})
        jester(t, cx=x, top=y, s=0.45, hat=P_[hat], flaps=P_[fl], hat_only=True)
        ha, hb = pals[hat]
        fa, fb = pals[fl]
        stamp(c, t, remap={"H": ha, "h": hb, "J": fa, "j": fb, "C": fa})


def kindling(c):
    J(c, "orange", "dark", top=2)
    c.pal.update({"D": "a8743a", "d": "6e4a20", "I": "e63946", "G": "f08a24", "Y": "f5d742", "y": "e8c08a"})
    flame(c, 40, 59, 6, 14, "I")
    flame(c, 40, 59, 3.5, 9, "G")
    flame(c, 40, 60, 1.8, 5, "Y")
    for i, y in enumerate((58, 61, 64, 67, 60, 65)):
        x0 = 11 + (i * 3) % 5
        c.line(x0, y + (i % 2), 46 - (i * 2) % 4, y + 1 - (i % 2), "Dd"[i % 2], 2)
        c.set(x0, y + (i % 2), "y")
    c.rect(20, 56, 21, 69, "I"), c.rect(34, 56, 35, 69, "I")
    c.outline(keep=".w")


def orbit(c):
    J(c, "sky", "orange", top=2)
    c.pal.update({"D": "f08a24", "d": "c05a20", "Y": "f5d742", "y": "c9a520", "M": "f4e7c4"})
    th = -0.25
    pts = []
    for k in range(240):
        t = 2 * math.pi * k / 240
        for rr in (19, 18, 17):
            x = 30 + rr * math.cos(t) * math.cos(th) - 4.5 * (rr / 19) * math.sin(t) * math.sin(th)
            y = 60 + rr * math.cos(t) * math.sin(th) + 4.5 * (rr / 19) * math.sin(t) * math.cos(th)
            pts.append((x, y, math.sin(t) > 0, "Y" if rr != 17 else "y"))
    for x, y, front, col in pts:
        if not front:
            c.set(x, y, col)
    c.ellipse(30, 60, 9.5, 9.5, "D")
    for y in (55, 59, 63):
        c.rect(20, y, 40, y + 1, "d", only="D")
    c.ellipse(27, 56, 2, 1.5, "M")
    for x, y, front, col in pts:
        if front:
            c.set(x, y, col)
    c.ellipse(13, 49, 2, 2, "M")
    c.outline(keep=".w")


def blankmask(c):
    J(c, "white", "dark", "white", top=2)
    c.pal.update({"M": "f4f1ea", "m": "c9c2b0", "I": "e63946"})
    c.line(10, 56, 20, 60, "I", 2), c.line(50, 56, 40, 60, "I", 2)
    c.line(10, 56, 12, 66, "I"), c.line(49, 56, 47, 66, "I")
    c.ellipse(30, 60, 11, 11.5, "M")
    c.ellipse(33, 63, 8, 8.5, "m", only="M")
    c.ellipse(29, 59, 9, 10, "M", only="m")
    c.ellipse(26, 57, 2.2, 1.5, "K"), c.ellipse(34, 57, 2.2, 1.5, "K")
    c.outline(keep=".w")


def roadtrip(c):
    c.pal.update({"1": "9fd8f5", "2": "6ab06a", "3": "5aa85a", "4": "4a8f4a", "A": "6d7078", "a": "4d5058",
                  "Y": "f5d742", "D": "2ec4b6", "d": "1a8a80", "I": "e63946", "M": "f4f1ea", "k": "2b2d42",
                  "G": "f5b82e"})
    gradient(c, "1", 1, 34)
    for x in range(1, W - 1):
        c.rect(x, int(30 + 3 * math.sin(x / 6.0)), x, 36, "2")
    c.rect(1, 36, W - 2, H - 2, "3")
    for y in range(40, H - 1, 5):
        c.rect(1, y, W - 2, y, "4", only="3")
    c.poly([(28, 36), (32, 36), (56, H - 2), (4, H - 2)], "A")
    c.poly([(28, 36), (29, 36), (6, H - 2), (4, H - 2)], "a")
    c.poly([(31, 36), (32, 36), (56, H - 2), (54, H - 2)], "a")
    for y in range(38, 52, 4):
        w = (y - 36) / 38
        c.rect(30 - w, y, 30 + w, y + 1 + (y > 44), "Y")

    def sign(t):
        t.pal.update(c.pal)
        t.rect(46, 35, 46, 46, "a")
        t.poly([(46, 27), (51, 32), (46, 37), (41, 32)], "Y")
        text(t, "J", 45, 30, "k")
    layer(c, sign)
    t = TJ("red", "gold", top=36, s=0.5)
    stamp(c, t, dst_clip=lambda x, y: y < 55)

    def car(t2):
        t2.pal.update(c.pal)
        t2.rect(15, 54, 45, 66, "D")
        t2.rect(15, 62, 45, 66, "d")
        t2.rect(13, 57, 15, 60, "D"), t2.rect(45, 57, 47, 60, "D")
        t2.rect(17, 57, 21, 59, "I"), t2.rect(39, 57, 43, 59, "I")
        t2.rect(26, 59, 34, 62, "M")
        t2.rect(16, 66, 21, 70, "k"), t2.rect(39, 66, 44, 70, "k")
    layer(c, car)


def doublevision(c):
    J(c, "pink", "teal", top=2)
    c.pal.update({"I": "e63946", "D": "2ec4d6", "A": "3a3d5c"})
    t1, t2 = Canvas({}), Canvas({})
    suit_shape(t1, "club", 25, 60, 9.5, "x")
    suit_shape(t2, "club", 35, 60, 9.5, "x")
    for y in range(46, 73):
        for x in range(9, 50):
            a, b = t1.get(x, y) == "x", t2.get(x, y) == "x"
            if a or b:
                c.set(x, y, "A" if a and b else "I" if a else "D")
    c.outline(keep=".w")
    for ex in (26.5, 33.5):
        c.set(ex + 1, 22, "J")


def tiny(c):
    c.pal.update({"M": "f4f1ea", "m": "d8d0c0", "A": "3a3d5c", "I": "e63946"})
    c.rect(13, 7, 47, 60, "M")
    c.rect(44, 9, 46, 60, "m")
    text(c, "2", 15, 9, "A")
    suit_shape(c, "spade", 16.5, 17, 2, "A")
    suit_shape(c, "spade", 30, 21, 6, "A")
    suit_shape(c, "spade", 30, 45, 6, "A")
    c.outline(keep=".w")
    jester(c, cx=30, top=50, s=0.45, hat=P_["orange"], flaps=P_["sky"], collar=P_["orange"])


def ringmaster(c):
    J(c, "red", "gold", top=2)
    c.pal.update({"A": "3a3d5c", "a": "22243a", "I": "e63946", "G": "f5b82e", "D": "8a5a30", "d": "5a3a20"})
    c.rect(15, 49, 31, 65, "A")
    c.rect(27, 49, 31, 65, "a")
    c.rect(15, 60, 31, 63, "I")
    c.ellipse(23, 66, 12, 2.6, "A")
    c.ellipse(23, 49, 8, 1.6, "a")
    pts = [(40, 70), (42, 60), (45, 54), (48, 49), (47, 46), (43, 46), (41, 49), (43, 51)]
    for a, b in zip(pts[1:], pts[2:]):
        c.line(a[0], a[1], b[0], b[1], "d")
    c.line(39, 71, 42, 60, "D", 2)
    c.rect(40, 60, 43, 61, "G")
    c.outline(keep=".w")


def lastlaugh(c):
    jester(c, top=2, hat=P_["dark"], flaps=P_["purple"], collar=P_["dark"], grin=True, face="f4f1ea")
    c.pal.update({"R": "dcd3c3", "M": "f4f1ea", "I": "e63946"})
    for ex in (26.5, 33.5):
        c.ellipse(ex, 24.5, 2.4, 2.6, "E")
    c.set(29.5, 28, "E"), c.set(30.5, 28, "E"), c.set(30, 29, "E")
    c.line(36, 15, 38, 19, "E")
    c.ring(30, 60, 11, 11, 4.5, "M")
    for k in range(4):
        a0 = k * math.pi / 2 + math.pi / 4
        for r in (7, 8, 9, 10):
            for j in range(-6, 7):
                a = a0 + j * 0.06
                c.set(30 + r * math.cos(a), 60 + r * math.sin(a), "I")
    c.line(36, 50, 37, 54, "w", 1)
    c.line(37, 54, 35, 56, "w", 1)
    c.outline(keep=".w")


def wear(c):
    J(c, "orange", "white", top=2)
    c.pal.update({"D": "c9a060", "d": "8a6a30"})
    for x in range(9, 50):
        thin = 26 <= x <= 33
        if thin:
            for k, off in enumerate((-2, 0, 2)):
                if not (x in (28, 29) and k != 1) and not (x == 31 and k == 0):
                    c.set(x, 60 + off + int(math.sin(x + k)), "D")
            continue
        r = 4 if x < 22 or x > 37 else 4 - (abs(x - 29.5) < 8) * (8 - abs(x - 29.5)) * 0.4
        c.rect(x, 60 - r, x, 60 + r, "D")
        for y in range(int(60 - r), int(60 + r) + 1):
            if (x + y) % 5 == 0:
                c.set(x, y, "d")
    for x, y in ((25, 55), (34, 65), (26, 66)):
        c.line(x, y, x + 2, y - 2 if y > 60 else y + 2, "D")
    c.outline(keep=".w")


# ------------------------------------------------------------------ legendary charms (full art)

def bonecrown(c):
    c.pal.update({"1": "120d1c", "2": "24183a", "3": "3a2456", "M": "efe6d2", "m": "b8ab90", "k": "2a2040",
                  "Y": "c9a0ff"})
    background(c, "1")
    c.ellipse(30, 30, 25, 26, "2")
    c.ellipse(30, 28, 15, 16, "3")
    stars(c, 16, "k", 2, 2, 57, 2, 72)
    t = Canvas({})
    jester(t, top=13, s=0.9, hat=P_["dark"], flaps=P_["purple"], collar=("3a2456", "24183a"), crown=True,
           face="e8e4f0")
    for y in range(H):
        for x in range(W):
            if t.get(x, y) in "Bb" and y < 30:
                t.set(x, y, ".")
    t.outline()
    stamp(c, t)

    def crown(t2):
        t2.pal.update(c.pal)
        for x, top in ((19, 18), (24, 15), (30, 11), (36, 15), (41, 18)):
            t2.rect(x - 1, top, x + 1, 26, "M")
            t2.ellipse(x - 1, top, 1.5, 1.5, "M"), t2.ellipse(x + 1.5, top, 1.5, 1.5, "M")
            t2.rect(x + 1, top + 2, x + 1, 25, "m")
        t2.rect(16, 24, 44, 28, "M")
        t2.ellipse(15, 24.5, 2, 2, "M"), t2.ellipse(15, 28, 2, 2, "M")
        t2.ellipse(45, 24.5, 2, 2, "M"), t2.ellipse(45, 28, 2, 2, "M")
        t2.rect(16, 27, 44, 28, "m")
        t2.ellipse(30, 20, 4, 3.6, "M")
        t2.rect(28, 22, 32, 24, "M")
        t2.set(28, 20, "k"), t2.set(32, 20, "k"), t2.set(30, 22, "k")
        for x in (22, 27, 33, 38):
            t2.ellipse(x, 26, 1, 1, "Y")
    layer(c, crown)

    def pile(t3):
        t3.pal.update(c.pal)
        for x, y in ((14, 66), (44, 67), (30, 69)):
            t3.ellipse(x, y, 4, 3.5, "M")
            t3.rect(x - 2, y + 2, x + 2, y + 4, "M")
            t3.set(x - 1, y, "k"), t3.set(x + 1, y, "k"), t3.set(x - 1, y + 4, "m"), t3.set(x + 1, y + 4, "m")
        for x0, y0, x1, y1 in ((19, 70, 26, 62), (35, 62, 41, 71)):
            t3.line(x0, y0, x1, y1, "M", 2)
            t3.ellipse(x0, y0, 1.4, 1.4, "M"), t3.ellipse(x1, y1, 1.4, 1.4, "M")
    layer(c, pile)


def foolking(c):
    c.pal.update({"Q": "6e1530", "q": "9b2240", "G": "f5b82e", "g": "b8801a", "A": "6a3fa0", "a": "4a2a70",
                  "M": "f4f1ea", "k": "2b2d42", "I": "e63946"})
    background(c, "Q")
    for x in range(2, W - 2, 6):
        c.rect(x, 1, x + 2, H - 2, "q")
    c.ellipse(30, 30, 20, 26, "G")
    c.ellipse(30, 32, 17, 23, "a")
    c.rect(10, 30, 50, H - 2, "G", only="Qq")
    c.rect(13, 30, 47, H - 2, "a", only="G")
    t = Canvas({})
    jester(t, top=13, s=0.88, hat=P_["red"], flaps=P_["gold"], collar=("f4f1ea", "c9c2b0"), crown=True,
           grin=True)

    def robe(t2):
        t2.pal.update(c.pal)
        t2.poly([(17, 46), (43, 46), (50, 72), (10, 72)], "A")
        t2.poly([(30, 50), (43, 46), (50, 72), (34, 72)], "a")
        t2.rect(27, 48, 33, 72, "M")
        for x0, x1, y in ((10, 50, 70),):
            t2.rect(x0, y, x1, y + 2, "M")
        for x, y in ((29, 52), (31, 57), (29, 62), (31, 67), (14, 71), (22, 71), (38, 71), (46, 71)):
            t2.set(x, y, "k")
    layer(c, robe)
    t.outline()
    stamp(c, t)

    def cards(t3):
        t3.pal.update(c.pal)
        for x0, ch, a in ((12, "K", -0.25), (38, "Q", 0.25)):
            pts = rot_pts([(x0, 52), (x0 + 10, 52), (x0 + 10, 66), (x0, 66)], a, x0 + 5, 59)
            t3.poly(pts, "M")
            text(t3, ch, x0 + 4, 54, "I")
            suit_shape(t3, "heart" if ch == "Q" else "spade", x0 + 5, 62, 2.3, "I" if ch == "Q" else "k")
    layer(c, cards)
    for x, y in ((10, 10), (50, 12), (12, 28), (49, 26)):
        sparkle(c, x, y, "G", 1)


def skull(c):
    c.pal.update({"1": "14101e", "2": "221a32", "M": "efe9dc", "m": "b8ae9a", "k": "1a1424", "I": "e63946",
                  "W": "f4f1ea", "A": "3a3d5c", "Y": "ff6a4a"})
    background(c, "1")
    c.ellipse(30, 40, 26, 30, "2")

    import random
    rnd = random.Random(23)
    for i, (x, y) in enumerate(((14, 62), (44, 61), (17, 69), (42, 68), (24, 66), (36, 67), (30, 70))):
        a = rnd.uniform(-0.9, 0.9)
        suit = ("heart", "spade", "diamond", "club")[i % 4]

        def card(t, x=x, y=y, a=a, suit=suit, i=i):
            t.pal.update(c.pal)
            t.poly(rot_pts([(x - 4, y - 6), (x + 4, y - 6), (x + 4, y + 6), (x - 4, y + 6)], a, x, y), "W")
            suit_shape(t, suit, x, y, 2, "IA"[i % 2])
        layer(c, card)

    def head(t):
        t.pal.update(c.pal)
        t.ellipse(30, 38, 14, 13, "M")
        t.rect(22, 44, 38, 55, "M")
        t.ellipse(34, 42, 9, 10, "m", only="M")
        t.ellipse(29, 37, 11, 11, "M", only="m")
        t.ellipse(24.5, 41, 3.8, 4, "k"), t.ellipse(35.5, 41, 3.8, 4, "k")
        t.set(25, 41, "Y"), t.set(36, 41, "Y")
        t.poly([(30, 45), (32, 49), (28, 49)], "k")
        t.rect(23, 51, 37, 51, "k")
        for x in range(24, 38, 3):
            t.rect(x, 52, x, 55, "k")
        t.rect(22, 55, 38, 55, "m")
        t.line(20, 32, 23, 36, "m")
    layer(c, head)
    jester(c, cx=30, top=13, s=0.92, hat=P_["red"], flaps=P_["gold"], collar=P_["red"], hat_only=True)
    t = Canvas({})


def veto(c):
    c.pal.update({"1": "fff1c9", "2": "ffe0a0", "A": "6a3fa0", "a": "4a2a70", "M": "f4f1ea", "I": "e63946",
                  "i": "a02030", "k": "2b2d42", "G": "f5b82e"})
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            a = math.atan2(y + 0.5 - 30, x + 0.5 - 30)
            c.set(x, y, "12"[int((a + math.pi) / (2 * math.pi) * 16) % 2])

    def chip(t):
        t.pal.update(c.pal)
        t.ellipse(30, 30, 15, 15, "A")
        for k in range(8):
            a = k * math.pi / 4
            t.ellipse(30 + 13 * math.cos(a), 30 + 13 * math.sin(a), 2.2, 2.2, "M")
        t.ellipse(30, 30, 10, 10, "a")
        t.poly([(22, 24), (21, 16), (26, 22)], "M"), t.poly([(38, 24), (39, 16), (34, 22)], "M")
        t.poly([(24, 28), (29, 30), (24, 31)], "G"), t.poly([(36, 28), (31, 30), (36, 31)], "G")
        t.rect(25, 35, 35, 36, "k")
        for x in (26, 29, 32, 35):
            t.set(x, 34, "M")
    layer(c, chip)
    c.ring(30, 30, 20, 20, 4, "I")
    for k in range(-30, 31):
        u = k / 2
        for w in range(-2, 3):
            c.set(30 + u * 0.707 - w * 0.707, 30 + u * 0.707 + w * 0.707, "I")
    c.ring(30, 30, 20, 20, 1, "i")
    t = Canvas({})
    t.pal.update(c.pal)
    t.ring(30, 30, 20, 20, 4, "I")
    t.outline()
    stamp(c, t, remap=lambda ch, x, y: "k" if ch == "K" and c.get(x, y) in "12" else None)
    c.pal["k"] = "2b2d42"
    t2 = TJ("gold", "red", top=50, s=0.48, grin=True)
    stamp(c, t2)
    for x, y in ((12, 54), (48, 50), (14, 66), (46, 64)):
        sparkle(c, x, y, "G", 1)


def hoarder(c):
    c.pal.update({"1": "1e1630", "2": "2e2248", "A": "4b3a8a", "a": "2e2160", "G": "f5b82e", "Y": "f5d742",
                  "N": "b4c575", "n": "d1ddf7", "M": "f4e7c4"})
    background(c, "1")
    c.ellipse(30, 34, 24, 26, "2")
    t = TJ("gold", "purple", top=10, s=0.84, grin=True)
    stamp(c, t)

    def card(t2, x, y, a, neg):
        pts = rot_pts([(x - 5, y - 7), (x + 5, y - 7), (x + 5, y + 7), (x - 5, y + 7)], a, x, y)
        inner = rot_pts([(x - 4, y - 6), (x + 4, y - 6), (x + 4, y + 6), (x - 4, y + 6)], a, x, y)
        t2.poly(pts, "n" if neg else "G")
        t2.poly(inner, "N" if neg else "A")
        sparkle(t2, x, y, "a" if neg else "Y", 1)

    def piles(t2):
        t2.pal.update(c.pal)
        for i in range(6):
            card(t2, 15 + (i % 2), 66 - i * 4, (i % 3 - 1) * 0.15, i == 4)
        for i in range(5):
            card(t2, 45 - (i % 2), 66 - i * 4, (1 - i % 3) * 0.15, i == 2)
        for i, (x, a) in enumerate(((22, -0.5), (27, -0.2), (33, 0.2), (38, 0.5))):
            card(t2, x, 64 + abs(a) * 4, a, i == 1)
    layer(c, piles)
    for x, y in ((11, 30), (49, 22), (48, 38)):
        sparkle(c, x, y, "Y", 1)


def seer(c):
    t = Canvas({})
    jester(t, top=5, hat=P_["purple"], flaps=P_["gold"], collar=P_["purple"], crown=True)
    for y in range(H):
        for x in range(W):
            if y < 17 or (y < 20 and t.get(x, y) in "Bb"):
                t.set(x, y, ".")
    stamp(c, t)
    c.pal.update({"A": "2ec4b6", "a": "1a8a80", "I": "e63946", "Y": "f5d742", "M": "f4fbff", "D": "9b5de5",
                  "d": "6a3fa0", "G": "f5b82e", "g": "b8801a", "Q": "8fd8f0"})
    c.ellipse(30, 15, 11.5, 7, "A")
    for k in range(3):
        c.line(19 + k * 2, 18 - k * 3, 41 - k, 13 - k * 2, "a")
    c.ellipse(30, 18, 2.4, 2.4, "I")
    c.set(29, 17, "M")
    c.poly([(31, 8), (34, 0), (36, 3), (33, 9)], "Y")
    c.line(32, 8, 35, 2, "G")
    c.outline(keep=".w")
    c.ellipse(30, 59, 10, 10, "Q")
    c.ellipse(33, 62, 7.5, 7, "D", only="Q")
    c.ellipse(29, 58, 7.5, 7.5, "Q", only="D")
    for k in range(24):
        a = k * 0.45
        r = 1 + k * 0.28
        c.set(30 + r * math.cos(a), 59 + r * math.sin(a), "d")
    c.ellipse(26, 54, 2, 1.3, "M")
    c.ellipse(30, 68, 7, 2.2, "G")
    c.poly([(23, 68), (37, 68), (40, 72), (20, 72)], "G")
    c.rect(20, 71, 40, 72, "g")
    c.outline(keep=".w")
    for x, y in ((14, 52), (46, 50), (45, 66)):
        sparkle(c, x, y, "D", 1)


def scrapbook(c):
    J(c, "orange", "teal", top=2)
    c.pal.update({"A": "c0603a", "a": "8a3a20", "M": "f8f0dc", "m": "d8c8a8", "Q": "a8d8f0", "I": "e63946",
                  "Y": "f5e642", "G": "3fb97a", "q": "fdfbe8"})
    c.poly([(9, 50), (29, 52), (31, 52), (49, 50), (49, 71), (31, 72), (29, 72), (9, 71)], "A")
    c.poly([(11, 51), (29, 53), (29, 70), (11, 69)], "M")
    c.poly([(31, 53), (47, 51), (47, 69), (31, 70)], "M")
    c.rect(29, 52, 30, 72, "a")
    c.rect(13, 55, 21, 62, "Q")
    c.ellipse(17, 60, 3, 2, "G", only="Q")
    c.rect(14, 54, 17, 55, "q")
    c.rect(19, 63, 27, 68, "I")
    suit_shape(c, "heart", 23, 65.5, 2, "M")
    c.poly(rot_pts([(33, 55), (41, 55), (41, 66), (33, 66)], 0.15, 37, 60), "q")
    text(c, "A", 35, 57, "I")
    suit_shape(c, "spade", 37, 63, 2, "a")
    sparkle(c, 44, 66, "Y", 2)
    c.rect(32, 54, 35, 54, "Y")
    c.outline(keep=".w")


def daydream(c):
    c.pal.update({"M": "eef2ff", "m": "c9d0ea", "A": "9b5de5", "a": "6a3fa0", "Y": "f5d742", "G": "c9d3dc",
                  "g": "8a96a3", "I": "e63946", "k": "6a7ab0"})
    for x, y, rx, ry in ((40, 14, 9, 6), (33, 13, 5, 4), (47, 15, 4, 4), (40, 9, 5, 4), (38, 19, 6, 3)):
        c.ellipse(x, y, rx, ry, "M")
    c.ellipse(42, 18, 7, 2.5, "m", only="M")
    c.poly(rot_pts([(36, 8), (44, 8), (44, 19), (36, 19)], 0.2, 40, 13), "A")
    sparkle(c, 40, 13, "Y", 2)
    c.ellipse(34, 26, 2.4, 2, "M")
    c.ellipse(31, 31, 1.5, 1.3, "M")
    c.outline(keep=".w")
    J(c, "sky", "white", "sky", cx=24, top=22, s=0.66)
    c.set(24, 43, "E"), c.set(24, 42, "E")
    for i, (x, y) in enumerate(((11, 20), (14, 14), (11, 9))):
        n = 2 + (i > 0)
        c.rect(x, y, x + n, y, "k"), c.line(x + n, y, x, y + n, "k"), c.rect(x, y + n, x + n, y + n, "k")

    def pack(t):
        t.pal.update(c.pal)
        t.rect(14, 56, 44, 71, "G")
        t.rect(14, 56, 44, 58, "g"), t.rect(14, 69, 44, 71, "g")
        for x in range(15, 44, 2):
            t.set(x, 57, "G"), t.set(x + 1, 70, "G")
        t.ellipse(29, 64, 5, 3.5, "A")
        sparkle(t, 29, 64, "Y", 1)
    layer(c, pack, rot=-0.08, pivot=(29, 64))


def rewind(c):
    J(c, "teal", "orange", top=2)
    c.pal.update({"M": "f4f1ea", "m": "c9c2b0", "A": "3a3d5c", "I": "e63946", "D": "42aaf0", "d": "1d6fd1"})
    for k in range(70):
        a = math.radians(-60 + k * 4)
        c.ellipse(30 + 15.5 * math.cos(a), 60 + 11.5 * math.sin(a), 1.3, 1.3, "D")
    a = math.radians(-60)
    hx, hy = 30 + 15.5 * math.cos(a), 60 + 11.5 * math.sin(a)
    c.poly([(hx - 5, hy - 1), (hx + 4, hy - 3), (hx + 1, hy + 5)], "D")
    c.ellipse(30, 60, 10.5, 10.5, "M")
    c.ellipse(32, 62, 8, 8, "m", only="M")
    c.ellipse(29, 59, 8, 8, "M", only="m")
    for k in range(12):
        b = k * math.pi / 6
        c.set(30 + 8.5 * math.cos(b), 60 + 8.5 * math.sin(b), "A")
    c.line(30, 60, 30, 54, "A"), c.line(30, 60, 25, 62, "I")
    c.poly([(26, 52), (21, 55), (26, 58)], "d")
    c.poly([(31, 52), (26, 55), (31, 58)], "d") if False else None
    c.outline(keep=".w")
    for x0 in (13, 19):
        c.poly([(x0 + 5, 46), (x0, 49.5), (x0 + 5, 53)], "d")
    c.outline(keep=".w")


def float_(c):
    J(c, "pink", "sky", "pink", cx=24, top=6)
    c.pal.update({"D": "7a3a1a", "d": "5a2810", "M": "f8e8c8", "Q": "e4f4fc", "q": "b8dcf0", "I": "e63946",
                  "Y": "fff3d6", "y": "e8d0a0"})
    c.line(44, 52, 49, 34, "I", 2)
    for y in range(36, 52, 4):
        c.set(48 - (y - 36) // 4, y, "w")
    c.poly([(35, 48), (49, 48), (46, 72), (38, 72)], "Q")
    c.poly([(36, 54), (48, 54), (46, 71), (38, 71)], "D")
    c.poly([(44, 54), (48, 54), (46, 71), (43, 71)], "d")
    c.rect(36, 50, 48, 54, "M")
    c.ellipse(42, 46, 6.5, 5, "Y")
    c.ellipse(44, 48, 4, 2.5, "y", only="Y")
    c.ellipse(42, 40, 2, 2, "I")
    c.line(42, 38, 44, 35, "d")
    c.rect(36, 56, 37, 68, "q")
    c.outline(keep=".w")


CHARMS = {
    "jester": jester_card,
    "ruby": ring_card(("e63946", "ff8a8a"), "heart", "red"),
    "topaz": ring_card(("f08a24", "ffc078"), "diamond", "orange"),
    "onyx": ring_card(("2b2d42", "5b5e80"), "spade", "dark"),
    "jade": ring_card(("3fb97a", "8ae0b0"), "club", "green"),
    "twin": masks_card(2, "white", "dark", "white"),
    "triad": masks_card(3, "gold", "white", "gold"),
    "duo": masks_card(4, "red", "blue", "blue"),
    "ladder": ladder, "tide": tide, "mint": mint, "flag": flag, "glitch": glitch, "even": even,
    "odd": odd, "scribe": scribe, "well": well, "crowd": crowd, "laststand": laststand, "court": court,
    "spiral": spiral, "gold": gold, "snowball": snowball, "treasury": treasury, "hollow": hollow,
    "prism": prism, "warden": warden, "duet": duet, "seer": seer,
    "pairchips": veil_card(2, "blue", ("1d6fd1", "13478a")),
    "twopairchips": veil_card(4, "green", ("e63946", "a02030")),
    "tripschips": veil_card(3, "gold", ("3fb97a", "2a8a58")),
    "straightchips": veil_card(4, "orange", ("9b5de5", "6a3fa0"), rising=True),
    "flushchips": veil_card(3, "sky", ("f5b82e", "b8801a"), flush=True),
    "tripsx": crown_card("red", _crowns(3)),
    "quadsx": crown_card("purple", _crowns(4)),
    "straightx": crown_card("orange", _rail),
    "flushx": crown_card("blue", _flushwave),
    "grin": grin, "radio": radio, "spearhead": spearhead, "clover": clover, "rawgem": rawgem,
    "heartstone": heartstone, "portrait": portrait, "tightrope": tightrope, "fist": fist,
    "regent": regent, "moonrise": moonrise, "encore": encore, "masquerade": masquerade,
    "punchcard": punchcard, "twilight": twilight, "callingcard": callingcard, "ticket": ticket,
    "patience": patience, "corsair": corsair, "fame": fame, "commuter": commuter,
    "sprinter": sprinter, "foursquare": foursquare, "sorbet": sorbet, "kettle": kettle,
    "plantain": plantain, "ripe": ripe, "fizz": fizz, "cardshark": cardshark, "loyal": loyal,
    "slate": slate,
    "spread": spread, "hopscotch": hopscotch, "blot": blot, "mirage": mirage, "puddle": puddle,
    "mimic": mimic, "ironwill": ironwill, "quarry": quarry, "mason": mason, "midas": midas, "leech": leech,
    "rambler": rambler, "relic": relic, "keep": keep, "idol": idol, "rebate": rebate, "errand": errand,
    "trousers": trousers, "flashcard": flashcard, "monolith": monolith, "frenzy": frenzy, "dagger": dagger,
    "hologram": hologram, "starmap": starmap, "bonfire": bonfire, "maneki": maneki, "glazier": glazier,
    "iou": iou, "nestegg": nestegg, "giftwrap": giftwrap, "skyrocket": skyrocket, "ninelives": ninelives,
    "moonshot": moonshot, "satellite": satellite, "valet": valet, "bootstraps": bootstraps,
    "toreador": toreador, "wanderer": wanderer, "trader": trader, "burglar": burglar, "tipsy": tipsy,
    "juggler": juggler, "minstrel": minstrel, "merry": merry, "daredevil": daredevil, "sprout": sprout,
    "noodles": noodles, "chaos": chaos, "stargazer": stargazer, "license": license, "pennant": pennant,
    "tracing": tracing, "brainwave": brainwave, "phantom": phantom, "loaded": loaded, "crystal": crystal,
    "secondsight": secondsight, "ouija": ouija, "quantum": quantum, "diviner": diviner, "notary": notary,
    "clone": clone, "rabble": rabble, "kindling": kindling, "orbit": orbit, "blankmask": blankmask,
    "roadtrip": roadtrip, "doublevision": doublevision, "tiny": tiny, "ringmaster": ringmaster,
    "lastlaugh": lastlaugh, "wear": wear, "bonecrown": bonecrown, "foolking": foolking, "skull": skull,
    "veto": veto, "hoarder": hoarder, "scrapbook": scrapbook, "daydream": daydream, "rewind": rewind,
    "float": float_,
}

FULL_ART = {"tide", "glitch", "even", "spiral", "snowball", "hollow", "prism", "tightrope", "moonrise",
            "twilight", "slate", "mirage", "monolith", "starmap", "moonshot", "satellite", "tracing",
            "phantom", "chaos", "roadtrip", "bonecrown", "foolking", "skull", "veto", "hoarder"}

# 5x7 bold corner letters
LETTERS = {
    "C": [".###.", "##.##", "##...", "##...", "##...", "##.##", ".###."],
    "H": ["##.##", "##.##", "##.##", "#####", "##.##", "##.##", "##.##"],
    "A": [".###.", "##.##", "##.##", "#####", "##.##", "##.##", "##.##"],
    "R": ["####.", "##.##", "##.##", "####.", "##.#.", "##.##", "##.##"],
    "M": ["#...#", "##.##", "#####", "#.#.#", "#.#.#", "#...#", "#...#"],
}


def corner_word(c, light):
    """CHARM down the top-left corner, and upside down in the bottom-right."""
    col = "L" if light else "K"
    c.pal["L"] = "ffffff"
    y = 3
    for ch in "CHARM":
        for j, row in enumerate(LETTERS[ch]):
            for i, px in enumerate(row):
                if px == "#":
                    c.set(3 + i, y + j, col)
                    c.set(W - 1 - (3 + i), H - 1 - (y + j), col)
        y += 8


DARK_ART = {"glitch", "spiral", "hollow", "prism", "moonrise", "twilight", "slate", "monolith", "starmap",
            "moonshot", "satellite", "phantom", "bonecrown", "foolking", "skull", "hoarder"}


def build(cid):
    c = Canvas({})
    if cid not in FULL_ART:
        background(c, "w")
    CHARMS[cid](c)
    corner_word(c, cid in DARK_ART)
    card_edge(c)
    rows = c.rows()
    used = set("".join(rows)) - {"."}
    pal = {}
    for ch in sorted(used):
        assert ch in c.pal, (cid, ch)
        pal[ch] = c.pal[ch]
    return rows, pal


def write_gd(path):
    out = [
        "class_name CharmArt",
        "extends RefCounted",
        "",
        "## Generated by tools/make_charms.py - edit that, not this file.",
        "## Charm cards, %d x %d: rows of palette letters and each card's palette." % (W, H),
        "## FULL_ART cards paint their own background behind the corner word.",
        "",
        "const FULL_ART := %s" % str(sorted(FULL_ART)).replace("'", '"'),
        "",
        "const CARDS := {",
    ]
    for cid in CHARMS:
        rows, pal = build(cid)
        out.append('\t"%s": {' % cid)
        out.append('\t\t"pal": {%s},' % ", ".join('"%s": "%s"' % (k, v) for k, v in pal.items()))
        out.append('\t\t"rows": [')
        for r in rows:
            out.append('\t\t\t"%s",' % r)
        out.append("\t\t],")
        out.append("\t},")
    out.append("}")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")


def preview(path):
    from PIL import Image
    ids = list(CHARMS)
    cols = 10
    sheet = Image.new("RGB", (cols * (W + 4), ((len(ids) + cols - 1) // cols) * (H + 4)), (27, 77, 62))
    for i, cid in enumerate(ids):
        rows, pal = build(cid)
        img = Image.new("RGB", (W, H), (27, 77, 62))
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch != ".":
                    img.putpixel((x, y), tuple(int(pal[ch][k:k + 2], 16) for k in (0, 2, 4)))
        sheet.paste(img, ((i % cols) * (W + 4) + 2, (i // cols) * (H + 4) + 2))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(path)


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    write_gd(os.path.join(root, "scripts", "charm_art.gd"))
    if len(sys.argv) > 1:
        preview(sys.argv[1])
