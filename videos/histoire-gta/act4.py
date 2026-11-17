"""Acte 4 : Liberty City. Narration clips 8-9."""
import sys
import math
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
from style import sfx, ENTER, Shot, words, tag, kicker
import gta as G

CLIPS = (8, 9)
cue = make_cue(CLIPS)

# ---- real material (SOURCES.md)
STEAM = lambda n: Image.open(asset(f'game/steam/gta3_{n}.jpg'))                       # official GTA III screenshots (Steam)
NEON, WALK, DRIVE, FIGHT, SNIPE = STEAM(2), STEAM(7), STEAM(9), STEAM(4), STEAM(1)
GTA3_LOGO = P.load(asset('G03_gta3.png'), width=520)
GTA3_BOX = P.print_card(Image.open(asset('game/wikipedia/b03_gta3_box.jpg')), 470, seed=41)
COPCAR = P.print_card(Image.open(asset('game/wikipedia/s03_gta3_copcar.jpg')), 1100, seed=42)     # before / after (Wikipedia)
IGN, IGN_BOX = G.article('A08_ign_head.png', 'A08_ign_q.png', 'IGN', '19 SEPTEMBRE 2001', width=1400, seed=43)
RQ, RQ_BOX = G.article('A07_rockstar_head.png', 'A07_rockstar_q.png', 'Rockstar Newswire', 'GTA III : vos questions', width=1120, seed=44)
GR, GR_BOX = G.article('A09_gr_head.png', 'A09_gr_slow.png', 'GamesRadar+', '26 AVRIL 2024', width=1000, seed=45)
SR, SR_BOX = G.article('A10_sr_head.png', 'A10_sr_q.png', 'IGN', '25 AOÛT 2006', width=1400, seed=46)   # Saints Row review


def sA(t, D):
    """GTA III change d'échelle."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, NEON, t, -1.0, ken=(1.0, 1.10), focus=(0.5, 0.45), darken=0.3, fade=0.01)
    P.drop(s.mid, GTA3_LOGO, W / 2, 540, t, w(cue(8, 'III')) - 0.1, rot=0, spin=6, height=0.8, key='g3')
    kicker(s.hud, t, 4, 'Liberty City')
    return s


def sB(t, D):
    """Quelques semaines avant sa sortie, les attentats du 11 septembre 2001 frappent New York."""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='grief')
    s.camera(1.03, 1.0)
    words(s.top, (W / 2, 540), '11 SEPTEMBRE 2001', 130, t, [w(cue(8, '11')), w(cue(8, 'septembre')), w(cue(8, '2001'))], fill=S.ink(s))
    words(s.top, (W / 2, 740), 'NEW YORK', 72, t, [w(cue(8, 'New')), w(cue(8, 'York'))], fill=S.accent(s))
    return s


IGN_XY = (W / 2 - IGN.width / 2, 300)


def sC(t, D):
    """Rockstar repousse le jeu, ..."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.04, (W / 2, 450))
    cy = IGN_XY[1] + IGN.height / 2
    P.slide(s.mid, IGN, (W + IGN.width, cy), (W / 2, cy), t, ENTER, dur=0.8, rot=0.0, lag=4.0, key='ign')
    G.highlight(s.mid, IGN_XY, IGN_BOX[list(IGN_BOX)[0]], t, w(cue(8, 'repousse')))
    return s


def sD(t, D):
    """... repeint les voitures de police, trop proches de celles de la ville, ..."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.04)
    P.drop(s.mid, COPCAR, W / 2, 500, t, ENTER, rot=-1, spin=6, key='cop')
    tag(s.mid, (W / 2 - 560, 330), 'AVANT', 44, t, ENTER + 0.4, anchor='r')
    tag(s.mid, (W / 2 - 560, 680), 'APRÈS', 44, t, w(cue(8, 'celles')), bg=G.THIEF, fg=INK, anchor='r')
    return s


RQ_XY = (W / 2 - RQ.width / 2, 70)


def sE(t, D):
    """... et retire une mission qui évoquait des terroristes."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.03, (W / 2, 520))
    cy = RQ_XY[1] + RQ.height / 2
    P.slide(s.mid, RQ, (-RQ.width, cy), (W / 2, cy), t, ENTER, dur=0.8, rot=0.0, lag=4.0, key='rq')
    G.highlight(s.mid, RQ_XY, RQ_BOX[list(RQ_BOX)[0]], t, w(cue(8, 'mission')), dark=True)
    G.typed_quote(s.hud, (W / 2, 960), '« Nous avons retiré une seule mission qui évoquait des terroristes. »', t,
                  w(cue(8, 'mission')) - 0.2, size=38, cps=40)
    return s


def sF(t, D):
    """GTA III sort finalement en octobre 2001 sur PlayStation 2."""
    s = Shot(t, D)
    S.env(s, 'grid')
    s.camera(1.0, 1.04, (620, 540))
    P.drop(s.mid, GTA3_BOX, 600, 540, t, ENTER, rot=-3, spin=10, key='g3b')
    TY.big_number(s.top, (1300, 330), '2001', t, w(cue(8, 'octobre')), role='date', label='OCTOBRE')
    tag(s.hud, (1300, 720), 'PLAYSTATION 2', 56, t, w(cue(8, 'PlayStation')))
    return s


def sG(t, D):
    """Pour la première fois, Liberty City se parcourt en trois dimensions, à pied ou au volant, et
    chaque mission peut s'aborder de plusieurs façons."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    seq = [(ENTER - 1.0, WALK, (0.5, 0.4)), (w(cue(8, 'pied')), WALK, (0.5, 0.6)),
           (w(cue(8, 'volant')) - 0.15, DRIVE, (0.5, 0.5)), (w(cue(8, 'chaque')), FIGHT, (0.55, 0.5)),
           (w(cue(8, 'plusieurs')), SNIPE, (0.5, 0.5))]
    k = max(i for i, (a, *_) in enumerate(seq) if t >= a)
    a, img, f = seq[k]
    if k > 0 and seq[k - 1][1] is img:                            # same picture: keep it, don't re-fade
        a = seq[k - 1][0]
    S.fullbleed(s, img, t, a, ken=(1.0, 1.08), focus=f, darken=0.35, fade=0.25 if k else 0.01)
    return s


def sH(t, D):
    """Cette liberté cachait des contraintes."""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='tense')
    s.camera(1.03, 1.0)
    words(s.top, (W / 2, 450), 'CETTE LIBERTÉ', 120, t, [ENTER, w(cue(9, 'liberte'))], fill=S.ink(s))
    words(s.top, (W / 2, 610), 'CACHAIT DES CONTRAINTES', 92, t,
          [w(cue(9, x)) for x in ('cache', 'des', 'contraintes')], fill=S.accent(s))
    return s


def sI(t, D):
    """La console ne pouvait garder en mémoire que quelques pâtés de maisons à la fois, ..."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    s.camera(1.0, 1.0)
    city = G.city().copy()
    T = t
    x = 330 + (1590 - 330) * ((T * 0.18) % 1.0)                   # the car crosses town; only nearby blocks exist
    y = 830
    r = 330
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), fill=255)
    from PIL import ImageFilter
    mask = mask.filter(ImageFilter.GaussianBlur(60))
    dark = Image.new('RGBA', (W, H), (14, 16, 20, 255))
    dark.paste(city, (0, 0), mask)
    s.mid.alpha_composite(dark)
    G.car(s.mid, 'thief', x, y, 0, t)
    return s


GR_XY = (W / 2 - GR.width / 2, 210)


def sJ(t, D):
    """... et les développeurs ont placé des bâtiments en travers des grandes avenues pour ralentir
    le joueur."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    cy = GR_XY[1] + GR.height / 2
    P.slide(s.mid, GR, (W + GR.width, cy), (W / 2, cy), t, ENTER, dur=0.8, rot=0.0, lag=4.0, key='gr')
    box = GR_BOX[list(GR_BOX)[0]]
    G.highlight(s.mid, GR_XY, box, t, w(cue(9, 'ralentir')) - 0.3)
    s.zoom_to((GR_XY[0] - 20, GR_XY[1] + box[0][1] - 240, GR_XY[0] + GR.width + 20, GR_XY[1] + box[-1][3] + 60),
              w(cue(9, 'place')), dur=1.1, fill=0.95)
    G.typed_quote(s.hud, (W / 2, 950), '« Nous n’avions pas d’autre choix que de ralentir le joueur. »', t,
                  w(cue(9, 'avenues')), size=40, cps=34)
    return s


def sK(t, D):
    """Le résultat se vend à environ 15 millions d'exemplaires, ..."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.04, (620, 540))
    P.drop(s.mid, GTA3_BOX, 560, 540, t, ENTER, rot=3, spin=10, key='g3k')
    TY.big_number(s.top, (1300, 380), '15', t, w(cue(9, '15')), role='stat', label="MILLIONS D'EXEMPLAIRES (ENVIRON)")
    return s


def sL(t, D):
    """... et pendant des années, la presse appellera les jeux qui l'imitent des « clones de GTA »."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.03)
    xy = (W / 2 - SR.width / 2, 240)
    cy = xy[1] + SR.height / 2
    P.slide(s.mid, SR, (W + SR.width, cy), (W / 2, cy), t, ENTER, dur=0.9, rot=0.0, lag=4.0, key='sr')
    G.highlight(s.mid, xy, SR_BOX[list(SR_BOX)[0]], t, w(cue(9, 'clones')) - 0.2)
    bx = SR_BOX[list(SR_BOX)[0]][0]
    s.zoom_to((xy[0] + 10, xy[1] + bx[1] - 190, xy[0] + SR.width - 10, xy[1] + bx[3] + 50), w(cue(9, 'qui')), dur=1.0, fill=0.95)
    tag(s.hud, (W / 2, 960), '« CLONES DE GTA »', 64, t, w(cue(9, 'clones')))
    return s


SHOTS = [
    (0.0, sA),
    (cue(8, '11') - LEAD, sB, 'cut'),
    (cue(8, 'Rockstar') - LEAD, sC, 'up'),
    (cue(8, 'trop') - LEAD, sD, 'lr'),
    (cue(8, 'une mission') - LEAD, sE, 'rl'),
    (cue(8, 'GTA III', 2) - LEAD, sF, 'rl'),
    (cue(8, 'Pour la') - LEAD, sG, ('circle', {'at': (W / 2, H / 2)})),
    (cue(9, 'Cette') - LEAD, sH, 'cut'),
    (cue(9, 'La console') - LEAD, sI, 'lr'),
    (cue(9, 'et le') - LEAD, sJ, 'up'),
    (cue(9, 'Le resultat') - LEAD, sK, 'rl'),
    (cue(9, 'et pendant') - LEAD, sL, 'shape'),
]
END = cue.total + 1.5          # hold the highlighted « GTA clones » after the last word


G.sync(globals())


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
