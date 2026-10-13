class_name Ivy
extends RefCounted
## Climbing ivy that slowly creeps up walls and cottages over time.
##
## Each vine is a woody stem that wanders upwards with a little momentum,
## throws off side branches and carries heart-shaped leaves in several
## greens, alternating along the stem and turned out from the wall. Vines
## favour corners and wall ends, cover walls only partially, and grow from
## the root up: stem segments and leaves are ordered by their distance along
## the vine, so revealing a growing fraction of instances grows the ivy.

const LEAF_SIZE := 0.16
const STEM_COLOR := Color(0.62, 0.52, 0.32, 1.0)

static var _leaf: ArrayMesh
static var _stem: ArrayMesh


## A heart-shaped leaf pointing up +Y in the XY plane, slightly cupped, with
## a darker underside. Vertex alpha 0 = foliage channel (sways, seasons).
static func leaf_mesh() -> ArrayMesh:
	if _leaf:
		return _leaf
	var outline := [
		Vector2(0.0, 0.08), Vector2(-0.28, 0.0), Vector2(-0.52, 0.18), Vector2(-0.56, 0.48),
		Vector2(-0.4, 0.74), Vector2(-0.18, 0.92), Vector2(0.0, 1.12), Vector2(0.18, 0.92),
		Vector2(0.4, 0.74), Vector2(0.56, 0.48), Vector2(0.52, 0.18), Vector2(0.28, 0.0),
	]
	var mb := MeshBuilder.new()
	var c := Color(0.52, 0.70, 0.34, 0.0)
	var centre := Vector3(0, 0.5, 0.06)
	for i in outline.size():
		var p0: Vector2 = outline[i]
		var p1: Vector2 = outline[(i + 1) % outline.size()]
		var a := Vector3(p0.x, p0.y, 0.0)
		var b := Vector3(p1.x, p1.y, 0.0)
		# lighter towards the midrib, darker at the rim
		mb.tri_facing(centre, a, b, Vector3(0, 0, 1), c)
		mb.tri_facing(centre - Vector3(0, 0, 0.004), b, a, Vector3(0, 0, -1), c.darkened(0.25))
	_leaf = mb.commit()
	return _leaf


## Unit stem segment along +Y (scaled per instance).
static func stem_mesh() -> ArrayMesh:
	if _stem:
		return _stem
	var mb := MeshBuilder.new()
	mb.box(Transform3D(Basis.IDENTITY, Vector3(0, 0.5, 0)), Vector3(1.0, 1.0, 1.0), STEM_COLOR)
	_stem = mb.commit()
	return _stem


## faces: Array of {a, b (bottom corners), n (outward), h (height)}.
## Returns a node holding the stem and leaf MultiMeshes; grow it with
## set_growth().
static func build(faces: Array, seed_value: int, density := 1.0) -> Node3D:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var stems: Array = []   # [order, Transform3D]
	var leaves: Array = []  # [order, Transform3D, Color]
	for f in faces:
		var a: Vector3 = f.a
		var b: Vector3 = f.b
		var n: Vector3 = f.n
		var width := a.distance_to(b)
		if width < 0.6:
			continue
		var along := (b - a).normalized()
		var vines := int(width / 1.7 * density + rng.randf())
		for v in vines:
			# prefer corners and wall ends, otherwise anywhere along the face
			var t := rng.randf_range(0.03, 0.14) if rng.randf() < 0.45 else rng.randf_range(0.1, 0.9)
			if rng.randf() < 0.5:
				t = 1.0 - t
			var max_h: float = f.h * rng.randf_range(0.45, 1.0)
			var origin := a.lerp(b, t)
			_grow(stems, leaves, rng, origin, along, n, 0.0, 0.0, max_h, 0.0, 0, true)
	stems.sort_custom(func(l, r): return l[0] < r[0])
	leaves.sort_custom(func(l, r): return l[0] < r[0])
	var root := Node3D.new()
	root.name = "Ivy"
	var smm := MultiMesh.new()
	smm.transform_format = MultiMesh.TRANSFORM_3D
	smm.mesh = stem_mesh()
	smm.instance_count = stems.size()
	for i in stems.size():
		smm.set_instance_transform(i, stems[i][1])
	var lmm := MultiMesh.new()
	lmm.transform_format = MultiMesh.TRANSFORM_3D
	lmm.use_colors = true
	lmm.mesh = leaf_mesh()
	lmm.instance_count = leaves.size()
	for i in leaves.size():
		lmm.set_instance_transform(i, leaves[i][1])
		lmm.set_instance_color(i, leaves[i][2])
	for pair in [["Stems", smm], ["Leaves", lmm]]:
		var mmi := MultiMeshInstance3D.new()
		mmi.name = pair[0]
		mmi.multimesh = pair[1]
		mmi.material_override = ModelLib.grass_material
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		(pair[1] as MultiMesh).visible_instance_count = 0
		root.add_child(mmi)
	return root


## One vine (or branch) wandering up the wall from (x, y) in face space.
static func _grow(stems: Array, leaves: Array, rng: RandomNumberGenerator, origin: Vector3, along: Vector3, n: Vector3,
		x: float, y: float, max_h: float, order: float, depth: int, main: bool) -> void:
	var step := 0.11 if main else 0.09
	var dx := rng.randf_range(-0.3, 0.3) if main else (rng.randf_range(0.5, 0.95) * (1.0 if rng.randf() < 0.5 else -1.0))
	var length := max_h if main else rng.randf_range(0.35, 0.9)
	var travelled := 0.0
	var side := 1.0
	var thick := 0.034 if main else 0.02
	var wall_off := 0.075
	while travelled < length:
		# persistent, gently curving direction; branches arc back upwards
		dx = clampf(dx * 0.86 + rng.randf_range(-0.12, 0.12) + (0.0 if main else -dx * 0.05), -0.9, 0.9)
		var dy := sqrt(maxf(0.15, 1.0 - dx * dx))
		var nx := x + dx * step
		var ny := y + dy * step
		if ny > max_h:
			break
		var p0 := origin + along * x + Vector3.UP * y + n * wall_off
		var p1 := origin + along * nx + Vector3.UP * ny + n * wall_off
		var seg := p1 - p0
		var ydir := seg
		var xdir := n.cross(seg.normalized()).normalized() * thick
		stems.append([order, Transform3D(Basis(xdir, ydir, n * thick * 0.7), p0)])
		# leaves alternate along the stem, turned outwards and upwards
		if rng.randf() < 0.82:
			var lp := p1 + xdir.normalized() * side * rng.randf_range(0.02, 0.05) + n * 0.01
			var up_dir := (Vector3.UP * rng.randf_range(0.6, 1.0) + xdir.normalized() * side * rng.randf_range(0.3, 0.9)).normalized()
			var right := n.cross(up_dir).normalized()
			var tilt := rng.randf_range(0.25, 0.6)
			var face_n := (n * cos(tilt) - up_dir * sin(tilt)).normalized()
			var basis := Basis(right, up_dir, face_n).orthonormalized()
			basis = basis.scaled(Vector3.ONE * LEAF_SIZE * rng.randf_range(0.7, 1.35) * (1.0 if main else 0.85))
			var g := rng.randf()
			var col := Color(1, 1, 1)
			if g < 0.25:
				col = Color(1.15, 1.12, 0.85)   # young, lighter leaves
			elif g < 0.5:
				col = Color(0.78, 0.86, 0.82)   # deep green
			elif g < 0.58:
				col = Color(0.95, 1.0, 0.7)     # sun-yellowed
			leaves.append([order + 0.5, Transform3D(basis, lp), col * rng.randf_range(0.9, 1.08)])
			side = -side
		# side branches
		if depth < 2 and rng.randf() < (0.13 if main else 0.06):
			_grow(stems, leaves, rng, origin, along, n, nx, ny, max_h, order + 1.0, depth + 1, false)
		x = nx
		y = ny
		travelled += step
		order += 1.0


static func set_growth(ivy: Node, growth: float) -> void:
	if ivy == null:
		return
	for c in ivy.get_children():
		var mmi := c as MultiMeshInstance3D
		if mmi and mmi.multimesh:
			mmi.multimesh.visible_instance_count = int(mmi.multimesh.instance_count * clampf(growth, 0.0, 1.0))
