"""Act 4 — Eo and the Lie, Vox editorial style. Narration clips 8-10 (act-local 0.0-50.3s)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageEnhance
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vox import *

S4 = os.path.join(SCR, 'act4', 'src')


def cut(path, h, **k):
    return Cutout(Image.open(path).convert('RGBA'), h, **k)


DARROW = cut(os.path.join(A3, 'C01A_standing.png'), 860)
EO = cut(os.path.join(S4, 'eo.png'), 800)
EO_HEAD = cut(os.path.join(S4, 'eo_head.png'), 760)
GRIEF = cut(os.path.join(A3, 'C01D_grief.png'), 760)
SONS = cut(os.path.join(S4, 'sons.png'), 940)
GOLD = cut(os.path.join(A3, 'C02A_standing.png'), 940)
FG = foreground()

SQUARE = Image.open(os.path.join(B3, 'E11.png'))
CARD_SQUARE = PhotoCard(SQUARE, 1150, rot=-1.5, seed=81)
CARD_SQUARE_GREY = PhotoCard(ImageEnhance.Color(SQUARE).enhance(0.0), 1150, rot=-1.5, seed=81)
CARD_CITY = PhotoCard(Image.open(os.path.join(B2, 'E04A.png')), 900, rot=2, seed=83)
CARD_SHOP = PhotoCard(Image.open(os.path.join(B2, 'E05.png')), 860, rot=-2.5, seed=85)
CARD_EYE = PhotoCard(Image.open(os.path.join(A3, 'C02D_eye.png')), 1250, rot=1.5, seed=87)


def sA(t, D):
    """Darrow accepts this life: sixteen, newly married to Eo, proud of his skill."""
    c = background()
    DARROW.place(c, 640, H + 40, t, 0.0, side='left')
    EO.place(c, 1280, H + 40, t, 0.5, side='right')
    headline(c, (W / 2, 120), 'DARROW & EO', 96, t, 1.0)
    typewriter(c, (W / 2, 205), 'sixteen, and newly married', 40, t, 1.8, anchor='mm', cursor=False)
    c.alpha_composite(FG)
    return c


def sB(t, D):
    """Eo dreams of more: better to die free than to live in chains."""
    c = background()
    EO_HEAD.place(c, 500, H + 20, t, 0.0, side='left')
    lines = [('"Better to die', 0.8), ('free', 1.6), ('than to live', 2.2), ('in chains."', 2.9)]
    for i, (ln, t0) in enumerate(lines):
        col = RED if ln == 'free' else INK
        headline(c, (1300, 300 + i * 150), ln.upper(), 110, t, t0, fill=col)
    return c


def sC(t, D):
    """She sings a forbidden song of mourning before the authorities, and is executed for it.
    Shown only through the empty square draining of colour: no violence on screen."""
    c = background()
    k = ease((t - 3.4) / 1.2)
    card = CARD_SQUARE if k < 0.5 else CARD_SQUARE_GREY
    card.place(c, W / 2, 560, t, 0.0, zoom=lerp(1.0, 1.08, ease(t / D)))
    typewriter(c, (W / 2, 95), 'a forbidden song of mourning', 46, t, 0.6, anchor='mm', cursor=False)
    if t > 4.2:
        headline(c, (W / 2, 1015), 'EXECUTED', 80, t, 4.4, fill=RED)
    return c


def sD(t, D):
    """Driven by grief."""
    c = background()
    GRIEF.place(c, W / 2, H + 30, t, 0.0, side='right')
    typewriter(c, (W / 2, 140), 'DRIVEN BY GRIEF', 56, t, 0.6, anchor='mm', cursor=False)
    c.alpha_composite(FG)
    return c


RECORD = document(620, 520, ['', 'Surface of Mars:', 'UNINHABITABLE', '', 'Keep digging.', '---'], seed=88,
                  title='OFFICIAL RECORD', title_size=46, body_size=36, typed=True)


def sE(t, D):
    """The truth: the surface was settled long ago, and his people were lied to for generations."""
    c = background()
    headline(c, (560, 120), 'THE TRUTH', 96, t, 0.0)
    CARD_CITY.place(c, 560, 600, t, 0.4, zoom=lerp(1.0, 1.1, ease(t / D)))
    typewriter(c, (560, 1000), 'cities under open skies', 36, t, 1.6, anchor='mm', cursor=False)
    pos = place_sheet(c, RECORD, 1500, 540, t, 3.2, rot=3)
    if pos:
        x0, y0 = pos
        strike(c, x0 + 50, x0 + 420, y0 + 290, ease((t - 4.6) / 0.5), width=12)
        stamp(c, 1520, 820, 'A LIE', 80, t, 5.2, ang=-10)
    return c


def sF(t, D):
    """The Sons of Ares offer a terrible bargain."""
    c = background()
    SONS.place(c, 1200, H + 40, t, 0.0, side='right')
    headline(c, (560, 430), 'THE SONS', 120, t, 0.7)
    headline(c, (560, 560), 'OF ARES', 120, t, 0.95, fill=RED)
    typewriter(c, (560, 680), 'a terrible bargain', 42, t, 1.8, anchor='mm', cursor=False)
    c.alpha_composite(FG)
    return c


STEPS = [('eyes dyed gold', 2.4), ('bones strengthened', 3.6), ('hands reshaped', 4.8)]
CHECK = document(620, 560, [], seed=90, title='THE CARVING', title_size=48)


def sG(t, D):
    """A secret workshop: a sculptor of flesh rebuilds him bone by bone."""
    c = background()
    CARD_SHOP.place(c, 620, 560, t, 0.0, zoom=lerp(1.0, 1.08, ease(t / D)))
    typewriter(c, (620, 1000), 'a secret workshop', 38, t, 0.8, anchor='mm', cursor=False)
    pos = place_sheet(c, CHECK, 1430, 540, t, 1.4, rot=-2)
    if pos:
        x0, y0 = pos
        d = ImageDraw.Draw(c)
        for i, (step, t0) in enumerate(STEPS):
            y = y0 + 230 + i * 100
            d.rectangle((x0 + 60, y - 22, x0 + 104, y + 22), outline=INK + (255,), width=4)
            text(c, (x0 + 130, y), step, F_TYPE(38), anchor='lm', alpha=ease((t - 1.8) / 0.4))
            marker_line(c, [(x0 + 62, y), (x0 + 80, y + 20), (x0 + 112, y - 30)], ease((t - t0) / 0.3), width=9)
    return c


def sH(t, D):
    """His eyes turn gold; he learns his enemies' manners until he can pass as one of them."""
    c = background()
    if t < 3.4:
        CARD_EYE.place(c, W / 2, 540, t, 0.0, zoom=lerp(1.0, 1.08, ease(t / 3.4)))
        typewriter(c, (W / 2, 1010), 'manners, speech, history', 38, t, 1.0, anchor='mm', cursor=False)
    else:
        GOLD.place(c, 1250, H + 40, t, 3.4, side='right')
        headline(c, (600, 470), 'ONE OF', 130, t, 3.9)
        headline(c, (600, 610), 'THEM', 160, t, 4.15, fill=RED)
        c.alpha_composite(FG)
    return c


SHOTS = [(0.0, sA), (6.5, sB), (12.5, sC), (18.9, sD), (22.5, sE), (30.6, sF), (35.5, sG), (43.0, sH)]
END = 50.3


def frame(t):
    return make_frame(SHOTS, END, t)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    elif mode == 'video':
        render_video(frame, END, (8, 9, 10), sys.argv[2], os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a4'))
