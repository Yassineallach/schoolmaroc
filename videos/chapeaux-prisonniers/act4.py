"""Acte 4 : Toujours. Narration clips 21-23, then the channel outro."""
import sys
import math
from PIL import Image
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
import brand
from style import sfx, ENTER, Shot, kicker, caption
import ch as C

CLIPS = (21, 22, 23)
cue = make_cue(CLIPS)
HOLD = 3.0                                          # the empty plate holds in silence before the outro

LCX, LCY = W / 2, H - C.LINE.height / 2 + 40       # the line, full size, as at the end of act 3's sJ... then as in act 2
FREE = C.plate('G05', 'les dix sortent, libres')
TABLE = C.drawing('G02', 1920, 'la table extraterrestre')
PLATE_C = (0.48, 0.55)                              # the empty plate in G02, as fractions

# three other line-ups « quelle que soit la répartition »: each one resolves the same way
OTHERS = [['noir', 'noir', 'blanc', 'noir', 'blanc', 'noir', 'noir', 'blanc', 'blanc', 'noir'],
          ['blanc', 'blanc', 'blanc', 'noir', 'noir', 'blanc', 'noir', 'blanc', 'noir', 'blanc'],
          ['noir', 'blanc', 'noir', 'blanc', 'blanc', 'blanc', 'noir', 'noir', 'blanc', 'noir']]


def hats(s, t, colours, start=None, stagger=0.05):
    for i in range(10):
        if start is None:
            C.place_hat(s.mid, i, colours[i], LCX, LCY, t, 0, drop=False, seed=5)
        else:
            C.place_hat(s.mid, i, colours[i], LCX, LCY, t, start + stagger * i + (0.03 if i % 3 == 1 else 0), seed=5 + int(start))


def sA(t, D):
    """Cette stratégie fonctionne quelle que soit la répartition des chapeaux."""
    s = Shot(t, D)
    S.env(s, 'grid')
    C.put_line(s.mid, LCX, LCY)
    turns = [w(cue(21, 'quelle')), w(cue(21, 'repartition'))]
    for i in range(10):                               # the hats turn over to a new line-up, twice
        w_ = C.hat_w(i)
        x, y = C.hat_at(i, LCX, LCY)
        lag = [0, .06, .1, .17, .2, .27, .31, .38, .42, .47][i]
        if t < turns[0] + lag:
            P.put(s.mid, C.hat(OTHERS[0][i], w_), x, y, sh_op=0.18)
        elif t < turns[1] + lag:
            P.flip(s.mid, C.hat(OTHERS[0][i], w_), C.hat(OTHERS[1][i], w_), x, y, t, turns[0] + lag, dur=0.45)
        else:
            P.flip(s.mid, C.hat(OTHERS[1][i], w_), C.hat(OTHERS[2][i], w_), x, y, t, turns[1] + lag, dur=0.45)
    kicker(s.hud, t, 4, 'Toujours', start=0.4)
    return s


def coin(s, t, start, stop):
    """Prisoner 1's own hat spins like a coin: black, white, black..."""
    w_ = C.hat_w(0)
    x, y = C.hat_at(0, LCX, LCY)
    if t < start:
        P.put(s.mid, C.unknown_hat(w_), x, y, sh_op=0.18)
        return
    if t >= stop:
        P.flip(s.mid, C.hat('blanc', w_), C.unknown_hat(w_), x, y, t, stop, dur=0.4)
        return
    ph = (t - start) / 0.36
    face = C.hat('noir' if int(ph) % 2 == 0 else 'blanc', w_)
    sx = abs(math.cos(math.pi * (ph % 1)))
    im = face.resize((max(2, int(face.width * max(sx, 0.05))), face.height), Image.LANCZOS)
    P.put(s.mid, im, x, y, sh_op=0.15)
    for n in range(int((stop - start) / 0.36) + 1):                 # a soft flip on each turn
        at = start + n * 0.36
        if abs(t - at) < 1 / 60:
            sfx('flip', at, x, gain=0.35)


def sB(t, D):
    """Le premier prisonnier a une chance sur deux de se tromper sur son propre chapeau..."""
    s = Shot(t, D)
    S.env(s, 'grid')                                  # locked off: only his hat moves
    C.put_line(s.mid, LCX, LCY)
    for i in range(1, 10):
        C.place_hat(s.mid, i, C.EXAMPLE[i], LCX, LCY, t, 0, drop=False, seed=5)
    coin(s, t, w(cue(21, 'chance')) - 0.2, w(cue(21, 'chapeau')) + 0.3)
    hx, hy = C.head(0, LCX, LCY)
    TY.Text('1 sur 2', 'subhead', size=72, colour=PAL.accent).draw(s.top, (hx + 140, hy - 120), t, w(cue(21, 'deux')),
                                                                  anim='scale', anchor='l')
    return s


def sC(t, D):
    """... mais l'information de parité qu'il transmet permet à tous les autres de deviner le leur avec une
    certitude absolue."""
    s = Shot(t, D)
    S.env(s, 'grid')
    C.put_line(s.mid, LCX, LCY)
    C.place_hat(s.mid, 0, '?', LCX, LCY, t, 0, drop=False, seed=5)
    go = w(cue(21, 'transmet'))
    pts = []
    for i in (0, 3, 6, 9):
        x, y = C.hat_at(i, LCX, LCY)
        pts.append((x, y - C.hat_w(i) * 0.5 - 50))
    A.connect(s.top, pts, t, go, dur=1.4, colour=PAL.ink2, dashed=True, arrowhead=True)
    for i in range(1, 10):
        x, y = C.hat_at(i, LCX, LCY)
        w_ = C.hat_w(i)
        at = w(cue(21, 'deviner')) + 0.16 * (i - 1)
        P.flip(s.mid, C.unknown_hat(w_), C.hat(C.EXAMPLE[i], w_), x, y, t, at, dur=0.5)
        if t >= at + 0.45:
            A.mark(s.mid, (x + w_ * 0.55, y - w_ * 0.35), 'tick', t, at + 0.45, size=40, width=8, colour=C.PAIR,
                   sound=i % 3 == 1)
    return s


# the rule as a loop (a non-linear path: the one place a diagram explains better than an image)
NODES = {'attend': ((330, 360), 'On attend', 'pair ou impair'),
         'compte': ((960, 360), 'On compte', 'les chapeaux noirs'),
         'match': ((1640, 360), 'Ça correspond ?', ''),
         'noir': ((1640, 760), '« noir »', 'son chapeau est noir'),
         'flip': ((330, 760), 'Le suivant', 'inverse la parité')}


def node(s, t, key, at, colour=None):
    (x, y), title, sub = NODES[key]
    TY.Text(title, 'statement', size=64, colour=colour or INK).draw(s.top, (x, y - 50), t, at, anim='words', anchor='m')
    if sub:
        TY.Text(sub, 'caption', size=40, colour=PAL.ink2).draw(s.top, (x, y + 40), t, at + 0.25, anim='words', anchor='m', sound=False)


def sD(t, D):
    """Chacun commence par s'attendre à voir un nombre pair ou impair de chapeaux de la couleur convenue. Si ce
    qu'il compte ne correspond pas, c'est que son propre chapeau est de cette couleur. Et chaque fois que cela
    arrive, la personne suivante inverse la parité qu'elle s'attend à voir."""
    s = Shot(t, D)
    S.env(s, 'paper')
    node(s, t, 'attend', ENTER + 0.1)
    A.arrow(s.top, (560, 330), (740, 330), t, w(cue(22, 'compte')) - 0.35, bend=0.0, colour=PAL.ink2, width=7)
    node(s, t, 'compte', w(cue(22, 'compte')))
    A.arrow(s.top, (1160, 330), (1350, 330), t, w(cue(22, 'correspond')) - 0.3, bend=0.0, colour=PAL.ink2, width=7)
    node(s, t, 'match', w(cue(22, 'correspond')))
    A.arrow(s.top, (1640, 420), (1640, 620), t, w(cue(22, 'pas')), bend=0.0, colour=C.IMPAIR, width=8)
    if t >= w(cue(22, 'pas')):
        TY.Text('non', 'label', size=34, colour=C.IMPAIR).draw(s.top, (1680, 520), t, w(cue(22, 'pas')), anim='words', anchor='l', sound=False)
    node(s, t, 'noir', w(cue(22, 'couleur')))
    A.arrow(s.top, (1380, 740), (580, 740), t, w(cue(22, 'arrive')), bend=0.0, colour=C.IMPAIR, width=8)
    node(s, t, 'flip', w(cue(22, 'suivante')))
    A.arrow(s.top, (330, 640), (330, 470), t, w(cue(22, 'inverse')) + 0.3, bend=0.0, colour=C.IMPAIR, width=8)
    return s


def sE(t, D):
    """Voilà, vous êtes libres. On dirait que ces extraterrestres..."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, FREE, t, -2.0, ken=(1.0, 1.06), focus=(0.5, 0.5), focus_to=(0.5, 0.42), fade=0.01)
    caption(s.hud, 'Illustration', t, 0.8, corner='bl')
    return s


def sF(t, D):
    """... vont devoir rester sur leur faim, ou aller enlever des créatures un peu moins logiques."""
    s = Shot(t, D)
    S.env(s, 'paper')
    fx = W / 2 + (PLATE_C[0] - 0.5) * TABLE.width
    fy = H / 2 + (PLATE_C[1] - 0.5) * TABLE.height
    s.camera(1.0, 1.16, (W / 2, H / 2), (fx, fy))     # a slow push to the empty plate, then it holds
    P.put(s.mid, TABLE, W / 2, H / 2, shadow=False)
    return s


SHOTS = [
    (0.0, sA),
    (cue(21, 'Le premier') - LEAD, sB, 'cut'),
    (cue(21, 'mais') - LEAD, sC, 'cut'),
    (cue(22, 'Chacun') - LEAD, sD, 'up'),
    (cue(23, 'Voila') - LEAD, sE, ('circle', {'at': (W / 2, H / 2)})),
    (cue(23, 'rester') - LEAD, sF, 'lr'),
]
if brand.CFG['outro']['enabled']:
    SHOTS.append((cue.total + HOLD, brand.outro_scene, 'up'))
END = cue.total + HOLD + brand.outro_seconds()


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
