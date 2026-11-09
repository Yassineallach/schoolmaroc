"""Lift a figure off its paper/ivory background into a clean transparent PNG.

Usage:
  python cutout.py SRC.png OUT.png [--crop x0,y0,x1,y1] [--mode standard|gentle|edge|ink] [--backed] [--head 0.2]

Modes (pick by what the figure is made of; then ALWAYS run check_cutout.py):
  standard  dark/saturated costumes. Removes border paper, enclosed paper pockets below the
            head zone (--head = fraction of height protecting eyes, teeth, lamp glass),
            shadowed paper in arm/leg gaps, and the pale fringe along the outline.
  gentle    costumes close to the paper colour (gold armour, cream tunics, pale dresses).
            Removes only near-exact paper pockets and a thin fringe; keeps interiors.
  edge      near-paper skin or horses (faces punch holes otherwise). Border paper only,
            then fills small holes and closes notches with the original drawn pixels.

Every mode keeps only the main figure (drops neighbour slivers from character sheets) and
crops to the figure's bounding box. Edge pixels take the colour from just inside the drawing,
so outlines never glow pale on dark scenes.
"""
import argparse
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd


def paper_colour(a):
    border = np.concatenate([a[:4].reshape(-1, 3), a[-4:].reshape(-1, 3), a[:, :4].reshape(-1, 3), a[:, -4:].reshape(-1, 3)])
    return np.median(border, axis=0)


def base_cut(a, bgc, head, remove_pockets, tol=62):
    h = a.shape[0]
    sm = nd.uniform_filter(a, size=(3, 3, 1))
    dist = np.sqrt(((sm - bgc) ** 2).sum(axis=2))
    cand = dist < tol
    lab, n = nd.label(cand)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    sizes = nd.sum(cand, lab, range(1, n + 1))
    cy = nd.center_of_mass(cand, lab, range(1, n + 1)) if n else []
    keep = np.zeros(n + 1, bool)
    for i in range(1, n + 1):
        if i in edge or (remove_pockets and sizes[i - 1] > 25 and cy[i - 1][0] > head * h):
            keep[i] = True
    bg = keep[lab]
    fg = nd.binary_opening(~bg, iterations=1)
    l2, n2 = nd.label(fg)
    if n2:
        s2 = nd.sum(fg, l2, range(1, n2 + 1))
        fg = np.isin(l2, [i + 1 for i, s in enumerate(s2) if s >= 0.02 * s2.max()])
    core = nd.binary_erosion(fg, iterations=2)
    band = fg & ~core
    d_raw = np.sqrt(((a - bgc) ** 2).sum(axis=2))
    alpha = core.astype(float)
    alpha[band] = np.clip((d_raw[band] - 45) / 70, 0, 1)
    _, idx = nd.distance_transform_edt(~core, return_indices=True)
    rgb = np.where(band[..., None], a[idx[0], idx[1]], a)
    a8 = np.array(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)), np.float32)
    return np.dstack([rgb, a8])


def shadowed_paper(a, bgc, head):
    """Remove paper that sits in shadow inside arm/leg gaps (standard mode)."""
    h = a.shape[0]
    for _ in range(3):
        d = np.sqrt(((nd.uniform_filter(a[..., :3], size=(3, 3, 1)) - bgc) ** 2).sum(axis=2))
        flag = (d < 82) & (a[..., 3] > 0)
        flag[:int(head * h)] = False
        lab, k = nd.label(flag)
        s = nd.sum(flag, lab, range(1, k + 1))
        flag = np.isin(lab, [i + 1 for i, v in enumerate(s) if v > 6])
        grow = nd.binary_dilation(flag, iterations=2) & (d < 105)
        grow[:int(head * h)] = False
        a[grow, 3] = 0
    return a


def fringe(a, bgc, head, tight=False):
    h = a.shape[0]
    for _ in range(3):
        d = np.sqrt(((a[..., :3] - bgc) ** 2).sum(axis=2))
        lum = a[..., :3].mean(axis=2)
        sat = a[..., :3].max(axis=2) - a[..., :3].min(axis=2)
        near = nd.binary_dilation(a[..., 3] < 30, iterations=3 if tight else 5)
        k = near & (a[..., 3] > 0) & ((d < 42) if tight else ((d < 95) | ((lum > 185) & (sat < 90))))
        k[:int(head * h)] = False
        a[k, 3] = 0
    return a


def gentle_pockets(a, bgc):
    d = np.sqrt(((nd.uniform_filter(a[..., :3], size=(5, 5, 1)) - bgc) ** 2).sum(axis=2))
    cand = (d < 26) & (a[..., 3] > 0)
    lab, n = nd.label(cand)
    s = nd.sum(cand, lab, range(1, n + 1))
    pock = np.isin(lab, [i + 1 for i, v in enumerate(s) if v > 350])
    a[nd.binary_dilation(pock, iterations=2) & (d < 40), 3] = 0
    return a


def fill_holes_and_notches(a, close_px=8):
    vis = a[..., 3] > 20
    holes = nd.binary_fill_holes(vis) & ~vis
    lab, n = nd.label(holes)
    s = nd.sum(holes, lab, range(1, n + 1))
    a[np.isin(lab, [i + 1 for i, v in enumerate(s) if v < 2500]), 3] = 255
    vis = a[..., 3] > 20
    pad = close_px + 2
    closed = nd.binary_closing(np.pad(vis, pad), structure=np.ones((3, 3)), iterations=close_px)[pad:-pad, pad:-pad]
    a[nd.binary_fill_holes(closed) & ~vis, 3] = 255
    return a


def main_body(a):
    vis = a[..., 3] > 20
    core = nd.binary_erosion(vis, iterations=4)
    lab, n = nd.label(core)
    if n:
        s = nd.sum(core, lab, range(1, n + 1))
        keep = nd.binary_dilation(lab == (np.argmax(s) + 1), iterations=6) & vis
        a[~keep, 3] = 0
    return a


def ink_cut(a, bgc, backed=False):
    """Line art / engravings: the paper becomes transparent and the lines become the episode's
    ink (palette text_primary), so the drawing reads as printed on the film's own paper.
    backed=True also fills the silhouette with the light paper colour, so an object laid over
    another object or a print hides what is underneath (closed outline needed)."""
    from scipy import ndimage
    try:
        import palette
        ink = np.array(palette.ACTIVE.ink[:3], float)
    except Exception:
        ink = np.array((36, 24, 15), float)
    lum = a @ np.array([0.299, 0.587, 0.114])
    pl = float(bgc @ np.array([0.299, 0.587, 0.114]))
    k = np.clip((pl - 18 - lum) / max(40.0, pl - 60), 0, 1) ** 0.85         # 0 on paper, 1 on solid ink
    r = np.zeros(a.shape[:2] + (4,), float)
    r[..., :3] = ink
    r[..., 3] = k * 255
    if backed:
        try:
            import palette
            light = np.array(palette.ACTIVE.cream[:3], float)
        except Exception:
            light = np.array((239, 227, 200), float)
        body = ndimage.binary_fill_holes(ndimage.binary_closing(k > 0.25, iterations=6))
        body = ndimage.binary_opening(body, iterations=2)
        r[..., :3] = light * (1 - k[..., None]) + ink * k[..., None]
        r[..., 3] = np.maximum(k, body.astype(float)) * 255
    return r


def ink_image(src, width=None, backed=False, crop=None):
    """In code: an ink drawing / engraving (path or PIL image) printed on the film's paper as RGBA.
    White paper becomes transparent, the lines take the identity's ink. Use it for ink plates
    (full-frame scenes) and ink objects without writing a file:
        LAKE = cutout.ink_image(asset('P03.png'), 1800)
        P.mask_reveal(s.mid, LAKE, W / 2, H / 2, t, 0.05, lip=False)"""
    im = (Image.open(src) if isinstance(src, str) else src).convert('RGB')
    if crop:
        im = im.crop(crop)
    if width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    a = np.asarray(im).astype(float)
    return Image.fromarray(ink_cut(a, paper_colour(a), backed).clip(0, 255).astype(np.uint8), 'RGBA')


def cut(src, out, crop=None, mode='standard', head=0.2, backed=False):
    im = Image.open(src).convert('RGB')
    bgc = paper_colour(np.asarray(im).astype(float))  # sample paper on the whole sheet, before cropping
    if crop:
        im = im.crop(crop)
    a = np.asarray(im).astype(float)
    if mode == 'standard':
        r = base_cut(a, bgc, head, remove_pockets=True)
        r = shadowed_paper(r, bgc, head)
        r = fringe(r, bgc, head)
    elif mode == 'gentle':
        r = base_cut(a, bgc, 1.0, remove_pockets=False)
        r = gentle_pockets(r, bgc)
        r = fringe(r, bgc, 0.0, tight=True)
    elif mode == 'ink':
        r = ink_cut(a, bgc, backed)
    elif mode == 'edge':
        r = base_cut(a, bgc, 1.0, remove_pockets=False)
        r = fringe(r, bgc, 0.0, tight=True)
        r = fill_holes_and_notches(r)
    else:
        raise SystemExit(f'unknown mode {mode}')
    if mode != 'ink':
        r = main_body(r)
    o = Image.fromarray(r.clip(0, 255).astype(np.uint8), 'RGBA')
    o = o.crop(o.getchannel('A').getbbox())
    o.save(out)
    print(f'{out}: {o.size[0]}x{o.size[1]}  paper={bgc.round().astype(int).tolist()}  mode={mode}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('out')
    ap.add_argument('--crop', help='x0,y0,x1,y1 in source pixels (for character sheets)')
    ap.add_argument('--mode', default='standard', choices=['standard', 'gentle', 'edge', 'ink'])
    ap.add_argument('--backed', action='store_true', help='ink mode: fill the silhouette with light paper')
    ap.add_argument('--head', type=float, default=0.2, help='fraction of height protected from pocket removal')
    a = ap.parse_args()
    cut(a.src, a.out, tuple(int(v) for v in a.crop.split(',')) if a.crop else None, a.mode, a.head, a.backed)
