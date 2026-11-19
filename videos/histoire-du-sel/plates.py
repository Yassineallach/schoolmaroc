"""The film's one picture system (the user's notes: « the artwork animation must be consistent »,
then the flat vector style of their Freepik reference).

Every picture is a ChatGPT illustration in one flat-vector style (PROMPTS.md), shown the same way:
full frame, colours untouched (no sepia, no paper), the same slow push towards the subject, and the
same cut between every shot, alternating direction.
"""
import os
from functools import lru_cache
from PIL import Image, ImageDraw
from vox import W, H, F_HEAD, asset
from style import ease_io
import scenes as S

PUSH = (1.0, 1.05)        # the same slow push on every shot
MARGIN = 1.06             # cached cover size, a little larger than the largest zoom


def _placeholder(label):
    im = Image.new('RGB', (1672, 941), (246, 238, 228))
    d = ImageDraw.Draw(im)
    d.polygon([(0, 941), (520, 380), (900, 941)], fill=(81, 58, 71))
    d.polygon([(600, 941), (1150, 300), (1672, 941)], fill=(237, 98, 43))
    d.polygon([(1000, 941), (1400, 520), (1672, 760), (1672, 941)], fill=(255, 184, 51))
    d.text((836, 160), label, font=F_HEAD(56), fill=(66, 34, 31), anchor='mm')
    return im


class Drawing:
    def __init__(self, code, label):
        self.code, self.label = code, label
        self.path = next((asset(code + e) for e in ('.png', '.jpg') if os.path.exists(asset(code + e))), None)

    @lru_cache(maxsize=2)
    def cover(self):
        src = Image.open(self.path).convert('RGB') if self.path else _placeholder(f'{self.code} · {self.label}')
        bw, bh = int(W * MARGIN), int(H * MARGIN)
        s = max(bw / src.width, bh / src.height)
        im = src.resize((int(src.width * s + 1), int(src.height * s + 1)), Image.LANCZOS)
        x0, y0 = (im.width - bw) // 2, (im.height - bh) // 2
        return im.crop((x0, y0, x0 + bw, y0 + bh))


def drawing(code, label):
    return Drawing(code, label)


def plate(s, d, t, focus_to=(0.5, 0.5), **_):
    """The illustration full frame, pushing slowly from the whole picture towards focus_to."""
    S.env(s, 'bleed')
    base = d.cover()
    k = ease_io(min(1.0, max(0.0, t / max(s.D, 0.1))))
    z = PUSH[0] + (PUSH[1] - PUSH[0]) * k
    fx, fy = 0.5 + (focus_to[0] - 0.5) * k, 0.5 + (focus_to[1] - 0.5) * k
    ww, wh = base.width / (MARGIN * z), base.height / (MARGIN * z)    # the frame's view at zoom z
    cx = base.width / 2 + (fx - 0.5) * (base.width - ww)
    cy = base.height / 2 + (fy - 0.5) * (base.height - wh)
    box = (cx - ww / 2, cy - wh / 2, cx + ww / 2, cy + wh / 2)
    frame = base.resize((W, H), Image.BILINEAR, box=box).convert('RGBA')
    s.mid.alpha_composite(frame)


def cuts(shots):
    """Same cut on every shot, alternating direction."""
    return [sh if i == 0 else (sh[0], sh[1], 'lr' if i % 2 else 'rl') for i, sh in enumerate(shots)]
