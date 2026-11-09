"""Acte 3 : Le bronze. Narration clips 8-10."""
import sys
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

CLIPS = (8, 9, 10)
cue = make_cue(CLIPS)

# ---- real images (credits in assets/credits.json) ----
INGOT = Image.open(asset('C09.jpg'))                                   # copper ingot, the Met (CC0)
THAMES = Image.open(asset('C04.jpg')).crop((0, 20, 1920, 270))         # Bronze Age sword, River Thames (CC0)
HILT = Image.open(asset('C11.jpg'))                                     # bronze sword hilt, Lyon (CC BY-SA 2.0 fr)
BENT = Image.open(asset('P05.jpg'))                                     # deliberately bent sword (CC BY 2.0)
UGARIT = Image.open(asset('P06.jpg'))                                   # Ugarit palace ruins (CC BY-SA 4.0)
SPEAR = Image.open(asset('P02.jpg'))                                    # Speer VII (CC BY-SA 3.0 de)

INGOT_CARD = P.print_card(S.treated(INGOT), 520, seed=41)
THAMES_CARD = P.print_card(S.treated(THAMES), 1500, border=12, seed=42)
THAMES_SMALL = P.print_card(S.treated(THAMES), 760, border=10, seed=43)
HILT_CARD = P.print_card(S.treated(HILT), 640, seed=44)
BENT_CARD = P.print_card(S.treated(BENT), 900, seed=45)
SWORDS = cutout.ink_image(asset('C10.jpg'), 720, backed=True)           # Bronze Age swords engraving (CC0)
HABU = cutout.ink_image(asset('P06b.jpg'), 1840)                        # Medinet Habu relief drawing (public domain)
SPEAR_TINY = P.print_card(S.treated(SPEAR).crop((430, 180, 600, 1300)).rotate(90, expand=True), 300, border=6, seed=46)
OFFERING = P.paper_card(BENT_CARD.width, BENT_CARD.height, seed=47, text='UNE OFFRANDE', size=86)
TIN = P.paper_card(420, 300, seed=48, text="L'ÉTAIN", size=70)
LABEL = document(700, 560, ['London Museum', '---', 'Épées · IIe millénaire av. notre ère', '---',
                            'marqueurs de statut', "et d'identité", '---'], seed=9, title='CARTEL', body_size=36)
M = maps.WorldMap(box=(0, 0, W, H))


def sA(t, D):
    """Le métal change l'échelle de cette histoire."""
    s = Shot(t, D)
    s.camera(1.0, 1.05, (W / 2, H / 2), (1250, 520))
    P.mask_reveal(s.mid, HILT_CARD, 1250, 520, t, 0.05, dur=1.4, origin=(0.6, 0.4))
    words(s.top, (520, 420), 'LE MÉTAL', 130, t, [w(cue(8, 'Le metal')), w(cue(8, 'metal'))])
    words(s.hud, (520, 580), "change l'échelle", 50, t, [w(cue(8, 'change')), w(cue(8, "l'echelle"))], font=F_TYPE)
    kicker(s.hud, t, 3, 'Le bronze')
    return s


def sB(t, D):
    """Le cuivre se travaille, mais reste relativement tendre."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.04, (700, 520))
    P.drop(s.mid, INGOT_CARD, 680, 520, t, ENTER, rot=-3, spin=-10, key='ingot')
    words(s.top, (1380, 380), 'LE CUIVRE', 110, t, [w(cue(8, 'Le cuivre')), w(cue(8, 'cuivre'))])
    words(s.hud, (1380, 540), 'se travaille', 50, t, [w(cue(8, 'se')), w(cue(8, 'travaille'))], font=F_TYPE)
    tag(s.hud, (1380, 660), 'RELATIVEMENT TENDRE', 50, t, w(cue(8, 'tendre')))
    return s


def sC(t, D):
    """En l'alliant à l'étain, les artisans obtiennent le bronze, mieux adapté à certains objets durables."""
    s = Shot(t, D)
    S.env(s, 'grid')
    s.camera(1.0, 1.02)
    P.put(s.mid, P.rot_scale(INGOT_CARD, -3, 0.62, key='ingC'), 300, 460)
    P.drop(s.mid, TIN, 760, 460, t, w(cue(8, "l'etain")) - 0.1, rot=3, spin=10, key='tin')
    words(s.top, (530, 440), '+', 110, t, w(cue(8, "l'alliant")))
    words(s.top, (1010, 440), '=', 110, t, w(cue(8, 'obtiennent')))
    P.drop(s.mid, P.rot_scale(HILT_CARD, 2, 0.95, key='hiltC'), 1440, 460, t, w(cue(8, 'le bronze')) - 0.1, rot=2, spin=8, key='hiltCd')
    words(s.top, (300, 690), 'CUIVRE', 54, t, ENTER)
    words(s.top, (1440, 820), 'LE BRONZE', 72, t, w(cue(8, 'bronze')), fill=S.PAL.accent)
    words(s.hud, (W / 2, 960), 'mieux adapté aux objets durables', 46, t,
          [w(cue(8, x)) for x in ('mieux', 'adapte', 'adapte', 'objets', 'durables')], font=F_TYPE)
    return s


def sD(t, D):
    """Les épées en bronze deviennent coûteuses et exigent des artisans spécialisés."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.04, (1250, 520))
    P.slide(s.mid, SWORDS, (W + 500, 540), (1300, 540), t, ENTER, dur=1.1, rot=1, key='swordsD')
    words(s.top, (520, 330), 'LES ÉPÉES', 96, t, [w(cue(8, 'Les epees')), w(cue(8, 'epees'))])
    words(s.top, (520, 450), 'EN BRONZE', 96, t, [w(cue(8, 'en bronze')), w(cue(8, 'bronze', 2))])
    P.stamp_hit(s.mid, 'COÛTEUSES', 520, 640, t, w(cue(8, 'couteuses')), size=84, ang=-7, shot=s)
    words(s.hud, (520, 830), 'des artisans spécialisés', 46, t,
          [w(cue(8, x)) for x in ('des artisans', 'artisans', 'specialises')], font=F_TYPE)
    return s


def sE(t, D):
    """Au London Museum, des épées du deuxième millénaire avant notre ère sont décrites comme des
    marqueurs de statut et d'identité."""
    s = Shot(t, D)
    S.env(s, 'archive')
    s.camera(1.0, 1.03, (W / 2, 560), (1300, 560))
    P.slide(s.mid, THAMES_SMALL, (-700, 300), (560, 300), t, ENTER, dur=1.0, rot=-2, key='thE')
    P.unfold(s.mid, LABEL, 1330, 600, t, w(cue(8, 'London')), dur=1.1)
    A.ring(s.mid, (1000, 645, 1400, 712), t, w(cue(8, 'statut')))
    A.ring(s.mid, (1000, 700, 1320, 762), t, w(cue(8, "d'identite")))
    tag(s.hud, (560, 560), 'IIe MILLÉNAIRE AV. NOTRE ÈRE', 40, t, w(cue(8, 'deuxieme')))
    return s


def sF(t, D):
    """L'épée possède une particularité sociale. Une lance peut équiper de nombreux combattants ; une
    épée bien travaillée peut signaler le rang d'un individu."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.03)
    words(s.top, (W / 2, 110), 'UNE PARTICULARITÉ SOCIALE', 64, t,
          [w(cue(9, x)) for x in ('une particularite', 'particularite', 'sociale')])
    # many spears: the same real spear, again and again
    lance = w(cue(9, 'lance'))
    for i in range(12):
        r_, c_ = divmod(i, 4)
        P.drop(s.mid, SPEAR_TINY, 230 + c_ * 330, 330 + r_ * 150, t, lance + 0.06 * i, rot=(-3, 2, -1, 3)[c_], spin=6,
               height=0.5, key=f'sp{i}')
    words(s.hud, (690, 820), 'NOMBREUX COMBATTANTS', 46, t, [w(cue(9, 'nombreux')), w(cue(9, 'combattants'))])
    # one sword, one rank
    P.drop(s.mid, P.rot_scale(THAMES_SMALL, -90, 0.9, key='thF'), 1620, 560, t, ENTER, rot=-2, spin=10, key='thFd')
    A.ring(s.mid, (1500, 170, 1740, 950), t, w(cue(9, 'Une epee')))
    tag(s.hud, (1620, 960), "LE RANG D'UN INDIVIDU", 42, t, w(cue(9, 'rang')))
    return s


def sG(t, D):
    """Elle accompagne des élites, des cérémonies et des sépultures."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, HILT, t, ENTER, ken=(1.02, 1.12), focus=(0.55, 0.45), focus_to=(0.6, 0.4), darken=0.25)
    for i, (word, ph) in enumerate((('ÉLITES', 'elites'), ('CÉRÉMONIES', 'ceremonies'), ('SÉPULTURES', 'sepultures'))):
        tag(s.hud, (480 + i * 480, 960), word, 52, t, w(cue(9, ph)))
    return s


def sH(t, D):
    """Certaines lames ont été volontairement pliées ou endommagées avant d'être déposées dans des rivières."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.letterbox(s, BENT, t, ENTER, ken=(1.0, 1.08), focus=(0.4, 0.5))
    tag(s.hud, (W / 2, 70), 'VOLONTAIREMENT PLIÉES', 44, t, w(cue(9, 'pliees')))
    words(s.hud, (W / 2, 1005), 'déposées dans des rivières', 44, t,
          [w(cue(9, x)) for x in ('deposees', 'dans', 'des rivieres', 'rivieres')], font=F_TYPE, fill=S.PAL.cream)
    return s


def sI(t, D):
    """L'objet change alors de fonction. Il quitte le monde des vivants pour devenir une offrande."""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='calm')
    s.camera(1.0, 1.03)
    P.flip(s.mid, BENT_CARD, OFFERING, W / 2, 470, t, w(cue(9, 'offrande')) - 0.3)
    words(s.top, (W / 2, 900), "L'OBJET CHANGE DE FONCTION", 56, t,
          [w(cue(9, x)) for x in ("L'objet", 'change', 'de fonction', 'fonction')], fill=S.ink(s))
    return s


def sJ(t, D):
    """Mais la diffusion des épées accompagne aussi des bouleversements plus vastes."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.05, (W / 2, 520))
    P.put(s.mid, P.rot_scale(SWORDS, 0, 0.8, key='swJ'), 1440, 520)
    words(s.top, (620, 380), 'LA DIFFUSION', 84, t, [w(cue(10, 'la diffusion')), w(cue(10, 'diffusion'))])
    words(s.top, (620, 480), 'DES ÉPÉES', 84, t, [w(cue(10, 'des epees')), w(cue(10, 'epees'))])
    tag(s.hud, (620, 650), 'DES BOULEVERSEMENTS PLUS VASTES', 42, t, w(cue(10, 'bouleversements')))
    return s


def sK(t, D):
    """À la fin de l'âge du bronze, vers 1200 avant notre ère, plusieurs centres de la Méditerranée
    orientale connaissent destructions, abandons et changements politiques."""
    s = Shot(t, D)
    S.env(s, 'cream')
    med = M.around((27.0, 36.5), 3400)
    east = M.around((33.0, 35.0), 1700)
    a = w(cue(10, 'Mediterranee'))
    view = M.zoom(t, [(0.0, med), (a - 0.2, med), (a + 1.6, east)])
    M.draw(s.mid, view, t)
    M.marker(s.mid, view, (35.79, 35.60), 'UGARIT', t, w(cue(10, 'centres')))
    TY.big_number(s.top, (W / 2, 80), '1200', t, w(cue(10, '1200')), role='stat', label='AVANT NOTRE ÈRE', colour=INK)
    return s


def sL(t, D):
    """... destructions, abandons et changements politiques."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, UGARIT, t, ENTER, ken=(1.02, 1.1), focus=(0.5, 0.55), focus_to=(0.6, 0.55), darken=0.3)
    for i, (word, ph) in enumerate((('DESTRUCTIONS', 'destruction'), ('ABANDONS', 'abandon'), ('CHANGEMENTS POLITIQUES', 'politique'))):
        tag(s.hud, (W / 2, 760 + i * 90), word, 48, t, w(cue(10, ph)), bg=S.PAL.accent if i == 0 else S.PAL.cream,
            fg=S.PAL.cream if i == 0 else INK)
    tag(s.hud, (330, 80), 'UGARIT', 40, t, ENTER, bg=S.PAL.cream, fg=INK)
    return s


def sM(t, D):
    """Migrations, conflits, crises internes et changements climatiques figurent parmi les facteurs proposés."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.06, (W / 2, 470), (800, 420))
    P.mask_reveal(s.mid, HABU, W / 2, 470, t, ENTER, dur=1.2, origin=(0.4, 0.5), lip=False)
    for i, (word, ph) in enumerate((('MIGRATIONS', 'Migration'), ('CONFLITS', 'conflit'), ('CRISES INTERNES', 'crise interne'),
                                    ('CHANGEMENTS CLIMATIQUES', 'climatique'))):
        tag(s.hud, ((250, 640, 1080, 1590)[i], 990), word, 34, t, w(cue(10, ph)))
    tag(s.hud, (W / 2, 60), 'DES FACTEURS PROPOSÉS', 38, t, w(cue(10, 'facteurs')), bg=S.PAL.cream, fg=INK)
    return s


def sN(t, D):
    """Aucune cause unique n'explique cet effondrement. Les armes appartiennent à cette histoire, sans en être
    l'explication à elles seules."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.03)
    P.put(s.mid, P.rot_scale(THAMES_SMALL, -2, 1.0, key='thN'), W / 2, 660)
    words(s.top, (W / 2, 200), 'UNE CAUSE UNIQUE', 104, t, [w(cue(10, 'Aucune')), w(cue(10, 'cause')), w(cue(10, 'unique'))])
    A.strike(s.top, A.grow(A.text_box((W / 2, 200), 'UNE CAUSE UNIQUE', 104), 30, -40), t, w(cue(10, "n")), scribble=True)
    words(s.hud, (W / 2, 880), 'les armes appartiennent à cette histoire', 44, t,
          [w(cue(10, x)) for x in ('Les armes', 'armes', 'appartiennent', 'a cette', 'cette', 'histoire')], font=F_TYPE)
    words(s.hud, (W / 2, 950), "sans en être l'explication", 44, t,
          [w(cue(10, x)) for x in ('sans', 'en etre', 'etre', "'explication")], font=F_TYPE)
    return s


SHOTS = [
    (0.0, sA),
    (cue(8, 'Le cuivre') - LEAD, sB, 'up'),
    (cue(8, 'En') - LEAD, sC, 'lr'),
    (cue(8, 'Les epees') - LEAD, sD, 'rl'),
    (cue(8, 'Au') - LEAD, sE, 'pageturn'),
    (cue(9, "L'epee") - LEAD, sF, 'up'),
    (cue(9, 'Elle') - LEAD, sG, ('circle', {'at': (W / 2, H / 2)})),
    (cue(9, 'Certaines') - LEAD, sH, 'lr'),
    (cue(9, "L'objet") - LEAD, sI, 'up'),
    (cue(10, 'Mais') - LEAD, sJ, 'rl'),
    (cue(10, 'A la fin') - LEAD, sK, 'shape'),
    (cue(10, 'destruction') - LEAD, sL, ('zoom', {'at': (W * 0.75, H * 0.45)})),
    (cue(10, 'Migration') - LEAD, sM, 'lr'),
    (cue(10, 'Aucune') - LEAD, sN, 'up'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
