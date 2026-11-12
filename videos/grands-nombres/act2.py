"""Acte 2 : Un, deux, beaucoup. Narration clips 4-5."""
import sys
import math
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
import maps
from style import sfx, ENTER, Shot, words, tag, kicker, caption
import gn as N

CLIPS = (4, 5)
cue = make_cue(CLIPS)

# ---- real images (Wikimedia Commons, credits in assets/credits.json) ----
NARMER = N.image('R05', (1920, 1203), 'massue de Narmer')
HEH = N.image('R06', (1500, 2000), 'Heh')
MILESTONE = N.image('R07', (1400, 1050), 'borne milliaire')

NARMER_CARD = P.print_card(S.treated(NARMER), 1640, seed=51)
HEH_CARD = P.print_card(S.treated(HEH).crop((int(HEH.width * 0.12), int(HEH.height * 0.12), int(HEH.width * 0.88), int(HEH.height * 0.92))), 430, seed=52)
MILESTONE_CARD = P.print_card(S.treated(MILESTONE), 900, seed=53)

M = maps.WorldMap(box=(0, 0, W, H))
AFRICA_S = M.around((22.0, -26.0), km=2600)
ATLANTIC = M.around((-20.0, -12.0), km=11000)
AMAZON = M.around((-62.0, -7.5), km=2200)
KHOI = (18.5, -27.5)                       # southern Africa, the Khoekhoe-speaking region
PIRAHA = (-62.0, -7.5)                     # the Maici river, Amazonas

QUOTE = P.paper_card(760, 150, seed=61, colour=PAL.light)
_qd = ImageDraw.Draw(QUOTE)
_qd.text((380, 75), '« un, deux, trois, beaucoup »', font=F_TYPE(46), fill=PAL.ink + (255,), anchor='mm')


def on_narmer(fx, fy, cx=W / 2, cy=520):
    w_, h_ = NARMER_CARD.size
    return cx - w_ / 2 + 16 + fx * (w_ - 32), cy - h_ / 2 + 16 + fy * (h_ - 32)


LOTUS = on_narmer(0.615, 0.945)
TADPOLE = on_narmer(0.515, 0.94)
HEH_PT = on_narmer(0.632, 0.855)


def sA(t, D):
    """Dans le même livre, Gamow affirme qu'un peuple d'Afrique australe, les Khoïkhoïs, ne
    comptait pas au-delà de trois et disait simplement « beaucoup » ensuite."""
    s = Shot(t, D)
    S.env(s, 'paper')
    view = M.zoom(t, [(ENTER, M.WORLD), (w(cue(4, "'Afrique")), AFRICA_S)])
    M.draw(s.mid, view, t)
    M.marker(s.mid, view, KHOI, 'Khoïkhoïs', t, w(cue(4, 'les Khoikhois')))
    P.drop(s.mid, QUOTE, 1380, 820, t, w(cue(4, 'trois')), rot=-3, spin=9, key='quote')
    kicker(s.hud, t, 2, 'Un, deux, beaucoup', start=0.3)
    return s


def sB(t, D):
    """L'anecdote a fait le tour du monde. Elle est fausse."""
    s = Shot(t, D)
    S.env(s, 'cream')
    P.put(s.mid, QUOTE.rotate(-3, Image.BICUBIC, expand=True), W / 2, 500)
    box = A.grow((W / 2 - 330, 455, W / 2 + 330, 545), 0, 0)
    A.strike(s.mid, box, t, w(cue(4, 'Elle est')), scribble=False)
    P.stamp_hit(s.mid, 'FAUX', W / 2 + 280, 650, t, w(cue(4, 'fausse')), size=96, ang=-8, shot=s)
    return s


def sC(t, D):
    """Le khoekhoe possède des mots pour quatre, pour dix, pour mille et même pour un million."""
    s = Shot(t, D)
    S.env(s, 'theme')
    s.camera(1.0, 1.03)
    P.put(s.mid, QUOTE.rotate(-3, Image.BICUBIC, expand=True).resize((456, 98), Image.LANCZOS), 300, 190)   # Gamow's claim, struck
    A.strike(s.mid, (90, 175, 510, 205), t, -5.0, sound=False)
    tags = (('quatre', '4', 420, 520, -4), ('dix', '10', 760, 650, 2.5), ('mille', '1 000', 1140, 500, -1.5),
            ('un million', '1 000 000', 1480, 700, 3))
    for i, (ph, txt, x, y, rot) in enumerate(tags):
        card = P.paper_card(int(140 + 52 * len(txt)), 150, seed=70 + i, colour=PAL.light, text=None)
        ImageDraw.Draw(card).text((card.width / 2, 75), txt, font=F_HEAD(72), fill=PAL.ink + (255,), anchor='mm')
        at = w(cue(4, ph)) - 0.1
        P.drop(s.mid, card, x, y, t, at, rot=rot, spin=10, key=f'num{i}')
    return s


def sD(t, D):
    """Pourtant, certaines langues comptent bien ainsi. En 2004, le psychologue Peter Gordon a
    montré que les Pirahãs d'Amazonie..."""
    s = Shot(t, D)
    S.env(s, 'paper')
    view = M.zoom(t, [(ENTER, AFRICA_S), (w(cue(4, 'certaines')), ATLANTIC), (w(cue(4, 'Piranhas')) - 0.4, AMAZON)])
    M.draw(s.mid, view, t)
    M.route(s.mid, view, [KHOI, (-5.0, -15.0), PIRAHA], t, w(cue(4, 'certaines')) + 0.2, dur=1.8)
    M.marker(s.mid, view, PIRAHA, 'Pirahãs · 2004', t, w(cue(4, 'Piranhas')) + 0.3)
    return s


def sE(t, D):
    """...dont les mots signifient à peu près « un », « deux » et « beaucoup », peinaient à
    reproduire exactement une quantité supérieure à trois."""
    s = Shot(t, D)
    S.env(s, 'grid')
    d = ImageDraw.Draw(s.mid)
    ink, acc = PAL.ink, PAL.accent

    def row(n, y, start, colour, x0=520, step=118, r=36, jitter=None):
        for i in range(n):
            at = start + 0.09 * i
            k = P.ease_out(P.clamp01((t - at) / 0.25))
            if k <= 0:
                continue
            x = x0 + i * step + (jitter[i] if jitter else 0)
            rr = r * k
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=colour + (255,))
    row(3, 300, ENTER, ink)                                     # three: copied exactly
    row(3, 420, w(cue(4, 'un', 2)), acc)
    row(7, 640, w(cue(4, 'peinaient')), ink)                    # seven: copied as six, then eight
    row(6, 760, w(cue(4, 'reproduire')), acc, jitter=[0, 6, -4, 10, 3, -6])
    A.mark(s.mid, (520 + 7 * 118 + 30, 760), 'question', t, w(cue(4, 'exactement')) + 0.3)
    return s


def sF(t, D):
    """Les grandes civilisations ont repoussé cette limite, mais symbole après symbole."""
    s = Shot(t, D)
    S.env(s, 'archive')
    s.camera(1.0, 1.05, (W / 2, 520), (W / 2, 600))
    P.put(s.mid, NARMER_CARD, W / 2, 520)
    caption(s.hud, 'Massue de Narmer, relevé de J. E. Quibell, 1900', t, ENTER + 1.0)
    return s


def sG(t, D):
    """Les scribes égyptiens dessinaient une fleur de lotus pour mille, un têtard pour cent mille
    et un dieu agenouillé, bras levés, pour un million."""
    s = Shot(t, D)
    S.env(s, 'paper')
    cx, cy = (LOTUS[0] + TADPOLE[0]) / 2, (HEH_PT[1] + LOTUS[1]) / 2
    s.camera(2.1, 2.3, (cx, cy), (cx + 30, cy))
    P.put(s.mid, NARMER_CARD, W / 2, 520)
    marks = (('lotus', LOTUS, '1 000', 34), ('tetard', TADPOLE, '100 000', 46), ('dieu', HEH_PT, '1 000 000', 30))
    for ph, (x, y), lab, r in marks:
        at = w(cue(5, ph))
        A.ring(s.mid, (x - r, y - r, x + r, y + r), t, at, width=4, until=at + 2.6)
    P.slide(s.hud, HEH_CARD, (W + 300, 560), (1560, 560), t, w(cue(5, 'agenouille')), dur=1.0, rot=3, key='heh')
    caption(s.hud, 'Signe heh, « millions », faïence, Égypte (Met)', t, w(cue(5, 'agenouille')) + 0.9)
    return s


def sH(t, D):
    """Les Romains écrivaient M pour mille."""
    s = Shot(t, D)
    S.env(s, 'theme')
    s.camera(1.0, 1.12, (W / 2, 520), (W / 2 + 40, 470))           # towards the inscription
    P.put(s.mid, MILESTONE_CARD, W / 2, 520)
    caption(s.hud, 'Borne milliaire romaine de Middleton, Cumbria (« M P LIII »)', t, ENTER + 0.8)
    return s


def sI(t, D):
    """Sans zéro ni valeur de position, chaque ordre de grandeur réclamait un signe nouveau, et
    les nombres s'arrêtaient là où s'arrêtaient les signes."""
    s = Shot(t, D)
    S.env(s, 'cream')
    signs = [N.crop_frac(NARMER, b) for b in ((0.598, 0.905, 0.632, 0.985), (0.47, 0.895, 0.56, 0.985))]
    signs.append(HEH)
    xs = (360, 760, 1160)
    for i, (im, x) in enumerate(zip(signs, xs)):
        card = P.print_card(S.treated(im), 300 if i < 2 else 320, seed=80 + i)
        at = ENTER + 0.25 * i if i else ENTER
        P.drop(s.mid, card, x, 520 + (-12, 8, -4)[i], t, at, rot=(-3, 1.5, -1)[i], spin=8, key=f'sign{i}')
    # the next sign that does not exist: an empty dashed slot
    k = P.clamp01((t - w(cue(5, 'signe'))) / 0.6)
    if k > 0:
        d = ImageDraw.Draw(s.mid)
        x0, y0, x1, y1 = 1420, 330, 1700, 710
        per = 2 * (x1 - x0) + 2 * (y1 - y0)
        L = per * P.ease_io(k)
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        for a, b in zip(pts[:-1], pts[1:]):
            seg = math.hypot(b[0] - a[0], b[1] - a[1])
            n = int(seg // 22)
            for j in range(n):
                if L <= 0:
                    break
                f0, f1 = j / n, min(1.0, (j + 0.55) / n)
                d.line((a[0] + (b[0] - a[0]) * f0, a[1] + (b[1] - a[1]) * f0, a[0] + (b[0] - a[0]) * f1, a[1] + (b[1] - a[1]) * f1),
                       fill=PAL.muted + (255,), width=4)
                L -= 22
    return s


SHOTS = [
    (0.0, sA),
    (cue(4, "'anecdote") - LEAD - 0.1, sB, 'up'),
    (cue(4, 'le khoekhoe') - LEAD, sC, 'lr'),
    (cue(4, 'Pourtant') - LEAD, sD, 'rl'),
    (cue(4, 'dont') - LEAD, sE, 'up'),
    (cue(5, 'Les grandes') - LEAD, sF, 'pageturn'),
    (cue(5, 'Les scribes') - LEAD, sG, 'lr'),
    (cue(5, 'Les Romains') - LEAD, sH, 'rl'),
    (cue(5, 'Sans') - LEAD, sI, 'up'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
