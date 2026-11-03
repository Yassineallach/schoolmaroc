"""Editorial typography and kinetic type, English and Arabic.

HIERARCHY (role -> typeface, size, colour, case, tracking; Arabic has its own faces)
    headline   Archivo Black 128 / Noto Kufi Arabic 900      big discoveries, act ideas
    subhead    Archivo Black 64  / Noto Kufi Arabic 800      secondary lines
    statement  Fraunces 700 76   / Noto Kufi Arabic 700      dramatic sentences, said word by word
    name       Playfair 700 92   / Amiri Bold                people (editorial emphasis)
    date       Archivo Black 300 / Noto Kufi Arabic 900      years, oversized numerals
    stat       Archivo Black 240 / Noto Kufi Arabic 900      statistics
    caption    Special Elite 42  / Noto Naskh Arabic 500     explanatory captions (typed)
    quote      Fraunces 500 italic 64 / Amiri                quotations
    label      Inter 600 26 caps, +6 tracking / Noto Naskh 600   places, kickers, small labels
    term       Archivo Black 56 / Noto Kufi 800 + a caption gloss   technical terminology

    T = Text('THE UNIVERSE IS EXPANDING', 'headline', max_w=1400)        # layout once, at module level
    T.draw(layer, (160, 300), t, start, anim='words', cues=[w(cue(6, x)) for x in (...)])
    T.box('EXPANDING', (160, 300))        # pixel box of a word, for annotate.sweep / ring / strike

ANIMATIONS (anim=)                      Arabic text is shaped and right-to-left; letter-level
    words      word by word, rising inside its own slot (clipping mask)      animations fall back
    letters    letter-by-letter stagger                                       to word level, because
    lines      each line slides up from behind a clipping mask               Arabic letters join
    scale      words scale into position with a slight overshoot
    slide      words slide in from alternating directions (dirs=...)
    assemble   letters scattered on the desk converge into the headline
    split      the line splits horizontally, halves pull apart, then rejoin (contradictions)
    tracking   letter spacing closes from wide to the role's tracking
    cutout     each word on its own paper scrap, dropped onto the desk
    mask       revealed through a geometric shape: shape='circle' | 'diagonal' | 'bars' | 'rect'
    stamp      the whole line hits as a rubber stamp
    type       typewriter (Arabic types with live shaping); sound per key
    + accent={'WORD': at}   charcoal -> terracotta colour change on a cue (any anim)
    + until=..., exit='fade' | 'settle'

COMPOSITIONS
    press(...)       newspaper headline: rules draw, dateline types, headline wipes in
    big_number(...)  oversized number or year, digits rolling into place, label + accent bar
    term_card(...)   a technical term with a one-line gloss, bracketed
    name_card(...)   a person's name in editorial style with a role line and a rule
"""
import math, re
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import vox
from style import sfx

FONTS = vox.FONTS
TERRA = (205, 88, 48)
CHARCOAL = (44, 42, 40)
WARM_BLACK = (28, 24, 22)
CREAM = (244, 238, 224)
MUTED = (110, 104, 96)
ARABIC = re.compile(r'[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]')
AR_DIGITS = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')


def is_arabic(s):
    return bool(ARABIC.search(s))


@lru_cache(maxsize=128)
def face(file, size, weight=None):
    f = ImageFont.truetype(f'{FONTS}/{file}', size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


#           role:      (latin file, size, colour, upper, tracking, line-height) | (arabic file, size, weight)
ROLES = {
    'headline':  (('ArchivoBlack.ttf', 128, WARM_BLACK, True, -3, 1.02), ('NotoKufiArabic-VF.ttf', 112, 900)),
    'subhead':   (('ArchivoBlack.ttf', 64, CHARCOAL, True, -1, 1.08), ('NotoKufiArabic-VF.ttf', 58, 800)),
    'statement': (('Fraunces700.ttf', 76, WARM_BLACK, False, -1, 1.12), ('NotoKufiArabic-VF.ttf', 66, 700)),
    'name':      (('Playfair700.ttf', 92, WARM_BLACK, False, 0, 1.05), ('Amiri-Bold.ttf', 96, None)),
    'date':      (('ArchivoBlack.ttf', 300, TERRA, False, -8, 0.95), ('NotoKufiArabic-VF.ttf', 270, 900)),
    'stat':      (('ArchivoBlack.ttf', 240, WARM_BLACK, False, -6, 0.95), ('NotoKufiArabic-VF.ttf', 220, 900)),
    'caption':   (('SpecialElite.ttf', 42, CHARCOAL, False, 0, 1.35), ('NotoNaskhArabic-VF.ttf', 44, 500)),
    'quote':     (('Fraunces500i.ttf', 64, WARM_BLACK, False, 0, 1.2), ('Amiri-Regular.ttf', 66, None)),
    'label':     (('Inter600.ttf', 26, CHARCOAL, True, 6, 1.3), ('NotoNaskhArabic-VF.ttf', 30, 600)),
    'term':      (('ArchivoBlack.ttf', 56, WARM_BLACK, True, 0, 1.1), ('NotoKufiArabic-VF.ttf', 52, 800)),
}


def _c(x):
    return min(max(x, 0.0), 1.0)


def _ease(x):
    x = _c(x)
    return 1 - (1 - x) ** 3


def _eio(x):
    x = _c(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def _pop(u, amount=0.08):
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    return 1 - math.exp(-6 * u) * math.cos(7.5 * u) + amount * math.sin(math.pi * u) * (1 - u)


def _mix(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


class Text:
    """Laid-out text. Build once (module level), draw every frame."""

    def __init__(self, s, role='headline', size=None, colour=None, max_w=None, align=None, tracking=None,
                 upper=None, lang=None, lh=None, digits=None):
        self.role = role
        self.rtl = (lang == 'ar') if lang else is_arabic(s)
        (lf, lsize, lcol, lup, ltr, llh), (af, asize, aw) = ROLES[role]
        if self.rtl:
            self.font = face(af, size or asize, aw)
            self.tracking = 0
            up = False
            if digits == 'arabic':
                s = s.translate(AR_DIGITS)
        else:
            self.font = face(lf, size or lsize)
            self.tracking = ltr if tracking is None else tracking
            up = lup if upper is None else upper
        self.s = s.upper() if up else s
        self.size = size or (asize if self.rtl else lsize)
        self.colour = colour or lcol
        self.align = align or ('r' if self.rtl else 'l')
        # Arabic needs more room for dots and marks, except oversized numerals (no marks)
        self.lh = lh or ((1.12 if role in ('date', 'stat') else 1.5) if self.rtl else llh)
        asc, desc = self.font.getmetrics()
        self.asc, self.desc = asc, desc
        self.line_h = int(self.size * self.lh)
        self.pad = int(self.size * 0.35)
        self._layout(max_w)
        self._tiles = {}

    # ---------------------------------------------------------------- layout
    def _len(self, s):
        if self.rtl:
            return self.font.getlength(s, direction='rtl', language='ar')
        return self.font.getlength(s) + self.tracking * max(0, len(s) - 1)

    def _layout(self, max_w):
        words = self.s.split()
        space = self.font.getlength(' ') + self.tracking
        lines, cur, cw = [], [], 0
        for wd in words:
            wl = self._len(wd)
            if cur and max_w and cw + space + wl > max_w:
                lines.append(cur)
                cur, cw = [], 0
            cw += (space if cur else 0) + wl
            cur.append(wd)
        if cur:
            lines.append(cur)
        self.lines = []
        self.words = []                                 # (text, x, y, w, line)
        widths = []
        for li, ln in enumerate(lines):
            lw = sum(self._len(wd) for wd in ln) + space * (len(ln) - 1)
            widths.append(lw)
        self.w = max(widths) if widths else 0
        self.h = self.line_h * len(lines)
        for li, ln in enumerate(lines):
            lw = widths[li]
            off = {'l': 0, 'm': (self.w - lw) / 2, 'r': self.w - lw}[self.align]
            y = li * self.line_h
            if self.rtl:
                x = off + lw
                for wd in ln:
                    wl = self._len(wd)
                    x -= wl
                    self.words.append((wd, x, y, wl, li))
                    x -= space
            else:
                x = off
                for wd in ln:
                    wl = self._len(wd)
                    self.words.append((wd, x, y, wl, li))
                    x += wl + space
            self.lines.append((li, y, lw, off))
        # letter units (Latin only)
        self.letters = []
        for wi, (wd, x, y, wl, li) in enumerate(self.words):
            if self.rtl:
                self.letters.append((wd, x, y, wl, li, wi))
                continue
            for ci, ch in enumerate(wd):
                cx = x + self.font.getlength(wd[:ci]) + self.tracking * ci
                self.letters.append((ch, cx, y, self.font.getlength(ch), li, wi))

    def origin(self, xy, anchor='l'):
        """Top-left of the text block for an anchor point xy (anchor l / m / r, top edge at xy[1])."""
        x, y = xy
        return (x - {'l': 0, 'm': self.w / 2, 'r': self.w}[anchor], y)

    def box(self, word, xy, anchor='l', nth=1):
        """Pixel box of a word (or a run of words) after placement, for annotate.*."""
        ox, oy = self.origin(xy, anchor)
        target = word.upper().split() if self.s.isupper() and not self.rtl else word.split()
        ws = [w_[0] for w_ in self.words]
        hits = 0
        for i in range(len(ws)):
            if ws[i:i + len(target)] == target:
                hits += 1
                if hits == nth:
                    run = self.words[i:i + len(target)]
                    x0 = min(r[1] for r in run)
                    x1 = max(r[1] + r[3] for r in run)
                    y = run[0][2]
                    top = y + self.line_h / 2 - self.size * 0.42
                    return (ox + x0, oy + top, ox + x1, oy + top + self.size * 0.84)
        raise KeyError(f'{word!r} not in {self.s!r}')

    def bbox(self, xy, anchor='l'):
        ox, oy = self.origin(xy, anchor)
        return (ox, oy, ox + self.w, oy + self.h)

    # ---------------------------------------------------------------- tiles
    def _tile(self, s):
        """L-mode glyph mask for a word or letter, with padding."""
        if s in self._tiles:
            return self._tiles[s]
        w = int(self._len(s)) + 2 * self.pad
        h = self.line_h + 2 * self.pad
        m = Image.new('L', (max(1, w), h), 0)
        d = ImageDraw.Draw(m)
        base = self.pad + (self.line_h - (self.asc + self.desc)) / 2 + self.asc
        if self.rtl:
            d.text((self.pad + self._len(s), base), s, font=self.font, fill=255, anchor='rs', direction='rtl', language='ar')
        elif self.tracking and len(s) > 1:
            x = self.pad
            for ch in s:
                d.text((x, base), ch, font=self.font, fill=255, anchor='ls')
                x += self.font.getlength(ch) + self.tracking
        else:
            d.text((self.pad, base), s, font=self.font, fill=255, anchor='ls')
        self._tiles[s] = m
        return m

    def _whole(self):
        if '__whole__' not in self._tiles:
            m = Image.new('L', (int(self.w) + 2 * self.pad, int(self.h) + 2 * self.pad), 0)
            for wd, x, y, wl, li in self.words:
                m.paste(self._tile(wd), (int(x), int(y)), self._tile(wd))
            self._tiles['__whole__'] = m
        return self._tiles['__whole__']

    @staticmethod
    def _blit(layer, mask, x, y, colour, alpha=1.0, scale=1.0, rot=0.0, clip=None):
        if alpha <= 0.01:
            return
        m = mask
        if clip is not None:                     # clip = (dy): the glyph slides inside its own slot
            slot = Image.new('L', m.size, 0)
            slot.paste(m, (0, int(clip)))
            m = slot
        if abs(scale - 1) > 1e-3:
            nw, nh = max(1, int(m.width * scale)), max(1, int(m.height * scale))
            m2 = m.resize((nw, nh), Image.BICUBIC)
            x, y = x + (m.width - nw) / 2, y + (m.height - nh) / 2
            m = m2
        if abs(rot) > 0.05:
            w0, h0 = m.size
            m = m.rotate(rot, Image.BICUBIC, expand=True)
            x, y = x - (m.width - w0) / 2, y - (m.height - h0) / 2
        if alpha < 0.999:
            m = m.point(lambda v: int(v * alpha))
        tile = Image.new('RGBA', m.size, colour + (0,))
        tile.putalpha(m)
        x, y = int(round(x)), int(round(y))
        cx0, cy0 = max(0, -x), max(0, -y)
        cx1, cy1 = min(tile.width, layer.width - x), min(tile.height, layer.height - y)
        if cx1 > cx0 and cy1 > cy0:
            layer.alpha_composite(tile.crop((cx0, cy0, cx1, cy1)), (x + cx0, y + cy0))

    # ---------------------------------------------------------------- draw
    def draw(self, layer, xy, t, start, anim='words', anchor='l', cues=None, dur=None, stagger=None,
             colour=None, accent=None, accent_colour=TERRA, until=None, exit='fade', dirs='alt',
             shape='circle', seed=3, shot=None, sound=True):
        """Draw the text at xy (anchor l/m/r on the top edge) animated from `start`.
        cues: one start time per word (narration sync); otherwise words follow `stagger`."""
        if t < start - 0.5 and anim not in ('stamp',):
            return
        ox, oy = self.origin(xy, anchor)
        col0 = colour or self.colour
        life = 1.0
        if until is not None and t > until:
            k = _c((t - until) / 0.4)
            life = 1 - k if exit == 'fade' else 1 - 0.6 * k
            if life <= 0.01:
                return
        nwords = len(self.words)
        stg = stagger if stagger is not None else {'letters': 0.035, 'scale': 0.12, 'slide': 0.11, 'cutout': 0.22, 'assemble': 0.0}.get(anim, 0.09)
        wstarts = list(cues) if cues else [start + i * stg for i in range(nwords)]
        if len(wstarts) < nwords:
            wstarts += [wstarts[-1] + stg * (i + 1) for i in range(nwords - len(wstarts))]
        if self.rtl and anim == 'letters':
            anim = 'words'

        def wcol(wi):
            if accent:
                wd = self.words[wi][0]
                for key, at in accent.items():
                    if wd.strip('.,;:!?"“”«»') == key or wd.upper().strip('.,;:!?"“”') == key.upper():
                        return _mix(col0, accent_colour, _c((t - at) / 0.35))
            return col0

        P = self.pad
        if anim in ('words', 'scale', 'slide', 'cutout'):
            if anim == 'cutout':
                self._cutouts(layer, ox, oy, t, wstarts, life, sound)
                return
            if sound and anim == 'slide':
                sfx('swipe', wstarts[0], ox + self.w / 2)
            for wi, (wd, x, y, wl, li) in enumerate(self.words):
                st = wstarts[wi]
                if t < st:
                    continue
                u = (t - st)
                m = self._tile(wd)
                X, Y = ox + x - P, oy + y - P
                if anim == 'words':
                    p = _ease(u / 0.38)
                    self._blit(layer, m, X, Y, wcol(wi), life * _c(u / 0.12), clip=(1 - p) * self.line_h * 0.9)
                elif anim == 'scale':
                    p = _pop(u / 0.5, 0.06)
                    self._blit(layer, m, X, Y, wcol(wi), life * _c(u / 0.2), scale=max(0.92, 1 + 0.7 * (1 - p)))   # overshoots below 1, settles
                elif anim == 'slide':
                    d_ = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}
                    order = ['left', 'right', 'down', 'up'] if dirs == 'alt' else [dirs]
                    dx, dy = d_[order[wi % len(order)]]
                    p = _pop(u / 0.55, 0.05)
                    dist = 380 * (1 - p)
                    self._blit(layer, m, X + dx * dist, Y + dy * dist * 0.6, wcol(wi), life * _c(u / 0.18))
            return

        if anim == 'letters':
            for i, (ch, x, y, wl, li, wi) in enumerate(self.letters):
                ci = sum(1 for L in self.letters[:i] if L[5] == wi)
                st = wstarts[wi] + ci * stg
                if t < st:
                    continue
                u = t - st
                p = _ease(u / 0.3)
                self._blit(layer, self._tile(ch), ox + x - P, oy + y - P - (1 - p) * self.size * 0.35, wcol(wi), life * _c(u / 0.15),
                           rot=(1 - p) * (8 if ci % 2 else -8))
            return

        if anim == 'lines':
            for li, ly, lw, off in self.lines:
                st = (wstarts[[w_[4] for w_ in self.words].index(li)] if cues else start + li * 0.16)
                if t < st:
                    continue
                p = _ease((t - st) / 0.5)
                for wi, (wd, x, y, wl, l2) in enumerate(self.words):
                    if l2 == li:
                        self._blit(layer, self._tile(wd), ox + x - P, oy + y - P, wcol(wi), life, clip=(1 - p) * self.line_h)
            return

        if anim == 'tracking':
            p = _ease((t - start) / (dur or 1.2))
            extra = (1 - p) * self.size * 0.6
            n = len(self.letters)
            if sound:
                sfx('whoosh', start + 0.3, ox + self.w / 2, dur=0.8)
            for i, (ch, x, y, wl, li, wi) in enumerate(self.letters):
                self._blit(layer, self._tile(ch), ox + x - P + extra * (i - (n - 1) / 2), oy + y - P, wcol(wi), life * _c((t - start) / 0.4))
            return

        if anim == 'assemble':
            r = np.random.default_rng(seed)
            if sound:
                sfx('assemble', start, ox + self.w / 2, n=min(9, len(self.letters)), stagger=0.04, dur=0.6)
            units = self.letters if not self.rtl else [(w_[0], w_[1], w_[2], w_[3], w_[4], i) for i, w_ in enumerate(self.words)]
            for i, (ch, x, y, wl, li, wi) in enumerate(units):
                sx, sy, sr = r.uniform(-500, 500), r.uniform(-260, 260), r.uniform(-50, 50)
                p = _pop((t - start - i * 0.025) / (dur or 0.8), 0.04)
                if p <= 0:
                    continue
                k = 1 - min(p, 1.0)
                self._blit(layer, self._tile(ch), ox + x - P + sx * k, oy + y - P + sy * k, wcol(wi), life * _c(p * 3), rot=sr * k)
            return

        if anim == 'split':
            # whole line drawn; at `start` it slices in two along its middle, halves pull apart,
            # then rejoin at start + (dur or 1.2)
            m = self._whole()
            hold = dur or 1.2
            k = _eio((t - start) / 0.35) * (1 - _eio((t - start - hold) / 0.4))
            gap, shift = 26 * k, 90 * k
            for li, ly, lw, off in self.lines:            # every line is sliced through its own middle
                y0, mid, y1 = int(ly + P / 2), int(P + ly + self.line_h * 0.52), int(ly + self.line_h + P / 2)   # bands never overlap
                top, bot = m.crop((0, y0, m.width, mid)), m.crop((0, mid, m.width, min(m.height, y1)))
                self._blit(layer, top, ox - P - shift, oy - P + y0 - gap / 2, col0, life)
                self._blit(layer, bot, ox - P + shift, oy - P + mid + gap / 2, col0, life)
            if sound:
                sfx('tear', start, ox + self.w / 2, dur=0.5)
            return

        if anim == 'mask':
            m = self._whole()
            p = _ease((t - start) / (dur or 0.8))
            if p <= 0:
                return
            w_, h_ = m.size
            mk = Image.new('L', (w_, h_), 0)
            d = ImageDraw.Draw(mk)
            if shape == 'circle':
                cxm = w_ * (0.85 if self.rtl else 0.15)
                R = math.hypot(max(cxm, w_ - cxm), h_) * 1.05 * p     # reaches the far corner
                d.ellipse((cxm - R, h_ / 2 - R, cxm + R, h_ / 2 + R), fill=255)
            elif shape == 'diagonal':
                e = -h_ + (w_ + 2 * h_) * p
                d.polygon([(0, 0), (e, 0), (e - h_, h_), (0, h_)] if not self.rtl else [(w_, 0), (w_ - e, 0), (w_ - e + h_, h_), (w_, h_)], fill=255)
            elif shape == 'bars':
                n = 6
                for i in range(n):
                    q = _ease((t - start - i * 0.06) / (dur or 0.6))
                    y0 = i * h_ / n
                    d.rectangle((0, y0, w_ * q, y0 + h_ / n + 1), fill=255)
            else:
                d.rectangle((w_ / 2 * (1 - p), h_ / 2 * (1 - p), w_ / 2 * (1 + p), h_ / 2 * (1 + p)), fill=255)
            out = Image.fromarray(np.minimum(np.asarray(m), np.asarray(mk)))
            if shape in ('circle', 'diagonal') and p < 1:   # the geometric shape itself, in terracotta, behind
                sh = Image.fromarray((np.asarray(mk).astype(np.float32) * 0.9 * (1 - p)).astype(np.uint8))
                self._blit(layer, sh, ox - P, oy - P, TERRA, life)
            self._blit(layer, out, ox - P, oy - P, col0, life)
            if sound:
                sfx('whoosh', start + 0.2, ox + self.w / 2, dur=0.6)
            return

        if anim == 'stamp':
            import presets as PR
            if t < start - 0.2:
                return
            if shot is not None:
                shot.hit(start)
            if sound:
                sfx('stamp', start, ox + self.w / 2)
            m = self._whole()
            bw, bh = m.width, m.height
            st_ = Image.new('L', (bw + 40, bh + 20), 0)
            d = ImageDraw.Draw(st_)
            d.rectangle((P - 4, P - 4, bw - P + 44, bh - P + 16), outline=255, width=max(4, int(self.size * 0.06)))
            st_.paste(m, (20, 10), m)
            a = np.asarray(st_).astype(np.float32)
            rr = np.random.default_rng(len(self.s))
            a[rr.random(a.shape) < 0.12] = 0
            st_ = Image.fromarray(a.astype(np.uint8))
            if t < start:
                u = _c((t - start + 0.2) / 0.2)
                self._blit(layer, st_, ox - P - 20, oy - P - 10, colour or TERRA, life * (0.25 + 0.5 * u), scale=1.9 - 0.9 * u ** 2, rot=-8 + 4 * (1 - u))
            else:
                k = _c((t - start) / 0.12)
                self._blit(layer, st_, ox - P - 20, oy - P - 10, colour or TERRA, life, scale=1.04 - 0.04 * k, rot=-8)
            return

        if anim == 'type':
            self.typewriter(layer, (ox, oy), t, start, colour=col0, life=life, sound=sound, cps=(1 / stg if stagger else 18))
            return
        raise ValueError(f'unknown anim {anim!r}')

    def _cutouts(self, layer, ox, oy, t, wstarts, life, sound):
        import presets as PR
        for wi, (wd, x, y, wl, li) in enumerate(self.words):
            key = ('cut', self.s, wi)
            if key not in self._tiles:
                m = self._tile(wd)
                card = PR.paper_card(m.width + 10, m.height - self.pad, seed=wi * 7 + 3, colour=(246, 241, 229))
                ink = Image.new('RGBA', card.size, self.colour + (0,))
                im2 = Image.new('L', card.size, 0)
                im2.paste(m, (5, -self.pad // 2))
                ink.putalpha(im2)
                card.alpha_composite(ink)
                self._tiles[key] = card
            card = self._tiles[key]
            cx, cy = ox + x + wl / 2, oy + y + self.line_h / 2
            PR.drop(layer, PR.fade_img(card, life), cx, cy, t, wstarts[wi], rot=(-3, 2, -1.5, 3)[wi % 4], spin=(-10, 8)[wi % 2],
                    height=0.5, key=('cutd',) + key + (round(life, 2),))

    def typewriter(self, layer, xy, t, start, colour=None, cps=18, cursor=True, life=1.0, sound=True):
        """Characters appear at `cps`; Arabic is re-shaped every frame so letters join correctly
        as they are typed. Multi-line text types line by line."""
        ox, oy = xy
        col = colour or self.colour
        total = 0
        for li, ly, lw, off in self.lines:
            words = [w_[0] for w_ in self.words if w_[4] == li]
            line = ' '.join(words)
            n = len(line)
            if sound:
                for k in range(0, n, 2):
                    sfx('type', start + (total + k) / cps, ox + off + lw / 2, n=2, cps=cps)
            shown = int(max(0, (t - start) * cps) - total)
            total += n + 4
            if shown <= 0:
                break
            s = line[:min(n, shown)]
            d = ImageDraw.Draw(layer)
            base = oy + ly + (self.line_h - (self.asc + self.desc)) / 2 + self.asc
            fill = col + (int(255 * life),)
            if self.rtl:
                xr = ox + off + lw
                d.text((xr, base), s, font=self.font, fill=fill, anchor='rs', direction='rtl', language='ar')
                cx = xr - self._len(s) - 10
            else:
                x = ox + off
                if self.tracking:
                    for ch in s:
                        d.text((x, base), ch, font=self.font, fill=fill, anchor='ls')
                        x += self.font.getlength(ch) + self.tracking
                    cx = x + 4
                else:
                    d.text((x, base), s, font=self.font, fill=fill, anchor='ls')
                    cx = x + self.font.getlength(s) + 4
            if cursor and shown < n and int(t * 3) % 2 == 0:
                d.rectangle((cx, base - self.size * 0.7, cx + self.size * 0.42, base + self.size * 0.1), fill=TERRA + (220,))


# ==================================================================== compositions
def press(layer, xy, headline, t, start, width=1500, dateline='', role='headline', size=96, colour=WARM_BLACK, sound=True):
    """A newspaper headline: a double rule draws across, the dateline types, the headline is
    wiped in left to right (right to left for Arabic) behind the moving rule."""
    import annotate as A
    rtl = is_arabic(headline)
    x, y = xy
    T = Text(headline, role, size=size, max_w=width, align='m', colour=colour)
    if sound:
        sfx('pencil', start, x + width / 2, dur=0.6)
    p = _ease((t - start) / 0.6)
    for dy, wd in ((0, 5), (10, 2)):
        a, b = (x, x + width * p) if not rtl else (x + width * (1 - p), x + width)
        if p > 0:
            ImageDraw.Draw(layer).rectangle((a, y + dy, b, y + dy + wd), fill=colour + (255,))
    if dateline:
        D = Text(dateline, 'label', align='l' if not rtl else 'r')
        D.typewriter(layer, (x if not rtl else x + width - D.w, y + 24), t, start + 0.35, cps=30, cursor=False, sound=sound)
    hy = y + 90
    m = T._whole()
    q = _ease((t - start - 0.55) / 0.7)
    if q > 0:
        mk = Image.new('L', m.size, 0)
        if not rtl:
            ImageDraw.Draw(mk).rectangle((0, 0, m.width * q, m.height), fill=255)
        else:
            ImageDraw.Draw(mk).rectangle((m.width * (1 - q), 0, m.width, m.height), fill=255)
        out = Image.fromarray(np.minimum(np.asarray(m), np.asarray(mk)))
        Text._blit(layer, out, x + (width - T.w) / 2 - T.pad, hy - T.pad, colour)
        edge = x + (width - T.w) / 2 + (T.w * q if not rtl else T.w * (1 - q))
        if q < 1:
            ImageDraw.Draw(layer).rectangle((edge - 3, hy - 10, edge + 3, hy + T.h + 10), fill=TERRA + (255,))
    by = hy + T.h + 24
    if q > 0.9:
        ImageDraw.Draw(layer).rectangle((x, by, x + width, by + 2), fill=colour + (255,))
    return T


def big_number(layer, xy, value, t, start, role='date', label=None, anchor='m', roll=True, dur=1.2, colour=None, accent_bar=True, sound=True, lang=None):
    """Oversized numerals: each digit rolls into place (left to right), a label in small caps
    sits under it, a terracotta bar draws beneath. value: '1963', '237', '10M', '٢٣٧'."""
    T = Text(str(value), role, colour=colour, lang=lang)
    ox, oy = T.origin(xy, anchor)
    col = colour or T.colour
    s = T.s
    digits = '0123456789' if not is_arabic(s) else '٠١٢٣٤٥٦٧٨٩'
    if sound:
        for k in range(8):
            sfx('tick', start + dur * (1 - (1 - k / 8) ** 0.5), ox + T.w / 2)
    if t < start:
        return T
    x = 0.0
    seq = list(s) if not T.rtl else list(s)
    for i, ch in enumerate(seq):
        cw = T.font.getlength(ch) + T.tracking
        u = _ease((t - start - i * 0.1) / dur)
        if ch in digits and roll:
            target = digits.index(ch)
            pos = target + 10 * (1 - u) * (1 + i * 0.3)           # spins a little over a full turn
            frac = pos - math.floor(pos)
            d0 = digits[int(math.floor(pos)) % 10]
            d1 = digits[(int(math.floor(pos)) + 1) % 10]
            slot = Image.new('L', (int(cw) + 2 * T.pad, T.line_h + 2 * T.pad), 0)
            for dd, off in ((d0, -frac), (d1, 1 - frac)):
                g = T._tile(dd)
                slot.paste(g, (0, int(off * T.line_h * 0.92)), g)
            mk = Image.new('L', slot.size, 0)
            ImageDraw.Draw(mk).rectangle((0, T.pad + T.size * 0.02, slot.width, T.pad + T.line_h * 0.98), fill=255)
            Text._blit(layer, Image.fromarray(np.minimum(np.asarray(slot), np.asarray(mk))), ox + x - T.pad, oy - T.pad, col, _c((t - start - i * 0.1) / 0.15))
        else:
            Text._blit(layer, T._tile(ch), ox + x - T.pad, oy - T.pad - (1 - u) * 40, col, _c((t - start - i * 0.1) / 0.2))
        x += cw
    if accent_bar:
        b = _ease((t - start - dur * 0.7) / 0.5)
        if b > 0:
            ImageDraw.Draw(layer).rectangle((ox, oy + T.h - T.size * 0.02, ox + T.w * b, oy + T.h + T.size * 0.03), fill=TERRA + (255,))
    if label:
        L = Text(label, 'label', align='m' if anchor == 'm' else ('r' if T.rtl else 'l'))
        L.draw(layer, (ox + T.w / 2 if anchor == 'm' else ox, oy + T.h + T.size * 0.1), t, start + dur * 0.8, anim='words', anchor=anchor if anchor == 'm' else 'l', sound=False)
    return T


def term_card(layer, xy, term, gloss, t, start, width=820, anchor='l', until=None):
    """Technical terminology made concrete: the term in bold caps with a terracotta bracket,
    then a one-line gloss typed under it."""
    import annotate as A
    T = Text(term, 'term', max_w=width)
    G = Text(gloss, 'caption', max_w=width)
    ox, oy = T.origin(xy, anchor)
    rtl = T.rtl
    T.draw(layer, (ox, oy), t, start, anim='lines', until=until)
    G.typewriter(layer, (ox + (T.w - G.w if rtl else 0), oy + T.h + 10), t, start + 0.45, cps=28, cursor=False)
    bx = ox - 26 if not rtl else ox + max(T.w, G.w) + 26
    A.bracket(layer, bx, oy + 6, oy + T.h + G.h + 10, t, start + 0.2, side='left' if not rtl else 'right', dur=0.4, sound=False,
              until=until)
    return T, G


def name_card(layer, xy, name, role_line, t, start, anchor='l', until=None, accent=TERRA):
    """A person's name with editorial emphasis: small-caps role line, the name in display serif
    revealed line by line, a short terracotta rule drawing beneath."""
    R = Text(role_line, 'label')
    N = Text(name, 'name')
    ox, oy = N.origin(xy, anchor)
    rtl = N.rtl
    R.draw(layer, (ox + (N.w - R.w if rtl else 0), oy), t, start, anim='words', until=until, sound=False)
    N.draw(layer, (ox, oy + R.h), t, start + 0.15, anim='lines', until=until)
    p = _ease((t - start - 0.5) / 0.4)
    if p > 0:
        x0 = ox if not rtl else ox + N.w - 140 * p
        ImageDraw.Draw(layer).rectangle((x0, oy + R.h + N.h + 6, x0 + 140 * p, oy + R.h + N.h + 14), fill=accent + (255,))
    return N
