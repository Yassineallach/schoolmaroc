"""The film's one picture system (the user's notes: « the artwork animation must be consistent », then
the ink-sketch style of their goat reference).

Every picture is a ChatGPT drawing in one black ink-sketch style, a single subject on white
(PROMPTS.md). Each is shown the same way: cut out with its white kept as light paper and its lines in
the film's ink (cutout.ink_image, backed), laid on the same parchment (the astrolabe theme), revealed
through the same torn opening, under the same slow camera push, and every cut is the same torn wipe.
"""
import os
from functools import lru_cache
from PIL import Image, ImageDraw
from vox import W, H, F_HEAD, asset
import presets as P
import scenes as S
import cutout
from style import ENTER

BOX = (1500, 880)         # every drawing fits the same box
REVEAL = 1.2              # same reveal everywhere
PUSH = (1.0, 1.05)        # same slow push on every shot


def _placeholder(label):
    im = Image.new('RGB', (1500, 880), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 1480, 860), radius=30, outline=(0, 0, 0), width=8)
    d.text((750, 440), label, font=F_HEAD(56), fill=(0, 0, 0), anchor='mm')
    return im


class Drawing:
    def __init__(self, code, label):
        self.code, self.label = code, label
        self.path = next((asset(code + e) for e in ('.png', '.jpg') if os.path.exists(asset(code + e))), None)

    @lru_cache(maxsize=2)
    def ink(self, scale=1.0):
        if self.path:
            src = Image.open(self.path)
            if src.mode == 'RGBA':                      # transparent PNG: put it on white first
                bg = Image.new('RGB', src.size, (255, 255, 255)); bg.paste(src, (0, 0), src); src = bg
            src = src.convert('RGB')
        else:
            src = _placeholder(f'{self.code} · {self.label}')
        k = min(BOX[0] * scale / src.width, BOX[1] * scale / src.height)
        return cutout.ink_image(src, int(src.width * k), backed=True)


def drawing(code, label):
    return Drawing(code, label)


def plate(s, d, t, start=ENTER, focus_to=(0.5, 0.5), scale=1.0, cx=W / 2, cy=H / 2 + 10):
    """The drawing on the parchment, revealed and pushed the same way in every shot."""
    S.env(s, 'theme')
    im = d.ink(scale)
    fx = cx - im.width / 2 + focus_to[0] * im.width
    fy = cy - im.height / 2 + focus_to[1] * im.height
    s.camera(PUSH[0], PUSH[1], (W / 2, H / 2), (fx, fy))
    P.mask_reveal(s.mid, im, cx, cy, t, start, dur=REVEAL, lip=False, origin=(0.5, 0.55))


def cuts(shots):
    """Same torn wipe on every cut, alternating direction."""
    return [sh if i == 0 else (sh[0], sh[1], 'lr' if i % 2 else 'rl') for i, sh in enumerate(shots)]
