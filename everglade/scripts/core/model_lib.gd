extends Node
## Loads the Blender-made GLB props, re-skins them with the shared stylised
## materials and offers merged meshes for MultiMesh batching.

const MODEL_DIR := "res://assets/models/"

var props_material: ShaderMaterial
var glow_material: ShaderMaterial
var arch_material: ShaderMaterial
var leaf_material: ShaderMaterial

var _scenes: Dictionary = {}
var _merged: Dictionary = {}


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


func has_model(kind: String) -> bool:
	return ResourceLoader.exists(MODEL_DIR + kind + ".glb")


func _scene(kind: String) -> PackedScene:
	if not _scenes.has(kind):
		_scenes[kind] = load(MODEL_DIR + kind + ".glb") as PackedScene
	return _scenes[kind]


## Instantiates the model as a node tree with stylised materials applied.
## Animated props/creatures use this to reach their named child pivots.
func instance(kind: String) -> Node3D:
	var packed := _scene(kind)
	if packed == null:
		push_warning("Missing model: " + kind)
		return Node3D.new()
	var root := packed.instantiate() as Node3D
	_reskin(root)
	return root


func _reskin(node: Node) -> void:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		mi.material_override = glow_material if _is_glow(mi) else (leaf_material if _is_leaves(mi) else props_material)
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
func merged(kind: String) -> Dictionary:
	if _merged.has(kind):
		return _merged[kind]
	var root := instance(kind)
	var solid := SurfaceTool.new()
	var glow := SurfaceTool.new()
	var leaves := SurfaceTool.new()
	var has_solid := false
	var has_glow := false
	var has_leaves := false
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
					var target := glow if _is_glow(mi) else (leaves if _is_leaves(mi) else solid)
					for s in mi.mesh.get_surface_count():
						target.append_from(mi.mesh, s, cxf)
					if target == glow:
						has_glow = true
					elif target == leaves:
						has_leaves = true
					else:
						has_solid = true
				stack.append([child, cxf])
	root.free()
	var result := {"solid": null, "glow": null, "leaves": null, "aabb": AABB(Vector3(-0.5, 0, -0.5), Vector3.ONE)}
	if has_solid:
		var m := solid.commit()
		result.solid = m
		result.aabb = m.get_aabb()
	if has_glow:
		result.glow = glow.commit()
	if has_leaves:
		result.leaves = leaves.commit()
		if result.solid == null:
			result.aabb = result.leaves.get_aabb()
		else:
			result.aabb = result.aabb.merge(result.leaves.get_aabb())
	_merged[kind] = result
	return result


## Footprint radius used for picking/erasing props.
func radius(kind: String) -> float:
	var aabb: AABB = merged(kind).aabb
	return maxf(0.25, maxf(aabb.size.x, aabb.size.z) * 0.45)


## Material for one architecture mesh (walls/buildings) so each can animate
## its own build-up effect.
func new_arch_material() -> ShaderMaterial:
	var mat := arch_material.duplicate() as ShaderMaterial
	return mat
