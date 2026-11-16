"""Acte 1 « Le bug », rebuilt with vox-director's local motion engine (vd_motion.py, MIT).

vox-director style: each beat is a bold flat-colour collage poster; real images, article
clippings and cut-out headlines fly in and snap into place with a back-overshoot, settled
pieces breathe (sway + pulse), confetti drifts, entrances kick the camera (impact shake), and
beats are joined by whip pans. Same narration, same word timing, same real material as act1.py;
every word enters on (never before) the word that says it.

    python act1_vox.py sheet out/act1_vox_sheet.png 2 6 ...
    python act1_vox.py render out/act1_vox.mp4
"""
import math
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from vox import *  # noqa: F401,F403
import presets as P
import style as st
from style import event
import gta as G
import vd_motion as M

CLIPS = (1, 2, 3)
cue = make_cue(CLIPS)
FPSV = 30


# ------------------------------------------------------------------ pieces
class Piece(M.Layer):
    """vox-director Layer built from a PIL image instead of a file path."""
    def __init__(self, im, keys, sway=0.0, pulse=0.0, shadow=True, sound=None, x=None):
        self.im = im.convert('RGBA')
        self.keys = sorted(keys, key=lambda k: k['t'])
        self.sway, self.pulse, self.shadow, self.z = sway, pulse, shadow, 0
        if sound:
            event(sound, self.keys[0]['t'], x if x is not None else self.keys[-1]['x'])


def card(img, width, seed, tilt=0):
    c = P.print_card(img, width, seed=seed)
    return c.rotate(tilt, Image.BICUBIC, expand=True) if tilt else c


def cutout(text, size, bg=(250, 247, 238), fg=(20, 20, 20), seed=1, pad=(34, 18)):
    """A headline cut out of paper: torn-edged slip, heavy type."""
    f = F_HEAD(size)
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    l, t_, r, b = d.textbbox((0, 0), text, font=f)
    w, h = r - l + 2 * pad[0], b - t_ + 2 * pad[1]
    im = Image.new('RGBA', (w, h), bg + (255,))
    ImageDraw.Draw(im).text((pad[0] - l, pad[1] - t_), text, font=f, fill=fg + (255,))
    im.putalpha(torn_mask(w, h, seed, amp=4, step=10))
    return im


def sticker(text, size, bg, fg=(250, 247, 238), seed=3):
    return cutout(text, size, bg=bg, fg=fg, seed=seed, pad=(26, 12))


def halftone(w, h, col, step=26, r=5, seed=0):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(0, h, step):
        for x in range((y // step) % 2 * step // 2, w, step):
            d.ellipse((x - r, y - r, x + r, y + r), fill=col + (70,))
    return im


def poster(bg, accent, seed):
    """The beat's flat-colour poster ground: paper grain, a torn band, a halftone corner."""
    im = Image.new('RGBA', (W, H), bg + (255,))
    a = np.asarray(im).astype(np.float32)
    a[..., :3] += np.random.default_rng(seed).normal(0, 5, (H, W, 1))
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    band = Image.new('RGBA', (W + 200, 260), accent + (255,))
    band.putalpha(torn_mask(W + 200, 260, seed, amp=9, step=14))
    band = band.rotate(-6 if seed % 2 else 5, Image.BICUBIC, expand=True)
    im.alpha_composite(band, (-100, int(H * (0.62 if seed % 2 else 0.08))))
    im.alpha_composite(halftone(620, 420, (0, 0, 0), seed=seed), (W - 620 if seed % 2 else 0, H - 420))
    return im


# ------------------------------------------------------------------ material
DUNDEE = card(Image.open(asset('P01_dundee.jpg')), 1240, 11, tilt=-3)
MOCKUP = card(Image.open(asset('R01_racenchase.jpg')), 560, 12, tilt=4)
GTA1 = card(Image.open(asset('game/wikipedia/s01_gta1.png')), 620, 13, tilt=-4)
LOGO = P.load(asset('G01_gta1997.png'), width=760)
TAKE2 = P.load(asset('L02_take2.png'), width=230)
PENN, PENN_BOX = G.article('A01_penn_head.png', 'A01_penn_quote.png', 'Game Developer (Gamasutra)', '31 JANVIER 2011', width=1300)
GD, GD_BOX = G.article('A02_gd_head.png', 'A02_gd_475.png', 'Game Developer', '7 AOÛT 2026', width=1180, seed=23)
def marked(card, boxes):
    """The clipping with its quoted phrases already highlighted (multiplied in like marker ink)."""
    im = card.copy()
    for rects in boxes.values():
        G.highlight(im, (0, 0), rects, 99.0, 0.0)
    return im


PENN_HL = marked(PENN, PENN_BOX)
GD_HL = marked(GD, GD_BOX)


def reveal(t0, x, y, dur=0.35):
    return [dict(t=t0, x=x, y=y, s=1.0, r=0, a=0, e='linear'), dict(t=t0 + dur, x=x, y=y, s=1.0, r=0, a=1, e='out')]


FOLDER = document(520, 620, ['---', '---', '---', '---', '---', '---'], seed=8, title='PROJET', typed=True)


def car(kind, scale, heading):
    im = G._car(kind, 0)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    return im.rotate(-heading, Image.BICUBIC, expand=True)


C = lambda *a: cue(*a)

# ------------------------------------------------------------------ beats
# (start, end, background, accent, builder). Times in act seconds.
B = [C(1, 'Au'), C(1, 'un concepteur'), C(1, 'Ce jour'), C(2, 'Le program'), C(2, 'Le voiture'),
     C(2, 'Le concepteur'), C(2, 'Ce bug'), C(3, 'Ce projet'), C(3, 'Il deviendra'), C(3, 'Reste'), cue.total]
B[0] = 0.0
INK = (18, 18, 18)
CREAM_P = (247, 242, 230)
PAL_ = [((23, 52, 104), (230, 190, 60)),     # 1 Dundee: navy / mustard
        ((242, 196, 48), (24, 24, 24)),      # 2 the chase: tape yellow / black
        ((196, 38, 38), (24, 24, 24)),       # 3 they ram: red / black
        ((20, 20, 22), (196, 38, 38)),       # 4 broken: black / red
        ((36, 110, 120), (242, 196, 48)),    # 5 ram, push, surround: teal / yellow
        ((232, 224, 205), (196, 38, 38)),    # 6 Gary Penn: newsprint / red
        ((120, 30, 40), (232, 224, 205)),    # 7 abandoned: oxblood / paper
        ((242, 196, 48), (23, 52, 104)),     # 8 Race'n'Chase: yellow / navy
        ((23, 52, 104), (196, 38, 38)),      # 9 GTA, 475M: navy / red
        ((196, 38, 38), (242, 196, 48))]     # 10 the close: red / yellow
GROUNDS = [poster(bg, ac, 30 + i) for i, (bg, ac) in enumerate(PAL_)]
HITS = []                                     # impact times (camera shake)


def fly(t0, x, y, frm, spin=8, dur=0.6, s=1.0):
    HITS.append(t0 + dur * 0.8)
    return M.fly_in(t0, x, y, W, H, frm, spin=spin, dur=dur, s=s)


def slap(t0, x, y, s=1.0):
    HITS.append(t0 + 0.2)
    return M.slap(t0, x, y, s=s)


def drop(t0, x, y, s=1.0):
    HITS.append(t0 + 0.6)
    return M.drop(t0, x, y, H, s=s)


def pop(t0, x, y, s=1.0):
    return M.pop_settle(t0, x, y, s=s)


def beat_layers(i):
    a, b = B[i], B[i + 1]
    Ls = []
    if i == 0:      # « Au milieu des années 1990, dans un studio de Dundee, en Écosse »
        Ls += [Piece(DUNDEE, pop(a + 0.02, 1060, 520), sway=0.3, pulse=0.003, sound='drop'),
               Piece(cutout('MILIEU DES ANNÉES 1990', 64, seed=2), fly(C(1, 'annees'), 520, 150, 'L', spin=-6), sway=0.5, sound='whoosh'),
               Piece(sticker('DUNDEE', 92, (196, 38, 38), seed=4), slap(C(1, 'Dundee'), 1460, 900), sway=0.7, sound='stamp'),
               Piece(sticker('ÉCOSSE', 54, INK, seed=5), fly(C(1, 'Ecosse'), 1560, 1010, 'R', spin=10), sway=0.9, sound='whoosh')]
    elif i == 1:    # « un concepteur teste une course-poursuite... la police le suit... »
        Ls += [Piece(GTA1, drop(a + 0.05, 560, 560), sway=0.4, sound='drop'),
               Piece(cutout('UNE COURSE-POURSUITE', 78, seed=6), fly(C(1, 'course'), 1300, 210, 'R', spin=6), sway=0.5, sound='whoosh'),
               Piece(sticker('LE VOLEUR', 60, INK, (242, 196, 48), seed=7), slap(C(1, 'voleur'), 1180, 560), sway=0.8, sound='stamp'),
               Piece(car('thief', 2.2, 0), [dict(t=C(1, 'voleur'), x=-300, y=780, s=1, r=0, a=1, e='linear'),
                                             dict(t=b + 0.5, x=W + 300, y=780, s=1, r=0, a=1, e='linear')]),
               Piece(sticker('LA POLICE', 60, (196, 38, 38), seed=8), slap(C(1, 'police'), 1560, 640), sway=0.8, sound='stamp'),
               Piece(car('cop', 2.2, 0), [dict(t=C(1, 'police'), x=-300, y=900, s=1, r=0, a=1, e='linear'),
                                           dict(t=b + 0.5, x=W - 50, y=900, s=1, r=0, a=1, e='linear')])]
    elif i == 2:    # « Ce jour-là, les policiers ne se contentent plus de suivre. Ils foncent droit sur le joueur. »
        ram = C(1, 'foncent', 2)
        Ls += [Piece(car('thief', 3.0, 0), pop(a + 0.02, W / 2, 560), sway=0.6),
               Piece(car('cop', 3.0, 30), [dict(t=a, x=-420, y=180, s=1, r=0, a=1, e='linear'),
                                           dict(t=ram - 0.3, x=260, y=300, s=1, r=0, a=1, e='out'),
                                           dict(t=ram + 0.25, x=W / 2 - 330, y=470, s=1, r=-8, a=1, e='back')]),
               Piece(car('cop', 3.0, 150), [dict(t=a, x=W + 420, y=180, s=1, r=0, a=1, e='linear'),
                                            dict(t=ram - 0.3, x=W - 260, y=300, s=1, r=0, a=1, e='out'),
                                            dict(t=ram + 0.25, x=W / 2 + 330, y=470, s=1, r=8, a=1, e='back')]),
               Piece(cutout('ILS FONCENT', 120, bg=(250, 247, 238), seed=9), slap(ram, W / 2, 860), sway=0.6, sound='stamp')]
        HITS.append(ram + 0.25)
        event('stamp', ram + 0.25, W / 2)
    elif i == 3:    # « Leur programme de déplacement semble cassé. »
        Ls += [Piece(cutout('LEUR PROGRAMME', 96, bg=CREAM_P, seed=10), fly(a + 0.05, W / 2, 360, 'L', spin=-5), sway=0.4, sound='whoosh'),
               Piece(cutout('DE DÉPLACEMENT', 96, bg=CREAM_P, seed=11), fly(C(2, 'deplacement') - 0.1, W / 2, 520, 'R', spin=5), sway=0.4, sound='whoosh'),
               Piece(sticker('CASSÉ', 170, (196, 38, 38), seed=12), slap(C(2, 'casse'), W / 2 + 120, 790, s=1.0), sway=1.2, sound='stamp')]
    elif i == 4:    # « Les voitures de patrouille percutent, poussent et encerclent... lutte pour survivre »
        Ls += [Piece(car('thief', 2.6, 0), pop(a + 0.02, W / 2, 560), sway=0.8)]
        for k, (w_, x) in enumerate((('PERCUTENT', 'percutent'), ('POUSSENT', 'poussent'), ('ENCERCLENT', 'encerclent'))):
            t0 = C(2, x)
            ang = math.radians(200 + k * 120)
            Ls += [Piece(car('cop', 2.6, math.degrees(ang) + 180), fly(t0, W / 2 + 330 * math.cos(ang), 560 + 260 * math.sin(ang),
                                                                        ('L', 'R', 'B')[k], spin=12), sway=1.0),
                   Piece(sticker(w_, 58, ((196, 38, 38), INK, (196, 38, 38))[k], seed=13 + k), slap(t0 + 0.1, 360 + k * 600, 130), sway=0.8, sound='stamp')]
        Ls += [Piece(cutout('UNE LUTTE POUR SURVIVRE', 66, seed=17), fly(C(2, 'lutte'), W / 2, 960, 'B', spin=0), sway=0.4, sound='whoosh')]
    elif i == 5:    # Gary Penn
        Ls += [Piece(PENN, fly(a + 0.05, W / 2, 470, 'R', spin=4, dur=0.7), sway=0.15, sound='slide'),
               Piece(PENN_HL, reveal(C(2, 'racontera'), W / 2, 470), sway=0.15, shadow=False),
               Piece(sticker('GARY PENN', 70, (196, 38, 38), seed=18), slap(C(2, 'Gary'), 360, 110), sway=0.6, sound='stamp'),
               Piece(cutout('« LA POLICE EST DEVENUE FOLLE »', 56, seed=19), fly(C(2, 'parce'), W / 2, 980, 'B', spin=0), sway=0.3, sound='whoosh')]
    elif i == 6:    # « Ce bug allait relancer un projet qui risquait d'être abandonné. »
        Ls += [Piece(cutout('CE BUG', 150, bg=CREAM_P, seed=20), slap(a + 0.05, 560, 420), sway=0.6, sound='stamp'),
               Piece(FOLDER, drop(C(2, 'projet') - 0.1, 1350, 560), sway=0.5, sound='drop'),
               Piece(sticker('ABANDONNÉ ?', 70, INK, seed=21), slap(C(2, 'abandonne'), 1350, 600), sway=0.9, sound='stamp')]
    elif i == 7:    # « Ce projet s'appelait Race'n'Chase. »
        Ls += [Piece(MOCKUP, drop(a + 0.02, 600, 540), sway=0.5, sound='drop'),
               Piece(cutout("RACE'N'CHASE", 110, bg=CREAM_P, seed=22), slap(C(3, 'Race'), 1300, 480), sway=0.6, sound='stamp')]
    elif i == 8:    # « Il deviendra Grand Theft Auto ... Take-Two ... près de 475 millions d'exemplaires vendus »
        Ls += [Piece(LOGO, slap(C(3, 'Grand'), 560, 330), sway=0.5, pulse=0.004, sound='stamp'),
               Piece(GD, fly(C(3, 'Take') - 0.2, 1200, 640, 'R', spin=4, dur=0.6), sway=0.12, sound='slide'),
               Piece(GD_HL, reveal(C(3, '475') - 0.2, 1200, 640), sway=0.12, shadow=False),
               Piece(TAKE2, pop(C(3, 'Take') + 0.3, 1680, 330), sway=0.6),
               Piece(sticker('475 MILLIONS', 110, (242, 196, 48), INK, seed=23), slap(C(3, '475'), 560, 960), sway=0.8, pulse=0.006, sound='stamp')]
    elif i == 9:    # « Reste à comprendre comment une course-poursuite déréglée a donné naissance ... »
        cards = [(DUNDEE, 300, 300, -6), (GTA1, 1650, 280, 5), (MOCKUP, 330, 820, 4), (PENN, 1560, 830, -3)]
        for k, (im, x, y, r) in enumerate(cards):
            small = im.resize((int(im.width * 0.42), int(im.height * 0.42)), Image.LANCZOS).rotate(r, Image.BICUBIC, expand=True)
            Ls.append(Piece(small, fly(a + 0.1 + 0.15 * k, x, y, ('L', 'R', 'L', 'R')[k], spin=10), sway=0.6, sound='whoosh'))
        Ls += [Piece(cutout('UNE COURSE-POURSUITE', 84, bg=CREAM_P, seed=24), slap(C(3, 'course'), W / 2, 470), sway=0.4, sound='stamp'),
               Piece(sticker('DÉRÉGLÉE', 120, (242, 196, 48), INK, seed=25), slap(C(3, 'dereglee'), W / 2, 640), sway=1.0, pulse=0.006, sound='stamp')]
    return Ls


LAYERS = [beat_layers(i) for i in range(len(B) - 1)]
CONF = M.Confetti(W, H, n=34)
WHIP = 0.24


def beat_frame(i, t):
    cv = GROUNDS[i].copy()
    if i in (2, 8, 9) and t > B[i] + 0.3:                       # payoff beats: a turning starburst behind the pieces
        M.starburst(cv, W / 2, H / 2, t, R=1300, col=PAL_[i][1])
    for L in LAYERS[i]:
        L.draw(cv, t)
    return cv


def cam(t):
    a = max(x for x in B[:-1] if x <= t + 1e-9)
    b = min(x for x in B[1:] if x > t)
    z = 1.0 + 0.05 * (t - a) / max(0.1, b - a)
    sx = sy = 0.0
    for h in HITS:
        if 0 <= t - h < 0.6:
            d = t - h
            amp = 16 * math.exp(-8 * d)
            sx += amp * math.sin(d * 60)
            sy += amp * math.cos(d * 55)
    return z, sx, sy


def frame(t):
    i = max(k for k in range(len(B) - 1) if B[k] <= t + 1e-9)
    cv = beat_frame(i, t)
    nxt = i + 1 < len(B) - 1 and t > B[i + 1] - WHIP / 2
    prv = i > 0 and t < B[i] + WHIP / 2
    if nxt or prv:                                              # whip pan between beats
        j0, j1 = (i, i + 1) if nxt else (i - 1, i)
        p = (t - (B[j1] - WHIP / 2)) / WHIP
        p = 0.5 - 0.5 * math.cos(math.pi * max(0, min(1, p)))
        A_, B_ = beat_frame(j0, t), beat_frame(j1, t)
        strip = Image.new('RGBA', (2 * W, H))
        strip.paste(A_, (0, 0)); strip.paste(B_, (W, 0))
        off = int(p * W)
        cv = strip.crop((off, 0, off + W, H))
        blur = int(60 * math.sin(math.pi * p))
        if blur > 2:
            small = cv.resize((max(1, W // blur), H), Image.BILINEAR)
            cv = Image.blend(cv, small.resize((W, H), Image.BILINEAR), 0.75)
        if nxt and abs(t - B[i + 1]) < 1 / FPSV:
            event('whoosh', B[i + 1] - WHIP / 2, W / 2, dur=WHIP)
    CONF.draw(cv, t, 1 / FPSV)
    z, sx, sy = cam(t)
    zw, zh = int(W * z), int(H * z)
    big = cv.convert('RGB').resize((zw, zh), Image.LANCZOS)
    cx = max(0, min(zw - W, (zw - W) // 2 + int(sx)))
    cy = max(0, min(zh - H, (zh - H) // 2 + int(sy)))
    out = np.asarray(big.crop((cx, cy, cx + W, cy + H)))
    try:
        import brand
        out = brand.overlay(out, t)
    except Exception:
        pass
    return out


END = cue.total

if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    elif sys.argv[1] == 'render':
        out = sys.argv[2]
        render_video(frame, END, CLIPS, out, os.path.join(os.path.dirname(out), '_work_act1_vox'))
