"""Import rigged animals from Quaternius' Ultimate Animated Animals (CC0) as
Everglade wildlife: material colours are baked into vertex colours with the
plain "paint" surface id (so the shared prop shader lights them like every
other creature), and only the clips the game plays are kept.

  /tmp/bvenv/bin/python tools/import_quaternius_animals.py -- <pack glTF dir> assets/models Deer Fox ...
Writes q_<name>.glb and prints each model's height in metres.
"""
import bpy, bmesh, sys, os, json

args = sys.argv[sys.argv.index("--") + 1:]
src, out_dir, names = args[0], args[1], args[2:]
KEEP = ("Walk", "Idle", "Eating", "Idle_2", "Gallop")
M_PAINT = 0

for name in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path = os.path.join(src, name + ".gltf")
    # the importer hides base colours in a mix node; read them from the file
    factors = {m["name"]: tuple(m.get("pbrMetallicRoughness", {}).get("baseColorFactor", (0.8, 0.8, 0.8, 1))[:3])
               for m in json.load(open(path)).get("materials", [])}
    bpy.ops.import_scene.gltf(filepath=path)
    for act in list(bpy.data.actions):
        base = act.name.split("|")[-1].split(".")[0]
        if base not in KEEP:
            bpy.data.actions.remove(act)
    vc = bpy.data.materials.new("VertexColor")
    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        me = o.data
        cols = [factors.get(m.name.split(".")[0], (0.8, 0.8, 0.8)) if m else (0.8, 0.8, 0.8) for m in me.materials]
        while len(me.color_attributes) > 0:
            me.color_attributes.remove(me.color_attributes[0])
        bm = bmesh.new(); bm.from_mesh(me)
        col = bm.loops.layers.color.new("Color")
        uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new("UVMap")
        for f in bm.faces:
            c = cols[f.material_index] if f.material_index < len(cols) else (0.8, 0.8, 0.8)
            for l in f.loops:
                l[col] = (c[0], c[1], c[2], 1.0)
                l[uv].uv = ((M_PAINT + 0.5) / 16.0, 0.5)
        bm.to_mesh(me); bm.free()
        me.color_attributes.active_color = me.color_attributes[0]
        me.materials.clear()
        me.materials.append(vc)
    zs = [(o.matrix_world @ v.co).z for o in bpy.data.objects if o.type == "MESH" for v in o.data.vertices]
    print("animal", name, "height", round(max(zs) - min(zs), 3))
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "q_" + name.lower() + ".glb"), export_format="GLB",
                              export_yup=True, export_normals=True, export_vertex_color="ACTIVE",
                              export_all_vertex_colors=False, export_materials="EXPORT", export_image_format="NONE",
                              export_animations=True, export_animation_mode="ACTIONS", export_skins=True)
