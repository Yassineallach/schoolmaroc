class_name GrassField
extends Node3D
## Scatters swaying grass tufts and wild flowers over the meadow, avoiding
## paths, water and building footprints. One MultiMesh per terrain chunk.

var terrain: Terrain
var _grass_mm: Array[MultiMeshInstance3D] = []
var _flower_mm: Array[MultiMeshInstance3D] = []
var _dirty: Dictionary = {}
var _grass_mesh: Mesh
var _flower_meshes: Array[Mesh] = []


func setup(t: Terrain) -> void:
	terrain = t
	_grass_mesh = ModelLib.merged("grass_tuft").solid
	for k in ["flowers_white", "flowers_yellow", "flowers_pink"]:
		_flower_meshes.append(ModelLib.merged(k).solid)
	for i in Terrain.CHUNKS * Terrain.CHUNKS:
		var g := MultiMeshInstance3D.new()
		g.material_override = ModelLib.grass_material
		g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		g.visibility_range_end = 60.0
		add_child(g)
		_grass_mm.append(g)
		var f := MultiMeshInstance3D.new()
		f.material_override = ModelLib.grass_material
		f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(f)
		_flower_mm.append(f)
	terrain.chunk_rebuilt.connect(func(cx, cz): _dirty[Vector2i(cx, cz)] = true)
	Settings.changed.connect(refresh_all)


func refresh_all() -> void:
	for cz in Terrain.CHUNKS:
		for cx in Terrain.CHUNKS:
			_dirty[Vector2i(cx, cz)] = true


func _process(_delta: float) -> void:
	var budget := 3
	for key in _dirty.keys():
		if budget <= 0:
			break
		_dirty.erase(key)
		_build(key.x, key.y)
		budget -= 1


func _build(cx: int, cz: int) -> void:
	var size := Terrain.CHUNK_CELLS * Terrain.CELL
	var x0 := -Terrain.HALF + cx * size
	var z0 := -Terrain.HALF + cz * size
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(Vector2i(cx, cz))
	var count := int(size * size * Settings.grass_density())
	var grass_xf: Array[Transform3D] = []
	var grass_col: PackedColorArray = []
	var flower_xf: Array = [[], [], []]
	for i in count:
		var x := x0 + rng.randf() * size
		var z := z0 + rng.randf() * size
		var edge := maxf(absf(x), absf(z))
		if edge > Terrain.PLAY_HALF + 6.0:
			continue
		var h := terrain.height_at(x, z)
		if h < Terrain.WATER_LEVEL + 0.12:
			continue
		var m := terrain.mask_at(x, z)
		if m.r > 0.25 or m.g > 0.25 or m.a > 0.25 or m.b > 0.55:
			continue
		var n := terrain.normal_at(x, z)
		if n.y < 0.7:
			continue
		var s := rng.randf_range(0.7, 1.35) * (1.0 - m.b * 0.6)
		var basis := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.9, 1.7), s))
		var xf := Transform3D(basis, Vector3(x, h - 0.02, z))
		if rng.randf() < 0.035:
			flower_xf[rng.randi() % 3].append(xf.scaled_local(Vector3.ONE * 0.8))
		else:
			grass_xf.append(xf)
			# same golden drifts as the terrain shader, plus per-tuft jitter
			var gold := smoothstep(0.58, 0.7, _fbm(Vector2(x, z) * 0.09 + Vector2(11.0, 11.0)))
			var c := Color(1, 1, 1).lerp(GOLD_TINT, gold * 0.85)
			c = c * rng.randf_range(0.9, 1.08)
			c.a = 1.0
			grass_col.append(c)
	var idx := cz * Terrain.CHUNKS + cx
	_grass_mm[idx].multimesh = _make_mm(_grass_mesh, grass_xf, grass_col)
	# flowers: one chunk-level multimesh per colour would be 3x the nodes, so
	# pick the colour by chunk hash and mix the rest into neighbouring chunks
	var pick := (cx * 7 + cz * 3) % 3
	var all: Array[Transform3D] = []
	for a in flower_xf:
		for t in a:
			all.append(t)
	_flower_mm[idx].multimesh = _make_mm(_flower_meshes[pick], all)


func _make_mm(mesh: Mesh, xforms: Array[Transform3D], colors: PackedColorArray = PackedColorArray()) -> MultiMesh:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = not colors.is_empty()
	mm.mesh = mesh
	mm.instance_count = xforms.size()
	for i in xforms.size():
		mm.set_instance_transform(i, xforms[i])
		if mm.use_colors:
			mm.set_instance_color(i, colors[i])
	return mm


# GDScript twin of the terrain shader's value noise so grass tints line up
# with the golden patches painted on the ground.
const GOLD_TINT := Color(1.45, 1.12, 0.62)


static func _hash12(p: Vector2) -> float:
	var p3 := Vector3(p.x, p.y, p.x) * 0.1031
	p3 = Vector3(p3.x - floorf(p3.x), p3.y - floorf(p3.y), p3.z - floorf(p3.z))
	p3 += Vector3.ONE * p3.dot(Vector3(p3.y, p3.z, p3.x) + Vector3.ONE * 33.33)
	var v := (p3.x + p3.y) * p3.z
	return v - floorf(v)


static func _noise(p: Vector2) -> float:
	var i := p.floor()
	var f := p - i
	var u := f * f * (Vector2(3, 3) - 2.0 * f)
	var a := lerpf(_hash12(i), _hash12(i + Vector2(1, 0)), u.x)
	var b := lerpf(_hash12(i + Vector2(0, 1)), _hash12(i + Vector2(1, 1)), u.x)
	return lerpf(a, b, u.y)


static func _fbm(p: Vector2) -> float:
	var v := 0.0
	var a := 0.5
	for i in 4:
		v += a * _noise(p)
		p *= 2.1
		a *= 0.5
	return v
