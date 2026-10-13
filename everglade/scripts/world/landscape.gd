class_name Landscape
extends Node3D
## The world around the glade, so it never looks like an island:
##  * an endless ground ring that continues the terrain without a seam and
##    swells into soft hills toward the horizon, fading into haze
##  * a dense forest belt right up to the plot's edge (as in Tiny Glade, the
##    buildable square is a clearing in the woods), thinning into scattered
##    copses and lone trees over the far meadows
## Trees are drawn through one MultiMesh per kind (and per part).

const RADIUS := 420.0
const RINGS := 26
const SEGMENTS := 96

static var _noise: FastNoiseLite


## Height of the land outside the terrain: flat at the terrain's border so
## the two meet, rising into rolling hills with distance.
static func outer_height(x: float, z: float) -> float:
	if _noise == null:
		_noise = FastNoiseLite.new()
		_noise.seed = 77
		_noise.frequency = 0.012
		_noise.fractal_octaves = 3
	var d := maxf(absf(x), absf(z))
	var rise := smoothstep(Terrain.HALF, Terrain.HALF + 70.0, d)
	var hills := (_noise.get_noise_2d(x, z) * 0.5 + 0.5) * 16.0 + smoothstep(120.0, 380.0, Vector2(x, z).length()) * 18.0
	return Terrain.EDGE_LEVEL + hills * rise


var terrain: Terrain
var _ground: MeshInstance3D
var _forest: Node3D


func build(template: String, t: Terrain) -> void:
	terrain = t
	if _ground == null:
		_ground = MeshInstance3D.new()
		_ground.name = "OuterGround"
		_ground.mesh = _make_ground()
		var mat := ShaderMaterial.new()
		mat.shader = load("res://shaders/outer_ground.gdshader")
		ModelLib.apply_surface_textures(mat)
		mat.set_shader_parameter("play_half", Terrain.PLAY_HALF)
		_ground.material_override = mat
		_ground.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(_ground)
	if _forest:
		_forest.free()
	_forest = Node3D.new()
	_forest.name = "Forest"
	add_child(_forest)
	_plant_forest(template)


## A square-holed ground ring: its inner edge is the terrain border (shared
## heights there are EDGE_LEVEL), its outer edge far beyond the fog.
func _make_ground() -> ArrayMesh:
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var idx := PackedInt32Array()
	var inner := Terrain.HALF - 0.05
	for r in RINGS + 1:
		var t := float(r) / RINGS
		# rings get denser near the glade
		var f := t * t
		for s in SEGMENTS:
			var a := TAU * s / SEGMENTS
			var dir := Vector2(cos(a), sin(a))
			# square inner border -> circular far edge
			var sq := dir / maxf(absf(dir.x), absf(dir.y))
			var p := (sq * inner).lerp(dir * RADIUS, f)
			verts.append(Vector3(p.x, outer_height(p.x, p.y), p.y))
	for i in verts.size():
		var v := verts[i]
		var e := 1.5
		var dx := outer_height(v.x + e, v.z) - outer_height(v.x - e, v.z)
		var dz := outer_height(v.x, v.z + e) - outer_height(v.x, v.z - e)
		normals.append(Vector3(-dx, 2.0 * e, -dz).normalized())
	for r in RINGS:
		for s in SEGMENTS:
			var a := r * SEGMENTS + s
			var b := r * SEGMENTS + (s + 1) % SEGMENTS
			var c := a + SEGMENTS
			var d := b + SEGMENTS
			idx.append_array([a, c, b, b, c, d])
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh


func _ground_y(x: float, z: float) -> float:
	if absf(x) < Terrain.HALF and absf(z) < Terrain.HALF:
		return terrain.height_at(x, z)
	return outer_height(x, z)


func _plant_forest(template: String) -> void:
	var kinds: Array = ["tree_round_a", "tree_round_c", "tree_pine_a", "tree_pine_b", "tree_round_a", "tree_birch"]
	match template:
		"town", "hamlet":
			kinds = ["tree_round_a", "tree_golden", "tree_pine_a", "tree_round_c", "tree_orange", "tree_pine_b"]
		"village":
			kinds = ["tree_teal", "tree_blossom", "tree_pine_a", "tree_golden", "tree_teal", "tree_round_c"]
		"ruins":
			kinds = ["tree_round_a", "tree_round_c", "tree_golden", "tree_pine_b", "tree_round_a", "tree_birch"]
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(template) & 0xFFFF
	var placed: Dictionary = {}
	for k in kinds:
		placed[k] = []
	var edge := Terrain.PLAY_HALF + 1.2
	# --- dense belt hugging the plot (a clearing in the woods)
	var tries := 0
	var count := 0
	while count < 950 and tries < 9000:
		tries += 1
		var p := Vector2(rng.randf_range(-95.0, 95.0), rng.randf_range(-95.0, 95.0))
		var d := maxf(absf(p.x), absf(p.y))
		if d < edge:
			continue
		# density: thick near the clearing, thinning with distance, with glades
		var dens := 1.0 - smoothstep(edge + 10.0, 95.0, d) * 0.8
		dens *= 0.55 + (Landscape._noise.get_noise_2d(p.x * 3.0, p.y * 3.0) * 0.5 + 0.5) * 0.9
		if rng.randf() > dens:
			continue
		_place(placed, kinds, rng, p, rng.randf_range(1.0, 1.6) * lerpf(1.0, 1.5, smoothstep(edge, 60.0, d)))
		count += 1
	# --- copses and lone trees on the far meadows
	for c in 40:
		var a := rng.randf() * TAU
		var r := rng.randf_range(100.0, 300.0)
		var centre := Vector2(cos(a), sin(a)) * r
		for k in rng.randi_range(1, 7):
			var p2 := centre + Vector2(rng.randf_range(-12, 12), rng.randf_range(-12, 12))
			_place(placed, kinds, rng, p2, rng.randf_range(1.8, 2.8))
	for kind in placed:
		_commit(kind, placed[kind])


func _place(placed: Dictionary, kinds: Array, rng: RandomNumberGenerator, p: Vector2, s: float) -> void:
	var kind: String = kinds[rng.randi() % kinds.size()]
	var basis := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.9, 1.15), s))
	placed[kind].append(Transform3D(basis, Vector3(p.x, _ground_y(p.x, p.y) - 0.1, p.y)))


func _commit(kind: String, xforms: Array) -> void:
	if xforms.is_empty() or not ModelLib.has_model(kind):
		return
	var m := ModelLib.merged(kind, true)
	for part in ["solid", "leaves"]:
		if m[part] == null:
			continue
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = m[part]
		mm.instance_count = xforms.size()
		for i in xforms.size():
			mm.set_instance_transform(i, xforms[i])
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.material_override = m.leaf_mat if part == "leaves" else ModelLib.props_material
		# the near belt casts shadows onto the glade's edge; that's all we need
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_forest.add_child(mmi)
