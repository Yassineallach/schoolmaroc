extends Node
## Loads the Blender-made GLB props, re-skins them with the shared stylised
## materials and offers merged meshes for MultiMesh batching.

const MODEL_DIR := "res://assets/models/"
const FOLIAGE_DIR := "res://assets/textures/foliage/"
const KIT_TEX_DIR := "res://assets/textures/qkit/"

## Trees, bushes and grass from Quaternius' Stylized Nature MegaKit (CC0),
## converted by tools/import_quaternius.sh, stand in for the original
## procedural models under the same kind names (saves and templates keep
## working). The lightweight originals stay available with raw = true (the
## forest belt and backdrops use those).
const ALIAS := {
	"tree_round_a": "q_tree_round_a", "tree_round_c": "q_tree_round_c", "tree_round_b": "q_tree_round_b",
	"tree_birch": "q_tree_birch", "tree_blossom": "q_tree_blossom", "tree_golden": "q_tree_golden",
	"tree_orange": "q_tree_orange", "tree_teal": "q_tree_teal", "tree_pine_a": "q_tree_pine_a",
	"tree_pine_b": "q_tree_pine_b", "tree_cedar": "q_tree_cedar", "bush_a": "q_bush_a", "bush_golden": "q_bush_golden",
	# textured kit models (tools/import_quaternius_tex.py): Medieval Village
	# MegaKit details and props, Nature MegaKit flowers, bushes and stones
	"door": "q_door", "window_frame": "q_window_frame", "shutters": "q_shutters", "chimney": "q_chimney",
	"fence_ornate": "q_fence_ornate", "fence_rail": "q_fence_rail",
	"cart": "q_cart", "crate": "q_crate", "flowers_white": "q_flowers_white", "flowers_pink": "q_flowers_pink",
	"flowers_blue": "q_flowers_blue", "flowers_yellow": "q_flowers_yellow", "flowers_red": "q_flowers_red",
	"bush_b": "q_bush_b", "bush_berries": "q_bush_berries", "mushrooms": "q_mushrooms",
	"stepping_stone": "q_stepping_stone", "cobble_a": "q_cobble_a", "cobble_b": "q_cobble_b",
	# kit-only ground plants (no procedural original)
	"fern": "q_fern", "plant_leafy": "q_plant", "wheat": "q_wheat",
}
## leaf material name suffix -> texture file (where they differ)
const LEAF_FILES := {"Leaves_Pine": "Leaf_Pine"}

var props_material: ShaderMaterial
var glow_material: ShaderMaterial
var arch_material: ShaderMaterial
var leaf_material: ShaderMaterial
var grass_material: ShaderMaterial
var surface_albedo: TextureLayered = load("res://assets/textures/mat_albedo.png")
var surface_normal: TextureLayered = load("res://assets/textures/mat_normal.png")

var _scenes: Dictionary = {}
var _leaf_mats: Dictionary = {}
var _tex_mats: Dictionary = {}
var _tex_shader: Shader = load("res://shaders/props_tex.gdshader")
var _cut_shader: Shader = load("res://shaders/props_cut.gdshader")
var _merged: Dictionary = {}
var _tinted: Dictionary = {}

## The tg_* wood models' own colours: honey wood, and the sage shutters and
## cream frames their trims are painted in (blender/build_wood.py).
const HONEY := Color(0.72, 0.54, 0.31)
const TRIM_REFS := [Color(0.50, 0.53, 0.36), Color(0.93, 0.89, 0.81)]
const SLICE_PAINT := 0
const SLICE_WOOD := 3


func _init() -> void:
	props_material = ShaderMaterial.new()
	props_material.shader = load("res://shaders/props.gdshader")
	glow_material = ShaderMaterial.new()
	glow_material.shader = load("res://shaders/glow.gdshader")
	leaf_material = ShaderMaterial.new()
	leaf_material.shader = load("res://shaders/foliage.gdshader")
	leaf_material.set_shader_parameter("leaf_tex", load("res://assets/textures/leaves.png"))
	arch_material = ShaderMaterial.new()
	arch_material.shader = load("res://shaders/architecture.gdshader")
	grass_material = props_material.duplicate() as ShaderMaterial
	for m in [props_material, arch_material, grass_material]:
		apply_surface_textures(m)
	grass_material.set_shader_parameter("detail_on", 0.0)


## Hooks a material up to the shared stone/wood/plaster/... texture arrays.
func apply_surface_textures(m: ShaderMaterial) -> void:
	m.set_shader_parameter("mat_albedo", surface_albedo)
	m.set_shader_parameter("mat_normal", surface_normal)


func resolve(kind: String, raw := false) -> String:
	if raw:
		return kind
	var a: String = ALIAS.get(kind, kind)
	return a if ResourceLoader.exists(MODEL_DIR + a + ".glb") else kind


func has_model(kind: String) -> bool:
	return Clutter.KINDS.has(kind) or ResourceLoader.exists(MODEL_DIR + resolve(kind) + ".glb")


## Foliage material for one leaf-mask texture ("" = the painted atlas).
func leaf_material_for(tex: String) -> ShaderMaterial:
	if tex == "":
		return leaf_material
	if not _leaf_mats.has(tex):
		var path: String = FOLIAGE_DIR + LEAF_FILES.get(tex, tex) + ".png"
		if not ResourceLoader.exists(path):
			return leaf_material
		var m := leaf_material.duplicate() as ShaderMaterial
		m.set_shader_parameter("leaf_tex", load(path))
		m.set_shader_parameter("alpha_cut", 0.3)
		_leaf_mats[tex] = m
	return _leaf_mats[tex]


## Material for a kit model surface named "Tex__<file>" or "Cut__<file>"
## (painted texture; Cut = alpha-cut and double sided), null otherwise.
func kit_material_for(mat_name: String) -> ShaderMaterial:
	if not (mat_name.begins_with("Tex__") or mat_name.begins_with("Cut__")):
		return null
	if not _tex_mats.has(mat_name):
		var m := ShaderMaterial.new()
		m.shader = _cut_shader if mat_name.begins_with("Cut__") else _tex_shader
		var path := KIT_TEX_DIR + mat_name.substr(5)
		if ResourceLoader.exists(path):
			m.set_shader_parameter("albedo_tex", load(path))
		_tex_mats[mat_name] = m
	return _tex_mats[mat_name]


static func _mat_name(mi: MeshInstance3D) -> String:
	if mi.mesh and mi.mesh.get_surface_count() > 0:
		var mat := mi.mesh.surface_get_material(0)
		if mat:
			return mat.resource_name
	return ""


static func _leaf_tex_of(mi: MeshInstance3D) -> String:
	if mi.mesh and mi.mesh.get_surface_count() > 0:
		var mat := mi.mesh.surface_get_material(0)
		if mat and mat.resource_name.contains("__"):
			return mat.resource_name.split("__", true, 1)[1]
	return ""


func _scene(kind: String) -> PackedScene:
	if not _scenes.has(kind):
		_scenes[kind] = load(MODEL_DIR + kind + ".glb") as PackedScene
	return _scenes[kind]


## Instantiates the model as a node tree with stylised materials applied.
## Animated props/creatures use this to reach their named child pivots.
func instance(kind: String, raw := false) -> Node3D:
	if Clutter.KINDS.has(kind):
		var holder := Node3D.new()
		var mi := MeshInstance3D.new()
		mi.mesh = merged(kind).solid
		mi.material_override = props_material
		holder.add_child(mi)
		if merged(kind).glow:
			var gi := MeshInstance3D.new()
			gi.mesh = merged(kind).glow
			gi.material_override = glow_material
			holder.add_child(gi)
		return holder
	var packed := _scene(resolve(kind, raw))
	if packed == null:
		push_warning("Missing model: " + kind)
		return Node3D.new()
	var root := packed.instantiate() as Node3D
	_reskin(root)
	return root


func _reskin(node: Node) -> void:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		var kit := kit_material_for(_mat_name(mi))
		if kit:
			mi.material_override = kit
		else:
			mi.material_override = glow_material if _is_glow(mi) else (leaf_material_for(_leaf_tex_of(mi)) if _is_leaves(mi) else props_material)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for child in node.get_children():
		_reskin(child)


func _is_leaves(mi: MeshInstance3D) -> bool:
	if mi.name.begins_with("Leaves"):
		return true
	if mi.mesh and mi.mesh.get_surface_count() > 0:
		var mat := mi.mesh.surface_get_material(0)
		if mat and mat.resource_name.begins_with("Leaves"):
			return true
	return false


func _is_glow(mi: MeshInstance3D) -> bool:
	if mi.name.begins_with("Glow"):
		return true
	if mi.mesh and mi.mesh.get_surface_count() > 0:
		var mat := mi.mesh.surface_get_material(0)
		if mat and mat.resource_name.begins_with("Glow"):
			return true
	return false


## Returns {"solid": ArrayMesh, "glow": ArrayMesh or null, "aabb": AABB}
## with every child mesh baked into the model's root space.
func merged(kind: String, raw := false) -> Dictionary:
	var key := resolve(kind, raw)
	if _merged.has(key):
		return _merged[key]
	if Clutter.KINDS.has(kind):
		var cm := Clutter.build(kind)
		var cr := {"solid": cm, "glow": Clutter.build_glow(kind), "leaves": null, "tex": [], "aabb": cm.get_aabb(), "leaf_mat": leaf_material}
		_merged[key] = cr
		return cr
	var root := instance(key, true)
	var leaf_tex := ""
	var solid := SurfaceTool.new()
	var glow := SurfaceTool.new()
	var leaves := SurfaceTool.new()
	var has_solid := false
	var has_glow := false
	var has_leaves := false
	var kit: Dictionary = {} # kit material -> SurfaceTool
	var stack: Array = [[root, Transform3D.IDENTITY]]
	while not stack.is_empty():
		var item: Array = stack.pop_back()
		var node: Node3D = item[0]
		var xf: Transform3D = item[1]
		for child in node.get_children():
			if child is Node3D:
				var cxf: Transform3D = xf * (child as Node3D).transform
				if child is MeshInstance3D and (child as MeshInstance3D).mesh:
					var mi := child as MeshInstance3D
					var km := kit_material_for(_mat_name(mi))
					if km:
						if not kit.has(km):
							kit[km] = SurfaceTool.new()
						for s in mi.mesh.get_surface_count():
							(kit[km] as SurfaceTool).append_from(mi.mesh, s, cxf)
						stack.append([child, cxf])
						continue
					var target := glow if _is_glow(mi) else (leaves if _is_leaves(mi) else solid)
					for s in mi.mesh.get_surface_count():
						target.append_from(mi.mesh, s, cxf)
					if target == glow:
						has_glow = true
					elif target == leaves:
						has_leaves = true
						if leaf_tex == "":
							leaf_tex = _leaf_tex_of(mi)
					else:
						has_solid = true
				stack.append([child, cxf])
	root.free()
	var result := {"solid": null, "glow": null, "leaves": null, "tex": [], "aabb": AABB(Vector3(-0.5, 0, -0.5), Vector3.ONE)}
	var have_aabb := false
	result.leaf_mat = leaf_material_for(leaf_tex)
	if has_solid:
		var m := solid.commit()
		result.solid = m
		result.aabb = m.get_aabb()
		have_aabb = true
	for km in kit:
		var km_mesh := (kit[km] as SurfaceTool).commit()
		result.tex.append([km_mesh, km])
		result.aabb = result.aabb.merge(km_mesh.get_aabb()) if have_aabb else km_mesh.get_aabb()
		have_aabb = true
	if has_glow:
		result.glow = glow.commit()
	if has_leaves:
		result.leaves = leaves.commit()
		if not have_aabb:
			result.aabb = result.leaves.get_aabb()
		else:
			result.aabb = result.aabb.merge(result.leaves.get_aabb())
	_merged[key] = result
	return result


## Every part of a model as one multi-surface mesh with its materials set
## (for MultiMeshes drawn without a material override, e.g. meadow flowers).
## `solid_mat` draws the plain vertex-coloured parts.
func combined(kind: String, solid_mat: Material = null) -> ArrayMesh:
	var m := merged(kind)
	var out := ArrayMesh.new()
	var parts: Array = []
	if m.solid:
		parts.append([m.solid, solid_mat if solid_mat else props_material])
	if m.leaves:
		parts.append([m.leaves, m.leaf_mat])
	parts.append_array(m.tex)
	for part in parts:
		var src: ArrayMesh = part[0]
		for s in src.get_surface_count():
			out.add_surface_from_arrays(src.surface_get_primitive_type(s), src.surface_get_arrays(s))
			out.surface_set_material(out.get_surface_count() - 1, part[1])
	return out


## Footprint radius used for picking/erasing props.
func radius(kind: String) -> float:
	var aabb: AABB = merged(kind).aabb
	return maxf(0.25, maxf(aabb.size.x, aabb.size.z) * 0.45)


## Material for one architecture mesh (walls/buildings) so each can animate
## its own build-up effect.
func new_arch_material() -> ShaderMaterial:
	var mat := arch_material.duplicate() as ShaderMaterial
	return mat


## A model's merged meshes with its wood shifted to another tone and its
## painted trims (shutters, window frames) in another colour. A colour with
## alpha 0 keeps the model's own.
func tinted(kind: String, wood: Color, trim: Color) -> Dictionary:
	var base := merged(kind)
	if (wood.a <= 0.0 and trim.a <= 0.0) or base.solid == null:
		return base
	var key := "%s|%s|%s" % [kind, wood.to_html(), trim.to_html()]
	if _tinted.has(key):
		return _tinted[key]
	var arr: Array = (base.solid as ArrayMesh).surface_get_arrays(0)
	var cols: PackedColorArray = arr[Mesh.ARRAY_COLOR]
	var uvs: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV]
	if cols.size() == uvs.size():
		for i in cols.size():
			var c := cols[i]
			var slice := int(uvs[i].x * 16.0)
			if slice == SLICE_WOOD and wood.a > 0.0:
				cols[i] = Color(minf(1.0, c.r * wood.r / HONEY.r), minf(1.0, c.g * wood.g / HONEY.g), minf(1.0, c.b * wood.b / HONEY.b), c.a)
			elif slice == SLICE_PAINT and trim.a > 0.0:
				for ref: Color in TRIM_REFS:
					if absf(c.r - ref.r) + absf(c.g - ref.g) + absf(c.b - ref.b) < 0.2:
						# keep each board's small shift in tone
						var k := (c.r + c.g + c.b) / (ref.r + ref.g + ref.b)
						cols[i] = Color(minf(1.0, trim.r * k), minf(1.0, trim.g * k), minf(1.0, trim.b * k), c.a)
						break
		arr[Mesh.ARRAY_COLOR] = cols
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var out := base.duplicate()
	out.solid = mesh
	_tinted[key] = out
	return out
