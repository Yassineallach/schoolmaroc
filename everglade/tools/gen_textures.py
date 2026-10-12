"""
Everglade - procedural painted textures (no external art).

  leaves.png  : 2x2 atlas of painted leaf clusters (grey-scale, tinted in-game
                by vertex colour) with an alpha cut-out silhouette.
  clouds.png  : 2x2 atlas of painterly cumulus clouds (white tops, soft blue
                bellies) for the sky billboards.
  grass.png   : a strip of grass blades for distant grass cards.

    pip install pillow numpy
    python tools/gen_textures.py assets/textures
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def leaf_cluster(size, seed, leaves=520, pointy=True):
    rnd = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = size / 2
    # draw from the back (bottom, darker) to the front (top, lighter)
    pts = []
    for i in range(leaves):
        a = rnd.uniform(0, math.tau)
        r = (rnd.random() ** 0.85) * size * 0.40
        x = cx + math.cos(a) * r
        y = cy + math.sin(a) * r * 0.9
        pts.append((y + rnd.uniform(-10, 10), x, y))
    pts.sort(key=lambda p: -p[0])
    for _, x, y in pts:
        ang = rnd.uniform(0, math.tau)
        ln = rnd.uniform(0.055, 0.09) * size
        wd = ln * rnd.uniform(0.5, 0.72)
        # value: brighter towards upper-left (painted light) with jitter
        v = 0.45 + 0.6 * (1 - (y / size)) * 0.9 + 0.15 * (1 - x / size) + rnd.uniform(-0.07, 0.07)
        v = max(0.35, min(1.0, v))
        col = (int(255 * v), int(255 * v), int(255 * v), 255)
        poly = []
        for k in range(14):
            t = k / 13 * math.pi * 2
            px = math.cos(t) * ln * 0.5
            py = math.sin(t) * wd * 0.5 * (abs(math.cos(t)) ** 0.15 if pointy else 1)
            if pointy and math.cos(t) > 0.85:
                px *= 1.25
            rx = px * math.cos(ang) - py * math.sin(ang)
            ry = px * math.sin(ang) + py * math.cos(ang)
            poly.append((x + rx, y + ry))
        d.polygon(poly, fill=col)
        # thin darker vein / edge stroke for the painted look
        dv = int(255 * v * 0.78)
        d.line([poly[0], poly[7]], fill=(dv, dv, dv, 255), width=max(1, size // 256))
    img = img.filter(ImageFilter.SMOOTH)
    # crisp alpha (alpha-scissor friendly) with slightly grown edges
    a = np.array(img.split()[3]).astype(np.float32)
    a = np.where(a > 40, 255, 0).astype(np.uint8)
    img.putalpha(Image.fromarray(a))
    return img


def cloud(size, seed):
    rnd = random.Random(seed)
    w, h = size, size // 2
    mask = Image.new("L", (w, h), 0)
    shade = np.zeros((h, w), np.float32)
    d = ImageDraw.Draw(mask)
    blobs = []
    base = h * 0.82
    for i in range(rnd.randint(10, 14)):
        x = rnd.uniform(w * 0.18, w * 0.82)
        edge = 1 - abs(x - w / 2) / (w / 2)
        r = rnd.uniform(0.10, 0.17) * h * 2 * (0.45 + edge * 0.6)
        y = base - r * rnd.uniform(0.35, 0.8) - edge * h * 0.14
        r = min(r, y - 4)
        blobs.append((x, y, r))
    for x, y, r in blobs:
        d.ellipse([x - r, y - r, x + r, min(y + r, base)], fill=255)
    # soft flat belly made of small overlapping puffs
    for i in range(16):
        x = w * 0.2 + i / 15 * w * 0.6
        r = h * 0.08
        d.ellipse([x - r * 1.6, base - r * 1.5, x + r * 1.6, base], fill=255)
    yy, xx = np.mgrid[0:h, 0:w]
    lit = np.zeros((h, w), np.float32)
    for x, y, r in blobs:
        # each puff is lit from the upper-left
        dist = np.sqrt((xx - (x - r * 0.3)) ** 2 + (yy - (y - r * 0.4)) ** 2) / (r * 1.25)
        lit = np.maximum(lit, np.clip(1 - dist, 0, 1))
    m = np.array(mask.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    belly = np.clip((yy - (base - h * 0.32)) / (h * 0.32), 0, 1)
    v = np.clip(0.55 + lit * 0.7, 0, 1) * (1 - belly * 0.35)
    top = np.array([1.0, 1.0, 1.0])
    low = np.array([0.70, 0.80, 0.98])
    t = np.clip((v - 0.5) / 0.5, 0, 1)[..., None]
    rgb = low * (1 - t) + top * t
    out = np.dstack([rgb * 255, m * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def grass_strip(w, h, seed):
    rnd = random.Random(seed)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(90):
        x = rnd.uniform(0, w)
        bh = rnd.uniform(0.45, 1.0) * h
        lean = rnd.uniform(-0.25, 0.25) * bh
        bw = rnd.uniform(3, 7)
        v = rnd.uniform(0.7, 1.0)
        col = (int(255 * v),) * 3 + (255,)
        d.polygon([(x - bw, h), (x + bw, h), (x + lean, h - bh)], fill=col)
    return img


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "assets", "textures")
    os.makedirs(out, exist_ok=True)
    atlas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    for i in range(4):
        atlas.paste(leaf_cluster(512, 11 + i, pointy=i != 3), ((i % 2) * 512, (i // 2) * 512))
    atlas.save(os.path.join(out, "leaves.png"))
    catlas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    for i in range(4):
        catlas.paste(cloud(1024, 40 + i).resize((512, 256)), (0 if i % 2 == 0 else 512, (i // 2) * 512 + 128))
    catlas.save(os.path.join(out, "clouds.png"))
    grass_strip(512, 256, 7).save(os.path.join(out, "grass.png"))
    print("textures written to", out)


if __name__ == "__main__":
    main()
