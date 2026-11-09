"""Acte 5 : Damas et la poudre. Narration clips 13-14."""
import sys, os
from PIL import Image
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
import maps
import cutout
from style import sfx, ENTER, Shot, words, tag, kicker

CLIPS = (13, 14)
cue = make_cue(CLIPS)

# ---- images (credits in assets/credits.json) ----
RIDER = Image.open(asset('P09.png'))                                  # user's ChatGPT ink drawing
RIDER_INK = cutout.ink_image(asset('P09.png'), 1800)
SMITH = Image.open(asset('P10.jpg')).crop((0, 0, 3605, 3700))        # Damascus sword maker, c.1900 (public domain), caption cut
TULWAR = Image.open(asset('C07.jpg'))                                 # Deccan tulwar (CC BY-SA 4.0)
PATTERN = Image.open(asset('C07b.jpg'))                               # steel pattern (CC BY-SA 4.0)
IRON = Image.open(asset('C05.jpg')).crop((60, 120, 4930, 1130))       # an older sword, for "elle recule"
HAS_GUNS = os.path.exists(asset('P11.jpg'))
GUNS = Image.open(asset('P11.jpg')) if HAS_GUNS else None             # gunpowder: musketeers / fortress (pending)
HAS_SABRE = os.path.exists(asset('C08.jpg'))
SABRE = Image.open(asset('C08.jpg')) if HAS_SABRE else None            # ceremonial sabre (pending)

TULWAR_CARD = P.print_card(S.treated(TULWAR), 860, seed=61)
PATTERN_CARD = P.print_card(S.treated(PATTERN), 560, seed=62)
SMITH_CARD = P.print_card(S.treated(SMITH), 620, seed=63)
IRON_CARD = P.print_card(S.treated(IRON), 900, border=10, seed=64)
SABRE_CARD = P.print_card(S.treated(SABRE), 860, seed=65) if HAS_SABRE else P.print_card(S.treated(TULWAR), 900, seed=65)
M = maps.WorldMap(box=(0, 0, W, H))


def sA(t, D):
    """Cette logique traverse l'histoire arabe. Dans la poésie préislamique, l'épée occupe une place de
    prestige : elle accompagne le cavalier, marque son statut et devient une image de bravoure."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    P.mask_reveal(s.mid, RIDER_INK, W / 2, H / 2, t, 0.05, dur=1.8, origin=(0.55, 0.4), lip=False)
    s.push(w(cue(13, 'cavalier')), 0.10, (1050, 480), dur=2.0)
    words(s.hud, (380, 110), "l'histoire arabe", 48, t, [w(cue(13, "'histoire")), w(cue(13, 'arabe'))], font=F_TYPE)
    tag(s.hud, (380, 200), 'LA POÉSIE PRÉISLAMIQUE', 42, t, w(cue(13, 'poesie')))
    for i, (word, ph) in enumerate((('PRESTIGE', 'prestige'), ('STATUT', 'statut'), ('BRAVOURE', 'bravoure'))):
        tag(s.hud, (440 + i * 520, 990), word, 50, t, w(cue(13, ph)), bg=S.PAL.cream, fg=INK)
    kicker(s.hud, t, 5, 'Damas et la poudre')
    return s


def sB(t, D):
    """Les récits évoquent des lames célèbres comme al-Samsama, dont la réputation appartient autant à la
    mémoire littéraire qu'à l'histoire matérielle."""
    s = Shot(t, D)
    S.env(s, 'archive')
    s.camera(1.0, 1.03)
    TY.name_card(s.top, (W / 2, 140), 'al-Samsama', 'UNE LAME CÉLÈBRE', t, w(cue(13, 'Al')), anchor='m')
    left = P.print_card(S.treated(RIDER), 640, seed=66)
    P.drop(s.mid, left, 520, 600, t, ENTER, rot=-3, spin=10, key='memL')
    words(s.hud, (520, 330), 'les récits évoquent…', 44, t, [w(cue(13, x)) for x in ('Les recits', 'recits', 'evoquent')], font=F_TYPE)
    P.drop(s.mid, P.rot_scale(IRON_CARD, 0, 0.75, key='ironB'), 1400, 600, t, w(cue(13, "'histoire", 2)) - 0.1, rot=2, spin=10, key='memR')
    tag(s.hud, (520, 900), 'MÉMOIRE LITTÉRAIRE', 44, t, w(cue(13, 'litteraire')))
    tag(s.hud, (1400, 900), 'HISTOIRE MATÉRIELLE', 44, t, w(cue(13, 'materielle')))
    return s


def sC(t, D):
    """Les épées dites de Damas ajoutent une autre dimension. Leur acier à motifs, souvent associé au wootz,
    reposait sur une matière première dont les traditions remontent à l'Inde du Sud."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.03)
    P.slide(s.mid, TULWAR_CARD, (-800, 300), (620, 300), t, ENTER, dur=1.0, rot=-2, key='tulC')
    words(s.top, (620, 620), 'LES ÉPÉES DE DAMAS', 70, t, [w(cue(13, x)) for x in ('Les', 'epees', 'Damas', 'Damas')])
    P.drop(s.mid, PATTERN_CARD, 1540, 560, t, w(cue(13, 'motifs')) - 0.2, rot=3, spin=10, key='patC')
    tag(s.hud, (1540, 900), "L'ACIER À MOTIFS", 44, t, w(cue(13, 'motifs')))
    TY.term_card(s.top, (180, 760), 'WOOTZ', "un acier venu de l'Inde du Sud", t, w(cue(13, 'Woods')), width=760)
    return s


def sD(t, D):
    """... dont les traditions remontent à l'Inde du Sud."""
    s = Shot(t, D)
    S.env(s, 'cream')
    view = M.around((58.0, 22.0), 6200)
    M.draw(s.mid, view, t)
    india, damas = (77.5, 13.0), (36.3, 33.5)
    M.marker(s.mid, view, damas, 'DAMAS', t, ENTER + 0.1, side='left')
    M.marker(s.mid, view, india, "L'INDE DU SUD", t, w(cue(13, 'Sud')) - 0.3)
    M.route(s.mid, view, [india, (60.0, 22.0), damas], t, w(cue(13, 'remontent')), dur=1.2)
    tag(s.hud, (W / 2, 990), 'UNE MATIÈRE PREMIÈRE', 44, t, w(cue(13, 'matiere')))
    return s


def sE(t, D):
    """Le nom de Damas s'est attaché aux ateliers et aux commerces qui ont rendu ces lames célèbres."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, SMITH, t, ENTER, ken=(1.02, 1.1), focus=(0.5, 0.3), focus_to=(0.5, 0.5), darken=0.3)
    tag(s.hud, (W / 2, 100), 'DAMAS', 60, t, w(cue(13, 'Damas', 2)))
    tag(s.hud, (700, 980), 'LES ATELIERS', 48, t, w(cue(13, 'ateliers')), bg=S.PAL.cream, fg=INK)
    tag(s.hud, (1220, 980), 'LE COMMERCE', 48, t, w(cue(13, 'commerces')), bg=S.PAL.cream, fg=INK)
    return s


def sF(t, D):
    """Mais la poudre à canon change la distance du combat. Les armes à feu permettent de frapper sans
    s'approcher de la même manière."""
    s = Shot(t, D)
    S.env(s, 'geometric')
    s.camera(1.0, 1.03)
    words(s.top, (W / 2, 130), 'LA POUDRE À CANON', 96, t, [w(cue(14, x)) for x in ("L'poudre", "L'poudre", 'a canon', 'canon')], fill=S.ink(s))
    # the distance diagram from act 1 comes back, much longer: the one drawing that explains this line
    d0 = w(cue(14, 'distance'))
    stretch = P.ease_out(P.clamp01((t - d0) / 1.6))
    xa, xb = 300, 900 + 720 * stretch
    for x, label in ((xa, 'HUMAIN'), (xb, 'DANGER')):
        if t >= ENTER:
            from PIL import ImageDraw
            ImageDraw.Draw(s.mid).ellipse((x - 46, 520 - 46, x + 46, 520 + 46), outline=S.ink(s) + (255,), width=7)
            TY.Text(label, 'label', colour=S.ink(s)).draw(s.mid, (x, 590), t, ENTER, anchor='m', sound=False)
    A.connect(s.mid, [(xa + 60, 520), (xb - 60, 520)], t, d0, dur=0.5, arrowhead=True, dots=False, colour=S.accent(s))
    words(s.hud, (W / 2, 820), 'frapper sans s’approcher', 52, t,
          [w(cue(14, x)) for x in ('frapper', 'sans', "s'approcher")], font=F_TYPE, fill=S.ink(s))
    return s


def sG(t, D):
    """Leur diffusion transforme les armées, les fortifications et l'organisation des États."""
    s = Shot(t, D)
    if HAS_GUNS:
        S.env(s, 'bleed')
        S.fullbleed(s, GUNS, t, ENTER, ken=(1.02, 1.1), darken=0.3)
    else:                                                     # holds the place until P11 arrives
        S.env(s, 'archive')
        s.camera(1.0, 1.03)
        words(s.top, (W / 2, 380), 'LEUR DIFFUSION TRANSFORME', 80, t,
              [w(cue(14, x)) for x in ('Leur', 'diffusion', "'transforme")])
    for i, (word, ph) in enumerate((('LES ARMÉES', 'armees'), ('LES FORTIFICATIONS', 'fortifications'), ("L'ORGANISATION DES ÉTATS", "l'organisation"))):
        tag(s.hud, (W / 2, 640 + i * 100), word, 46, t, w(cue(14, ph)), bg=S.PAL.cream if HAS_GUNS else S.PAL.accent,
            fg=INK if HAS_GUNS else S.PAL.cream)
    return s


def sH(t, D):
    """L'épée ne disparaît pas : elle recule dans de nombreux contextes militaires, tandis qu'elle demeure
    dans les uniformes, les cérémonies et les représentations du commandement."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.03)
    words(s.top, (W / 2, 110), 'NE DISPARAÎT PAS', 80, t, [w(cue(14, x)) for x in ('ne', 'disparait', 'pas')])
    # "elle recule": the sword slides back with friction
    rec = w(cue(14, 'recule'))
    if t < rec:
        P.put(s.mid, IRON_CARD, 760, 360)
    else:
        P.slide(s.mid, IRON_CARD, (760, 360), (-200, 360), t, rec, dur=1.4, rot=-1, lag=4, key='ironH')
    P.drop(s.mid, SABRE_CARD, 1340, 640, t, w(cue(14, 'demeure')) - 0.1, rot=2, spin=8, key='sabH')
    for i, (word, ph) in enumerate((('UNIFORMES', 'uniformes'), ('CÉRÉMONIES', 'ceremonies'), ('COMMANDEMENT', 'commandement'))):
        tag(s.hud, (520, 520 + i * 110), word, 48, t, w(cue(14, ph)))
    return s


def sI(t, D):
    """Son pouvoir symbolique survit à une partie de son rôle pratique."""
    s = Shot(t, D)
    S.env(s, 'charcoal')
    s.camera(1.03, 1.0)
    P.put(s.mid, P.rot_scale(SABRE_CARD, 0, 0.7, key='sabI'), W / 2, 330)
    phr = ('Son', 'pouvoir', 'symbolique', 'survit')
    S.type_page(s, 'Son pouvoir symbolique survit.', t, ENTER, role='statement', size=86, xy=(W / 2, 700),
                cues=[w(cue(14, x)) for x in phr], accent={'survit.': w(cue(14, 'survit')) + 0.2})
    return s


SHOTS = [
    (0.0, sA),
    (cue(13, 'Les recits') - LEAD, sB, 'up'),
    (cue(13, 'Les epees') - LEAD, sC, 'lr'),
    (cue(13, 'dont', 2) - LEAD, sD, ('circle', {'at': (W * 0.6, H * 0.6)})),
    (cue(13, 'Le nom') - LEAD, sE, ('zoom', {'at': (W * 0.3, H * 0.3)})),
    (cue(14, "L'poudre") - LEAD, sF, 'shape'),
    (cue(14, 'Leur') - LEAD, sG, 'rl'),
    (cue(14, "L'epee") - LEAD, sH, 'up'),
    (cue(14, 'Son') - LEAD, sI, 'lr'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
