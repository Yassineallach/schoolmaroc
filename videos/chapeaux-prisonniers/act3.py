"""Acte 3 : Un par un. Narration clips 15-20.

The narration's example (ch.EXAMPLE), from the back of the line (1) to the front (10, « vous »):
each speaker's own hat is a « ? » until they answer; the hats ahead stay visible (they see them).
"""
import sys
from PIL import Image
from vox import *  # noqa: F401,F403
import vox
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
from style import sfx, ENTER, Shot, kicker
import ch as C

CLIPS = (15, 16, 17, 18, 19, 20)
cue = make_cue(CLIPS)

SC = 0.88                                         # a little smaller than act 2: room above the heads for the words
LCX, LCY = W / 2, H - C.LINE.height * SC / 2 + 36
HATS = C.EXAMPLE
B = {k: C.bubble(f'« {k} »', 56) for k in ('noir', 'blanc')}

# when each prisoner's own hat turns over (act-local seconds)
REVEAL = {0: cue(15, 'trompe'), 1: cue(16, 'blanc'), 2: cue(17, 'noirs', 2), 3: cue(18, 'noir')}
for k, i in enumerate(range(4, 9)):
    REVEAL[i] = cue(19, 'conclut') + [0.0, 0.22, 0.5, 0.66, 0.9][k]
REVEAL[9] = cue(20, 'chose', 1, 'e') + 0.75          # in the silence: the answer is shown, never said
SPEAK = {i: REVEAL[i] + 0.25 for i in range(10)}     # the bubble with the word they say
SAYS = ['noir', 'blanc', 'noir', 'noir', 'blanc', 'blanc', 'blanc', 'blanc', 'blanc', 'noir']
# the parity everyone expects to see, after each « noir » it flips
EXPECT = [(cue(15, 'impair'), 'IMPAIR'), (cue(18, 'pair'), 'PAIR'), (cue(18, 'aussi'), 'IMPAIR')]


def hat_box(i, pad=18):
    x, y = C.hat_at(i, LCX, LCY, SC)
    hw = C.hat_w(i, SC) / 2 + pad
    return (x - hw, y - hw * 0.75, x + hw, y + hw * 0.75)


def line(s, t, current=()):
    """The line with its hats: answered ones shown (turned over on their word), the current
    speakers' own hats as « ? », the rest visible as their neighbours see them."""
    C.put_line(s.mid, LCX, LCY, scale=SC)
    for i in range(10):
        w_ = C.hat_w(i, SC)
        x, y = C.hat_at(i, LCX, LCY, SC)
        rv = w(REVEAL[i])
        if i in current:
            P.flip(s.mid, C.unknown_hat(w_), C.hat(HATS[i], w_), x, y, t, rv, dur=0.7)
            if t >= rv + 0.6:
                hx, _ = C.head(i, LCX, LCY, SC)
                past = rv < -0.5
                A.mark(s.mid, (x + w_ * 0.55, y - w_ * 0.35), 'cross' if i == 0 else 'tick', t, rv + 0.6,
                       size=40, width=8, colour=C.IMPAIR if i == 0 else C.PAIR, sound=not past)
        else:
            C.place_hat(s.mid, i, HATS[i], LCX, LCY, t, 0, scale=SC, drop=False, seed=5)


def say(s, t, i, until=None):
    """The word prisoner i says, in a bubble above their head."""
    at = w(SPEAK[i])
    if t < at:
        return
    x, y = C.hat_at(i, LCX, LCY, SC)
    bx = x + 150 if i < 7 else x - 130
    by = max(95, y - C.hat_w(i, SC) * 0.6 - 80)
    C.pop_in(s.top, B[SAYS[i]], bx, by, t, at, until=until)


def expect(s, t):
    """Top right: the agreement, and the parity everyone now expects to see."""
    card_off = 117.95 - 114.86 - vox._SCENE_START          # the channel's like card holds this corner until then
    if t >= card_off:
        TY.Text('« noir » : impair  ·  « blanc » : pair', 'label', size=26, colour=PAL.ink2).draw(
            s.hud, (1860, 120), t, card_off, anim='words', anchor='r', sound=False)
    cur = None
    for k, (at, v) in enumerate(EXPECT):
        if t >= w(at) - 0.01 or (k == 0 and False):
            cur = (k, at, v)
    if cur is None:
        return
    k, at, v = cur
    TY.Text('ON ATTEND', 'label', size=24, colour=PAL.muted).draw(s.hud, (1860, 172), t, -1.0, anim='words', anchor='r', sound=False)
    TY.Text(v, 'subhead', size=72, colour=C.IMPAIR if v == 'IMPAIR' else C.PAIR).draw(
        s.hud, (1860, 205), t, w(at), anim='split' if k else 'scale', anchor='r', sound=k > 0)


def look(s, t, i, start, until=None, alpha=0.16):
    """Prisoner i's line of sight over the heads in front."""
    e = C.head(i, LCX, LCY, SC)
    f = C.head(9, LCX, LCY, SC)
    eye = (e[0] + C.FIGS[i]['hw'] * 0.38 * SC, e[1] + C.FIGS[i]['hw'] * 0.45 * SC)
    C.cone(s.top, eye, f[0] + 110, e[1] - 140, f[1] + 90, t, start, colour=PAL.ink2, alpha=alpha, until=until)


def count(s, t, ahead, start, step=0.28, colour=None):
    """Ring the black hats seen ahead, numbering them 1, 2, 3 on the spoken number."""
    for n, j in enumerate(ahead):
        at = start + n * step
        A.ring(s.mid, hat_box(j), t, at, colour=colour or PAL.ink, width=7, seed=40 + j)
        x0, y0, x1, y1 = hat_box(j)
        if t >= at:
            TY.Text(str(n + 1), 'subhead', size=46, colour=colour or PAL.ink).draw(s.top, ((x0 + x1) / 2, y0 - 70), t, at, anim='scale', anchor='m', sound=False)


BLACK = [i for i in range(10) if HATS[i] == 'noir']


def ahead(i):
    return [j for j in BLACK if j > i]


# ------------------------------------------------------------------ scenes
def sA(t, D):
    """Le plus grand des captifs voit trois chapeaux noirs devant lui. Il dit donc « noir », pour signaler
    aux autres qu'il en voit un nombre impair."""
    s = Shot(t, D)
    S.env(s, 'grid')
    # act 2 ends on the full-size line: start framed exactly like it, then ease back to make room above the heads
    c2y = H - C.LINE.height / 2 + 40
    k = P.ease_io((t - 0.35) / 1.3)
    z0 = 1 / SC
    s.zoom = z0 + (1 - z0) * k
    ly0 = LCY - (c2y - H / 2) * SC
    s.lx, s.ly = W / 2, ly0 + (H / 2 - ly0) * k
    C.put_line(s.mid, LCX, LCY, scale=SC)
    for i in range(1, 10):
        C.place_hat(s.mid, i, HATS[i], LCX, LCY, t, 0, scale=SC, drop=False, seed=5)
    w0 = C.hat_w(0, SC)
    x0, y0 = C.hat_at(0, LCX, LCY, SC)
    P.flip(s.mid, C.hat(HATS[0], w0), C.unknown_hat(w0), x0, y0, t, 0.5, dur=0.6)   # his own hat: he cannot see it
    look(s, t, 0, w(cue(15, 'voit')))
    count(s, t, ahead(0), w(cue(15, 'trois')), colour=C.IMPAIR)
    at = w(cue(15, 'noir'))
    if t >= at:
        x, y = C.hat_at(0, LCX, LCY, SC)
        C.pop_in(s.top, B['noir'], x + 150, max(95, y - C.hat_w(0, SC) * 0.6 - 70), t, at)
    expect(s, t)
    kicker(s.hud, t, 3, 'Un par un', start=0.4)
    return s


def sB(t, D):
    """Il se trompe sur la couleur de son propre chapeau, mais ce n'est pas grave : le groupe a droit à une erreur."""
    s = Shot(t, D)
    S.env(s, 'grid')
    hx, hy = C.head(0, LCX, LCY, SC)
    s.camera(1.0, 1.0)
    s.push(w(cue(15, 'trompe')) - 0.3, 0.30, (hx + 120, hy + 80), dur=1.4)
    line(s, t, current=(0,))
    expect(s, t)
    return s


def sC(t, D):
    """La deuxième prisonnière voit elle aussi un nombre impair de chapeaux noirs. Elle en conclut que le sien
    est blanc, et répond juste."""
    s = Shot(t, D)
    S.env(s, 'grid')
    line(s, t, current=(0, 1))
    look(s, t, 1, w(cue(16, 'voit')))
    count(s, t, ahead(1), w(cue(16, 'impair')), step=0.18, colour=C.IMPAIR)
    say(s, t, 1)
    expect(s, t)
    return s


def sD(t, D):
    """Le troisième prisonnier, lui, voit un nombre pair de chapeaux noirs. Il sait donc que son chapeau est
    forcément l'un des chapeaux noirs que les deux premiers avaient vus."""
    s = Shot(t, D)
    S.env(s, 'grid')
    line(s, t, current=(0, 1, 2))
    look(s, t, 2, w(cue(17, 'voit')), until=w(cue(17, 'forcement')))
    count(s, t, ahead(2), w(cue(17, 'pair')), step=0.25, colour=C.PAIR)
    if t >= w(cue(17, 'pair')) + 0.5:
        TY.Text('PAIR', 'subhead', size=56, colour=C.PAIR).draw(s.top, (C.head(2, LCX, LCY, SC)[0] + 40, 330), t,
                                                               w(cue(17, 'pair')) + 0.5, anim='scale', anchor='l', sound=False,
                                                               until=w(cue(17, 'forcement')))
    for k, i in enumerate((0, 1)):                    # the first two saw his hat among the black ones
        look(s, t, i, w(cue(17, 'premiers')) + 0.2 * k, alpha=0.08)
    A.ring(s.mid, hat_box(2, 26), t, w(cue(17, 'forcement')), colour=C.IMPAIR, width=8, seed=77)
    say(s, t, 2)
    expect(s, t)
    return s


def sE(t, D):
    """La quatrième prisonnière l'entend et comprend qu'elle doit maintenant s'attendre à voir un nombre pair
    de chapeaux noirs, puisque l'un d'eux se trouvait derrière elle."""
    s = Shot(t, D)
    S.env(s, 'grid')
    line(s, t, current=(0, 1, 2, 3))
    say(s, t, 2, until=w(cue(18, 'derriere')) + 1.5)
    x2, y2 = C.hat_at(2, LCX, LCY, SC)
    x3, y3 = C.head(3, LCX, LCY, SC)
    A.arrow(s.top, (x3 + 20, y3 - 150), (x2 + 30, y2 - C.hat_w(2, SC) * 0.55), t, w(cue(18, 'derriere')), bend=-0.5,
            colour=C.PAIR, width=7)
    expect(s, t)
    return s


def sF(t, D):
    """Or, elle n'en voit qu'un. Elle en déduit que son chapeau est noir, lui aussi."""
    s = Shot(t, D)
    S.env(s, 'grid')                                  # locked off: her line of sight, then her hat
    line(s, t, current=(0, 1, 2, 3))
    look(s, t, 3, ENTER, until=w(cue(18, 'deduit')))
    count(s, t, ahead(3), w(cue(18, "'un.")), colour=C.IMPAIR)
    say(s, t, 3)
    expect(s, t)
    return s


def sG(t, D):
    """Elle en déduit que son chapeau est noir, lui aussi."""
    s = Shot(t, D)
    S.env(s, 'grid')
    line(s, t, current=(0, 1, 2, 3))
    say(s, t, 3)
    expect(s, t)
    return s


def sH(t, D):
    """Les prisonniers cinq à neuf s'attendent chacun à voir un nombre impair de chapeaux noirs. C'est bien ce
    qu'ils voient, et ils en concluent que leur chapeau est blanc."""
    s = Shot(t, D)
    S.env(s, 'grid')
    hx4, _ = C.head(4, LCX, LCY, SC)
    hx8, _ = C.head(8, LCX, LCY, SC)
    s.camera(1.18, 1.18, (hx4 + 200, 560), (hx8 - 100, 560))
    line(s, t, current=tuple(range(9)))
    count(s, t, ahead(4), w(cue(19, 'voient')), colour=C.IMPAIR)
    expect(s, t)
    return s


def sI(t, D):
    """Tout repose maintenant sur vous, en tête de file."""
    s = Shot(t, D)
    S.env(s, 'charcoal')
    im, _ = C.figure(9, 1.6)
    cx, cy = W / 2 + 120, H - im.height / 2 + 60
    from scipy import ndimage                         # the drawing is ink lines on transparent paper:
    sil = ndimage.binary_fill_holes(np.asarray(im.split()[-1]) > 40)   # give the figure its paper back on the dark ground
    sil = ndimage.binary_closing(sil, iterations=3)
    sil = ndimage.binary_fill_holes(sil)
    lit = Image.new('RGBA', im.size, PAL.light + (255,))
    lit.putalpha(Image.fromarray((sil * 255).astype(np.uint8)))
    base = Image.new('RGBA', im.size, (0, 0, 0, 0))
    base.alpha_composite(lit)
    base.alpha_composite(im)
    P.put(s.mid, base, cx, cy, shadow=False)
    f = C.FIGS[9]
    w_ = C.hat_w(9) * 1.6
    hx = cx + (f['hx'] - (f['x0'] + f['x1']) / 2) * 1.6
    hy = cy - im.height / 2 + f['top'] * 1.6
    P.put(s.mid, C.unknown_hat(w_), hx, hy + 0.22 * w_ - C.hat('noir', w_).height / 2, sh_op=0.2)
    A.spotlight(s.mid, (hx, H / 2 + 80), 420, t, ENTER, dim=0.35, sound=False)
    return s


def sJ(t, D):
    """Si le neuvième prisonnier a vu un nombre impair de chapeaux noirs, cela ne peut signifier qu'une chose."""
    s = Shot(t, D)
    S.env(s, 'grid')
    hx, hy = C.head(9, LCX, LCY, SC)
    s.camera(1.0, 1.0)                                # locked off: the hat turning over is the only move
    line(s, t, current=tuple(range(10)))
    look(s, t, 8, w(cue(20, 'vu')), until=w(cue(20, 'chose')) + 0.3)
    expect(s, t)
    say(s, t, 9)
    return s


SHOTS = [
    (0.0, sA),
    (cue(15, 'Il se') - LEAD, sB, 'cut'),
    (cue(16, 'La') - LEAD, sC, 'cut'),
    (cue(17, 'Le') - LEAD, sD, 'cut'),
    (cue(18, 'La') - LEAD, sE, 'cut'),
    (cue(18, 'Or') - LEAD, sF, 'cut'),
    (cue(19, 'Les') - LEAD, sH, 'cut'),
    (cue(20, 'Tout') - LEAD, sI, ('circle', {'at': (1640, 560)})),
    (cue(20, 'Si') - LEAD, sJ, 'cut'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
