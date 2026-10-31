"""Act 3 — A World Ruled by Color, Vox editorial style. Narration clips 6-7 (act-local 0.0-39.2s)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vox import *

S3 = os.path.join(SCR, 'act3', 'src')
HAND = Image.open(os.path.join(A3, 'C01E_hand.png'))
CITY = Image.open(os.path.join(B2, 'E04A.png'))

DARROW = Cutout(Image.open(os.path.join(A3, 'C01A_standing.png')).convert('RGBA'), 900)
CARD_HAND = PhotoCard(HAND, 820, rot=-2.5, seed=61)
CARD_CITY = PhotoCard(CITY, 700, rot=3, seed=62)
FG = foreground()

CASTES = [('gold', 'GOLD', 'rulers & warriors', (196, 154, 69)),
          ('silver', 'SILVER', 'money', (168, 170, 174)),
          ('copper', 'COPPER', 'bureaucracy', (184, 115, 51)),
          ('blue', 'BLUE', 'pilots', (62, 92, 142)),
          ('obsidian', 'OBSIDIAN', 'soldiers', (44, 42, 44)),
          ('pink', 'PINK', 'pleasure', (220, 150, 160)),
          ('brown', 'BROWN', 'servants', (120, 84, 56)),
          ('red', 'RED', 'miners', (180, 60, 40))]


def small_cutout(name, h):
    return Cutout(Image.open(os.path.join(S3, name + '.png')).convert('RGBA'), h, stroke_x=10, stroke_y=4)


FIG = {n: small_cutout(n, 222 if n == 'obsidian' else 182) for n, *_ in CASTES}


def sA(t, D):
    """He wrote Red Rising: the story of a Red, a slave of the lowest caste."""
    c = background()
    DARROW.place(c, 560, H + 40, t, 0.0, side='left')
    headline(c, (1300, 430), 'A RED', 200, t, 0.9, fill=RED)
    typewriter(c, (1300, 580), 'a slave of the lowest caste', 44, t, 1.8, anchor='mm', cursor=False)
    c.alpha_composite(FG)
    return c


def sB(t, D):
    """Who believes he is building a future for humanity."""
    c = background()
    CARD_HAND.place(c, 600, 560, t, 0.0, zoom=lerp(1.0, 1.06, ease(t / D)))
    CARD_CITY.place(c, 1450, 470, t, 1.2)
    arrow = [(1010, 640), (1120, 690), (1230, 650)]
    marker_line(c, arrow, ease((t - 1.0) / 0.6), width=10)
    if t > 1.6:
        marker_line(c, [(1195, 620), (1232, 650), (1190, 682)], ease((t - 1.6) / 0.3), width=10)
    typewriter(c, (1450, 840), 'a future for humanity', 40, t, 2.0, anchor='mm', cursor=False)
    return c


def chip(color, name, seed):
    w_, h_ = 170, 250
    card = Image.new('RGBA', (w_, h_), (245, 241, 230, 255))
    d = ImageDraw.Draw(card)
    d.rectangle((14, 14, w_ - 14, 170), fill=color + (255,))
    d.text((w_ / 2, 210), name, font=F_HEAD(24), fill=INK + (255,), anchor='mm')
    card.putalpha(torn_mask(w_, h_, seed, amp=3, step=12))
    return card


CHIPS = [chip(col, nm, 70 + i) for i, (_, nm, _, col) in enumerate(CASTES)]


def sC(t, D):
    """A world ruled by color: caste is marked by eyes and hair, each bred for one purpose."""
    c = background()
    headline(c, (W / 2, 140), 'RULED BY COLOR', 110, t, 0.0)
    for i, ch in enumerate(CHIPS):
        x = 260 + i * 200
        place_sheet(c, ch, x, 520, t, 0.5 + i * 0.18, rot=((i * 37) % 7 - 3) * 1.2)
    typewriter(c, (W / 2, 790), 'born into a caste, marked by eyes and hair', 40, t, 2.6, anchor='mm', cursor=False)
    typewriter(c, (W / 2, 880), 'bred for a single purpose', 46, t, 4.6, anchor='mm', fill=RED, cursor=False)
    return c


ROWS = [(290, ['gold']), (480, ['silver', 'copper']), (670, ['blue', 'obsidian']), (860, ['pink', 'brown']), (1050, ['red'] * 6)]
APPEAR = {'gold': 0.2, 'silver': 3.4, 'copper': 5.0, 'blue': 6.8, 'obsidian': 8.8, 'pink': 11.0, 'brown': 13.0, 'red': 15.0}
INFO = {n: (nm, role) for n, nm, role, _ in CASTES}


def strip_img(w_, seed):
    s = Image.new('RGBA', (w_, 44), (245, 241, 230, 255))
    s.putalpha(torn_mask(w_, 44, seed, amp=4, step=12))
    return s


STRIPS = [strip_img(300 + 340 * i, 90 + i) for i in range(len(ROWS))]


def sD(t, D):
    """The caste pyramid, built from the top down as each color is named."""
    c = background()
    for i, (base, members) in enumerate(ROWS):
        first = min(APPEAR[m] for m in members) - 0.25
        place_sheet(c, STRIPS[i], W / 2, base - 22, t, first, rise=160)
        n = len(members)
        width = STRIPS[i].width
        for j, m in enumerate(members):
            cx = W / 2 - width / 2 + width * (j + 0.5) / n
            if m == 'red':
                cx = W / 2 - width / 2 + 300 + j * (width - 600) / (n - 1)
                cx += 0 if j < n / 2 else 0
            start = APPEAR[m] + (0.18 * j if m == 'red' else 0.0)
            FIG[m].place(c, cx, base - 30, t, start, rise=260, side='left')
            nm, role = INFO[m]
            label = None
            if m == 'red':
                if j == 0:
                    label = (W / 2, base - 22, 'mm')
            elif n == 1:
                label = (W / 2 + width / 2 + 24, base - 22, 'lm')
            elif j == 0:
                label = (W / 2 - width / 2 - 24, base - 22, 'rm')
            else:
                label = (W / 2 + width / 2 + 24, base - 22, 'lm')
            if label:
                lx, ly, an = label
                dy, op = arrive(t, start + 0.3, 60)
                if op > 0:
                    f1, f2 = F_HEAD(30), F_TYPE(26)
                    d_ = ImageDraw.Draw(c)
                    w1 = d_.textlength(nm, font=f1); w2 = d_.textlength(role, font=f2)
                    tot = w1 + 12 + w2
                    x0 = lx if an == 'lm' else (lx - tot if an == 'rm' else lx - tot / 2)
                    if m == 'red':
                        text(c, (x0 - 4, ly + dy), '', f1, anchor='lm')
                    text(c, (x0, ly + dy), nm, f1, anchor='lm', alpha=op)
                    text(c, (x0 + w1 + 12, ly + dy), role, f2, anchor='lm', alpha=op)
    if t > 17.5:
        marker_circle(c, W / 2, 975, 700, 100, ease((t - 17.5) / 0.9), width=10, seed=6)
    typewriter(c, (1190, 150), '"Your work will make', 34, t, 18.4, cursor=False)
    typewriter(c, (1190, 200), ' Mars livable."', 34, t, 19.3, cursor=False)
    headline(c, (360, 150), 'THE SOCIETY', 70, t, 0.0)
    return c


SHOTS = [(0.0, sA), (5.6, sB), (10.3, sC), (17.6, sD)]
END = 39.2


def frame(t):
    return make_frame(SHOTS, END, t)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    elif mode == 'video':
        render_video(frame, END, (6, 7), sys.argv[2], os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a3'))
