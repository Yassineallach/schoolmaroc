"""Acte 1 : Le test. Narration clips 1-10."""
import sys
import math
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
from style import sfx, ENTER, Shot, words, tag, kicker, caption
import ch as C

CLIPS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
cue = make_cue(CLIPS)

# ---- drawings (PROMPTS.md); a labelled placeholder until uploaded
HALL = C.plate('G01', 'la salle des ravisseurs')
GUARD = (0.80, 0.33)                          # the guard's horn in G01, as fractions of the plate
TABLE = C.drawing('G02', 1920, 'la table extraterrestre')     # every drawing full screen, no frame
CUTLERY = (0.84, 0.56)                        # the fork and knife in G02, as fractions
HUDDLE = C.drawing('G04', 1920, 'les dix se concertent')

LCX, LCY = W / 2, H - C.LINE.height / 2 + 40  # the line of ten, full width, feet near the bottom edge
HATS_RANDOM = ['noir', 'blanc', 'blanc', 'noir', 'blanc', 'noir', 'noir', 'blanc', 'blanc', 'blanc']


# ---- the aliens' law, in their own script (drawn: there is nothing to photograph)
def _glyph(d, x, y, s, r):
    k = r.integers(0, 5)
    col = INK + (255,)
    if k == 0:
        d.ellipse((x, y, x + s, y + s), outline=col, width=4)
        d.line((x + s / 2, y + s, x + s / 2, y + s * 1.4), fill=col, width=4)
    elif k == 1:
        d.line((x, y + s, x + s / 2, y, x + s, y + s), fill=col, width=4)
        d.ellipse((x + s / 2 - 4, y + s * 0.55, x + s / 2 + 4, y + s * 0.55 + 8), fill=col)
    elif k == 2:
        d.arc((x, y, x + s, y + s), 200, 520, fill=col, width=4)
        d.line((x + s * 0.2, y + s / 2, x + s * 0.8, y + s / 2), fill=col, width=4)
    elif k == 3:
        d.line((x, y, x + s, y), fill=col, width=4)
        d.line((x + s / 2, y, x + s / 2, y + s), fill=col, width=4)
        d.ellipse((x + s - 8, y + s - 8, x + s, y + s), fill=col)
    else:
        d.rectangle((x + s * 0.15, y + s * 0.15, x + s * 0.85, y + s * 0.85), outline=col, width=4)
        d.line((x + s * 0.15, y + s * 0.85, x + s * 0.85, y + s * 0.15), fill=col, width=3)


def _law():
    """The law, written straight on the screen in the aliens' script (no sheet)."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = np.random.default_rng(1977)
    rows = []
    x = 200
    for k in range(6):                                         # the title, larger
        _glyph(d, x, 90, 84, r)
        x += 124
    rows.append((180, 70, x, 210))
    d.line((200, 230, W - 200, 230), fill=INK + (255,), width=4)
    y = 290
    for row in range(8):
        x, n = 200, r.integers(14, 22)
        for k in range(n):
            if x > W - 260:
                break
            _glyph(d, x, y, 52, r)
            x += 72 + (22 if r.random() < 0.18 else 0)
        rows.append((180, y - 16, x + 10, y + 70))
        y += 96
    return layer, rows


LAW, LAW_ROWS = _law()


def law_box(i):
    x0, y0, x1, y1 = LAW_ROWS[i]
    return (x0, y0, x1, y1)


def _dossier():
    """Ten empty boxes, one per prisoner, straight on the screen (no card)."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(10):
        cx = 420 + (i % 5) * 270
        cy = 380 + (i // 5) * 330
        d.rectangle((cx - 80, cy - 80, cx + 80, cy + 80), outline=INK + (255,), width=8)
        d.text((cx, cy + 135), str(i + 1), font=F_TYPE(48), fill=PAL.ink2 + (255,), anchor='mm')
    return layer


DOSSIER = _dossier()


def _wave(amp):
    im = C.bubble('                ', 56)
    d = ImageDraw.Draw(im)
    w = im.width
    h0 = int(56 * 1.9) / 2 + 4
    pts = []
    for k in range(240):
        x = 44 + (w - 96) * k / 239
        env = math.sin(math.pi * k / 239)
        pts.append((x, h0 + amp * env * math.sin(k / 239 * 2 * math.pi * 5.5) * (0.6 + 0.4 * math.sin(k / 20))))
    d.line(pts, fill=INK + (255,), width=4)
    return im


WAVE_SOFT, WAVE_LOUD = _wave(10), _wave(30)
B_NOIR, B_BLANC = C.bubble('« noir »', 64), C.bubble('« blanc »', 64)
E_NOIR, E_BLANC = C.bubble('« noir »', 64, blank=True), C.bubble('« blanc »', 64, blank=True)


def set_cam(s, z, F):
    s.zoom = z
    s.lx, s.ly = F[0] - (F[0] - W / 2) / z, F[1] - (F[1] - H / 2) / z


# ------------------------------------------------------------------ scenes
def sA(t, D):
    """Vous et neuf autres personnes avez été capturés par des extraterrestres d'une intelligence
    redoutable."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, HALL, t, -0.05, ken=(1.0, 1.10), focus=(0.5, 0.5), focus_to=(0.45, 0.62), fade=0.01)   # on screen from frame 0
    caption(s.hud, 'Illustration', t, 1.2, corner='bl', on_dark=True)
    return s


def sB(t, D):
    """Ils trouvent les humains plutôt appétissants..."""
    s = Shot(t, D)
    S.env(s, 'theme')
    s.camera(1.0, 1.05, (W / 2, H / 2), (W / 2, 520))
    P.put(s.mid, TABLE, W / 2, H / 2, shadow=False)
    kicker(s.hud, t, 1, 'Le test', start=0.5)
    caption(s.hud, 'Illustration', t, 1.0, corner='bl')
    return s


def sC(t, D):
    """... mais leur civilisation interdit de manger des êtres très logiques et capables de coopérer."""
    s = Shot(t, D)
    S.env(s, 'archive')
    s.camera(1.0, 1.04, (W / 2, H / 2), (W / 2, 600))
    for k, (x0, y0, x1, y1) in enumerate(LAW_ROWS):           # the law writes itself, row by row
        at = ENTER + [0.0, 0.35, 0.5, 0.62, 0.8, 0.9, 1.05, 1.2, 1.3][k]
        u = P.ease_io((t - at) / 0.45)
        if u > 0:
            xr = int(x0 + (x1 - x0) * u)
            s.mid.alpha_composite(LAW.crop((x0, y0, xr, y1)), (x0, y0))
    A.ring(s.mid, law_box(5), t, w(cue(1, 'logiques')), seed=21)
    A.ring(s.mid, law_box(7), t, w(cue(1, 'cooperer')), seed=22)
    return s


def sD(t, D):
    """Problème : ils ne savent pas si vous entrez dans cette catégorie."""
    s = Shot(t, D)
    S.env(s, 'cream')                                          # locked off: no camera move
    C.put_line(s.mid, LCX, LCY)
    A.mark(s.top, (W / 2 + 40, 150), 'question', t, w(cue(1, 'savent')), size=170, width=13)
    caption(s.hud, 'Illustration', t, 0.6, corner='bl')
    return s


def sE(t, D):
    """Ils décident donc de vous faire passer un test."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.03)
    P.put(s.mid, DOSSIER, W / 2, H / 2, shadow=False)
    P.stamp_hit(s.mid, 'TEST', W / 2, H / 2 - 20, t, w(cue(1, 'test')), size=170, ang=-9, shot=s)
    return s


def sF(t, D):
    """Grâce à son traducteur universel, le garde extraterrestre vous annonce ceci :"""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, HALL, t, -0.05, ken=(1.04, 1.04), focus=(0.5, 0.5), fade=0.01)
    gx, gy = W / 2 + (GUARD[0] - 0.5) * W * 1.04, H / 2 + (GUARD[1] - 0.5) * H * 1.04
    s.zoom_to((gx - 330, gy - 190, gx + 330, gy + 190), w(cue(2, 'traducteur')), dur=2.2, fill=0.9)
    caption(s.hud, 'Illustration', t, 0.6, corner='bl', on_dark=True)
    return s


ORDER = [6, 2, 8, 0, 4, 9, 1, 5, 3, 7]                         # where each slot's figure stands before « rangés »


def sG(t, D):
    """Vous allez être placés en file indienne, tournés vers l'avant et rangés par taille, de sorte
    que chacun voie toutes les personnes devant lui. Vous ne pourrez ni vous retourner ni sortir du rang."""
    s = Shot(t, D)
    S.env(s, 'grid')
    sort = w(cue(3, 'ranges'))
    slot_x = [C.figure(j)[1] for j in range(10)]
    for slot, i in enumerate(ORDER):                           # figure i starts in `slot`, then walks to slot i
        im, _ = C.figure(i)
        lag = [0.0, 0.25, 0.1, 0.4, 0.05, 0.3, 0.15, 0.5, 0.2, 0.35][i]
        u = P.ease_io((t - sort - lag) / 0.9)
        x = LCX + slot_x[slot] + (slot_x[i] - slot_x[slot]) * u
        hop = -38 * math.sin(math.pi * u)
        P.put(s.mid, im, x, LCY + hop, sh_op=0.12)
        if abs(t - (sort + lag)) < 1 / 30:
            sfx('slide', sort + lag, x, gain=0.25)
    e = C.head(0, LCX, LCY)
    f = C.head(9, LCX, LCY)
    eye = (e[0] + C.FIGS[0]['hw'] * 0.38, e[1] + C.FIGS[0]['hw'] * 0.45)
    C.cone(s.top, eye, f[0] + 90, e[1] - 30, f[1] + 230, t, w(cue(3, 'voie')), until=w(cue(3, 'retourner')) - 0.2)
    hx, hy = C.head(4, LCX, LCY)
    A.arrow(s.top, (hx + 70, hy - 40), (hx - 120, hy - 60), t, w(cue(3, 'retourner')) - 0.1, bend=0.6, colour=PAL.ink2, width=7)
    A.strike(s.top, (hx - 140, hy - 110, hx + 90, hy + 10), t, w(cue(3, 'retourner')) + 0.35, scribble=False)
    hx, hy = C.head(7, LCX, LCY)
    A.arrow(s.top, (hx, LCY + 120), (hx + 30, LCY + 330), t, w(cue(3, 'sortir')) - 0.1, bend=0.3, colour=PAL.ink2, width=7)
    A.strike(s.top, (hx - 80, LCY + 150, hx + 120, LCY + 320), t, w(cue(3, 'sortir')) + 0.35)
    f9x, _ = C.head(9, LCX, LCY)
    tag(s.hud, (f9x, LCY + C.LINE.height / 2 + 50), 'vous', 40, t, w(cue(3, 'Vous', 2)), bg=INK, fg=CREAM)
    caption(s.hud, 'Illustration', t, 0.8, corner='bl')
    return s


def sH(t, D):
    """Chacun portera sur la tête un chapeau noir ou blanc, attribué au hasard, et je ne vous dirai pas
    combien il y en a de chaque couleur."""
    s = Shot(t, D)
    S.env(s, 'theme')
    s.camera(1.0, 1.0)                                         # locked off: only the hats move
    C.put_line(s.mid, LCX, LCY)
    start = w(cue(3, 'chapeau'))
    lags = [0.0, 0.35, 0.5, 0.95, 1.1, 1.5, 1.75, 2.0, 2.45, 2.6]
    for i in range(10):
        C.place_hat(s.mid, i, HATS_RANDOM[i], LCX, LCY, t, start + lags[i], seed=3)
    TY.Text('? noirs · ? blancs', 'subhead', size=60).draw(s.hud, (1840, 70), t, w(cue(3, 'combien')),
                                                            anim='words', anchor='r', cues=[w(cue(3, 'combien'))] * 5)
    return s


def sI(t, D):
    """À mon signal, chacun devra deviner la couleur de son propre chapeau, en commençant par le
    dernier de la file et en remontant vers l'avant."""
    s = Shot(t, D)
    S.env(s, 'grid')
    C.put_line(s.mid, LCX, LCY)
    turn = w(cue(4, 'deviner'))
    for i in range(10):
        w_ = C.hat_w(i)
        x, y = C.hat_at(i, LCX, LCY)
        at = turn + [0.0, 0.08, 0.2, 0.26, 0.35, 0.47, 0.52, 0.66, 0.71, 0.83][i]
        P.flip(s.mid, C.hat(HATS_RANDOM[i], w_), C.unknown_hat(w_), x, y, t, at, dur=0.6)
    hx, hy = C.head(0, LCX, LCY)
    A.ring(s.top, (hx - 90, hy - 120, hx + 90, LCY + C.LINE.height / 2 + 10), t, w(cue(4, 'dernier')), until=w(cue(4, 'remontant')) + 1.6)
    go = w(cue(4, 'remontant'))
    y = LCY + C.LINE.height / 2 + 46
    x0, _ = C.head(0, LCX, LCY)
    x9, _ = C.head(9, LCX, LCY)
    A.arrow(s.top, (x0 - 40, y + 50), (x9 + 70, y + 50), t, go, dur=1.3, bend=0.0, colour=PAL.ink2, width=6)
    for i in range(10):
        xi, _ = C.head(i, LCX, LCY)
        u = (xi - x0 + 40) / (x9 - x0 + 110)
        if t >= go + 1.3 * u:
            TY.Text(str(i + 1), 'label', size=34).draw(s.top, (xi, y), t, go + 1.3 * u, anim='scale', anchor='m', sound=False)
    return s


def sJ(t, D):
    """Et n'essayez pas de dire autre chose que « noir » ou « blanc », ni de faire passer un signal
    autrement, par l'intonation ou le volume de la voix..."""
    s = Shot(t, D)
    S.env(s, 'charcoal')
    s.camera(1.0, 1.04)
    for full, empty, x, word, lag in ((B_NOIR, E_NOIR, 640, 'noir', 0.05), (B_BLANC, E_BLANC, 1280, 'blanc', 0.3)):
        said = w(cue(4, word))
        C.pop_in(s.mid, empty if t < said else full, x, 380, t, ENTER + lag)   # empty from the cut, the word on its cue
        if abs(t - said) < 1 / 30:
            sfx('type', said, x)
    loud = w(cue(4, 'volume'))
    wave = WAVE_SOFT if t < loud else WAVE_LOUD
    C.pop_in(s.mid, wave, 960, 720, t, w(cue(4, "'intonation")))
    bx0, by0 = 960 - wave.width / 2, 720 - wave.height / 2
    A.strike(s.mid, (bx0 - 20, by0 + 10, bx0 + wave.width + 20, by0 + wave.height - 30), t, w(cue(4, 'voix')), width=12, scribble=True)
    return s


def sK(t, D):
    """... vous seriez tous dévorés sur-le-champ."""
    s = Shot(t, D)
    S.env(s, 'paper')                                          # locked off on the cutlery
    cx, cy = W / 2, H / 2
    P.put(s.mid, TABLE, cx, cy, shadow=False)
    fx = cx + (CUTLERY[0] - 0.5) * TABLE.width
    fy = cy + (CUTLERY[1] - 0.5) * TABLE.height
    set_cam(s, 2.0, (fx, fy))
    return s


def sL(t, D):
    """Si au moins neuf d'entre vous devinent juste, vous serez tous épargnés."""
    s = Shot(t, D)
    S.env(s, 'accent')
    TY.big_number(s.top, (W / 2, 250), '9', t, w(cue(5, 'neuf')), role='stat', colour=S.ink(s), accent_bar=False, dur=0.9)
    TY.Text('sur 10', 'statement', colour=S.ink(s)).draw(s.top, (W / 2, 640), t, w(cue(5, 'neuf')) + 0.5, anim='words', anchor='m')
    return s


def sM(t, D):
    """Vous avez cinq minutes pour vous concerter et mettre au point un plan."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.04, (W / 2, H / 2), (760, 520))
    P.put(s.mid, HUDDLE, W / 2, H / 2, shadow=False)
    at = w(cue(5, 'cinq'))
    if t >= at:                                                # the five minutes start running, no card
        left = max(0, 300 - int(t - at))
        TY.Text(f'{left // 60}:{left % 60:02d}', 'stat', size=120, colour=PAL.accent).draw(
            s.hud, (1700, 70), t, at, anim='scale', anchor='m', sound=False)
        if abs(t - at) < 1 / 30:
            sfx('type', at, 1700)
    caption(s.hud, 'Illustration', t, 0.9, corner='bl')
    return s


HATS_NEXT = ['blanc', 'noir', 'noir', 'blanc', 'blanc', 'noir', 'blanc', 'noir', 'blanc', 'blanc']


def sN(t, D):
    """Ensuite, je vous aligne, je distribue les chapeaux, et on commence."""
    s = Shot(t, D)
    S.env(s, 'theme')
    P.slide(s.mid, C.LINE, (-900, LCY), (LCX, LCY), t, ENTER, dur=1.0, rot=0, key='line')
    start = w(cue(5, 'chapeaux')) - 0.25
    for i in range(10):
        C.place_hat(s.mid, i, HATS_NEXT[i], LCX, LCY, t, start + [0, .1, .16, .3, .37, .5, .58, .66, .8, .86][i], seed=5)
    if t >= w(cue(5, 'commence')):
        s.push(w(cue(5, 'commence')), 0.06, (W / 2, 420))
    return s


def sO(t, D):
    """Quelle stratégie garantirait de sauver tout le monde ?"""
    s = Shot(t, D)
    S.env(s, 'cream')
    S.type_page(s, 'Quelle stratégie ?', t, ENTER, role='statement', size=110,
                cues=[w(cue(6, 'Quelle')), w(cue(6, 'strategie')), w(cue(6, 'monde'))])
    return s


def sP(t, D):
    """Mettez la vidéo en pause pour chercher par vous-même. Trois. Deux. Un."""
    s = Shot(t, D)
    S.env(s, 'charcoal')
    lit = S.ink(s)
    p = ENTER + 0.2                                            # the symbol draws as the line begins
    three, two, one = w(cue(8, 'Trois')), w(cue(9, 'Deux')), w(cue(10, 'Un'))
    k = A.life(t, p, three - 0.15, 'fade')
    for dx, sd in ((-62, 31), (62, 32)):
        A.stroke(s.top, A.wobble([(W / 2 + dx, 360), (W / 2 + dx, 720)], 1.2, sd), A.pen((t - p - (0.15 if dx > 0 else 0)) / 0.35), 46, lit, k)
    if abs(t - p) < 1 / 30:
        sfx('marker', p, W / 2)
    for n, at, until in (('3', three, two), ('2', two, one), ('1', one, None)):
        if t >= at and (until is None or t < until):
            TY.Text(n, 'stat', size=420, colour=lit).draw(s.top, (W / 2, 300), t, at, anim='scale', anchor='m', sound=False)
    return s


SHOTS = [
    (0.0, sA),
    (cue(1, 'Ils trouvent') - LEAD, sB, 'up'),
    (cue(1, 'mais') - LEAD, sC, 'lr'),
    (cue(1, 'Probleme') - LEAD, sD, 'rl'),
    (cue(1, 'Ils decident') - LEAD, sE, 'up'),
    (cue(2, 'Grace') - LEAD, sF, ('circle', {'at': (W / 2, H / 2)})),
    (cue(3, 'Vous') - LEAD, sG, ('zoom', {'at': (GUARD[0] * W, GUARD[1] * H)})),
    (cue(3, 'Chacun portera') - LEAD, sH, 'lr'),
    (cue(4, 'A mon') - LEAD, sI, 'up'),
    (cue(4, 'Et n') - LEAD, sJ, 'rl'),
    (cue(4, 'Vous') - LEAD, sK, 'lr'),
    (cue(5, 'au') - LEAD, sL, 'up'),
    (cue(5, 'Vous avez') - LEAD, sM, 'rl'),
    (cue(5, 'Ensuite') - LEAD, sN, 'collage'),
    (cue(6, 'Quelle') - LEAD, sO, 'lr'),
    (cue(7, 'Mettez') - LEAD, sP, 'up'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
