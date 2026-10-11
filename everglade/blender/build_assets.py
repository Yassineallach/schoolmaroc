"""
Everglade - Blender asset builder.

Generates every hand-made-looking prop of the game as low-poly, vertex-coloured
GLB files that Godot imports directly. Run with Blender 4.2+ / 5.x:

    blender --background --python blender/build_assets.py -- assets/models
or, with the `bpy` wheel from PyPI:
    python blender/build_assets.py assets/models

Conventions shared with the Godot side (scripts/core/model_lib.gd):
  * 1 Blender unit = 1 metre, origin on the ground at the prop's footprint centre.
  * Creatures face -Y in Blender, which becomes +Z (glTF/Godot model front).
  * Vertex colour RGB = albedo. Vertex colour ALPHA encodes a material channel:
        1.0  solid (wood, stone, cloth)
        0.0  foliage (wind sway + season tint in the Godot shader)
        0.25 evergreen (wind sway, no season tint: pines, grass)
        0.5  petals (wind sway, no season tint)
  * Objects named "Glow*" are lamp glass and get the emissive night material.
  * Animated parts are separate child objects (legs, wings, flags, heads...).
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
# Palette (soft, warm storybook tones)
# ---------------------------------------------------------------------------
STONE = (0.72, 0.70, 0.66)
STONE_DARK = (0.52, 0.50, 0.48)
STONE_WARM = (0.80, 0.74, 0.64)
WOOD = (0.50, 0.34, 0.22)
WOOD_DARK = (0.34, 0.23, 0.15)
WOOD_LIGHT = (0.66, 0.50, 0.33)
BARK = (0.38, 0.27, 0.19)
LEAF = (0.36, 0.56, 0.24)
LEAF_DARK = (0.24, 0.42, 0.20)
LEAF_LIGHT = (0.50, 0.66, 0.30)
PINE = (0.17, 0.36, 0.25)
GRASS = (0.45, 0.62, 0.28)
WOOL = (0.95, 0.93, 0.88)
SKIN_DARK = (0.18, 0.15, 0.14)
HAY = (0.88, 0.74, 0.40)
IRON = (0.22, 0.22, 0.24)
GLASS = (1.00, 0.82, 0.48)
ROOF_RED = (0.70, 0.33, 0.25)
ROOF_BLUE = (0.33, 0.45, 0.62)
CLOTH_RED = (0.78, 0.25, 0.22)
CLOTH_BLUE = (0.25, 0.42, 0.72)
CLOTH_YELLOW = (0.95, 0.78, 0.30)
WHITE = (0.97, 0.96, 0.93)
DUCK_GREEN = (0.13, 0.42, 0.26)
BEAK = (0.98, 0.62, 0.18)
WATER = (0.35, 0.58, 0.70)

SOLID, FOLIAGE, EVERGREEN, PETAL = 1.0, 0.0, 0.25, 0.5

rng = random.Random(1987)


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
    """Accumulates coloured primitives into a single bmesh."""

    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.color.new("Color")

    # -- internal ---------------------------------------------------------
    def _finish(self, verts, color, alpha, matrix, jitter=0.0, smooth=True):
        verts = [v for v in verts if isinstance(v, bmesh.types.BMVert)]
        if jitter > 0.0:
            for v in verts:
                n = v.co.normalized() if v.co.length > 1e-5 else Vector((0, 0, 1))
                v.co += n * rng.uniform(-jitter, jitter)
        bmesh.ops.transform(self.bm, matrix=matrix, verts=verts)
        faces = {f for v in verts for f in v.link_faces}
        r, g, b = color
        for f in faces:
            f.smooth = smooth
            for loop in f.loops:
                k = rng.uniform(0.96, 1.04)
                loop[self.col] = (min(r * k, 1), min(g * k, 1), min(b * k, 1), alpha)
        return verts

    # -- primitives -------------------------------------------------------
    def box(self, size, loc=(0, 0, 0), color=STONE, alpha=SOLID, rot=(0, 0, 0), smooth=False, jitter=0.0):
        ret = bmesh.ops.create_cube(self.bm, size=1.0)
        m = trs(loc, rot, size)
        return self._finish(ret["verts"], color, alpha, m, jitter, smooth)

    def cyl(self, r1, r2, depth, loc=(0, 0, 0), color=WOOD, alpha=SOLID, seg=8, rot=(0, 0, 0), smooth=True, jitter=0.0):
        ret = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg,
                                    radius1=r1, radius2=r2, depth=depth)
        # cone is centred on origin; shift so it sits on its base
        bmesh.ops.translate(self.bm, vec=(0, 0, depth * 0.5), verts=ret["verts"])
        m = trs(loc, rot, (1, 1, 1))
        return self._finish(ret["verts"], color, alpha, m, jitter, smooth)

    def ball(self, radius, loc=(0, 0, 0), color=LEAF, alpha=SOLID, subdiv=2, scale=(1, 1, 1), rot=(0, 0, 0), jitter=0.0, smooth=True):
        ret = bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv, radius=radius)
        if jitter:
            for v in ret["verts"]:
                v.co *= 1.0 + rng.uniform(-jitter, jitter)
        m = trs(loc, rot, scale)
        return self._finish(ret["verts"], color, alpha, m, 0.0, smooth)

    def to_object(self, name, parent=None, mat_name="VertexColor", emissive=False):
        mesh = bpy.data.meshes.new(name)
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
# Asset definitions. Each function populates an empty scene.
# ---------------------------------------------------------------------------
def tree_round(seed, height=3.2, blobs=5, tint=LEAF):
    rng.seed(seed)
    b = Builder()
    trunk_h = height * 0.55
    b.cyl(0.20, 0.12, trunk_h, color=BARK, seg=7, jitter=0.015)
    # a couple of branches
    for i in range(2):
        a = rng.uniform(0, math.tau)
        b.cyl(0.07, 0.04, 0.9, loc=(0, 0, trunk_h * 0.6), rot=(0.7, 0, a), color=BARK, seg=5)
    crown_z = trunk_h + height * 0.18
    b.ball(height * 0.30, loc=(0, 0, crown_z), color=tint, alpha=FOLIAGE, subdiv=2, jitter=0.10)
    for i in range(blobs):
        a = i / blobs * math.tau + rng.uniform(-0.3, 0.3)
        d = height * rng.uniform(0.16, 0.24)
        z = crown_z + rng.uniform(-0.25, 0.35) * height * 0.3
        shade = LEAF_DARK if i % 2 else LEAF_LIGHT
        mix = tuple(t * 0.5 + s * 0.5 for t, s in zip(tint, shade))
        b.ball(height * rng.uniform(0.17, 0.23), loc=(math.cos(a) * d, math.sin(a) * d, z),
               color=mix, alpha=FOLIAGE, subdiv=2, jitter=0.12)
    b.to_object("Tree")


def tree_pine(seed, height=4.2):
    rng.seed(seed)
    b = Builder()
    b.cyl(0.16, 0.10, height * 0.3, color=BARK, seg=6)
    tiers = 4
    for i in range(tiers):
        t = i / tiers
        r = (1.0 - t * 0.7) * height * 0.24
        z = height * (0.18 + t * 0.62)
        col = PINE if i % 2 == 0 else tuple(c * 1.15 for c in PINE)
        b.cyl(r, r * 0.12, height * 0.36, loc=(0, 0, z), color=col, alpha=EVERGREEN, seg=9, jitter=0.03)
    b.to_object("Tree")


def tree_birch(seed):
    rng.seed(seed)
    b = Builder()
    b.cyl(0.11, 0.07, 3.0, color=(0.92, 0.90, 0.86), seg=6)
    for z in (0.5, 1.2, 1.9, 2.5):  # dark bark rings
        b.cyl(0.115, 0.105, 0.06, loc=(0, 0, z), color=(0.2, 0.2, 0.2), seg=6)
    for i in range(6):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0.2, 0.55)
        b.ball(rng.uniform(0.45, 0.6), loc=(math.cos(a) * d, math.sin(a) * d, rng.uniform(2.4, 3.4)),
               color=(0.55, 0.70, 0.30), alpha=FOLIAGE, subdiv=1, jitter=0.12, scale=(1, 1, 1.2))
    b.to_object("Tree")


def bush(seed, size=0.7, tint=LEAF):
    rng.seed(seed)
    b = Builder()
    for i in range(4):
        a = i / 4 * math.tau + rng.uniform(-0.4, 0.4)
        d = size * 0.35
        b.ball(size * rng.uniform(0.45, 0.6), loc=(math.cos(a) * d, math.sin(a) * d, size * 0.4),
               color=tint, alpha=FOLIAGE, subdiv=2, jitter=0.12, scale=(1, 1, 0.8))
    b.to_object("Bush")


def bush_berries(seed):
    bush(seed, 0.75, LEAF_DARK)
    rng.seed(seed + 9)
    b = Builder()
    for i in range(14):
        a = rng.uniform(0, math.tau)
        z = rng.uniform(0.25, 0.75)
        r = 0.55 + rng.uniform(-0.05, 0.05)
        b.ball(0.05, loc=(math.cos(a) * r * 0.85, math.sin(a) * r * 0.85, z), color=CLOTH_RED, alpha=PETAL, subdiv=1)
    b.to_object("Berries")


def flowers(seed, petal):
    rng.seed(seed)
    b = Builder()
    for i in range(7):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0.0, 0.22)
        x, y = math.cos(a) * d, math.sin(a) * d
        h = rng.uniform(0.18, 0.34)
        b.cyl(0.012, 0.01, h, loc=(x, y, 0), color=GRASS, alpha=FOLIAGE, seg=4)
        for p in range(5):
            pa = p / 5 * math.tau
            b.ball(0.035, loc=(x + math.cos(pa) * 0.035, y + math.sin(pa) * 0.035, h),
                   color=petal, alpha=PETAL, subdiv=1, scale=(1, 1, 0.45))
        b.ball(0.025, loc=(x, y, h + 0.01), color=CLOTH_YELLOW, alpha=PETAL, subdiv=1)
    for i in range(6):  # leaves
        a = rng.uniform(0, math.tau)
        b.ball(0.07, loc=(math.cos(a) * 0.1, math.sin(a) * 0.1, 0.04), color=LEAF, alpha=FOLIAGE,
               subdiv=1, scale=(1.4, 0.5, 0.3), rot=(0, 0, a))
    b.to_object("Flowers")


def grass_tuft(seed):
    rng.seed(seed)
    b = Builder()
    for i in range(9):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 0.12)
        h = rng.uniform(0.18, 0.35)
        lean = rng.uniform(0.1, 0.45)
        b.cyl(0.025, 0.0, h, loc=(math.cos(a) * d, math.sin(a) * d, 0),
              rot=(lean * math.cos(a + 1.57), lean * math.sin(a + 1.57), 0),
              color=tuple(c * rng.uniform(0.85, 1.15) for c in GRASS), alpha=EVERGREEN, seg=3, smooth=False)
    b.to_object("Grass")


def reeds(seed):
    rng.seed(seed)
    b = Builder()
    for i in range(7):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 0.2)
        h = rng.uniform(0.6, 1.0)
        x, y = math.cos(a) * d, math.sin(a) * d
        b.cyl(0.015, 0.008, h, loc=(x, y, 0), color=(0.42, 0.55, 0.27), alpha=EVERGREEN, seg=4)
        if i % 2 == 0:
            b.cyl(0.03, 0.03, 0.14, loc=(x, y, h - 0.05), color=(0.42, 0.28, 0.17), alpha=FOLIAGE, seg=6)
    b.to_object("Reeds")


def lily_pad(seed):
    rng.seed(seed)
    b = Builder()
    b.cyl(0.25, 0.25, 0.02, color=(0.30, 0.55, 0.28), seg=10, alpha=SOLID)
    if seed % 2 == 0:
        for p in range(6):
            pa = p / 6 * math.tau
            b.ball(0.05, loc=(math.cos(pa) * 0.05, math.sin(pa) * 0.05, 0.05), color=(0.98, 0.78, 0.86), subdiv=1, scale=(1, 1, 0.6))
    b.to_object("Lily")


def rock(seed, size=0.6, color=STONE):
    rng.seed(seed)
    b = Builder()
    b.ball(size, loc=(0, 0, size * 0.35), color=color, subdiv=1, jitter=0.22,
           scale=(1.0, rng.uniform(0.7, 1.0), rng.uniform(0.55, 0.8)), smooth=False)
    # moss on top
    b.ball(size * 0.55, loc=(size * 0.1, 0, size * 0.75), color=(0.42, 0.56, 0.26), alpha=FOLIAGE, subdiv=1,
           jitter=0.2, scale=(1.2, 1.0, 0.35), smooth=False)
    b.to_object("Rock")


def cobble(seed):
    rng.seed(seed)
    b = Builder()
    b.ball(0.16, loc=(0, 0, 0.0), color=STONE_WARM, subdiv=1, jitter=0.15, scale=(1.0, 0.8, 0.35), smooth=False)
    b.to_object("Cobble")


def stepping_stone(seed):
    rng.seed(seed)
    b = Builder()
    b.cyl(0.38, 0.34, 0.25, loc=(0, 0, -0.15), color=STONE, seg=9, jitter=0.04, smooth=False)
    b.to_object("Step")


def sheep():
    root = empty("Sheep")
    body = Builder()
    for i in range(7):  # fluffy wool from overlapping balls
        a = i / 7 * math.tau
        body.ball(0.22, loc=(math.cos(a) * 0.14, math.sin(a) * 0.24, 0.62 + rng.uniform(-0.03, 0.05)),
                  color=WOOL, subdiv=2, jitter=0.06)
    body.ball(0.30, loc=(0, 0, 0.66), color=WOOL, subdiv=2, scale=(0.95, 1.35, 0.9), jitter=0.05)
    body.ball(0.17, loc=(0, -0.05, 0.86), color=WOOL, subdiv=2, jitter=0.08)
    body.ball(0.08, loc=(0, 0.42, 0.7), color=WOOL, subdiv=1)  # tail
    body.to_object("Body", root)
    head_pivot = empty("Head", (0, -0.40, 0.78), root)
    head = Builder()
    head.ball(0.14, loc=(0, -0.10, 0.0), color=SKIN_DARK, subdiv=2, scale=(0.85, 1.25, 0.95))
    head.ball(0.13, loc=(0, -0.02, 0.09), color=WOOL, subdiv=2, scale=(1.1, 0.9, 0.6), jitter=0.08)  # wool cap
    for s in (-1, 1):
        head.ball(0.07, loc=(s * 0.15, -0.02, 0.02), color=SKIN_DARK, subdiv=1, scale=(1.4, 0.5, 0.4), rot=(0, s * 0.4, 0))
        head.ball(0.022, loc=(s * 0.075, -0.19, 0.05), color=(0.02, 0.02, 0.02), subdiv=1)
    head.to_object("HeadMesh", head_pivot)
    for name, x, y in (("LegFL", -0.12, -0.22), ("LegFR", 0.12, -0.22), ("LegBL", -0.12, 0.24), ("LegBR", 0.12, 0.24)):
        pivot = empty(name, (x, y, 0.45), root)
        leg = Builder()
        leg.cyl(0.045, 0.04, 0.45, loc=(0, 0, -0.45), color=SKIN_DARK, seg=6)
        leg.to_object(name + "Mesh", pivot)


def duck(color_body=WHITE, color_head=DUCK_GREEN):
    root = empty("Duck")
    b = Builder()
    b.ball(0.16, loc=(0, 0.02, 0.10), color=color_body, subdiv=2, scale=(0.8, 1.3, 0.7))
    b.ball(0.07, loc=(0, 0.20, 0.17), color=color_body, subdiv=1, scale=(0.7, 1.0, 0.8), rot=(0.6, 0, 0))  # tail
    for s in (-1, 1):
        b.ball(0.09, loc=(s * 0.11, 0.05, 0.13), color=tuple(c * 0.85 for c in color_body), subdiv=1, scale=(0.4, 1.3, 0.6))
    b.to_object("Body", root)
    head_pivot = empty("Head", (0, -0.15, 0.20), root)
    h = Builder()
    h.cyl(0.05, 0.045, 0.12, loc=(0, 0, 0), color=color_head, seg=6)
    h.ball(0.075, loc=(0, -0.02, 0.15), color=color_head, subdiv=2)
    h.ball(0.04, loc=(0, -0.10, 0.13), color=BEAK, subdiv=1, scale=(0.9, 1.5, 0.45))
    for s in (-1, 1):
        h.ball(0.014, loc=(s * 0.05, -0.06, 0.18), color=(0.02, 0.02, 0.02), subdiv=1)
    h.to_object("HeadMesh", head_pivot)


def chick():
    root = empty("Chicken")
    b = Builder()
    b.ball(0.16, loc=(0, 0.03, 0.30), color=WHITE, subdiv=2, scale=(0.85, 1.15, 0.95))
    b.ball(0.10, loc=(0, 0.17, 0.42), color=WHITE, subdiv=1, scale=(0.5, 0.8, 1.2), rot=(-0.5, 0, 0))
    b.to_object("Body", root)
    hp = empty("Head", (0, -0.14, 0.44), root)
    h = Builder()
    h.ball(0.08, color=WHITE, subdiv=2)
    h.ball(0.03, loc=(0, -0.08, -0.01), color=BEAK, subdiv=1, scale=(0.8, 1.3, 0.6))
    h.ball(0.035, loc=(0, -0.01, 0.08), color=CLOTH_RED, subdiv=1, scale=(0.4, 1.2, 0.8))
    h.ball(0.03, loc=(0, -0.06, -0.06), color=CLOTH_RED, subdiv=1, scale=(0.5, 0.6, 1.0))
    for s in (-1, 1):
        h.ball(0.012, loc=(s * 0.06, -0.04, 0.02), color=(0.02, 0.02, 0.02), subdiv=1)
    h.to_object("HeadMesh", hp)
    for name, x in (("LegFL", -0.06), ("LegFR", 0.06)):
        p = empty(name, (x, 0.02, 0.17), root)
        l = Builder()
        l.cyl(0.015, 0.015, 0.17, loc=(0, 0, -0.17), color=BEAK, seg=4)
        l.to_object(name + "Mesh", p)


def bird():
    root = empty("Bird")
    b = Builder()
    b.ball(0.07, loc=(0, 0, 0), color=(0.35, 0.30, 0.28), subdiv=1, scale=(0.8, 1.5, 0.8))
    b.ball(0.05, loc=(0, -0.09, 0.03), color=(0.35, 0.30, 0.28), subdiv=1)
    b.ball(0.02, loc=(0, -0.14, 0.03), color=BEAK, subdiv=1, scale=(0.6, 1.4, 0.6))
    b.box((0.06, 0.12, 0.01), loc=(0, 0.13, 0.01), color=(0.30, 0.25, 0.23))
    b.to_object("Body", root)
    for name, s in (("WingL", -1), ("WingR", 1)):
        p = empty(name, (s * 0.04, 0, 0.02), root)
        w = Builder()
        w.box((0.20, 0.09, 0.012), loc=(s * 0.10, 0, 0), color=(0.30, 0.26, 0.24))
        w.to_object(name + "Mesh", p)


def butterfly():
    root = empty("Butterfly")
    b = Builder()
    b.cyl(0.006, 0.006, 0.05, rot=(math.pi / 2, 0, 0), loc=(0, 0.025, 0), color=SKIN_DARK, seg=4)
    b.to_object("Body", root)
    for name, s in (("WingL", -1), ("WingR", 1)):
        p = empty(name, (0, 0, 0), root)
        w = Builder()
        w.ball(0.03, loc=(s * 0.03, -0.01, 0), color=CLOTH_YELLOW, subdiv=1, scale=(1, 0.9, 0.1))
        w.ball(0.022, loc=(s * 0.025, 0.02, 0), color=(0.98, 0.6, 0.2), subdiv=1, scale=(1, 0.9, 0.1))
        w.to_object(name + "Mesh", p)


def lantern():
    b = Builder()
    b.cyl(0.07, 0.06, 1.7, color=WOOD_DARK, seg=6)
    b.box((0.10, 0.45, 0.06), loc=(0, -0.18, 1.62), color=WOOD_DARK)
    b.cyl(0.015, 0.015, 0.12, loc=(0, -0.36, 1.48), color=IRON, seg=4)
    b.box((0.18, 0.18, 0.04), loc=(0, -0.36, 1.30), color=IRON)
    b.cyl(0.13, 0.02, 0.10, loc=(0, -0.36, 1.46), color=IRON, seg=4, rot=(0, 0, math.pi / 4), smooth=False)
    b.box((0.18, 0.18, 0.03), loc=(0, -0.36, 1.13), color=IRON)
    b.to_object("Lantern")
    g = Builder()
    g.box((0.14, 0.14, 0.18), loc=(0, -0.36, 1.22), color=GLASS)
    g.to_object("Glow", mat_name="Glow", emissive=True)


def wall_lantern():
    b = Builder()
    b.box((0.06, 0.18, 0.06), loc=(0, 0.06, 0.25), color=IRON)
    b.box((0.16, 0.16, 0.03), loc=(0, 0.18, 0.15), color=IRON)
    b.cyl(0.12, 0.02, 0.09, loc=(0, 0.18, 0.31), color=IRON, seg=4, rot=(0, 0, math.pi / 4), smooth=False)
    b.box((0.16, 0.16, 0.02), loc=(0, 0.18, -0.03), color=IRON)
    b.to_object("WallLantern")
    g = Builder()
    g.box((0.12, 0.12, 0.16), loc=(0, 0.18, 0.06), color=GLASS)
    g.to_object("Glow", mat_name="Glow", emissive=True)


def fence_post():
    b = Builder()
    b.box((0.12, 0.12, 1.0), loc=(0, 0, 0.5), color=WOOD, jitter=0.01)
    b.cyl(0.085, 0.0, 0.08, loc=(0, 0, 1.0), color=WOOD, seg=4, rot=(0, 0, math.pi / 4), smooth=False)
    b.to_object("FencePost")


def fence_rail():
    # 1 m long along +X, starting at the origin; Godot stretches it per segment
    b = Builder()
    b.box((1.0, 0.05, 0.09), loc=(0.5, 0, 0.75), color=WOOD_LIGHT, jitter=0.004)
    b.box((1.0, 0.05, 0.09), loc=(0.5, 0, 0.38), color=WOOD_LIGHT, jitter=0.004)
    b.to_object("FenceRail")


def gate():
    root = empty("Gate")
    for name, s in (("LeafL", -1), ("LeafR", 1)):
        pivot = empty(name, (s * 0.5, 0, 0), root)
        b = Builder()
        for i in range(4):
            b.box((0.09, 0.04, 0.85), loc=(-s * (0.07 + i * 0.12), 0, 0.5), color=WOOD_LIGHT)
        b.box((0.48, 0.05, 0.08), loc=(-s * 0.25, 0.02, 0.75), color=WOOD)
        b.box((0.48, 0.05, 0.08), loc=(-s * 0.25, 0.02, 0.30), color=WOOD)
        b.box((0.55, 0.05, 0.07), loc=(-s * 0.25, 0.03, 0.52), rot=(0, s * 0.75, 0), color=WOOD)
        b.to_object(name + "Mesh", pivot)


def well():
    b = Builder()
    seg = 14
    for ring in range(4):
        z = ring * 0.18
        for i in range(seg):
            a = (i + 0.5 * (ring % 2)) / seg * math.tau
            b.box((0.26, 0.18, 0.17), loc=(math.cos(a) * 0.62, math.sin(a) * 0.62, z + 0.09), rot=(0, 0, a),
                  color=tuple(c * rng.uniform(0.9, 1.08) for c in STONE), jitter=0.01)
    b.cyl(0.62, 0.62, 0.06, loc=(0, 0, 0.71), color=STONE_DARK, seg=seg)
    for s in (-1, 1):
        b.box((0.10, 0.10, 1.55), loc=(s * 0.66, 0, 0.78), color=WOOD)
    b.cyl(0.05, 0.05, 1.4, loc=(-0.7, 0, 1.30), rot=(0, math.pi / 2, 0), color=WOOD_DARK, seg=6)
    b.cyl(0.006, 0.006, 0.55, loc=(0, 0, 0.75), color=(0.7, 0.6, 0.4), seg=3)
    b.cyl(0.10, 0.12, 0.16, loc=(0, 0, 0.62), color=WOOD_LIGHT, seg=8)
    # little gable roof
    for s in (-1, 1):
        b.box((1.6, 0.62, 0.05), loc=(0, s * 0.27, 1.73), rot=(-s * 0.62, 0, 0), color=ROOF_RED)
    b.box((1.62, 0.06, 0.06), loc=(0, 0, 1.92), color=WOOD_DARK)
    b.to_object("Well")
    w = Builder()
    w.cyl(0.56, 0.56, 0.02, loc=(0, 0, 0.45), color=WATER, seg=seg)
    w.to_object("WellWater")


def haystack():
    b = Builder()
    b.cyl(0.65, 0.45, 0.7, color=HAY, seg=12, jitter=0.03)
    b.ball(0.48, loc=(0, 0, 0.7), color=HAY, subdiv=2, jitter=0.05, scale=(1, 1, 0.9))
    b.cyl(0.03, 0.03, 0.5, loc=(0, 0, 1.0), color=WOOD_DARK, seg=4, rot=(0.2, 0, 0))
    b.to_object("Haystack")


def hay_bale():
    b = Builder()
    b.box((0.9, 0.5, 0.45), loc=(0, 0, 0.225), color=HAY, jitter=0.01)
    for x in (-0.25, 0.25):
        b.box((0.03, 0.52, 0.47), loc=(x, 0, 0.225), color=(0.66, 0.52, 0.25))
    b.to_object("HayBale")


def barrel():
    b = Builder()
    b.cyl(0.26, 0.30, 0.38, color=WOOD, seg=10)
    b.cyl(0.30, 0.26, 0.38, loc=(0, 0, 0.38), color=WOOD, seg=10)
    for z in (0.08, 0.38, 0.68):
        b.cyl(0.31 if z == 0.38 else 0.285, 0.31 if z == 0.38 else 0.285, 0.04, loc=(0, 0, z), color=IRON, seg=10)
    b.cyl(0.25, 0.25, 0.02, loc=(0, 0, 0.75), color=WOOD_LIGHT, seg=10)
    b.to_object("Barrel")


def crate():
    b = Builder()
    b.box((0.6, 0.6, 0.6), loc=(0, 0, 0.3), color=WOOD_LIGHT)
    for s in (-1, 1):
        b.box((0.62, 0.62, 0.07), loc=(0, 0, 0.3 + s * 0.26), color=WOOD)
    b.box((0.62, 0.04, 0.07), loc=(0, -0.3, 0.3), rot=(0, 0.75, 0), color=WOOD)
    b.to_object("Crate")


def cart():
    root = empty("Cart")
    b = Builder()
    b.box((1.0, 1.5, 0.1), loc=(0, 0, 0.55), color=WOOD_LIGHT)
    for s in (-1, 1):
        b.box((0.06, 1.5, 0.35), loc=(s * 0.5, 0, 0.75), color=WOOD)
        b.box((1.0, 0.06, 0.35), loc=(0, s * 0.75, 0.75), color=WOOD)
        b.box((0.06, 1.2, 0.06), loc=(s * 0.25, -1.3, 0.5), color=WOOD_DARK, rot=(0.12, 0, 0))
    b.cyl(0.04, 0.04, 1.2, loc=(-0.6, 0, 0.4), rot=(0, math.pi / 2, 0), color=IRON, seg=5)
    b.ball(0.3, loc=(0, 0.2, 0.85), color=HAY, subdiv=1, jitter=0.1, scale=(1.3, 1.6, 0.6))
    b.to_object("Body", root)
    for name, s in (("WheelL", -1), ("WheelR", 1)):
        p = empty(name, (s * 0.58, 0, 0.4), root)
        w = Builder()
        w.cyl(0.4, 0.4, 0.08, loc=(-0.04, 0, 0), rot=(0, math.pi / 2, 0), color=WOOD, seg=12)
        w.cyl(0.09, 0.09, 0.12, loc=(-0.06, 0, 0), rot=(0, math.pi / 2, 0), color=IRON, seg=8)
        w.to_object(name + "Mesh", p)


def bench():
    b = Builder()
    b.box((1.4, 0.4, 0.07), loc=(0, 0, 0.45), color=WOOD_LIGHT)
    b.box((1.4, 0.06, 0.25), loc=(0, 0.2, 0.75), rot=(-0.15, 0, 0), color=WOOD_LIGHT)
    for x in (-0.6, 0.6):
        b.box((0.08, 0.38, 0.45), loc=(x, 0, 0.22), color=WOOD)
        b.box((0.06, 0.06, 0.55), loc=(x, 0.2, 0.62), color=WOOD)
    b.to_object("Bench")


def banner():
    root = empty("Banner")
    b = Builder()
    b.cyl(0.04, 0.03, 3.2, color=WOOD_DARK, seg=6)
    b.ball(0.07, loc=(0, 0, 3.25), color=CLOTH_YELLOW, subdiv=1)
    b.to_object("Pole", root)
    p = empty("Flag", (0.04, 0, 3.05), root)
    f = Builder()
    # flag subdivided along X so the Godot shader can wave it
    for i in range(6):
        f.box((0.16, 0.015, 0.55), loc=(0.08 + i * 0.16, 0, -0.30), color=CLOTH_RED if i < 5 else CLOTH_YELLOW, alpha=PETAL)
    f.to_object("FlagMesh", p)


def chimney():
    b = Builder()
    for z in range(6):
        for i, (x, y) in enumerate(((0, -0.22), (0.22, 0), (0, 0.22), (-0.22, 0))):
            b.box((0.46 if y else 0.04, 0.04 if y else 0.46, 0.19), loc=(x, y, z * 0.2 + 0.1),
                  color=tuple(c * rng.uniform(0.9, 1.08) for c in STONE_WARM))
    b.box((0.44, 0.44, 1.2), loc=(0, 0, 0.6), color=STONE_WARM)
    b.box((0.56, 0.56, 0.1), loc=(0, 0, 1.22), color=STONE_DARK)
    b.cyl(0.09, 0.08, 0.22, loc=(0.08, 0.05, 1.25), color=ROOF_RED, seg=8)
    b.to_object("Chimney")


def window_frame():
    # Unit window: 0.8 wide x 1.1 tall, back face on the wall plane (y=0), facing -Y.
    b = Builder()
    w, h, t = 0.8, 1.1, 0.07
    b.box((w + 0.12, 0.10, 0.08), loc=(0, -0.05, -h / 2 - 0.02), color=STONE_WARM)  # sill
    b.box((w, 0.06, t), loc=(0, -0.03, h / 2), color=WOOD_DARK)
    b.box((w, 0.06, t), loc=(0, -0.03, -h / 2 + 0.02), color=WOOD_DARK)
    for s in (-1, 1):
        b.box((t, 0.06, h), loc=(s * w / 2, -0.03, 0), color=WOOD_DARK)
    b.box((0.04, 0.05, h), loc=(0, -0.025, 0), color=WOOD_DARK)
    b.box((w, 0.05, 0.04), loc=(0, -0.025, 0.1), color=WOOD_DARK)
    b.to_object("Frame")
    g = Builder()
    g.box((w - 0.04, 0.01, h - 0.04), loc=(0, -0.01, 0), color=GLASS)
    g.to_object("Glow", mat_name="Glow", emissive=True)


def shutters():
    b = Builder()
    for s in (-1, 1):
        b.box((0.42, 0.04, 1.08), loc=(s * 0.64, -0.03, 0), color=ROOF_BLUE)
        for z in (-0.3, 0.3):
            b.box((0.36, 0.05, 0.04), loc=(s * 0.64, -0.05, z), color=tuple(c * 0.8 for c in ROOF_BLUE))
    b.to_object("Shutters")


def flower_box():
    b = Builder()
    b.box((0.9, 0.22, 0.18), loc=(0, -0.13, -0.66), color=WOOD)
    rng.seed(4)
    for i in range(9):
        x = -0.38 + i * 0.095
        b.ball(0.07, loc=(x, -0.13, -0.53), color=LEAF, alpha=FOLIAGE, subdiv=1)
        b.ball(0.045, loc=(x + 0.02, -0.18, -0.47), color=[CLOTH_RED, CLOTH_YELLOW, WHITE, (0.9, 0.5, 0.7)][i % 4], alpha=PETAL, subdiv=1)
    b.to_object("FlowerBox")


def door():
    # 1.0 wide, 2.0 tall arched door, facing -Y, base at z=0.
    b = Builder()
    for i in range(5):
        b.box((0.19, 0.06, 1.75), loc=(-0.4 + i * 0.2, -0.03, 0.875), color=tuple(c * rng.uniform(0.9, 1.1) for c in WOOD))
    for i in range(7):
        a = i / 6 * math.pi
        b.box((0.20, 0.06, 0.20), loc=(math.cos(a) * 0.38, -0.03, 1.75 + math.sin(a) * 0.20), color=WOOD)
    for z in (0.45, 1.35):
        b.box((0.95, 0.07, 0.06), loc=(0, -0.07, z), color=IRON)
    b.ball(0.04, loc=(0.32, -0.1, 0.95), color=IRON, subdiv=1)
    b.to_object("Door")


def trapdoor():
    b = Builder()
    b.box((0.8, 0.8, 0.05), loc=(0, 0, 0.025), color=WOOD)
    b.box((0.85, 0.06, 0.06), loc=(0, -0.2, 0.06), color=IRON)
    b.box((0.85, 0.06, 0.06), loc=(0, 0.2, 0.06), color=IRON)
    b.to_object("Trapdoor")


def dormer():
    # small gable dormer, front face at y=0 facing -Y, sits on a roof slope.
    b = Builder()
    b.box((0.9, 0.9, 0.8), loc=(0, 0.45, 0.4), color=(0.93, 0.89, 0.80))
    for s in (-1, 1):
        b.box((0.62, 1.1, 0.05), loc=(s * 0.24, 0.45, 0.98), rot=(0, s * 0.75, 0), color=ROOF_RED)
    b.to_object("Dormer")


def bridge_plank():
    # 1 m segment along +X; rails both sides
    b = Builder()
    for i in range(5):
        b.box((0.18, 1.4, 0.07), loc=(0.1 + i * 0.2, 0, 0), color=tuple(c * rng.uniform(0.9, 1.1) for c in WOOD_LIGHT))
    for s in (-1, 1):
        b.box((1.0, 0.08, 0.1), loc=(0.5, s * 0.66, -0.08), color=WOOD_DARK)
        b.box((0.08, 0.08, 0.75), loc=(0.04, s * 0.66, 0.35), color=WOOD_DARK)
        b.box((1.0, 0.06, 0.06), loc=(0.5, s * 0.66, 0.70), color=WOOD)
    b.to_object("Bridge")


def stair_step():
    b = Builder()
    b.box((1.0, 0.4, 0.22), loc=(0, 0, 0.11), color=STONE_WARM, jitter=0.01)
    b.to_object("Step")


def mushroom(seed):
    rng.seed(seed)
    b = Builder()
    for i in range(3):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 0.08)
        h = rng.uniform(0.06, 0.14)
        b.cyl(0.018, 0.014, h, loc=(math.cos(a) * d, math.sin(a) * d, 0), color=WHITE, seg=6)
        b.ball(0.05, loc=(math.cos(a) * d, math.sin(a) * d, h), color=CLOTH_RED, subdiv=1, scale=(1, 1, 0.55))
    b.to_object("Mushroom")


def log_pile():
    b = Builder()
    rows = [(3, 0.0), (2, 0.18)]
    for n, z in rows:
        for i in range(n):
            x = (i - (n - 1) / 2) * 0.22
            b.cyl(0.11, 0.11, 1.0, loc=(x, -0.5, z + 0.11), rot=(-math.pi / 2, 0, 0), color=BARK, seg=7)
    b.to_object("Logs")


def stump():
    b = Builder()
    b.cyl(0.28, 0.22, 0.35, color=BARK, seg=8, jitter=0.02)
    b.cyl(0.22, 0.22, 0.01, loc=(0, 0, 0.35), color=WOOD_LIGHT, seg=8)
    b.to_object("Stump")


def cloud(seed):
    rng.seed(seed)
    b = Builder()
    for i in range(6):
        b.ball(rng.uniform(1.2, 2.0), loc=(rng.uniform(-3, 3), rng.uniform(-1.2, 1.2), rng.uniform(0, 0.8)),
               color=WHITE, subdiv=2, scale=(1, 1, 0.65))
    b.to_object("Cloud")


def weathervane():
    root = empty("Vane")
    b = Builder()
    b.cyl(0.02, 0.02, 0.9, color=IRON, seg=4)
    for a in (0, math.pi / 2):
        b.box((0.5, 0.015, 0.015), loc=(0, 0, 0.6), rot=(0, 0, a), color=IRON)
    b.to_object("Pole", root)
    p = empty("Arrow", (0, 0, 0.8), root)
    a = Builder()
    a.box((0.6, 0.02, 0.02), color=IRON)
    a.cyl(0.07, 0.0, 0.14, loc=(-0.3, 0, 0), rot=(0, -math.pi / 2, 0), color=IRON, seg=4)
    a.box((0.15, 0.01, 0.15), loc=(0.3, 0, 0.0), rot=(0, 0.785, 0), color=IRON)
    a.to_object("ArrowMesh", p)


def scarecrow():
    b = Builder()
    b.cyl(0.04, 0.04, 1.8, color=WOOD_DARK, seg=5)
    b.box((1.1, 0.06, 0.06), loc=(0, 0, 1.35), color=WOOD_DARK)
    b.box((0.45, 0.24, 0.6), loc=(0, 0, 1.2), color=CLOTH_BLUE)
    b.box((1.0, 0.18, 0.16), loc=(0, 0, 1.38), color=CLOTH_BLUE)
    b.ball(0.16, loc=(0, 0, 1.72), color=HAY, subdiv=2)
    b.cyl(0.32, 0.0, 0.25, loc=(0, 0, 1.82), color=HAY, seg=10)
    b.to_object("Scarecrow")


def windmill_sails():
    root = empty("Sails")
    b = Builder()
    for i in range(4):
        a = i / 4 * math.tau
        b.box((0.06, 0.05, 2.0), loc=(math.cos(a) * 1.0, 0, math.sin(a) * 1.0), rot=(0, -a + math.pi / 2, 0), color=WOOD_DARK)
        b.box((0.55, 0.02, 1.6), loc=(math.cos(a) * 1.1 + math.cos(a + 1.57) * 0.3, -0.02, math.sin(a) * 1.1 + math.sin(a + 1.57) * 0.3),
              rot=(0, -a + math.pi / 2, 0), color=WHITE)
    b.ball(0.12, color=WOOD_DARK, subdiv=1)
    b.to_object("SailsMesh", root)


ASSETS = {
    "tree_round_a": lambda: tree_round(1, 3.2, 5),
    "tree_round_b": lambda: tree_round(2, 3.8, 6, (0.40, 0.60, 0.26)),
    "tree_round_c": lambda: tree_round(3, 2.6, 4, (0.44, 0.58, 0.22)),
    "tree_pine_a": lambda: tree_pine(4, 4.4),
    "tree_pine_b": lambda: tree_pine(5, 3.4),
    "tree_birch": lambda: tree_birch(6),
    "bush_a": lambda: bush(7, 0.7),
    "bush_b": lambda: bush(8, 0.55, LEAF_LIGHT),
    "bush_berries": lambda: bush_berries(9),
    "flowers_pink": lambda: flowers(10, (0.96, 0.62, 0.74)),
    "flowers_white": lambda: flowers(11, WHITE),
    "flowers_blue": lambda: flowers(12, (0.55, 0.62, 0.95)),
    "flowers_yellow": lambda: flowers(13, CLOTH_YELLOW),
    "flowers_red": lambda: flowers(14, CLOTH_RED),
    "grass_tuft": lambda: grass_tuft(15),
    "reeds": lambda: reeds(16),
    "lily_pad_a": lambda: lily_pad(18),
    "lily_pad_b": lambda: lily_pad(19),
    "rock_a": lambda: rock(20, 0.55),
    "rock_b": lambda: rock(21, 0.35, STONE_DARK),
    "rock_c": lambda: rock(22, 0.85),
    "cobble_a": lambda: cobble(23),
    "cobble_b": lambda: cobble(24),
    "stepping_stone": lambda: stepping_stone(25),
    "sheep": sheep,
    "duck": lambda: duck(),
    "duckling": lambda: duck(CLOTH_YELLOW, CLOTH_YELLOW),
    "chicken": chick,
    "bird": bird,
    "butterfly": butterfly,
    "lantern": lantern,
    "wall_lantern": wall_lantern,
    "fence_post": fence_post,
    "fence_rail": fence_rail,
    "gate": gate,
    "well": well,
    "haystack": haystack,
    "hay_bale": hay_bale,
    "barrel": barrel,
    "crate": crate,
    "cart": cart,
    "bench": bench,
    "banner": banner,
    "chimney": chimney,
    "window_frame": window_frame,
    "shutters": shutters,
    "flower_box": flower_box,
    "door": door,
    "trapdoor": trapdoor,
    "dormer": dormer,
    "bridge_plank": bridge_plank,
    "stair_step": stair_step,
    "mushrooms": lambda: mushroom(30),
    "log_pile": log_pile,
    "stump": stump,
    "cloud_a": lambda: cloud(40),
    "cloud_b": lambda: cloud(41),
    "weathervane": weathervane,
    "scarecrow": scarecrow,
    "windmill_sails": windmill_sails,
}


def render_icon(path, size=512, transparent=False, ortho_scale=6.2):
    """Renders the launcher icon: a tiny glade diorama on a soft sky disc."""
    reset_scene()
    scene = bpy.context.scene
    # island
    b = Builder()
    b.cyl(2.6, 2.2, 0.5, loc=(0, 0, -0.5), color=(0.55, 0.42, 0.30), seg=24)
    b.cyl(2.6, 2.6, 0.12, loc=(0, 0, -0.06), color=(0.50, 0.70, 0.32), seg=24)
    b.to_object("Island")
    # cottage
    c = Builder()
    c.box((1.6, 1.1, 1.0), loc=(-0.3, 0.1, 0.5), color=(0.96, 0.92, 0.83))
    for s in (-1, 1):
        c.box((1.8, 0.85, 0.08), loc=(-0.3, 0.1 + s * 0.33, 1.25), rot=(-s * 0.75, 0, 0), color=ROOF_RED)
    c.box((0.3, 0.05, 0.4), loc=(-0.6, -0.46, 0.55), color=GLASS)
    c.box((0.3, 0.05, 0.6), loc=(0.05, -0.46, 0.3), color=WOOD)
    c.box((0.25, 0.25, 0.7), loc=(0.2, 0.3, 1.5), color=STONE_WARM)
    # tower
    c.cyl(0.45, 0.42, 2.0, loc=(1.15, 0.5, 0), color=STONE, seg=16)
    c.cyl(0.6, 0.0, 1.0, loc=(1.15, 0.5, 2.0), color=ROOF_BLUE, seg=16)
    c.to_object("Cottage")
    t = Builder()
    for x, y, r in ((-1.6, 1.0, 0.55), (-1.4, -1.2, 0.4), (1.6, -1.2, 0.45)):
        t.cyl(0.08, 0.06, 0.6, loc=(x, y, 0), color=BARK)
        t.ball(r, loc=(x, y, 0.6 + r * 0.8), color=LEAF, subdiv=2, jitter=0.08)
    t.ball(0.22, loc=(0.6, -1.3, 0.2), color=WOOL, subdiv=2, scale=(1, 1.3, 0.9))
    t.to_object("Trees")
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.70, 0.85, 0.95, 1.0)
    bg.inputs[1].default_value = 1.0
    scene.world = world
    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 3.5
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-40))
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = ortho_scale
    cam = bpy.data.objects.new("Cam", cam_data)
    cam.location = (7.5, -7.5, 6.2)
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
        # adaptive-icon foreground: transparent, island kept inside the 66% safe zone
        render_icon(os.path.abspath(os.path.join(icon_dir, "icon_foreground_432.png")), 432, True, 9.0)


if __name__ == "__main__":
    main()
