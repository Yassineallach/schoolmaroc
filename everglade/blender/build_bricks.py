"""
Everglade - Tiny Glade's stonework and brickwork, modelled in Blender from
its screenshots.

What the screenshots show:

  * Stone towers are faced in "broken-course" stonework: flat-faced
    rectangular blocks with only softly eased edges (not pillows), mixed
    sizes, courses that never run straight for long (some stones are one and
    a half or two courses tall), thin dark recessed joints, every stone set a
    little proud or back and a touch out of square. Cool lavender-grey stone,
    many blocks washed ochre or olive by lichen and sun.
  * Gothic windows sit in deep openings inside thick pale stone frames:
    pointed arches, two lancets under a round eye, leaded diamond panes.
  * A string course (a projecting band) runs round between the storeys.
  * Plastered towers have quoin piers at every corner: small creamy-yellow
    blocks, long and short in turn, interlocking round the corner. The pale
    sage plaster peels in soft patches showing the brick behind, and a
    projecting course of bricks runs under the top.

    python blender/build_bricks.py render <out.png>
    python blender/build_bricks.py export assets/models   # tg_window_tracery
"""

import math
import os
import random
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_wood as bw  # noqa: E402
import build_houses as bh  # noqa: E402
from build_wood import Piece, M_PAINT, M_STONE, M_METAL  # noqa: E402
from build_houses import lin  # noqa: E402

rng = random.Random(23)

GREY = [lin("#ABA6A8"), lin("#B4AEAC"), lin("#A09CA1"), lin("#BCB5AC"), lin("#A7A39C")]
LICHEN = [lin("#BDB984"), lin("#C9BF86"), lin("#ACB07F"), lin("#C2B27A")]
MORTAR = lin("#8C857C")
DRESSED = lin("#D7D0C0")      # window frames, string course
QUOIN = [lin("#D9C990"), lin("#CFBD84"), lin("#E0D3A0"), lin("#C8B47C"), lin("#D3C48E")]
PLASTER = [lin("#CDCFB6"), lin("#D4D4BB"), lin("#C8CBB0")]
LEAD = lin("#3B3530")


def stone_colour():
    c = rng.choice(GREY)
    k = rng.random() ** 1.6 * 0.85      # how much lichen
    t = rng.choice(LICHEN)
    b = rng.uniform(0.9, 1.08)
    return tuple(min(1.0, (c[i] * (1 - k) + t[i] * k) * b) for i in range(3))


# ---------------------------------------------------------------------------
# Broken-course stonework: a skyline packer
# ---------------------------------------------------------------------------
def broken_course(u0, u1, z0, z1, blocked=None, cell=0.05):
    """Packs blocks over [u0,u1] x [z0,z1] the way the stones go up: always
    filling the lowest gap, each stone as wide as fits (0.28-0.7 m) and one
    of a few heights, sometimes tall. blocked(u, z) vetoes cells (openings).
    Yields (u_centre, z_centre, w, h)."""
    n = int(round((u1 - u0) / cell))
    sky = [z0] * n
    heights = [0.2, 0.24, 0.28, 0.24, 0.32, 0.46]
    guard = 0
    while guard < 20000:
        guard += 1
        lo = min(sky)
        if lo >= z1 - 0.02:
            break
        i0 = sky.index(lo)
        i1 = i0
        while i1 < n and abs(sky[i1] - lo) < 1e-6:
            i1 += 1
        gap = (i1 - i0) * cell
        if i1 - i0 < 3:
            # too narrow for a stone: let the mortar take it up to the
            # lower of its neighbours
            nbs = [sky[i0 - 1]] if i0 > 0 else []
            if i1 < n:
                nbs.append(sky[i1])
            top = min(nbs) if nbs else lo + 0.1
            for k in range(i0, i1):
                sky[k] = max(lo + 0.02, top)
            continue
        want = rng.uniform(0.28, 0.7)
        w_cells = max(1, min(i1 - i0, int(round(want / cell))))
        # don't leave a sliver
        if 0 < (i1 - i0) - w_cells < int(0.2 / cell):
            w_cells = i1 - i0
        h = rng.choice(heights)
        # match a neighbouring stone's top now and then, so courses read
        nb = [sky[i0 - 1]] if i0 > 0 else []
        if i1 < n:
            nb.append(sky[i1])
        for t in nb:
            if 0.12 < t - lo < 0.5 and rng.random() < 0.55:
                h = t - lo
        h = min(h, z1 - lo)
        if z1 - (lo + h) < 0.12:
            h = z1 - lo
        if blocked:
            # near an opening try smaller stones so the coursing runs right
            # up to the frame; where nothing fits, step past one cell
            fit = None
            for (wc, hh) in ((w_cells, h), (max(3, w_cells * 2 // 3), h), (max(3, w_cells // 2), h),
                             (max(3, w_cells // 2), min(h, 0.18)), (4, min(h, 0.15))):
                wc = min(wc, i1 - i0)
                a = u0 + i0 * cell
                if not blocked(a + wc * cell / 2, lo + hh / 2, wc * cell, hh):
                    fit = (wc, hh)
                    break
            if fit is None:
                sky[i0] = lo + cell
                continue
            w_cells, h = fit
        a = u0 + i0 * cell
        b = a + w_cells * cell
        for k in range(i0, i0 + w_cells):
            sky[k] = lo + h
        yield ((a + b) / 2, lo + h / 2, b - a, h)


def lay_block(p, loc, rot, w, h, depth, color, chip=True):
    """A flat-faced stone with eased edges, a little out of square."""
    p.plank((w - 0.03, depth, h - 0.03), loc, rot=rot, color=color, mat=M_STONE, round_=0.13,
            vary=0.04, wonky=0.9)


# ---------------------------------------------------------------------------
# Gothic tracery window (pale dressed stone, two lancets, an eye, leading)
# ---------------------------------------------------------------------------
def pointed_points(half, spring, steps=14):
    """Outline of an equilateral pointed arch over [-half, half] from the
    springing line up, as (x, z) from the right jamb round to the left."""
    R, c = 2 * half, half
    pts = []
    for i in range(steps + 1):
        x = half - 2 * half * i / steps
        cx = -c if x >= 0 else c
        pts.append((x, spring + math.sqrt(max(0.0, R * R - (x - cx) ** 2))))
    return pts


def pointed_arc(p, half, spring, depth, thick, y, color):
    R, c = 2 * half, half
    a_end = math.acos(c / R)
    p.arc_frame(-c, spring, R, depth, thick, y=y, color=color, mat=M_STONE, a0=0.0, a1=a_end, steps=16)
    p.arc_frame(c, spring, R, depth, thick, y=y, color=color, mat=M_STONE, a0=math.pi - a_end, a1=math.pi, steps=16)


def tracery_window(W=1.0, spring=1.15):
    """Origin at the bottom centre of the opening, front facing -Y."""
    p = Piece("tracery")
    half = W / 2
    t = 0.12
    # thick outer frame: jambs and the pointed head, a deep sill
    for s in (-1, 1):
        p.plank((t, 0.3, spring), (s * (half + t / 2 - 0.02), 0.0, spring / 2), color=DRESSED, mat=M_STONE, round_=0.25, wonky=0.3)
    pointed_arc(p, half + t / 2 - 0.02, spring, 0.3, t, 0.0, DRESSED)
    p.plank((W + 0.34, 0.36, 0.1), (0, -0.06, -0.04), color=DRESSED, mat=M_STONE, round_=0.3, wonky=0.4)
    # mullion and the two lancets' heads
    p.plank((0.06, 0.16, spring + 0.1), (0, 0.04, (spring + 0.1) / 2), color=DRESSED, mat=M_STONE, round_=0.3, wonky=0.2)
    q = half / 2
    p2 = p
    for s in (-1, 1):
        R, c = 2 * (q - 0.01), (q - 0.01)
        a_end = math.acos(c / R)
        p2.arc_frame(s * q - c, spring - 0.05, R, 0.14, 0.05, y=0.04, color=DRESSED, mat=M_STONE, a0=0.0, a1=a_end, steps=10)
        p2.arc_frame(s * q + c, spring - 0.05, R, 0.14, 0.05, y=0.04, color=DRESSED, mat=M_STONE, a0=math.pi - a_end, a1=math.pi, steps=10)
    # the round eye above, with a little quatrefoil cross
    top = spring + math.sqrt(3) * half
    ez = spring + (top - spring) * 0.52
    p.ring(0.13, 0.03, (0, 0.04, ez), rot=(math.pi / 2, 0, 0), color=DRESSED, mat=M_STONE)
    for a in range(4):
        ang = a * math.pi / 2 + math.pi / 4
        p.ball(0.045, (math.cos(ang) * 0.07, 0.04, ez + math.sin(ang) * 0.07), DRESSED, mat=M_STONE)
    # leaded diamond panes over the glass, clipped to the outline
    outline = [(-half, 0.0), (half, 0.0)] + pointed_points(half, spring)

    def inside(x, z):
        n = len(outline)
        c = False
        for i in range(n):
            x1, z1 = outline[i]
            x2, z2 = outline[(i + 1) % n]
            if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1 + 1e-9) + x1:
                c = not c
        return c
    step = 0.15
    H = top
    k = -H
    while k < W + H:
        for sgn in (-1, 1):
            # line x = -half + k + sgn * z
            run = []
            best = []
            for i in range(80):
                z = H * i / 79
                x = -half + k + sgn * z if sgn > 0 else half - k + sgn * z
                if inside(x, z) and abs(x) < half - 0.03:
                    run.append((x, z))
                else:
                    if len(run) > len(best):
                        best = run
                    run = []
            if len(run) > len(best):
                best = run
            if len(best) >= 2:
                (xa, za), (xb, zb) = best[0], best[-1]
                L = math.hypot(xb - xa, zb - za)
                ang = math.atan2(zb - za, xb - xa)
                p.plank((L, 0.02, 0.018), ((xa + xb) / 2, 0.07, (za + zb) / 2), rot=(0, -ang, 0), color=LEAD,
                        mat=M_METAL, round_=0.4, wonky=0.0, vary=0.0)
        k += step
    p.glass(outline, 0.08)
    return p


# ---------------------------------------------------------------------------
# The round stone tower
# ---------------------------------------------------------------------------
def stone_tower(ox, oy):
    R = 2.3
    H = 5.6
    parts = []
    windows = []   # (angle, z sill, width, spring)
    for a in (-90, -45, -135):
        windows.append((math.radians(a), 0.95, 1.0 if a == -90 else 0.78, 1.0))
    for a in (-90, -45, -135):
        windows.append((math.radians(a), 3.4, 0.86 if a == -90 else 0.7, 0.85))
    core = Piece("tower_core")
    core.cyl(R - 0.12, H, (0, 0, H / 2), color=MORTAR, mat=M_STONE, seg=48)
    core = core.to_object()
    cuts = []
    for (ang, z, w, sp) in windows:
        out = bh.opening_outline(w + 0.2, sp, "pointed")
        m = Matrix.Translation((math.cos(ang) * R, math.sin(ang) * R, z)) @ Matrix.Rotation(ang + math.pi / 2, 4, "Z")
        cuts.append((m, out, 1.2))
    bh.cut_openings(core, cuts, lin("#9C968F"), M_STONE)
    parts.append(core)

    # each window's outline (frame included) in the face's (u, z) plane
    polys = []
    for (ang, wz, ww, spg) in windows:
        half = ww / 2 + 0.13
        uc = ((ang % (2 * math.pi))) * R
        pts = [(-half, -0.12), (half, -0.12)] + [(x * half / (ww / 2 + 0.0001) if False else x, z)
                                                for (x, z) in pointed_points(half, spg + 0.02)]
        polys.append([(uc + x, wz + z) for (x, z) in pts])

    def inside(poly, x, z):
        c = False
        n = len(poly)
        for i in range(n):
            x1, z1 = poly[i]
            x2, z2 = poly[(i + 1) % n]
            if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1 + 1e-9) + x1:
                c = not c
        return c

    def blocked(u, z, w, h):
        """Stones fill right up to the window frames (not their bounding box)."""
        for poly in polys:
            for du in (0.0, 2 * math.pi * R, -2 * math.pi * R):
                pts = [(u + du + sx * (w / 2 - 0.02), z + sz * (h / 2 - 0.02)) for sx in (-1, 0, 1) for sz in (-1, 0, 1)]
                if any(inside(poly, x, zz) for (x, zz) in pts):
                    return True
                for (px, pz) in poly:
                    if abs(px - (u + du)) < w / 2 - 0.02 and abs(pz - z) < h / 2 - 0.02:
                        return True
        return False

    sp = Piece("tower_stones")
    for (uc, zc, w, h) in broken_course(0.0, 2 * math.pi * R, 0.0, H, blocked):
        if 2.92 < zc < 3.08 and h < 0.15:
            continue
        a = uc / R
        depth = 0.22
        proud = rng.uniform(-0.01, 0.03)
        r = R - 0.1 + depth / 2 + proud
        lay_block(sp, (math.cos(a) * r, math.sin(a) * r, zc), (0, 0, a + math.pi / 2), w * (R - 0.04) / R, h, depth, stone_colour())
    # string course between the storeys, and a plinth course
    n = 40
    for zc, hh, out in ((2.98, 0.16, 0.1), (0.12, 0.24, 0.07)):
        for i in range(n):
            a = 2 * math.pi * (i + 0.5) / n
            if zc > 1 and any(abs(((a - wa + math.pi) % (2 * math.pi)) - math.pi) * R < ww / 2 + 0.2 and wz < zc < wz + sp + 1.0
                              for (wa, wz, ww, sp) in windows):
                continue
            r = R + out
            sp.plank((2 * math.pi * R / n + 0.02, 0.26, hh), (math.cos(a) * (r - 0.13), math.sin(a) * (r - 0.13), zc),
                     rot=(0, 0, a + math.pi / 2), color=DRESSED if zc > 1 else stone_colour(), mat=M_STONE, round_=0.25, wonky=0.5)
    parts.append(sp.to_object())
    # tracery windows set back in the openings
    for (ang, z, w, spg) in windows:
        bw.SURF = 0.0
        win = tracery_window(w, spg).to_object()
        r = R + 0.02 - 0.14
        win.matrix_world = Matrix.Translation((math.cos(ang) * r, math.sin(ang) * r, z)) @ Matrix.Rotation(ang + math.pi / 2, 4, "Z")
        parts.append(win)
    rp = Piece("tower_roof")
    bh.cone_roof(rp, 0, 0, R, H, 3.4, [lin("#6E6A80"), lin("#7A7590"), lin("#635F74"), lin("#857F95"), lin("#5A5669")])
    parts.append(rp.to_object())
    for o in parts:
        o.location = (o.location[0] + ox, o.location[1] + oy, o.location[2])
    return parts


# ---------------------------------------------------------------------------
# The plastered tower with quoin piers
# ---------------------------------------------------------------------------
def plaster_tower(ox, oy):
    S = 2.6       # outer size
    H = 5.4
    parts = []
    t = 0.3
    # plaster faces, set a little behind the quoins
    walls = Piece("pl_walls")
    for (sx, sy, x, y) in ((S - 0.3, t, 0, -S / 2 + t / 2 + 0.04), (S - 0.3, t, 0, S / 2 - t / 2 - 0.04),
                           (t, S - 0.3, -S / 2 + t / 2 + 0.04, 0), (t, S - 0.3, S / 2 - t / 2 - 0.04, 0)):
        walls.plank((sx, sy, H - 0.4), (x, y, (H - 0.4) / 2), color=rng.choice(PLASTER), mat=M_PAINT, round_=0.04, vary=0.0, wonky=0.0)
    parts.append(walls.to_object())
    q = Piece("quoins")
    # quoin piers: small blocks, long and short in turn on each face
    for (cx, cy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        z = 0.0
        k = 0
        while z < H - 0.3:
            h = rng.uniform(0.13, 0.17)
            long_x = k % 2 == 0
            lx = rng.uniform(0.36, 0.44) if long_x else rng.uniform(0.2, 0.26)
            ly = rng.uniform(0.2, 0.26) if long_x else rng.uniform(0.36, 0.44)
            x = cx * (S / 2 - lx / 2)
            y = cy * (S / 2 - ly / 2)
            q.plank((lx - 0.02, ly - 0.02, h - 0.025), (x + rng.uniform(-0.01, 0.01), y + rng.uniform(-0.01, 0.01), z + h / 2),
                    rot=(0, 0, rng.uniform(-0.03, 0.03)), color=rng.choice(QUOIN), mat=M_STONE, round_=0.18, wonky=1.0)
            z += h
            k += 1
    # brick courses under the top, projecting
    for (z, out) in ((H - 0.4, 0.06), (H - 0.26, 0.1)):
        for face in range(4):
            u = -S / 2 - out
            while u < S / 2 + out:
                w = min(rng.uniform(0.26, 0.36), S / 2 + out - u)
                if w > 0.06:
                    c = (u + w / 2)
                    loc = {0: (c, -S / 2 - out + 0.12, z), 1: (S / 2 + out - 0.12, c, z), 2: (-c, S / 2 + out - 0.12, z),
                           3: (-S / 2 - out + 0.12, -c, z)}[face]
                    q.plank((w - 0.025, 0.24, 0.13), loc, rot=(0, 0, face * math.pi / 2), color=rng.choice(QUOIN),
                            mat=M_STONE, round_=0.18, wonky=1.0)
                u += w
    # a timber rail across each face at mid height
    for face in range(4):
        loc = {0: (0, -S / 2 - 0.0, 1.9), 1: (S / 2, 0, 1.9), 2: (0, S / 2, 1.9), 3: (-S / 2, 0, 1.9)}[face]
        q.plank((S - 0.7, 0.08, 0.07), loc, rot=(0, 0, face * math.pi / 2), color=lin("#D6C79A"), mat=M_STONE, round_=0.3, wonky=0.3)
    # peeling plaster: soft patches of brick showing through
    for (face, pu, pz, rw, rh) in ((0, -0.4, 3.7, 0.5, 0.3), (0, 0.5, 1.1, 0.42, 0.26), (3, 0.3, 2.8, 0.46, 0.3),
                                   (0, 0.2, 4.6, 0.6, 0.2)):
        z = pz - rh
        row = 0
        while z < pz + rh:
            u = pu - rw - (0.07 if row % 2 else 0)
            while u < pu + rw:
                w = 0.26
                du = (u + w / 2 - pu) / rw
                dz = (z + 0.06 - pz) / rh
                if du * du + dz * dz < 1.0 + rng.uniform(-0.2, 0.15):
                    c = u + w / 2
                    loc = {0: (c, -S / 2 + 0.03, z + 0.06), 3: (-S / 2 + 0.03, -c, z + 0.06)}[face]
                    q.plank((w - 0.03, 0.08, 0.11), loc, rot=(0, 0, face * math.pi / 2), color=rng.choice(QUOIN),
                            mat=M_STONE, round_=0.2, wonky=1.2)
                u += w
            z += 0.13
            row += 1
    parts.append(q.to_object())
    rp = Piece("pl_roof")
    bh.gable_roof(rp, -S / 2, S / 2, S / 2, H, 1.6, bh.TERRACOTTA, over=0.3, gable_over=0.25, curve=0.08)
    for sgn in (-1, 1):
        gp = Piece("pgable")
        bm = gp.bm
        x = sgn * (S / 2 - 0.08)
        verts = [bm.verts.new((x, -S / 2, H)), bm.verts.new((x, S / 2, H)), bm.verts.new((x, 0, H + 1.45))]
        f = bm.faces.new(verts)
        bm.normal_update()
        import bmesh
        bmesh.ops.solidify(bm, geom=[f], thickness=0.16)
        gp._paint(list(bm.faces), rng.choice(PLASTER), M_PAINT)
        bh.flat_faces(gp, bm.faces)
        parts.append(gp.to_object())
    parts.append(rp.to_object())
    for o in parts:
        o.location = (o.location[0] + ox, o.location[1] + oy, o.location[2])
    return parts


def render(out):
    bw.reset()
    stone_tower(-2.6, 0)
    plaster_tower(3.4, 0.6)
    bh.stage(out, (0.6, 0.0, 3.0), 22.0, res=(1700, 1100), yaw=-10, pitch=14, lens=50)


def close(out):
    bw.reset()
    stone_tower(0, 0)
    bh.stage(out, (0.0, -2.0, 2.6), 9.0, res=(1600, 1000), yaw=-12, pitch=10, lens=50)


def export(out_dir):
    """tg_window_tracery for the game: origin at the bottom centre of its wall
    opening on the face, the frame set back into it (as build_wood's)."""
    bw.reset()
    surf = 0.14
    obj = tracery_window(0.8, 0.85).to_object()
    for o in [obj] + list(obj.children):
        if o.name.startswith("Glow"):
            continue
        for ca in o.data.color_attributes:
            for item in ca.data:
                c = item.color
                item.color = (bw._to_srgb(c[0]), bw._to_srgb(c[1]), bw._to_srgb(c[2]), c[3])
    obj.location = (0.0, surf, 0.0)
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.context.scene.objects:
        o.select_set(True)
    path = os.path.join(out_dir, "tg_window_tracery.glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_normals=True, export_vertex_color="ACTIVE",
                              export_all_vertex_colors=False, export_materials="EXPORT",
                              export_image_format="NONE", export_animations=False)
    print("exported", path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if args and args[0] == "render":
        render(args[1])
    elif args and args[0] == "close":
        close(args[1])
    elif args and args[0] == "export":
        export(os.path.abspath(args[1]))
