"""Act 5 — The Institute, Vox editorial style. Narration clips 11-13 (act-local 0.0-54.2s)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vox import *

S5 = os.path.join(SCR, 'act5', 'src')


cue = make_cue((11, 12, 13))


def cut(path, h, **k):
    return Cutout(Image.open(path).convert('RGBA'), h, **k)


GOLD = cut(os.path.join(A3, 'C02A_standing.png'), 900)
RALLY = cut(os.path.join(A3, 'C02C_rallying.png'), 900)
PROCTORS = [cut(os.path.join(S5, f'p{i}.png'), 520, stroke_x=16, stroke_y=6) for i in (1, 2, 3, 4)]
FG = foreground()

HIGHLANDS = Image.open(os.path.join(B2, 'E06.png'))
CARD_INST = PhotoCard(HIGHLANDS, 1000, rot=2, seed=101)
CARD_WILD = PhotoCard(HIGHLANDS, 1300, rot=-1.2, seed=103)
CARD_BASIN = PhotoCard(Image.open(os.path.join(A3, 'C02E_basin.png')), 1180, rot=-1.5, seed=105)
CARD_HALL = PhotoCard(Image.open(os.path.join(B2, 'E07A.png')), 1250, rot=1.5, seed=107)
CARD_CHAOS = PhotoCard(Image.open(os.path.join(B2, 'E07B.png')), 1250, rot=-2, seed=109)


def sA(t, D):
    """He enters the Institute, a brutal war school for the children of the elite."""
    c = background()
    CARD_INST.place(c, 1290, 470, t, 0.0, zoom=lerp(1.0, 1.08, ease(t / D)))
    GOLD.place(c, 480, H + 40, t, w(cue(11, 'he enters')), side='left')
    c.alpha_composite(FG)
    headline(c, (1290, 860), 'THE INSTITUTE', 110, t, w(cue(11, 'institute')))
    typewriter(c, (1290, 975), 'a war school for the children of the elite', 34, t, w(cue(11, 'a brutal')), anchor='mm', cursor=False)
    return c


TRIAL = document(700, 620, ['', 'Candidate vs. candidate', '', 'Condition of entry:', 'SURVIVE', '', '---'], seed=111,
                 title='ENTRY TRIAL', title_size=54, body_size=38, typed=True)


def sB(t, D):
    """To gain entry, each student must survive a deadly trial against another. Darrow passes."""
    c = background()
    place_sheet(c, TRIAL, W / 2, 560, t, 0.0, rot=-2)
    stamp(c, W / 2 + 190, 790, 'PASSED', 84, t, w(cue(11, 'passes')), ang=-12)
    return c


def sC(t, D):
    """But the cost will haunt him."""
    c = background()
    CARD_BASIN.place(c, W / 2, 520, t, 0.0, zoom=lerp(1.0, 1.06, ease(t / D)))
    typewriter(c, (W / 2, 1010), 'the cost will haunt him', 46, t, w(cue(11, 'the cost')), anchor='mm', fill=RED, cursor=False)
    return c


HOUSES = [('MARS', (178, 52, 40)), ('MINERVA', (54, 86, 140)), ('JUPITER', (196, 154, 69)), ('APOLLO', (214, 120, 40))]


def banner(name, color, w_=300, h_=560):
    b = Image.new('RGBA', (w_, h_), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    d.polygon([(0, 0), (w_, 0), (w_, h_), (w_ / 2, h_ - 90), (0, h_)], fill=color + (255,))
    d.rectangle((0, 0, w_, 24), fill=INK + (255,))
    f = F_HEAD(46 if len(name) < 7 else 40)
    for i, ch in enumerate(name):
        d.text((w_ / 2, 80 + i * 56), ch, font=f, fill=CREAM + (255,), anchor='mm')
    return b


BANNERS = [banner(n, col) for n, col in HOUSES]
MORE = banner('...', (150, 148, 143))


def sD(t, D):
    """Students are divided into houses named for the Roman gods: Mars, Minerva, Jupiter, Apollo, and more."""
    c = background()
    headline(c, (W / 2, 110), 'HOUSES OF THE GODS', 90, t, w(cue(12, 'houses')))
    d = ImageDraw.Draw(c)
    d.line((120, 250, W - 120, 250), fill=INK + (255,), width=6)
    starts = [w(cue(12, x)) for x in ('mars', 'minerva', 'jupiter', 'apollo', 'and more')]
    for i, b in enumerate(BANNERS + [MORE]):
        x = 260 + i * 350
        sway = 2.5 * math.sin(t * 1.6 + i)
        bb = b.rotate(sway, resample=Image.BICUBIC, expand=True, center=(b.width / 2, 0))
        place_sheet(c, bb, x, 250 + bb.height / 2, t, starts[i], rise=-300)
    typewriter(c, (1660, 900), 'and more', 40, t, w(cue(12, 'and more')), anchor='mm', cursor=False)
    return c


def sE(t, D):
    """Released into a vast wilderness and told to conquer one another."""
    c = background()
    CARD_WILD.place(c, W / 2, 540, t, 0.0, zoom=lerp(1.0, 1.12, ease(t / D)), pan=(0.5, 0.45))
    typewriter(c, (W / 2, 1020), 'CONQUER ONE ANOTHER', 52, t, w(cue(12, 'conquer')), anchor='mm', fill=RED, cursor=False)
    return c


RULES = None  # built after cue is defined


def sF(t, D):
    """There are no rules, no supplies, and no mercy."""
    c = background()
    for i, (w_, t0) in enumerate(RULES):
        headline(c, (W / 2, 330 + i * 210), w_, 160, t, w(t0), fill=RED if i == 2 else INK)
    return c


def sG(t, D):
    """The Proctors watch from above, and they do not always play fair."""
    c = background()
    xs = [330, 760, 1180, 1600]
    for i, p in enumerate(PROCTORS):
        bob = 12 * math.sin(t * 1.3 + i * 1.7)
        p.place(c, xs[i], 640 + bob, t, w(cue(12, 'the teachers')) + i * 0.3, rise=-400, side='left' if i < 2 else 'right')
    headline(c, (W / 2, 790), 'THE PROCTORS', 120, t, w(cue(12, 'proctors')))
    typewriter(c, (W / 2, 900), 'they do not always play fair', 44, t, w(cue(12, 'and they')), anchor='mm', fill=RED, cursor=False)
    return c


def sH(t, D):
    """Darrow is sorted into House Mars."""
    c = background()
    CARD_HALL.place(c, W / 2, 500, t, 0.0, zoom=lerp(1.0, 1.06, ease(t / D)))
    headline(c, (W / 2, 990), 'HOUSE MARS', 120, t, w(cue(13, 'house mars')), fill=RED)
    return c


def sI(t, D):
    """His house descends into chaos, students turning on one another out of fear and cruelty."""
    c = background()
    CARD_CHAOS.place(c, W / 2, 500, t, 0.0, zoom=lerp(1.0, 1.08, ease(t / D)))
    headline(c, (W / 2, 990), 'CHAOS', 120, t, w(cue(13, 'chaos')))
    typewriter(c, (1500, 1000), 'fear and cruelty', 38, t, w(cue(13, 'fear')), anchor='mm', fill=RED, cursor=False)
    return c


def sJ(t, D):
    """Strength alone will not save him. To win, he must become a leader."""
    c = background()
    RALLY.place(c, 1280, H + 30, t, 0.0, side='right')
    headline(c, (560, 400), 'STRENGTH', 130, t, w(cue(13, 'strength')))
    wpx = ImageDraw.Draw(c).textlength('STRENGTH', font=F_HEAD(130))
    strike(c, 560 - wpx / 2 - 20, 560 + wpx / 2 + 20, 405, ease((t - w(cue(13, 'not save'))) / 0.45), width=16)
    headline(c, (560, 580), 'A LEADER', 130, t, w(cue(13, 'a leader')), fill=RED)
    c.alpha_composite(FG)
    return c


RULES = [('NO RULES', cue(12, 'no rules')), ('NO SUPPLIES', cue(12, 'no supplies')), ('NO MERCY', cue(12, 'no mercy'))]
SHOTS = [(0.0, sA), (cue(11, 'to gain') - LEAD, sB), (cue(11, 'but the cost') - LEAD, sC), (cue(12, 'inside') - LEAD, sD),
         (cue(12, 'then they') - LEAD, sE), (cue(12, 'there are') - LEAD, sF), (cue(12, 'the teachers') - LEAD, sG),
         (cue(13, 'darrow is sorted') - LEAD, sH), (cue(13, 'at first') - LEAD, sI), (cue(13, 'darrow realizes') - LEAD, sJ)]
END = cue.total


def frame(t):
    return make_frame(SHOTS, END, t)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    elif mode == 'video':
        render_video(frame, END, (11, 12, 13), sys.argv[2], os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a5'))
