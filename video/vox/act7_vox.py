"""Act 7 — Allies and Enemies, Vox editorial style. Narration clips 17-20 (act-local 0.0-67.9s)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vox import *

S7 = os.path.join(SCR, 'act7', 'src')


cue = make_cue((17, 18, 19, 20))


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
    ts = w(cue(17, 'darrow is joined'))
    hop = 40 * math.sin(min(max(t - ts, 0), 1.2) / 1.2 * math.pi)
    SEVRO.place(c, 620, 900 - hop, t, ts, side='left')
    headline(c, (1340, 420), 'SEVRO', 200, t, w(cue(17, 'sevro')))
    typewriter(c, (1340, 560), 'ferocious and loyal', 46, t, w(cue(17, 'ferocious')), anchor='mm', cursor=False)
    return c


def sB(t, D):
    """A wild outcast who prefers howling with wolves to dining with nobles."""
    c = background()
    SEVRO.place(c, 1440, 860, t, -1.0, side='right')
    headline(c, (680, 380), 'WOLVES', 150, t, w(cue(17, 'wolves')))
    headline(c, (680, 530), 'OVER', 90, t, w(cue(17, 'to dining')), fill=GREY)
    headline(c, (680, 680), 'NOBLES', 150, t, w(cue(17, 'nobles')))
    wpx = ImageDraw.Draw(c).textlength('NOBLES', font=F_HEAD(150))
    strike(c, 680 - wpx / 2 - 20, 680 + wpx / 2 + 20, 685, ease((t - w(cue(17, 'nobles')) - 0.5) / 0.4), width=16)
    return c


def sC(t, D):
    """A close bond with Cassius, a charming young Gold whose honor will make him Darrow's fiercest rival."""
    c = background()
    CASSIUS.place(c, 560, H + 40, t, 0.0, side='left')
    headline(c, (1320, 340), 'CASSIUS', 170, t, w(cue(17, 'cassius')))
    typewriter(c, (1320, 470), 'charming, honorable', 44, t, w(cue(17, 'charming')), anchor='mm', cursor=False)
    if t > w(cue(17, 'whose sense')):
        headline(c, (1320, 640), 'FRIEND', 110, t, w(cue(17, 'whose sense')))
    if t > w(cue(17, 'turn him')):
        wpx = ImageDraw.Draw(c).textlength('FRIEND', font=F_HEAD(110))
        strike(c, 1320 - wpx / 2 - 20, 1320 + wpx / 2 + 20, 645, ease((t - w(cue(17, 'turn him'))) / 0.4), width=14)
        headline(c, (1320, 800), 'RIVAL', 130, t, w(cue(17, 'rival')), fill=RED)
    c.alpha_composite(FG)
    return c


def sD(t, D):
    """Later he meets Mustang, a Gold as clever as she is compassionate."""
    c = background()
    MUSTANG_HORSE.place(c, 520, H + 40, t, 0.0, side='left')
    headline(c, (1380, 400), 'MUSTANG', 150, t, w(cue(18, 'mustang')), fill=RED)
    typewriter(c, (1340, 530), 'clever', 50, t, w(cue(18, 'clever')), anchor='mm', cursor=False)
    typewriter(c, (1340, 610), 'compassionate', 50, t, w(cue(18, 'compassionate')), anchor='mm', cursor=False)
    c.alpha_composite(FG)
    return c


def sE(t, D):
    """One of the most powerful families on Mars, yet she questions the cruelty of her own caste."""
    c = background()
    CARD_FEAST.place(c, 640, 500, t, 0.0, zoom=lerp(1.0, 1.06, ease(t / D)))
    typewriter(c, (640, 990), 'one of the most powerful families on Mars', 34, t, w(cue(18, 'one of')), anchor='mm', cursor=False)
    MUSTANG.place(c, 1520, H + 40, t, w(cue(18, 'yet she')), side='right')
    c.alpha_composite(FG)
    headline(c, (640, 1010), '', 10, t, 0)
    return c


def sF(t, D):
    """Darrow and Mustang are a study in opposites: one burning for revenge, the other searching for a better way."""
    c = background()
    d = ImageDraw.Draw(c)
    p = ease((t - w(cue(19, 'study'))) / 0.6)
    if p > 0:
        d.line((W / 2, 140, W / 2, 140 + 780 * p), fill=INK + (255,), width=5)
    GOLD_D.place(c, 470, H + 40, t, 0.0, side='left')
    MUSTANG.place(c, 1450, H + 40, t, 0.3, side='right')
    c.alpha_composite(FG)
    headline(c, (470, 990), 'REVENGE', 80, t, w(cue(19, 'revenge')), fill=RED)
    headline(c, (1450, 990), 'A BETTER WAY', 70, t, w(cue(19, 'a better')))
    return c


def sG(t, D):
    """Their bond forces Darrow to question whether every Gold is truly his enemy."""
    c = background()
    lines = [('IS EVERY GOLD', cue(19, 'every gold')), ('HIS ENEMY?', cue(19, 'his enemy'))]
    for i, (ln, t0) in enumerate(lines):
        headline(c, (W / 2, 420 + i * 180), ln, 150, t, w(t0), fill=RED if i == 1 else INK)
    return c


def sH(t, D):
    """If his enemies can love, grieve, and sacrifice, the war is more complicated than he imagined."""
    c = background()
    CARD_GRAVE.place(c, W / 2, 470, t, 0.0, zoom=lerp(1.0, 1.06, ease(t / D)))
    for i, (w_, t0) in enumerate([('LOVE', cue(19, 'love')), ('GRIEVE', cue(19, 'grieve')), ('SACRIFICE', cue(19, 'sacrifice'))]):
        headline(c, (W / 2 - 520 + i * 520, 960), w_, 80, t, w(t0), fill=RED if i == 2 else INK)
    return c


def sI(t, D):
    """Meanwhile, a darker figure rises: Mustang's brother, the Jackal."""
    c = background()
    JACKAL.place(c, 1300, H + 40, t, 0.0, side='right')
    typewriter(c, (560, 360), "Mustang's brother", 44, t, w(cue(20, "mustang's brother")), anchor='mm', cursor=False)
    headline(c, (560, 500), 'THE', 110, t, w(cue(20, 'known as')))
    headline(c, (560, 650), 'JACKAL', 170, t, w(cue(20, 'jackal')), fill=RED)
    c.alpha_composite(FG)
    return c


TRAITS = [('brilliant', cue(20, 'brilliant')), ('patient', cue(20, 'patient')), ('utterly without mercy', cue(20, 'utterly'))]


def sJ(t, D):
    """Brilliant, patient, and utterly without mercy."""
    c = background()
    JACKAL_HEAD.place(c, 560, H + 20, t, 0.0, side='left')
    for i, (w_, t0) in enumerate(TRAITS):
        typewriter(c, (1060, 380 + i * 120), w_, 60, t, w(t0), fill=RED if i == 2 else INK, cursor=False)
    return c


def sK(t, D):
    """Where Darrow fights for a cause, the Jackal fights only for himself."""
    c = background()
    d = ImageDraw.Draw(c)
    p = ease((t - w(cue(20, 'where darrow'))) / 0.5)
    if p > 0:
        d.line((W / 2, 140, W / 2, 140 + 780 * p), fill=INK + (255,), width=5)
    GOLD_D.place(c, 470, H + 40, t, 0.0, side='left')
    JACKAL.place(c, 1450, H + 40, t, 0.3, side='right')
    c.alpha_composite(FG)
    headline(c, (470, 990), 'A CAUSE', 80, t, w(cue(20, 'a cause')))
    headline(c, (1450, 990), 'HIMSELF', 80, t, w(cue(20, 'himself')), fill=RED)
    return c


def sL(t, D):
    """One of the most unsettling villains in modern science fiction."""
    c = background()
    JACKAL_HEAD.place(c, W / 2, H + 20, t, 0.0, side='right')
    typewriter(c, (W / 2, 150), 'ONE OF THE MOST UNSETTLING VILLAINS', 54, t, w(cue(20, 'one of the most')), anchor='mm', fill=RED, cursor=False)
    typewriter(c, (W / 2, 225), 'in modern science fiction', 40, t, w(cue(20, 'in modern')), anchor='mm', cursor=False)
    return c


SHOTS = [(0.0, sA), (cue(17, 'a wild') - LEAD, sB), (cue(17, 'darrow also') - LEAD, sC), (cue(18, 'later') - LEAD, sD),
         (cue(18, 'she belongs') - LEAD, sE), (cue(19, 'darrow and mustang') - LEAD, sF), (cue(19, 'their tense') - LEAD, sG),
         (cue(19, 'if his') - LEAD, sH), (cue(20, 'meanwhile') - LEAD, sI), (cue(20, 'is brilliant') - LEAD, sJ),
         (cue(20, 'where darrow') - LEAD, sK), (cue(20, 'and he becomes') - LEAD, sL)]
END = cue.total


def frame(t):
    return make_frame(SHOTS, END, t)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    elif mode == 'video':
        render_video(frame, END, (17, 18, 19, 20), sys.argv[2], os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a7'))
