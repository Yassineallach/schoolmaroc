"""
Everglade - Tiny Glade-style woodwork, modelled in Blender.

Tiny Glade's wood is chunky and toy-like: thick planks and beams with
generously rounded edges, nothing perfectly straight (every plank a little
narrower or wider, tilted a degree or two, set slightly proud or back), thin
dark seams between planks, a gentle per-plank shift in colour and only a
faint, large grain. Iron is kept to simple dark straps and rings; window
frames are fat, rounded and often painted cream.

This script builds those pieces:
  door_tg, door_tg_arch, window_tg, window_tg_arch, shutters_tg,
  flower_box_tg, fence_tg (one bay of upright planks), stairs_tg (a short
  timber flight with a railing), bracket_tg (a curved corbel under an
  overhang), wall_planks_h / wall_planks_v (plank wall panels on a stone
  footing), beam_bay (a timber-framing bay)

    python blender/build_wood.py preview <out.png>   # lineup render
    python blender/build_wood.py export <out_dir> [names...]

Conventions match blender/build_assets.py: 1 unit = 1 m, origin at the
piece's foot, front facing -Y, vertex colour RGB = albedo, alpha = channel
(1 solid), UV.x = surface material slice (wood, metal, stone, painted),
"Glow*" objects are window glass.
"""

import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

# Warm, moderately saturated woods (Tiny Glade's GI lifts and warms them in
# game; these are estimates picked to match its screenshots' feel)
WOOD = (0.54, 0.35, 0.23)        # #8A5A3B
WOOD_LIGHT = (0.69, 0.52, 0.35)  # #B08458
WOOD_DARK = (0.35, 0.23, 0.15)   # #5A3A26
WOOD_GREY = (0.55, 0.52, 0.47)   # weathered
CREAM = (0.93, 0.89, 0.81)       # painted frames
SEAM = (0.23, 0.15, 0.09)
IRON = (0.23, 0.23, 0.23)
STONE = (0.78, 0.75, 0.68)
GLASS = (1.0, 0.86, 0.6)
FLOWERS = [(0.95, 0.55, 0.66), (0.98, 0.86, 0.42), (0.95, 0.95, 0.92), (0.85, 0.32, 0.36)]
LEAF = (0.40, 0.62, 0.30)

M_PAINT, M_STONE, M_WOOD, M_METAL = 0, 1, 3, 8
MAT_SLICES = 16

rng = random.Random(7)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
class Piece:
    """Collects rounded boxes and other parts into one vertex-coloured mesh."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.color.new("Color")
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.glow = None

    def _paint(self, faces, color, mat, alpha=1.0, vary=0.0):
        k = 1.0 + rng.uniform(-vary, vary)
        c = (min(color[0] * k, 1), min(color[1] * k, 1), min(color[2] * k, 1), alpha)
        uv = ((mat + 0.5) / MAT_SLICES, 0.5)
        for f in faces:
            f.smooth = True
            for loop in f.loops:
                loop[self.col] = c
                loop[self.uv].uv = uv

    def plank(self, size, loc, rot=(0, 0, 0), color=None, mat=M_WOOD, round_=0.22, vary=0.07, wonky=1.0):
        """A chunky board with soft, rounded edges (bevel ~ round_ of its
        thinnest side), a little jitter in size, tilt and position."""
        color = color or WOOD
        sx, sy, sz = size
        j = wonky
        sx *= 1.0 + rng.uniform(-0.04, 0.04) * j
        sz *= 1.0 + rng.uniform(-0.03, 0.03) * j
        # tilt so the ends wander ~1-2 cm at most, whatever the length
        long_side = max(sx, sy, sz)
        k = min(1.0, 0.5 / max(long_side, 0.05))
        rot = (rot[0] + math.radians(rng.uniform(-1.5, 1.5)) * j * k,
               rot[1] + math.radians(rng.uniform(-2.0, 2.0)) * j * k,
               rot[2] + math.radians(rng.uniform(-1.2, 1.2)) * j * k)
        loc = (loc[0] + rng.uniform(-0.006, 0.006) * j, loc[1] + rng.uniform(-0.008, 0.008) * j, loc[2])
        before = set(self.bm.faces)
        ret = bmesh.ops.create_cube(self.bm, size=1.0)
        verts = ret["verts"]
        bmesh.ops.scale(self.bm, vec=(sx, sy, sz), verts=verts)
        edges = list({e for v in verts for e in v.link_edges})
        r = min(sx, sy, sz) * round_
        bmesh.ops.bevel(self.bm, geom=edges, offset=r, offset_type="OFFSET", segments=3, profile=0.5,
                        affect="EDGES", clamp_overlap=True)
        # the bevelled box's faces (bevel adds new ones)
        faces = [f for f in self.bm.faces if f not in before]
        allv = list({v for f in faces for v in f.verts})
        m = Matrix.Translation(loc) @ Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[0], 4, "X")
        bmesh.ops.transform(self.bm, matrix=m, verts=allv)
        self._paint(faces, color, mat, vary=vary)
        return allv


    def round_top(self, verts, top, shape):
        """Bends the top of a board onto a curve: verts within reach of `top`
        move by shape(x) - top (an arch, or a soft dome on a fence board)."""
        for v in verts:
            if v.co.z > top - 0.14:
                v.co.z += shape(v.co.x) - top

    def arc_frame(self, cx, zc, r, depth, thick, y=0.0, color=WOOD_DARK, mat=M_WOOD, a0=0.0, a1=math.pi, steps=28):
        """One smooth curved member (an arch head): a soft, rounded square
        section swept round a circle in the XZ plane."""
        before = set(self.bm.faces)
        prof = []
        n = 12
        for k in range(n):
            a = math.tau * (k + 0.5) / n
            # squircle section: flat faces, round corners
            cx_ = math.copysign(abs(math.cos(a)) ** 0.5, math.cos(a)) * thick * 0.5
            cy_ = math.copysign(abs(math.sin(a)) ** 0.5, math.sin(a)) * depth * 0.5
            prof.append((cx_, cy_))
        rings = []
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            radial = Vector((math.cos(a), 0, math.sin(a)))
            ring = []
            for (u, w) in prof:
                pos = Vector((cx, y, zc)) + radial * (r + u) + Vector((0, w, 0))
                ring.append(self.bm.verts.new(pos))
            rings.append(ring)
        for i in range(steps):
            for k in range(n):
                self.bm.faces.new((rings[i][k], rings[i][(k + 1) % n], rings[i + 1][(k + 1) % n], rings[i + 1][k]))
        self.bm.faces.new(list(reversed(rings[0])))
        self.bm.faces.new(rings[-1])
        faces = [f for f in self.bm.faces if f not in before]
        self._paint(faces, color, mat, vary=0.04)

    def cyl(self, r, depth, loc, rot=(0, 0, 0), color=IRON, mat=M_METAL, seg=10, r2=None):
        before = set(self.bm.faces)
        bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r,
                              radius2=r if r2 is None else r2, depth=depth)
        faces = [f for f in self.bm.faces if f not in before]
        allv = list({v for f in faces for v in f.verts})
        m = Matrix.Translation(loc) @ Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[0], 4, "X")
        bmesh.ops.transform(self.bm, matrix=m, verts=allv)
        self._paint(faces, color, mat)

    def ring(self, major, minor, loc, rot=(0, 0, 0), color=IRON, mat=M_METAL):
        seg, ring = 14, 6
        rows = []
        for i in range(seg):
            a = i / seg * math.tau
            row = []
            for k in range(ring):
                b = k / ring * math.tau
                rr = major + minor * math.cos(b)
                row.append(self.bm.verts.new((rr * math.cos(a), minor * math.sin(b), rr * math.sin(a))))
            rows.append(row)
        faces = []
        for i in range(seg):
            for k in range(ring):
                faces.append(self.bm.faces.new((rows[i][k], rows[(i + 1) % seg][k], rows[(i + 1) % seg][(k + 1) % ring], rows[i][(k + 1) % ring])))
        allv = [v for r in rows for v in r]
        m = Matrix.Translation(loc) @ Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[0], 4, "X")
        bmesh.ops.transform(self.bm, matrix=m, verts=allv)
        self._paint(faces, color, mat)

    def ball(self, r, loc, color, mat=M_PAINT, squash=1.0):
        before = set(self.bm.faces)
        bmesh.ops.create_icosphere(self.bm, subdivisions=1, radius=r)
        faces = [f for f in self.bm.faces if f not in before]
        allv = list({v for f in faces for v in f.verts})
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(loc) @ Matrix.Diagonal((1, 1, squash, 1)), verts=allv)
        self._paint(faces, color, mat, vary=0.08)

    def glass(self, verts2d, y):
        """Window glass (glows at night): a flat polygon in the XZ plane."""
        if self.glow is None:
            self.glow = Piece("Glow")
        g = self.glow
        vs = [g.bm.verts.new((x, y, z)) for x, z in verts2d]
        f = g.bm.faces.new(vs)
        g._paint([f], GLASS, M_PAINT, alpha=0.5)

    def to_object(self, parent=None):
        mesh = bpy.data.meshes.new(self.name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.normal_update()
        self.bm.to_mesh(mesh)
        self.bm.free()
        attr = mesh.color_attributes[0]
        mesh.color_attributes.active_color = attr
        try:
            mesh.color_attributes.default_color_name = attr.name
        except AttributeError:
            pass
        mat = bpy.data.materials.get("VertexColor") or _vc_material()
        mesh.materials.append(mat)
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        if parent:
            obj.parent = parent
        if self.glow is not None:
            gobj = self.glow.to_object(obj)
            gobj.data.materials.clear()
            gobj.data.materials.append(bpy.data.materials.get("Glow") or _glow_material())
        return obj


GRAIN = os.environ.get("WOOD_GRAIN", "")


def _vc_material():
    m = bpy.data.materials.new("VertexColor")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    vc = nt.nodes.new("ShaderNodeVertexColor")
    bsdf.inputs["Roughness"].default_value = 0.8
    if GRAIN and os.path.exists(GRAIN):
        # preview the game's grain: a box-projected detail texture around 0.5
        # multiplying the painted colour (as shaders/materials.gdshaderinc does)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (0.95, 0.95, 0.95)
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(GRAIN)
        tex.projection = "BOX"
        tex.projection_blend = 0.3
        mul = nt.nodes.new("ShaderNodeMixRGB")
        mul.blend_type = "MULTIPLY"
        mul.inputs["Fac"].default_value = 1.0
        two = nt.nodes.new("ShaderNodeMixRGB")
        two.blend_type = "MULTIPLY"
        two.inputs["Fac"].default_value = 1.0
        two.inputs["Color2"].default_value = (2.0, 2.0, 2.0, 1.0)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], two.inputs["Color1"])
        nt.links.new(vc.outputs["Color"], mul.inputs["Color1"])
        nt.links.new(two.outputs["Color"], mul.inputs["Color2"])
        # only the wood slice (UV.x) gets the grain, like the game's layers
        uvn = nt.nodes.new("ShaderNodeUVMap")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        sub = nt.nodes.new("ShaderNodeMath")
        sub.operation = "SUBTRACT"
        sub.inputs[1].default_value = (M_WOOD + 0.5) / MAT_SLICES
        ab = nt.nodes.new("ShaderNodeMath")
        ab.operation = "ABSOLUTE"
        lt = nt.nodes.new("ShaderNodeMath")
        lt.operation = "LESS_THAN"
        lt.inputs[1].default_value = 0.02
        nt.links.new(uvn.outputs["UV"], sep.inputs["Vector"])
        nt.links.new(sep.outputs["X"], sub.inputs[0])
        nt.links.new(sub.outputs[0], ab.inputs[0])
        nt.links.new(ab.outputs[0], lt.inputs[0])
        pick = nt.nodes.new("ShaderNodeMixRGB")
        nt.links.new(lt.outputs[0], pick.inputs["Fac"])
        nt.links.new(vc.outputs["Color"], pick.inputs["Color1"])
        nt.links.new(mul.outputs["Color"], pick.inputs["Color2"])
        nt.links.new(pick.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def _glow_material():
    m = bpy.data.materials.new("Glow")
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.12, 0.14, 0.17, 1)
    bsdf.inputs["Roughness"].default_value = 0.15
    return m


# ---------------------------------------------------------------------------
# Pieces (front faces -Y, foot at z = 0)
# ---------------------------------------------------------------------------
def _boards(p, x0, x1, z0, z1, y, n, color=None, thick=0.06, arch=None):
    """n upright boards filling x0..x1 up to z1; with arch = (cx, zc, r) their
    tops are cut cleanly to that circle."""
    color = color or WOOD
    w = (x1 - x0) / n
    for i in range(n):
        x = x0 + w * (i + 0.5)
        top = z1
        tone = color if i % 3 else (color[0] * 1.06, color[1] * 1.05, color[2] * 1.03)
        if arch:
            cx, zc, r = arch
            top = zc + r
        verts = p.plank((w - 0.012, thick, top - z0), (x, y, (z0 + top) * 0.5), color=tone, wonky=0.5)
        if arch:
            cx, zc, r = arch
            p.round_top(verts, top, lambda vx, cx=cx, zc=zc, r=r: zc + math.sqrt(max(0.0, r * r - (vx - cx) ** 2)) - 0.03)


def door_tg(arch=False):
    p = Piece("door_tg_arch" if arch else "door_tg")
    W, H = 1.12, 2.2
    r = W / 2
    spring = H - r if arch else H     # a round arch starts here
    # chunky frame posts
    p.plank((0.16, 0.2, spring + 0.04), (-W / 2 - 0.08, 0.0, (spring + 0.04) / 2), color=WOOD_DARK, wonky=0.4)
    p.plank((0.16, 0.2, spring + 0.04), (W / 2 + 0.08, 0.0, (spring + 0.04) / 2), color=WOOD_DARK, wonky=0.4)
    if arch:
        # one smooth curved head, not a ring of blocks
        p.arc_frame(0.0, spring, r + 0.08, 0.2, 0.16)
        _boards(p, -W / 2, W / 2, 0.02, H, 0.04, 5, arch=(0.0, spring, r))
    else:
        p.plank((W + 0.5, 0.22, 0.2), (0, 0.0, H + 0.1), color=WOOD_DARK)
        _boards(p, -W / 2, W / 2, 0.02, H, 0.04, 5)
    # two ledges behind, and simple iron strap hinges with round ends in front
    for z in (0.45, spring - 0.45):
        p.plank((W - 0.08, 0.05, 0.14), (0, 0.09, z), color=WOOD_DARK, wonky=0.5)
        p.plank((W * 0.62, 0.025, 0.07), (-W / 2 + W * 0.31, -0.005, z), color=IRON, mat=M_METAL, round_=0.4, wonky=0.3)
        p.cyl(0.05, 0.025, (-W / 2 + W * 0.62, 0.0, z), rot=(math.pi / 2, 0, 0))
    # ring handle
    p.ring(0.07, 0.014, (W / 2 - 0.2, -0.03, 1.05), rot=(0, 0, 0))
    p.cyl(0.035, 0.03, (W / 2 - 0.2, -0.0, 1.12), rot=(math.pi / 2, 0, 0))
    # a worn threshold step
    p.plank((W + 0.3, 0.42, 0.12), (0, -0.16, 0.0), color=STONE, mat=M_STONE, round_=0.35)
    return p


def window_tg(arch=False):
    p = Piece("window_tg_arch" if arch else "window_tg")
    W, H = 0.86, 1.04
    t = 0.12    # fat, rounded frame bars
    r = W / 2
    p.plank((t, 0.16, H), (-W / 2, 0, H / 2), color=CREAM, mat=M_PAINT, round_=0.35, vary=0.02, wonky=0.4)
    p.plank((t, 0.16, H), (W / 2, 0, H / 2), color=CREAM, mat=M_PAINT, round_=0.35, vary=0.02, wonky=0.4)
    if arch:
        # a smooth round head on the side posts
        p.arc_frame(0.0, H, r, 0.16, t, color=CREAM, mat=M_PAINT)
        p.plank((0.05, 0.08, H + r - 0.08), (0, 0.02, (H + r - 0.08) / 2 + 0.02), color=CREAM, mat=M_PAINT, round_=0.4, wonky=0.2)
    else:
        p.plank((W + t, 0.16, t), (0, 0, H), color=CREAM, mat=M_PAINT, round_=0.35, vary=0.02)
        p.plank((0.05, 0.08, H - 0.06), (0, 0.02, H / 2), color=CREAM, mat=M_PAINT, round_=0.4, wonky=0.3)
    # cross bar: 2 x 2 panes
    p.plank((W - 0.06, 0.08, 0.05), (0, 0.02, H * 0.52), color=CREAM, mat=M_PAINT, round_=0.4, wonky=0.3)
    # a proud sill
    p.plank((W + 0.3, 0.26, 0.09), (0, -0.06, -0.02), color=WOOD, round_=0.35)
    pts = [(-W / 2, 0.0), (W / 2, 0.0), (W / 2, H)]
    if arch:
        for i in range(1, 16):
            a = math.pi * i / 16
            pts.append((math.cos(a) * r, H + math.sin(a) * r))
    pts.append((-W / 2, H))
    p.glass(pts, 0.05)
    return p


def shutters_tg():
    p = Piece("shutters_tg")
    W, H = 0.86, 1.04
    leaf = W / 2 + 0.04
    for sgn in (-1, 1):
        hinge = sgn * (W / 2 + 0.06)
        # each leaf swung open flat against the wall: three boards and a Z brace
        for k in range(3):
            x = hinge + sgn * (leaf / 3 * (k + 0.5))
            p.plank((leaf / 3 - 0.012, 0.045, H), (x, 0.0, H / 2), color=(0.42, 0.52, 0.48) if False else WOOD_LIGHT)
        cx = hinge + sgn * leaf / 2
        for z in (0.18, H - 0.18):
            p.plank((leaf - 0.04, 0.03, 0.1), (cx, -0.035, z), color=WOOD, wonky=0.4)
        diag = math.atan2(H - 0.36, leaf - 0.08)
        p.plank((math.hypot(H - 0.36, leaf - 0.08), 0.03, 0.09), (cx, -0.035, H / 2), rot=(0, sgn * diag, 0), color=WOOD, wonky=0.3)
        for z in (0.18, H - 0.18):
            p.cyl(0.03, 0.03, (hinge, -0.02, z), rot=(math.pi / 2, 0, 0))
    return p


def flower_box_tg():
    p = Piece("flower_box_tg")
    L = 0.98
    for z, d in ((0.06, 0.24), (0.17, 0.24)):
        p.plank((L, 0.04, 0.12), (0, -d / 2, z), color=WOOD)
        p.plank((L, 0.04, 0.12), (0, d / 2, z), color=WOOD)
    p.plank((0.05, 0.26, 0.24), (-L / 2, 0, 0.12), color=WOOD_DARK)
    p.plank((0.05, 0.26, 0.24), (L / 2, 0, 0.12), color=WOOD_DARK)
    for i in range(14):
        x = -L / 2 + 0.08 + (L - 0.16) * i / 13 + rng.uniform(-0.02, 0.02)
        p.ball(0.07, (x, rng.uniform(-0.06, 0.06), 0.26), LEAF, squash=0.8)
        if i % 2 == 0:
            p.ball(0.045, (x + 0.02, rng.uniform(-0.08, 0.04), 0.33), rng.choice(FLOWERS))
    for x in (-L / 3, L / 3):
        p.plank((0.05, 0.16, 0.14), (x, 0.12, -0.04), rot=(math.radians(-30), 0, 0), color=WOOD_DARK, wonky=0.3)
    return p


def fence_tg():
    p = Piece("fence_tg")
    L = 1.5
    for x in (-L / 2, L / 2):
        p.plank((0.13, 0.13, 1.18), (x, 0.05, 0.59), color=WOOD_DARK)
    for z in (0.3, 0.82):
        p.plank((L, 0.05, 0.1), (0, 0.1, z), color=WOOD_DARK, wonky=0.5)
    n = 8
    for i in range(n):
        x = -L / 2 + 0.1 + (L - 0.2) * (i + 0.5) / n
        h = 1.0 + rng.uniform(-0.04, 0.04)
        bw = (L - 0.2) / n - 0.025
        verts = p.plank((bw, 0.045, h), (x, 0.05, h / 2), color=WOOD if i % 2 else WOOD_LIGHT, wonky=0.6)
        # a soft, rounded top (a gentle dome across the board)
        p.round_top(verts, h, lambda vx, x=x, h=h, bw=bw: h - 0.07 * (1.0 - math.sqrt(max(0.0, 1.0 - ((vx - x) / (bw * 0.5 + 0.01)) ** 2))))
    return p


def stairs_tg():
    p = Piece("stairs_tg")
    n, rise, run, w = 6, 0.19, 0.3, 1.1
    for i in range(n):
        z = rise * (i + 1)
        p.plank((w, run + 0.04, 0.07), (0, -run * (n - i - 0.5), z - 0.035), color=WOOD if i % 2 else WOOD_LIGHT)
    for sgn in (-1, 1):
        L = math.hypot(run * n, rise * n)
        ang = math.atan2(rise * n, run * n)
        p.plank((0.07, L + 0.2, 0.24), (sgn * (w / 2 + 0.03), -run * n / 2, rise * n / 2 - 0.05), rot=(ang, 0, 0), color=WOOD_DARK)
        for i in range(0, n + 1, 2):
            y = -run * (n - i) + 0.05
            z0 = rise * i
            p.plank((0.08, 0.08, 0.95 + 0.12), (sgn * (w / 2 + 0.03), y, z0 + 0.47), color=WOOD_DARK, wonky=0.6)
        p.plank((0.08, L + 0.15, 0.08), (sgn * (w / 2 + 0.03), -run * n / 2 + 0.05, rise * n / 2 + 0.93), rot=(ang, 0, 0), color=WOOD)
    return p


def bracket_tg():
    p = Piece("bracket_tg")
    # a corbel under an overhang: wall post, a beam reaching out, a knee brace
    p.plank((0.18, 0.18, 1.3), (0, 0.0, 0.65), color=WOOD_DARK)
    p.plank((0.18, 1.0, 0.2), (0, -0.42, 1.3), color=WOOD_DARK)
    # the brace bows gently: three short segments along a shallow curve
    a = Vector((0, 0, 0.62))
    b = Vector((0, -0.7, 1.24))
    mid = (a + b) / 2 + Vector((0, 0.07, -0.07))
    pts = [a, a.lerp(mid, 0.5) * 0.5 + (a + mid) * 0.25, mid, mid.lerp(b, 0.5), b]
    for i in range(len(pts) - 1):
        d = pts[i + 1] - pts[i]
        ang = math.atan2(d.z, -d.y)
        p.plank((0.15, d.length + 0.06, 0.15), tuple((pts[i] + pts[i + 1]) / 2), rot=(-ang, 0, 0), color=WOOD, wonky=0.2)
    p.cyl(0.03, 0.04, (0, -0.09, 1.3), rot=(math.pi / 2, 0, 0), color=WOOD_DARK, mat=M_WOOD, seg=8)
    return p


def wall_planks(vertical):
    p = Piece("wall_planks_v" if vertical else "wall_planks_h")
    L, H = 2.4, 2.6
    foot = 0.7
    # stone footing
    x = -L / 2
    row = 0
    while x < L / 2 - 0.05:
        w = rng.uniform(0.32, 0.5)
        w = min(w, L / 2 - x)
        p.plank((w - 0.02, 0.32, foot / 2 - 0.02), (x + w / 2, 0.0, foot * 0.25), color=STONE, mat=M_STONE, round_=0.3)
        x += w
    x = -L / 2 + 0.2
    while x < L / 2 - 0.05:
        w = min(rng.uniform(0.32, 0.5), L / 2 - x)
        p.plank((w - 0.02, 0.32, foot / 2 - 0.02), (x + w / 2, 0.0, foot * 0.75), color=STONE, mat=M_STONE, round_=0.3)
        x += w
    p.plank((L + 0.06, 0.26, 0.08), (0, 0.0, foot + 0.02), color=WOOD_DARK)
    if vertical:
        n = int(L / 0.2)
        for i in range(n):
            xx = -L / 2 + L * (i + 0.5) / n
            p.plank((L / n - 0.014, 0.06, H - foot), (xx, 0.0, foot + (H - foot) / 2), color=WOOD if i % 3 else WOOD_LIGHT)
            if i % 2 == 0:
                p.plank((0.06, 0.04, H - foot), (xx + L / n / 2, -0.04, foot + (H - foot) / 2), color=WOOD_DARK, wonky=0.4)
    else:
        z = foot + 0.04
        k = 0
        while z < H - 0.05:
            h = 0.22
            p.plank((L, 0.06, h - 0.012), (0, -0.012 * (k % 2), z + h / 2), rot=(math.radians(-5), 0, 0), color=WOOD if k % 3 else WOOD_LIGHT)
            z += h - 0.02
            k += 1
    for sgn in (-1, 1):
        p.plank((0.18, 0.18, H - foot + 0.1), (sgn * (L / 2 + 0.05), -0.02, foot + (H - foot) / 2), color=WOOD_DARK)
    return p


def beam_bay():
    p = Piece("beam_bay")
    L, H = 2.4, 2.6
    # plaster infill behind
    p.plank((L, 0.1, H), (0, 0.06, H / 2), color=(0.95, 0.91, 0.82), mat=M_PAINT, round_=0.05, wonky=0.0, vary=0.0)
    s = 0.17
    for x in (-L / 2, L / 2):
        p.plank((s, s, H), (x, 0, H / 2), color=WOOD_DARK)
    for z in (s / 2, H * 0.48, H - s / 2):
        p.plank((L + s, s, s * 0.95), (0, -0.01, z), color=WOOD_DARK)
    ang = math.atan2(H * 0.48 - s, L / 2)
    p.plank((math.hypot(L / 2, H * 0.48 - s) + 0.1, s * 0.85, s * 0.8), (-L / 4, -0.01, H * 0.24 + s * 0.2), rot=(0, -ang, 0), color=WOOD_DARK)
    p.plank((math.hypot(L / 2, H * 0.48 - s) + 0.1, s * 0.85, s * 0.8), (L / 4, -0.01, H * 0.24 + s * 0.2), rot=(0, ang, 0), color=WOOD_DARK)
    p.plank((s * 0.9, s * 0.85, H * 0.5), (0, -0.01, H * 0.74), color=WOOD_DARK)
    return p


PIECES = {
    "door_tg": lambda: door_tg(False), "door_tg_arch": lambda: door_tg(True),
    "window_tg": lambda: window_tg(False), "window_tg_arch": lambda: window_tg(True),
    "shutters_tg": shutters_tg, "flower_box_tg": flower_box_tg, "fence_tg": fence_tg,
    "stairs_tg": stairs_tg, "bracket_tg": bracket_tg, "wall_planks_h": lambda: wall_planks(False),
    "wall_planks_v": lambda: wall_planks(True), "beam_bay": beam_bay,
}


# ---------------------------------------------------------------------------
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def preview(out):
    reset()
    order = ["door_tg", "door_tg_arch", "window_tg", "window_tg_arch", "shutters_tg", "flower_box_tg",
             "wall_planks_h", "wall_planks_v", "beam_bay", "fence_tg", "stairs_tg", "bracket_tg"]
    cols = 4
    cell = 3.9
    for i, name in enumerate(order):
        obj = PIECES[name]().to_object()
        obj.location = ((i % cols) * cell, -(i // cols) * cell * 1.5, 0)
        if name in ("stairs_tg", "bracket_tg"):
            obj.rotation_euler.z = math.radians(-55)
        if name == "window_tg" or name == "window_tg_arch":
            obj.location.z = 0.9
        if name == "shutters_tg":
            # shown round a window, as in game
            w = window_tg(False).to_object()
            w.location = obj.location + Vector((0, 0.03, 0.0))
            obj.location.z = 0.9
            w.location.z = 0.9
        if name == "flower_box_tg":
            w = window_tg(False).to_object()
            w.location = obj.location + Vector((0, 0.05, 0.75))
            obj.location.z = 0.55
        td = bpy.data.curves.new("t%d" % i, "FONT")
        td.body = "%d  %s" % (i + 1, name)
        td.size = 0.24
        td.align_x = "CENTER"
        to = bpy.data.objects.new("t%d" % i, td)
        to.location = (obj.location.x, obj.location.y - 1.35, 0.01)
        bpy.context.scene.collection.objects.link(to)
        mt = bpy.data.materials.new("ink")
        mt.use_nodes = True
        mt.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0, 0, 0, 1)
        to.data.materials.append(mt)
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, -0.005))
    gm = bpy.data.materials.new("ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.56, 0.28, 1)
    bpy.context.active_object.data.materials.append(gm)
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.74, 0.84, 0.95, 1)
    bg.inputs[1].default_value = 0.7
    sc.world = w
    sd = bpy.data.lights.new("Sun", "SUN")
    sd.energy = 3.2
    sd.angle = math.radians(4)
    sd.color = (1.0, 0.94, 0.84)
    so = bpy.data.objects.new("Sun", sd)
    so.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
    sc.collection.objects.link(so)
    cd = bpy.data.cameras.new("C")
    cd.type = "ORTHO"
    rows = (len(order) + cols - 1) // cols
    cd.ortho_scale = cols * cell * 1.0
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cx = (cols - 1) * cell / 2
    cy = -(rows - 1) * cell * 1.5 / 2
    ang = math.radians(32)
    cam.location = (cx, cy - 30 * math.cos(ang), 30 * math.sin(ang) + 1.1)
    cam.rotation_euler = (math.radians(90) - ang, 0, 0)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 48
    sc.cycles.device = "CPU"
    sc.cycles.diffuse_bounces = 4
    sc.render.resolution_x = 1800
    sc.render.resolution_y = 1700
    try:
        sc.view_settings.view_transform = "AgX"
    except TypeError:
        sc.view_settings.view_transform = "Filmic"
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("wrote", out)


def vignette(out):
    """The pieces put together: a little timber cottage corner."""
    reset()
    def put(name, loc, rz=0.0):
        o = PIECES[name]().to_object()
        o.location = loc
        o.rotation_euler.z = math.radians(rz)
        return o
    # two plank walls meeting at a corner, a door, windows with shutters and a flower box
    put("wall_planks_h", (0, 0, 0))
    put("wall_planks_h", (2.45, 0, 0))
    put("wall_planks_v", (3.75, 1.3, 0), 90)
    put("beam_bay", (-2.45, 0, 0))
    put("door_tg", (2.45, -0.07, 0))
    put("window_tg", (0, -0.06, 1.25))
    put("shutters_tg", (0, -0.05, 1.25))
    put("flower_box_tg", (0, -0.2, 1.1))
    put("window_tg_arch", (-2.45, -0.11, 1.15))
    put("bracket_tg", (1.25, -0.1, 1.4), 0)
    put("fence_tg", (-0.6, -2.6, 0))
    put("fence_tg", (0.95, -2.6, 0))
    put("stairs_tg", (5.4, 0.6, 0), 90)
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, -0.005))
    gm = bpy.data.materials.new("ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.56, 0.28, 1)
    bpy.context.active_object.data.materials.append(gm)
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.74, 0.84, 0.95, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.75
    sc.world = w
    sd = bpy.data.lights.new("Sun", "SUN")
    sd.energy = 3.4
    sd.angle = math.radians(4)
    sd.color = (1.0, 0.93, 0.82)
    so = bpy.data.objects.new("Sun", sd)
    so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
    sc.collection.objects.link(so)
    cd = bpy.data.cameras.new("C")
    cd.lens = 50
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = (3.2, -12.5, 5.2)
    cam.rotation_euler = (math.radians(70), 0, math.radians(8))
    cd.dof.use_dof = True
    cd.dof.focus_distance = 13.0
    cd.dof.aperture_fstop = 2.8
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 64
    sc.cycles.device = "CPU"
    sc.cycles.diffuse_bounces = 4
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 1000
    try:
        sc.view_settings.view_transform = "AgX"
    except TypeError:
        sc.view_settings.view_transform = "Filmic"
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("wrote", out)


# Wood tones, like Tiny Glade's palette tool (estimates: no published values)
# - name: (main, light, dark beams)
WOOD_TONES = {
    "Natural": ((0.54, 0.35, 0.23), (0.69, 0.52, 0.35), (0.35, 0.23, 0.15)),
    "Honey": ((0.70, 0.50, 0.30), (0.82, 0.65, 0.43), (0.47, 0.32, 0.19)),
    "Walnut": ((0.40, 0.26, 0.18), (0.52, 0.36, 0.25), (0.25, 0.16, 0.11)),
    "Weathered": ((0.56, 0.53, 0.48), (0.68, 0.65, 0.59), (0.38, 0.35, 0.31)),
    "Driftwood": ((0.72, 0.66, 0.57), (0.82, 0.77, 0.68), (0.50, 0.45, 0.38)),
}
# painted trims (window frames, shutters, doors can be painted)
TRIMS = {"Cream": (0.93, 0.89, 0.81), "Sage": (0.56, 0.66, 0.54), "Blue": (0.44, 0.55, 0.65),
         "Red": (0.65, 0.33, 0.29), "Bottle": (0.27, 0.42, 0.36)}


def palette_sheet(out):
    """Door, shutters on a window, plank wall and fence in each wood tone,
    plus the painted trim colours on windows and shutters."""
    global WOOD, WOOD_LIGHT, WOOD_DARK, CREAM
    reset()
    cell = 3.2
    names = list(WOOD_TONES.keys())
    for row, tone in enumerate(names):
        WOOD, WOOD_LIGHT, WOOD_DARK = WOOD_TONES[tone]
        for col, piece in enumerate(["door_tg_arch", "shutters_tg", "wall_planks_v", "fence_tg"]):
            o = PIECES[piece]().to_object()
            o.location = (col * cell, -row * cell * 1.15, 0.9 if piece == "shutters_tg" else 0)
            if piece == "shutters_tg":
                w = window_tg(False).to_object()
                w.location = o.location
            if piece == "wall_planks_v":
                o.scale = (0.85, 0.85, 0.85)
        _label("%s" % tone, (-1.9, -row * cell * 1.15 + 0.5, 0.01), 0.3)
    WOOD, WOOD_LIGHT, WOOD_DARK = WOOD_TONES["Natural"]
    for i, (name, c) in enumerate(TRIMS.items()):
        CREAM = c
        x = i * 2.6
        y = -len(names) * cell * 1.15 - 0.6
        w = window_tg(i % 2 == 1).to_object()
        w.location = (x, y, 0.9)
        WOOD_LIGHT = c
        sh = shutters_tg().to_object()
        sh.location = (x, y, 0.9)
        WOOD_LIGHT = WOOD_TONES["Natural"][1]
        _label(name, (x, y - 0.9, 0.01), 0.26)
    _stage(out, cols_w=max(4 * cell, len(TRIMS) * 2.6) + 4.0, rows_h=(len(names) + 1) * cell * 1.15, cx=(4 * cell) / 2 - 2.0)


def _label(text, loc, size):
    td = bpy.data.curves.new("t", "FONT")
    td.body = text
    td.size = size
    td.align_x = "CENTER"
    to = bpy.data.objects.new("t", td)
    to.location = loc
    bpy.context.scene.collection.objects.link(to)
    mt = bpy.data.materials.get("ink") or bpy.data.materials.new("ink")
    mt.use_nodes = True
    mt.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0, 0, 0, 1)
    to.data.materials.append(mt)


def _stage(out, cols_w, rows_h, cx):
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -0.005))
    gm = bpy.data.materials.new("ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.56, 0.28, 1)
    bpy.context.active_object.data.materials.append(gm)
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.74, 0.84, 0.95, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    sc.world = w
    sd = bpy.data.lights.new("Sun", "SUN")
    sd.energy = 3.2
    sd.angle = math.radians(4)
    sd.color = (1.0, 0.94, 0.84)
    so = bpy.data.objects.new("Sun", sd)
    so.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
    sc.collection.objects.link(so)
    cd = bpy.data.cameras.new("C")
    cd.type = "ORTHO"
    cd.ortho_scale = max(cols_w, rows_h * 0.62)
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    ang = math.radians(32)
    cy = -rows_h / 2 + 1.5
    cam.location = (cx, cy - 40 * math.cos(ang), 40 * math.sin(ang) + 1.0)
    cam.rotation_euler = (math.radians(90) - ang, 0, 0)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 48
    sc.cycles.device = "CPU"
    sc.cycles.diffuse_bounces = 4
    sc.render.resolution_x = 1800
    sc.render.resolution_y = int(1800 * min(1.4, rows_h * 0.55 / cols_w)) + 200
    try:
        sc.view_settings.view_transform = "AgX"
    except TypeError:
        sc.view_settings.view_transform = "Filmic"
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("wrote", out)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if args and args[0] == "preview":
        preview(args[1])
    elif args and args[0] == "vignette":
        vignette(args[1])
    elif args and args[0] == "palette":
        palette_sheet(args[1])
