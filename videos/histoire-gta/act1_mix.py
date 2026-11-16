"""Acte 1 « Le bug », mixed: paper desk for the calm, sourced beats (act1.py) and vox-director
flat-colour posters for the punchy ones (act1_vox.py). Style changes are whip pans.

    python act1_mix.py sheet out/act1_mix_sheet.png 2 6 ...
    python act1_mix.py render out/act1_mix.mp4
"""
import math
import os
import sys
import numpy as np
from PIL import Image
from vox import *  # noqa: F401,F403
from style import event
import act1 as PAPER
import act1_vox as VOX

CLIPS = PAPER.CLIPS
B = VOX.B                       # beat starts (act time), the same cues as act1.py's shots
VOX_BEATS = {2, 3, 4, 8, 9}     # « ils foncent », « cassé », percutent/poussent/encerclent, GTA + 475M, « déréglée »
WHIP = 0.26


def beat_of(t):
    return max(k for k in range(len(B) - 1) if B[k] <= t + 1e-9)


def vox_frame(i, t):
    cv = VOX.beat_frame(i, t)
    VOX.CONF.draw(cv, t, 1 / 30)
    z, sx, sy = VOX.cam(t)
    zw, zh = int(W * z), int(H * z)
    big = cv.convert('RGB').resize((zw, zh), Image.LANCZOS)
    cx = max(0, min(zw - W, (zw - W) // 2 + int(sx)))
    cy = max(0, min(zh - H, (zh - H) // 2 + int(sy)))
    return np.asarray(big.crop((cx, cy, cx + W, cy + H)))


def paper_frame(i, t):
    # keep the paper film inside beat i: no tear into a shot that the vox style replaces
    a, b = B[i], B[i + 1]
    lo = a + 0.22 if i > 0 and (i - 1) in VOX_BEATS else a
    hi = b - 0.42 if (i + 1) in VOX_BEATS else b
    return np.asarray(PAPER.frame(min(max(t, lo), hi)))[..., :3]


def styled(i, t):
    return vox_frame(i, t) if i in VOX_BEATS else paper_frame(i, t)


def whip(A_, B_, p):
    p = 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, p)))
    strip = np.concatenate([A_, B_], axis=1)
    off = int(p * W)
    cv = Image.fromarray(np.ascontiguousarray(strip[:, off:off + W]))
    blur = int(60 * math.sin(math.pi * p))
    if blur > 2:
        small = cv.resize((max(1, W // blur), H), Image.BILINEAR)
        cv = Image.blend(cv, small.resize((W, H), Image.BILINEAR), 0.75)
    return np.asarray(cv)


for k in range(1, len(B) - 1):                       # whoosh on every style change
    if ((k - 1) in VOX_BEATS) != (k in VOX_BEATS) or (k in VOX_BEATS and (k - 1) in VOX_BEATS):
        event('whoosh', B[k] - WHIP / 2, W / 2, dur=WHIP)


def frame(t):
    i = beat_of(t)
    for k in (i, i + 1):                             # a whip at boundary k when either side is vox
        if 0 < k < len(B) - 1 and abs(t - B[k]) < WHIP / 2 and ((k - 1) in VOX_BEATS or k in VOX_BEATS):
            p = (t - (B[k] - WHIP / 2)) / WHIP
            out = whip(styled(k - 1, t), styled(k, t), p)
            break
    else:
        out = styled(i, t)
    if i in VOX_BEATS:
        try:
            import brand
            out = brand.overlay(np.ascontiguousarray(out), t)
        except Exception:
            pass
    return np.ascontiguousarray(out)


END = PAPER.END

if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    elif sys.argv[1] == 'render':
        out = sys.argv[2]
        render_video(frame, END, CLIPS, out, os.path.join(os.path.dirname(out), '_work_act1_mix'))
