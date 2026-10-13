class_name GrassField
extends Node3D
## Lush meadow grass in the style of a hand-tended diorama: a dense carpet of
## thin curved blades (procedural "patches" of blades instanced through one
## MultiMesh per terrain chunk) plus taller wild tufts and dotted flowers.
## Blades avoid paths, water and building footprints, grow shorter on
## trodden ground and taller in the golden wild drifts. Colour, wind and
## lighting live in shaders/grass.gdshader.

const PATCH_BLADES := 36
const PATCH_RADIUS := 0.5
const TALL_BLADES := 16
const MAX_PUSHERS := 8
## Hand-modelled grass clumps (Quaternius Stylized Nature, CC0), converted by
## tools/import_quaternius.py so their vertex colours carry the same
## random/along-the-blade data as the procedural blades.
const CLUMPS := ["q_grass_short", "q_grass_tall", "q_grass_wispy", "q_grass_wide"]

var terrain: Terrain
var material: ShaderMaterial
var _grass_mm: Array[MultiMeshInstance3D] = []
var _tall_mm: Array[MultiMeshInstance3D] = []
var _flower_mm: Array[MultiMeshInstance3D] = []
var _dirty: Dictionary = {}
var _patch_mesh: ArrayMesh
var _tall_mesh: ArrayMesh
var _flower_meshes: Array[Mesh] = []
var _density := 0.0


func setup(t: Terrain) -> void:
	terrain = t
	material = ShaderMaterial.new()
	material.shader = load("res://shaders/grass.gdshader")
	_patch_mesh = _clump_patch(CLUMPS, 7, 0.42, 101)
	if _patch_mesh == null:
		_patch_mesh = _make_patch(PATCH_BLADES, PATCH_RADIUS, Vector2(0.13, 0.28), 101)
	_tall_mesh = _clump_patch(["q_grass_wild"], 2, 0.16, 202)
	if _tall_mesh == null:
		_tall_mesh = _make_patch(TALL_BLADES, 0.22, Vector2(0.38, 0.7), 202)
	for k in ["flowers_white", "flowers_yellow", "flowers_pink"]:
		_flower_meshes.append(ModelLib.merged(k).solid)
	for i in Terrain.CHUNKS * Terrain.CHUNKS:
		var g := _new_mmi(material, 40.0)
		_grass_mm.append(g)
		_tall_mm.append(_new_mmi(material, 40.0))
		var f := _new_mmi(ModelLib.grass_material, 0.0)
		_flower_mm.append(f)
	terrain.chunk_rebuilt.connect(func(cx, cz): _dirty[Vector2i(cx, cz)] = true)
	Settings.changed.connect(func():
		# only a new grass density needs the meadow rebuilt
		if not is_equal_approx(Settings.grass_density(), _density):
			_density = Settings.grass_density()
			refresh_all())
	_density = Settings.grass_density()


func _new_mmi(mat: Material, range_end: float) -> MultiMeshInstance3D:
	var m := MultiMeshInstance3D.new()
	m.material_override = mat
	m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if range_end > 0.0:
		m.visibility_range_end = range_end
	add_child(m)
	return m


func refresh_all() -> void:
	for cz in Terrain.CHUNKS:
		for cx in Terrain.CHUNKS:
			_dirty[Vector2i(cx, cz)] = true


## World positions (xyz) and radii (w) of creatures that part the grass.
func set_pushers(list: Array) -> void:
	var arr: Array[Vector4] = []
	for p in list:
		if arr.size() >= MAX_PUSHERS:
			break
		arr.append(p)
	var n := arr.size()
	while arr.size() < MAX_PUSHERS:
		arr.append(Vector4.ZERO)
	material.set_shader_parameter("pushers", arr)
	material.set_shader_parameter("pusher_count", n)


func _process(_delta: float) -> void:
	var budget := 3
	for key in _dirty.keys():
		if budget <= 0:
			break
		_dirty.erase(key)
		_build(key.x, key.y)
		budget -= 1


## A patch made of several modelled grass clumps scattered in a disc, or
## null when the models are missing (procedural blades are used instead).
static func _clump_patch(kinds: Array, count: int, radius: float, seed_value: int) -> ArrayMesh:
	var meshes: Array[Mesh] = []
	for k in kinds:
		var path := "res://assets/models/%s.glb" % k
		if not ResourceLoader.exists(path):
			return null
		var scene := (load(path) as PackedScene).instantiate()
		var mi := _first_mesh(scene)
		if mi:
			meshes.append(mi.mesh)
		scene.free()
	if meshes.is_empty():
		return null
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var st := SurfaceTool.new()
	for i in count:
		var a := rng.randf() * TAU
		var r := sqrt((i + rng.randf()) / count) * radius
		var s := rng.randf_range(0.8, 1.2)
		var basis := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.85, 1.2), s))
		st.append_from(meshes[i % meshes.size()], 0, Transform3D(basis, Vector3(cos(a) * r, 0.0, sin(a) * r)))
	var mesh := st.commit()
	mesh.custom_aabb = AABB(Vector3(-1.2, -0.2, -1.2), Vector3(2.4, 1.4, 2.4))
	return mesh


static func _first_mesh(n: Node) -> MeshInstance3D:
	if n is MeshInstance3D:
		return n
	for c in n.get_children():
		var m := _first_mesh(c)
		if m:
			return m
	return null


## One clump of curved, tapered blades. Vertex COLOR carries per-blade data
## for the shader: r = random, g = position along the blade (0 root, 1 tip).
static func _make_patch(blades: int, radius: float, height: Vector2, seed_value: int) -> ArrayMesh:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var cols := PackedColorArray()
	var uvs := PackedVector2Array()
	var uv2s := PackedVector2Array()
	var idx := PackedInt32Array()
	for b in blades:
		var a := rng.randf() * TAU
		# evenly spread (stratified rings) so overlapping patches form a carpet
		var r := sqrt((b + rng.randf()) / blades) * radius
		var root := Vector3(cos(a) * r, 0.0, sin(a) * r)
		var face := rng.randf() * TAU
		var side := Vector3(cos(face), 0.0, sin(face))
		var lean_a := rng.randf() * TAU
		var lean := Vector3(cos(lean_a), 0.0, sin(lean_a))
		var h := rng.randf_range(height.x, height.y)
		var lean_amt := rng.randf_range(0.15, 0.45) * h
		var w0 := rng.randf_range(0.026, 0.042) * (1.0 + h * 0.5)
		var rnd := rng.randf()
		var n := side.cross(Vector3.UP).normalized() + Vector3.UP * 0.35
		n = n.normalized()
		var base := verts.size()
		for t in [0.0, 0.55]:
			var c: Vector3 = root + Vector3.UP * (h * t) + lean * (lean_amt * t * t)
			var w: float = w0 * pow(1.0 - t, 0.6)
			verts.append(c - side * w)
			verts.append(c + side * w)
			for k in 2:
				norms.append(n)
				cols.append(Color(rnd, t, h, 1.0))
				# UV.x = signed half-width, UV2 = blade's side direction, so the
				# shader can thin blades up close and widen them far away
				uvs.append(Vector2(-w if k == 0 else w, t))
				uv2s.append(Vector2(side.x, side.z))
		verts.append(root + Vector3.UP * h + lean * lean_amt)
		norms.append(n)
		cols.append(Color(rnd, 1.0, h, 1.0))
		uvs.append(Vector2(0.0, 1.0))
		uv2s.append(Vector2(side.x, side.z))
		# root pair 0/1, mid pair 2/3, tip 4
		for tri in [[0, 1, 2], [1, 3, 2], [2, 3, 4]]:
			for v in tri:
				idx.append(base + v)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = norms
	arrays[Mesh.ARRAY_COLOR] = cols
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_TEX_UV2] = uv2s
	arrays[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mesh.custom_aabb = AABB(Vector3(-radius - 0.6, -0.2, -radius - 0.6), Vector3(radius * 2.0 + 1.2, height.y + 0.4, radius * 2.0 + 1.2))
	return mesh


func _build(cx: int, cz: int) -> void:
	var size := Terrain.CHUNK_CELLS * Terrain.CELL
	var x0 := -Terrain.HALF + cx * size
	var z0 := -Terrain.HALF + cz * size
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(Vector2i(cx, cz))
	var count := int(size * size * Settings.grass_density())
	var grass_xf: Array[Transform3D] = []
	var tall_xf: Array[Transform3D] = []
	var flower_xf: Array[Transform3D] = []
	for i in count:
		var x := x0 + rng.randf() * size
		var z := z0 + rng.randf() * size
		var edge := maxf(absf(x), absf(z))
		if edge > Terrain.PLAY_HALF + 4.0:
			continue
		var h := terrain.height_at(x, z)
		if h < Terrain.WATER_LEVEL + 0.12:
			continue
		var m := terrain.mask_at(x, z)
		if m.r > 0.3 or m.g > 0.3 or m.a > 0.3 or m.b > 0.7:
			continue
		var n := terrain.normal_at(x, z)
		if n.y < 0.68:
			continue
		var wild := smoothstep(0.58, 0.7, _fbm(Vector2(x, z) * 0.09 + Vector2(11.0, 11.0)))
		# mown near buildings and path edges, shaggier in the wild drifts
		var tall := (1.0 - m.b * 0.65) * (1.0 - maxf(m.r, maxf(m.g, m.a)) * 0.8) * (0.85 + wild * 0.5)
		tall *= 0.8 + _noise(Vector2(x, z) * 0.6) * 0.45
		var s := rng.randf_range(0.85, 1.2)
		var basis := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * tall, s))
		var xf := Transform3D(basis, Vector3(x, h - 0.03, z))
		grass_xf.append(xf)
		var r := rng.randf()
		# wildflowers grow in loose drifts rather than evenly sprinkled
		var drift := smoothstep(0.5, 0.72, _noise(Vector2(x, z) * 0.32 + Vector2(5.0, 9.0)))
		if r < 0.002 + drift * 0.05:
			flower_xf.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * 0.75), Vector3(x, h - 0.02, z)))
		elif r < 0.02 + wild * 0.08 and m.b < 0.2:
			tall_xf.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(1, rng.randf_range(0.8, 1.25), 1)), Vector3(x, h - 0.03, z)))
	var idx := cz * Terrain.CHUNKS + cx
	_grass_mm[idx].multimesh = _make_mm(_patch_mesh, grass_xf)
	_tall_mm[idx].multimesh = _make_mm(_tall_mesh, tall_xf)
	_flower_mm[idx].multimesh = _make_mm(_flower_meshes[(cx * 7 + cz * 3) % 3], flower_xf)


func _make_mm(mesh: Mesh, xforms: Array[Transform3D]) -> MultiMesh:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = xforms.size()
	for i in xforms.size():
		mm.set_instance_transform(i, xforms[i])
	return mm


# GDScript twin of the meadow shader's value noise so grass height follows
# the golden wild drifts painted on the ground.
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
