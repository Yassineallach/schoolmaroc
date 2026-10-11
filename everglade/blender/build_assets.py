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
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.normal_update()
        self.bm.to_mesh(mesh)
        self.bm.free()
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
def tree_round(seed, height=3.4, tint=(LEAF_TOP, LEAF, LEAF_DARK)):
    rng.seed(seed)
    b = Builder()
    top = trunk(b, height * 0.55, 0.2, 0.12, lean=(rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15)))
    for i in range(3):
        a = rng.uniform(0, math.tau)
        b.cyl(0.07, 0.03, 0.9, loc=(top[0] * 0.6, top[1] * 0.6, height * 0.4), rot=(0.75 * math.cos(a), 0.75 * math.sin(a), 0), color=BARK, seg=5)
    canopy(b, (top[0], top[1], height * 0.72), height * 0.36, 3, *tint, clumps=7, seed=seed)
    b.to_object("Tree")





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



def bush(seed, size=0.7, tint=(LEAF_TOP, LEAF, LEAF_DARK)):
    rng.seed(seed)
    b = Builder()
    for i in range(5):
        a = i / 5 * math.tau + rng.uniform(-0.4, 0.4)
        d = size * 0.35
        b.ball(size * rng.uniform(0.45, 0.6), loc=(math.cos(a) * d, math.sin(a) * d, size * 0.42), color=tint[1], alpha=FOLIAGE,
               subdiv=2, scale=(1, 1, 0.82), wgrad=(tint[0], tint[2], 0.0, size * 1.1))
    b.ball(size * 0.5, loc=(0, 0, size * 0.7), color=tint[0], alpha=FOLIAGE, subdiv=2, scale=(1, 1, 0.8), wgrad=(tint[0], tint[2], 0.0, size * 1.1))
    b.to_object("Bush")


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


def grass_tuft(seed):
    rng.seed(seed)
    b = Builder()
    for i in range(11):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 0.12)
        h = rng.uniform(0.2, 0.42)
        lean = rng.uniform(0.15, 0.5)
        b.cyl(0.028, 0.0, h, loc=(math.cos(a) * d, math.sin(a) * d, 0), rot=(lean * math.cos(a + 1.57), lean * math.sin(a + 1.57), 0),
              color=GRASS, alpha=EVERGREEN, seg=3, smooth=False, grad=(GRASS_TIP, GRASS_ROOT))
    b.to_object("Grass")


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


def tree_grand(seed, height=5.2):
    """Grand old oak with a huge layered canopy (the village's landmark tree)."""
    rng.seed(seed)
    b = Builder()
    top = trunk(b, height * 0.5, 0.42, 0.24, lean=(0.08, -0.05), color=BARK, segments=4)
    for i in range(5):
        a = i / 5 * math.tau + rng.uniform(-0.3, 0.3)
        b.cyl(0.14, 0.05, height * 0.38, loc=(top[0] * 0.8, top[1] * 0.8, height * 0.42), rot=(0.95 * math.cos(a), 0.95 * math.sin(a), 0), color=BARK, seg=6)
    canopy(b, (top[0], top[1], height * 0.72), height * 0.42, 4, LEAF_TOP, LEAF, LEAF_DARK, squash=0.72, clumps=10, seed=seed)
    b.to_object("Tree")


def tree_fir(seed, height=4.6):
    """Tall painted fir: soft stacked boughs, bright tips, deep shadows."""
    rng.seed(seed)
    b = Builder()
    b.cyl(0.17, 0.08, height * 0.35, color=BARK, seg=7)
    tiers = 6
    for i in range(tiers):
        t = i / tiers
        r = (1.0 - t * 0.8) * height * 0.24
        z = height * (0.16 + t * 0.68)
        b.cyl(r, r * 0.25, height * 0.2, loc=(0, 0, z), color=PINE, alpha=EVERGREEN, seg=10, jitter=0.02,
              wgrad=(PINE_TOP, PINE_DARK, height * 0.15, height))
        b.ball(r * 0.5, loc=(0, 0, z + height * 0.04), color=PINE, alpha=EVERGREEN, subdiv=1, scale=(1, 1, 0.5),
               wgrad=(PINE_TOP, PINE_DARK, height * 0.15, height))
    b.cyl(0.08, 0.0, height * 0.16, loc=(0, 0, height * 0.86), color=PINE_TOP, alpha=EVERGREEN, seg=8)
    b.to_object("Tree")


def tree_birch(seed, height=3.6):
    rng.seed(seed)
    b = Builder()
    trunk(b, height * 0.75, 0.1, 0.06, lean=(rng.uniform(-0.1, 0.1), 0.05), color=(0.94, 0.93, 0.90), segments=3, roots=False)
    for z in (0.5, 1.0, 1.6, 2.1):
        b.cyl(0.105, 0.1, 0.05, loc=(0, 0, z), color=(0.25, 0.24, 0.26), seg=6)
    canopy(b, (0.1, 0, height * 0.78), height * 0.26, 3, (0.80, 0.94, 0.46), (0.56, 0.82, 0.36), (0.28, 0.56, 0.30), squash=0.9, clumps=6, seed=seed)
    b.to_object("Tree")


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
    """Village windmill: stone tower, teal cap and slowly turning sails ("Sails")."""
    root = empty("Windmill")
    b = Builder()
    g = (STONE_LIGHT, STONE_DARK)
    b.cyl(1.4, 1.0, 4.6, color=STONE_WARM, seg=16, grad=g)
    b.cyl(1.5, 1.5, 0.3, color=STONE_DARK, seg=16)
    for z in (1.6, 3.2):
        b.torus(1.25 - z * 0.08, 0.06, loc=(0, 0, z), color=WOOD_DARK, seg=20, ring=4)
    b.cyl(1.25, 0.1, 1.5, loc=(0, 0, 4.6), color=TEAL, seg=16, grad=(TEAL_LIGHT, TEAL_DARK))
    b.ball(0.12, loc=(0, 0, 6.15), color=GOLD, subdiv=1)
    b.box((0.7, 0.1, 1.1), loc=(0, -1.25, 0.6), color=WOOD)
    b.box((0.45, 0.08, 0.6), loc=(0, -1.12, 2.6), color=(0.98, 0.9, 0.66))
    b.cyl(0.18, 0.18, 0.9, loc=(0, -0.9, 4.8), rot=(math.pi / 2, 0, 0), color=WOOD_DARK, seg=8)
    b.to_object("Tower", root)
    p = empty("Sails", (0, -1.85, 4.8), root)
    s = Builder()
    s.ball(0.25, color=WOOD_DARK, subdiv=1)
    for i in range(4):
        a = i / 4 * math.tau
        ca, sa = math.cos(a), math.sin(a)
        s.box((0.1, 0.08, 3.2), loc=(ca * 1.6, 0, sa * 1.6), rot=(0, -a + math.pi / 2, 0), color=WOOD_DARK)
        for k in range(4):
            r = 0.9 + k * 0.62
            off = 0.32
            s.box((0.55, 0.03, 0.55), loc=(ca * r - sa * off, -0.04, sa * r + ca * off), rot=(0, -a + math.pi / 2, 0),
                  color=WHITE if k % 2 == 0 else (0.94, 0.92, 0.86), alpha=PETAL)
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


ASSETS = {
    # trees: names kept so saved glades and code keep working
    "tree_round_a": lambda: tree_round(1, 3.4),
    "tree_round_b": lambda: tree_grand(2, 5.2),
    "tree_round_c": lambda: tree_round(3, 2.8, ((0.72, 0.92, 0.42), (0.48, 0.80, 0.34), (0.22, 0.52, 0.30))),
    "tree_pine_a": lambda: tree_fir(4, 4.8),
    "tree_pine_b": lambda: tree_fir(5, 3.6),
    "tree_birch": lambda: tree_birch(6),
    "tree_cedar": lambda: tree_cedar(9, 5.4),
    "bush_a": lambda: bush(11, 0.7),
    "bush_b": lambda: bush_flowering(12, CLOTH_PINK, 0.6),
    "bush_berries": lambda: bush_fruit(13),
    "flowers_pink": lambda: flowers(14, CLOTH_PINK),
    "flowers_white": lambda: flower_cecilia(15),
    "flowers_blue": lambda: flower_windwheel(16),
    "flowers_yellow": lambda: flower_dandelion(17),
    "flowers_red": lambda: flowers(18, (1.0, 0.32, 0.28)),
    "grass_tuft": lambda: grass_tuft(19),
    "reeds": lambda: reeds(20),
    "lily_pad_a": lambda: lily_pad(22),
    "lily_pad_b": lambda: lily_pad(23),
    "rock_a": lambda: rock(24, 0.55),
    "rock_b": lambda: rock(25, 0.35, STONE_DARK),
    "rock_c": lambda: rock(26, 0.85),
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
