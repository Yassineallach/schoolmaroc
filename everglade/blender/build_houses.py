"""
Everglade - Tiny Glade-style houses, modelled in Blender as a look target.

Tiny Glade's buildings are soft and toy-like: every stone, tile and beam a
rounded, slightly wonky block, nothing perfectly straight. This script puts
whole houses together out of such blocks, from the details measured off
Tiny Glade screenshots and its developers' notes:

  * roofs of individual chunky tiles in staggered rows, each tile a little
    tilted and its own shade (slate blue-teal or terracotta), a gentle
    concave sweep, rounded ridge tiles, a deep overhang
  * walls that are real slabs with openings cut through them, so doors and
    windows sit back in deep reveals
  * pale sandy stonework of rounded blocks (big at the foot), cream lime
    plaster with worn patches, stone quoins and dressed surrounds
  * half-timbering in honey wood: posts, plates, a St Andrew's cross under
    each window, a jettied upper storey on a row of beam ends
  * leaded windows with sage shutters and flower boxes, plank doors with
    iron straps, gothic doors in stone surrounds (blender/build_wood.py)
  * stone chimneys, a round tower with a tiled cone roof

    python blender/build_houses.py render <out.png> [house]
      house: all (default), timber, cottage, chapel, tower
"""

import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_wood as bw  # noqa: E402
from build_wood import Piece, M_PAINT, M_STONE, M_WOOD  # noqa: E402

rng = random.Random(11)


def lin(h):
    """sRGB hex -> linear tuple (Blender vertex colours are linear)."""
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


# Measured off Tiny Glade screenshots
PLASTER = lin("#EFE6D3")
PLASTER_SHADE = lin("#E2D6BF")
STONES = [lin("#D8C8A6"), lin("#CDBB97"), lin("#E2D4B4"), lin("#C2AF8C"), lin("#D4C3A0")]
MORTAR = lin("#9E8F78")
SLATE = [lin("#5E7D89"), lin("#6B8D98"), lin("#55717C"), lin("#7898A0"), lin("#4F6973"), lin("#668A86")]
TERRACOTTA = [lin("#B8694A"), lin("#C47A56"), lin("#A85C42"), lin("#CC8660"), lin("#B07052"), lin("#9E5640")]
BEAM = lin("#A8814F")
BEAM_DARK = lin("#8E6A44")
M_TILES = 6
M_PLASTER = 5


def stone_col():
    return rng.choice(STONES)


# ---------------------------------------------------------------------------
# Walls: slabs with openings cut through (so doors and windows sit inside)
# ---------------------------------------------------------------------------
class Openings:
    """Opening shapes on a wall face, in the face's (u, z) plane."""

    def __init__(self):
        self.items = []   # (u, z0, w, h, kind) kind: rect / round / pointed

    def add(self, u, z0, w, h, kind="rect"):
        self.items.append((u, z0, w, h, kind))

    def hits(self, u0, u1, z0, z1, pad=0.06):
        for (u, oz, w, h, kind) in self.items:
            top = oz + h + (w * 0.5 if kind == "round" else w * 0.78 if kind == "pointed" else 0.0)
            if u1 > u - w / 2 - pad and u0 < u + w / 2 + pad and z1 > oz - pad and z0 < top + pad:
                return True
        return False


def _cutter(name, outline, depth):
    """A prism through the wall: outline in (x, z), centred on y = 0."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, -depth / 2, z)) for x, z in outline]
    hi = [bm.verts.new((x, depth / 2, z)) for x, z in outline]
    bm.faces.new(lo)
    bm.faces.new(list(reversed(hi)))
    n = len(outline)
    for i in range(n):
        bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def opening_outline(w, h, kind, steps=16):
    pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h)]
    if kind == "round":
        r = w / 2
        for i in range(1, steps):
            a = math.pi * i / steps
            pts.append((math.cos(a) * r, h + math.sin(a) * r))
    elif kind == "pointed":
        half = w / 2
        R, c = half * 1.7, half * 0.7
        for i in range(1, steps):
            x = half - w * i / steps
            cx = -c if x >= 0 else c
            pts.append((x, h + math.sqrt(max(0.0, R * R - (x - cx) ** 2))))
        pts.insert(3 + steps // 2 - 1, (0.0, h + math.sqrt(R * R - c * c)))
        pts = [pts[0], pts[1], pts[2]] + sorted(pts[3:], key=lambda p: -p[0])
    pts.append((-w / 2, h))
    return pts


def cut_openings(obj, faces, color=PLASTER, mat=M_PAINT):
    """faces: list of (matrix placing the opening's (x, z) plane on the wall,
    outline, depth). Boolean-subtracts each opening and applies it."""
    cutters = []
    for i, (m, outline, depth) in enumerate(faces):
        c = _cutter("cut%d" % i, outline, depth)
        c.matrix_world = m
        mod = obj.modifiers.new("b%d" % i, "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = c
        mod.solver = "EXACT"
        cutters.append(c)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    obj.modifiers.clear()
    old = obj.data
    obj.data = me
    bpy.data.meshes.remove(old)
    for c in cutters:
        bpy.data.objects.remove(c)
    # the cut faces (the reveals) come from the cutters and carry no colour:
    # paint them like the wall
    for ca in me.color_attributes:
        for item in ca.data:
            c = item.color
            if c[0] + c[1] + c[2] < 0.001:
                item.color = (color[0], color[1], color[2], 1.0)
    uvl = me.uv_layers.active
    if uvl:
        for d in uvl.data:
            if d.uv[0] == 0.0 and d.uv[1] == 0.0:
                d.uv = ((mat + 0.5) / 16.0, 0.5)
    return obj


def walls(name, w, d, z0, z1, thick, color, mat, cuts=None, reveal=None, rmat=None):
    """A rectangular ring of wall slabs (outer w x d), each its own object so
    openings can be cut cleanly through the ones that have them.
    cuts: {"front"|"back"|"left"|"right": [(matrix, outline, depth)...]}"""
    t = thick
    out = []
    for face, (sx, sy, x, y) in (("front", (w, t, 0, -d / 2 + t / 2)), ("back", (w, t, 0, d / 2 - t / 2)),
                                 ("left", (t, d - 2 * t, -w / 2 + t / 2, 0)), ("right", (t, d - 2 * t, w / 2 - t / 2, 0))):
        p = Piece("%s_%s" % (name, face))
        p.plank((sx, sy, z1 - z0), (x, y, (z0 + z1) / 2), color=color, mat=mat, round_=0.06, vary=0.0, wonky=0.0)
        ob = p.to_object()
        if cuts and cuts.get(face):
            cut_openings(ob, cuts[face], reveal or color, mat if rmat is None else rmat)
        out.append(ob)
    return out


def flat_faces(p, faces):
    """Flat shading for thin slabs (smooth normals would cancel out)."""
    for f in faces:
        f.smooth = False


# ---------------------------------------------------------------------------
# Stonework
# ---------------------------------------------------------------------------
def stone_face(p, u0, u1, z0, z1, place, ops=None, big_foot=True, depth=0.16, proud=0.05):
    """Courses of rounded, irregular stones over a face. place(u, z, out)
    maps face coordinates to a point; the face normal is the 'out' axis."""
    z = z0
    row = 0
    while z < z1 - 0.04:
        h = (0.3 if big_foot and z < z0 + 0.6 else 0.22) * rng.uniform(0.85, 1.15)
        h = min(h, z1 - z)
        u = u0 - (0.13 if row % 2 else 0.0)
        while u < u1 - 0.03:
            w = rng.uniform(0.3, 0.55) * (1.25 if big_foot and z < z0 + 0.6 else 1.0)
            a, b = max(u, u0), min(u + w, u1)
            if b - a > 0.08 and not (ops and ops.hits(a, b, z, z + h)):
                yield ((a + b) / 2, z + h / 2, b - a - 0.035, h - 0.035)
            u += w
        z += h
        row += 1


def lay_stones(p, stones, place_rot, depth=0.16, proud=0.04, colors=None):
    for (uc, zc, w, h) in stones:
        loc, rot = place_rot(uc, zc, proud - depth / 2 + rng.uniform(-0.012, 0.015))
        p.plank((w, depth, h), loc, rot=rot, color=rng.choice(colors or STONES), mat=M_STONE,
                round_=0.32, vary=0.05, wonky=1.6)


def front_placer(y_face, sign=-1):
    """Face on the plane y = y_face facing sign*Y (u = x)."""
    def f(u, z, out):
        return (u, y_face + sign * out, z), (0, 0, 0)
    return f


def side_placer(x_face, sign):
    """Face on the plane x = x_face facing sign*X (u = y)."""
    def f(u, z, out):
        return (x_face + sign * out, u, z), (0, 0, math.pi / 2)
    return f


# ---------------------------------------------------------------------------
# Tiled roofs
# ---------------------------------------------------------------------------
def gable_roof(p, x0, x1, half_d, z_eave, rise, palette, over=0.42, gable_over=0.3, curve=0.12):
    """Two tiled slopes, ridge along X at y = 0, eaves at y = +-(half_d + over).
    `curve` sweeps the slopes gently concave, as Tiny Glade's roofs."""
    slope = rise / half_d
    yd = half_d + over
    z_lo = z_eave - over * slope
    run = yd
    span = math.hypot(run, rise + over * slope)
    tile_w, tile_l, expose, thick = 0.3, 0.34, 0.235, 0.055

    t0 = over / yd    # where the slope passes over the wall top

    def surf(t):  # t 0 eave .. 1 ridge -> (y_abs, z)
        y = yd * (1 - t)
        # the concave sweep only starts inside the wall line, so the roof
        # keeps clear of the wall plates
        u = max(0.0, (t - t0) / (1 - t0))
        z = z_lo + (rise + over * slope) * t - curve * math.sin(math.pi * u)
        return y, z

    rows = int(span / expose) + 1
    for side in (-1, 1):
        # a dark board deck under the tiles so nothing shows through
        for k in range(8):
            ta, tb = k / 8, (k + 1) / 8
            ya, za = surf(ta)
            yb, zb = surf(tb)
            ang = math.atan2(zb - za, ya - yb)
            L = math.hypot(ya - yb, zb - za)
            p.plank((x1 - x0 + 2 * gable_over, L + 0.02, 0.09), ((x0 + x1) / 2, side * (ya + yb) / 2, (za + zb) / 2 - 0.06),
                    rot=(-side * ang, 0, 0), color=BEAM_DARK, mat=M_WOOD, round_=0.1, vary=0.0, wonky=0.0)
        for r in range(rows):
            t = min(1.0, r * expose / span)
            t2 = min(1.0, t + 0.02)
            ya, za = surf(t)
            yb, zb = surf(t2)
            ang = math.atan2(zb - za, ya - yb) + math.radians(5)   # butts kicked up a touch
            nx = (x1 - x0 + 2 * gable_over) / tile_w
            n = int(nx) + 1
            off = (tile_w / 2) if r % 2 else 0.0
            for i in range(-1, n + 1):
                x = x0 - gable_over + i * tile_w + off
                if x < x0 - gable_over - 0.02 or x > x1 + gable_over + 0.02:
                    continue
                w = tile_w - 0.03 + rng.uniform(-0.02, 0.01)
                # centre the tile up-slope of its butt
                cy = ya - math.cos(ang) * tile_l * 0.5
                cz = za + math.sin(ang) * tile_l * 0.5 + 0.03 + r * 0.0
                tilt = rng.uniform(-0.05, 0.05)
                p.plank((w, tile_l, thick), (x + rng.uniform(-0.012, 0.012), side * cy, cz),
                        rot=(-side * ang + rng.uniform(-0.03, 0.03), tilt * 0.4, tilt * 0.3),
                        color=rng.choice(palette), mat=M_TILES, round_=0.45, vary=0.09, wonky=0.6)
    # rounded ridge tiles
    zr = surf(1.0)[1] + 0.07
    x = x0 - gable_over
    while x < x1 + gable_over:
        p.cyl(0.13, 0.36, (x + 0.17, 0, zr), rot=(0, math.pi / 2, 0), color=rng.choice(palette), mat=M_TILES, seg=12)
        x += 0.33
    return surf


def cone_roof(p, cx, cy, r_base, z_base, height, palette, over=0.35, flare=0.18):
    """A tower's cone of tile rings, flaring out at the eaves, with a finial."""
    R = r_base + over
    span = math.hypot(R, height)
    expose = 0.2
    rows = int(span / expose)
    for k in range(rows):
        t = k / rows
        r = R * (1 - t)
        z = z_base + height * t - flare * (1 - t) ** 3 * 0.0 - flare * math.sin(math.pi * t) * 0.4
        if r < 0.12:
            break
        n = max(5, int(2 * math.pi * r / 0.27))
        slope = math.atan2(height, R) * (1.0 + 0.35 * (1 - t) ** 2 * -1) + math.radians(6)
        for i in range(n):
            a = 2 * math.pi * (i + (0.5 if k % 2 else 0)) / n
            w = 2 * math.pi * r / n - 0.025
            loc = (cx + math.cos(a) * (r - 0.12 * math.cos(slope)), cy + math.sin(a) * (r - 0.12 * math.cos(slope)),
                   z + 0.12 * math.sin(slope) + 0.03)
            p.plank((max(0.08, w), 0.3, 0.05), loc, rot=(slope, 0, a - math.pi / 2 + math.pi),
                    color=rng.choice(palette), mat=M_TILES, round_=0.45, vary=0.09, wonky=0.5)
    # a solid core so no light leaks through the rings
    p.cyl(R * 0.98, 0.02, (cx, cy, z_base - 0.05), color=BEAM_DARK, mat=M_WOOD, seg=24)
    p.cyl(R * 0.95, height * 0.97, (cx, cy, z_base + height * 0.97 / 2 - 0.08), color=BEAM_DARK, mat=M_WOOD, seg=24, r2=0.04)
    # finial
    p.cyl(0.05, 0.6, (cx, cy, z_base + height + 0.25), color=lin("#3B3530"), mat=8, seg=8)
    p.ball(0.09, (cx, cy, z_base + height + 0.55), lin("#C9A04A"), mat=8)


def gable_outline(surf, half_d, z_wall, gap=0.14):
    """A gable wall's outline in (y, z), tucked under the (curved) roof."""
    pts = [(-half_d, z_wall)]
    ts = [k / 16 for k in range(17)]
    side = []
    for t in ts:
        y, z = surf(t)
        if y <= half_d:
            side.append((y, z - gap))
    pts += [(-y, z) for (y, z) in side]
    pts += [(y, z) for (y, z) in reversed(side[:-1])]
    pts.append((half_d, z_wall))
    return pts


def chimney(p, x, y, z0, z1):
    z = z0
    k = 0
    while z < z1:
        h = 0.2
        for (dx, dy, w, d) in ((0, 0, 0.62, 0.5),):
            off = 0.04 if k % 2 else -0.04
            p.plank((w + rng.uniform(-0.03, 0.03), d, h - 0.02), (x + dx + off * 0.3, y + dy, z + h / 2), color=stone_col(),
                    mat=M_STONE, round_=0.3, vary=0.05, wonky=1.2)
        z += h
        k += 1
    p.plank((0.78, 0.66, 0.1), (x, y, z1 + 0.05), color=stone_col(), mat=M_STONE, round_=0.3)
    p.plank((0.32, 0.3, 0.22), (x, y, z1 + 0.2), color=lin("#6E625A"), mat=M_STONE, round_=0.3)


# ---------------------------------------------------------------------------
# Wood pieces from build_wood, set into openings
# ---------------------------------------------------------------------------
def place_piece(build, loc, rot_z, surf=0.0, dy=0.0, dz=0.0):
    """Builds a build_wood piece set back `surf` into its opening (as the game
    export does) and places it with its front facing the wall's outside."""
    bw.SURF = surf
    obj = build().to_object()
    bw.SURF = 0.0
    m = Matrix.Translation(loc) @ Matrix.Rotation(rot_z, 4, "Z") @ Matrix.Translation((0, surf + dy, dz))
    obj.matrix_world = m
    return obj


def face_frame(face, u, z, out=0.0):
    """(location, rot_z) for a point on one of a box house's faces.
    face: ('front', y) / ('back', y) / ('left', x) / ('right', x)."""
    kind, c = face
    if kind == "front":
        return (u, c - out, z), 0.0
    if kind == "back":
        return (-u, c + out, z), math.pi
    if kind == "left":
        return (c - out, -u, z), -math.pi / 2
    return (c + out, u, z), math.pi / 2


def face_matrix(face, u, z):
    loc, rz = face_frame(face, u, z)
    return Matrix.Translation(loc) @ Matrix.Rotation(rz, 4, "Z")


# ---------------------------------------------------------------------------
# Houses
# ---------------------------------------------------------------------------
def timber_house(ox, oy):
    """Tiny Glade's half-timbered house: sandy stone ground floor, a jettied,
    timber-framed upper storey in cream plaster, leaded windows with sage
    shutters and flower boxes, a terracotta roof and a stone chimney."""
    W, D = 5.6, 4.2
    T = 0.34
    plinth = 0.35
    g1 = plinth + 2.35          # top of the stone ground floor
    jet = 0.22                  # upper storey overhang
    g2 = g1 + 2.3               # eaves
    parts = []
    # --- ground floor: stone over a mortar core with openings
    ops = {"front": Openings(), "back": Openings(), "left": Openings(), "right": Openings()}
    door = (0.0, plinth, 1.4, 2.36)
    ops["front"].add(0.0, plinth, 1.4, 2.36)
    win1 = [(-1.85, plinth + 0.75, 0.9, 1.14), (1.85, plinth + 0.75, 0.9, 1.14)]
    for (u, z, w, h) in win1:
        ops["front"].add(u, z, w, h)
    ops["right"].add(0.0, plinth + 0.75, 0.9, 1.14)
    cuts = {}
    yf, yb, xl, xr = -D / 2, D / 2, -W / 2, W / 2
    faces = {"front": ("front", yf), "back": ("back", yb), "left": ("left", xl), "right": ("right", xr)}
    for name, o in ops.items():
        for (u, z, w, h, kind) in o.items:
            cuts.setdefault(name, []).append((face_matrix(faces[name], u, z), opening_outline(w, h, kind), T * 3))
    parts += walls("core1", W, D, 0.0, g1, T, MORTAR, M_STONE, cuts, lin("#E6D9BC"), M_STONE)
    sp = Piece("stones1")
    for name, (u_half) in (("front", W / 2), ("back", W / 2), ("left", D / 2), ("right", D / 2)):
        face = faces[name]

        def place(u, z, out, face=face):
            loc, rz = face_frame(face, u, z, out)
            return loc, (0, 0, rz)
        lay_stones(sp, list(stone_face(sp, -u_half - 0.06, u_half + 0.06, 0.0, g1, None, ops[name])), place)
    # reveals: dressed jamb stones round the ground-floor openings
    for name, o in ops.items():
        for (u, z, w, h, kind) in o.items:
            for sgn in (-1, 1):
                zz = z
                k = 0
                while zz < z + h - 0.05:
                    hh = min(0.3 if k % 2 == 0 else 0.24, z + h - zz)
                    ww = 0.22 if k % 2 == 0 else 0.15
                    loc, rz = face_frame(faces[name], u + sgn * (w / 2 + ww / 2), zz + hh / 2, 0.02)
                    sp.plank((ww, 0.2, hh - 0.025), loc, rot=(0, 0, rz), color=lin("#E6D9BC"), mat=M_STONE, round_=0.3, wonky=0.8)
                    zz += hh
                    k += 1
            # lintel
            loc, rz = face_frame(faces[name], u, z + h + 0.12, 0.02)
            sp.plank((w + 0.5, 0.22, 0.24), loc, rot=(0, 0, rz), color=lin("#E6D9BC"), mat=M_STONE, round_=0.3, wonky=0.6)
    parts.append(sp.to_object())
    # door, windows
    loc, rz = face_frame(faces["front"], 0.0, plinth)
    parts.append(place_piece(lambda: bw.door_tg(False), loc, rz, 0.16))
    for (u, z, w, h) in win1:
        loc, rz = face_frame(faces["front"], u, z)
        parts.append(place_piece(bw.window_tg_lattice, loc, rz, 0.14))
        parts.append(place_piece(bw.flower_box_tg, loc, rz, 0.0, dy=-0.16, dz=-0.3))
    loc, rz = face_frame(faces["right"], 0.0, plinth + 0.75)
    parts.append(place_piece(bw.window_tg_lattice, loc, rz, 0.14))
    # --- jetty: a plate on a row of beam ends
    wp = Piece("timber")
    W2, D2 = W + 2 * jet, D + 2 * jet
    n = 11
    for i in range(n):
        x = -W / 2 + 0.2 + (W - 0.4) * i / (n - 1)
        wp.plank((0.16, D2 + 0.3, 0.16), (x, 0, g1 - 0.04), color=BEAM, round_=0.28, wonky=0.8)
    for sgn in (-1, 1):
        wp.plank((W2 + 0.1, 0.2, 0.2), (0, sgn * (D2 / 2 - 0.08), g1 + 0.1), color=BEAM, round_=0.25)
        wp.plank((0.2, D2, 0.2), (sgn * (W2 / 2 - 0.08), 0, g1 + 0.1), color=BEAM, round_=0.25)
    # --- upper storey: plaster infill with openings, beams on the face
    ops2 = Openings()
    win2 = [(-1.85, g1 + 0.95, 0.9, 1.14), (0.0, g1 + 0.95, 0.9, 1.14), (1.85, g1 + 0.95, 0.9, 1.14)]
    f2 = ("front", -D2 / 2)
    cuts = []
    for (u, z, w, h) in win2:
        ops2.add(u, z, w, h)
        cuts.append((face_matrix(f2, u, z), opening_outline(w, h, "rect"), 0.8))
    parts += walls("core2", W2, D2, g1 + 0.2, g2, 0.26, PLASTER, M_PAINT, {"front": cuts})
    zb, zt = g1 + 0.2, g2
    # posts at the corners, either side of each window, sill and head rails
    for x in (-W2 / 2 + 0.09, W2 / 2 - 0.09):
        wp.plank((0.18, 0.16, zt - zb), (x, -D2 / 2 - 0.02, (zb + zt) / 2), color=BEAM, round_=0.25)
    for (u, z, w, h) in win2:
        for sgn in (-1, 1):
            wp.plank((0.15, 0.14, zt - zb), (u + sgn * (w / 2 + 0.07), -D2 / 2 - 0.03, (zb + zt) / 2), color=BEAM, round_=0.25)
        wp.plank((w + 0.3, 0.14, 0.14), (u, -D2 / 2 - 0.03, z - 0.07), color=BEAM, round_=0.25)
        wp.plank((w + 0.3, 0.14, 0.14), (u, -D2 / 2 - 0.03, z + h + 0.07), color=BEAM, round_=0.25)
        # St Andrew's cross under the window
        lo, hi = zb + 0.05, z - 0.14
        ang = math.atan2(hi - lo, w)
        L = math.hypot(w, hi - lo)
        for s in (-1, 1):
            wp.plank((L, 0.12, 0.11), (u, -D2 / 2 - 0.035, (lo + hi) / 2), rot=(0, s * ang, 0), color=BEAM, round_=0.25, wonky=0.4)
        loc, rz = face_frame(f2, u, z)
        parts.append(place_piece(bw.window_tg_lattice, loc, rz, 0.14))
        if u != 0.0:
            parts.append(place_piece(lambda: bw.shutters_tg(False), loc, rz, 0.0, dy=-0.04))
    wp.plank((W2 + 0.04, 0.16, 0.16), (0, -D2 / 2 - 0.03, zt - 0.08), color=BEAM, round_=0.25)
    # braces on the gable sides
    for sgn in (-1, 1):
        x = sgn * (W2 / 2 + 0.02)
        wp.plank((0.15, D2, 0.15), (x, 0, zt - 0.08), color=BEAM, round_=0.25)
        for s2 in (-1, 1):
            wp.plank((0.14, 0.14, zt - zb), (x, s2 * (D2 / 2 - 0.08), (zb + zt) / 2), color=BEAM, round_=0.25)
            ang = math.atan2(zt - zb - 0.2, D2 / 2 - 0.3)
            wp.plank((0.12, math.hypot(zt - zb - 0.2, D2 / 2 - 0.3), 0.12), (x, s2 * D2 / 4, (zb + zt) / 2),
                     rot=(s2 * ang, 0, 0), color=BEAM, round_=0.25, wonky=0.4)
    # --- roof: gable along X, eaves front and back, gables plastered
    rise = 2.3
    rp = Piece("roof")
    surf = gable_roof(rp, -W2 / 2, W2 / 2, D2 / 2, g2, rise, TERRACOTTA)
    # gable triangles
    for sgn in (-1, 1):
        gp = Piece("gable")
        bm = gp.bm
        x = sgn * (W2 / 2 - 0.1)
        vs = [bm.verts.new((x, y, z)) for (y, z) in gable_outline(surf, D2 / 2, g2)]
        f = bm.faces.new(vs)
        gp._paint([f], PLASTER, M_PAINT)
        bm.normal_update()
        bmesh.ops.solidify(bm, geom=[f], thickness=0.2)
        gp._paint(list(bm.faces), PLASTER, M_PAINT)
        flat_faces(gp, bm.faces)
        parts.append(gp.to_object())
        # rafter ends under the eaves
    for i in range(12):
        x = -W2 / 2 + 0.25 + (W2 - 0.5) * i / 11
        for sgn in (-1, 1):
            wp.plank((0.11, 0.42, 0.11), (x, sgn * (D2 / 2 + 0.16), g2 - 0.16 - 0.17 * rise / (D2 / 2)), rot=(sgn * -0.5, 0, 0), color=BEAM_DARK, round_=0.3)
    chimney(rp, W2 / 2 - 0.9, 0.9, g2 - 0.5, g2 + rise + 0.6)
    parts.append(rp.to_object())
    parts.append(wp.to_object())
    for o in parts:
        o.location = (o.location[0] + ox, o.location[1] + oy, o.location[2])
    return parts


def cottage(ox, oy):
    """A one-storey plaster cottage: cream lime wash with worn patches
    showing stone, stone quoins, an arched plank door, cream-framed windows
    with sage shutters, a slate roof with a chimney."""
    W, D = 5.0, 3.8
    T = 0.34
    plinth = 0.4
    g = plinth + 2.5
    parts = []
    front = ("front", -D / 2)
    ops = Openings()
    ops.add(0.0, plinth, 1.4, 1.64, "round")
    wins = [(-1.55, plinth + 0.75), (1.55, plinth + 0.75)]
    for (u, z) in wins:
        ops.add(u, z, 0.96, 1.08)
    cuts = [(face_matrix(front, u, z), opening_outline(w, h, k), 1.0) for (u, z, w, h, k) in ops.items]
    parts += walls("cott", W, D, 0.0, g, T, PLASTER, M_PAINT, {"front": cuts})
    sp = Piece("cott_stone")
    # plinth stones all round, quoins up the corners, worn patches
    for (face, half) in ((front, W / 2), (("back", D / 2), W / 2), (("left", -W / 2), D / 2), (("right", W / 2), D / 2)):
        def place(u, z, out, face=face):
            loc, rz = face_frame(face, u, z, out)
            return loc, (0, 0, rz)
        lay_stones(sp, list(stone_face(sp, -half - 0.05, half + 0.05, 0.0, plinth + 0.05, None, None)), place, proud=0.06)
        z = plinth + 0.05
        k = 0
        while z < g - 0.2:
            h = 0.32
            for sgn in (-1, 1):
                w = 0.5 if k % 2 == 0 else 0.32
                loc, rz = face_frame(face, sgn * (half - w / 2 + 0.03), z + h / 2, 0.02)
                sp.plank((w, 0.14, h - 0.03), loc, rot=(0, 0, rz), color=stone_col(), mat=M_STONE, round_=0.3, wonky=1.0)
            z += h
            k += 1
        for _ in range(2):
            pu = rng.uniform(-half + 0.9, half - 0.9)
            pz = rng.uniform(plinth + 0.4, g - 0.6)
            if face == front and ops.hits(pu - 0.5, pu + 0.5, pz - 0.4, pz + 0.4, 0.25):
                continue
            for (du, dz, w, h) in ((0, 0, 0.42, 0.24), (0.44, 0.02, 0.34, 0.22), (0.2, -0.26, 0.4, 0.24)):
                loc, rz = face_frame(face, pu + du, pz + dz, -0.04)
                sp.plank((w, 0.14, h), loc, rot=(0, 0, rz), color=stone_col(), mat=M_STONE, round_=0.32, wonky=1.2)
    parts.append(sp.to_object())
    loc, rz = face_frame(front, 0.0, plinth)
    parts.append(place_piece(lambda: bw.door_tg(True), loc, rz, 0.16))
    for (u, z) in wins:
        loc, rz = face_frame(front, u, z)
        parts.append(place_piece(lambda: bw.window_tg(False), loc, rz, 0.14))
        parts.append(place_piece(lambda: bw.shutters_tg(False), loc, rz, 0.0, dy=-0.04))
    rp = Piece("cott_roof")
    rise = 1.9
    surf = gable_roof(rp, -W / 2, W / 2, D / 2, g, rise, SLATE, curve=0.16)
    for sgn in (-1, 1):
        gp = Piece("cgable")
        bm = gp.bm
        x = sgn * (W / 2 - 0.1)
        vs = [bm.verts.new((x, y, z)) for (y, z) in gable_outline(surf, D / 2, g)]
        f = bm.faces.new(vs)
        bm.normal_update()
        bmesh.ops.solidify(bm, geom=[f], thickness=0.2)
        gp._paint(list(bm.faces), PLASTER, M_PAINT)
        flat_faces(gp, bm.faces)
        parts.append(gp.to_object())
    chimney(rp, -W / 2 + 0.7, 0.6, g - 0.3, g + rise + 0.5)
    for i in range(10):
        x = -W / 2 + 0.25 + (W - 0.5) * i / 9
        for sgn in (-1, 1):
            rp.plank((0.11, 0.42, 0.11), (x, sgn * (D / 2 + 0.16), g - 0.16 - 0.17 * rise / (D / 2)), rot=(sgn * -0.45, 0, 0), color=BEAM_DARK, round_=0.3)
    parts.append(rp.to_object())
    for o in parts:
        o.location = (o.location[0] + ox, o.location[1] + oy, o.location[2])
    return parts


def chapel(ox, oy):
    """A stone house of rounded sandy blocks with pointed (gothic) doors in
    stone surrounds and pointed windows, a terracotta roof."""
    W, D = 6.4, 4.4
    T = 0.4
    g = 3.4
    parts = []
    front = ("front", -D / 2)
    ops = Openings()
    doors = [-1.6, 1.6]
    for u in doors:
        ops.add(u, 0.25, 1.12, 1.548, "pointed")
    ops.add(0.0, 1.1, 0.8, 0.58, "pointed")
    cuts = [(face_matrix(front, u, z), opening_outline(w, h, k), 1.0) for (u, z, w, h, k) in ops.items]
    parts += walls("chap", W, D, 0.0, g, T, MORTAR, M_STONE, {"front": cuts}, lin("#D8C8A6"), M_STONE)
    sp = Piece("chap_stone")
    for (face, half) in ((front, W / 2), (("back", D / 2), W / 2), (("left", -W / 2), D / 2), (("right", W / 2), D / 2)):
        def place(u, z, out, face=face):
            loc, rz = face_frame(face, u, z, out)
            return loc, (0, 0, rz)
        lay_stones(sp, list(stone_face(sp, -half - 0.07, half + 0.07, 0.0, g, None, ops if face == front else None)), place, proud=0.05)
    parts.append(sp.to_object())
    for u in doors:
        loc, rz = face_frame(front, u, 0.25)
        parts.append(place_piece(bw.door_tg_gothic, loc, rz, 0.16))
    loc, rz = face_frame(front, 0.0, 1.1)
    parts.append(place_piece(bw.window_tg_gothic, loc, rz, 0.14))
    rp = Piece("chap_roof")
    rise = 2.4
    surf = gable_roof(rp, -W / 2, W / 2, D / 2, g, rise, TERRACOTTA, curve=0.1)
    for sgn in (-1, 1):
        gp = Piece("sgable")
        # stone gable: courses stepping in
        z = g
        while z < g + rise - 0.3:
            # each course as wide as the roof above it allows
            half = 0.0
            for k in range(200):
                yy, zz = surf(k / 200)
                if zz - 0.2 >= z + 0.24:
                    half = min(yy, D / 2)
                    break
            y = -half
            while y < half - 0.05:
                w = min(rng.uniform(0.32, 0.5), half - y)
                gp.plank((0.3, w - 0.03, 0.22), (sgn * (W / 2 - 0.12), y + w / 2, z + 0.11), color=stone_col(), mat=M_STONE, round_=0.3, wonky=1.2)
                y += w
            z += 0.24
        parts.append(gp.to_object())
    parts.append(rp.to_object())
    for o in parts:
        o.location = (o.location[0] + ox, o.location[1] + oy, o.location[2])
    return parts


def tower(ox, oy):
    """A round stone tower of rounded blocks with a pointed window and a
    flared cone of slate tiles."""
    R = 1.7
    H = 6.0
    parts = []
    sp = Piece("tower")
    sp.cyl(R - 0.1, H, (0, 0, H / 2), color=MORTAR, mat=M_STONE, seg=32)
    z = 0.0
    row = 0
    while z < H - 0.05:
        h = (0.3 if z < 0.6 else 0.24) * rng.uniform(0.9, 1.1)
        n = int(2 * math.pi * R / rng.uniform(0.42, 0.5))
        for i in range(n):
            a = 2 * math.pi * (i + (0.5 if row % 2 else 0) + rng.uniform(-0.12, 0.12)) / n
            if abs(math.atan2(math.sin(a + math.pi / 2), math.cos(a + math.pi / 2))) < 0.3 and 2.0 < z < 3.6:
                continue  # the window
            w = 2 * math.pi * R / n - 0.04
            sp.plank((w, 0.2, h - 0.035), (math.cos(a) * (R - 0.04), math.sin(a) * (R - 0.04), z + h / 2),
                     rot=(0, 0, a + math.pi / 2), color=stone_col(), mat=M_STONE, round_=0.32, wonky=1.4)
        z += h
        row += 1
    parts.append(sp.to_object())
    loc = (0, -R + 0.05, 2.1)
    parts.append(place_piece(bw.window_tg_gothic, loc, 0.0, 0.0, dy=-0.02))
    rp = Piece("tower_roof")
    cone_roof(rp, 0, 0, R, H, 3.6, SLATE)
    parts.append(rp.to_object())
    for o in parts:
        o.location = (o.location[0] + ox, o.location[1] + oy, o.location[2])
    return parts


# ---------------------------------------------------------------------------
# Stage and render
# ---------------------------------------------------------------------------
def stage(out, focus, dist, res=(1600, 1000), yaw=-28.0, pitch=24.0, lens=55):
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.01))
    gm = bpy.data.materials.new("ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin("#7FA35A"), 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
    bpy.context.active_object.data.materials.append(gm)
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*lin("#BFD8EE"), 1)
    bg.inputs[1].default_value = 0.85
    sc.world = w
    sd = bpy.data.lights.new("Sun", "SUN")
    sd.energy = 3.6
    sd.angle = math.radians(3)
    sd.color = (1.0, 0.92, 0.8)
    so = bpy.data.objects.new("Sun", sd)
    so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
    sc.collection.objects.link(so)
    cd = bpy.data.cameras.new("C")
    cd.lens = lens
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    yw, pt = math.radians(yaw), math.radians(pitch)
    fx, fy, fz = focus
    cam.location = (fx + dist * math.sin(yw) * math.cos(pt), fy - dist * math.cos(yw) * math.cos(pt), fz + dist * math.sin(pt))
    d = Vector(focus) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 64
    sc.cycles.device = "CPU"
    sc.cycles.diffuse_bounces = 4
    sc.render.resolution_x, sc.render.resolution_y = res
    try:
        sc.view_settings.view_transform = "AgX"
    except TypeError:
        sc.view_settings.view_transform = "Filmic"
    sc.view_settings.exposure = 0.5
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("wrote", out)


HOUSES = {
    "timber": (timber_house, (0, 0, 3.4), 24.0),
    "cottage": (cottage, (0, 0, 2.2), 19.0),
    "chapel": (chapel, (0, 0, 2.6), 21.0),
    "tower": (tower, (0, 0, 4.4), 22.0),
}


def render(out, which="all"):
    bw.reset()
    if which == "all":
        timber_house(-6.5, 0)
        cottage(0.5, 1.0)
        chapel(7.5, 0.5)
        tower(13.5, 2.5)
        stage(out, (3.4, 1.0, 2.8), 44.0, res=(1900, 1000), yaw=-16, pitch=22, lens=45)
        return
    fn, focus, dist = HOUSES[which]
    fn(0, 0)
    stage(out, focus, dist)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if args and args[0] == "render":
        render(args[1], args[2] if len(args) > 2 else "all")
