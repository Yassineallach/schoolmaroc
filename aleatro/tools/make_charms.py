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


def crown(c):
    jester(c, hat=P_["red"], flaps=P_["gold"], collar=("9b2240", "6e1530"), crown=True)


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
    "prism": prism, "warden": warden, "duet": duet, "crown": crown,
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
}

FULL_ART = {"tide", "glitch", "even", "spiral", "snowball", "hollow", "prism", "tightrope", "moonrise",
            "twilight", "slate"}

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


DARK_ART = {"glitch", "spiral", "hollow", "prism", "moonrise", "twilight", "slate"}


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
