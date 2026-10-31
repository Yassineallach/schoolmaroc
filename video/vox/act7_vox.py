"""Act 7 — Allies and Enemies, Vox editorial style. Narration clips 17-20 (act-local 0.0-67.9s)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vox import *

S7 = os.path.join(SCR, 'act7', 'src')


def cut(path, h, **k):
    return Cutout(Image.open(path).convert('RGBA'), h, **k)


SEVRO = cut(os.path.join(S7, 'sevro.png'), 720)
CASSIUS = cut(os.path.join(S7, 'cassius.png'), 940)
MUSTANG_HORSE = cut(os.path.join(S7, 'mustang_horse.png'), 860)
MUSTANG = cut(os.path.join(S7, 'mustang.png'), 900)
JACKAL = cut(os.path.join(S7, 'jackal.png'), 940)
JACKAL_HEAD = cut(os.path.join(S7, 'jackal_head.png'), 820)
GOLD_D = cut(os.path.join(A3, 'C02A_standing.png'), 900)
FG = foreground()

CARD_FEAST = PhotoCard(Image.open(os.path.join(B3, 'E08B.png')), 1000, rot=2, seed=141)
CARD_GRAVE = PhotoCard(Image.open(os.path.join(B3, 'E09B.png')), 1150, rot=-1.5, seed=143)


def sA(t, D):
    """Early on, Darrow is joined by a ferocious, loyal Gold named Sevro."""
    c = background()
    hop = 40 * math.sin(min(t, 1.2) / 1.2 * math.pi)
    SEVRO.place(c, 620, 900 - hop, t, 0.0, side='left')
    headline(c, (1340, 420), 'SEVRO', 200, t, 0.7)
    typewriter(c, (1340, 560), 'ferocious and loyal', 46, t, 1.4, anchor='mm', cursor=False)
    return c


def sB(t, D):
    """A wild outcast who prefers howling with wolves to dining with nobles."""
    c = background()
    SEVRO.place(c, 1440, 860, t, -1.0, side='right')
    headline(c, (680, 380), 'WOLVES', 150, t, 0.2)
    headline(c, (680, 530), 'OVER', 90, t, 0.6, fill=GREY)
    headline(c, (680, 680), 'NOBLES', 150, t, 1.0)
    wpx = ImageDraw.Draw(c).textlength('NOBLES', font=F_HEAD(150))
    strike(c, 680 - wpx / 2 - 20, 680 + wpx / 2 + 20, 685, ease((t - 1.8) / 0.4), width=16)
    return c


def sC(t, D):
    """A close bond with Cassius, a charming young Gold whose honor will make him Darrow's fiercest rival."""
    c = background()
    CASSIUS.place(c, 560, H + 40, t, 0.0, side='left')
    headline(c, (1320, 340), 'CASSIUS', 170, t, 0.6)
    typewriter(c, (1320, 470), 'charming, honorable', 44, t, 1.3, anchor='mm', cursor=False)
    if t > 4.0:
        headline(c, (1320, 640), 'FRIEND', 110, t, 4.0)
    if t > 6.0:
        wpx = ImageDraw.Draw(c).textlength('FRIEND', font=F_HEAD(110))
        strike(c, 1320 - wpx / 2 - 20, 1320 + wpx / 2 + 20, 645, ease((t - 6.0) / 0.4), width=14)
        headline(c, (1320, 800), 'RIVAL', 130, t, 6.5, fill=RED)
    c.alpha_composite(FG)
    return c


def sD(t, D):
    """Later he meets Mustang, a Gold as clever as she is compassionate."""
    c = background()
    MUSTANG_HORSE.place(c, 520, H + 40, t, 0.0, side='left')
    headline(c, (1380, 400), 'MUSTANG', 150, t, 0.6, fill=RED)
    typewriter(c, (1340, 530), 'clever', 50, t, 1.4, anchor='mm', cursor=False)
    typewriter(c, (1340, 610), 'compassionate', 50, t, 2.2, anchor='mm', cursor=False)
    c.alpha_composite(FG)
    return c


def sE(t, D):
    """One of the most powerful families on Mars, yet she questions the cruelty of her own caste."""
    c = background()
    CARD_FEAST.place(c, 640, 500, t, 0.0, zoom=lerp(1.0, 1.06, ease(t / D)))
    typewriter(c, (640, 990), 'one of the most powerful families on Mars', 34, t, 0.6, anchor='mm', cursor=False)
    MUSTANG.place(c, 1520, H + 40, t, 1.4, side='right')
    c.alpha_composite(FG)
    headline(c, (640, 1010), '', 10, t, 0)
    return c


def sF(t, D):
    """Darrow and Mustang are a study in opposites: one burning for revenge, the other searching for a better way."""
    c = background()
    d = ImageDraw.Draw(c)
    p = ease((t - 0.6) / 0.6)
    if p > 0:
        d.line((W / 2, 140, W / 2, 140 + 780 * p), fill=INK + (255,), width=5)
    GOLD_D.place(c, 470, H + 40, t, 0.0, side='left')
    MUSTANG.place(c, 1450, H + 40, t, 0.3, side='right')
    c.alpha_composite(FG)
    headline(c, (470, 990), 'REVENGE', 80, t, 1.6, fill=RED)
    headline(c, (1450, 990), 'A BETTER WAY', 70, t, 3.6)
    return c


def sG(t, D):
    """Their bond forces Darrow to question whether every Gold is truly his enemy."""
    c = background()
    lines = [('IS EVERY GOLD', 0.2), ('HIS ENEMY?', 0.9)]
    for i, (ln, t0) in enumerate(lines):
        headline(c, (W / 2, 420 + i * 180), ln, 150, t, t0, fill=RED if i == 1 else INK)
    return c


def sH(t, D):
    """If his enemies can love, grieve, and sacrifice, the war is more complicated than he imagined."""
    c = background()
    CARD_GRAVE.place(c, W / 2, 470, t, 0.0, zoom=lerp(1.0, 1.06, ease(t / D)))
    for i, (w_, t0) in enumerate([('LOVE', 0.8), ('GRIEVE', 1.6), ('SACRIFICE', 2.4)]):
        headline(c, (W / 2 - 520 + i * 520, 960), w_, 80, t, t0, fill=RED if i == 2 else INK)
    return c


def sI(t, D):
    """Meanwhile, a darker figure rises: Mustang's brother, the Jackal."""
    c = background()
    JACKAL.place(c, 1300, H + 40, t, 0.0, side='right')
    typewriter(c, (560, 360), "Mustang's brother", 44, t, 0.8, anchor='mm', cursor=False)
    headline(c, (560, 500), 'THE', 110, t, 1.6)
    headline(c, (560, 650), 'JACKAL', 170, t, 1.9, fill=RED)
    c.alpha_composite(FG)
    return c


TRAITS = [('brilliant', 0.4), ('patient', 1.1), ('utterly without mercy', 1.8)]


def sJ(t, D):
    """Brilliant, patient, and utterly without mercy."""
    c = background()
    JACKAL_HEAD.place(c, 560, H + 20, t, 0.0, side='left')
    for i, (w_, t0) in enumerate(TRAITS):
        typewriter(c, (1060, 380 + i * 120), w_, 60, t, t0, fill=RED if i == 2 else INK, cursor=False)
    return c


def sK(t, D):
    """Where Darrow fights for a cause, the Jackal fights only for himself."""
    c = background()
    d = ImageDraw.Draw(c)
    p = ease((t - 0.3) / 0.5)
    if p > 0:
        d.line((W / 2, 140, W / 2, 140 + 780 * p), fill=INK + (255,), width=5)
    GOLD_D.place(c, 470, H + 40, t, 0.0, side='left')
    JACKAL.place(c, 1450, H + 40, t, 0.3, side='right')
    c.alpha_composite(FG)
    headline(c, (470, 990), 'A CAUSE', 80, t, 1.0)
    headline(c, (1450, 990), 'HIMSELF', 80, t, 2.2, fill=RED)
    return c


def sL(t, D):
    """One of the most unsettling villains in modern science fiction."""
    c = background()
    JACKAL_HEAD.place(c, W / 2, H + 20, t, 0.0, side='right')
    typewriter(c, (W / 2, 150), 'ONE OF THE MOST UNSETTLING VILLAINS', 54, t, 0.6, anchor='mm', fill=RED, cursor=False)
    typewriter(c, (W / 2, 225), 'in modern science fiction', 40, t, 2.4, anchor='mm', cursor=False)
    return c


SHOTS = [(0.0, sA), (5.0, sB), (10.2, sC), (20.5, sD), (25.4, sE), (31.2, sF), (38.6, sG), (44.0, sH),
         (50.9, sI), (55.8, sJ), (59.3, sK), (63.6, sL)]
END = 67.9


def frame(t):
    return make_frame(SHOTS, END, t)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    elif mode == 'video':
        render_video(frame, END, (17, 18, 19, 20), sys.argv[2], os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a7'))
