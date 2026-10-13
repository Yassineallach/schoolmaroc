"""Import Quaternius' Stylized Nature MegaKit (CC0) trees, bushes and grass
into Everglade's conventions: leaves joined into a 'Leaves' mesh tinted by a
vertex-colour gradient with soft spherical crown normals; bark as vertex
coloured mesh with the bark material id; grass clumps get per-blade data
for Everglade's grass shader (COLOR.r random, COLOR.g height 0..1)."""
import bpy, bmesh, sys, os, math, random
from mathutils import Vector

#   /tmp/bvenv/bin/python tools/import_quaternius.py -- <megakit>/glTF assets/models \
#       CommonTree_5:tree:green:4.6:tree_round_a ...
# Leaf meshes get the material "Leaves__<texture>", so the game pairs each
# tree with its own leaf-mask texture from assets/textures/foliage/.
args = sys.argv[sys.argv.index("--") + 1:]
src, out_dir = args[0], args[1]
jobs = [a.split(":") for a in args[2:]]   # name:kind:palette:height:out_name
os.makedirs(out_dir, exist_ok=True)

PALETTES = {
    "green": ((0.68, 0.86, 0.40), (0.42, 0.66, 0.28), (0.18, 0.40, 0.22)),
    "deep": ((0.50, 0.74, 0.40), (0.26, 0.52, 0.30), (0.10, 0.30, 0.22)),
    "birch": ((0.86, 0.90, 0.46), (0.58, 0.76, 0.32), (0.30, 0.50, 0.22)),
    "blossom": ((1.00, 0.90, 0.94), (0.98, 0.74, 0.84), (0.80, 0.48, 0.62)),
    "gold": ((1.00, 0.86, 0.42), (0.92, 0.62, 0.24), (0.62, 0.36, 0.16)),
    "pine": ((0.40, 0.64, 0.42), (0.22, 0.46, 0.34), (0.10, 0.28, 0.24)),
    "orange": ((1.00, 0.70, 0.36), (0.92, 0.42, 0.20), (0.60, 0.22, 0.14)),
    "teal": ((0.52, 0.84, 0.74), (0.28, 0.62, 0.58), (0.12, 0.38, 0.40)),
}
BARK = ((0.52, 0.38, 0.28), (0.30, 0.21, 0.16))
BIRCH_BARK = ((0.92, 0.90, 0.86), (0.62, 0.60, 0.58))
M_BARK = 4

def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def join(objs, name):
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o.name = name
    o.data.name = name
    return o

def set_colors(obj, fn, uv_fn=None):
    me = obj.data
    while len(me.color_attributes) > 0:
        me.color_attributes.remove(me.color_attributes[0])
    bm = bmesh.new(); bm.from_mesh(me)
    col = bm.loops.layers.color.new("Color")
    uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for l in f.loops:
            c = fn(l.vert, f)
            l[col] = c
            if uv_fn:
                l[uv].uv = uv_fn(l)
    bm.to_mesh(me); bm.free()
    attr = me.color_attributes[0]
    me.color_attributes.active_color = attr
    try:
        me.color_attributes.active_color_name = attr.name
        me.color_attributes.default_color_name = attr.name
    except AttributeError:
        pass

def material(obj, name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    obj.data.materials.clear()
    obj.data.materials.append(m)

for job in jobs:
    name, kind, pal = job[0], job[1], job[2]
    target_h = float(job[3]) if len(job) > 3 else 0.0
    out_name = job[4] if len(job) > 4 else "q_" + name.lower()
    reset()
    bpy.ops.import_scene.gltf(filepath=os.path.join(src, name + ".gltf"))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    # split by material: leaves vs bark
    leaf_objs, bark_objs, tex = [], [], None
    for o in meshes:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        if len(o.data.materials) > 1:
            bpy.ops.mesh.separate(type="MATERIAL")
    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        mname = o.data.materials[0].name if o.data.materials else ""
        if mname.startswith("Leaves") or mname.startswith("Leaf") or kind == "grass":
            leaf_objs.append(o)
            tex = mname
        else:
            bark_objs.append(o)
    if kind == "grass":
        g = join(leaf_objs + bark_objs, "Grass")
        zs = [v.co.z for v in g.data.vertices]
        z0, z1 = min(zs), max(zs)
        # random per connected blade
        bm = bmesh.new(); bm.from_mesh(g.data)
        bm.verts.ensure_lookup_table()
        island = {}
        rnd = random.Random(7)
        for v in bm.verts:
            if v.index in island:
                continue
            r = rnd.random(); stack = [v]
            while stack:
                w = stack.pop()
                if w.index in island:
                    continue
                island[w.index] = r
                for e in w.link_edges:
                    stack.append(e.other_vert(w))
        bm.free()
        set_colors(g, lambda v, f: (island[v.index], (v.co.z - z0) / max(z1 - z0, 1e-4), (z1 - z0), 1.0),
                   lambda l: (0.0, 0.0))
        material(g, "Grass")
    else:
        leaves = join(leaf_objs, "Leaves")
        trunk = join(bark_objs, "Trunk")
        if leaves:
            vs = [v.co for v in leaves.data.vertices]
            lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
            hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
            centre = (lo + hi) / 2
            half = (hi - lo) / 2
            top, mid, bot = PALETTES[pal]
            alpha = 0.25 if pal == "pine" else (0.5 if pal in ("blossom",) else 0.0)
            def leaf_col(v, f):
                t = (v.co.z - lo.z) / max(hi.z - lo.z, 1e-4)
                c = lerp(bot, mid, min(t * 1.6, 1.0)) if t < 0.62 else lerp(mid, top, (t - 0.62) / 0.38)
                return (c[0], c[1], c[2], alpha)
            set_colors(leaves, leaf_col)
            # soft spherical crown normals (painted canopy shading)
            me = leaves.data
            normals = []
            for v in me.vertices:
                d = v.co - centre
                d = Vector((d.x / max(half.x, 0.1), d.y / max(half.y, 0.1), d.z / max(half.z, 0.1)))
                n = (v.normal * 0.3 + d.normalized() * 0.7).normalized()
                normals.append(n)
            me.normals_split_custom_set_from_vertices(normals)
            material(leaves, "Leaves__" + (tex or "Leaves_NormalTree"))
        if trunk:
            b = BIRCH_BARK if "Birch" in name else BARK
            zs = [v.co.z for v in trunk.data.vertices]
            z0, z1 = min(zs), max(zs)
            set_colors(trunk, lambda v, f: (*lerp(b[1], b[0], ((v.co.z - z0) / max(z1 - z0, 1e-4)) ** 0.6), 1.0),
                       lambda l: ((M_BARK + 0.5) / 16.0, 0.5))
            material(trunk, "VertexColor")
    # tidy: remove empties/non meshes, scale to game size, export
    for o in list(bpy.data.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    if target_h > 0.0:
        zs = [(o.matrix_world @ v.co).z for o in bpy.data.objects for v in o.data.vertices]
        k = target_h / max(max(zs) - min(zs), 1e-3)
        for o in bpy.data.objects:
            o.scale = (k, k, k)
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, out_name + ".glb"), export_format="GLB",
                              use_selection=True, export_apply=True, export_yup=True, export_normals=True,
                              export_vertex_color="ACTIVE", export_all_vertex_colors=False,
                              export_materials="EXPORT", export_image_format="NONE", export_animations=False)
    print("converted", name, "->", out_name, "leaf texture:", tex)
