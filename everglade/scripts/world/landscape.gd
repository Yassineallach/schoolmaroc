class_name Landscape
extends Node3D
## The world around the glade, so it never looks like an island:
##  * an endless ground ring that continues the terrain without a seam and
##    swells into soft hills toward the horizon, fading into haze
##  * a compact forest of real trees all around, as in Tiny Glade, where the
##    buildable square is a clearing in deep woods: packed mixed trees from
##    the clearing's edge, then the cheapest trees (firs) further out,
##    fading into the haze over the hills.
## To stay fast, trees are batched per kind into map tiles: tiles out of
## view are culled, far tiles stop drawing inside the fog, nothing casts
## shadows, and the forest is shallower on the Battery graphics preset.

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


const TILE := 26.0            # forest batching tile (metres)
## Forest depth beyond the clearing's edge for Battery / Balanced / Beautiful.
const DEPTH := [26.0, 36.0, 46.0]


func _plant_forest(template: String) -> void:
	var kinds: Array = ["tree_round_a", "tree_round_c", "tree_pine_a", "tree_pine_b", "tree_round_a", "tree_birch"]
	match template:
		"town", "hamlet":
			kinds = ["tree_round_a", "tree_golden", "tree_pine_a", "tree_round_c", "tree_orange", "tree_pine_b"]
		"village":
			kinds = ["tree_teal", "tree_blossom", "tree_pine_a", "tree_golden", "tree_teal", "tree_round_c"]
		"ruins":
			kinds = ["tree_round_a", "tree_round_c", "tree_golden", "tree_pine_b", "tree_round_a", "tree_birch"]
	var far_kinds: Array = ["tree_pine_a", "tree_pine_b", "tree_pine_a", kinds[0]]
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(template) & 0xFFFF
	var placed: Dictionary = {}   # kind -> {tile key -> [xforms]}
	var edge := Terrain.PLAY_HALF + 1.2
	var depth: float = DEPTH[clampi(Settings.quality, 0, 2)]
	var near := edge + depth
	# --- packed mixed woods from the clearing's edge (jittered grid)
	_fill(placed, kinds, rng, edge, near, 2.25, Vector2(1.15, 1.65), 0.95)
	# --- the deep woods: firs (the cheapest trees), bigger, into the haze
	_fill(placed, far_kinds, rng, near - 1.0, near + 34.0, 3.3, Vector2(1.6, 2.3), 0.9)
	for kind in placed:
		_commit_tiles(kind, placed[kind], near)


## Packs trees on a jittered grid over the square band inner..outer.
func _fill(placed: Dictionary, kinds: Array, rng: RandomNumberGenerator, inner: float, outer: float,
		step: float, scale_range: Vector2, keep: float) -> void:
	var x := -outer
	while x <= outer:
		var z := -outer
		while z <= outer:
			var p := Vector2(x, z) + Vector2(rng.randf_range(-0.38, 0.38), rng.randf_range(-0.38, 0.38)) * step
			z += step
			var d := maxf(absf(p.x), absf(p.y))
			if d < inner or d > outer or rng.randf() > keep:
				continue
			# the front rows step up from smaller trees so the edge reads as a wall of woods
			var front := 1.0 - smoothstep(inner, inner + 3.5, d)
			var s := rng.randf_range(scale_range.x, scale_range.y) * lerpf(1.0, 0.82, front)
			var kind: String = kinds[rng.randi() % kinds.size()]
			var basis := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.9, 1.15), s))
			var key := Vector2i(floori(p.x / TILE), floori(p.y / TILE))
			if not placed.has(kind):
				placed[kind] = {}
			if not placed[kind].has(key):
				placed[kind][key] = []
			placed[kind][key].append(Transform3D(basis, Vector3(p.x, _ground_y(p.x, p.y) - 0.1, p.y)))
		x += step


## One MultiMesh per kind, part and tile: tiles cull off screen, and tiles
## deep in the woods stop drawing where the fog has swallowed them.
func _commit_tiles(kind: String, tiles: Dictionary, near: float) -> void:
	if not ModelLib.has_model(kind):
		return
	var m := ModelLib.merged(kind, true)
	for key in tiles:
		var xforms: Array = tiles[key]
		var centre := (Vector2(key) + Vector2(0.5, 0.5)) * TILE
		var far := maxf(absf(centre.x), absf(centre.y)) > near
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
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			# trunks hide under the canopy from afar; far tiles fade into the fog
			mmi.visibility_range_end = (110.0 if far else 160.0) if part == "leaves" else (80.0 if far else 120.0)
			_forest.add_child(mmi)
