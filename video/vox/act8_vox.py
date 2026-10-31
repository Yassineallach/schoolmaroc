"""Act 8 — Legacy, Vox editorial style. Narration clips 21-26 (act-local 0.0-86.6s)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vox import *

S3 = os.path.join(SCR, 'act3', 'src')
S6 = os.path.join(SCR, 'act6', 'src')


def cut(path, h, **k):
    return Cutout(Image.open(path).convert('RGBA'), h, **k)


KNEEL = cut(os.path.join(A3, 'C02B_kneeling.png'), 600)
LORD = cut(os.path.join(S6, 'podium.png'), 880)
SHAKE = cut(os.path.join(S6, 'shake.png'), 820)
DAWN = cut(os.path.join(A3, 'C02G_dawn.png'), 940)
COMMANDER = cut(os.path.join(A3, 'C02H_commander.png'), 900)
UNITED = [cut(os.path.join(S3, n + '.png'), 380 if n == 'obsidian' else 320, stroke_x=12, stroke_y=5)
          for n in ('red', 'blue', 'obsidian', 'gold', 'pink', 'brown')]
FG = foreground()

CARD_FLEET = PhotoCard(Image.open(os.path.join(B3, 'E10.png')), 1250, rot=-1.5, seed=161)
CARD_WAR = PhotoCard(Image.open(os.path.join(B3, 'E09A.png')), 960, rot=2, seed=163)
CARD_READERS = PhotoCard(Image.open(os.path.join(A3, 'A01.png')), 1250, rot=-1.2, seed=165)


def book(title, color, seed, w_=300, h_=440):
    b = Image.new('RGBA', (w_, h_), color + (255,))
    d = ImageDraw.Draw(b)
    d.rectangle((0, 0, 26, h_), fill=tuple(int(c * 0.7) for c in color) + (255,))
    words = title.split()
    for i, wd in enumerate(words):
        d.text((w_ / 2 + 12, 150 + i * 70), wd, font=F_HEAD(46), fill=CREAM + (255,), anchor='mm')
    d.line((60, 330, w_ - 40, 330), fill=CREAM + (255,), width=3)
    d.text((w_ / 2 + 12, 375), 'PIERCE BROWN', font=F_TYPE(22), fill=CREAM + (255,), anchor='mm')
    b.putalpha(torn_mask(w_, h_, seed, amp=2, step=16))
    return b


BOOKS = [book('RED RISING', (168, 50, 38), 171), book('GOLDEN SON', (176, 132, 52), 172), book('MORNING STAR', (40, 46, 66), 173)]


def sA(t, D):
    """Red Rising was a huge success. Its sequels followed in quick succession."""
    c = background()
    headline(c, (W / 2, 130), 'A HUGE SUCCESS', 100, t, 0.0)
    for i, b in enumerate(BOOKS):
        place_sheet(c, b, 560 + i * 400, 600, t, 0.8 + i * 1.3, rot=(-4, 1, 4)[i])
    return c


def sB(t, D):
    """In Golden Son, Darrow climbs higher, serving powerful lords while secretly planning their downfall."""
    c = background()
    LORD.place(c, 520, H + 40, t, 0.0, side='left')
    KNEEL.place(c, 980, H + 40, t, 0.5, side='right')
    c.alpha_composite(FG)
    typewriter(c, (1240, 330), 'GOLDEN SON', 64, t, 0.8, cursor=False)
    typewriter(c, (1240, 450), 'serving powerful lords', 40, t, 1.8, cursor=False)
    typewriter(c, (1240, 530), 'planning their downfall', 40, t, 3.6, fill=RED, cursor=False)
    return c


def sC(t, D):
    """In Morning Star, the rebellion spreads beyond Mars."""
    c = background()
    CARD_FLEET.place(c, W / 2, 500, t, 0.0, zoom=lerp(1.0, 1.1, ease(t / D)))
    typewriter(c, (W / 2, 1010), 'the rebellion spreads beyond Mars', 46, t, 0.6, anchor='mm', fill=RED, cursor=False)
    return c


def sD(t, D):
    """The castes the Society kept divided begin to fight side by side."""
    c = background()
    headline(c, (W / 2, 150), 'SIDE BY SIDE', 120, t, 0.0)
    for i, f in enumerate(UNITED):
        f.place(c, 330 + i * 252, 900, t, 0.4 + i * 0.25, side='left' if i < 3 else 'right')
    marker_line(c, [(180, 925), (960, 915), (1740, 925)], ease((t - 2.2) / 0.8), width=12)
    return c


LIST = ['1.  MORNING STAR', '2.  ---------------', '3.  ---------------', '4.  ---------------', '5.  ---------------']


def sE(t, D):
    """The final volume reached the top of the bestseller lists."""
    c = background()
    sheet = document(820, 760, [], seed=181, title='BESTSELLERS', title_size=60)
    pos = place_sheet(c, sheet, W / 2, 560, t, 0.0, rot=-1.5)
    if pos:
        x0, y0 = pos
        for i, ln in enumerate(LIST):
            dy, op = arrive(t, 0.6 + i * 0.25, 60)
            text(c, (x0 + 90, y0 + 230 + i * 95 + dy), ln, F_TYPE(46) if i else F_HEAD(52), INK if i else RED, 'lm', op)
        marker_circle(c, x0 + 330, y0 + 230, 320, 60, ease((t - 2.4) / 0.7), seed=8)
    return c


def sF(t, D):
    """Readers clamored for more. Years later, Brown returned with a new series."""
    c = background()
    for i, b in enumerate(BOOKS):
        place_sheet(c, b.resize((220, 322)), 330 + i * 250, 560, t, 0.0, rot=(-4, 1, 4)[i], rise=0)
    typewriter(c, (1100, 330), 'YEARS LATER...', 60, t, 1.2, cursor=False)
    newb = book('A NEW SERIES', (70, 90, 80), 174)
    place_sheet(c, newb, 1450, 640, t, 2.6, rot=3)
    return c


def sG(t, D):
    """It asks a harder question: what happens after the revolution wins?"""
    c = background()
    typewriter(c, (W / 2, 260), 'a harder question', 46, t, 0.2, anchor='mm', cursor=False)
    headline(c, (W / 2, 470), 'WHAT HAPPENS', 140, t, 1.0)
    headline(c, (W / 2, 640), 'AFTER THE', 140, t, 1.4)
    headline(c, (W / 2, 810), 'REVOLUTION WINS?', 140, t, 1.8, fill=RED)
    return c


TIERS = [(300, 260), (440, 480), (580, 700), (720, 920), (860, 1140)]


def sH(t, D):
    """The Society cracks not only from below, but from the ambitions of its own nobles."""
    c = background()
    headline(c, (W / 2, 120), 'THE SOCIETY CRACKS', 96, t, 0.0)
    d = ImageDraw.Draw(c)
    cols = [(196, 154, 69), (168, 170, 174), (62, 92, 142), (220, 150, 160), (180, 60, 40)]
    for i, ((y, w_), col) in enumerate(zip(TIERS, cols)):
        dy, op = arrive(t, 0.3 + i * 0.15, 200)
        if op > 0:
            d.rectangle((W / 2 - w_ / 2, y + dy, W / 2 + w_ / 2, y + 120 + dy), fill=col + (int(255 * op),), outline=INK + (255,), width=4)
    crack_low = [(W / 2 - 60, 980), (W / 2 - 20, 900), (W / 2 - 70, 820), (W / 2 + 10, 740), (W / 2 - 40, 640)]
    crack_top = [(W / 2 + 20, 300), (W / 2 - 25, 360), (W / 2 + 30, 420), (W / 2 - 10, 500)]
    marker_line(c, crack_low, ease((t - 1.8) / 1.0), width=12)
    typewriter(c, (1560, 920), 'from below', 44, t, 2.2, cursor=False)
    marker_line(c, crack_top, ease((t - 3.6) / 0.8), width=12)
    typewriter(c, (1240, 330), 'and from its own nobles', 44, t, 4.0, fill=RED, cursor=False)
    return c


def sI(t, D):
    """Golds betray Golds, alliances shift overnight; the empire's greatest threat is its own pride."""
    c = background()
    SHAKE.place(c, 700, H + 40, t, 0.0, side='left')
    c.alpha_composite(FG)
    headline(c, (1450, 400), 'GOLDS', 120, t, 0.8)
    headline(c, (1450, 530), 'BETRAY', 120, t, 1.1, fill=RED)
    headline(c, (1450, 660), 'GOLDS', 120, t, 1.4)
    typewriter(c, (1450, 790), 'undone by its own pride', 40, t, 3.6, anchor='mm', cursor=False)
    return c


def sJ(t, D):
    """Every victory costs Darrow someone he loves. He wins the war at great expense."""
    c = background()
    CARD_WAR.place(c, 1300, 450, t, 0.0, zoom=lerp(1.0, 1.08, ease(t / D)))
    COMMANDER.place(c, 460, H + 40, t, 0.6, side='left')
    c.alpha_composite(FG)
    typewriter(c, (1300, 960), 'every victory costs someone he loves', 44, t, 1.2, anchor='mm', fill=RED, cursor=False)
    return c


def sK(t, D):
    """His story has inspired fan art, online communities, and a rallying cry shared worldwide."""
    c = background()
    CARD_READERS.place(c, W / 2, 500, t, 0.0, zoom=lerp(1.0, 1.06, ease(t / D)))
    for i, (w_, t0) in enumerate([('FAN ART', 1.0), ('COMMUNITIES', 2.0), ('A RALLYING CRY', 3.0)]):
        headline(c, (W / 2 - 600 + i * 600, 1000), w_, 54, t, t0, fill=RED if i == 2 else INK)
    return c


def sL(t, D):
    """Fans debate its battles, mourn its characters, and greet each other with the language of the rebellion."""
    c = background()
    for i, (w_, t0) in enumerate([('DEBATE ITS BATTLES', 0.3), ('MOURN ITS CHARACTERS', 1.6), ('SPEAK ITS LANGUAGE', 3.0)]):
        headline(c, (W / 2, 340 + i * 200), w_, 120, t, t0, fill=RED if i == 2 else INK)
    return c


THEMES = [('NO CHAIN IS UNBREAKABLE', 0.4), ('THE LOWEST CAN RISE', 2.6)]


def sM(t, D):
    """No chain is unbreakable, the lowest can rise, and the hardest fight is staying human once you've won."""
    c = background()
    if t < 7.4:
        DAWN.place(c, 1500, H + 40, t, 0.0, side='right')
        c.alpha_composite(FG)
        for i, (w_, t0) in enumerate(THEMES):
            typewriter(c, (110, 300 + i * 120), w_, 56, t, t0, cursor=False)
        typewriter(c, (110, 560), 'the hardest fight:', 46, t, 4.6, cursor=False)
        headline(c, (110, 690), 'STAYING HUMAN', 110, t, 5.4, fill=RED, anchor='lm')
    else:
        headline(c, (W / 2, 470), 'RED RISING', 230, t, 7.5, tracking=-4)
        marker_line(c, [(470, 610), (960, 598), (1450, 610)], ease((t - 8.0) / 0.6), width=14)
    return c


SHOTS = [(0.0, sA), (7.6, sB), (14.6, sC), (18.4, sD), (22.7, sE), (27.9, sF), (34.0, sG),
         (39.5, sH), (46.4, sI), (53.7, sJ), (62.7, sK), (69.2, sL), (76.8, sM)]
END = 86.6


def frame(t):
    return make_frame(SHOTS, END, t)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    elif mode == 'video':
        render_video(frame, END, (21, 22, 23, 24, 25, 26), sys.argv[2], os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a8'))
