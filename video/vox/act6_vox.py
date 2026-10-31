"""Act 6 — Rome and the Cost, Vox editorial style. Narration clips 14-16 (act-local 0.0-54.4s)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vox import *

S6 = os.path.join(SCR, 'act6', 'src')


cue = make_cue((14, 15, 16))


def cut(path, h, **k):
    return Cutout(Image.open(path).convert('RGBA'), h, **k)


PODIUM = cut(os.path.join(S6, 'podium.png'), 900)
WHISPER = cut(os.path.join(S6, 'whisper.png'), 760)
SHAKE = cut(os.path.join(S6, 'shake.png'), 760)
RED_D = cut(os.path.join(A3, 'C01A_standing.png'), 820)
GOLD_D = cut(os.path.join(A3, 'C02A_standing.png'), 880)
COMMANDER = cut(os.path.join(A3, 'C02H_commander.png'), 900)
FG = foreground()

CARD_SENATE = PhotoCard(Image.open(os.path.join(B3, 'E08A.png')), 1100, rot=-1.5, seed=121)
CARD_SENATE_SMALL = PhotoCard(Image.open(os.path.join(B3, 'E08A.png')), 760, rot=2, seed=122)
CARD_BLADE = PhotoCard(Image.open(os.path.join(A3, 'C02F_blade.png')), 1220, rot=1.5, seed=123)
CARD_WAR = PhotoCard(Image.open(os.path.join(B3, 'E09A.png')), 860, rot=-2, seed=125)


def sA(t, D):
    """Battles and betrayals borrowing from the history of ancient Rome."""
    c = background()
    CARD_SENATE.place(c, W / 2, 470, t, 0.0, zoom=lerp(1.0, 1.08, ease(t / D)))
    headline(c, (W / 2, 950), 'BORROWED FROM ROME', 110, t, w(cue(14, 'borrowing')))
    return c


def sB(t, D):
    """Senators scheme, generals plot, and noble families wage private wars for honor and revenge."""
    c = background()
    CARD_SENATE_SMALL.place(c, 1400, 420, t, 0.0)
    WHISPER.place(c, 560, H + 40, t, 0.4, side='left')
    for i, (w_, t0) in enumerate([('SENATORS SCHEME', cue(14, 'senators')), ('GENERALS PLOT', cue(14, 'generals')), ('PRIVATE WARS', cue(14, 'private'))]):
        typewriter(c, (1060, 690 + i * 70), w_, 44, t, w(t0), fill=RED if i == 2 else INK, cursor=False)
    c.alpha_composite(FG)
    return c


def sC(t, D):
    """The Society's leaders speak in the language of empire: only the strong deserve to rule."""
    c = background()
    PODIUM.place(c, 520, H + 40, t, 0.0, side='left')
    lines = [('"ONLY', cue(14, 'only')), ('THE STRONG', cue(14, 'the strong')), ('DESERVE', cue(14, 'deserve')), ('TO RULE."', cue(14, 'to rule'))]
    for i, (ln, t0) in enumerate(lines):
        headline(c, (1300, 290 + i * 150), ln, 120, t, w(t0), fill=RED if i == 1 else INK)
    c.alpha_composite(FG)
    return c


def sD(t, D):
    """Unlike many tales of chosen heroes: the cost of becoming the thing you hate."""
    c = background()
    CARD_BLADE.place(c, W / 2, 500, t, 0.0, zoom=lerp(1.0, 1.06, ease(t / D)))
    typewriter(c, (W / 2, 1000), 'becoming the thing you hate', 48, t, w(cue(15, 'becoming')), anchor='mm', fill=RED, cursor=False)
    return c


def sE(t, D):
    """To pass as a Gold, Darrow must think like one, and sometimes act like one."""
    c = background()
    RED_D.place(c, 420, H + 40, t, 0.0, side='left')
    GOLD_D.place(c, 1500, H + 40, t, w(cue(15, 'gold')), side='right')
    arrow = [(700, 520), (960, 470), (1220, 520)]
    ta = w(cue(15, 'gold')) + 0.3
    marker_line(c, arrow, ease((t - ta) / 0.6), width=12)
    if t > ta + 0.6:
        marker_line(c, [(1180, 480), (1222, 520), (1172, 552)], ease((t - ta - 0.6) / 0.3), width=12)
    headline(c, (960, 300), 'THINK LIKE ONE', 84, t, w(cue(15, 'think')))
    headline(c, (960, 640), 'ACT LIKE ONE', 84, t, w(cue(15, 'act like')), fill=RED)
    c.alpha_composite(FG)
    return c


COST = document(700, 560, [], seed=131, title='THE PRICE', title_size=54)
COST_LINES = [('lies to his friends', cue(15, 'lies')), ('makes ruthless choices', cue(15, 'makes ruthless')), ('wins battles', cue(15, 'wins battles')), ('...that leave him hollow', cue(15, 'that leave'))]


def sF(t, D):
    """He lies to his friends, makes ruthless choices, and wins battles that leave him hollow."""
    c = background()
    CARD_WAR.place(c, 1420, 520, t, w(cue(15, 'wins battles')), zoom=lerp(1.0, 1.08, ease(t / D)))
    pos = place_sheet(c, COST, 560, 540, t, 0.0, rot=-2)
    if pos:
        x0, y0 = pos
        for i, (ln, t0) in enumerate(COST_LINES):
            typewriter(c, (x0 + 70, y0 + 210 + i * 80), ln, 38, t, w(t0), fill=RED if i == 3 else INK, cursor=False)
    return c


STAGES = [(RED_D, 'A BOY', 'driven by revenge', cue(16, 'a boy')), (GOLD_D, 'A GOLD', 'learning to pass', cue(16, 'slowly')), (COMMANDER, 'A MAN', 'choosing his world', cue(16, 'a man'))]


def sG(t, D):
    """Darrow matures: from a boy driven by revenge to a man who must decide what world he fights for."""
    c = background()
    headline(c, (W / 2, 100), 'A PAINFUL TRANSFORMATION', 76, t, w(cue(16, 'painful')))
    xs = [400, 960, 1520]
    for i, (fig, title, sub, t0) in enumerate(STAGES):
        fig.place(c, xs[i], H + 40, t, w(t0), side='left' if i == 0 else 'right')
    c.alpha_composite(FG)
    for i, (fig, title, sub, t0) in enumerate(STAGES):
        headline(c, (xs[i], 945), title, 60, t, w(t0) + 0.4, fill=RED if i == 2 else INK)
        typewriter(c, (xs[i], 1015), sub, 32, t, w(t0) + 0.7, anchor='mm', cursor=False)
    return c


def sH(t, D):
    """This moral complexity: darker and bolder than the dystopias before it."""
    c = background()
    headline(c, (W / 2, 260), 'MORAL COMPLEXITY', 90, t, w(cue(16, 'moral')))
    wpx = ImageDraw.Draw(c).textlength('TOO SAFE', font=F_HEAD(120))
    headline(c, (W / 2, 470), 'TOO SAFE', 120, t, w(cue(16, 'has led')), fill=GREY)
    strike(c, W / 2 - wpx / 2 - 20, W / 2 + wpx / 2 + 20, 475, ease((t - w(cue(16, 'call red'))) / 0.4), width=16)
    headline(c, (W / 2, 680), 'DARKER', 160, t, w(cue(16, 'darker')))
    headline(c, (W / 2, 860), 'BOLDER', 160, t, w(cue(16, 'bolder')), fill=RED)
    return c


SHOTS = [(0.0, sA), (cue(14, 'senators') - LEAD, sB), (cue(14, "the society's") - LEAD, sC), (cue(15, 'yet unlike') - LEAD, sD),
         (cue(15, 'to pass') - LEAD, sE), (cue(15, 'he lies') - LEAD, sF), (cue(16, 'darrow matures') - LEAD, sG), (cue(16, 'this moral') - LEAD, sH)]
END = cue.total


def frame(t):
    return make_frame(SHOTS, END, t)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    elif mode == 'video':
        render_video(frame, END, (14, 15, 16), sys.argv[2], os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a6'))
