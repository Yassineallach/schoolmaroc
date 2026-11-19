"""The film's one picture system (the user's note: « the artwork animation must be consistent »).

Every picture is a ChatGPT drawing in one engraving style (PROMPTS.md). Each is printed the same way:
the white paper turns transparent and the lines take the film's ink (cutout.ink_image), on the same
parchment ground (the astrolabe theme), revealed through the same torn opening, under the same slow
camera push, and every shot is joined by the same torn-paper wipe, alternating direction.
"""
import os
from functools import lru_cache
from PIL import Image, ImageDraw
from vox import W, H, INK, F_HEAD, asset
import presets as P
import scenes as S
import cutout
from style import ENTER

PLATE_W = 1720            # every drawing at the same size
REVEAL = 1.2              # same reveal length everywhere
PUSH = (1.0, 1.05)        # same slow push on every shot


def _placeholder(label):
    im = Image.new('RGB', (1672, 941), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((10, 10, 1661, 930), outline=(0, 0, 0), width=5)
    for i in range(0, 1672, 28):               # light hatching so it reads as an engraving stand-in
        d.line((i, 930, i + 300, 10), fill=(225, 225, 225), width=2)
    d.text((836, 470), label, font=F_HEAD(60), fill=(0, 0, 0), anchor='mm')
    return im


class Drawing:
    def __init__(self, code, label):
        self.code, self.label = code, label
        self.path = next((asset(code + e) for e in ('.png', '.jpg') if os.path.exists(asset(code + e))), None)

    @lru_cache(maxsize=4)
    def ink(self, width):
        src = Image.open(self.path).convert('RGB') if self.path else _placeholder(f'{self.code} · {self.label}')
        return cutout.ink_image(src, width)


def drawing(code, label):
    return Drawing(code, label)


def plate(s, d, t, start=ENTER, focus_to=(0.5, 0.5), width=PLATE_W, cx=W / 2, cy=H / 2):
    """The drawing on the parchment, revealed and pushed the same way in every shot."""
    S.env(s, 'theme')
    im = d.ink(width)
    fx = cx - im.width / 2 + focus_to[0] * im.width
    fy = cy - im.height / 2 + focus_to[1] * im.height
    s.camera(PUSH[0], PUSH[1], (W / 2, H / 2), (fx, fy))
    P.mask_reveal(s.mid, im, cx, cy, t, start, dur=REVEAL, lip=False, origin=(0.5, 0.5))


def cuts(shots):
    """Same torn wipe on every cut, alternating direction."""
    out = []
    for i, sh in enumerate(shots):
        out.append(sh if i == 0 else (sh[0], sh[1], 'lr' if i % 2 else 'rl'))
    return out
