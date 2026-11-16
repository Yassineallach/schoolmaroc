"""Acte 1 : Le bug. Narration clips 1-3."""
import sys
import math
from PIL import Image
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
from style import sfx, ENTER, Shot, words, tag, kicker, caption
import gta as G

CLIPS = (1, 2, 3)
cue = make_cue(CLIPS)

# ---- real material (SOURCES.md)
MOCKUP = P.print_card(Image.open(asset('R01_racenchase.jpg')), 560, seed=11)     # Race'n'Chase mock-up, DMA Design (non-free still)
LOGO = P.load(asset('G01_gta1997.png'), width=480)                                # the first game's logo (Wikipedia)
TAKE2 = P.load(asset('L02_take2.png'), width=170)                                 # Take-Two Interactive logo (Wikipedia)
LOGO_CARD = P.paper_card(MOCKUP.width, MOCKUP.height, seed=12, colour=CREAM)
LOGO_CARD.alpha_composite(LOGO, ((LOGO_CARD.width - LOGO.width) // 2, (LOGO_CARD.height - LOGO.height) // 2))
PENN, PENN_BOX = G.article('A01_penn_head.png', 'A01_penn_quote.png', 'Game Developer (Gamasutra)', '31 JANVIER 2011', width=1380)
GD, GD_BOX = G.article('A02_gd_head.png', 'A02_gd_475.png', 'Game Developer', '7 AOÛT 2026', width=1080, seed=23)
GTA1_SHOT = P.print_card(Image.open(asset('game/wikipedia/s01_gta1.png')), 520, seed=13)   # GTA (1997), in-game (Wikipedia)
FOLDER = document(560, 660, ['---', '---', '---', '---', '---', '---'], seed=8, title='PROJET', typed=True)

DUNDEE_PHOTO = Image.open(asset('P01_dundee.jpg'))                                # Colin Smith, CC BY-SA 2.0 (Geograph / Commons)

# ---- the chase: one loop round the two middle blocks, the police 300 px behind
LOOP = G.Route([(330, 830), (1590, 830), (1590, 250), (330, 250), (330, 830)] * 3)
SPEED = 250.0
GAP = 300.0
T0 = cue(1, 'un concepteur')          # act time the thief sets off
RAM = cue(1, 'foncent', 2)            # the police turn on the player (the 1st 'foncent' is Whisper's '1990')


def thief_s(T):
    """Arc length of the thief: drives until the ram, then is shoved and stops."""
    if T < RAM + 0.55:
        return SPEED * (T - T0) + 700
    return SPEED * (RAM + 0.55 - T0) + 700 + 40 * P.ease_out((T - RAM - 0.55) / 0.6)


def chase(s, T, t, ram=True):
    """Draw the thief and two police cars at act time T."""
    x, y, h = LOOP.at(thief_s(T))
    cops = []
    for i, gap in enumerate((GAP, GAP * 2.1)):
        cx, cy, ch = LOOP.at(thief_s(min(T, RAM)) - gap if T < RAM else SPEED * (RAM - T0) + 700 - gap)
        if ram and T >= RAM:
            k = P.ease_io((T - RAM - 0.12 * i) / 0.55)
            side = math.radians(h + (90 if i == 0 else -150))
            tx, ty = x + 70 * math.cos(side), y + 70 * math.sin(side)
            cx, cy = cx + (tx - cx) * k, cy + (ty - cy) * k
            ch = ch + ((G.look((cx, cy), (x, y)) - ch + 180) % 360 - 180) * min(1.0, k * 1.6)
        cops.append((cx, cy, ch))
    jolt = 0.0
    if ram and T >= RAM + 0.55:
        jolt = 14 * math.exp(-(T - RAM - 0.55) * 5) * math.sin((T - RAM - 0.55) * 40)
    G.car(s.mid, 'thief', x + jolt, y, h + jolt * 0.6, t)
    for cx, cy, ch in cops:
        G.car(s.mid, 'cop', cx, cy, ch, t)
    return (x, y), cops


def sA(t, D):
    """Au milieu des années 1990, dans un studio de Dundee, en Écosse, ..."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, DUNDEE_PHOTO, t, -1.0, ken=(1.12, 1.0), focus=(0.55, 0.42), focus_to=(0.5, 0.5), darken=0.35, fade=0.01)
    tag(s.hud, (W / 2, 140), 'MILIEU DES ANNÉES 1990', 46, t, w(cue(1, 'annees')))
    tag(s.hud, (W / 2, 930), 'DUNDEE, ÉCOSSE', 58, t, w(cue(1, 'Dundee')), bg=CREAM, fg=INK)
    return s


def sB(t, D):
    """... un concepteur teste une course-poursuite. Le principe est simple : un voleur fuit en
    voiture, et la police le suit en essayant de lui barrer la route."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    s.camera(1.04, 1.0)
    s.mid.alpha_composite(G.city())
    T = t + SCENE0['sB']
    (x, y), cops = chase(s, T, t, ram=False)
    tag(s.hud, (330, 120), 'LE VOLEUR', 44, t, w(cue(1, 'voleur')), bg=G.THIEF, fg=INK)
    tag(s.hud, (1590, 120), 'LA POLICE', 44, t, w(cue(1, 'police')))
    kicker(s.hud, t, 1, 'Le bug', start=1.0)
    return s


def sC(t, D):
    """Ce jour-là, les policiers ne se contentent plus de suivre. Ils foncent droit sur le joueur."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    T = t + SCENE0['sC']
    x, y, _ = LOOP.at(thief_s(RAM + 0.6))
    s.camera(1.0, 1.0)
    s.push(w(cue(1, 'Ce jour')) + 0.3, 0.45, focus=(x, y), dur=2.6)
    s.mid.alpha_composite(G.city())
    chase(s, T, t)
    sfx('stamp', w(RAM) + 0.55, x, gain=0.6)
    tag(s.hud, (W / 2, 960), 'ILS FONCENT DROIT SUR LE JOUEUR', 54, t, w(cue(1, 'droit')))
    return s


def sD(t, D):
    """Leur programme de déplacement semble cassé."""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='tense')
    s.camera(1.03, 1.0)
    words(s.top, (W / 2, 470), 'LEUR PROGRAMME', 110, t, [ENTER, w(cue(2, 'program'))], fill=S.ink(s))
    words(s.top, (W / 2, 600), 'DE DÉPLACEMENT', 110, t, [w(cue(2, 'de deplacement')), w(cue(2, 'deplacement'))], fill=S.ink(s))
    P.stamp_hit(s.top, 'CASSÉ', 1440, 760, t, w(cue(2, 'casse')), size=120, ang=-9, shot=s)
    return s


ENC = (960, 540)                      # the encirclement, at the middle of the map


def sE(t, D):
    """Les voitures de patrouille percutent, poussent et encerclent, et chaque fuite devient une
    lutte pour survivre."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    s.camera(1.08, 1.16, ENC, ENC)
    city = G.city()
    s.mid.alpha_composite(city)
    hit, push, ring = w(cue(2, 'percutent')), w(cue(2, 'poussent')), w(cue(2, 'encerclent'))
    shove = 120 * P.ease_out((t - push) / 0.8)
    tx, ty = 820 + shove, 830 + 10 * math.sin(t * 9) * math.exp(-max(0, t - hit) * 2) * (t > hit)
    G.car(s.mid, 'thief', tx, ty, 8 + 25 * P.ease_out((t - push) / 0.8), t)
    for i in range(3):
        a0 = math.radians(200 + i * 120)
        r = 330 - 170 * P.ease_io((t - ENTER) / max(0.1, hit - ENTER))
        orbit = 0.7 * max(0.0, t - ring)
        a = a0 + orbit
        r = r if t < ring else 175
        cx, cy = tx + r * math.cos(a), ty + r * math.sin(a)
        hd = math.degrees(a) + 90 if t >= ring else G.look((cx, cy), (tx, ty))
        G.car(s.mid, 'cop', cx, cy, hd, t)
    for word, ph, x in (('PERCUTENT', 'percutent', 470), ('POUSSENT', 'poussent', 960), ('ENCERCLENT', 'encerclent', 1450)):
        tag(s.hud, (x, 120), word, 46, t, w(cue(2, ph)))
    words(s.hud, (W / 2, 975), 'une lutte pour survivre', 50, t,
          [w(cue(2, p)) for p in ('une lutte', 'lutte', 'pour', 'survivre')], font=F_TYPE, fill=CREAM)
    return s


PENN_XY = (W / 2 - PENN.width / 2, 230)


def sF(t, D):
    """Le concepteur Gary Penn racontera plus tard qu'il a vécu là un moment génial, parce que pour
    la première fois, la poursuite faisait peur."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.02)
    cx, cy = W / 2, PENN_XY[1] + PENN.height / 2
    P.slide(s.mid, PENN, (W + PENN.width, cy), (cx, cy), t, ENTER, dur=1.0, rot=0.0, lag=5.0, key='penn')
    ph1, ph2 = list(PENN_BOX)
    G.highlight(s.mid, PENN_XY, PENN_BOX[ph1], t, w(cue(2, 'racontera')))
    G.highlight(s.mid, PENN_XY, PENN_BOX[ph2], t, w(cue(2, 'premiere')))
    TY.name_card(s.top, (PENN_XY[0] + 10, 120), 'Gary Penn', 'CONCEPTEUR, DMA DESIGN', t, w(cue(2, 'Gary')))
    G.typed_quote(s.hud, (W / 2, 940), '« La police est devenue folle : elle essaie de me sortir de la route. »', t,
                  w(cue(2, 'parce')), size=40, cps=34)
    return s


def sG(t, D):
    """Ce bug allait relancer un projet qui risquait d'être abandonné."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.04, (W / 2, H / 2), (1300, 540))
    words(s.top, (560, 460), 'CE BUG', 150, t, [ENTER + 0.1, w(cue(2, 'bug'))])
    A.underline(s.top, A.grow(A.text_box((560, 460), 'CE BUG', 150), -10, 0), t, w(cue(2, 'relancer')))
    P.drop(s.mid, FOLDER, 1420, 560, t, w(cue(2, 'projet')) - 0.15, rot=3, spin=10, key='folder')
    P.stamp_hit(s.mid, 'ABANDONNÉ', 1420, 600, t, w(cue(2, 'risquait')), size=74, ang=-12, shot=s)
    A.strike(s.mid, (1210, 550, 1630, 650), t, w(cue(2, 'abandonne')) + 0.35, scribble=True)
    return s


MOCK_XY = (620, 520)


def sH(t, D):
    """Ce projet s'appelait Race'n'Chase."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.04, MOCK_XY)
    P.drop(s.mid, MOCKUP, *MOCK_XY, t, w(cue(3, 'Race')) - 0.3, rot=-3, spin=12, key='mock')
    words(s.top, (1400, 520), "RACE'N'CHASE", 104, t, w(cue(3, 'Race')))
    return s


def sI(t, D):
    """Il deviendra Grand Theft Auto, une série dont l'éditeur Take-Two revendique aujourd'hui près
    de 475 millions d'exemplaires vendus."""
    s = Shot(t, D)
    S.env(s, 'paper')
    P.flip(s.mid, MOCKUP, LOGO_CARD, 440, 400, t, w(cue(3, 'Grand')) - 0.2)
    P.drop(s.mid, GTA1_SHOT, 440, 830, t, w(cue(3, 'Auto')), rot=-3, spin=10, key='g1s')
    gx, gy = 1330 - GD.width / 2, 330
    P.slide(s.mid, GD, (W + GD.width, gy + GD.height / 2), (gx + GD.width / 2, gy + GD.height / 2), t,
            w(cue(3, 'Take')) - 0.3, rot=0.0, lag=5.0, key='gd')
    P.drop(s.mid, TAKE2, gx + GD.width - 190, gy - 95, t, w(cue(3, 'Take')), rot=0, spin=8, height=0.6, key='t2')
    box = GD_BOX[list(GD_BOX)[0]]
    G.highlight(s.mid, (gx, gy), box, t, w(cue(3, '475')))
    x0, y1, x1 = gx + box[0][0], gy + box[-1][3], gx + max(b[2] for b in box)
    s.zoom_to((x0 - 40, gy - 190, x1 + 40, y1 + 60), w(cue(3, 'aujourd')), dur=1.2, fill=0.95)
    tag(s.hud, (W / 2, 1002), "PRÈS DE 475 MILLIONS D'EXEMPLAIRES", 54, t, w(cue(3, '475')))
    return s


def sJ(t, D):
    """Reste à comprendre comment une course-poursuite déréglée a donné naissance à l'une des plus
    grandes franchises du divertissement."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    s.camera(1.12, 1.0, (960, 540))
    s.mid.alpha_composite(G.city())
    T = t + SCENE0['sJ']
    for i in range(3):                                             # the police weave, out of control
        ss = SPEED * (T - T0) + 400 - i * 330
        x, y, h = LOOP.at(ss % (LOOP.total / 3) + 1)
        wob = 26 * math.sin(T * (3.1 + i) + i)
        G.car(s.mid, 'thief' if i == 0 else 'cop', x + wob * math.sin(math.radians(h)), y - wob * math.cos(math.radians(h)), h + wob * 0.9, t)
    shade = Image.new('RGBA', (W, H), PAL.dark + (int(150 * P.clamp01((t - w(cue(3, 'une course')) + 0.3) / 0.5)),))
    s.hud.alpha_composite(shade)
    words(s.hud, (W / 2, 470), 'UNE COURSE-POURSUITE', 92, t, [w(cue(3, 'une course')), w(cue(3, 'course'))], fill=CREAM)
    A.emphasis(s.hud, (W / 2, 600), 'DÉRÉGLÉE', 120, t, w(cue(3, 'dereglee')), base=CREAM, colour=G.THIEF)
    return s


SHOTS = [
    (0.0, sA),
    (cue(1, 'un concepteur') - LEAD, sB, 'up'),
    (cue(1, 'Ce jour') - LEAD, sC, 'cut'),
    (cue(2, 'Le program') - LEAD, sD, 'lr'),
    (cue(2, 'Le voiture') - LEAD, sE, 'rl'),
    (cue(2, 'Le concepteur') - LEAD, sF, 'pageturn'),
    (cue(2, 'Ce bug') - LEAD, sG, 'up'),
    (cue(3, 'Ce projet') - LEAD, sH, ('circle', {'at': MOCK_XY})),
    (cue(3, 'Il deviendra') - LEAD, sI, 'cut'),
    (cue(3, 'Reste') - LEAD, sJ, 'shape'),
]
SCENE0 = {f.__name__: t0 for t0, f, *_ in SHOTS}
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
