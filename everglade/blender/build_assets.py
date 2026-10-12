"""
Everglade - Blender asset builder (Genshin Impact-inspired fantasy look).

Models every prop, plant and creature of the game as original designs in the
style of an open-world fantasy RPG village: white plaster and timber over warm
stone, teal and red tiled roofs with gold trim, stained glass, wrought iron,
stone arch bridges, windmills, painted top-lit canopies and cute creatures.
Exports vertex-coloured GLB files that Godot imports directly.
Cel shading and outlines are applied in Godot (shaders/toon.gdshaderinc).

    blender --background --python blender/build_assets.py -- assets/models
or, with the `bpy` wheel from PyPI:
    python blender/build_assets.py assets/models [only_this_asset ...] [icon]

Conventions shared with the Godot side (scripts/core/model_lib.gd):
  * 1 Blender unit = 1 metre, origin on the ground at the prop's footprint centre.
  * Creatures face -Y in Blender, which becomes +Z (glTF/Godot model front).
  * Vertex colour RGB = albedo. Vertex colour ALPHA encodes a material channel:
        1.0  solid (wood, stone, cloth)
        0.0  foliage (wind sway + season tint in the Godot shader)
        0.25 evergreen (wind sway, no season tint: firs, grass)
        0.5  petals / cloth / banners (wind sway, no season tint)
  * Objects named "Glow*" are paper/lamp surfaces lit at night.
  * Animated parts are separate child objects (legs, wings, tails, heads...).
"""

import math
import os
import random
import sys
import zlib

import bpy  # noqa: E402  (must precede bmesh when running as a module)
import bmesh
from mathutils import Matrix, Vector

# ---------------------------------------------------------------------------
# Anime palette: clean, saturated, slightly warm. Gradients go light -> dark.
# ---------------------------------------------------------------------------
STONE = (0.80, 0.79, 0.76)
STONE_DARK = (0.58, 0.58, 0.60)
STONE_WARM = (0.86, 0.80, 0.70)
MOSS = (0.45, 0.70, 0.32)
WOOD = (0.58, 0.38, 0.24)
WOOD_DARK = (0.30, 0.20, 0.16)
WOOD_LIGHT = (0.78, 0.60, 0.40)
BARK = (0.42, 0.29, 0.22)
BARK_DARK = (0.27, 0.19, 0.16)
LEAF_TOP = (0.64, 0.88, 0.38)
LEAF = (0.38, 0.72, 0.30)
LEAF_DARK = (0.16, 0.44, 0.28)
SAKURA_TOP = (1.00, 0.86, 0.91)
SAKURA = (0.98, 0.70, 0.80)
SAKURA_DARK = (0.86, 0.48, 0.64)
MOMIJI_TOP = (1.00, 0.55, 0.26)
MOMIJI = (0.92, 0.30, 0.18)
MOMIJI_DARK = (0.66, 0.14, 0.16)
PINE_TOP = (0.36, 0.66, 0.42)
PINE = (0.18, 0.46, 0.36)
PINE_DARK = (0.10, 0.30, 0.28)
BAMBOO = (0.50, 0.76, 0.36)
BAMBOO_DARK = (0.30, 0.54, 0.26)
GRASS_TIP = (0.70, 0.92, 0.42)
GRASS = (0.36, 0.70, 0.28)
GRASS_ROOT = (0.18, 0.46, 0.22)
WOOL = (1.00, 0.99, 0.96)
WOOL_SHADE = (0.86, 0.88, 0.96)
FACE = (0.30, 0.24, 0.24)
EYE = (0.06, 0.05, 0.08)
SHINE = (1.0, 1.0, 1.0)
BLUSH = (1.0, 0.56, 0.62)
HAY = (0.96, 0.82, 0.46)
HAY_DARK = (0.80, 0.62, 0.30)
IRON = (0.24, 0.24, 0.30)
PAPER = (0.99, 0.96, 0.88)
VERMILION = (0.92, 0.27, 0.16)
VERMILION_DARK = (0.70, 0.16, 0.12)
INDIGO = (0.18, 0.24, 0.48)
GOLD = (0.98, 0.78, 0.30)
CLOTH_RED = (0.90, 0.26, 0.26)
CLOTH_BLUE = (0.26, 0.48, 0.86)
CLOTH_YELLOW = (1.0, 0.84, 0.30)
CLOTH_PINK = (1.0, 0.62, 0.74)
WHITE = (1.0, 0.99, 0.96)
BEAK = (1.0, 0.66, 0.20)
WATER = (0.36, 0.70, 0.86)
ROOF_SLATE = (0.36, 0.42, 0.54)
CAT_ORANGE = (1.0, 0.66, 0.30)
CAT_DARK = (0.24, 0.20, 0.22)
KOI_ORANGE = (1.0, 0.45, 0.14)

SOLID, FOLIAGE, EVERGREEN, PETAL = 1.0, 0.0, 0.25, 0.5

rng = random.Random(1987)


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ---------------------------------------------------------------------------
# Scene helpers
# ---------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.objects):
        for block in list(coll):
            coll.remove(block)


_materials = {}


def material(name, emissive=False):
    if name in _materials:
        return _materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Color"
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    if emissive:
        nt.links.new(attr.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 2.0
    _materials[name] = mat
    return mat


class Builder:
    """Accumulates coloured primitives into a single bmesh.

    Colours can be flat, a local gradient across the primitive (`grad`) or a
    world-height gradient shared by many primitives (`wgrad`) - the latter is
    what gives canopies their painted, lit-from-above anime look.
    """

    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.color.new("Color")
        self.uv = None
        self.custom = {}

    def card(self, center, size, facing, roll, cell, color, alpha=FOLIAGE, normal=None, aspect=1.0):
        """Textured leaf/cloud card. `cell` picks a quarter of a 2x2 atlas;
        `normal` overrides the shading normal (spherical canopy normals)."""
        if self.uv is None:
            self.uv = self.bm.loops.layers.uv.new("UVMap")
        f = Vector(facing).normalized()
        up = Vector((0, 0, 1)) if abs(f.z) < 0.95 else Vector((1, 0, 0))
        u = f.cross(up).normalized()
        v = u.cross(f).normalized()
        cr, sr = math.cos(roll), math.sin(roll)
        u, v = u * cr + v * sr, v * cr - u * sr
        c = Vector(center)
        h = size * 0.5
        corners = [c - u * h - v * h * aspect, c + u * h - v * h * aspect, c + u * h + v * h * aspect, c - u * h + v * h * aspect]
        verts = [self.bm.verts.new(p) for p in corners]
        face = self.bm.faces.new(verts)
        face.smooth = True
        cx, cy = (cell % 2) * 0.5, (cell // 2) * 0.5
        uvs = [(cx, cy + 0.5), (cx + 0.5, cy + 0.5), (cx + 0.5, cy), (cx, cy)]
        n = Vector(normal).normalized() if normal is not None else f
        for loop, uvc in zip(face.loops, uvs):
            loop[self.uv].uv = uvc
            loop[self.col] = (color[0], color[1], color[2], alpha)
        for vv in verts:
            self.custom[vv] = n
        return face

    def _finish(self, verts, color, alpha, matrix, jitter=0.0, smooth=True, grad=None, wgrad=None):
        verts = [v for v in verts if isinstance(v, bmesh.types.BMVert)]
        if jitter > 0.0:
            for v in verts:
                n = v.co.normalized() if v.co.length > 1e-5 else Vector((0, 0, 1))
                v.co += n * rng.uniform(-jitter, jitter)
        local_z = {}
        if grad:
            zs = [v.co.z for v in verts]
            z0, z1 = min(zs), max(zs)
            for v in verts:
                local_z[v] = (v.co.z - z0) / max(z1 - z0, 1e-5)
        bmesh.ops.transform(self.bm, matrix=matrix, verts=verts)
        vset = set(verts)
        faces = {f for v in verts for f in v.link_faces}
        for f in faces:
            f.smooth = smooth
            for loop in f.loops:
                v = loop.vert
                if v not in vset:
                    continue
                c = color
                if grad:
                    c = lerp3(grad[1], grad[0], local_z.get(v, 0.5) ** 0.8)
                elif wgrad:
                    t = (v.co.z - wgrad[2]) / max(wgrad[3] - wgrad[2], 1e-5)
                    t = min(max(t, 0.0), 1.0)
                    c = lerp3(wgrad[1], wgrad[0], t)
                k = rng.uniform(0.985, 1.015)
                loop[self.col] = (min(c[0] * k, 1), min(c[1] * k, 1), min(c[2] * k, 1), alpha)
        return verts

    def box(self, size, loc=(0, 0, 0), color=STONE, alpha=SOLID, rot=(0, 0, 0), smooth=False, jitter=0.0, grad=None, wgrad=None):
        ret = bmesh.ops.create_cube(self.bm, size=1.0)
        return self._finish(ret["verts"], color, alpha, trs(loc, rot, size), jitter, smooth, grad, wgrad)

    def cyl(self, r1, r2, depth, loc=(0, 0, 0), color=WOOD, alpha=SOLID, seg=8, rot=(0, 0, 0), smooth=True, jitter=0.0, grad=None, wgrad=None, scale=(1, 1, 1)):
        ret = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg,
                                    radius1=r1, radius2=r2, depth=depth)
        bmesh.ops.translate(self.bm, vec=(0, 0, depth * 0.5), verts=ret["verts"])
        return self._finish(ret["verts"], color, alpha, trs(loc, rot, scale), jitter, smooth, grad, wgrad)

    def ball(self, radius, loc=(0, 0, 0), color=LEAF, alpha=SOLID, subdiv=2, scale=(1, 1, 1), rot=(0, 0, 0), jitter=0.0, smooth=True, grad=None, wgrad=None):
        ret = bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv, radius=radius)
        if jitter:
            for v in ret["verts"]:
                v.co *= 1.0 + rng.uniform(-jitter, jitter)
        return self._finish(ret["verts"], color, alpha, trs(loc, rot, scale), 0.0, smooth, grad, wgrad)

    def torus(self, major, minor, loc=(0, 0, 0), color=WOOD, alpha=SOLID, rot=(0, 0, 0), seg=16, ring=6):
        verts = []
        rows = []
        for i in range(seg):
            a = i / seg * math.tau
            row = []
            for j in range(ring):
                b = j / ring * math.tau
                r = major + minor * math.cos(b)
                row.append(self.bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b))))
            rows.append(row)
            verts += row
        for i in range(seg):
            for j in range(ring):
                a, b = rows[i][j], rows[(i + 1) % seg][j]
                c, d = rows[(i + 1) % seg][(j + 1) % ring], rows[i][(j + 1) % ring]
                self.bm.faces.new((a, b, c, d))
        return self._finish(verts, color, alpha, trs(loc, rot, (1, 1, 1)))

    def to_object(self, name, parent=None, mat_name="VertexColor", emissive=False):
        mesh = bpy.data.meshes.new(name)
        if not self.custom:
            bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.normal_update()
        self.bm.verts.index_update()
        normals = None
        if self.custom:
            normals = [tuple(self.custom.get(v, v.normal)) for v in self.bm.verts]
        self.bm.to_mesh(mesh)
        self.bm.free()
        if normals is not None:
            mesh.normals_split_custom_set_from_vertices(normals)
        # the glTF exporter only writes COLOR_0 for the active/default colour attribute
        if len(mesh.color_attributes) > 0:
            attr = mesh.color_attributes[0]
            mesh.color_attributes.active_color = attr
            try:
                mesh.color_attributes.active_color_name = attr.name
                mesh.color_attributes.default_color_name = attr.name
            except AttributeError:
                pass
        mesh.materials.append(material(mat_name, emissive))
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        if parent is not None:
            obj.parent = parent
        return obj


def trs(loc, rot, scale):
    if isinstance(scale, (int, float)):
        scale = (scale, scale, scale)
    s = Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
    r = (Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[0], 4, "X"))
    return Matrix.Translation(loc) @ r @ s


def empty(name, loc=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    obj.location = loc
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def export(out_dir, name):
    path = os.path.join(out_dir, name + ".glb")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_normals=True,
        export_vertex_color="ACTIVE",
        export_all_vertex_colors=False,
        export_materials="EXPORT",
        export_image_format="NONE",
        export_animations=False,
    )
    print("  wrote", path)


# ---------------------------------------------------------------------------
# Shared anime details
# ---------------------------------------------------------------------------
def anime_eye(b, x, y, z, r=0.035, look=(0, -1, 0)):
    """Big glossy eye: dark iris, two white highlights (the classic anime shine)."""
    lx, ly, lz = look
    b.ball(r, loc=(x, y, z), color=EYE, subdiv=2, scale=(0.85, 0.5, 1.15))
    b.ball(r * 0.38, loc=(x + r * 0.25, y + ly * r * 0.45, z + r * 0.42), color=SHINE, subdiv=1)
    b.ball(r * 0.18, loc=(x - r * 0.3, y + ly * r * 0.45, z - r * 0.35), color=SHINE, subdiv=1)


def blush(b, x, y, z, r=0.03):
    b.ball(r, loc=(x, y, z), color=BLUSH, subdiv=1, scale=(1.3, 0.35, 0.8))


def canopy(b, center, radius, layers, top, mid, bottom, alpha=FOLIAGE, squash=0.78, clumps=7, seed=0):
    """Ghibli-style cloud canopy: a dome of soft clumps painted with a shared
    top-lit gradient so it reads as one mass with bright crowns."""
    local = random.Random(seed)
    cx, cy, cz = center
    z0 = cz - radius * 0.85
    z1 = cz + radius * 1.0
    g_low = (mid, bottom, z0, cz)
    g_high = (top, mid, cz, z1)
    # core
    b.ball(radius * 0.82, loc=(cx, cy, cz), color=mid, alpha=alpha, subdiv=2, scale=(1, 1, squash), wgrad=(top, bottom, z0, z1))
    for layer in range(layers):
        t = layer / max(layers - 1, 1)
        ring_r = radius * (0.72 - 0.42 * t)
        z = cz + radius * (-0.25 + 0.75 * t)
        n = max(3, int(clumps * (1.0 - 0.5 * t)))
        for i in range(n):
            a = i / n * math.tau + local.uniform(-0.3, 0.3) + layer * 0.7
            rr = radius * local.uniform(0.34, 0.48) * (1.0 - 0.25 * t)
            p = (cx + math.cos(a) * ring_r, cy + math.sin(a) * ring_r, z + local.uniform(-0.1, 0.1) * radius)
            b.ball(rr, loc=p, color=mid, alpha=alpha, subdiv=2, scale=(1, 1, squash), wgrad=(top, bottom, z0, z1))
    b.ball(radius * 0.42, loc=(cx, cy, cz + radius * 0.62), color=top, alpha=alpha, subdiv=2, scale=(1, 1, squash), wgrad=(top, bottom, z0, z1))
    return g_low, g_high


def card_canopy(lb, center, radius, top, mid, bottom, alpha=FOLIAGE, squash=0.8, clumps=9, cards=10, seed=0, card_scale=1.0):
    """Painted canopy made of leaf-cluster cards arranged in clumps over a dome.
    Every card's shading normal points away from the canopy centre so the
    whole crown lights like one soft painted mass with a bright top."""
    local = random.Random(seed)
    cx, cy, cz = center
    z0 = cz - radius * squash
    z1 = cz + radius * squash
    centers = [(cx, cy, cz + radius * 0.35 * squash)]
    for i in range(clumps):
        # fibonacci-ish distribution over the upper 3/4 of a sphere
        t = (i + 0.5) / clumps
        incl = math.acos(1 - 1.6 * t)
        az = i * 2.39996 + local.uniform(-0.3, 0.3)
        r = radius * local.uniform(0.62, 0.78)
        centers.append((cx + math.sin(incl) * math.cos(az) * r, cy + math.sin(incl) * math.sin(az) * r, cz + math.cos(incl) * r * squash))
    for (px, py, pz) in centers:
        cr = radius * local.uniform(0.42, 0.55)
        for k in range(cards):
            d = Vector((local.uniform(-1, 1), local.uniform(-1, 1), local.uniform(-0.6, 1))).normalized()
            p = Vector((px, py, pz)) + d * cr * local.uniform(0.25, 0.8)
            outward = (p - Vector((cx, cy, cz - radius * 0.35))).normalized()
            n = (outward * 0.85 + Vector((0, 0, 0.35))).normalized()
            t = min(max((p.z - z0) / max(z1 - z0, 1e-4), 0.0), 1.0)
            col = lerp3(bottom, mid, min(t * 1.6, 1.0)) if t < 0.62 else lerp3(mid, top, (t - 0.62) / 0.38)
            facing = (d * 0.6 + Vector((local.uniform(-1, 1), local.uniform(-1, 1), local.uniform(-1, 1))) * 0.4)
            lb.card(p, cr * local.uniform(1.25, 1.65) * card_scale, facing, local.uniform(0, math.tau), local.randrange(4), col, alpha, n)
    return centers


def leafy(b, center, radius, top, mid, bottom, alpha=FOLIAGE, squash=0.8, clumps=9, cards=10, seed=0):
    """Dark inner core (hides the sky between cards) + painted leaf cards."""
    cx, cy, cz = center
    core = lerp3(bottom, (0.05, 0.12, 0.12), 0.35)
    b.ball(radius * 0.62, loc=(cx, cy, cz + radius * 0.1), color=core, alpha=alpha, subdiv=2, scale=(1, 1, squash))
    lb = Builder()
    card_canopy(lb, center, radius, top, mid, bottom, alpha, squash, clumps, cards, seed)
    return lb


def trunk(b, height, r0, r1, lean=(0.0, 0.0), color=BARK, segments=3, roots=True):
    """Gently curving trunk built from stacked tapered segments, with flared roots."""
    x = y = z = 0.0
    seg_h = height / segments
    for i in range(segments):
        t0 = i / segments
        t1 = (i + 1) / segments
        ra = r0 + (r1 - r0) * t0
        rb = r0 + (r1 - r0) * t1
        dx = lean[0] * (t1 ** 2 - t0 ** 2) * height
        dy = lean[1] * (t1 ** 2 - t0 ** 2) * height
        ang_x = -math.atan2(dy, seg_h)
        ang_y = math.atan2(dx, seg_h)
        b.cyl(ra, rb, seg_h * 1.08, loc=(x, y, z), rot=(ang_x, ang_y, 0), color=color, seg=8,
              grad=(lerp3(color, (1, 1, 1), 0.12), lerp3(color, (0, 0, 0), 0.25)))
        x += dx
        y += dy
        z += seg_h
    if roots:
        for i in range(4):
            a = i / 4 * math.tau + 0.4
            b.cyl(r0 * 0.55, r0 * 0.15, r0 * 2.2, loc=(math.cos(a) * r0 * 0.5, math.sin(a) * r0 * 0.5, -0.05),
                  rot=(math.sin(a) * 1.1, -math.cos(a) * 1.1, 0), color=color, seg=6)
    return (x, y, z)


# ---------------------------------------------------------------------------
# Trees & plants
# ---------------------------------------------------------------------------

def tree_cedar(seed, height=4.8):
    """Sugi cedar: tall soft-tiered cone."""
    rng.seed(seed)
    b = Builder()
    b.cyl(0.16, 0.08, height * 0.35, color=BARK, seg=7)
    tiers = 5
    for i in range(tiers):
        t = i / tiers
        r = (1.0 - t * 0.78) * height * 0.2
        z = height * (0.18 + t * 0.66)
        b.ball(r, loc=(0, 0, z + r * 0.4), color=PINE, alpha=EVERGREEN, subdiv=2, scale=(1, 1, 0.9),
               wgrad=(PINE_TOP, PINE_DARK, height * 0.15, height * 1.05))
    b.cyl(0.05, 0.0, height * 0.18, loc=(0, 0, height * 0.88), color=PINE, alpha=EVERGREEN, seg=6)
    b.to_object("Tree")




def bush_flowering(seed, petal, size=0.75):
    """Azalea / hydrangea: round bush sprinkled with flower balls."""
    bush(seed, size, (LEAF, (0.30, 0.62, 0.30), LEAF_DARK))
    rng.seed(seed + 9)
    b = Builder()
    for i in range(14):
        a = rng.uniform(0, math.tau)
        z = rng.uniform(0.35, 0.95) * size
        r = size * 0.62
        b.ball(size * rng.uniform(0.10, 0.16), loc=(math.cos(a) * r * 0.9, math.sin(a) * r * 0.9, z), color=petal, alpha=PETAL,
               subdiv=2, grad=(lerp3(petal, WHITE, 0.4), lerp3(petal, (0, 0, 0), 0.15)))
    b.to_object("Blooms")


def flowers(seed, petal):
    rng.seed(seed)
    b = Builder()
    for i in range(7):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0.0, 0.22)
        x, y = math.cos(a) * d, math.sin(a) * d
        h = rng.uniform(0.18, 0.36)
        b.cyl(0.013, 0.01, h, loc=(x, y, 0), color=GRASS, alpha=FOLIAGE, seg=4)
        for p in range(5):
            pa = p / 5 * math.tau
            b.ball(0.038, loc=(x + math.cos(pa) * 0.038, y + math.sin(pa) * 0.038, h), color=petal, alpha=PETAL,
                   subdiv=1, scale=(1, 1, 0.42), grad=(lerp3(petal, WHITE, 0.45), petal))
        b.ball(0.024, loc=(x, y, h + 0.012), color=CLOTH_YELLOW, alpha=PETAL, subdiv=1)
    for i in range(6):
        a = rng.uniform(0, math.tau)
        b.ball(0.07, loc=(math.cos(a) * 0.1, math.sin(a) * 0.1, 0.04), color=LEAF, alpha=FOLIAGE, subdiv=1, scale=(1.4, 0.5, 0.3), rot=(0, 0, a))
    b.to_object("Flowers")



def reeds(seed):
    rng.seed(seed)
    b = Builder()
    for i in range(8):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 0.22)
        h = rng.uniform(0.6, 1.1)
        x, y = math.cos(a) * d, math.sin(a) * d
        b.cyl(0.016, 0.006, h, loc=(x, y, 0), color=GRASS, alpha=EVERGREEN, seg=4, grad=(GRASS_TIP, GRASS_ROOT))
        if i % 2 == 0:
            b.cyl(0.032, 0.03, 0.15, loc=(x, y, h - 0.05), color=(0.55, 0.36, 0.22), alpha=EVERGREEN, seg=6)
    b.to_object("Reeds")


def lily_pad(seed):
    rng.seed(seed)
    b = Builder()
    b.cyl(0.26, 0.26, 0.02, color=LEAF, seg=12, grad=(LEAF_TOP, LEAF))
    if seed % 2 == 0:
        for p in range(8):
            pa = p / 8 * math.tau
            b.ball(0.055, loc=(math.cos(pa) * 0.05, math.sin(pa) * 0.05, 0.06), color=(1.0, 0.78, 0.88), subdiv=1, scale=(0.8, 0.8, 1.2),
                   rot=(math.sin(pa) * 0.5, -math.cos(pa) * 0.5, 0), grad=(WHITE, (1.0, 0.62, 0.78)))
        b.ball(0.03, loc=(0, 0, 0.08), color=CLOTH_YELLOW, subdiv=1)
    b.to_object("Lily")


def rock(seed, size=0.6, color=STONE):
    rng.seed(seed)
    b = Builder()
    b.ball(size, loc=(0, 0, size * 0.32), color=color, subdiv=2, jitter=0.12,
           scale=(1.0, rng.uniform(0.75, 1.0), rng.uniform(0.55, 0.75)), grad=(lerp3(color, WHITE, 0.25), lerp3(color, (0.2, 0.2, 0.35), 0.35)))
    b.ball(size * 0.6, loc=(size * 0.08, 0, size * 0.66), color=MOSS, alpha=FOLIAGE, subdiv=2, jitter=0.1, scale=(1.15, 1.0, 0.3), grad=(LEAF_TOP, MOSS))
    b.to_object("Rock")


def cobble(seed):
    rng.seed(seed)
    b = Builder()
    b.ball(0.16, color=STONE_WARM, subdiv=2, jitter=0.1, scale=(1.0, 0.8, 0.35), grad=(lerp3(STONE_WARM, WHITE, 0.3), STONE_DARK))
    b.to_object("Cobble")


def stepping_stone(seed):
    rng.seed(seed)
    b = Builder()
    b.cyl(0.38, 0.34, 0.25, loc=(0, 0, -0.15), color=STONE, seg=12, jitter=0.03, grad=(lerp3(STONE, WHITE, 0.3), STONE_DARK))
    b.to_object("Step")


def mushroom(seed):
    rng.seed(seed)
    b = Builder()
    for i in range(3):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 0.08)
        h = rng.uniform(0.07, 0.15)
        b.cyl(0.02, 0.016, h, loc=(math.cos(a) * d, math.sin(a) * d, 0), color=WHITE, seg=6)
        b.ball(0.055, loc=(math.cos(a) * d, math.sin(a) * d, h), color=CLOTH_RED, subdiv=2, scale=(1, 1, 0.55), grad=((1, 0.45, 0.4), VERMILION_DARK))
        for k in range(3):
            ka = rng.uniform(0, math.tau)
            b.ball(0.01, loc=(math.cos(a) * d + math.cos(ka) * 0.03, math.sin(a) * d + math.sin(ka) * 0.03, h + 0.022), color=WHITE, subdiv=1)
    b.to_object("Mushroom")


def stump():
    b = Builder()
    b.cyl(0.3, 0.24, 0.35, color=BARK, seg=10, jitter=0.015, grad=(BARK, BARK_DARK))
    b.cyl(0.235, 0.235, 0.01, loc=(0, 0, 0.35), color=WOOD_LIGHT, seg=10)
    b.torus(0.12, 0.012, loc=(0, 0, 0.362), color=WOOD, seg=14, ring=4)
    b.to_object("Stump")


def log_pile():
    b = Builder()
    for n, z in ((3, 0.0), (2, 0.19)):
        for i in range(n):
            x = (i - (n - 1) / 2) * 0.23
            b.cyl(0.115, 0.115, 1.0, loc=(x, -0.5, z + 0.115), rot=(-math.pi / 2, 0, 0), color=BARK, seg=8)
            b.cyl(0.1, 0.1, 1.01, loc=(x, -0.505, z + 0.115), rot=(-math.pi / 2, 0, 0), color=WOOD_LIGHT, seg=8)
    b.to_object("Logs")


# ---------------------------------------------------------------------------
# Creatures (cute anime proportions: big heads, shiny eyes, blush)
# ---------------------------------------------------------------------------
def sheep():
    root = empty("Sheep")
    body = Builder()
    for i in range(9):
        a = i / 9 * math.tau
        body.ball(0.21, loc=(math.cos(a) * 0.17, math.sin(a) * 0.25, 0.62 + 0.05 * math.sin(a * 2)),
                  color=WOOL, subdiv=2, wgrad=(WOOL, WOOL_SHADE, 0.4, 0.85))
    body.ball(0.32, loc=(0, 0, 0.66), color=WOOL, subdiv=3, scale=(0.95, 1.3, 0.9), wgrad=(WOOL, WOOL_SHADE, 0.4, 0.95))
    body.ball(0.18, loc=(0, -0.02, 0.88), color=WOOL, subdiv=2, wgrad=(WOOL, WOOL_SHADE, 0.4, 0.95))
    body.ball(0.09, loc=(0, 0.42, 0.72), color=WOOL, subdiv=2)
    body.to_object("Body", root)
    head_pivot = empty("Head", (0, -0.40, 0.80), root)
    head = Builder()
    head.ball(0.17, loc=(0, -0.08, 0.0), color=FACE, subdiv=3, scale=(0.95, 1.0, 0.95), grad=(lerp3(FACE, WHITE, 0.15), FACE))
    head.ball(0.15, loc=(0, -0.02, 0.12), color=WOOL, subdiv=2, scale=(1.15, 0.9, 0.55))
    for s in (-1, 1):
        head.ball(0.075, loc=(s * 0.18, -0.02, 0.03), color=FACE, subdiv=2, scale=(1.5, 0.45, 0.5), rot=(0, s * 0.5, 0))
        head.ball(0.05, loc=(s * 0.19, -0.04, 0.03), color=BLUSH, subdiv=1, scale=(1.3, 0.3, 0.4), rot=(0, s * 0.5, 0))
        anime_eye(head, s * 0.07, -0.23, 0.02, 0.04)
        blush(head, s * 0.115, -0.21, -0.05, 0.028)
    head.to_object("HeadMesh", head_pivot)
    for name, x, y in (("LegFL", -0.12, -0.22), ("LegFR", 0.12, -0.22), ("LegBL", -0.12, 0.24), ("LegBR", 0.12, 0.24)):
        pivot = empty(name, (x, y, 0.45), root)
        leg = Builder()
        leg.cyl(0.05, 0.045, 0.45, loc=(0, 0, -0.45), color=FACE, seg=8)
        leg.to_object(name + "Mesh", pivot)


def cat(fur=CAT_ORANGE, patch=WHITE):
    root = empty("Cat")
    b = Builder()
    b.ball(0.15, loc=(0, 0.05, 0.25), color=fur, subdiv=2, scale=(0.8, 1.45, 0.8), grad=(lerp3(fur, WHITE, 0.2), lerp3(fur, (0.3, 0.2, 0.3), 0.3)))
    b.ball(0.1, loc=(0, -0.08, 0.22), color=patch, subdiv=2, scale=(0.75, 0.9, 0.8))
    b.to_object("Body", root)
    hp = empty("Head", (0, -0.17, 0.36), root)
    h = Builder()
    h.ball(0.13, color=fur, subdiv=3, scale=(1.1, 0.95, 0.95), grad=(lerp3(fur, WHITE, 0.25), fur))
    h.ball(0.07, loc=(0, -0.08, -0.04), color=patch, subdiv=2, scale=(1.2, 0.7, 0.7))
    for s in (-1, 1):
        h.cyl(0.06, 0.0, 0.11, loc=(s * 0.08, 0.0, 0.08), rot=(0, s * 0.35, 0), color=fur, seg=4, smooth=False)
        h.cyl(0.035, 0.0, 0.07, loc=(s * 0.08, -0.012, 0.09), rot=(0, s * 0.35, 0), color=BLUSH, seg=4, smooth=False)
        anime_eye(h, s * 0.055, -0.11, 0.015, 0.034)
        blush(h, s * 0.085, -0.1, -0.035, 0.022)
        for k in (-1, 1):
            h.box((0.12, 0.004, 0.004), loc=(s * 0.12, -0.1, -0.03 + k * 0.012), rot=(0, k * 0.15, 0), color=CAT_DARK)
    h.ball(0.014, loc=(0, -0.135, -0.02), color=BLUSH, subdiv=1)
    h.to_object("HeadMesh", hp)
    tp = empty("Tail", (0, 0.24, 0.3), root)
    t = Builder()
    for i in range(5):
        t.ball(0.035, loc=(0, 0.05 * i, 0.06 * i), color=fur if i < 4 else patch, subdiv=1)
    t.to_object("TailMesh", tp)
    for name, x, y in (("LegFL", -0.06, -0.08), ("LegFR", 0.06, -0.08), ("LegBL", -0.06, 0.17), ("LegBR", 0.06, 0.17)):
        p = empty(name, (x, y, 0.17), root)
        l = Builder()
        l.cyl(0.032, 0.03, 0.17, loc=(0, 0, -0.17), color=fur, seg=6)
        l.ball(0.034, loc=(0, -0.01, -0.16), color=patch, subdiv=1, scale=(1, 1.2, 0.6))
        l.to_object(name + "Mesh", p)


def koi(color=KOI_ORANGE):
    root = empty("Koi")
    b = Builder()
    b.ball(0.08, loc=(0, 0, 0), color=WHITE, subdiv=2, scale=(0.7, 2.1, 0.6))
    for (y, s) in ((-0.06, 0.06), (0.05, 0.05)):
        b.ball(s, loc=(0, y, 0.025), color=color, subdiv=1, scale=(0.75, 1.4, 0.4))
    for s in (-1, 1):
        b.ball(0.012, loc=(s * 0.04, -0.13, 0.01), color=EYE, subdiv=1)
        b.ball(0.035, loc=(s * 0.05, -0.05, -0.02), color=WHITE, subdiv=1, scale=(1.4, 0.8, 0.15), rot=(0, s * 0.5, 0))
    b.to_object("Body", root)
    tp = empty("Tail", (0, 0.15, 0), root)
    t = Builder()
    t.ball(0.06, loc=(0, 0.05, 0), color=color, subdiv=1, scale=(0.15, 1.0, 1.0))
    t.to_object("TailMesh", tp)


def duck(color_body=WHITE, color_head=(0.16, 0.56, 0.36), duckling=False):
    root = empty("Duck")
    b = Builder()
    shade = lerp3(color_body, (0.5, 0.55, 0.8), 0.18)
    b.ball(0.16, loc=(0, 0.02, 0.10), color=color_body, subdiv=2, scale=(0.82, 1.3, 0.72), grad=(color_body, shade))
    b.ball(0.07, loc=(0, 0.20, 0.17), color=color_body, subdiv=1, scale=(0.7, 1.0, 0.8), rot=(0.6, 0, 0))
    for s in (-1, 1):
        b.ball(0.09, loc=(s * 0.11, 0.05, 0.13), color=shade, subdiv=1, scale=(0.4, 1.3, 0.6))
    b.to_object("Body", root)
    head_pivot = empty("Head", (0, -0.15, 0.20), root)
    h = Builder()
    hr = 0.09 if duckling else 0.078
    h.cyl(0.05, 0.045, 0.12, color=color_head, seg=8)
    h.ball(hr, loc=(0, -0.02, 0.15), color=color_head, subdiv=2, grad=(lerp3(color_head, WHITE, 0.25), color_head))
    h.ball(0.045, loc=(0, -0.11, 0.13), color=BEAK, subdiv=2, scale=(0.9, 1.4, 0.45))
    for s in (-1, 1):
        anime_eye(h, s * 0.05, -0.07, 0.18, 0.022)
        blush(h, s * 0.065, -0.06, 0.13, 0.016)
    h.to_object("HeadMesh", head_pivot)


def chick():
    root = empty("Chicken")
    b = Builder()
    b.ball(0.17, loc=(0, 0.03, 0.30), color=WHITE, subdiv=2, scale=(0.85, 1.1, 0.95), grad=(WHITE, WOOL_SHADE))
    b.ball(0.1, loc=(0, 0.18, 0.42), color=WHITE, subdiv=1, scale=(0.5, 0.8, 1.2), rot=(-0.5, 0, 0))
    b.to_object("Body", root)
    hp = empty("Head", (0, -0.14, 0.46), root)
    h = Builder()
    h.ball(0.09, color=WHITE, subdiv=2)
    h.ball(0.032, loc=(0, -0.09, -0.01), color=BEAK, subdiv=1, scale=(0.8, 1.3, 0.6))
    h.ball(0.04, loc=(0, -0.01, 0.09), color=CLOTH_RED, subdiv=1, scale=(0.4, 1.2, 0.8))
    h.ball(0.03, loc=(0, -0.07, -0.06), color=CLOTH_RED, subdiv=1, scale=(0.5, 0.6, 1.0))
    for s in (-1, 1):
        anime_eye(h, s * 0.055, -0.06, 0.02, 0.022)
        blush(h, s * 0.065, -0.05, -0.025, 0.015)
    h.to_object("HeadMesh", hp)
    for name, x in (("LegFL", -0.06), ("LegFR", 0.06)):
        p = empty(name, (x, 0.02, 0.17), root)
        l = Builder()
        l.cyl(0.016, 0.016, 0.17, loc=(0, 0, -0.17), color=BEAK, seg=4)
        l.to_object(name + "Mesh", p)


def bird():
    """Round little sparrow."""
    root = empty("Bird")
    b = Builder()
    b.ball(0.075, loc=(0, 0, 0), color=(0.62, 0.44, 0.32), subdiv=2, scale=(0.85, 1.3, 0.85), grad=((0.72, 0.54, 0.40), (0.45, 0.32, 0.26)))
    b.ball(0.06, loc=(0, -0.01, -0.02), color=(0.98, 0.92, 0.84), subdiv=1, scale=(0.8, 1.1, 0.7))
    b.ball(0.055, loc=(0, -0.08, 0.04), color=(0.58, 0.38, 0.28), subdiv=2)
    b.ball(0.018, loc=(0, -0.135, 0.035), color=BEAK, subdiv=1, scale=(0.6, 1.3, 0.6))
    for s in (-1, 1):
        anime_eye(b, s * 0.035, -0.115, 0.05, 0.013)
    b.box((0.06, 0.12, 0.012), loc=(0, 0.13, 0.015), color=(0.42, 0.30, 0.24))
    b.to_object("Body", root)
    for name, s in (("WingL", -1), ("WingR", 1)):
        p = empty(name, (s * 0.045, 0, 0.02), root)
        w = Builder()
        w.ball(0.1, loc=(s * 0.09, 0.01, 0), color=(0.5, 0.36, 0.28), subdiv=1, scale=(1.0, 0.5, 0.12))
        w.to_object(name + "Mesh", p)


def butterfly():
    root = empty("Butterfly")
    b = Builder()
    b.cyl(0.006, 0.006, 0.05, rot=(math.pi / 2, 0, 0), loc=(0, 0.025, 0), color=FACE, seg=4)
    b.to_object("Body", root)
    for name, s in (("WingL", -1), ("WingR", 1)):
        p = empty(name, (0, 0, 0), root)
        w = Builder()
        w.ball(0.032, loc=(s * 0.032, -0.012, 0), color=(0.62, 0.82, 1.0), subdiv=1, scale=(1, 0.9, 0.1), grad=(WHITE, (0.45, 0.68, 1.0)))
        w.ball(0.022, loc=(s * 0.025, 0.02, 0), color=CLOTH_PINK, subdiv=1, scale=(1, 0.9, 0.1))
        w.to_object(name + "Mesh", p)


# ---------------------------------------------------------------------------
# Lanterns & lights
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Fences, gates, bridges
# ---------------------------------------------------------------------------




def stair_step():
    b = Builder()
    b.box((1.0, 0.4, 0.22), loc=(0, 0, 0.11), color=STONE_WARM, jitter=0.01, grad=(lerp3(STONE_WARM, WHITE, 0.3), STONE_DARK))
    b.to_object("Step")


# ---------------------------------------------------------------------------
# Building details (used by the procedural houses)
# ---------------------------------------------------------------------------









# ---------------------------------------------------------------------------
# Countryside props
# ---------------------------------------------------------------------------

def haystack():
    """Straw stack with a little conical cap."""
    b = Builder()
    b.cyl(0.6, 0.45, 0.75, color=HAY, seg=14, jitter=0.02, grad=(HAY, HAY_DARK))
    b.cyl(0.55, 0.0, 0.7, loc=(0, 0, 0.72), color=HAY, seg=14, grad=(lerp3(HAY, WHITE, 0.3), HAY))
    b.torus(0.48, 0.03, loc=(0, 0, 0.75), color=HAY_DARK, seg=16, ring=4)
    b.to_object("Haystack")





def cart():
    root = empty("Cart")
    b = Builder()
    b.box((1.0, 1.5, 0.1), loc=(0, 0, 0.55), color=WOOD_LIGHT)
    for s in (-1, 1):
        b.box((0.06, 1.5, 0.3), loc=(s * 0.5, 0, 0.72), color=WOOD)
        b.box((1.0, 0.06, 0.3), loc=(0, s * 0.75, 0.72), color=WOOD)
        b.box((0.06, 1.2, 0.06), loc=(s * 0.25, -1.3, 0.5), color=WOOD_DARK, rot=(0.12, 0, 0))
    b.cyl(0.04, 0.04, 1.2, loc=(-0.6, 0, 0.4), rot=(0, math.pi / 2, 0), color=IRON, seg=5)
    for i in range(5):
        b.ball(0.13, loc=(rng.uniform(-0.3, 0.3), rng.uniform(-0.5, 0.5), 0.72), color=(0.62, 0.86, 0.38), subdiv=2, grad=(LEAF_TOP, LEAF))
    b.to_object("Body", root)
    for name, s in (("WheelL", -1), ("WheelR", 1)):
        p = empty(name, (s * 0.58, 0, 0.4), root)
        w = Builder()
        w.torus(0.36, 0.04, loc=(-0.04, 0, 0), rot=(0, math.pi / 2, 0), color=WOOD, seg=16, ring=5)
        for k in range(6):
            a = k / 6 * math.pi
            w.box((0.03, 0.7, 0.03), loc=(-0.04, 0, 0), rot=(a, 0, 0), color=WOOD)
        w.to_object(name + "Mesh", p)



def scarecrow():
    """Kakashi with a straw hat."""
    b = Builder()
    b.cyl(0.04, 0.04, 1.8, color=WOOD_DARK, seg=5)
    b.box((1.1, 0.06, 0.06), loc=(0, 0, 1.35), color=WOOD_DARK)
    b.box((0.5, 0.26, 0.62), loc=(0, 0, 1.15), color=INDIGO)
    b.box((1.0, 0.2, 0.18), loc=(0, 0, 1.38), color=INDIGO)
    b.box((0.08, 0.27, 0.62), loc=(0, -0.01, 1.15), color=WHITE)
    b.ball(0.17, loc=(0, 0, 1.68), color=PAPER, subdiv=2)
    for s in (-1, 1):
        b.ball(0.02, loc=(s * 0.06, -0.16, 1.7), color=EYE, subdiv=1)
    b.cyl(0.42, 0.06, 0.2, loc=(0, 0, 1.8), color=HAY, seg=16, grad=(HAY, HAY_DARK))
    b.to_object("Scarecrow")








def cloud(seed):
    """Big anime cumulus: puffy top, flat soft-blue underside."""
    rng.seed(seed)
    b = Builder()
    blobs = 10
    for i in range(blobs):
        x = rng.uniform(-3.5, 3.5)
        r = rng.uniform(1.1, 2.1) * (1.0 - abs(x) / 6.0)
        b.ball(r, loc=(x, rng.uniform(-1.1, 1.1), r * 0.45), color=WHITE, subdiv=2, scale=(1, 1, 0.8),
               wgrad=(WHITE, (0.78, 0.84, 0.98), -0.2, 2.2))
    b.ball(2.0, loc=(0, 0, 1.4), color=WHITE, subdiv=2, wgrad=(WHITE, (0.78, 0.84, 0.98), -0.2, 2.2))
    b.to_object("Cloud")


def windmill_sails():
    root = empty("Sails")
    b = Builder()
    b.ball(0.12, color=WOOD_DARK, subdiv=1)
    b.to_object("SailsMesh", root)


# ---------------------------------------------------------------------------
# Genshin / Mondstadt-inspired fantasy village assets (original designs)
# ---------------------------------------------------------------------------
TEAL = (0.22, 0.56, 0.62)
TEAL_DARK = (0.12, 0.34, 0.42)
TEAL_LIGHT = (0.42, 0.78, 0.80)
ROOF_RED = (0.86, 0.38, 0.26)
GOLD_DARK = (0.72, 0.52, 0.18)
CRYSTAL = (0.55, 0.92, 1.0)
CRYSTAL_DARK = (0.22, 0.62, 0.86)
STONE_LIGHT = (0.92, 0.89, 0.82)
GREEN_CLOTH = (0.30, 0.66, 0.52)




def bush_fruit(seed, fruit=(1.0, 0.58, 0.18), size=0.8):
    """Fruit bush (sunset-orange fruit) - bright accents for the meadow."""
    bush(seed, size)
    rng.seed(seed + 9)
    b = Builder()
    for i in range(12):
        a = rng.uniform(0, math.tau)
        z = rng.uniform(0.35, 0.95) * size
        r = size * 0.6
        b.ball(size * 0.08, loc=(math.cos(a) * r, math.sin(a) * r, z), color=fruit, alpha=PETAL, subdiv=2,
               grad=(lerp3(fruit, WHITE, 0.35), lerp3(fruit, (0.5, 0, 0), 0.2)))
    b.to_object("Fruit")


def flower_cecilia(seed):
    """Delicate white star flowers on tall stems."""
    rng.seed(seed)
    b = Builder()
    for i in range(6):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 0.2)
        x, y = math.cos(a) * d, math.sin(a) * d
        h = rng.uniform(0.3, 0.48)
        b.cyl(0.012, 0.01, h, loc=(x, y, 0), color=GRASS, alpha=FOLIAGE, seg=4)
        for p in range(5):
            pa = p / 5 * math.tau
            b.ball(0.05, loc=(x + math.cos(pa) * 0.045, y + math.sin(pa) * 0.045, h), color=WHITE, alpha=PETAL, subdiv=1,
                   scale=(1.0, 0.35, 0.12), rot=(0, 0, pa), grad=(WHITE, (0.86, 0.90, 1.0)))
        b.ball(0.02, loc=(x, y, h + 0.01), color=(0.75, 0.88, 1.0), alpha=PETAL, subdiv=1)
    b.to_object("Flowers")


def flower_windwheel(seed):
    """Pinwheel flowers: four twisted violet petals like little windmills."""
    rng.seed(seed)
    b = Builder()
    for i in range(6):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 0.2)
        x, y = math.cos(a) * d, math.sin(a) * d
        h = rng.uniform(0.22, 0.38)
        b.cyl(0.012, 0.01, h, loc=(x, y, 0), color=GRASS, alpha=FOLIAGE, seg=4)
        for p in range(4):
            pa = p / 4 * math.tau + i
            b.ball(0.045, loc=(x + math.cos(pa) * 0.04, y + math.sin(pa) * 0.04, h), color=(0.62, 0.48, 0.96), alpha=PETAL, subdiv=1,
                   scale=(1.0, 0.45, 0.1), rot=(0.5, 0, pa), grad=((0.86, 0.80, 1.0), (0.48, 0.36, 0.90)))
        b.ball(0.018, loc=(x, y, h), color=CLOTH_YELLOW, alpha=PETAL, subdiv=1)
    b.to_object("Flowers")


def flower_dandelion(seed):
    """Dandelion clocks: white fluffy seed balls."""
    rng.seed(seed)
    b = Builder()
    for i in range(6):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 0.2)
        x, y = math.cos(a) * d, math.sin(a) * d
        h = rng.uniform(0.25, 0.42)
        b.cyl(0.01, 0.008, h, loc=(x, y, 0), color=GRASS, alpha=FOLIAGE, seg=4)
        b.ball(0.06, loc=(x, y, h + 0.05), color=WHITE, alpha=PETAL, subdiv=2, grad=(WHITE, (0.88, 0.92, 0.98)))
    for i in range(5):
        a = rng.uniform(0, math.tau)
        b.ball(0.07, loc=(math.cos(a) * 0.1, math.sin(a) * 0.1, 0.03), color=LEAF, alpha=FOLIAGE, subdiv=1, scale=(1.5, 0.45, 0.25), rot=(0, 0, a))
    b.to_object("Flowers")


def slime(color=(0.45, 0.88, 0.48)):
    """Bouncy jelly slime with a glossy highlight and a happy face."""
    root = empty("Slime")
    body_pivot = empty("Body", (0, 0, 0), root)
    b = Builder()
    b.ball(0.32, loc=(0, 0, 0.27), color=color, subdiv=3, scale=(1.0, 1.0, 0.85),
           grad=(lerp3(color, WHITE, 0.45), lerp3(color, (0.0, 0.15, 0.3), 0.35)))
    b.ball(0.08, loc=(-0.1, -0.12, 0.46), color=WHITE, subdiv=2, scale=(1.2, 0.6, 0.7))
    for s in (-1, 1):
        anime_eye(b, s * 0.1, -0.29, 0.3, 0.045)
        blush(b, s * 0.17, -0.27, 0.22, 0.03)
    b.ball(0.025, loc=(0, -0.31, 0.22), color=(0.2, 0.1, 0.15), subdiv=1, scale=(1.4, 0.4, 0.6))
    b.to_object("BodyMesh", body_pivot)


def crystalfly():
    """Small glowing crystal moth that drifts around at dusk."""
    root = empty("Butterfly")
    b = Builder()
    b.ball(0.02, color=CRYSTAL, subdiv=1, scale=(0.6, 1.6, 0.6))
    b.to_object("Body", root)
    for name, s in (("WingL", -1), ("WingR", 1)):
        p = empty(name, (0, 0, 0), root)
        w = Builder()
        w.box((0.07, 0.05, 0.006), loc=(s * 0.04, 0, 0), rot=(0, 0, s * 0.6), color=CRYSTAL)
        w.to_object("Glow" + name, p, mat_name="Glow", emissive=True)


def lantern():
    """Ornate wrought-iron street lamp with a glowing glass cage."""
    b = Builder()
    b.cyl(0.18, 0.14, 0.18, color=STONE, seg=8, grad=(STONE_LIGHT, STONE_DARK))
    b.cyl(0.06, 0.045, 2.1, loc=(0, 0, 0.18), color=IRON, seg=8)
    for z in (0.5, 1.6):
        b.torus(0.07, 0.02, loc=(0, 0, z), color=GOLD, seg=10, ring=4)
    b.box((0.36, 0.36, 0.05), loc=(0, 0, 2.28), color=IRON)
    for i in range(4):
        a = i / 4 * math.tau + math.pi / 4
        b.box((0.035, 0.035, 0.42), loc=(math.cos(a) * 0.17, math.sin(a) * 0.17, 2.5), color=IRON)
    b.cyl(0.3, 0.04, 0.22, loc=(0, 0, 2.72), color=TEAL, seg=8, smooth=False, grad=(TEAL_LIGHT, TEAL_DARK))
    b.ball(0.05, loc=(0, 0, 2.98), color=GOLD, subdiv=1, scale=(1, 1, 1.4))
    b.to_object("Lantern")
    g = Builder()
    g.box((0.26, 0.26, 0.36), loc=(0, 0, 2.5), color=(1.0, 0.86, 0.55))
    g.to_object("Glow", mat_name="Glow", emissive=True)


def wall_lantern():
    """Iron bracket lantern (faces -Y)."""
    b = Builder()
    b.box((0.05, 0.28, 0.05), loc=(0, 0.1, 0.34), color=IRON)
    b.box((0.2, 0.2, 0.03), loc=(0, 0.22, 0.13), color=IRON)
    b.cyl(0.17, 0.02, 0.14, loc=(0, 0.22, 0.36), color=TEAL, seg=6, smooth=False)
    b.box((0.2, 0.2, 0.03), loc=(0, 0.22, -0.06), color=IRON)
    b.to_object("WallLantern")
    g = Builder()
    g.box((0.15, 0.15, 0.2), loc=(0, 0.22, 0.04), color=(1.0, 0.86, 0.55))
    g.to_object("Glow", mat_name="Glow", emissive=True)


def paper_lantern_post():
    """Double-arm plaza lamp post."""
    b = Builder()
    b.cyl(0.22, 0.18, 0.25, color=STONE, seg=8, grad=(STONE_LIGHT, STONE_DARK))
    b.cyl(0.07, 0.05, 2.6, loc=(0, 0, 0.25), color=IRON, seg=8)
    for s in (-1, 1):
        b.box((0.7, 0.05, 0.05), loc=(s * 0.35, 0, 2.6), color=IRON)
        b.cyl(0.2, 0.03, 0.16, loc=(s * 0.68, 0, 2.62), color=TEAL, seg=6, smooth=False)
    b.ball(0.08, loc=(0, 0, 2.9), color=GOLD, subdiv=1)
    b.to_object("Post")
    g = Builder()
    for s in (-1, 1):
        g.box((0.18, 0.18, 0.26), loc=(s * 0.68, 0, 2.45), color=(1.0, 0.86, 0.55))
    g.to_object("Glow", mat_name="Glow", emissive=True)


def wind_shrine():
    """Floating wind crystal over a carved stone plinth - a glowing landmark."""
    b = Builder()
    g = (STONE_LIGHT, STONE_DARK)
    b.cyl(0.9, 0.8, 0.3, color=STONE, seg=8, smooth=False, grad=g)
    b.cyl(0.6, 0.5, 0.35, loc=(0, 0, 0.3), color=STONE, seg=8, smooth=False, grad=g)
    for i in range(4):
        a = i / 4 * math.tau
        b.box((0.16, 0.16, 1.4), loc=(math.cos(a) * 0.55, math.sin(a) * 0.55, 0.65), rot=(0, 0, a), color=STONE_LIGHT)
        b.cyl(0.1, 0.0, 0.3, loc=(math.cos(a) * 0.55, math.sin(a) * 0.55, 2.05), color=GOLD, seg=4, smooth=False)
        b.box((0.06, 0.4, 0.08), loc=(math.cos(a) * 0.42, math.sin(a) * 0.42, 1.95), rot=(0.6, 0, a + math.pi / 2), color=GOLD)
    b.torus(0.5, 0.04, loc=(0, 0, 1.3), color=GOLD, seg=20, ring=4)
    b.to_object("Shrine")
    c = Builder()
    c.ball(0.3, loc=(0, 0, 1.55), color=CRYSTAL, subdiv=0, scale=(0.7, 0.7, 1.5), smooth=False)
    c.ball(0.12, loc=(0, 0, 0.75), color=CRYSTAL, subdiv=0, scale=(0.7, 0.7, 1.4), smooth=False)
    c.to_object("Glow", mat_name="Glow", emissive=True)


def fence_post():
    b = Builder()
    b.box((0.13, 0.13, 1.05), loc=(0, 0, 0.52), color=WOOD, grad=(WOOD_LIGHT, WOOD_DARK))
    b.cyl(0.095, 0.0, 0.1, loc=(0, 0, 1.05), color=WOOD_DARK, seg=4, rot=(0, 0, math.pi / 4), smooth=False)
    b.to_object("FencePost")


def fence_rail():
    """1 m rustic split-rail bay along +X."""
    b = Builder()
    for z in (0.78, 0.4):
        b.box((1.0, 0.055, 0.1), loc=(0.5, 0, z), color=WOOD_LIGHT, jitter=0.004, grad=(WOOD_LIGHT, WOOD))
    b.to_object("FenceRail")


def gate():
    root = empty("Gate")
    for name, s in (("LeafL", -1), ("LeafR", 1)):
        pivot = empty(name, (s * 0.5, 0, 0), root)
        b = Builder()
        for i in range(4):
            b.box((0.1, 0.045, 0.9), loc=(-s * (0.07 + i * 0.12), 0, 0.52), color=WOOD_LIGHT, grad=(WOOD_LIGHT, WOOD))
        for z in (0.3, 0.8):
            b.box((0.48, 0.05, 0.08), loc=(-s * 0.25, 0.02, z), color=WOOD)
        b.box((0.55, 0.05, 0.07), loc=(-s * 0.25, 0.03, 0.55), rot=(0, s * 0.8, 0), color=WOOD)
        b.box((0.06, 0.06, 0.1), loc=(-s * 0.45, -0.03, 0.55), color=IRON)
        b.to_object(name + "Mesh", pivot)


def bridge_plank():
    """1 m segment of a stone arch bridge with a balustrade, along +X."""
    b = Builder()
    g = (STONE_LIGHT, STONE_DARK)
    b.box((1.0, 1.6, 0.3), loc=(0.5, 0, -0.1), color=STONE_WARM, grad=(STONE_LIGHT, STONE_WARM))
    b.box((1.0, 1.7, 0.08), loc=(0.5, 0, -0.29), color=STONE_DARK)
    for s in (-1, 1):
        b.box((1.0, 0.16, 0.12), loc=(0.5, s * 0.74, 0.1), color=STONE, grad=g)
        for k in range(3):
            x = 0.17 + k * 0.33
            b.cyl(0.05, 0.035, 0.45, loc=(x, s * 0.74, 0.16), color=STONE_LIGHT, seg=6)
            b.ball(0.06, loc=(x, s * 0.74, 0.38), color=STONE_LIGHT, subdiv=1, scale=(1, 1, 0.6))
        b.box((1.02, 0.2, 0.1), loc=(0.5, s * 0.74, 0.66), color=STONE_LIGHT, grad=g)
        b.box((1.0, 0.1, 0.5), loc=(0.5, s * 0.82, -0.45), color=STONE, grad=g)
    b.to_object("Bridge")


def window_frame():
    """Arched window with leaded stained glass and a stone surround.
    0.8 wide x 1.1 tall, back on the wall plane (y=0), facing -Y."""
    b = Builder()
    w, h = 0.8, 1.1
    b.box((w + 0.2, 0.14, 0.09), loc=(0, -0.07, -h / 2 - 0.03), color=STONE_LIGHT)
    for s in (-1, 1):
        b.box((0.09, 0.08, h * 0.8), loc=(s * w / 2, -0.04, -h * 0.1), color=WOOD_DARK)
    for i in range(9):
        a = i / 8 * math.pi
        b.box((0.13, 0.09, 0.1), loc=(math.cos(a) * w / 2, -0.045, h * 0.3 + math.sin(a) * w * 0.45), rot=(0, -a + math.pi / 2, 0), color=STONE_LIGHT)
    b.box((0.03, 0.06, h * 0.95), loc=(0, -0.03, 0.0), color=IRON)
    for z in (-0.2, 0.15):
        b.box((w, 0.06, 0.03), loc=(0, -0.03, z), color=IRON)
    b.box((0.06, 0.08, 0.1), loc=(0, -0.08, h * 0.3 + w * 0.47), color=GOLD)
    b.to_object("Frame")
    g = Builder()
    g.box((w - 0.06, 0.01, h * 0.8), loc=(0, -0.012, -h * 0.1), color=(0.98, 0.90, 0.66))
    for i in range(6):
        a = (i + 0.5) / 6 * math.pi
        g.box((0.14, 0.01, 0.12), loc=(math.cos(a) * w * 0.33, -0.012, h * 0.3 + math.sin(a) * w * 0.3), color=(0.62, 0.86, 0.96))
    g.box((w * 0.7, 0.01, w * 0.25), loc=(0, -0.012, h * 0.37), color=(0.98, 0.86, 0.6))
    g.to_object("Glow", mat_name="Glow", emissive=True)


def shutters():
    """Painted teal shutters with diamond cut-outs."""
    b = Builder()
    for s in (-1, 1):
        b.box((0.42, 0.045, 0.9), loc=(s * 0.64, -0.03, -0.1), color=TEAL, grad=(TEAL_LIGHT, TEAL_DARK))
        b.box((0.08, 0.05, 0.08), loc=(s * 0.64, -0.055, 0.1), rot=(0, math.pi / 4, 0), color=WOOD_DARK)
        for z in (-0.4, 0.2):
            b.box((0.36, 0.05, 0.035), loc=(s * 0.64, -0.05, z), color=IRON)
    b.to_object("Shutters")


def flower_box():
    b = Builder()
    b.box((0.95, 0.24, 0.18), loc=(0, -0.14, -0.7), color=WOOD, grad=(WOOD_LIGHT, WOOD_DARK))
    rng.seed(4)
    cols = [CLOTH_RED, WHITE, CLOTH_YELLOW, (0.62, 0.48, 0.96)]
    for i in range(10):
        x = -0.4 + i * 0.09
        b.ball(0.075, loc=(x, -0.14, -0.57), color=LEAF, alpha=FOLIAGE, subdiv=1, grad=(LEAF_TOP, LEAF_DARK))
        b.ball(0.048, loc=(x + 0.02, -0.19, -0.5), color=cols[i % 4], alpha=PETAL, subdiv=1)
    for k in range(4):
        b.ball(0.05, loc=(-0.35 + k * 0.23, -0.27, -0.72), color=LEAF, alpha=FOLIAGE, subdiv=1, scale=(0.7, 0.7, 1.6))
    b.to_object("FlowerBox")


def door():
    """Arched double wooden door with iron straps, under a stone arch. 1.0 x 2.0, faces -Y."""
    b = Builder()
    for x in (-0.25, 0.25):
        b.box((0.48, 0.07, 1.75), loc=(x, -0.035, 0.875), color=WOOD, grad=(WOOD_LIGHT, WOOD))
    for i in range(9):
        a = i / 8 * math.pi
        b.box((0.2, 0.07, 0.2), loc=(math.cos(a) * 0.4, -0.035, 1.75 + math.sin(a) * 0.25), color=WOOD)
        b.box((0.2, 0.12, 0.16), loc=(math.cos(a) * 0.58, -0.06, 1.75 + math.sin(a) * 0.42), rot=(0, -a + math.pi / 2, 0), color=STONE_LIGHT)
    for s in (-1, 1):
        b.box((0.14, 0.12, 1.75), loc=(s * 0.58, -0.06, 0.875), color=STONE_LIGHT)
    for z in (0.4, 1.3):
        b.box((0.95, 0.09, 0.07), loc=(0, -0.08, z), color=IRON)
    for s in (-1, 1):
        b.torus(0.06, 0.012, loc=(s * 0.08, -0.1, 0.95), rot=(math.pi / 2, 0, 0), color=GOLD, seg=10, ring=4)
    b.box((0.2, 0.1, 0.12), loc=(0, -0.12, 2.2), color=GOLD)
    b.to_object("Door")


def trapdoor():
    b = Builder()
    b.box((0.8, 0.8, 0.05), loc=(0, 0, 0.025), color=WOOD)
    b.to_object("Trapdoor")


def dormer():
    b = Builder()
    b.box((0.9, 0.9, 0.8), loc=(0, 0.45, 0.4), color=(0.97, 0.95, 0.90))
    for s in (-1, 1):
        b.box((0.66, 1.1, 0.07), loc=(s * 0.25, 0.45, 1.0), rot=(0, s * 0.8, 0), color=TEAL, grad=(TEAL_LIGHT, TEAL_DARK))
        b.box((0.08, 0.92, 0.82), loc=(s * 0.46, 0.45, 0.4), color=WOOD_DARK)
    b.cyl(0.03, 0.0, 0.25, loc=(0, 0.0, 1.22), color=GOLD, seg=4)
    b.to_object("Dormer")


def chimney():
    b = Builder()
    b.box((0.46, 0.46, 1.2), loc=(0, 0, 0.6), color=STONE_WARM, grad=(STONE_LIGHT, STONE_DARK))
    b.box((0.58, 0.58, 0.1), loc=(0, 0, 1.22), color=STONE_DARK)
    b.cyl(0.1, 0.09, 0.22, loc=(0.08, 0.05, 1.27), color=ROOF_RED, seg=8)
    b.to_object("Chimney")


def weathervane():
    """Golden finial with wing-shaped vanes crowning spires."""
    root = empty("Vane")
    b = Builder()
    b.cyl(0.035, 0.02, 1.0, color=GOLD, seg=8)
    b.ball(0.08, loc=(0, 0, 0.35), color=GOLD, subdiv=2)
    b.ball(0.05, loc=(0, 0, 1.02), color=GOLD, subdiv=1, scale=(1, 1, 1.5))
    b.to_object("Pole", root)
    p = empty("Arrow", (0, 0, 0.75), root)
    a = Builder()
    for s in (-1, 1):
        for k in range(3):
            a.box((0.32 - k * 0.07, 0.015, 0.06), loc=(s * (0.17 - k * 0.02), 0, 0.05 - k * 0.06), rot=(0, s * (0.35 + k * 0.15), 0), color=GOLD)
    a.to_object("ArrowMesh", p)


def banner():
    """Tall wind banner: teal cloth with a gold swirl emblem (original design)."""
    root = empty("Banner")
    b = Builder()
    b.cyl(0.04, 0.03, 3.4, color=WOOD_DARK, seg=6)
    b.box((0.8, 0.04, 0.04), loc=(0.4, 0, 3.25), color=GOLD)
    b.ball(0.07, loc=(0, 0, 3.45), color=GOLD, subdiv=1)
    b.to_object("Pole", root)
    p = empty("Flag", (0.04, 0, 3.22), root)
    f = Builder()
    for i in range(7):
        f.box((0.72, 0.012, 0.26), loc=(0.38, 0, -0.14 - i * 0.26), color=TEAL if i < 6 else GOLD, alpha=PETAL, grad=(TEAL_LIGHT, TEAL))
    for i in range(10):
        a = i / 10 * math.tau * 1.3
        r = 0.04 + i * 0.016
        f.box((0.06, 0.02, 0.06), loc=(0.38 + math.cos(a) * r, -0.01, -0.85 + math.sin(a) * r), color=GOLD, alpha=PETAL)
    f.cyl(0.0, 0.36, 0.25, loc=(0.38, 0, -2.0), rot=(math.pi, 0, 0), color=TEAL, alpha=PETAL, seg=3, scale=(1, 0.05, 1))
    f.to_object("FlagMesh", p)


def well():
    """Round stone well with a teal tiled roof."""
    b = Builder()
    seg = 14
    for ring in range(4):
        z = ring * 0.18
        for i in range(seg):
            a = (i + 0.5 * (ring % 2)) / seg * math.tau
            b.box((0.26, 0.18, 0.17), loc=(math.cos(a) * 0.62, math.sin(a) * 0.62, z + 0.09), rot=(0, 0, a),
                  color=lerp3(STONE_LIGHT, STONE, rng.uniform(0, 1)))
    b.cyl(0.66, 0.66, 0.07, loc=(0, 0, 0.71), color=STONE_DARK, seg=seg)
    for s in (-1, 1):
        b.box((0.1, 0.1, 1.6), loc=(s * 0.66, 0, 0.8), color=WOOD_DARK)
        b.box((1.7, 0.66, 0.06), loc=(0, s * 0.28, 1.78), rot=(-s * 0.62, 0, 0), color=TEAL, grad=(TEAL_LIGHT, TEAL_DARK))
    b.box((1.72, 0.08, 0.08), loc=(0, 0, 1.98), color=GOLD)
    b.cyl(0.05, 0.05, 1.4, loc=(-0.7, 0, 1.32), rot=(0, math.pi / 2, 0), color=WOOD_DARK, seg=6)
    b.cyl(0.11, 0.13, 0.17, loc=(0, 0, 0.62), color=WOOD_LIGHT, seg=8)
    b.to_object("Well")
    w = Builder()
    w.cyl(0.56, 0.56, 0.02, loc=(0, 0, 0.45), color=WATER, seg=seg)
    w.to_object("WellWater")


def hay_bale():
    b = Builder()
    b.box((0.9, 0.5, 0.45), loc=(0, 0, 0.225), color=HAY, jitter=0.01, grad=(HAY, HAY_DARK))
    for x in (-0.25, 0.25):
        b.box((0.03, 0.52, 0.47), loc=(x, 0, 0.225), color=HAY_DARK)
    b.to_object("HayBale")


def barrel():
    """Stacked wine barrels with iron hoops (the village's famous vintage)."""
    b = Builder()
    for x, z in ((-0.33, 0.0), (0.33, 0.0)):
        b.cyl(0.3, 0.3, 0.7, loc=(x, -0.35, z + 0.3), rot=(-math.pi / 2, 0, 0), color=WOOD, seg=12, grad=(WOOD_LIGHT, WOOD_DARK))
        b.cyl(0.25, 0.25, 0.72, loc=(x, -0.36, z + 0.3), rot=(-math.pi / 2, 0, 0), color=WOOD_LIGHT, seg=12)
        for y in (-0.25, 0.25):
            b.torus(0.305, 0.02, loc=(x, y, z + 0.3), rot=(math.pi / 2, 0, 0), color=IRON, seg=14, ring=4)
    b.cyl(0.28, 0.32, 0.4, loc=(0, 0, 0.6), color=WOOD, seg=12, grad=(WOOD_LIGHT, WOOD_DARK))
    b.cyl(0.32, 0.28, 0.4, loc=(0, 0, 1.0), color=WOOD, seg=12, grad=(WOOD_LIGHT, WOOD_DARK))
    b.cyl(0.27, 0.27, 0.02, loc=(0, 0, 1.4), color=WOOD_LIGHT, seg=12)
    b.box((0.2, 0.02, 0.14), loc=(0, -0.33, 1.0), color=(0.55, 0.12, 0.2))
    b.to_object("Barrel")


def crate():
    b = Builder()
    b.box((0.6, 0.6, 0.6), loc=(0, 0, 0.3), color=WOOD_LIGHT, grad=(WOOD_LIGHT, WOOD))
    for s in (-1, 1):
        b.box((0.62, 0.62, 0.07), loc=(0, 0, 0.3 + s * 0.26), color=WOOD)
    rng.seed(5)
    for i in range(7):
        b.ball(0.085, loc=(rng.uniform(-0.18, 0.18), rng.uniform(-0.18, 0.18), 0.62), color=(0.92, 0.18, 0.18), subdiv=2,
               grad=((1.0, 0.45, 0.4), (0.6, 0.08, 0.1)))
    b.to_object("Crate")


def bench():
    """Park bench: carved wood slats on curly iron legs."""
    b = Builder()
    for i in range(3):
        b.box((1.5, 0.12, 0.05), loc=(0, -0.14 + i * 0.14, 0.46), color=WOOD_LIGHT, grad=(WOOD_LIGHT, WOOD))
    for i in range(2):
        b.box((1.5, 0.05, 0.12), loc=(0, 0.24, 0.66 + i * 0.16), rot=(-0.15, 0, 0), color=WOOD_LIGHT)
    for x in (-0.65, 0.65):
        b.box((0.06, 0.45, 0.06), loc=(x, 0.0, 0.42), color=IRON)
        b.box((0.06, 0.06, 0.45), loc=(x, -0.18, 0.22), color=IRON)
        b.box((0.06, 0.06, 0.85), loc=(x, 0.22, 0.42), rot=(-0.12, 0, 0), color=IRON)
        b.torus(0.06, 0.015, loc=(x, -0.2, 0.5), rot=(0, math.pi / 2, 0), color=IRON, seg=10, ring=4)
    b.to_object("Bench")


def fountain():
    """Tiered plaza fountain with a gold crest."""
    b = Builder()
    g = (STONE_LIGHT, STONE_DARK)
    b.cyl(1.5, 1.55, 0.5, color=STONE, seg=24, grad=g)
    b.torus(1.5, 0.1, loc=(0, 0, 0.5), color=STONE_LIGHT, seg=28, ring=6)
    b.cyl(0.28, 0.22, 1.2, loc=(0, 0, 0.4), color=STONE_LIGHT, seg=12, grad=g)
    b.cyl(0.75, 0.3, 0.25, loc=(0, 0, 1.4), color=STONE, seg=18, grad=g)
    b.cyl(0.16, 0.12, 0.6, loc=(0, 0, 1.6), color=STONE_LIGHT, seg=10)
    b.cyl(0.38, 0.14, 0.18, loc=(0, 0, 2.15), color=STONE, seg=14, grad=g)
    b.ball(0.13, loc=(0, 0, 2.45), color=GOLD, subdiv=2, grad=(CLOTH_YELLOW, GOLD_DARK))
    for i in range(4):
        a = i / 4 * math.tau
        b.ball(0.12, loc=(math.cos(a) * 1.5, math.sin(a) * 1.5, 0.62), color=GOLD, subdiv=1, scale=(1, 1, 0.7))
    b.to_object("Fountain")
    w = Builder()
    w.cyl(1.38, 1.38, 0.02, loc=(0, 0, 0.42), color=WATER, seg=24, grad=(TEAL_LIGHT, WATER))
    w.cyl(0.66, 0.66, 0.02, loc=(0, 0, 1.6), color=WATER, seg=18)
    for i in range(8):
        a = i / 8 * math.tau
        w.cyl(0.035, 0.02, 0.9, loc=(math.cos(a) * 0.62, math.sin(a) * 0.62, 0.62), rot=(math.sin(a) * 0.5, -math.cos(a) * 0.5, 0),
              color=(0.82, 0.95, 1.0), alpha=PETAL, seg=5)
    w.to_object("WellWater")


def market_stall():
    """Market stall with a striped awning and baskets of produce."""
    b = Builder()
    b.box((2.0, 0.9, 0.08), loc=(0, 0, 0.9), color=WOOD_LIGHT, grad=(WOOD_LIGHT, WOOD))
    b.box((2.0, 0.08, 0.85), loc=(0, -0.42, 0.45), color=WOOD)
    for x in (-0.95, 0.95):
        for y in (-0.4, 0.4):
            b.box((0.08, 0.08, 2.3 if y > 0 else 1.9), loc=(x, y, 1.15 if y > 0 else 0.95), color=WOOD_DARK)
    for i in range(8):
        col = CLOTH_RED if i % 2 == 0 else WHITE
        b.box((0.26, 1.2, 0.04), loc=(-0.91 + i * 0.26, -0.15, 2.05), rot=(0.32, 0, 0), color=col, alpha=PETAL)
        b.box((0.26, 0.03, 0.18), loc=(-0.91 + i * 0.26, -0.72, 1.82), color=col, alpha=PETAL)
    rng.seed(11)
    for k, col in enumerate(((1.0, 0.62, 0.18), (0.92, 0.18, 0.2), (0.62, 0.86, 0.34))):
        x = -0.6 + k * 0.6
        b.cyl(0.24, 0.2, 0.15, loc=(x, 0, 0.94), color=WOOD_LIGHT, seg=10)
        for i in range(6):
            b.ball(0.07, loc=(x + rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), 1.12), color=col, subdiv=1)
    b.to_object("Stall")


def windmill():
    """Town windmill: stone base, timbered white upper storey ringed by a
    wooden balcony, a red conical cap and big canvas sails ("Sails")."""
    root = empty("Windmill")
    b = Builder()
    g = (STONE_LIGHT, STONE_DARK)
    plaster = (0.97, 0.95, 0.89)
    b.cyl(1.55, 1.2, 3.2, color=STONE_WARM, seg=18, grad=g)
    b.cyl(1.65, 1.65, 0.3, color=STONE_DARK, seg=18)
    b.cyl(1.2, 0.98, 2.5, loc=(0, 0, 3.2), color=plaster, seg=18, grad=(WHITE, (0.86, 0.84, 0.80)))
    for k in range(8):
        a = k / 8 * math.tau
        b.box((0.1, 0.1, 2.5), loc=(math.cos(a) * 1.1, math.sin(a) * 1.1, 4.45), rot=(0, 0.08, a), color=WOOD_DARK)
    b.torus(1.05, 0.06, loc=(0, 0, 5.1), color=WOOD_DARK, seg=20, ring=4)
    # balcony deck on carved brackets with a turned railing
    b.cyl(1.85, 1.85, 0.14, loc=(0, 0, 3.2), color=WOOD, seg=24, grad=(WOOD_LIGHT, WOOD_DARK))
    for k in range(10):
        a = k / 10 * math.tau
        b.box((0.5, 0.1, 0.1), loc=(math.cos(a) * 1.45, math.sin(a) * 1.45, 3.0), rot=(0, -0.6, a), color=WOOD_DARK)
    for k in range(28):
        a = k / 28 * math.tau
        b.box((0.05, 0.05, 0.62), loc=(math.cos(a) * 1.76, math.sin(a) * 1.76, 3.58), color=WOOD_DARK)
    b.torus(1.76, 0.05, loc=(0, 0, 3.9), color=WOOD, seg=28, ring=4)
    # red cap with a gold finial
    b.cyl(1.4, 0.12, 1.9, loc=(0, 0, 5.65), color=ROOF_RED, seg=18, grad=((0.94, 0.52, 0.36), (0.60, 0.24, 0.18)))
    b.cyl(1.42, 1.42, 0.1, loc=(0, 0, 5.62), color=(0.50, 0.20, 0.15), seg=18)
    b.ball(0.13, loc=(0, 0, 7.62), color=GOLD, subdiv=1)
    # door, windows and the balcony door
    b.box((0.8, 0.12, 1.3), loc=(0, -1.38, 0.75), color=WOOD, grad=(WOOD_LIGHT, WOOD_DARK))
    b.box((0.9, 0.1, 0.08), loc=(0, -1.4, 1.42), color=STONE_DARK)
    b.box((0.42, 0.08, 0.55), loc=(0.8, -1.14, 2.2), color=(0.98, 0.9, 0.66))
    b.box((0.55, 0.1, 0.95), loc=(0, -1.06, 3.75), color=WOOD_DARK)
    b.box((0.4, 0.06, 0.45), loc=(-0.55, -0.92, 4.7), color=(0.98, 0.9, 0.66))
    b.cyl(0.18, 0.18, 0.8, loc=(0, -1.2, 5.9), rot=(math.pi / 2, 0, 0), color=WOOD_DARK, seg=8)
    b.to_object("Tower", root)
    p = empty("Sails", (0, -1.6, 5.9), root)
    s = Builder()
    s.ball(0.26, color=WOOD_DARK, subdiv=1)
    canvas = (0.97, 0.94, 0.86)
    for i in range(4):
        a = i / 4 * math.tau + math.pi / 4
        ca, sa = math.cos(a), math.sin(a)
        rot = (0, -a + math.pi / 2, 0)
        s.box((0.12, 0.1, 4.0), loc=(ca * 2.05, 0, sa * 2.05), rot=rot, color=WOOD_DARK)
        # lattice ribs across the sail frame
        for k in range(6):
            r = 0.75 + k * 0.62
            s.box((0.06, 0.06, 1.05), loc=(ca * r - sa * 0.45, -0.02, sa * r + ca * 0.45), rot=(0, -a, 0), color=WOOD)
        for off in (0.05, 0.92):
            s.box((0.05, 0.05, 3.3), loc=(ca * 2.3 - sa * off, -0.02, sa * 2.3 + ca * off), rot=rot, color=WOOD)
        # billowing canvas panel
        s.box((0.84, 0.02, 3.1), loc=(ca * 2.3 - sa * 0.48, -0.07, sa * 2.3 + ca * 0.48), rot=rot, color=canvas, alpha=PETAL,
              grad=(WHITE, (0.86, 0.82, 0.72)))
    s.to_object("SailsMesh", p)


def signpost():
    b = Builder()
    b.cyl(0.06, 0.05, 2.1, color=WOOD_DARK, seg=6)
    for i, (z, r) in enumerate(((1.75, 0.3), (1.45, -0.7), (1.15, 1.9))):
        b.box((0.8, 0.04, 0.2), loc=(0.35 * math.cos(r), 0.35 * math.sin(r), z), rot=(0, 0, r), color=WOOD_LIGHT, grad=(WOOD_LIGHT, WOOD))
        b.cyl(0.0, 0.14, 0.16, loc=(0.78 * math.cos(r), 0.78 * math.sin(r), z), rot=(0, math.pi / 2, r), color=WOOD_LIGHT, seg=3, scale=(1, 0.3, 1))
    b.ball(0.08, loc=(0, 0, 2.12), color=GOLD, subdiv=1)
    b.to_object("Sign")


def notice_board():
    b = Builder()
    for s in (-1, 1):
        b.box((0.1, 0.1, 2.0), loc=(s * 0.75, 0, 1.0), color=WOOD_DARK)
    b.box((1.5, 0.08, 1.0), loc=(0, 0, 1.25), color=WOOD, grad=(WOOD_LIGHT, WOOD))
    b.box((1.8, 0.6, 0.06), loc=(0, 0.0, 2.0), rot=(0.3, 0, 0), color=TEAL, grad=(TEAL_LIGHT, TEAL_DARK))
    rng.seed(3)
    for i in range(5):
        b.box((rng.uniform(0.2, 0.35), 0.02, rng.uniform(0.25, 0.4)), loc=(-0.5 + i * 0.25, -0.05, 1.25 + rng.uniform(-0.2, 0.2)),
              rot=(0, rng.uniform(-0.15, 0.15), 0), color=PAPER)
    b.to_object("Board")


def flower_cart():
    root = empty("Cart")
    b = Builder()
    b.box((1.4, 0.8, 0.5), loc=(0, 0, 0.75), color=WOOD, grad=(WOOD_LIGHT, WOOD_DARK))
    b.box((0.06, 1.3, 0.06), loc=(0.55, -0.9, 0.7), rot=(0.1, 0, 0), color=WOOD_DARK)
    b.box((0.06, 1.3, 0.06), loc=(-0.55, -0.9, 0.7), rot=(0.1, 0, 0), color=WOOD_DARK)
    rng.seed(7)
    cols = [CLOTH_RED, WHITE, CLOTH_YELLOW, (0.62, 0.48, 0.96), CLOTH_PINK]
    for i in range(22):
        x = rng.uniform(-0.6, 0.6)
        y = rng.uniform(-0.32, 0.32)
        b.ball(0.1, loc=(x, y, 1.05), color=LEAF, alpha=FOLIAGE, subdiv=1, grad=(LEAF_TOP, LEAF_DARK))
        b.ball(0.06, loc=(x, y, 1.15), color=cols[i % len(cols)], alpha=PETAL, subdiv=1)
    b.to_object("Body", root)
    for name, s in (("WheelL", -1), ("WheelR", 1)):
        p = empty(name, (s * 0.75, 0.15, 0.4), root)
        w = Builder()
        w.torus(0.36, 0.04, rot=(0, math.pi / 2, 0), color=WOOD, seg=16, ring=5)
        for k in range(6):
            w.box((0.03, 0.7, 0.03), rot=(k / 6 * math.pi, 0, 0), color=WOOD)
        w.to_object(name + "Mesh", p)


# ---------------------------------------------------------------------------
# Painted-card vegetation (reference: lush stylised fantasy meadows)
# ---------------------------------------------------------------------------
GOLD_LEAF = ((1.0, 0.92, 0.42), (0.98, 0.76, 0.22), (0.78, 0.50, 0.14))
ORANGE_LEAF = ((1.0, 0.78, 0.44), (0.96, 0.56, 0.24), (0.70, 0.30, 0.16))
BLOSSOM = ((1.0, 1.0, 0.98), (0.92, 0.96, 0.96), (0.62, 0.78, 0.80))
GREEN_LEAF = (LEAF_TOP, LEAF, LEAF_DARK)
TEAL_LEAF = ((0.56, 0.92, 0.80), (0.26, 0.70, 0.62), (0.10, 0.40, 0.42))


def card_tree(seed, height, tint, alpha=FOLIAGE, crown=0.36, squash=0.8, clumps=9, cards=10, bark=BARK, lean=None, branches=3):
    rng.seed(seed)
    b = Builder()
    ln = lean or (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15))
    top = trunk(b, height * 0.55, 0.06 + height * 0.04, 0.03 + height * 0.02, lean=ln, color=bark)
    for i in range(branches):
        a = i / branches * math.tau + rng.uniform(-0.4, 0.4)
        b.cyl(0.06, 0.025, height * 0.32, loc=(top[0] * 0.7, top[1] * 0.7, height * 0.42), rot=(0.85 * math.cos(a), 0.85 * math.sin(a), 0), color=bark, seg=5)
    lb = leafy(b, (top[0], top[1], height * 0.72), height * crown, *tint, alpha=alpha, squash=squash, clumps=clumps, cards=cards, seed=seed)
    b.to_object("Tree")
    lb.to_object("Leaves", mat_name="Leaves")


def tree_round(seed, height=3.4, tint=GREEN_LEAF):
    card_tree(seed, height, tint)


def tree_grand(seed, height=5.6):
    card_tree(seed, height, GREEN_LEAF, crown=0.44, squash=0.72, clumps=14, cards=12, branches=5, lean=(0.08, -0.05))


def tree_birch(seed, height=3.8):
    rng.seed(seed)
    b = Builder()
    trunk(b, height * 0.8, 0.1, 0.06, lean=(rng.uniform(-0.1, 0.1), 0.05), color=(0.94, 0.93, 0.90), segments=3, roots=False)
    for z in (0.5, 1.0, 1.6, 2.1):
        b.cyl(0.105, 0.1, 0.05, loc=(0, 0, z), color=(0.25, 0.24, 0.26), seg=6)
    lb = leafy(b, (0.1, 0, height * 0.78), height * 0.26, (0.82, 0.96, 0.48), (0.56, 0.84, 0.36), (0.26, 0.56, 0.30), squash=1.0, clumps=6, cards=9, seed=seed)
    b.to_object("Tree")
    lb.to_object("Leaves", mat_name="Leaves")


def tree_fir(seed, height=4.6):
    """Painted conifer: tiers of drooping leaf cards around a cone."""
    rng.seed(seed)
    b = Builder()
    b.cyl(0.16, 0.06, height * 0.95, color=BARK, seg=7)
    b.cyl(height * 0.17, 0.02, height * 0.8, loc=(0, 0, height * 0.18), color=PINE_DARK, alpha=EVERGREEN, seg=8)
    lb = Builder()
    tiers = 6
    for i in range(tiers):
        t = i / (tiers - 1)
        r = (1.0 - t * 0.8) * height * 0.24
        z = height * (0.2 + t * 0.68)
        n_cards = int(10 - t * 5)
        for k in range(n_cards):
            a = k / n_cards * math.tau + rng.uniform(-0.2, 0.2) + i
            p = Vector((math.cos(a) * r * 0.75, math.sin(a) * r * 0.75, z))
            n = (Vector((math.cos(a), math.sin(a), 0.6))).normalized()
            col = lerp3(PINE_DARK, PINE_TOP, 0.25 + t * 0.75)
            lb.card(p, r * 1.15, (math.cos(a), math.sin(a), -0.9), rng.uniform(-0.4, 0.4), rng.randrange(4), col, EVERGREEN, n, 0.75)
    lb.card((0, 0, height * 0.95), height * 0.12, (0.3, 0.3, 1), 0.0, 1, PINE_TOP, EVERGREEN, (0, 0, 1))
    b.to_object("Tree")
    lb.to_object("Leaves", mat_name="Leaves")


def bush(seed, size=0.7, tint=GREEN_LEAF, alpha=FOLIAGE):
    rng.seed(seed)
    b = Builder()
    lb = leafy(b, (0, 0, size * 0.55), size * 0.75, *tint, alpha=alpha, squash=0.7, clumps=5, cards=6, seed=seed)
    b.to_object("Bush")
    lb.to_object("Leaves", mat_name="Leaves")


def flower_lavender(seed):
    """Tall lavender-purple flower spikes (meadow accent)."""
    rng.seed(seed)
    b = Builder()
    for i in range(7):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 0.18)
        x, y = math.cos(a) * d, math.sin(a) * d
        h = rng.uniform(0.45, 0.75)
        lean = rng.uniform(-0.15, 0.15)
        b.cyl(0.012, 0.008, h, loc=(x, y, 0), rot=(lean, lean * 0.5, 0), color=GRASS, alpha=FOLIAGE, seg=4)
        for k in range(7):
            z = h * (0.6 + k * 0.06)
            b.ball(0.028 - k * 0.002, loc=(x + lean * z * 0.5 * 0, y - lean * z, z), color=(0.70, 0.46, 0.96), alpha=PETAL, subdiv=1,
                   scale=(1, 1, 1.3), grad=((0.86, 0.72, 1.0), (0.52, 0.30, 0.86)))
    for i in range(5):
        a = rng.uniform(0, math.tau)
        b.ball(0.08, loc=(math.cos(a) * 0.1, math.sin(a) * 0.1, 0.04), color=LEAF, alpha=FOLIAGE, subdiv=1, scale=(1.5, 0.4, 0.3), rot=(0, 0, a))
    b.to_object("Flowers")


def grass_tuft(seed):
    """Tall meadow grass: dark roots, sunlit tips."""
    rng.seed(seed)
    b = Builder()
    for i in range(16):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 0.16)
        h = rng.uniform(0.3, 0.62)
        lean = rng.uniform(0.15, 0.55)
        b.cyl(0.03, 0.0, h, loc=(math.cos(a) * d, math.sin(a) * d, 0), rot=(lean * math.cos(a + 1.57), lean * math.sin(a + 1.57), 0),
              color=GRASS, alpha=EVERGREEN, seg=3, smooth=False, grad=(GRASS_TIP, GRASS_ROOT))
    b.to_object("Grass")


# ---------------------------------------------------------------------------
# Ancient ruins (reference: meadow ruins with carved arch and rotunda)
# ---------------------------------------------------------------------------
RUIN = (0.80, 0.75, 0.64)
RUIN_DARK = (0.50, 0.48, 0.44)
RUIN_G = ((0.88, 0.83, 0.72), (0.54, 0.52, 0.48))


def _blocks(b, x0, x1, z0, z1, y=0.0, depth=0.5, row=0.42, broken_top=None, seed=0):
    """Dry-stone wall face made of individual offset blocks (chunky, readable)."""
    local = random.Random(seed)
    z = z0
    r = 0
    while z < z1 - 0.05:
        x = x0 - (0.3 if r % 2 else 0.0)
        while x < x1 - 0.05:
            w = local.uniform(0.5, 0.85)
            xa, xb = max(x, x0), min(x + w, x1)
            top = z1 if broken_top is None else broken_top((xa + xb) * 0.5)
            if xb - xa > 0.12 and z + row * 0.5 < top:
                hgt = min(row, top - z)
                b.box((xb - xa - 0.03, depth + local.uniform(-0.03, 0.04), hgt - 0.03), loc=((xa + xb) / 2, y, z + hgt / 2),
                      color=lerp3(RUIN, RUIN_DARK, local.uniform(0, 0.35)), grad=RUIN_G)
            x += w
        z += row
        r += 1


def _moss(b, x, y, z, w, d=0.5, seed=0):
    local = random.Random(seed)
    for i in range(max(1, int(w / 0.35))):
        b.ball(0.2, loc=(x - w / 2 + (i + 0.5) * w / max(1, int(w / 0.35)), y + local.uniform(-0.1, 0.1), z + 0.04), color=MOSS, alpha=FOLIAGE,
               subdiv=1, scale=(1.3, d * 2.2, 0.38), grad=(LEAF_TOP, MOSS))


def ruin_arch():
    """Carved ceremonial archway with relief bands and mossy tops."""
    b = Builder()
    span, h = 2.6, 4.2
    for s in (-1, 1):
        x = s * (span / 2 + 0.45)
        b.box((1.0, 1.0, 0.4), loc=(x, 0, 0.2), color=RUIN_DARK, grad=RUIN_G)
        for k in range(6):
            b.box((0.8, 0.8, 0.5), loc=(x, 0, 0.65 + k * 0.5), color=lerp3(RUIN, RUIN_DARK, (k % 3) * 0.12), grad=RUIN_G)
        b.box((1.0, 1.0, 0.25), loc=(x, 0, 3.55), color=RUIN, grad=RUIN_G)
    # arch voussoirs with a carved band
    n = 13
    for i in range(n):
        a = i / (n - 1) * math.pi
        r = span / 2 + 0.4
        cx, cz = math.cos(a) * r, 3.65 + math.sin(a) * r
        b.box((0.62, 0.8, 0.45), loc=(cx, 0, cz), rot=(0, -a + math.pi / 2, 0), color=RUIN, grad=RUIN_G)
        b.box((0.3, 0.86, 0.12), loc=(math.cos(a) * (r - 0.05), 0, 3.65 + math.sin(a) * (r - 0.05)), rot=(0, -a + math.pi / 2, 0), color=STONE_LIGHT)
        if i % 2 == 0:
            b.ball(0.08, loc=(math.cos(a) * r, -0.42, 3.65 + math.sin(a) * r), color=STONE_LIGHT, subdiv=1)
    b.box((0.5, 0.86, 0.6), loc=(0, 0, 3.65 + span / 2 + 0.5), color=STONE_LIGHT, grad=RUIN_G)
    _moss(b, 0, 0, 3.65 + span / 2 + 0.85, 1.6, 0.45, 3)
    _moss(b, -span / 2 - 0.45, 0, 3.7, 0.9, 0.5, 4)
    b.to_object("Arch")


def ruin_wall():
    """Broken wall segment with a pointed-arch niche window and a stump pillar."""
    b = Builder()
    def top(x):
        return 3.0 - abs(x - 0.4) * 0.6 - (0.9 if x > 2.2 else 0.0) + math.sin(x * 4.0) * 0.15
    _blocks(b, -2.5, 3.0, 0.0, 3.2, depth=0.6, broken_top=top, seed=5)
    # niche window (darker recess + pointed arch frame)
    b.box((0.7, 0.2, 1.1), loc=(-0.6, -0.25, 1.5), color=(0.42, 0.44, 0.48))
    for s in (-1, 1):
        b.box((0.16, 0.25, 1.2), loc=(-0.6 + s * 0.45, -0.3, 1.5), color=STONE_LIGHT)
        b.box((0.16, 0.25, 0.62), loc=(-0.6 + s * 0.22, -0.3, 2.26), rot=(0, s * 0.75, 0), color=STONE_LIGHT)
    b.box((1.1, 0.3, 0.12), loc=(-0.6, -0.32, 0.9), color=STONE_LIGHT)
    # pillar
    for k in range(5):
        b.box((0.6, 0.6, 0.5), loc=(-2.8, 0, 0.25 + k * 0.5), color=lerp3(RUIN, RUIN_DARK, (k % 2) * 0.15), grad=RUIN_G)
    b.box((0.8, 0.8, 0.2), loc=(-2.8, 0, 2.6), color=STONE_LIGHT)
    _moss(b, -2.8, 0, 2.7, 0.7, 0.4, 7)
    _moss(b, 0.3, 0, 2.9, 1.6, 0.45, 8)
    for i in range(5):
        b.ball(rng.uniform(0.15, 0.3), loc=(rng.uniform(-2, 3), rng.uniform(-0.9, -0.4), 0.1), color=RUIN, subdiv=1, jitter=0.2, smooth=False)
    b.to_object("Wall")


def ruin_pillar():
    """Free-standing pillar with a carved capital, slightly toppled."""
    b = Builder()
    b.box((0.9, 0.9, 0.3), loc=(0, 0, 0.15), color=RUIN_DARK, grad=RUIN_G)
    for k in range(5):
        b.box((0.62, 0.62, 0.55), loc=(0, 0, 0.55 + k * 0.55), rot=(0, 0, k * 0.04), color=lerp3(RUIN, RUIN_DARK, (k % 2) * 0.12), grad=RUIN_G)
    b.box((0.9, 0.9, 0.18), loc=(0, 0, 3.05), color=STONE_LIGHT)
    b.box((0.75, 0.75, 0.25), loc=(0, 0, 3.25), color=RUIN, grad=RUIN_G)
    _moss(b, 0, 0, 3.4, 0.7, 0.4, 2)
    b.to_object("Pillar")


def ruin_slab():
    """Fallen lintel resting on a broken post, overgrown with moss."""
    b = Builder()
    b.box((0.7, 0.7, 1.8), loc=(0.9, 0, 0.9), color=RUIN, grad=RUIN_G)
    b.box((3.4, 1.0, 0.55), loc=(-0.2, 0, 1.25), rot=(0, 0.42, 0.1), color=RUIN, grad=RUIN_G)
    _moss(b, -0.6, 0, 1.7, 1.8, 0.5, 4)
    b.ball(0.6, loc=(-1.6, 0.1, 0.2), color=RUIN_DARK, subdiv=1, jitter=0.2, smooth=False)
    b.to_object("Slab")


def rotunda():
    """Domed rotunda on columns with a broken dome and glowing rune rings."""
    b = Builder()
    g = RUIN_G
    b.cyl(2.4, 2.5, 0.35, color=RUIN_DARK, seg=24, grad=g)
    b.cyl(2.15, 2.2, 0.3, loc=(0, 0, 0.35), color=RUIN, seg=24, grad=g)
    for tier, (z0, r, hgt) in enumerate(((0.65, 1.9, 2.4), (3.6, 1.5, 1.8))):
        for i in range(8):
            a = i / 8 * math.tau
            x, y = math.cos(a) * r, math.sin(a) * r
            b.cyl(0.2, 0.2, 0.18, loc=(x, y, z0), color=STONE_LIGHT, seg=8)
            b.cyl(0.15, 0.13, hgt, loc=(x, y, z0 + 0.18), color=RUIN, seg=10, grad=g)
            b.box((0.42, 0.42, 0.2), loc=(x, y, z0 + 0.18 + hgt), rot=(0, 0, a), color=STONE_LIGHT)
        b.cyl(r + 0.35, r + 0.3, 0.42, loc=(0, 0, z0 + 0.38 + hgt), color=RUIN, seg=24, grad=g)
        b.torus(r + 0.33, 0.06, loc=(0, 0, z0 + 0.8 + hgt), color=STONE_LIGHT, seg=28, ring=4)
    # broken dome: partial shell built from ribs and panels (one sector missing)
    for i in range(16):
        a0 = i / 16 * math.tau
        if 9 <= i <= 11:
            continue
        for k in range(5):
            el0 = k / 5 * math.pi / 2
            el1 = (k + 1) / 5 * math.pi / 2
            r0, r1 = 1.85 * math.cos(el0), 1.85 * math.cos(el1)
            z_0, z_1 = 6.2 + 1.85 * math.sin(el0), 6.2 + 1.85 * math.sin(el1)
            a1 = a0 + math.tau / 16
            mid = (a0 + a1) / 2
            b.box((r0 * 0.42, 0.14, (z_1 - z_0) * 1.25), loc=(math.cos(mid) * (r0 + r1) / 2, math.sin(mid) * (r0 + r1) / 2, (z_0 + z_1) / 2),
                  rot=(0, -(el0 + el1) / 2 + math.pi / 2, mid), color=lerp3(RUIN, RUIN_DARK, (k % 2) * 0.1))
    b.cyl(0.3, 0.22, 0.4, loc=(0, 0, 8.0), color=STONE_LIGHT, seg=10)
    b.ball(0.22, loc=(0, 0, 8.55), color=RUIN, subdiv=2)
    _moss(b, 1.2, 0, 7.5, 1.0, 0.6, 5)
    b.to_object("Rotunda")
    gl = Builder()
    for z, r in ((0.72, 1.4), (2.0, 1.0), (4.6, 0.8)):
        gl.torus(r, 0.03, loc=(0, 0, z), color=CRYSTAL, seg=32, ring=4)
        for k in range(6):
            a = k / 6 * math.tau
            gl.box((0.14, 0.02, 0.14), loc=(math.cos(a) * r, math.sin(a) * r, z), rot=(0, 0, a), color=CRYSTAL)
    gl.cyl(0.08, 0.02, 5.0, loc=(0, 0, 0.7), color=(0.62, 0.92, 1.0), seg=8)
    gl.to_object("Glow", mat_name="Glow", emissive=True)


def rock_big(seed, size=1.4):
    """Large flat-topped boulder (perch for birds)."""
    rng.seed(seed)
    b = Builder()
    b.ball(size, loc=(0, 0, size * 0.25), color=STONE, subdiv=1, jitter=0.12, scale=(1.3, 1.0, 0.65), smooth=False,
           grad=((0.86, 0.85, 0.80), (0.46, 0.50, 0.56)))
    b.ball(size * 0.7, loc=(size * 0.2, 0, size * 0.6), color=MOSS, alpha=FOLIAGE, subdiv=2, scale=(1.3, 1.1, 0.22), grad=(LEAF_TOP, MOSS))
    b.to_object("Rock")


# ---------------------------------------------------------------------------
# Town square pieces (reference: windmill town plaza)
# ---------------------------------------------------------------------------
def cafe_table():
    b = Builder()
    b.cyl(0.42, 0.42, 0.05, loc=(0, 0, 0.72), color=WOOD_LIGHT, seg=14, grad=(WOOD_LIGHT, WOOD))
    b.cyl(0.05, 0.05, 0.72, color=IRON, seg=6)
    b.cyl(0.25, 0.25, 0.03, color=IRON, seg=10)
    for i in range(3):
        a = i / 3 * math.tau + 0.4
        x, y = math.cos(a) * 0.7, math.sin(a) * 0.7
        b.cyl(0.2, 0.2, 0.05, loc=(x, y, 0.44), color=WOOD, seg=10)
        for k in range(3):
            ka = k / 3 * math.tau
            b.cyl(0.02, 0.02, 0.44, loc=(x + math.cos(ka) * 0.13, y + math.sin(ka) * 0.13, 0), color=WOOD_DARK, seg=4)
    b.cyl(0.04, 0.03, 0.12, loc=(0.1, 0.05, 0.77), color=(0.95, 0.95, 1.0), seg=8)
    b.ball(0.06, loc=(-0.12, -0.05, 0.8), color=CLOTH_RED, subdiv=1)
    b.to_object("Table")


def planter():
    b = Builder()
    b.box((1.0, 0.5, 0.45), loc=(0, 0, 0.22), color=STONE_LIGHT, grad=(STONE_LIGHT, STONE))
    b.box((1.1, 0.6, 0.08), loc=(0, 0, 0.47), color=STONE)
    rng.seed(9)
    cols = [CLOTH_RED, CLOTH_YELLOW, WHITE, (0.7, 0.5, 1.0)]
    for i in range(12):
        x, y = rng.uniform(-0.4, 0.4), rng.uniform(-0.18, 0.18)
        b.ball(0.12, loc=(x, y, 0.6), color=LEAF, alpha=FOLIAGE, subdiv=1, grad=(LEAF_TOP, LEAF_DARK))
        b.ball(0.06, loc=(x, y, 0.72), color=cols[i % 4], alpha=PETAL, subdiv=1)
    b.to_object("Planter")


def fence_pillar():
    """Stone pillar post with a cap stone (ornamental town fence)."""
    b = Builder()
    b.box((0.38, 0.38, 1.25), loc=(0, 0, 0.62), color=STONE_LIGHT, grad=RUIN_G)
    b.box((0.48, 0.48, 0.12), loc=(0, 0, 1.3), color=STONE)
    b.cyl(0.24, 0.05, 0.22, loc=(0, 0, 1.36), color=STONE_LIGHT, seg=4, rot=(0, 0, math.pi / 4), smooth=False)
    b.to_object("FencePost")


def fence_ornate():
    """1 m ornamental wooden railing with carved scroll arches, along +X."""
    b = Builder()
    b.box((1.0, 0.09, 0.1), loc=(0.5, 0, 1.0), color=WOOD, grad=(WOOD_LIGHT, WOOD_DARK))
    b.box((1.0, 0.09, 0.1), loc=(0.5, 0, 0.2), color=WOOD, grad=(WOOD_LIGHT, WOOD_DARK))
    for k in range(5):
        a = k / 4 * math.pi
        b.box((0.13, 0.06, 0.05), loc=(0.5 + math.cos(a) * 0.36, 0, 0.55 + math.sin(a) * 0.36), rot=(0, -a + math.pi / 2, 0), color=WOOD_DARK)
    for x in (0.12, 0.88):
        b.box((0.05, 0.06, 0.8), loc=(x, 0, 0.6), color=WOOD_DARK)
    b.torus(0.12, 0.022, loc=(0.5, 0, 0.55), rot=(math.pi / 2, 0, 0), color=WOOD_DARK, seg=12, ring=4)
    b.to_object("FenceRail")


def gate_ornate():
    root = empty("Gate")
    for name, s in (("LeafL", -1), ("LeafR", 1)):
        pivot = empty(name, (s * 0.5, 0, 0), root)
        b = Builder()
        for i in range(5):
            b.box((0.085, 0.05, 1.5 - abs(i - 2) * 0.05), loc=(-s * (0.06 + i * 0.095), 0, 0.8), color=WOOD, grad=(WOOD_LIGHT, WOOD_DARK))
        for z in (0.35, 1.25):
            b.box((0.5, 0.06, 0.08), loc=(-s * 0.25, 0.02, z), color=WOOD_DARK)
        b.box((0.06, 0.07, 0.4), loc=(-s * 0.46, -0.03, 0.85), color=IRON)
        b.to_object(name + "Mesh", pivot)


# ---------------------------------------------------------------------------
# Lakeside village pieces (reference: white-walled village by a jade lake)
# ---------------------------------------------------------------------------
def window_lattice():
    """Square dark-wood lattice window over glowing paper. Same footprint as window_frame."""
    b = Builder()
    w, h = 0.8, 0.9
    b.box((w + 0.14, 0.1, h + 0.14), loc=(0, -0.04, 0), color=WOOD_DARK)
    g = Builder()
    g.box((w - 0.04, 0.01, h - 0.04), loc=(0, -0.1, 0), color=(0.98, 0.92, 0.78))
    for i in range(1, 5):
        b.box((0.025, 0.04, h), loc=(-w / 2 + i * w / 5, -0.11, 0), color=WOOD_DARK)
        b.box((w, 0.04, 0.025), loc=(0, -0.11, -h / 2 + i * h / 5), color=WOOD_DARK)
    b.to_object("Frame")
    g.to_object("Glow", mat_name="Glow", emissive=True)


def door_wood():
    """Dark lacquered double door with a frame and two red lanterns. 1.0 x 2.0, faces -Y."""
    b = Builder()
    for x in (-0.25, 0.25):
        b.box((0.48, 0.07, 1.95), loc=(x, -0.035, 0.98), color=(0.36, 0.22, 0.16), grad=((0.5, 0.32, 0.22), (0.26, 0.16, 0.12)))
        for z in (0.5, 1.0, 1.5):
            b.ball(0.025, loc=(x * 0.6, -0.08, z), color=GOLD, subdiv=1)
    b.box((1.25, 0.14, 0.14), loc=(0, -0.07, 2.05), color=(0.26, 0.18, 0.14))
    for s in (-1, 1):
        b.box((0.12, 0.14, 2.05), loc=(s * 0.58, -0.07, 1.0), color=(0.26, 0.18, 0.14))
    b.to_object("Door")
    g = Builder()
    for s in (-1, 1):
        g.ball(0.13, loc=(s * 0.82, -0.25, 1.9), color=CLOTH_RED, subdiv=2, scale=(1, 1, 1.25))
    g.to_object("Glow", mat_name="Glow", emissive=True)


def bridge_slab():
    """1 m segment of a flat stone causeway (no railings), along +X."""
    b = Builder()
    b.box((1.0, 1.7, 0.32), loc=(0.5, 0, -0.12), color=STONE_LIGHT, grad=RUIN_G)
    for s in (-1, 1):
        b.box((1.0, 0.12, 0.6), loc=(0.5, s * 0.82, -0.45), color=STONE, grad=RUIN_G)
    b.box((0.04, 1.72, 0.33), loc=(0.98, 0, -0.12), color=RUIN_DARK)
    b.to_object("Bridge")


def bamboo_raft():
    """Bamboo raft floating on the lake, with a basket."""
    b = Builder()
    for i in range(9):
        y = -0.8 + i * 0.2
        b.cyl(0.09, 0.09, 3.0, loc=(-1.5, y, 0.05), rot=(0, math.pi / 2, 0), color=(0.86, 0.80, 0.52), seg=8, grad=((0.92, 0.88, 0.62), (0.66, 0.56, 0.32)))
    for x in (-1.0, 0.0, 1.0):
        b.box((0.08, 1.9, 0.05), loc=(x, 0, 0.16), color=WOOD_DARK)
    b.cyl(0.32, 0.36, 0.25, loc=(0.6, 0.2, 0.14), color=(0.78, 0.64, 0.36), seg=12)
    b.cyl(0.035, 0.035, 2.4, loc=(-1.2, 0.3, 0.14), rot=(1.2, 0.0, 0.3), color=(0.75, 0.70, 0.44), seg=5)
    b.to_object("Raft")


def stone_lantern2():
    """Squat stone lantern with a little pagoda cap."""
    b = Builder()
    b.box((0.5, 0.5, 0.2), loc=(0, 0, 0.1), color=STONE, grad=RUIN_G)
    b.box((0.24, 0.24, 0.55), loc=(0, 0, 0.47), color=STONE_LIGHT)
    b.box((0.44, 0.44, 0.1), loc=(0, 0, 0.78), color=STONE)
    for i in range(4):
        a = i / 4 * math.tau + math.pi / 4
        b.box((0.07, 0.07, 0.32), loc=(math.cos(a) * 0.15, math.sin(a) * 0.15, 0.99), color=STONE_LIGHT)
    b.cyl(0.42, 0.06, 0.25, loc=(0, 0, 1.15), color=STONE, seg=4, rot=(0, 0, math.pi / 4), smooth=False)
    b.ball(0.06, loc=(0, 0, 1.45), color=STONE_LIGHT, subdiv=1)
    b.to_object("Lantern")
    g = Builder()
    g.box((0.2, 0.2, 0.26), loc=(0, 0, 0.98), color=(1.0, 0.86, 0.55))
    g.to_object("Glow", mat_name="Glow", emissive=True)


def tea_terrace():
    """Terraced tea field: stepped rows of round, neatly clipped bushes (4 x 4 m)."""
    b = Builder()
    lb = Builder()
    for row in range(4):
        z = row * 0.45
        y = -1.6 + row * 1.05
        b.box((4.2, 1.1, z + 0.4), loc=(0, y, (z + 0.4) / 2 - 0.2), color=(0.62, 0.48, 0.34), grad=((0.66, 0.54, 0.38), (0.48, 0.36, 0.28)))
        b.box((4.2, 0.12, z + 0.45), loc=(0, y - 0.55, (z + 0.45) / 2 - 0.2), color=STONE, grad=RUIN_G)
        for k in range(8):
            x = -1.8 + k * 0.52
            b.ball(0.3, loc=(x, y + 0.05, z + 0.38), color=(0.30, 0.66, 0.36), alpha=EVERGREEN, subdiv=2, scale=(1.05, 1.0, 0.75),
                   grad=((0.54, 0.86, 0.42), (0.18, 0.46, 0.30)))
    b.to_object("Terrace")


def karst(seed, height=28.0):
    """Towering karst peak for the backdrop: tiered rock with green ledges."""
    rng.seed(seed)
    b = Builder()
    lb = Builder()
    tiers = 6
    for i in range(tiers):
        t = i / tiers
        r = height * (0.34 - 0.24 * t) * rng.uniform(0.9, 1.1)
        z = height * t * 0.92
        off = (rng.uniform(-1, 1) * r * 0.15, rng.uniform(-1, 1) * r * 0.15)
        b.cyl(r, r * 0.82, height * 0.2, loc=(off[0], off[1], z), color=(0.56, 0.64, 0.70), seg=9, jitter=r * 0.06, smooth=False,
              wgrad=((0.80, 0.86, 0.86), (0.36, 0.44, 0.52), 0, height))
        # grassy ledge cap
        b.cyl(r * 0.86, r * 0.6, height * 0.025, loc=(off[0], off[1], z + height * 0.19), color=(0.42, 0.70, 0.44), alpha=EVERGREEN, seg=9, jitter=r * 0.04,
              smooth=False)
        for k in range(3):
            a = rng.uniform(0, math.tau)
            p = (off[0] + math.cos(a) * r * 0.6, off[1] + math.sin(a) * r * 0.6, z + height * 0.215)
            lb.card(p, r * 0.5, (math.cos(a), math.sin(a), 0.6), rng.uniform(0, 6), rng.randrange(4), (0.36, 0.66, 0.46), EVERGREEN, (math.cos(a), math.sin(a), 1))
    b.ball(height * 0.09, loc=(0, 0, height * 1.05), color=(0.42, 0.70, 0.44), alpha=EVERGREEN, subdiv=1, scale=(1, 1, 0.5))
    b.to_object("Karst")
    lb.to_object("Leaves", mat_name="Leaves")


def cliff(seed, width=16.0):
    """Layered grey cliff wall with grassy top (town backdrop)."""
    rng.seed(seed)
    b = Builder()
    for i in range(7):
        x = -width / 2 + i * width / 6 + rng.uniform(-1, 1)
        h = rng.uniform(7, 13)
        b.box((rng.uniform(3, 5), rng.uniform(3, 4.5), h), loc=(x, rng.uniform(-0.8, 0.8), h / 2), rot=(rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08), rng.uniform(-0.3, 0.3)),
              color=(0.66, 0.68, 0.70), jitter=0.3, wgrad=((0.86, 0.86, 0.84), (0.42, 0.46, 0.52), 0, 13))
        b.box((rng.uniform(3.2, 5.2), rng.uniform(3.2, 4.7), 0.5), loc=(x, 0, h), color=(0.46, 0.74, 0.40), alpha=EVERGREEN, jitter=0.2)
    b.to_object("Cliff")


ASSETS = {
    # trees: names kept so saved glades and code keep working
    "tree_round_a": lambda: tree_round(1, 3.4),
    "tree_round_b": lambda: tree_grand(2, 5.2),
    "tree_round_c": lambda: tree_round(3, 2.8, ((0.72, 0.92, 0.42), (0.48, 0.80, 0.34), (0.22, 0.52, 0.30))),
    "tree_pine_a": lambda: tree_fir(4, 4.8),
    "tree_pine_b": lambda: tree_fir(5, 3.6),
    "tree_birch": lambda: tree_birch(6),
    "tree_cedar": lambda: tree_cedar(9, 5.4),
    "tree_golden": lambda: card_tree(31, 3.8, GOLD_LEAF, alpha=PETAL, clumps=10),
    "tree_orange": lambda: card_tree(32, 3.4, ORANGE_LEAF, alpha=PETAL, clumps=9),
    "tree_blossom": lambda: card_tree(33, 3.6, BLOSSOM, alpha=PETAL, clumps=10, bark=BARK_DARK),
    "tree_teal": lambda: card_tree(34, 4.0, TEAL_LEAF, alpha=EVERGREEN, clumps=10),
    "bush_a": lambda: bush(11, 0.7),
    "bush_b": lambda: bush_flowering(12, CLOTH_PINK, 0.6),
    "bush_golden": lambda: bush(35, 0.8, ((0.98, 0.94, 0.52), (0.86, 0.80, 0.32), (0.52, 0.56, 0.20)), PETAL),
    "bush_berries": lambda: bush_fruit(13),
    "flowers_pink": lambda: flowers(14, CLOTH_PINK),
    "flowers_white": lambda: flower_cecilia(15),
    "flowers_blue": lambda: flower_windwheel(16),
    "flowers_yellow": lambda: flower_dandelion(17),
    "flowers_red": lambda: flowers(18, (1.0, 0.32, 0.28)),
    "flowers_lavender": lambda: flower_lavender(36),
    "grass_tuft": lambda: grass_tuft(19),
    "reeds": lambda: reeds(20),
    "lily_pad_a": lambda: lily_pad(22),
    "lily_pad_b": lambda: lily_pad(23),
    "rock_a": lambda: rock(24, 0.55),
    "rock_b": lambda: rock(25, 0.35, STONE_DARK),
    "rock_c": lambda: rock(26, 0.85),
    "rock_big": lambda: rock_big(37),
    "cobble_a": lambda: cobble(27),
    "cobble_b": lambda: cobble(28),
    "stepping_stone": lambda: stepping_stone(29),
    "mushrooms": lambda: mushroom(30),
    "stump": stump,
    "log_pile": log_pile,
    # creatures
    "sheep": sheep,
    "cat": lambda: cat(),
    "cat_black": lambda: cat(CAT_DARK, WHITE),
    "koi": lambda: koi(),
    "koi_white": lambda: koi((0.98, 0.22, 0.18)),
    "duck": lambda: duck(),
    "duckling": lambda: duck(CLOTH_YELLOW, CLOTH_YELLOW, True),
    "chicken": chick,
    "bird": bird,
    "butterfly": butterfly,
    "crystalfly": crystalfly,
    "slime": lambda: slime(),
    "slime_blue": lambda: slime((0.42, 0.76, 1.0)),
    # lights & landmarks
    "lantern": lantern,
    "wall_lantern": wall_lantern,
    "paper_lantern": paper_lantern_post,
    "wind_shrine": wind_shrine,
    # structures & details
    "fence_post": fence_post,
    "fence_rail": fence_rail,
    "gate": gate,
    "bridge_plank": bridge_plank,
    "stair_step": stair_step,
    "window_frame": window_frame,
    "shutters": shutters,
    "flower_box": flower_box,
    "door": door,
    "trapdoor": trapdoor,
    "dormer": dormer,
    "chimney": chimney,
    "weathervane": weathervane,
    "banner": banner,
    # village props
    "well": well,
    "fountain": fountain,
    "market_stall": market_stall,
    "windmill": windmill,
    "signpost": signpost,
    "notice_board": notice_board,
    "flower_cart": flower_cart,
    "haystack": haystack,
    "hay_bale": hay_bale,
    "barrel": barrel,
    "crate": crate,
    "cart": cart,
    "bench": bench,
    "scarecrow": scarecrow,
    "cloud_a": lambda: cloud(40),
    "cloud_b": lambda: cloud(41),
    "windmill_sails": windmill_sails,
    # ancient ruins
    "ruin_arch": ruin_arch,
    "ruin_wall": ruin_wall,
    "ruin_pillar": ruin_pillar,
    "ruin_slab": ruin_slab,
    "rotunda": rotunda,
    # town square
    "cafe_table": cafe_table,
    "planter": planter,
    "fence_pillar": fence_pillar,
    "fence_ornate": fence_ornate,
    "gate_ornate": gate_ornate,
    # lakeside village
    "window_lattice": window_lattice,
    "door_wood": door_wood,
    "bridge_slab": bridge_slab,
    "bamboo_raft": bamboo_raft,
    "stone_lantern": stone_lantern2,
    "tea_terrace": tea_terrace,
    # backdrops
    "karst_a": lambda: karst(50, 30.0),
    "karst_b": lambda: karst(51, 22.0),
    "karst_c": lambda: karst(52, 38.0),
    "cliff": lambda: cliff(53),
}


def render_icon(path, size=512, transparent=False, ortho_scale=6.2):
    """Launcher icon: a floating island with a fantasy cottage, tower and tree."""
    reset_scene()
    scene = bpy.context.scene
    b = Builder()
    b.cyl(2.6, 1.6, 1.0, loc=(0, 0, -1.0), color=(0.62, 0.44, 0.34), seg=28, grad=((0.70, 0.50, 0.38), (0.45, 0.30, 0.26)))
    b.cyl(2.65, 2.65, 0.16, loc=(0, 0, -0.08), color=LEAF, seg=28, grad=(LEAF_TOP, LEAF))
    b.to_object("Island")
    h = Builder()
    h.box((1.7, 1.2, 0.5), loc=(-0.25, 0.2, 0.25), color=STONE_WARM)
    h.box((1.7, 1.2, 0.6), loc=(-0.25, 0.2, 0.8), color=PAPER)
    for x in (-1.08, -0.25, 0.58):
        h.box((0.08, 1.24, 0.62), loc=(x, 0.2, 0.8), color=WOOD_DARK)
    for s_ in (-1, 1):
        h.box((2.0, 0.9, 0.1), loc=(-0.25, 0.2 + s_ * 0.36, 1.38), rot=(-s_ * 0.85, 0, 0), color=TEAL)
    h.box((0.4, 0.05, 0.45), loc=(-0.45, -0.41, 0.8), color=(0.98, 0.9, 0.6))
    h.cyl(0.42, 0.36, 2.2, loc=(1.1, 0.6, 0), color=STONE_WARM, seg=16)
    h.cyl(0.55, 0.0, 1.0, loc=(1.1, 0.6, 2.2), color=ROOF_RED, seg=16)
    h.box((0.1, 0.1, 1.6), loc=(1.1, 0.12, 2.0), rot=(0, 0.6, 0), color=WOOD_DARK)
    h.box((0.1, 0.1, 1.6), loc=(1.1, 0.12, 2.0), rot=(0, -0.6, 0), color=WOOD_DARK)
    h.to_object("House")
    t = Builder()
    trunk(t, 1.0, 0.12, 0.07, lean=(0.05, 0.05), roots=False)
    canopy(t, (0.05, 0.05, 1.4), 0.8, 3, LEAF_TOP, LEAF, LEAF_DARK, squash=0.75, clumps=8, seed=3)
    t.to_object("Tree")
    for obj in bpy.context.scene.objects:
        if obj.name == "Tree":
            obj.location = (-1.5, 1.1, 0)
    s = Builder()
    s.ball(0.2, loc=(-1.4, -1.0, 0.25), color=WOOL, subdiv=2, scale=(1, 1.25, 0.9))
    s.ball(0.11, loc=(-1.4, -1.25, 0.32), color=FACE, subdiv=2)
    s.to_object("Sheep")
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.78, 0.98, 1.0)
    bg.inputs[1].default_value = 1.0
    scene.world = world
    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 3.2
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-40))
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = ortho_scale
    cam = bpy.data.objects.new("Cam", cam_data)
    cam.location = (7.5, -7.5, 6.0)
    cam.rotation_euler = (math.radians(58), 0, math.radians(45))
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.film_transparent = transparent
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("  rendered", path)


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    out_dir = os.path.abspath(args[0] if args else os.path.join(os.path.dirname(__file__), "..", "assets", "models"))
    os.makedirs(out_dir, exist_ok=True)
    only = set(args[1:]) if len(args) > 1 else None
    for name, build in ASSETS.items():
        if only and name not in only:
            continue
        reset_scene()
        _materials.clear()
        rng.seed(zlib.crc32(name.encode()))
        build()
        export(out_dir, name)
    if only is None or "icon" in only:
        icon_dir = os.path.join(out_dir, "..", "icons")
        os.makedirs(icon_dir, exist_ok=True)
        _materials.clear()
        render_icon(os.path.abspath(os.path.join(icon_dir, "icon_512.png")), 512)
        _materials.clear()
        render_icon(os.path.abspath(os.path.join(icon_dir, "icon_foreground_432.png")), 432, True, 9.0)


if __name__ == "__main__":
    main()
