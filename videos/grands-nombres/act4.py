"""Acte 4 : Des jeux plus grands que le monde. Narration clips 8-9."""
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
from gn import power

CLIPS = (8, 9)
cue = make_cue(CLIPS)

# ---- real images (Wikimedia Commons, credits in assets/credits.json) ----
HANOI_ENG = N.image('R12', (960, 1421), 'tour de Hanoï 1884')
HANOI_TOY = N.image('R13', (1600, 2400), 'tour en bois')
BENARES = N.image('R14', (1920, 1317), 'Bénarès')
CARDS = N.image('R15', (1280, 853), 'cartes')
PACIFIC = N.image('R16', (1920, 1920), 'Pacifique')
SUN = N.image('R17', (1920, 1833), 'Soleil')

ENG_CARD = P.print_card(S.treated(HANOI_ENG), 480, seed=121)
TOY_CARD = P.print_card(S.treated(HANOI_TOY).crop((0, int(HANOI_TOY.height * 0.18), HANOI_TOY.width, int(HANOI_TOY.height * 0.82))), 330, seed=122)
BEN_CARD = P.print_card(S.treated(BENARES), 900, seed=123)
CARDS_CARD = P.print_card(S.treated(CARDS), 1000, seed=124)
SUN_CARD = P.print_card(S.treated(SUN), 300, seed=125)
BOARD, _, _ = N.board_image(520)

GOLD = (196, 152, 66)
GOLD_DARK = (150, 110, 40)


def _hanoi_moves(n, a=0, b=2, c=1):
    if n == 0:
        return []
    return _hanoi_moves(n - 1, a, c, b) + [(a, b)] + _hanoi_moves(n - 1, c, b, a)


MOVES = _hanoi_moves(4)


def hanoi(layer, cx, cy, t, start, per=0.24, n=4, scale=1.0):
    """Three pegs and n gold discs moving by the rule (one at a time, never a big one on a small)."""
    d = ImageDraw.Draw(layer)
    pegs = [cx - 300 * scale, cx, cx + 300 * scale]
    base_y = cy + 120 * scale
    d.rounded_rectangle((cx - 450 * scale, base_y, cx + 450 * scale, base_y + 22 * scale), radius=6, fill=(120, 92, 60, 255))
    for x in pegs:
        d.rounded_rectangle((x - 6 * scale, base_y - 230 * scale, x + 6 * scale, base_y), radius=4, fill=(150, 116, 76, 255))
    stacks = [list(range(n, 0, -1)), [], []]
    k = max(0.0, (t - start) / per)
    done = int(k)
    frac = k - done
    for (a, b) in MOVES[:min(done, len(MOVES))]:
        stacks[b].append(stacks[a].pop())
    moving = None
    if done < len(MOVES) and t >= start:
        a, b = MOVES[done]
        moving = (stacks[a].pop(), a, b, P.ease_io(frac))
    hgt = 30 * scale
    for i, st_ in enumerate(stacks):
        for j, size in enumerate(st_):
            wd = (60 + 46 * size) * scale
            y = base_y - (j + 1) * hgt
            d.rounded_rectangle((pegs[i] - wd / 2, y, pegs[i] + wd / 2, y + hgt - 3), radius=8, fill=GOLD + (255,), outline=GOLD_DARK + (255,), width=2)
    if moving:
        size, a, b, u = moving
        wd = (60 + 46 * size) * scale
        top = base_y - 280 * scale
        ya = base_y - (len(stacks[a]) + 1) * hgt
        yb = base_y - (len(stacks[b]) + 1) * hgt
        if u < 0.33:
            x, y = pegs[a], ya + (top - ya) * (u / 0.33)
        elif u < 0.66:
            x, y = pegs[a] + (pegs[b] - pegs[a]) * ((u - 0.33) / 0.33), top
        else:
            x, y = pegs[b], top + (yb - top) * ((u - 0.66) / 0.34)
        d.rounded_rectangle((x - wd / 2, y, x + wd / 2, y + hgt - 3), radius=8, fill=GOLD + (255,), outline=GOLD_DARK + (255,), width=2)


def sA(t, D):
    """Ces nombres naissent aussi de jeux. En 1883, le mathématicien français Édouard Lucas publie
    la tour de Hanoï, avec une légende :"""
    s = Shot(t, D)
    S.env(s, 'archive')
    P.drop(s.mid, ENG_CARD, 600, 540, t, ENTER, rot=-2.5, spin=8, key='eng')
    TY.name_card(s.top, (1000, 380), 'Édouard Lucas', 'MATHÉMATICIEN · 1883', t, w(cue(8, '1883')))
    kicker(s.hud, t, 4, 'Des jeux plus grands que le monde', start=0.3)
    caption(s.hud, 'La tour d’Hanoï, Popular Science Monthly, 1884', t, ENTER + 1.0)
    return s


def sB(t, D):
    """À Bénarès, des prêtres déplacent soixante-quatre disques d'or entre trois aiguilles de diamant,"""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.letterbox(s, BENARES, t, ENTER, ken=(1.0, 1.06), focus=(0.5, 0.5))
    caption(s.hud, 'Bénarès (Varanasi), 1922', t, ENTER + 0.8, on_dark=True)
    return s


def sC(t, D):
    """un à la fois, sans jamais poser un grand disque sur un petit."""
    s = Shot(t, D)
    S.env(s, 'paper')
    hanoi(s.mid, W / 2, 520, t, ENTER + 0.1, per=0.24)
    return s


def sD(t, D):
    """Quand ils auront fini, le monde s'achèvera."""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='tense')
    P.put(s.mid, BEN_CARD, W / 2, 540)                               # locked off
    return s


def sE(t, D):
    """Il leur faut deux puissance soixante-quatre moins un déplacements, exactement le nombre de
    grains de l'échiquier."""
    s = Shot(t, D)
    S.env(s, 'geometric')
    hanoi(s.mid, 480, 520, t, -99, n=4, scale=0.62)                  # the tower, still
    P.put(s.mid, BOARD, 1440, 520)
    k = P.ease_out(P.clamp01((t - w(cue(8, 'deux'))) / 0.6))
    power(s.top, (W / 2, 120), '2', '64', 150, t, w(cue(8, 'deux')), anchor='m')
    words(s.top, (W / 2 + 205, 196), '− 1', 110, t, w(cue(8, 'moins')))
    A.connect(s.mid, [(700, 560), (1160, 560)], t, w(cue(8, 'exactement')), dur=0.8, arrowhead=True, dots=False)
    return s


def sF(t, D):
    """À un déplacement par seconde, cela prendrait environ 585 milliards d'années, plus de quarante
    fois l'âge de l'univers."""
    s = Shot(t, D)
    S.env(s, 'grid')
    hanoi(s.mid, 360, 360, t, ENTER, per=1.0, scale=0.42)            # one move a second, from the cut
    d = ImageDraw.Draw(s.mid)
    one = ENTER
    many = w(cue(8, '40'))
    cell, gap = 52, 12
    for i in range(41):
        at = one if i == 0 else many + 0.035 * i
        k = P.ease_out(P.clamp01((t - at) / 0.25))
        if k <= 0:
            continue
        col, row = (i % 14), (i // 14)
        x = 700 + col * (cell + gap)
        y = 560 + row * (cell + gap)
        c = PAL.accent if i == 0 else PAL.soft
        d.rectangle((x, y + (1 - k) * 20, x + cell, y + cell), fill=c + (int(255 * k),))
    TY.Text('l’âge de l’univers', 'label', size=26).draw(s.top, (700, 520), t, w(cue(8, "'age")), anchor='l', sound=False)
    TY.big_number(s.top, (1180, 200), '585', t, w(cue(8, '585')), role='stat', label='MILLIARDS D’ANNÉES')
    return s


def sG(t, D):
    """Un simple jeu de cartes suffit pourtant à dépasser l'échiquier."""
    s = Shot(t, D)
    S.env(s, 'paper')
    P.slide(s.mid, CARDS_CARD, (-700, 560), (900, 540), t, ENTER, dur=1.1, rot=-3, key='cards')
    caption(s.hud, 'Mélange de cartes', t, ENTER + 1.0)
    return s


DIGITS52 = '80658175170943878571660636856403766975289505440883277824000000000000'


def sH(t, D):
    """Le nombre de façons de mélanger 52 cartes, factorielle 52, c'est-à-dire 52 fois 51 fois 50,
    et ainsi de suite jusqu'à 1, compte soixante-huit chiffres."""
    s = Shot(t, D)
    S.env(s, 'cream')
    P.put(s.mid, CARDS_CARD.resize((380, int(380 * CARDS_CARD.height / CARDS_CARD.width)), Image.LANCZOS).rotate(4, Image.BICUBIC, expand=True), 300, 230)
    TY.Text('52 !', 'headline', size=170).draw(s.top, (W / 2, 140), t, w(cue(9, 'factorielle')), anim='scale', anchor='m')
    parts = (('52', '52', 3), ('× 51', '51', 1), ('× 50', '50', 1), ('× … × 1', '1,', 1))
    f = F_HEAD(64)
    x = W / 2 - f.getlength('52 × 51 × 50 × … × 1') / 2
    for txt, ph, nth in parts:
        words(s.top, (x + f.getlength(txt) / 2, 430), txt, 64, t, w(cue(9, ph, nth)))
        x += f.getlength(txt + ' ')
    # the actual value of 52!, typed fast in two lines: 68 digits
    at = w(cue(9, 'compte'))
    n = int(max(0, (t - at) / 0.9) * 68)
    if n:
        ff = F_TYPE(54)
        line1, line2 = DIGITS52[:34][:n], DIGITS52[34:][:max(0, n - 34)]
        d = ImageDraw.Draw(s.top)
        d.text((W / 2, 640), line1, font=ff, fill=PAL.ink + (255,), anchor='mm')
        if line2:
            d.text((W / 2, 720), line2, font=ff, fill=PAL.ink + (255,), anchor='mm')
        sfx('type', at, W / 2, n=68, cps=75)
    if t > at + 1.0:
        A.ring(s.top, (W / 2 - 520, 600, W / 2 + 520, 760), t, at + 1.0, width=5, until=at + 3.0)
    return s


def sI(t, D):
    """Scott Czepiel en a donné une image :"""
    s = Shot(t, D)
    S.env(s, 'theme')
    TY.name_card(s.top, (560, 420), 'Scott Czepiel', 'UNE IMAGE', t, ENTER + 0.1)
    return s


MAP = maps.WorldMap(box=(0, 60, W, 1020))


def sJ(t, D):
    """faire le tour de l'équateur en avançant d'un pas tous les milliards d'années,"""
    s = Shot(t, D)
    S.env(s, 'paper')
    view = MAP.WORLD
    MAP.draw(s.mid, view, t)
    k = P.clamp01((t - w(cue(9, 'avancant'))) / 2.8)
    pts = [(-170 + 360 * k * j / 20, 0.0) for j in range(21)]
    if k > 0:
        MAP.route(s.mid, view, [(-170, 0.0), (-170 + 359 * k, 0.0)], t, w(cue(9, 'avancant')), dur=2.8, arc=0.0, head=True)
    return s


def sK(t, D):
    """retirer une goutte du Pacifique à chaque tour,"""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, PACIFIC, t, ENTER, ken=(1.15, 1.22), focus=(0.42, 0.5), darken=0.2)
    caption(s.hud, 'Le Pacifique vu par le satellite GOES-18, NOAA / NASA', t, ENTER + 0.8, on_dark=True)
    # one drop lifts away
    at = w(cue(9, 'goutte'))
    u = P.clamp01((t - at) / 1.2)
    if 0 < u < 1:
        d = ImageDraw.Draw(s.hud)
        x, y = 860, 640 - 260 * P.ease_out(u)
        r = 9
        a = int(255 * (1 - max(0, u - 0.7) / 0.3))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(200, 225, 245, a))
        d.polygon([(x - r * 0.8, y - 2), (x, y - 26), (x + r * 0.8, y - 2)], fill=(200, 225, 245, a))
    return s


def sL(t, D):
    """poser une feuille de papier chaque fois que l'océan est vide, jusqu'à ce que la pile touche le
    Soleil, puis recommencer mille fois."""
    s = Shot(t, D)
    S.env(s, 'theme')
    P.put(s.mid, SUN_CARD, W / 2, 190)
    d = ImageDraw.Draw(s.mid)
    top = 360
    k = P.ease_io(P.clamp01((t - ENTER) / (w(cue(9, 'Soleil')) - ENTER + 0.2)))
    h = (1000 - top) * k
    n = int(h / 6)
    for i in range(n):
        y = 1000 - i * 6
        jit = ((i * 37) % 11) - 5
        d.rectangle((W / 2 - 150 + jit, y - 5, W / 2 + 150 + jit, y), fill=(PAL.light if i % 2 else PAL.paper2) + (255,), outline=PAL.soft + (255,))
    words(s.top, (W / 2 + 330, 640), '× 1 000', 96, t, w(cue(9, 'mille')), fill=PAL.accent)
    caption(s.hud, 'Le Soleil, SDO / NASA', t, ENTER + 0.8)
    return s


def sM(t, D):
    """Cela ne couvrirait qu'environ un tiers de ce nombre, compté en secondes."""
    s = Shot(t, D)
    S.env(s, 'cream')
    k = P.ease_out(P.clamp01((t - ENTER) / 0.5))                    # the whole disc is there from the cut
    if k > 0:
        ImageDraw.Draw(s.mid).ellipse((W / 2 - 280, 520 - 280, W / 2 + 280, 520 + 280), fill=PAL.soft + (int(255 * k),),
                                      outline=PAL.ink + (int(255 * k),), width=4)
    A.wedge(s.mid, (W / 2, 520), 280, 0, 120, t, w(cue(9, 'tiers')) - 0.3, colour=PAL.accent)
    return s


SHOTS = [
    (0.0, sA),
    (cue(8, 'A') - LEAD, sB, 'lr'),
    (cue(8, 'un', 1) - LEAD, sC, 'up'),
    (cue(8, 'Quand') - LEAD, sD, 'rl'),
    (cue(8, 'Il leur') - LEAD, sE, 'shape'),
    (cue(8, 'A un') - LEAD, sF, 'lr'),
    (cue(9, 'Un simple') - LEAD, sG, 'up'),
    (cue(9, 'Le nombre') - LEAD, sH, 'rl'),
    (cue(9, 'Scott') - LEAD, sI, 'up'),
    (cue(9, 'Faire') - LEAD, sJ, 'lr'),
    (cue(9, 'retirer') - LEAD, sK, ('circle', {'at': (W / 2, H / 2)})),
    (cue(9, 'poser') - LEAD, sL, 'up'),
    (cue(9, 'Cela') - LEAD, sM, 'rl'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
