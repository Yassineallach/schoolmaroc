"""Import textured Quaternius (CC0) models — Medieval Village MegaKit building
details and props, Stylized Nature MegaKit flowers, mushrooms, stones and
ground plants — into Everglade.

Unlike the tree importer this keeps each model's UVs and painted textures:
every material is renamed so the game knows how to draw it
  Tex__<file>   opaque textured surface   (shaders/props_tex.gdshader)
  Cut__<file>   alpha-cut, double sided   (leaves, petals, wheat)
  Glow          window glass that lights up at night
and the vertex colour carries Everglade's channel in alpha (1 solid,
0 foliage that sways and follows the season, 0.5 petals that only sway).

Sizing: "fit=<kind>" stretches the model into the bounding box of our own
assets/models/<kind>.glb, so it drops into exactly the same slot (doors in
wall openings, shutters beside windows, fence rails between posts);
"h=<metres>" scales it uniformly to a height.

  /tmp/bvenv/bin/python tools/import_quaternius_tex.py -- <nature glTF> <village glTF> assets/models \
      QM/Door_1_Round:fit=door:q_door [rot=90] [part=rails|post] [dec=0.3] ...
"""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix

args = sys.argv[sys.argv.index("--") + 1:]
packs = {"QN": args[0], "QM": args[1]}
out_dir = args[2]
jobs = args[3:]

CUT = ("Leaves", "Leaf", "Flowers", "Grass")
PETALS = ("Flowers", "Grass")


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def meshes():
    return [o for o in bpy.data.objects if o.type == "MESH"]


def bounds(objs):
    lo = Vector((1e9, 1e9, 1e9)); hi = -lo
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi


def apply_all():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def texture_path(pack, tex):
    d = packs[pack]
    return os.path.join(d, tex) if pack == "QN" else os.path.join(d, "..", "Textures", tex)


def texture_of(mat):
    if mat is None or not mat.use_nodes:
        return ""
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image:
            return os.path.basename(n.image.filepath or n.image.name)
    return ""


def our_bounds(kind):
    reset()
    bpy.ops.import_scene.gltf(filepath=os.path.join(out_dir, kind + ".glb"))
    lo, hi = bounds(meshes())
    return lo, hi


def keep_parts(part):
    """Split into loose parts and keep the rails (wide, low) or one post (tall)."""
    for o in meshes():
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.mesh.separate(type="LOOSE")
    parts = meshes()
    tall = []
    for o in parts:
        lo, hi = bounds([o])
        size = hi - lo
        is_post = size.z > max(size.x, size.y) * 1.5
        tall.append((o, is_post, lo.x))
    if part == "rails":
        for o, is_post, _ in tall:
            if is_post:
                bpy.data.objects.remove(o)
    else:
        posts = sorted([t for t in tall if t[1]], key=lambda t: t[2])
        keep = posts[0][0] if posts else None
        for o, _, _ in tall:
            if o is not keep:
                bpy.data.objects.remove(o)


def recolour(o, alpha, rgb=(1.0, 1.0, 1.0)):
    me = o.data
    while len(me.color_attributes) > 0:
        me.color_attributes.remove(me.color_attributes[0])
    attr = me.color_attributes.new("Color", "FLOAT_COLOR", "CORNER")
    for d in attr.data:
        d.color = (rgb[0], rgb[1], rgb[2], alpha)
    me.color_attributes.active_color = attr
    try:
        me.color_attributes.default_color_name = attr.name
    except AttributeError:
        pass


def set_material(o, name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    o.data.materials.clear()
    o.data.materials.append(m)


textures = set()
for job in jobs:
    parts = job.split(":")
    src, size, out_name = parts[0], parts[1], parts[2]
    opts = dict(p.split("=", 1) for p in parts[3:])
    pack, name = src.split("/", 1)
    fit_lo = fit_hi = None
    if size.startswith("fit="):
        fit_lo, fit_hi = our_bounds(size[4:])
    reset()
    bpy.ops.import_scene.gltf(filepath=os.path.join(packs[pack], name + ".gltf"))
    for o in list(bpy.data.objects):
        if o.type != "MESH":
            # keep meshes' world transforms when dropping empties/armatures
            for c in o.children:
                mw = c.matrix_world.copy()
                c.parent = None
                c.matrix_world = mw
            bpy.data.objects.remove(o)
    apply_all()
    if "part" in opts:
        keep_parts(opts["part"])
    # one object per material
    for o in meshes():
        if len(o.data.materials) > 1:
            bpy.ops.object.select_all(action="DESELECT")
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            bpy.ops.mesh.separate(type="MATERIAL")
    for o in meshes():
        mat = o.data.materials[0] if o.data.materials else None
        mname = mat.name if mat else ""
        tex = texture_of(mat)
        if tex and not os.path.exists(texture_path(pack, tex)):
            tex = ""   # not shipped with the free edition: flat colour instead
        if "Glass" in mname:
            recolour(o, 1.0, (0.36, 0.42, 0.5))
            set_material(o, "Glow")
            o.name = "Glow"
        elif tex and mname.startswith(CUT):
            recolour(o, 0.5 if mname.startswith(PETALS) else 0.0)
            set_material(o, "Cut__" + tex)
            textures.add((pack, tex))
        elif tex:
            recolour(o, 1.0)
            set_material(o, "Tex__" + tex)
            textures.add((pack, tex))
        else:
            iron = "Metal" in mname
            recolour(o, 1.0, (0.2, 0.21, 0.24) if iron else (tuple(mat.diffuse_color[:3]) if mat else (0.8, 0.8, 0.8)))
            set_material(o, "VertexColor")
    if "dec" in opts:
        # fine ironwork is far denser than a phone needs for a fence segment
        for o in meshes():
            d = o.modifiers.new("dec", "DECIMATE")
            d.ratio = float(opts["dec"])
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier="dec")
    rot = math.radians(float(opts.get("rot", "0")))
    for o in meshes():
        o.matrix_world = Matrix.Rotation(rot, 4, "Z") @ o.matrix_world
    apply_all()
    lo, hi = bounds(meshes())
    if fit_lo is not None:
        s = Vector([(fit_hi[i] - fit_lo[i]) / max(hi[i] - lo[i], 1e-4) for i in range(3)])
        for o in meshes():
            o.matrix_world = Matrix.Translation(fit_lo) @ Matrix.Diagonal((*s, 1.0)) @ Matrix.Translation(-lo) @ o.matrix_world
    else:
        k = float(size[2:]) / max(hi.z - lo.z, 1e-4)
        c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
        for o in meshes():
            o.matrix_world = Matrix.Scale(k, 4) @ Matrix.Translation(-c) @ o.matrix_world
    apply_all()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, out_name + ".glb"), export_format="GLB",
                              use_selection=True, export_apply=True, export_yup=True, export_normals=True,
                              export_vertex_color="ACTIVE", export_all_vertex_colors=False,
                              export_materials="EXPORT", export_image_format="NONE", export_animations=False)
    print("converted", src, "->", out_name)

with open(os.path.join(out_dir, "..", "textures", "qkit_list.txt"), "w") as f:
    for pack, tex in sorted(textures):
        f.write(pack + " " + tex + "\n")
