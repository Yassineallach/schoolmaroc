"""
Everglade - procedural surface materials (no external art).

Writes two 16-slice texture strips (each slice 512x512, seamlessly tileable):

  mat_albedo.png : RGB = detail colour around mid-grey (it multiplies the
                   painted vertex colour, so 0.5 = "no change"), A = roughness
  mat_normal.png : tangent-space normal map (x = +u, y = +v image rows)

Slices (keep in sync with shaders/materials.gdshaderinc):
   0 painted     1 cut stone    2 rough rock   3 wood planks
   4 bark        5 plaster      6 roof tiles   7 woven cloth
   8 metal       9 moss/leafy  10 cobbles     11 straw
  12 meadow     13 dirt        14 flagstones  15 sand

    pip install numpy pillow
    python tools/gen_materials.py assets/textures
"""
import os
import sys

import numpy as np
from PIL import Image

S = 512
N_SLICES = 16


# ---------------------------------------------------------------------------
# tileable noise helpers
# ---------------------------------------------------------------------------
def vnoise(rnd, px, py=None):
    """Periodic value noise with px x py cells over the tile."""
    py = py or px
    g = rnd.random((py, px))
    xs = np.arange(S) * px / S
    ys = np.arange(S) * py / S
    x0 = np.floor(xs).astype(int)
    y0 = np.floor(ys).astype(int)
    fx = xs - x0
    fy = ys - y0
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    x1 = (x0 + 1) % px
    y1 = (y0 + 1) % py
    a = g[np.ix_(y0, x0)]
    b = g[np.ix_(y0, x1)]
    c = g[np.ix_(y1, x0)]
    d = g[np.ix_(y1, x1)]
    fx = fx[None, :]
    fy = fy[:, None]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(rnd, px, octaves=5, py=None, gain=0.5):
    py = py or px
    v = np.zeros((S, S))
    amp = 1.0
    total = 0.0
    for o in range(octaves):
        v += vnoise(rnd, px * 2 ** o, py * 2 ** o) * amp
        total += amp
        amp *= gain
    return v / total


def worley(rnd, n):
    """Tileable cellular noise: returns F1, F2 (in cell units) and cell id."""
    pts = rnd.random((n, n, 2))
    ids = rnd.random((n, n))
    u = (np.arange(S) + 0.5) * n / S
    X, Y = np.meshgrid(u, u)
    cx = np.floor(X).astype(int)
    cy = np.floor(Y).astype(int)
    f1 = np.full((S, S), 9.0)
    f2 = np.full((S, S), 9.0)
    cid = np.zeros((S, S))
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            gx = cx + ox
            gy = cy + oy
            p = pts[gy % n, gx % n]
            d = np.hypot(gx + p[..., 0] - X, gy + p[..., 1] - Y)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            cid = np.where(closer, ids[gy % n, gx % n], cid)
            f1 = np.where(closer, d, f1)
    return f1, f2, cid


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def normal_map(h, strength):
    dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5 * strength * S / 64.0
    dy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5 * strength * S / 64.0
    n = np.stack([-dx, -dy, np.ones_like(h)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n


def tint(v, rgb=(1.0, 1.0, 1.0)):
    """Grey-scale detail value -> RGB around 0.5 with a gentle tint."""
    return np.stack([v * rgb[0], v * rgb[1], v * rgb[2]], axis=-1)


def running_bond(rnd, rows, wmin, wmax, jitter=0.0):
    """Rectangular blocks laid in rows. Returns (edge distance px, block id, row index)."""
    row_h = S / rows
    edge = np.zeros((S, S))
    bid = np.zeros((S, S))
    yy = np.arange(S)
    for r in range(rows):
        y0 = int(round(r * row_h))
        y1 = int(round((r + 1) * row_h))
        widths = []
        while sum(widths) < S:
            widths.append(rnd.uniform(wmin, wmax))
        scale = S / sum(widths)
        cuts = np.cumsum([0] + [w * scale for w in widths])
        shift = rnd.uniform(0, S)
        xs = (np.arange(S) + shift) % S
        k = np.searchsorted(cuts, xs, side="right") - 1
        left = xs - cuts[k]
        right = cuts[k + 1] - xs
        ex = np.minimum(left, right)
        ids = rnd.random(len(widths) + 1)
        for y in range(y0, y1):
            ey = min(y - y0 + 0.5, y1 - y - 0.5)
            edge[y] = np.minimum(ex, ey)
            bid[y] = ids[k]
    return edge, bid, (yy // row_h)[:, None]


# ---------------------------------------------------------------------------
# materials: each returns (albedo grey/rgb HxWx3 around 0.5, height, roughness)
# ---------------------------------------------------------------------------
def m_painted(rnd):
    strokes = fbm(rnd, 3, 4, py=12) * 0.6 + fbm(rnd, 8, 4) * 0.4
    v = 0.5 + (strokes - 0.5) * 0.12
    return tint(v), strokes * 0.25, 0.8


def m_stone(rnd):
    edge, bid, _ = running_bond(rnd, 8, 70, 150)
    grain = fbm(rnd, 6, 5)
    chips = worley(rnd, 28)
    pits = smoothstep(0.08, 0.0, chips[0]) * 0.5
    bevel = smoothstep(0.0, 7.0, edge)
    h = bevel * (0.75 + bid * 0.15) + (grain - 0.5) * 0.35 - pits * 0.3
    mortar = 1.0 - smoothstep(1.0, 3.5, edge)
    v = 0.5 * (0.84 + bid * 0.3) * (0.85 + grain * 0.3) * (1.0 - pits * 0.25)
    v = v * (1 - mortar) + 0.27 * mortar * (0.9 + grain * 0.2)
    # dark grime collecting along the lower edges of each block
    v *= 1.0 - (1.0 - smoothstep(0.0, 14.0, edge)) * 0.12
    warm = 0.98 + bid * 0.05
    return tint(v, (warm, 1.0, 2.0 - warm)), h, 0.85


def m_rock(rnd):
    f1, f2, cid = worley(rnd, 7)
    cracks = smoothstep(0.0, 0.07, f2 - f1)
    big = fbm(rnd, 3, 6)
    strata = np.sin((np.arange(S)[:, None] / S * 9 + big * 3.0) * np.pi * 2) * 0.5 + 0.5
    h = big * 0.8 + cracks * 0.35 + strata * 0.12 + cid * 0.15
    v = 0.5 * (0.78 + big * 0.38 + cid * 0.12) * (0.62 + cracks * 0.38) * (0.92 + strata * 0.1)
    return tint(v, (1.01, 1.0, 0.99)), h, 0.9


def m_wood(rnd):
    planks = 4
    ph = S // planks
    yy = np.arange(S)[:, None]
    py = yy % ph
    pid = yy // ph
    gap = 1.0 - smoothstep(0.0, 3.0, np.minimum(py, ph - 1 - py).astype(float))
    grain = np.zeros((S, S))
    for p in range(planks):
        g = fbm(rnd, 2, 4, py=40) * 0.6 + vnoise(rnd, 1, 96) * 0.4
        g = np.roll(g, rnd.integers(0, S), axis=1)
        grain[p * ph:(p + 1) * ph] = g[p * ph:(p + 1) * ph]
    rings = np.sin(grain * 38.0) * 0.5 + 0.5
    tone = np.array([rnd.uniform(0.85, 1.15) for _ in range(planks)])[pid]
    # occasional knots
    f1, _, cid = worley(rnd, 5)
    knot = smoothstep(0.16, 0.0, f1) * (cid > 0.6)
    v = 0.5 * tone * (0.8 + rings * 0.22 + grain * 0.15) * (1 - knot * 0.45)
    v = v * (1 - gap) + 0.16 * gap
    h = 0.6 + rings * 0.12 - gap * 0.6 - knot * 0.15
    return tint(v, (1.03, 1.0, 0.95)), h, 0.75


def m_bark(rnd):
    ridges = fbm(rnd, 36, 3, py=3) * 0.65 + fbm(rnd, 72, 2, py=6) * 0.35
    deep = smoothstep(0.4, 0.58, ridges)
    breaks = fbm(rnd, 6, 3, py=10)
    h = deep * 0.9 + breaks * 0.2
    v = 0.5 * (0.55 + deep * 0.55) * (0.9 + breaks * 0.2)
    return tint(v, (1.02, 1.0, 0.96)), h, 0.95


def m_plaster(rnd):
    mottle = fbm(rnd, 4, 6)
    fine = fbm(rnd, 48, 2)
    f1, _, _ = worley(rnd, 40)
    pits = smoothstep(0.1, 0.0, f1)
    trowel = np.sin((np.arange(S)[None, :] / S * 6 + mottle * 4) * np.pi * 2) * 0.5 + 0.5
    v = 0.5 * (0.93 + (mottle - 0.5) * 0.16 + fine * 0.04) * (1 - pits * 0.12)
    h = mottle * 0.2 + fine * 0.12 + trowel * 0.05 - pits * 0.25
    return tint(v, (1.01, 1.0, 0.98)), h, 0.9


def m_tiles(rnd):
    rows, cols = 8, 8
    rh, cw = S / rows, S / cols
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    row = np.floor(yy / rh)
    x = (xx + (row % 2) * cw * 0.5) % S
    col = np.floor(x / cw)
    fx = (x - col * cw) / cw - 0.5
    fy = (yy - row * rh) / rh
    # each tile overlaps the one below: rises toward its rounded lower lip
    curve = 1.0 - (2 * fx) ** 2
    rnd_t = rnd.random((rows, cols))[row.astype(int) % rows, col.astype(int) % cols]
    grain = fbm(rnd, 8, 4)
    h = fy * 0.6 + curve * 0.35 + grain * 0.1
    edge = smoothstep(0.5, 0.42, np.abs(fx))
    shade = (0.7 + fy * 0.35) * (0.86 + edge * 0.14)
    v = 0.5 * shade * (0.88 + rnd_t * 0.24) * (0.9 + grain * 0.2)
    gapline = smoothstep(0.04, 0.0, np.abs(fy - 0.0))
    v *= 1 - gapline * 0.45
    h = h - gapline * 0.4
    return tint(v), h, 0.65


def m_cloth(rnd):
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    f = 2 * np.pi * 96 / S
    warp = np.sin(xx * f) * 0.5 + 0.5
    weft = np.sin(yy * f) * 0.5 + 0.5
    over = (np.floor(xx * 96 / S) + np.floor(yy * 96 / S)) % 2
    weave = np.where(over > 0, warp, weft)
    slub = fbm(rnd, 6, 3, py=48)
    v = 0.5 * (0.86 + weave * 0.16 + (slub - 0.5) * 0.12)
    h = weave * 0.5 + slub * 0.15
    return tint(v), h, 0.95


def m_metal(rnd):
    f1, f2, cid = worley(rnd, 22)
    dents = np.sqrt(np.clip(f1, 0, 1))
    scratches = fbm(rnd, 2, 3, py=128)
    v = 0.5 * (0.86 + cid * 0.12 + (scratches - 0.5) * 0.16) * (0.9 + dents * 0.15)
    h = dents * 0.5 + scratches * 0.1
    rough = 0.35
    return tint(v), h, rough


def m_moss(rnd):
    blades = fbm(rnd, 40, 3, py=10) * 0.5 + fbm(rnd, 10, 3, py=40) * 0.5
    clumps = fbm(rnd, 5, 4)
    v = 0.5 * (0.72 + blades * 0.34 + (clumps - 0.5) * 0.3)
    h = blades * 0.6 + clumps * 0.4
    return tint(v, (1.0, 1.02, 0.94)), h, 0.95


def m_cobble(rnd):
    f1, f2, cid = worley(rnd, 9)
    d = f2 - f1
    dome = np.sqrt(np.clip(smoothstep(0.0, 0.45, d), 0, 1))
    mortar = 1.0 - smoothstep(0.03, 0.09, d)
    grain = fbm(rnd, 16, 3)
    h = dome * 0.9 + grain * 0.1
    v = 0.5 * (0.78 + cid * 0.36) * (0.88 + grain * 0.2) * (0.8 + dome * 0.2)
    v = v * (1 - mortar) + 0.22 * mortar
    return tint(v, (1.0 + cid * 0.04, 1.0, 1.0 - cid * 0.03)), h, 0.85


def m_straw(rnd):
    a = vnoise(rnd, 3, 180) * 0.6 + vnoise(rnd, 6, 90) * 0.4
    b = np.rot90(vnoise(rnd, 3, 150))
    strands = np.maximum(a, b * 0.85)
    v = 0.5 * (0.7 + strands * 0.5)
    return tint(v, (1.02, 1.0, 0.92)), strands, 0.9


def m_meadow(rnd):
    blades = vnoise(rnd, 64, 12) * 0.4 + vnoise(rnd, 12, 64) * 0.3 + vnoise(rnd, 90, 90) * 0.3
    clumps = fbm(rnd, 4, 4)
    v = 0.5 * (0.8 + blades * 0.26 + (clumps - 0.5) * 0.28)
    h = blades * 0.5 + clumps * 0.3
    return tint(v, (1.0, 1.01, 0.97)), h, 0.95


def m_dirt(rnd):
    base = fbm(rnd, 6, 6)
    f1, f2, cid = worley(rnd, 36)
    pebble = smoothstep(0.28, 0.12, f1) * (cid > 0.55)
    v = 0.5 * (0.84 + (base - 0.5) * 0.38) * (1 + pebble * (cid - 0.55) * 0.9)
    h = base * 0.45 + pebble * 0.5
    return tint(v, (1.02, 1.0, 0.96)), h, 0.95


def m_flagstone(rnd):
    edge, bid, _ = running_bond(rnd, 3, 140, 260)
    grain = fbm(rnd, 8, 5)
    f1, f2, _ = worley(rnd, 4)
    crack = smoothstep(0.012, 0.0, f2 - f1) * (bid > 0.65)
    bevel = smoothstep(0.0, 6.0, edge)
    joint = 1.0 - smoothstep(1.5, 4.0, edge)
    h = bevel * (0.8 + bid * 0.12) + grain * 0.12 - crack * 0.3
    v = 0.5 * (0.82 + bid * 0.3) * (0.88 + grain * 0.22) * (1 - crack * 0.4)
    v = v * (1 - joint) + 0.25 * joint
    return tint(v, (1.0 + bid * 0.03, 1.0, 0.99)), h, 0.8


def m_sand(rnd):
    grain = vnoise(rnd, 160) * 0.5 + vnoise(rnd, 80) * 0.5
    ripples = np.sin((np.arange(S)[:, None] / S * 14 + fbm(rnd, 3, 3) * 2.5) * 2 * np.pi) * 0.5 + 0.5
    v = 0.5 * (0.9 + (grain - 0.5) * 0.2 + ripples * 0.06)
    h = ripples * 0.4 + grain * 0.2
    return tint(v, (1.01, 1.0, 0.97)), h, 0.95


MATERIALS = [
    (m_painted, 0.6), (m_stone, 3.2), (m_rock, 3.0), (m_wood, 2.2),
    (m_bark, 3.4), (m_plaster, 1.6), (m_tiles, 2.6), (m_cloth, 1.4),
    (m_metal, 1.8), (m_moss, 2.4), (m_cobble, 3.4), (m_straw, 2.0),
    (m_meadow, 2.0), (m_dirt, 2.4), (m_flagstone, 3.0), (m_sand, 1.4),
]


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    alb = np.zeros((S, S * N_SLICES, 4), np.uint8)
    nrm = np.zeros((S, S * N_SLICES, 3), np.uint8)
    for i, (fn, strength) in enumerate(MATERIALS):
        rnd = np.random.default_rng(1000 + i)
        rgb, h, rough = fn(rnd)
        h = (h - h.min()) / max(h.max() - h.min(), 1e-6)
        n = normal_map(h, strength)
        # detail multiplies the painted colour: keep each slice centred on 0.5
        rgb = np.clip(rgb * (0.5 / rgb.mean()), 0, 1)
        sl = slice(i * S, (i + 1) * S)
        alb[:, sl, :3] = (rgb * 255).astype(np.uint8)
        rmap = np.clip(rough + (h - 0.5) * 0.1, 0, 1) if np.isscalar(rough) else rough
        alb[:, sl, 3] = (rmap * 255).astype(np.uint8)
        nrm[:, sl] = ((n * 0.5 + 0.5) * 255).astype(np.uint8)
        print("material", i, fn.__name__, "mean", round(float(rgb.mean()), 3))
    Image.fromarray(alb, "RGBA").save(os.path.join(out_dir, "mat_albedo.png"), optimize=True)
    Image.fromarray(nrm, "RGB").save(os.path.join(out_dir, "mat_normal.png"), optimize=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "assets/textures")
