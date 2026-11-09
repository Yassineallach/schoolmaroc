"""Acte 4 : Le fer et Rome. Narration clips 11-12."""
import sys
from PIL import Image
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
import maps
from style import sfx, ENTER, Shot, words, tag, kicker

CLIPS = (11, 12)
cue = make_cue(CLIPS)

# ---- real images (credits in assets/credits.json) ----
FORGE = Image.open(asset('P07.jpg'))                                     # blacksmith hammering iron (CC0)
IRON = Image.open(asset('C05.jpg')).crop((60, 120, 4930, 1130))          # Iron Age sword (CC BY 4.0)
GLADII = Image.open(asset('C06.jpg'))                                     # gladius, Museo de la Romanización (CC BY-SA 4.0)
TIBERIUS = Image.open(asset('C06b.jpg')).crop((500, 700, 4080, 1660))     # gladius and scabbard, Carnuntum (CC BY 2.5)
LEGION = Image.open(asset('P08.jpg'))                                     # legionaries relief, Lyon (CC BY-SA 2.0 fr)
TRAJAN = Image.open(asset('P08b.jpg'))                                    # Trajan's Column, legionaries (CC BY-SA 3.0)

IRON_CARD = P.print_card(S.treated(IRON), 1300, border=12, seed=51)
IRON_SMALL = P.print_card(S.treated(IRON), 520, border=8, seed=52)
GLADII_CARD = P.print_card(S.treated(GLADII), 430, seed=53)
TIBERIUS_CARD = P.print_card(S.treated(TIBERIUS), 1300, border=12, seed=54)
LEGION_CARD = P.print_card(S.treated(LEGION), 560, seed=55)
COVER = P.paper_card(GLADII_CARD.width + 10, GLADII_CARD.height + 10, seed=56, text='?', size=180)
M = maps.WorldMap(box=(0, 0, W, H))
NEAR_EAST = ('SYR', 'LBN', 'ISR', 'JOR', 'TUR', 'CYP')
SOUTH_EUROPE = ('GRC', 'ITA', 'ESP', 'PRT')


def sA(t, D):
    """Le fer s'impose ensuite dans de vastes régions, notamment entre le XIIe et le IXe siècle avant notre
    ère au Proche-Orient et en Europe méridionale."""
    s = Shot(t, D)
    S.env(s, 'cream')
    view = M.around((22.0, 38.5), 5200)
    hl = {k: w(cue(11, 'Proche')) for k in NEAR_EAST}
    hl.update({k: w(cue(11, 'Europe')) for k in SOUTH_EUROPE})
    M.draw(s.mid, view, t, highlight=hl)
    words(s.top, (W / 2, 90), 'LE FER', 110, t, [w(cue(11, 'Le fer')), w(cue(11, 'fer'))])
    tag(s.hud, (W / 2, 230), 'XIIe – IXe SIÈCLE AVANT NOTRE ÈRE', 44, t, w(cue(11, 'XIIe')))
    tag(s.hud, (1450, 820), 'PROCHE-ORIENT', 40, t, w(cue(11, 'Proche')), bg=S.PAL.cream, fg=INK)
    tag(s.hud, (560, 900), 'EUROPE MÉRIDIONALE', 40, t, w(cue(11, 'Europe')), bg=S.PAL.cream, fg=INK)
    kicker(s.hud, t, 4, 'Le fer et Rome')
    return s


def sB(t, D):
    """Il devient essentiel pour les outils et les armes."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, FORGE, t, ENTER, ken=(1.02, 1.12), focus=(0.6, 0.6), focus_to=(0.62, 0.66), darken=0.3)
    tag(s.hud, (W / 2, 120), 'ESSENTIEL', 56, t, w(cue(11, 'essentiel')))
    tag(s.hud, (760, 960), 'LES OUTILS', 50, t, w(cue(11, 'outils')), bg=S.PAL.cream, fg=INK)
    tag(s.hud, (1160, 960), 'LES ARMES', 50, t, w(cue(11, 'armes')), bg=S.PAL.cream, fg=INK)
    return s


def sC(t, D):
    """Les sociétés qui maîtrisent sa production peuvent équiper davantage de personnes, même si la qualité
    dépend des minerais, des ateliers et des échanges."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.03)
    words(s.top, (W / 2, 110), 'ÉQUIPER DAVANTAGE DE PERSONNES', 64, t,
          [w(cue(11, x)) for x in ('equiper', 'davantage', 'de personnes', 'personnes')])
    P.drop(s.mid, IRON_SMALL, 400, 280, t, ENTER, rot=-2, spin=8, key='ir0')
    eq = w(cue(11, 'equiper'))
    for i in range(1, 9):                                  # the same real sword, more and more of them
        r_, c_ = divmod(i, 3)
        P.drop(s.mid, IRON_SMALL, 400 + c_ * 560, 280 + r_ * 170, t, eq + 0.08 * i, rot=(-2, 2, -1)[c_], spin=6,
               height=0.5, key=f'ir{i}')
    for i, (word, ph) in enumerate((('LES MINERAIS', 'minerais'), ('LES ATELIERS', 'ateliers'), ('LES ÉCHANGES', 'echanges'))):
        tag(s.hud, (480 + i * 480, 900), word, 42, t, w(cue(11, ph)))
    words(s.hud, (W / 2, 990), 'la qualité dépend…', 40, t, [w(cue(11, x)) for x in ('la qualite', 'qualite', 'depend')], font=F_TYPE)
    return s


def sD(t, D):
    """L'épée conserve une charge symbolique, elle représente l'honneur, le rang et la responsabilité
    guerrière dans des traditions différentes."""
    s = Shot(t, D)
    S.env(s, 'charcoal')
    s.camera(1.03, 1.0)
    P.slide(s.mid, IRON_CARD, (-900, 380), (W / 2, 380), t, ENTER, dur=1.1, rot=0, lag=6, key='irD')
    words(s.top, (W / 2, 620), 'UNE CHARGE SYMBOLIQUE', 72, t,
          [w(cue(11, x)) for x in ('une charge', 'charge', 'symbolique')], fill=S.ink(s))
    for i, (word, ph) in enumerate((("L'HONNEUR", "l'honneur"), ('LE RANG', 'rang'), ('LA RESPONSABILITÉ', 'responsabilite'))):
        words(s.top, ((380, 860, 1420)[i], 800), word, 54, t, w(cue(11, ph)), fill=S.accent(s))
    return s


def sE(t, D):
    """À Rome, une transformation militaire montre comment une arme venue d'ailleurs peut modifier les
    habitudes d'une puissance."""
    s = Shot(t, D)
    S.env(s, 'archive')
    s.camera(1.0, 1.04, (W / 2, H / 2), (1300, 520))
    P.mask_reveal(s.mid, LEGION_CARD, 1350, 520, t, ENTER, dur=1.2, origin=(0.5, 0.4))
    words(s.top, (560, 330), 'ROME', 150, t, w(cue(12, 'Rome')))
    words(s.hud, (560, 520), "une arme venue d'ailleurs", 46, t,
          [w(cue(12, x)) for x in ('une arme', 'arme', 'venue', "d'ailleurs")], font=F_TYPE)
    return s


def sF(t, D):
    """Pendant la deuxième guerre punique, à la fin du IIIe siècle avant notre ère, les Romains adoptent
    progressivement ..."""
    s = Shot(t, D)
    S.env(s, 'cream')
    view = M.around((4.0, 40.5), 2600)
    M.draw(s.mid, view, t, highlight={'ESP': w(cue(12, 'IIIe'))})
    M.marker(s.mid, view, (12.5, 41.9), 'ROME', t, ENTER + 0.2)
    M.route(s.mid, view, [(-3.7, 40.0), (2.0, 40.6), (12.5, 41.9)], t, w(cue(12, 'adoptent')), dur=1.6)
    tag(s.hud, (W / 2, 110), 'DEUXIÈME GUERRE PUNIQUE', 50, t, w(cue(12, 'deuxieme')))
    tag(s.hud, (W / 2, 190), 'FIN DU IIIe SIÈCLE AVANT NOTRE ÈRE', 38, t, w(cue(12, 'IIIe')), bg=S.PAL.cream, fg=INK)
    return s


def sG(t, D):
    """... le gladius hispaniensis, l'épée dite espagnole."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.03, (1300, 540))
    P.put(s.mid, GLADII_CARD, 1380, 540)
    P.tear_reveal(s.mid, COVER, 1380, 540, t, w(cue(12, 'gladius')) - 0.1)
    TY.term_card(s.top, (180, 420), 'GLADIUS HISPANIENSIS', "l'épée dite espagnole", t, w(cue(12, 'gladius')), width=860)
    return s


def sH(t, D):
    """L'historien grec Polybe décrit une lame adaptée à l'estoc et à la coupe."""
    s = Shot(t, D)
    S.env(s, 'archive')
    s.camera(1.0, 1.02)
    P.slide(s.mid, TIBERIUS_CARD, (W + 800, 640), (W / 2, 640), t, ENTER, dur=1.0, rot=-1, key='tib')
    TY.name_card(s.top, (180, 140), 'Polybe', 'HISTORIEN GREC', t, w(cue(12, 'Polybe')))
    # where the blade works: its point (estoc) and its edge (coupe)
    A.arrow(s.top, (1700, 360), (1585, 640), t, w(cue(12, "l'estoc")), colour=S.PAL.accent)
    tag(s.hud, (1700, 320), "L'ESTOC", 46, t, w(cue(12, "l'estoc")))
    A.arrow(s.top, (1150, 360), (1120, 590), t, w(cue(12, 'coupe')), colour=S.PAL.accent)
    tag(s.hud, (1150, 320), 'LA COUPE', 46, t, w(cue(12, 'coupe')))
    return s


def sI(t, D):
    """Son adoption accompagne l'évolution de l'équipement légionnaire, où bouclier, javelot et combat
    rapproché forment un ensemble."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, TRAJAN, t, ENTER, ken=(1.02, 1.1), focus=(0.45, 0.45), focus_to=(0.55, 0.45), darken=0.25)
    tag(s.hud, (W / 2, 110), "L'ÉQUIPEMENT LÉGIONNAIRE", 48, t, w(cue(12, 'legionnaire')))
    for i, (word, ph) in enumerate((('BOUCLIER', 'bouclier'), ('JAVELOT', 'javelot'), ('COMBAT RAPPROCHÉ', 'rapproche'))):
        tag(s.hud, (480 + i * 480, 960), word, 48, t, w(cue(12, ph)), bg=S.PAL.cream, fg=INK)
    tag(s.hud, (W / 2, 860), 'UN ENSEMBLE', 52, t, w(cue(12, 'ensemble')))
    return s


def sJ(t, D):
    """La force romaine repose aussi sur sa capacité à emprunter, adapter et diffuser."""
    s = Shot(t, D)
    S.env(s, 'theme')
    s.camera(1.0, 1.03)
    P.put(s.mid, P.rot_scale(LEGION_CARD, 2, 0.8, key='legJ'), 1560, 520)
    words(s.top, (640, 230), 'LA FORCE ROMAINE', 84, t, [w(cue(12, 'La force')), w(cue(12, 'force')), w(cue(12, 'romaine'))])
    steps = (('EMPRUNTER', 'emprunter'), ('ADAPTER', 'adapter'), ('DIFFUSER', 'diffuser'))
    for i, (word, ph) in enumerate(steps):
        words(s.top, (640, 440 + i * 170), word, 76, t, w(cue(12, ph)), fill=S.PAL.accent if i == 2 else INK)
        if i:
            A.arrow(s.mid, (640, 440 + i * 170 - 120), (640, 440 + i * 170 - 50), t, w(cue(12, ph)) - 0.2, dur=0.3, bend=0.0,
                    colour=INK, width=6, head=18)
    return s


SHOTS = [
    (0.0, sA),
    (cue(11, 'Il') - LEAD, sB, ('circle', {'at': (W / 2, H / 2)})),
    (cue(11, 'Les') - LEAD, sC, 'lr'),
    (cue(11, "L'epee") - LEAD, sD, 'up'),
    (cue(12, 'A Rome') - LEAD, sE, 'pageturn'),
    (cue(12, 'Pendant') - LEAD, sF, 'rl'),
    (cue(12, 'le gladius') - LEAD, sG, 'shape'),
    (cue(12, "L'historien") - LEAD, sH, 'up'),
    (cue(12, 'Son') - LEAD, sI, ('zoom', {'at': (W / 2, H / 2)})),
    (cue(12, 'La force') - LEAD, sJ, 'lr'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
