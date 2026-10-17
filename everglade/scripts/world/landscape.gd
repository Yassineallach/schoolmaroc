class_name Landscape
extends Node3D
## The world around the glade, so it never looks like an island:
##  * an endless ground ring that continues the terrain without a seam and
##    swells into soft hills toward the horizon, fading into haze
##  * a forest of real trees all around, as in Tiny Glade, where the
##    buildable square is a clearing in deep woods. Every tree kind grows
##    in it, in groves of 2-6: packed at the clearing's edge, opening up
##    behind, and carrying on over the hills to the horizon, softened by
##    the camera blur and the haze.
## To stay fast, trees are batched per kind into map tiles that cull off
## screen, distant tiles use automatic detail levels and skip the trunks
## hidden under their crowns, nothing casts shadows, and the woods end
## nearer on the Battery graphics preset.

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
## Where each band of woods ends for Battery / Balanced / Beautiful: the
## packed woods at the clearing's edge, the open woods behind them, and the
## far woods over the hills to the horizon.
const NEAR := [24.0, 32.0, 42.0]
const MID := 120.0
const HORIZON := [200.0, 260.0, 300.0]
## Every broadleaf kind we have (no cone-shaped firs).
const ALL_TREES := ["tree_round_a", "tree_round_b", "tree_round_c", "tree_birch", "tree_blossom", "tree_golden",
		"tree_orange", "tree_teal"]

static var _lod_meshes: Dictionary = {}


func _plant_forest(template: String) -> void:
	# every tree kind grows in every glade; the template picks which lead
	var lead: Array = ["tree_round_a", "tree_round_c", "tree_round_b", "tree_birch"]
	match template:
		"town", "hamlet":
			lead = ["tree_round_a", "tree_golden", "tree_round_c", "tree_orange"]
		"village":
			lead = ["tree_teal", "tree_blossom", "tree_round_a", "tree_golden"]
		"ruins":
			lead = ["tree_round_c", "tree_round_b", "tree_golden", "tree_birch"]
	var weights: Dictionary = {}
	for kind in ALL_TREES:
		weights[kind] = 3.0 if kind in lead else 1.0
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(template) & 0xFFFF
	var q := clampi(Settings.quality, 0, 2)
	var edge := Terrain.PLAY_HALF + 1.2
	var near: float = edge + NEAR[q]
	var horizon: float = HORIZON[q]
	var placed: Dictionary = {}   # kind -> {tile key -> [xforms]}
	_groves(placed, rng, weights, edge, near, 4.4, Vector2(1.1, 1.6))
	_groves(placed, rng, weights, near, MID, 7.0, Vector2(1.4, 2.1))
	_groves(placed, rng, weights, MID, horizon, 11.0, Vector2(2.0, 2.9))
	for kind in placed:
		_commit_tiles(kind, placed[kind], near)


## Plants groves of 2-6 trees over the square band inner..outer: grove
## centres on a jittered grid (spacing step), each grove mostly one kind
## around a taller leader, with the odd tree of another kind mixed in.
func _groves(placed: Dictionary, rng: RandomNumberGenerator, weights: Dictionary, inner: float, outer: float,
		step: float, scale_range: Vector2) -> void:
	var total := 0.0
	for kind in weights:
		total += weights[kind]
	var x := -outer
	while x <= outer:
		var z := -outer
		while z <= outer:
			var c := Vector2(x, z) + Vector2(rng.randf_range(-0.4, 0.4), rng.randf_range(-0.4, 0.4)) * step
			z += step
			var dc := maxf(absf(c.x), absf(c.y))
			if dc < inner - step * 0.5 or dc > outer + step * 0.5:
				continue
			var kind := _pick(rng, weights, total)
			var count := rng.randi_range(2, 6)
			var spread := step * (0.22 + 0.06 * count)
			for i in count:
				var p := c
				if i > 0:
					var a := rng.randf() * TAU
					p += Vector2(cos(a), sin(a)) * spread * sqrt(rng.randf_range(0.15, 1.0))
				var d := maxf(absf(p.x), absf(p.y))
				if d < inner or d >= outer:
					continue
				# the front rows step up from smaller trees so the edge reads as a wall of woods
				var front := 1.0 - smoothstep(inner, inner + 3.5, d)
				var s := rng.randf_range(scale_range.x, scale_range.y) * lerpf(1.0, 0.82, front)
				if i == 0:
					s *= 1.12
				var k := kind if rng.randf() < 0.8 else _pick(rng, weights, total)
				var basis := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.9, 1.15), s))
				var key := Vector2i(floori(p.x / TILE), floori(p.y / TILE))
				if not placed.has(k):
					placed[k] = {}
				if not placed[k].has(key):
					placed[k][key] = []
				placed[k][key].append(Transform3D(basis, Vector3(p.x, _ground_y(p.x, p.y) - 0.1, p.y)))
		x += step


func _pick(rng: RandomNumberGenerator, weights: Dictionary, total: float) -> String:
	var r := rng.randf() * total
	for kind in weights:
		r -= weights[kind]
		if r <= 0.0:
			return kind
	return weights.keys()[0]


## One MultiMesh per kind, part and tile: tiles cull off screen, trees past
## the packed woods use meshes with automatic detail levels (simplified
## only where the camera blur and haze soften them), and far trunks, hidden
## under the crowns, aren't drawn at all.
func _commit_tiles(kind: String, tiles: Dictionary, near: float) -> void:
	if not ModelLib.has_model(kind):
		return
	var m := ModelLib.merged(kind, true)
	for key in tiles:
		var xforms: Array = tiles[key]
		var centre := (Vector2(key) + Vector2(0.5, 0.5)) * TILE
		var d := maxf(absf(centre.x), absf(centre.y))
		for part in ["solid", "leaves"]:
			if m[part] == null:
				continue
			# trunks hide under the crowns far away
			if part == "solid" and d > MID and m.leaves != null:
				continue
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = m[part] if d <= near + TILE * 0.5 else _lod_mesh(kind, part, m[part])
			mm.instance_count = xforms.size()
			for i in xforms.size():
				mm.set_instance_transform(i, xforms[i])
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = mm
			mmi.material_override = m.leaf_mat if part == "leaves" else ModelLib.props_material
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			if d <= MID:
				# trunks hide under the canopy from afar
				mmi.visibility_range_end = 220.0 if part == "leaves" else 140.0
			# behind the camera blur and the haze, simpler detail levels can't
			# be told apart: let them kick in sooner there
			if d > MID:
				mmi.lod_bias = 0.15
			elif d > near + TILE:
				mmi.lod_bias = 0.4
			_forest.add_child(mmi)


## The same tree mesh with automatic level-of-detail versions. Light meshes
## are kept whole: simplifying them leaves thin spikes.
static func _lod_mesh(kind: String, part: String, src: ArrayMesh) -> ArrayMesh:
	var key := kind + "/" + part
	var tris := 0
	for s in src.get_surface_count():
		var n := src.surface_get_array_index_len(s)
		tris += (n if n > 0 else src.surface_get_array_len(s)) / 3
	if tris < 200:
		return src
	if not _lod_meshes.has(key):
		var im := ImporterMesh.new()
		for s in src.get_surface_count():
			im.add_surface(src.surface_get_primitive_type(s), src.surface_get_arrays(s), [], {}, src.surface_get_material(s))
		im.generate_lods(60.0, 0.0, [])
		_lod_meshes[key] = im.get_mesh()
	return _lod_meshes[key]
