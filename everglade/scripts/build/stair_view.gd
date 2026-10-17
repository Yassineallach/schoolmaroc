class_name StairView
extends Node3D
## Stairs drawn along a line (Tiny Glade's stair tool): straight or curving,
## wrapped round a tower into a spiral, from the ground or a wall top up to
## a flat roof. Height runs from y0 at the first point to y1 at the last.
## How steep it gets decides what is built:
##  * nearly level: a landing / walkway deck
##  * a normal rise: steps (solid stone blocks down to the ground, or timber
##    treads on stringers and posts)
##  * very steep: a ladder
## Railings line the sides once it is high enough; "float" leaves out the
## supports and hangs a few levitating rocks under it instead.

const RISE := 0.19          # target step height (m)
const LADDER_SLOPE := 1.35  # rise per run beyond which it becomes a ladder

const STONE := Color(0.80, 0.76, 0.68)
const WOOD := Color(0.72, 0.54, 0.31)   # Tiny Glade honey wood, #B88A50

var data: Dictionary
var body: StaticBody3D
var perches: Array[Vector3] = []
var kind := "steps"   # steps | deck | ladder


func build(d: Dictionary, terrain: Terrain, preview := false) -> void:
	data = d
	for c in get_children():
		c.free()
	perches.clear()
	var pts: PackedVector2Array = d.pts
	if pts.size() < 2:
		return
	var total := Geo.length(pts)
	if total < 0.2:
		return
	var y0: float = d.get("y0", 0.0)
	var y1: float = d.get("y1", 1.0)
	var w: float = d.get("w", 1.2)
	var wood: bool = d.get("mat", "stone") == "wood"
	var floating: bool = d.get("float", false)
	var dy := y1 - y0
	var mb := MeshBuilder.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = int(d.get("id", 1)) * 977 + 5
	if absf(dy) < 0.22:
		kind = "deck"
	elif absf(dy) / total > LADDER_SLOPE:
		kind = "ladder"
	else:
		kind = "steps"
	match kind:
		"deck":
			_deck(mb, pts, total, y0, y1, w, wood, floating, terrain)
		"ladder":
			_ladder(mb, pts, total, y0, y1, w, terrain)
		_:
			_steps(mb, pts, total, y0, y1, w, wood, floating, terrain, rng)
	if kind != "ladder" and d.get("rail", true):
		_railings(mb, pts, total, y0, y1, w, wood, terrain)
	var mi := MeshInstance3D.new()
	mi.name = "Mesh"
	mi.mesh = mb.commit()
	mi.material_override = ModelLib.props_material
	add_child(mi)
	if floating and not preview:
		_levitation(pts, total, y0, y1, w, terrain, rng)
	if preview or mi.mesh.get_surface_count() == 0:
		return
	body = StaticBody3D.new()
	body.collision_layer = 2
	body.set_meta("kind", "stairs")
	body.set_meta("id", d.id)
	var cs := CollisionShape3D.new()
	cs.shape = mi.mesh.create_trimesh_shape()
	body.add_child(cs)
	add_child(body)


## Height of the walking surface at arclength s (steps are quantised).
static func height_at(d: Dictionary, s: float) -> float:
	var pts: PackedVector2Array = d.pts
	var total := maxf(0.01, Geo.length(pts))
	var y0: float = d.get("y0", 0.0)
	var y1: float = d.get("y1", 1.0)
	return lerpf(y0, y1, clampf(s / total, 0.0, 1.0))


func _steps(mb: MeshBuilder, pts: PackedVector2Array, total: float, y0: float, y1: float, w: float,
		wood: bool, floating: bool, terrain: Terrain, rng: RandomNumberGenerator) -> void:
	var dy := y1 - y0
	var n := maxi(1, int(round(absf(dy) / RISE)))
	var run := total / n
	var up := dy > 0.0
	for i in n:
		var s0 := run * i
		var s1 := run * (i + 1)
		var top := y0 + dy * float(i + 1) / n if up else y0 + dy * float(i) / n
		var sm := (s0 + s1) * 0.5
		var p := Geo.point_at(pts, sm)
		var t := Geo.tangent_at(pts, sm)
		var basis := DecoMerge.along(Vector3(t.x, 0, t.y))
		# a little overlap so curved flights close up on their outer edge
		var depth := run + 0.06
		if wood:
			var shade := 0.9 + 0.1 * rng.randf()
			_box(mb, Transform3D(basis, Vector3(p.x, top - 0.035, p.y)), Vector3(depth, 0.07, w), WOOD * shade, Ornaments.M_WOOD)
		else:
			var g := terrain.height_at_v(p)
			var bottom := top - 0.32 if floating else minf(g - 0.1, top - 0.2)
			var c := STONE.darkened(rng.randf_range(0.0, 0.08))
			_box(mb, Transform3D(basis, Vector3(p.x, (top + bottom) * 0.5, p.y)), Vector3(depth, top - bottom, w), c, Ornaments.M_STONE)
			# a proud nosing on each tread
			_box(mb, Transform3D(basis, Vector3(p.x, top - 0.03, p.y)), Vector3(depth + 0.04, 0.06, w + 0.06), c.lightened(0.05), Ornaments.M_STONE)
		perches.append(Vector3(p.x, top, p.y))
	if wood:
		# stringers along both sides, posts down to the ground
		var side_n := 10 if total > 2.0 else 5
		for sgn in [-1.0, 1.0]:
			var prev := Vector3.INF
			for k in side_n + 1:
				var s := total * k / side_n
				var p2 := Geo.point_at(pts, s)
				var t2 := Geo.tangent_at(pts, s)
				var side: Vector2 = Vector2(-t2.y, t2.x) * (w * 0.5 + 0.04) * sgn
				var y := lerpf(y0, y1, s / total) - 0.12
				var at := Vector3(p2.x + side.x, y, p2.y + side.y)
				if prev != Vector3.INF:
					_beam(mb, prev, at, 0.06, 0.2, WOOD.darkened(0.15))
				prev = at
		if not floating:
			var post_n := maxi(1, int(total / 1.6))
			for k in post_n + 1:
				var s3 := total * k / post_n
				var p3 := Geo.point_at(pts, s3)
				var t3 := Geo.tangent_at(pts, s3)
				var y3 := lerpf(y0, y1, s3 / total) - 0.2
				for sgn2 in [-1.0, 1.0]:
					var sp: Vector2 = p3 + Vector2(-t3.y, t3.x) * (w * 0.5 + 0.04) * sgn2
					var g3 := terrain.height_at_v(sp)
					if y3 - g3 > 0.25:
						_box(mb, Transform3D(Basis.IDENTITY, Vector3(sp.x, (y3 + g3) * 0.5, sp.y)), Vector3(0.12, y3 - g3 + 0.1, 0.12), WOOD.darkened(0.2), Ornaments.M_WOOD)


func _deck(mb: MeshBuilder, pts: PackedVector2Array, total: float, y0: float, y1: float, w: float,
		wood: bool, floating: bool, terrain: Terrain) -> void:
	var dense := Geo.resample(pts, 0.4)
	var acc := 0.0
	for i in dense.size() - 1:
		var a := dense[i]
		var b := dense[i + 1]
		var l := a.distance_to(b)
		var mid := (a + b) * 0.5
		var y := lerpf(y0, y1, (acc + l * 0.5) / total)
		acc += l
		var basis := DecoMerge.along(Vector3(b.x - a.x, 0, b.y - a.y))
		var g := terrain.height_at_v(mid)
		if wood:
			_box(mb, Transform3D(basis, Vector3(mid.x, y - 0.04, mid.y)), Vector3(l + 0.03, 0.08, w), WOOD * (0.92 + 0.08 * float(i % 2)), Ornaments.M_WOOD)
		else:
			var bottom := y - 0.35 if floating or y - g > 0.9 else g - 0.1
			_box(mb, Transform3D(basis, Vector3(mid.x, (y + bottom) * 0.5, mid.y)), Vector3(l + 0.03, y - bottom, w), STONE, Ornaments.M_STONE)
		perches.append(Vector3(mid.x, y, mid.y))
	if floating:
		return
	# posts or pillars carry a raised walkway
	var post_n := maxi(1, int(total / 2.2))
	for k in post_n + 1:
		var s := total * k / post_n
		var p := Geo.point_at(pts, s)
		var y2 := lerpf(y0, y1, s / total) - (0.08 if wood else 0.35)
		var g2 := terrain.height_at_v(p)
		if y2 - g2 > 0.3:
			var size := Vector3(0.16, y2 - g2 + 0.1, 0.16) if wood else Vector3(0.45, y2 - g2 + 0.1, 0.45)
			_box(mb, Transform3D(Basis.IDENTITY, Vector3(p.x, (y2 + g2) * 0.5, p.y)), size,
					WOOD.darkened(0.2) if wood else STONE.darkened(0.06), Ornaments.M_WOOD if wood else Ornaments.M_STONE)


func _ladder(mb: MeshBuilder, pts: PackedVector2Array, total: float, y0: float, y1: float, w: float, terrain: Terrain) -> void:
	var lw := minf(w, 0.7)
	var a := pts[0]
	var b := pts[pts.size() - 1]
	var lo := Vector3(a.x, y0, a.y) if y0 < y1 else Vector3(b.x, y1, b.y)
	var hi := Vector3(b.x, y1, b.y) if y0 < y1 else Vector3(a.x, y0, a.y)
	lo.y = minf(lo.y, terrain.height_at(lo.x, lo.z))
	var flat := Vector3(hi.x - lo.x, 0, hi.z - lo.z)
	var side := (flat.cross(Vector3.UP).normalized() if flat.length() > 0.05 else Vector3.RIGHT) * lw * 0.5
	for sgn in [-1.0, 1.0]:
		_beam(mb, lo + side * sgn, hi + side * sgn + Vector3.UP * 0.6, 0.07, 0.09, WOOD.darkened(0.1))
	var rungs := maxi(2, int((hi.y + 0.6 - lo.y) / 0.3))
	for k in range(1, rungs):
		var p := lo.lerp(hi + Vector3.UP * 0.6, float(k) / rungs)
		_beam(mb, p - side, p + side, 0.045, 0.045, WOOD)
	perches.append(hi + Vector3.UP * 0.6)


## Posts and a handrail on both sides wherever the drop is worth guarding.
func _railings(mb: MeshBuilder, pts: PackedVector2Array, total: float, y0: float, y1: float, w: float, wood: bool,
		terrain: Terrain) -> void:
	var col := WOOD.darkened(0.1) if wood else Color(0.22, 0.22, 0.25)
	var layer := Ornaments.M_WOOD if wood else Ornaments.M_METAL
	var n := maxi(1, int(total / 0.9))
	for sgn in [-1.0, 1.0]:
		var prev := Vector3.INF
		for k in n + 1:
			var s := total * k / n
			var p := Geo.point_at(pts, s)
			var t := Geo.tangent_at(pts, s)
			var sp: Vector2 = p + Vector2(-t.y, t.x) * (w * 0.5 - 0.06) * sgn
			var y := lerpf(y0, y1, s / total)
			if y - terrain.height_at_v(sp) < 0.7:
				prev = Vector3.INF
				continue
			var foot := Vector3(sp.x, y, sp.y)
			_box(mb, Transform3D(Basis.IDENTITY, foot + Vector3.UP * 0.45), Vector3(0.06, 0.9, 0.06), col, layer)
			var top := foot + Vector3.UP * 0.92
			if prev != Vector3.INF:
				_beam(mb, prev, top, 0.06, 0.05, col)
			prev = top


## A few rocks bobbing under floating stairs, with glittering motes.
func _levitation(pts: PackedVector2Array, total: float, y0: float, y1: float, w: float, terrain: Terrain, rng: RandomNumberGenerator) -> void:
	var rocks := Node3D.new()
	rocks.name = "Levitation"
	add_child(rocks)
	var count := maxi(2, int(total / 1.6))
	for k in count:
		var s := total * (k + 0.5) / count
		var p := Geo.point_at(pts, s)
		var y := lerpf(y0, y1, s / total) - rng.randf_range(0.7, 1.3)
		var mi := MeshInstance3D.new()
		var m := ModelLib.merged(["rock_a", "rock_b", "rock_c"][k % 3])
		mi.mesh = m.solid
		mi.material_override = ModelLib.props_material
		mi.position = Vector3(p.x + rng.randf_range(-0.3, 0.3) * w, y, p.y + rng.randf_range(-0.3, 0.3) * w)
		mi.rotation = Vector3(rng.randf() * TAU, rng.randf() * TAU, 0)
		mi.scale = Vector3.ONE * rng.randf_range(0.35, 0.6)
		rocks.add_child(mi)
		var tw := mi.create_tween().set_loops()
		var amp := rng.randf_range(0.08, 0.16)
		tw.tween_property(mi, "position:y", y + amp, rng.randf_range(1.6, 2.4)).set_trans(Tween.TRANS_SINE)
		tw.tween_property(mi, "position:y", y - amp, rng.randf_range(1.6, 2.4)).set_trans(Tween.TRANS_SINE)
	var motes := CPUParticles3D.new()
	motes.amount = 16
	motes.lifetime = 2.5
	var mid := Geo.point_at(pts, total * 0.5)
	motes.position = Vector3(mid.x, lerpf(y0, y1, 0.5) - 0.6, mid.y)
	motes.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	motes.emission_box_extents = Vector3(total * 0.4, 0.4, total * 0.4)
	motes.gravity = Vector3(0, 0.15, 0)
	motes.scale_amount_min = 0.5
	motes.scale_amount_max = 1.0
	var q := QuadMesh.new()
	q.size = Vector2(0.06, 0.06)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	mat.albedo_color = Color(1.0, 0.95, 0.7)
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.9, 0.6)
	q.material = mat
	motes.mesh = q
	add_child(motes)


func _beam(mb: MeshBuilder, a: Vector3, b: Vector3, wdt: float, ht: float, col: Color) -> void:
	var d := b - a
	if d.length() < 0.01:
		return
	var fwd := d.normalized()
	var up := Vector3.UP if absf(fwd.y) < 0.95 else Vector3.RIGHT
	var basis := Basis.looking_at(fwd, up)
	_box(mb, Transform3D(basis, (a + b) * 0.5), Vector3(wdt, ht, d.length()), col, Ornaments.M_WOOD if col.r > 0.3 else Ornaments.M_METAL)


static func _box(mb: MeshBuilder, xf: Transform3D, size: Vector3, col: Color, layer: int) -> void:
	Ornaments._box(mb, xf, size, Color(col.r, col.g, col.b, 1.0), layer)


func play_build_anim() -> void:
	scale = Vector3(1, 0.01, 1)
	var tw := create_tween()
	tw.tween_property(self, "scale", Vector3.ONE, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func set_ivy(_growth: float) -> void:
	pass
