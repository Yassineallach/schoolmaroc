"""Acte 2 : Le code. Narration clips 11-14."""
import sys
from PIL import Image
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
from style import sfx, ENTER, Shot, kicker
import ch as C

CLIPS = (11, 12, 13, 14)
cue = make_cue(CLIPS)

LCX, LCY = W / 2, H - C.LINE.height / 2 + 40      # the line of ten, as in act 1
B_NOIR, B_BLANC = C.bubble('« noir »', 60), C.bubble('« blanc »', 60)

# the ten digits of « le nombre total »: a row, then sorted by parity
DIG_Y = 560
DIG_X = [W / 2 + (i - 4.5) * 165 for i in range(10)]
PAR_Y = {0: 470, 1: 800}                          # evens above, odds below
PAR_X = [800 + (i // 2) * 200 for i in range(10)]


def line_with(s, t, hats, start=None, lags=None):
    C.put_line(s.mid, LCX, LCY)
    for i in range(10):
        if start is None:
            C.place_hat(s.mid, i, hats[i], LCX, LCY, t, 0, drop=False, seed=5)
        else:
            C.place_hat(s.mid, i, hats[i], LCX, LCY, t, start + lags[i], seed=5)


def sA(t, D):
    """La clé, c'est que la personne au fond de la file, qui voit tous les autres chapeaux..."""
    s = Shot(t, D)
    S.env(s, 'grid')
    s.camera(1.0, 1.03, (W / 2, H / 2), (W / 2 - 200, H / 2))
    line_with(s, t, C.SHOWN)
    e = C.head(0, LCX, LCY)
    f = C.head(9, LCX, LCY)
    eye = (e[0] + C.FIGS[0]['hw'] * 0.38, e[1] + C.FIGS[0]['hw'] * 0.45)
    C.cone(s.top, eye, f[0] + 90, e[1] - 150, f[1] + 60, t, w(cue(11, 'voit')), colour=PAL.ink2, alpha=0.14)
    A.spotlight(s.mid, (e[0] + 10, LCY - 60), 400, t, w(cue(11, 'fond')), dim=0.16)
    kicker(s.hud, t, 2, 'Le code', start=0.4)
    return s


def sB(t, D):
    """... peut se servir des mots « noir » et « blanc » pour transmettre une information codée."""
    s = Shot(t, D)
    S.env(s, 'theme')
    sc = 0.8                                          # a smaller line leaves room for the words above it
    cy = H - C.LINE.height * sc / 2 + 30
    C.put_line(s.mid, LCX, cy, scale=sc)
    for i in range(10):
        C.place_hat(s.mid, i, C.SHOWN[i], LCX, cy, t, 0, scale=sc, drop=False, seed=5)
    hx, hy = C.head(0, LCX, cy, sc)
    C.pop_in(s.top, B_NOIR, hx + 240, hy - 250, t, w(cue(11, 'noir')))
    C.pop_in(s.top, B_BLANC, hx + 540, hy - 190, t, w(cue(11, 'blanc')))
    pts = []
    for i in (0, 3, 6, 9):
        x, y = C.hat_at(i, LCX, cy, sc)
        pts.append((x, y - C.hat_w(i, sc) * 0.5 - 40))
    A.connect(s.top, pts, t, w(cue(11, 'transmettre')), dur=1.1, colour=PAL.ink2, dashed=True, arrowhead=True)
    return s


def sC(t, D):
    """Mais quel sens donner à ces mots pour que tous les autres puissent déduire la couleur de leur chapeau ?"""
    s = Shot(t, D)
    S.env(s, 'cream')                                 # locked off: the question, nothing else
    at = w(cue(11, 'sens'))
    for k, (word, y) in enumerate((('« noir »', 400), ('« blanc »', 640))):
        TY.Text(word, 'statement', size=120).draw(s.top, (W / 2 - 60, y), t, at + 0.25 * k, anim='words', anchor='r')
        TY.Text('= ?', 'statement', size=120, colour=PAL.accent).draw(s.top, (W / 2 + 40, y), t, w(cue(11, 'deduire')) + 0.2 * k, anim='scale', anchor='l')
    return s


def digits(s, t, start, sort_at=None, strike_at=None, until_strike=None):
    for i in range(10):
        at = start + [0, .06, .14, .2, .3, .34, .45, .5, .58, .66][i]
        x, y = DIG_X[i], DIG_Y
        col = INK
        if sort_at is not None:                       # both rows part at once, then each takes its colour on its word
            k = P.ease_io((t - sort_at[0] - 0.04 * (i // 2)) / 0.8)
            x = DIG_X[i] + (PAR_X[i] - DIG_X[i]) * k
            y = DIG_Y + (PAR_Y[i % 2] - DIG_Y) * k
            if t >= sort_at[i % 2] + 0.3:
                col = C.PAIR if i % 2 == 0 else C.IMPAIR
        TY.Text(str(i), 'stat', size=170, colour=col).draw(s.top, (x, y), t, at, anim='scale', anchor='m', sound=False)
    if strike_at is not None:
        A.strike(s.top, (DIG_X[0] - 90, DIG_Y + 60, DIG_X[-1] + 90, DIG_Y + 120), t, strike_at, width=12, until=until_strike, exit='fade')


def sD(t, D):
    """Ce ne peut pas être le nombre total de chapeaux noirs ou blancs : il a plus de deux valeurs possibles."""
    s = Shot(t, D)
    S.env(s, 'grid')
    digits(s, t, ENTER + 0.1, strike_at=w(cue(12, 'possibles')))
    return s


def sE(t, D):
    """En revanche, une chose n'en a que deux : la parité de ce nombre, c'est-à-dire le fait qu'il soit pair ou impair."""
    s = Shot(t, D)
    S.env(s, 'paper')
    digits(s, t, -5.0, sort_at=(w(cue(12, 'pere')) - 0.5, w(cue(12, 'impere'))))
    TY.term_card(s.top, (180, 120), 'Parité', 'pair ou impair', t, w(cue(12, 'parite')), width=760)
    TY.Text('PAIR', 'label', size=40, colour=C.PAIR).draw(s.top, (560, PAR_Y[0]), t, w(cue(12, 'pere')), anim='words', anchor='r')
    TY.Text('IMPAIR', 'label', size=40, colour=C.IMPAIR).draw(s.top, (560, PAR_Y[1]), t, w(cue(12, 'impere')), anim='words', anchor='r')
    return s


def sF(t, D):
    """La solution consiste donc à convenir que le premier à parler dira, par exemple, « noir » s'il voit un nombre
    impair de chapeaux noirs, et « blanc » s'il en voit un nombre pair."""
    s = Shot(t, D)
    S.env(s, 'theme')
    s.camera(1.0, 1.03)
    TY.Text('chapeaux noirs vus devant soi', 'label', size=34, colour=PAL.ink2).draw(s.top, (W / 2, 250), t, ENTER + 0.1, anim='words', anchor='m')
    for k, (word, par, col, y, a, b) in enumerate((('« noir »', 'impair', C.IMPAIR, 460, 'noir', 'impair'),
                                                    ('« blanc »', 'pair', C.PAIR, 700, 'blanc', 'pair'))):
        TY.Text(word, 'statement', size=110).draw(s.top, (W / 2 - 130, y), t, w(cue(13, a)), anim='words', anchor='r')
        A.arrow(s.top, (W / 2 - 90, y + 55), (W / 2 + 110, y + 55), t, w(cue(13, a)) + 0.4, bend=0.0, colour=PAL.ink2, width=8)
        TY.Text(par, 'statement', size=110, colour=col).draw(s.top, (W / 2 + 150, y), t, w(cue(13, b)), anim='words', anchor='l')
    return s


def sG(t, D):
    """Voyons comment cela se passerait avec cette répartition des chapeaux."""
    s = Shot(t, D)
    S.env(s, 'grid')
    line_with(s, t, C.EXAMPLE, start=w(cue(14, 'repartition')) - 0.1,
              lags=[0, .12, .2, .34, .4, .52, .6, .7, .82, .9])
    return s


SHOTS = [
    (0.0, sA),
    (cue(11, 'peut') - LEAD, sB, 'cut'),
    (cue(11, 'Mais') - LEAD, sC, 'lr'),
    (cue(12, 'Ce') - LEAD, sD, 'rl'),
    (cue(12, 'En revanche') - LEAD, sE, 'cut'),
    (cue(13, 'La solution') - LEAD, sF, 'up'),
    (cue(14, 'Voyons') - LEAD, sG, 'pageturn'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
