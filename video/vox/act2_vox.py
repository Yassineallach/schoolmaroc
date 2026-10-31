"""Act 2 — The Author, Vox editorial style. Narration clips 4-5 (act-local 0.0-44.6s)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vox import *

PORTRAIT = Image.open(os.path.join(A3, 'P02_portrait.png'))
P01 = Image.open(os.path.join(A3, 'P01_v2.png'))
E10 = Image.open(os.path.join(B3, 'E10.png'))
E09A = Image.open(os.path.join(B3, 'E09A.png'))

CARD_PORTRAIT = PhotoCard(PORTRAIT, 560, rot=-2.5, seed=31)
CARD_CLOSING = PhotoCard(P01, 620, rot=2, seed=33, crop=(860, 110, 1536, 1000))
CARD_DESK = PhotoCard(P01, 600, rot=-3, seed=32, crop=(30, 30, 840, 960))
CARD_FLEET = PhotoCard(E10, 1080, rot=-1.5, seed=35)
CARD_WAR = PhotoCard(E09A, 1320, rot=1.2, seed=37)


def sA(t, D):
    """His creator, Pierce Brown."""
    c = background()
    CARD_PORTRAIT.place(c, 470, 560, t, 0.0, zoom=lerp(1.0, 1.05, ease(t / D)))
    headline(c, (1300, 470), 'PIERCE BROWN', 96, t, 0.8)
    marker_line(c, [(1000, 545), (1300, 538), (1600, 548)], ease((t - 1.4) / 0.7), width=12)
    typewriter(c, (1300, 620), 'the author of Red Rising', 40, t, 2.0, anchor='mm', cursor=False)
    return c


RESUME = [('Odd jobs in television', 0.6), ('Odd jobs in politics', 1.6), ('Writing novels', 2.6)]


def sB(t, D):
    """His early twenties: odd jobs, and writing novels no one would publish."""
    c = background()
    CARD_DESK.place(c, 1440, 560, t, 0.3)
    sheet = document(820, 640, [], seed=41, title='HIS EARLY TWENTIES', title_size=48)
    pos = place_sheet(c, sheet, 620, 540, t, 0.0, rot=-1.5)
    if pos:
        x0, y0 = pos
        for i, (line, t0) in enumerate(RESUME):
            typewriter(c, (x0 + 80, y0 + 230 + i * 110), line, 40, t, t0, cps=26)
        strike(c, x0 + 70, x0 + 600, y0 + 230, ease((t - 4.0) / 0.5))
        strike(c, x0 + 70, x0 + 540, y0 + 340, ease((t - 4.5) / 0.5))
    return c


def sC(t, D):
    """Rejection followed rejection."""
    c = background()
    headline(c, (W / 2, 110), 'REJECTED', 96, t, 2.6, fill=RED)
    for i in range(6):
        t0 = i * 0.55
        sheet = document(520, 660, ['Dear Mr. Brown,', '', '---', '---', '---', '---', '', 'Regrettably...'], seed=50 + i, body_size=30)
        x = W / 2 + ((i * 53) % 7 - 3) * 60
        y = 600 + ((i * 31) % 5 - 2) * 18
        rot = ((i * 37) % 11 - 5) * 1.4
        if place_sheet(c, sheet, x, y, t, t0, rot=rot):
            stamp(c, x + 40, y + 120, 'REJECTED', 54, t, t0 + 0.35, ang=-12 + i * 3)
    return c


def sD(t, D):
    """2014: his breakthrough, an epic rebellion set among the stars."""
    c = background()
    CARD_FLEET.place(c, 1240, 560, t, 0.5, zoom=lerp(1.0, 1.12, ease(t / D)), pan=(0.5, 0.55))
    headline(c, (330, 470), '2014', 150, t, 0.0, fill=RED)
    typewriter(c, (330, 580), 'THE BREAKTHROUGH', 36, t, 0.8, anchor='mm', cursor=False)
    typewriter(c, (1240, 1015), 'an epic rebellion set among the stars', 38, t, 2.0, anchor='mm', cursor=False)
    return c


SPINES = [(150, 84, 58), (96, 104, 112), (70, 70, 74), (120, 112, 100), (176, 150, 100), (140, 70, 64), (200, 196, 186)]


def make_shelf():
    Wd = 3000
    img = Image.new('RGBA', (Wd, 760), (0, 0, 0, 0))
    r = np.random.default_rng(12)
    d = ImageDraw.Draw(img)
    for row, base in enumerate((330, 700)):
        x = 40
        while x < Wd - 100:
            w_, h_ = int(r.integers(46, 90)), int(r.integers(220, 300))
            col = SPINES[int(r.integers(len(SPINES)))]
            d.rectangle((x, base - h_, x + w_, base), fill=col + (255,), outline=INK + (255,), width=2)
            d.line((x + 6, base - h_ * 0.85, x + w_ - 6, base - h_ * 0.85), fill=INK + (120,), width=2)
            x += w_ + int(r.integers(2, 7))
        d.rectangle((0, base, Wd, base + 26), fill=INK + (255,))
    return img


SHELF = make_shelf()


def sE(t, D):
    """Young adult dystopias crowded bookstore shelves."""
    c = background()
    x = lerp(0, SHELF.width - W, ease(t / D))
    dy, op = arrive(t, 0.0, 380)
    c.alpha_composite(alpha_mul(SHELF.crop((int(x), 0, int(x) + W, 760)), op), (0, int(240 + dy)))
    headline(c, (W / 2, 120), 'YOUNG ADULT DYSTOPIAS', 84, t, 0.6)
    return c


TROPES = [('ARENAS', 0.2), ('WALLED CITIES', 1.6), ('CRUEL GOVERNMENTS', 3.0)]


def sF(t, D):
    """Arenas, walled cities, cruel governments, and stories that felt too safe."""
    c = background()
    for i, (word, t0) in enumerate(TROPES):
        y = 330 + i * 190
        headline(c, (W / 2, y), word, 110, t, t0)
    for i, (word, t0) in enumerate(TROPES):
        y = 330 + i * 190
        wpx = ImageDraw.Draw(c).textlength(word, font=F_HEAD(110))
        strike(c, W / 2 - wpx / 2 - 20, W / 2 + wpx / 2 + 20, y + 6, ease((t - 4.6 - i * 0.2) / 0.4), width=14)
    stamp(c, 1560, 930, 'TOO SAFE', 70, t, 5.4, ang=-9)
    return c


def sG(t, D):
    """While Brown was a fan, he was weary of stories that felt too safe."""
    c = background()
    CARD_CLOSING.place(c, 520, 560, t, 0.0, zoom=lerp(1.04, 1.0, ease(t / D)))
    headline(c, (1340, 470), 'A FAN,', 110, t, 0.6)
    headline(c, (1340, 600), 'BUT WEARY', 110, t, 1.1, fill=RED)
    return c


def sH(t, D):
    """He wanted war to feel like war, and power to feel truly dangerous."""
    c = background()
    CARD_WAR.place(c, W / 2, 560, t, 0.0, zoom=lerp(1.0, 1.1, ease(t / D)), pan=(0.5, 0.6))
    typewriter(c, (W / 2, 100), 'WAR SHOULD FEEL LIKE WAR', 54, t, 0.8, anchor='mm', fill=RED, cursor=False)
    return c


SHOTS = [(0.0, sA), (6.3, sB), (13.3, sC), (18.8, sD), (23.8, sE), (28.1, sF), (34.3, sG), (39.3, sH)]
END = 44.6


def frame(t):
    return make_frame(SHOTS, END, t)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    elif mode == 'video':
        render_video(frame, END, (4, 5), sys.argv[2], os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a2'))
