"""Acte 1 : Un grain sur la première case. Narration clips 1-3."""
import sys
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
import charts as CH
from style import sfx, ENTER, Shot, words, tag, kicker, caption
import gn as N

CLIPS = (1, 2, 3)
cue = make_cue(CLIPS)

# ---- real images (Wikimedia Commons, credits in assets/credits.json) ----
MINIATURE = N.image('R01', (1600, 1200), 'miniature')
PAINTING = N.crop_frac(MINIATURE, (0.105, 0.205, 0.645, 0.69)) if N.have('R01') else MINIATURE   # the painted scene, without the page margin
PAINT_CARD = P.print_card(S.treated(PAINTING), 740, seed=10)
PCX, PCY = W / 2, 540                                     # where the print sits
_pw, _ph = PAINT_CARD.size


def on_paint(fx, fy):
    """Screen point of a point given as fractions of the painted scene."""
    return PCX - _pw / 2 + 16 + fx * (_pw - 32), PCY - _ph / 2 + 16 + fy * (_ph - 32)


CHESS = on_paint(0.676, 0.845)                            # the chessboard in the painting
KING = on_paint(0.27, 0.46)                               # the king on his throne


def set_cam(s, z, F):
    s.zoom = z
    s.lx, s.ly = F[0] - (F[0] - W / 2) / z, F[1] - (F[1] - H / 2) / z
GRAIN = N.image('R02', (1600, 960), 'grain')
SACKS = N.image('R03b', (1400, 1080), 'sacs de grain')
GAMOW = N.image('H01', (900, 1100), 'Gamow')

GRAIN_CARD = P.print_card(S.treated(GRAIN), 760, seed=12)
SACKS_CARD = P.print_card(S.treated(SACKS), 820, seed=13)
GAMOW_CARD = P.print_card(S.treated(GAMOW), 560, seed=14)
BOARD, BPAD, BSQ = N.board_image(760)
BOARD_SMALL = BOARD.resize((560, 560), Image.LANCZOS)
BS = 760 * 560 / BOARD.width        # playing area of the small board on screen


def sA(t, D):
    """Dans un palais de l'Inde, un roi veut récompenser l'homme qui vient de lui offrir un jeu
    nouveau : les échecs."""
    s = Shot(t, D)
    S.env(s, 'charcoal')                                  # the night ground: the miniature glows on it
    s.camera(1.0, 1.16, (PCX, PCY), (CHESS[0], CHESS[1] - 120))   # a slow push towards the chessboard
    P.put(s.mid, PAINT_CARD, PCX, PCY)
    caption(s.hud, 'Bozorgmehr et le jeu d’échecs, Shâhnâmeh de Shah Tahmasp, vers 1530', t, 1.2, on_dark=True)
    return s


def sB(t, D):
    """Le vizir pourrait réclamer de l'or. Il demande du blé."""
    s = Shot(t, D)
    S.env(s, 'theme')
    P.put(s.mid, BOARD_SMALL, 1330, 560)                                     # the empty board is already there
    P.drop(s.mid, GRAIN_CARD, 600, 520, t, w(cue(1, 'demande')) - 0.1, rot=-4, spin=12, key='grain')
    kicker(s.hud, t, 1, 'Un grain sur la première case', start=0.6)
    caption(s.hud, 'Grain de blé épeautre', t, w(cue(1, 'demande')) + 0.8)
    return s


def sC(t, D):
    """Un grain sur la première case de l'échiquier, deux sur la deuxième, quatre sur la troisième,
    en doublant à chaque case."""
    s = Shot(t, D)
    S.env(s, 'paper')
    cx, cy = W / 2, 560
    s.camera(1.0, 1.0)
    s.push(w(cue(1, 'doublant')), 0.10, (cx - 220, cy - 290))
    P.put(s.mid, BOARD, cx, cy)
    marks = (('Un', 1, 1), ('deux', 2, 2), ('quatre', 3, 4))
    for ph, k, n in marks:
        x, y = N.square_centre(cx, cy, 760, k)
        N.scatter(s.mid, x, y, n, 20, t, w(cue(1, ph)), seed=k, dur=0.25)
        words(s.top, (x, y + 70), str(n), 34, t, w(cue(1, ph)) + 0.2, fill=PAL.accent)
    base = w(cue(1, 'doublant'))
    for k in range(4, 9):                                                    # the doubling runs on along the row
        x, y = N.square_centre(cx, cy, 760, k)
        N.scatter(s.mid, x, y, 2 ** (k - 1), 30, t, base + 0.32 * (k - 4), seed=k, dur=0.3, size=0.7)
    return s


def sD(t, D):
    """Le roi sourit de cette modestie."""
    s = Shot(t, D)
    S.env(s, 'charcoal')
    back = w(cue(2, 'intendants'))                        # held on the king, then back to the court
    k = P.ease_io(P.clamp01((t - back) / 1.6))
    set_cam(s, 2.1 - 1.0 * k, (KING[0] + (PCX - KING[0]) * k, KING[1] + (PCY - KING[1]) * k))
    P.put(s.mid, PAINT_CARD, PCX, PCY)
    return s


def sE(t, D):
    """Ses intendants cessent vite de sourire. Avant la vingtième case, le premier sac est vide."""
    s = Shot(t, D)
    S.env(s, 'theme')
    s.camera(1.0, 1.04, (W / 2, H / 2), (1250, 520))
    P.slide(s.mid, SACKS_CARD, (-500, 560), (560, 540), t, ENTER, dur=1.1, rot=-3, key='sacks')
    bx, by = 1340, 540
    P.put(s.mid, BOARD_SMALL, bx, by)
    x, y = N.square_centre(bx, by, BS, 20)
    A.ring(s.mid, (x - 44, y - 44, x + 44, y + 44), t, w(cue(2, 'vingtieme')))
    caption(s.hud, 'Récolte de céréales, 1960', t, ENTER + 1.0)
    return s


def sF(t, D):
    """Pour couvrir les soixante-quatre cases, il faudrait plus de dix-huit milliards de milliards
    de grains."""
    s = Shot(t, D)
    S.env(s, 'accent')
    P.put(s.mid, BOARD_SMALL.rotate(4, Image.BICUBIC, expand=True), 470, 540)        # the board is there from the cut
    TY.big_number(s.top, (1300, 300), '18', t, w(cue(2, 'dix')), role='stat', colour=S.ink(s), accent_bar=False)
    TY.Text('milliards de milliards de grains', 'statement', colour=S.ink(s), max_w=880).draw(
        s.top, (1300, 600), t, w(cue(2, 'milliards')), anim='words', anchor='m',
        cues=[w(cue(2, 'milliards')), w(cue(2, 'de milliards')), w(cue(2, 'milliards', 2)), w(cue(2, 'de grains')), w(cue(2, 'grains'))])
    return s


def sG(t, D):
    """Environ 1 200 milliards de tonnes de blé : plus de mille quatre cents années de la récolte
    mondiale actuelle."""
    s = Shot(t, D)
    S.env(s, 'grid')
    one, many = ENTER, w(cue(2, 'mille'))
    cols, cell = 56, 21                                                      # 56 x 25 = 1 400 years
    ox, oy = (W - cols * cell) / 2, 250
    d = ImageDraw.Draw(s.mid)
    for i in range(1400):
        at = one if i == 0 else many + 1.4 * (i / 1400) ** 0.8
        if t < at:
            continue
        k = P.clamp01((t - at) / 0.25)
        x, y = ox + (i % cols) * cell, oy + (i // cols) * cell
        if i == 0:                                                           # one year: large, then it takes its place
            u = P.ease_io(P.clamp01((t - many + 0.2) / 0.8))
            size = 200 + (cell - 4 - 200) * u
            cx, cy = W / 2 + (x + cell / 2 - W / 2) * u, 520 + (y + cell / 2 - 520) * u
            d.rectangle((cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2), fill=N.GOLD + (255,))
            continue
        c = tuple(int(a + (b - a) * k) for a, b in zip((241, 236, 226), PAL.accent))
        d.rectangle((x + 2, y + 2, x + cell - 2, y + cell - 2), fill=c + (255,))
    if t >= one:
        TY.Text('1 an de récolte mondiale', 'label').draw(s.top, (W / 2, 660), t, one + 0.2, anchor='m', sound=False, until=many - 0.3)
    if t >= many:
        TY.Text('× 1 400', 'stat', size=120, colour=PAL.accent).draw(s.top, (W / 2, 880), t, many + 0.6, anim='scale', anchor='m')
    return s


def sH(t, D):
    """Cette légende, notée dès 1256 par l'historien Ibn Khallikan..."""
    s = Shot(t, D)
    S.env(s, 'archive')
    s.camera(1.0, 1.03)
    P.slide(s.mid, BOARD_SMALL, (-400, 560), (560, 560), t, ENTER, dur=1.0, rot=-3, key='legend')
    TY.name_card(s.top, (1020, 430), 'Ibn Khallikan', 'HISTORIEN · 1256', t, w(cue(3, '1256')))
    return s


def sI(t, D):
    """... ouvre l'histoire des très grands nombres."""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='wonder')
    S.type_page(s, 'Les très grands nombres', t, ENTER, role='headline', size=118,
                cues=[w(cue(3, x)) for x in ('des', 'tres', 'grands', 'nombres')])
    return s


def sJ(t, D):
    """En 1947, le physicien George Gamow la raconte dans « Un, deux, trois... l'infini » et donne
    un nom au roi : Shirham."""
    s = Shot(t, D)
    S.env(s, 'theme')
    s.camera(1.0, 1.03, (W / 2, H / 2), (900, 520))
    P.drop(s.mid, GAMOW_CARD, 560, 520, t, ENTER, rot=-3, spin=10, key='gamow')
    TY.name_card(s.top, (1000, 330), 'George Gamow', 'PHYSICIEN · 1947', t, w(cue(3, 'physicien')))
    tag(s.hud, (1250, 760), 'Shirham', 54, t, w(cue(3, 'Shirham')), bg=PAL.accent, fg=CREAM)
    caption(s.hud, 'George Gamow', t, w(cue(3, 'George')) + 1.0)
    return s


SHOTS = [
    (0.0, sA),
    (cue(1, 'Le vizir') - LEAD, sB, 'up'),
    (cue(1, 'Un grain') - LEAD, sC, 'lr'),
    (cue(1, 'Le roi') - LEAD, sD, ('zoom', {'at': (W / 2, 420)})),
    (cue(2, 'Avant') - LEAD, sE, 'rl'),
    (cue(2, 'Pour couvrir') - LEAD, sF, 'up'),
    (cue(2, 'environ') - LEAD, sG, 'lr'),
    (cue(3, 'legende') - LEAD - 0.3, sH, 'pageturn'),
    (cue(3, 'ouvre') - LEAD, sI, 'rl'),
    (cue(3, 'le physicien') - LEAD, sJ, 'up'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
