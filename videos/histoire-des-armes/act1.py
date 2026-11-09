"""Acte 1 : Une arme dans la boue. Narration clips 1-4."""
import sys
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
from style import sfx, ENTER, Shot, words, tag, kicker

CLIPS = (1, 2, 3, 4)
cue = make_cue(CLIPS)

# ---- real images (Wikimedia Commons, credits in assets/credits.json) ----
MINE = Image.open(asset('P01.jpg'))                       # Tagebau Schöningen (CC0)
SPEAR_PHOTO = Image.open(asset('P02.jpg'))                # Speer VII im Sediment 1997 (CC BY-SA 3.0 de)

MINE_CARD = P.print_card(S.treated(MINE), 900, seed=11)
SPEAR_CARD = P.print_card(S.treated(SPEAR_PHOTO).rotate(90, expand=True), 1240, seed=12)   # spear lying across the print
SPEAR_SMALL = P.print_card(S.treated(SPEAR_PHOTO).rotate(90, expand=True), 760, seed=13)


def spear_strip(length=1500):
    """The spear itself, cut from the excavation photo as a long torn strip lying flat."""
    im = S.treated(SPEAR_PHOTO)
    w, h = im.size
    x0, y0, x1, y1 = SPEAR_BOX
    strip = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))).rotate(90, expand=True)
    strip = strip.rotate(SPEAR_TILT, Image.BICUBIC, expand=False)
    k = length / strip.width
    strip = strip.resize((length, int(strip.height * k)), Image.LANCZOS)
    return P.print_card(strip, length, border=10, seed=14)


SPEAR_BOX = (0.45, 0.13, 0.62, 0.95)     # the spear band in the photo (fractions)
SPEAR_TILT = 0.0
STRIP = spear_strip()
# a succession of real objects: wooden spear, stone point, bronze sword (Thames)
ROW = [P.print_card(S.treated(Image.open(asset('P02.jpg'))).crop((430, 180, 600, 1300)).rotate(90, expand=True), 560, border=10, seed=31),
       P.print_card(S.treated(Image.open(asset('C02.jpg')).crop((185, 120, 730, 840))), 300, seed=32),
       P.print_card(S.treated(Image.open(asset('C04.jpg')).crop((0, 20, 1920, 270))), 580, border=10, seed=33)]


def sA(t, D):
    """En 1994, près d'une mine à ciel ouvert, l'archéologue Hartmut Thieme met au jour une forme
    sombre dans le sédiment."""
    s = Shot(t, D)
    s.camera(1.0, 1.04, (W / 2, H / 2), (800, 500))
    P.mask_reveal(s.mid, MINE_CARD, 540, 500, t, 0.1, dur=2.0, origin=(0.45, 0.55))
    P.stamp_hit(s.mid, '1994', 250, 190, t, w(cue(1, '1994')), size=110, ang=-7, shot=s)
    TY.name_card(s.top, (1060, 330), 'Hartmut Thieme', 'ARCHÉOLOGUE', t, w(cue(1, "'archeologue")))
    words(s.hud, (1530, 640), 'une forme sombre', 46, t,
          [w(cue(1, x)) for x in ('une forme', 'forme', 'sombre')], font=F_TYPE)
    words(s.hud, (1530, 700), 'dans le sédiment', 46, t,
          [w(cue(1, x)) for x in ('dans le', 'le sediment', 'sediment')], font=F_TYPE)
    kicker(s.hud, t, 1, 'Une arme dans la boue')
    return s


def sB(t, D):
    """Ce n'est ni un os ni une branche ordinaire."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.04, (640, 520))
    P.drop(s.mid, SPEAR_SMALL, 540, 540, t, ENTER, rot=-2, spin=-10, key='spsmall')
    for i, (word, ph) in enumerate((('UN OS', 'os'), ('UNE BRANCHE', 'branche'))):
        y = 360 + i * 230
        words(s.top, (1390, y), word, 96, t, w(cue(1, ph)))
        box = A.text_box((1390, y), word, 96)
        A.strike(s.top, A.grow(box, 20, -30), t, w(cue(1, ph)) + 0.45)
    return s


def sC(t, D):
    """Le bois repose près des restes de chevaux chassés au bord d'un ancien lac."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, SPEAR_PHOTO.rotate(90, expand=True), t, ENTER, ken=(1.02, 1.12), focus=(0.5, 0.5), focus_to=(0.42, 0.5), darken=0.35)
    tag(s.hud, (560, 900), 'DES CHEVAUX CHASSÉS', 46, t, w(cue(1, 'chevaux')))
    tag(s.hud, (1380, 900), 'UN ANCIEN LAC', 46, t, w(cue(1, 'ancien lac')), bg=S.PAL.cream, fg=INK)
    return s


def sD(t, D):
    """Le passé vient de conserver une arme."""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='wonder')
    s.camera(1.04, 1.0)
    phr = ('le passe', 'passe', 'vient', 'de conserver', 'conserver', 'une arme', 'arme')
    S.type_page(s, 'Le passé vient de conserver une arme.', t, ENTER, role='statement', size=96,
                cues=[w(cue(1, x)) for x in phr], accent={'arme.': w(cue(1, 'arme')) + 0.2})
    return s


def sE(t, D):
    """Elle mesure plus de deux mètres. Et elle est en bois."""
    s = Shot(t, D)
    S.env(s, 'grid')
    s.camera(1.0, 1.03)
    P.slide(s.mid, STRIP, (-900, 470), (W / 2, 470), t, ENTER, dur=1.2, rot=0.0, lag=6.0, key='strip')
    x0, x1 = W / 2 - STRIP.width / 2 + 20, W / 2 + STRIP.width / 2 - 20
    A.connect(s.mid, [(x0, 640), (x1, 640)], t, w(cue(2, 'mesure')), dur=0.9, arrowhead=True, dots=False)
    words(s.top, (W / 2, 690), 'PLUS DE 2 MÈTRES', 88, t,
          [w(cue(2, x)) for x in ('plus', 'de deux', 'deux', 'metres')])
    P.stamp_hit(s.mid, 'BOIS', 1480, 300, t, w(cue(2, 'bois')), size=120, ang=-9, shot=s)
    return s


def sF(t, D):
    """Cette découverte ouvre sur l'hoplologie, l'étude des armes et des comportements de combat."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.03, (W / 2, H / 2), (900, 480))
    P.slide(s.mid, SPEAR_SMALL, (W + 500, 520), (1440, 520), t, ENTER, dur=1.1, rot=3, key='spF')
    TY.term_card(s.top, (180, 400), 'HOPLOLOGIE', "l'étude des armes et des comportements de combat",
                 t, w(cue(3, "l'hoplologie")), width=880)
    return s


def sG(t, D):
    """Le terme apparaît au XIXe siècle, puis Donn F. Draeger contribue à développer ce champ d'étude
    dans les années 1960."""
    import timeline as TL
    s = Shot(t, D)
    S.env(s, 'archive')
    s.camera(1.0, 1.03)
    tl = TL.Timeline(1800, 2000, box=(220, 640, 1700, 680), step=50)
    tl.axis(s.mid, t, ENTER)
    tl.era(s.mid, 1800, 1900, 'XIXe SIÈCLE', t, w(cue(3, 'XIXe')))
    tl.event(s.mid, 1960, 'ANNÉES 1960', t, w(cue(3, 'annees')), side='up')
    TY.name_card(s.top, (1100, 220), 'Donn F. Draeger', 'HOPLOLOGUE', t, w(cue(3, 'Donn')))
    return s


def sH(t, D):
    """L'histoire qu'il examine est moins linéaire qu'il n'y paraît : les humains transforment leur
    environnement, puis leurs sociétés, en modifiant la distance à laquelle ils affrontent le danger."""
    s = Shot(t, D)
    S.env(s, 'geometric')
    s.camera(1.0, 1.03)
    import math as _m
    lin, turn = ENTER, w(cue(3, 'lineaire'))
    d_end = w(cue(3, 'modifiant')) - 1.0                          # gone before the distance diagram draws
    if t < d_end + 0.5:
        op = 1.0 - P.clamp01((t - d_end) / 0.5)
        k = P.ease_io(P.clamp01((t - turn) / 0.9))                  # 0 straight -> 1 winding
        pts = [(260 + i * 14, 470 + k * (120 * _m.sin(i * 0.11) + 50 * _m.sin(i * 0.31 + 1.0))) for i in range(101)]
        A.stroke(s.mid, pts, P.clamp01((t - lin) / 1.2), width=9, colour=S.ink(s), alpha=op)
        tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        words(tmp, (W / 2, 700), 'MOINS LINÉAIRE', 96, t, [w(cue(3, 'moins')), w(cue(3, 'lineaire'))], fill=S.accent(s))
        s.top.alpha_composite(alpha_mul(tmp, op))
    words(s.top, (520, 220), 'ENVIRONNEMENT', 64, t, w(cue(3, 'environnement')), fill=S.ink(s))
    words(s.top, (1400, 220), 'SOCIÉTÉS', 64, t, w(cue(3, 'societes')), fill=S.ink(s))
    d0 = w(cue(3, 'modifiant'))
    stretch = P.ease_out(P.clamp01((t - d0) / 2.2))
    xa, xb = 420, 900 + 600 * stretch
    for x, label in ((xa, 'HUMAIN'), (xb, 'DANGER')):
        if t >= d0 - 0.3:
            d = ImageDraw.Draw(s.mid)
            d.ellipse((x - 46, 560 - 46, x + 46, 560 + 46), outline=S.ink(s) + (255,), width=7)
            Text_ = TY.Text(label, 'label', colour=S.ink(s))
            Text_.draw(s.mid, (x, 630), t, d0 - 0.3, anchor='m', sound=False)
    A.connect(s.mid, [(xa + 60, 560), (xb - 60, 560)], t, d0, dur=0.5, arrowhead=True, dots=False, colour=S.accent(s))
    words(s.top, (W / 2, 780), 'LA DISTANCE', 120, t, [w(cue(3, 'la distance')), w(cue(3, 'distance'))], fill=S.accent(s))
    return s


def sI(t, D):
    """Contrairement à une histoire racontée comme une succession de progrès, celle des armes suit une
    autre règle : chaque innovation déplace un équilibre."""
    s = Shot(t, D)
    s.camera(1.0, 1.04)
    for i, (card, x) in enumerate(zip(ROW, (340, 960, 1580))):          # one after the other: a 'succession'
        P.drop(s.mid, card, x, 480, t, ENTER + 0.45 * i, rot=(-3, 2, -2)[i], spin=10, key=f'row{i}')
    words(s.top, (W / 2, 150), 'PROGRÈS', 130, t, w(cue(4, 'progres')))
    A.strike(s.top, A.grow(A.text_box((W / 2, 150), 'PROGRÈS', 130), 30, -40), t, w(cue(4, 'autre regle')), scribble=True)
    A.emphasis(s.top, (W / 2, 790), 'ÉQUILIBRE', 120, t, w(cue(4, 'equilibre')))
    words(s.hud, (W / 2, 950), 'chaque innovation déplace un équilibre', 46, t,
          [w(cue(4, x)) for x in ('chaque', 'innovation', 'deplace', 'un equilibre', 'equilibre')], font=F_TYPE)
    return s


def sJ(t, D):
    """Elle peut protéger un groupe, accroître le pouvoir d'un chef, ou rendre une ancienne manière de
    combattre moins utile."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.03)
    for i, (txt, ph) in enumerate((('PROTÉGER UN GROUPE', 'proteger'), ("LE POUVOIR D'UN CHEF", 'pouvoir'),
                                   ('MOINS UTILE', 'moins utile'))):
        card = P.paper_card(760, 150, seed=40 + i, text=txt, size=58)
        P.drop(s.mid, card, 560 + i * 400, 300 + i * 220, t, w(cue(4, ph)) - 0.15, rot=(-4, 3, -2)[i], spin=10, key=f'tagcard{i}')
    return s


def sK(t, D):
    """Une arme est aussi une décision sociale, prise dans un monde de ressources, de croyances et de
    rivalités."""
    s = Shot(t, D)
    S.env(s, 'accent')
    s.camera(1.03, 1.0)
    phr = ('une arme', 'arme', 'est aussi', 'aussi', 'une decision', 'decision', 'sociale')
    S.type_page(s, 'Une arme est aussi une décision sociale.', t, ENTER, role='statement', size=92,
                xy=(W / 2, 300), cues=[w(cue(4, x)) for x in phr])
    for i, (word, ph) in enumerate((('RESSOURCES', 'ressources'), ('CROYANCES', 'croyances'), ('RIVALITÉS', 'rivalites'))):
        words(s.top, (480 + i * 480, 720), word, 60, t, w(cue(4, ph)), fill=S.ink(s))
    return s


SHOTS = [
    (0.0, sA),
    (cue(1, 'Ce') - LEAD, sB, 'up'),
    (cue(1, 'Le bois') - LEAD, sC, ('circle', {'at': (W / 2, H / 2)})),
    (cue(1, 'Le passe') - LEAD, sD, 'lr'),
    (cue(2, 'Elle mesure') - LEAD, sE, 'rl'),
    (cue(3, 'Cette decouverte') - LEAD, sF, 'up'),
    (cue(3, 'Le terme') - LEAD, sG, 'pageturn'),
    (cue(3, "L'histoire") - LEAD, sH, 'lr'),
    (cue(4, 'Contrairement') - LEAD, sI, 'shape'),
    (cue(4, 'Elle peut') - LEAD, sJ, 'rl'),
    (cue(4, 'Une arme est') - LEAD, sK, 'up'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
