class_name Clutter
extends RefCounted
## Small cottage clutter modelled in code, so it needs no asset files:
## pumpkins, vegetables, a bread stall, anvil, fabric rolls, brooms, a door
## wreath, wheelbarrow, chairs, a birdhouse, flower pots, a doorbell,
## buckets, sacks, a beehive and a table. ModelLib serves them like any
## other prop kind (props, decor picker, thumbnails), and the Glade strews
## a few by new doors (Tiny Glade's clutter).

const KINDS := ["jack_o_lantern", "pumpkins", "veg_crate", "bread_stall", "anvil", "fabric_rolls", "broom_rack", "wreath",
		"wheelbarrow", "chair", "birdhouse", "flower_pots", "doorbell", "bucket", "sacks", "beehive", "table"]
## What turns up by a new door.
const DOORSTEP := ["pumpkins", "veg_crate", "broom_rack", "wheelbarrow", "chair", "flower_pots", "bucket", "sacks",
		"barrel", "crate", "hay_bale", "log_pile", "planter", "bench", "wreath"]

const M_PAINT := 0
const M_STONE := 1
const M_WOOD := 3
const M_CLOTH := 7
const M_METAL := 8
const M_STRAW := 11

const WOOD := Color(0.56, 0.41, 0.27)
const DARK_WOOD := Color(0.40, 0.29, 0.19)
const IRON := Color(0.24, 0.25, 0.28)


static func build(kind: String) -> ArrayMesh:
	var mb := MeshBuilder.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(kind)
	match kind:
		"jack_o_lantern":
			_gourd(mb, Vector3.ZERO, 0.3, Color(0.93, 0.5, 0.14))
		"pumpkins":
			for i in 3:
				var p := Vector3(rng.randf_range(-0.3, 0.3), 0, rng.randf_range(-0.3, 0.3)) if i > 0 else Vector3.ZERO
				var r := rng.randf_range(0.16, 0.26) if i > 0 else 0.3
				_gourd(mb, p, r, Color(0.92, 0.52, 0.16).lerp(Color(0.95, 0.75, 0.3), rng.randf() * 0.4))
		"veg_crate":
			_crate(mb, Vector3.ZERO, Vector3(0.62, 0.32, 0.42))
			var cols := [Color(0.9, 0.48, 0.15), Color(0.42, 0.62, 0.25), Color(0.75, 0.18, 0.16), Color(0.55, 0.32, 0.5)]
			for i in 9:
				var c: Color = cols[i % cols.size()]
				_ball(mb, Vector3(rng.randf_range(-0.22, 0.22), 0.3, rng.randf_range(-0.13, 0.13)), rng.randf_range(0.06, 0.09), c, 1.0)
		"bread_stall":
			_box(mb, Vector3(0, 0.78, 0), Vector3(1.6, 0.08, 0.8), WOOD, M_WOOD)
			for x in [-0.72, 0.72]:
				for z in [-0.32, 0.32]:
					_box(mb, Vector3(x, 0.39, z), Vector3(0.08, 0.78, 0.08), DARK_WOOD, M_WOOD)
				_box(mb, Vector3(x, 1.2, 0.36), Vector3(0.07, 0.9, 0.07), DARK_WOOD, M_WOOD)
			# striped awning
			for k in 8:
				var col := Color(0.86, 0.3, 0.26) if k % 2 == 0 else Color(0.96, 0.92, 0.84)
				var x0 := -0.8 + k * 0.2
				_quad2(mb, Vector3(x0, 1.7, -0.2), Vector3(x0 + 0.2, 1.7, -0.2), Vector3(x0 + 0.2, 1.5, 0.55), Vector3(x0, 1.5, 0.55), col, M_CLOTH)
			for i in 7:
				var lp := Vector3(-0.6 + i * 0.2, 0.86, rng.randf_range(-0.2, 0.2))
				_ball(mb, lp, 0.09, Color(0.82, 0.6, 0.32), 0.6, 1.7)
		"anvil":
			_box(mb, Vector3(0, 0.25, 0), Vector3(0.42, 0.5, 0.42), DARK_WOOD, M_WOOD)
			_box(mb, Vector3(0, 0.56, 0), Vector3(0.2, 0.12, 0.16), IRON, M_METAL)
			_box(mb, Vector3(0, 0.68, 0), Vector3(0.5, 0.12, 0.2), IRON, M_METAL)
			_box(mb, Vector3(0.3, 0.7, 0), Vector3(0.14, 0.07, 0.1), IRON, M_METAL)
		"fabric_rolls":
			var cols2 := [Color(0.72, 0.24, 0.24), Color(0.3, 0.42, 0.66), Color(0.86, 0.76, 0.42), Color(0.4, 0.58, 0.36), Color(0.9, 0.88, 0.82)]
			for i in 5:
				var a := -0.35 + i * 0.17
				_cyl(mb, Vector3(a, 0.0, 0.0), Vector3(a + 0.18, 0.95, 0.12), 0.08, cols2[i], M_CLOTH)
			_box(mb, Vector3(0.02, 0.85, 0.16), Vector3(1.0, 0.06, 0.06), WOOD, M_WOOD)
			for x in [-0.45, 0.48]:
				_box(mb, Vector3(x, 0.45, 0.16), Vector3(0.06, 0.9, 0.06), WOOD, M_WOOD)
		"broom_rack":
			_box(mb, Vector3(0, 0.9, 0), Vector3(0.9, 0.06, 0.08), WOOD, M_WOOD)
			for x in [-0.4, 0.4]:
				_box(mb, Vector3(x, 0.45, 0), Vector3(0.06, 0.9, 0.06), WOOD, M_WOOD)
			for i in 3:
				var bx := -0.22 + i * 0.22
				_cyl(mb, Vector3(bx, 0.25, 0.06), Vector3(bx + 0.02, 1.25, 0.04), 0.022, DARK_WOOD, M_WOOD)
				_cyl(mb, Vector3(bx, 0.0, 0.07), Vector3(bx, 0.3, 0.07), 0.09, Color(0.82, 0.68, 0.38), M_STRAW, 0.05)
		"wreath":
			# a straw door wreath on a little easel
			for x in [-0.2, 0.2]:
				_cyl(mb, Vector3(x, 0, 0.1), Vector3(x * 0.4, 1.0, -0.02), 0.025, WOOD, M_WOOD)
			for i in 14:
				var a2 := TAU * i / 14.0
				_ball(mb, Vector3(cos(a2) * 0.2, 0.72 + sin(a2) * 0.2, 0.05), 0.07, Color(0.82, 0.66, 0.36) if i % 3 else Color(0.42, 0.56, 0.3), 0.7)
			_ball(mb, Vector3(0, 0.52, 0.08), 0.05, Color(0.8, 0.2, 0.2), 1.0)
		"wheelbarrow":
			_box(mb, Vector3(0, 0.42, 0), Vector3(0.6, 0.06, 0.9), WOOD, M_WOOD)
			for x in [-0.3, 0.3]:
				_box(mb, Vector3(x, 0.55, 0), Vector3(0.05, 0.24, 0.9), WOOD, M_WOOD)
				_box(mb, Vector3(x * 0.8, 0.42, -0.75), Vector3(0.05, 0.05, 0.7), DARK_WOOD, M_WOOD)
				_box(mb, Vector3(x * 0.8, 0.2, 0.2), Vector3(0.05, 0.4, 0.05), DARK_WOOD, M_WOOD)
			_box(mb, Vector3(0, 0.55, 0.45), Vector3(0.6, 0.24, 0.05), WOOD, M_WOOD)
			_cyl(mb, Vector3(-0.04, 0.2, 0.5), Vector3(0.04, 0.2, 0.5), 0.2, DARK_WOOD, M_WOOD)
			for i in 4:
				_ball(mb, Vector3(rng.randf_range(-0.18, 0.18), 0.55, rng.randf_range(-0.3, 0.3)), 0.12, Color(0.86, 0.5, 0.16), 0.8)
		"chair":
			_box(mb, Vector3(0, 0.45, 0), Vector3(0.44, 0.05, 0.42), WOOD, M_WOOD)
			for x in [-0.19, 0.19]:
				for z in [-0.18, 0.18]:
					_box(mb, Vector3(x, 0.22, z), Vector3(0.05, 0.45, 0.05), DARK_WOOD, M_WOOD)
				_box(mb, Vector3(x, 0.72, -0.19), Vector3(0.05, 0.55, 0.05), DARK_WOOD, M_WOOD)
			for y in [0.66, 0.84]:
				_box(mb, Vector3(0, y, -0.19), Vector3(0.4, 0.07, 0.03), WOOD, M_WOOD)
		"birdhouse":
			_box(mb, Vector3(0, 0.8, 0), Vector3(0.07, 1.6, 0.07), DARK_WOOD, M_WOOD)
			_box(mb, Vector3(0, 1.75, 0), Vector3(0.3, 0.32, 0.3), Color(0.72, 0.5, 0.36), M_WOOD)
			_quad2(mb, Vector3(-0.2, 1.88, -0.2), Vector3(0.0, 2.05, -0.2), Vector3(0.0, 2.05, 0.22), Vector3(-0.2, 1.88, 0.22), Color(0.6, 0.3, 0.24), M_WOOD)
			_quad2(mb, Vector3(0.2, 1.88, -0.2), Vector3(0.0, 2.05, -0.2), Vector3(0.0, 2.05, 0.22), Vector3(0.2, 1.88, 0.22), Color(0.6, 0.3, 0.24), M_WOOD)
			_ball(mb, Vector3(0, 1.78, 0.155), 0.05, Color(0.1, 0.08, 0.06), 1.0, 0.2)
		"flower_pots":
			for i in 3:
				var pp := Vector3(-0.25 + i * 0.25, 0, rng.randf_range(-0.08, 0.08))
				var pr := rng.randf_range(0.09, 0.13)
				_cyl(mb, pp, pp + Vector3.UP * pr * 1.8, pr, Color(0.72, 0.4, 0.28), M_STONE, pr * 0.75)
				for k in 5:
					_ball(mb, pp + Vector3(rng.randf_range(-0.07, 0.07), pr * 1.8 + 0.06, rng.randf_range(-0.07, 0.07)), 0.05,
							[Color(0.9, 0.36, 0.5), Color(0.96, 0.86, 0.4), Color(0.45, 0.65, 0.3)][k % 3], 1.0)
		"doorbell":
			_box(mb, Vector3(0, 0.9, 0), Vector3(0.08, 1.8, 0.08), DARK_WOOD, M_WOOD)
			_box(mb, Vector3(0, 1.75, 0.15), Vector3(0.05, 0.05, 0.36), IRON, M_METAL)
			_cyl(mb, Vector3(0, 1.45, 0.3), Vector3(0, 1.7, 0.3), 0.11, Color(0.82, 0.64, 0.3), M_METAL, 0.05)
		"bucket":
			_cyl(mb, Vector3.ZERO, Vector3(0, 0.3, 0), 0.15, WOOD, M_WOOD, 0.18)
			_cyl(mb, Vector3(0, 0.08, 0), Vector3(0, 0.1, 0), 0.165, IRON, M_METAL)
			_cyl(mb, Vector3(0, 0.24, 0), Vector3(0, 0.26, 0), 0.18, IRON, M_METAL)
		"sacks":
			for i in 3:
				var sp := Vector3(-0.22 + i * 0.25, 0, rng.randf_range(-0.1, 0.1))
				_ball(mb, sp + Vector3.UP * 0.22, 0.2, Color(0.82, 0.74, 0.56), 0.9, 1.3)
				_cyl(mb, sp + Vector3.UP * 0.45, sp + Vector3.UP * 0.55, 0.05, Color(0.7, 0.6, 0.42), M_CLOTH)
		"beehive":
			_box(mb, Vector3(0, 0.2, 0), Vector3(0.5, 0.4, 0.5), WOOD, M_WOOD)
			for k in 4:
				var r2 := 0.32 - k * 0.06
				_cyl(mb, Vector3(0, 0.4 + k * 0.13, 0), Vector3(0, 0.53 + k * 0.13, 0), r2, Color(0.86, 0.72, 0.4), M_STRAW, r2 - 0.04)
		"table":
			_box(mb, Vector3(0, 0.74, 0), Vector3(1.3, 0.07, 0.7), WOOD, M_WOOD)
			for x in [-0.56, 0.56]:
				for z in [-0.28, 0.28]:
					_box(mb, Vector3(x, 0.37, z), Vector3(0.07, 0.74, 0.07), DARK_WOOD, M_WOOD)
			_cyl(mb, Vector3(-0.3, 0.78, 0), Vector3(-0.3, 0.95, 0), 0.06, Color(0.7, 0.45, 0.3), M_STONE, 0.05)
			_ball(mb, Vector3(0.25, 0.83, 0.05), 0.09, Color(0.82, 0.6, 0.32), 0.6, 1.6)
	return mb.commit()


## Glowing parts (lit at night by glow.gdshader), or null.
static func build_glow(kind: String) -> ArrayMesh:
	if kind != "jack_o_lantern":
		return null
	# a carved face: two eyes and a toothy grin, glowing candle-orange
	var mb := MeshBuilder.new()
	var c := Color(1.0, 0.62, 0.2, 1.0)
	var z := 0.36
	var n := Vector3(0, 0, 1)
	for ex in [-0.11, 0.11]:
		mb.tri_facing(Vector3(ex - 0.06, 0.28, z), Vector3(ex + 0.06, 0.28, z), Vector3(ex, 0.38, z - 0.01), n, c)
	var pts := [Vector3(-0.17, 0.17, z - 0.01), Vector3(-0.1, 0.12, z), Vector3(-0.05, 0.16, z), Vector3(0.0, 0.11, z),
			Vector3(0.05, 0.16, z), Vector3(0.1, 0.12, z), Vector3(0.17, 0.17, z - 0.01)]
	for i in pts.size() - 1:
		var a: Vector3 = pts[i]
		var b: Vector3 = pts[i + 1]
		mb.quad_facing(a, b, b + Vector3.DOWN * 0.07, a + Vector3.DOWN * 0.07, n, c)
	return mb.commit()


static func _box(mb: MeshBuilder, at: Vector3, size: Vector3, col: Color, layer: int) -> void:
	Ornaments._box(mb, Transform3D(Basis.IDENTITY, at), size, Color(col.r, col.g, col.b, 1.0), layer)


static func _quad2(mb: MeshBuilder, a: Vector3, b: Vector3, c: Vector3, d: Vector3, col: Color, layer: int) -> void:
	Ornaments._two_sided(mb, a, b, c, d, Color(col.r, col.g, col.b, 1.0), layer)


## A low-poly ellipsoid (squash < 1 flattens it, stretch > 1 lengthens it in x).
static func _ball(mb: MeshBuilder, c: Vector3, r: float, col: Color, squash := 1.0, stretch := 1.0) -> void:
	var start := mb.verts.size()
	var rings := 5
	var segs := 8
	var sc := Vector3(r * stretch, r * squash, r)
	for i in rings:
		var a0 := PI * float(i) / rings - PI * 0.5
		var a1 := PI * float(i + 1) / rings - PI * 0.5
		for k in segs:
			var b0 := TAU * k / segs
			var b1 := TAU * (k + 1) / segs
			var p00 := Vector3(cos(a0) * cos(b0), sin(a0), cos(a0) * sin(b0))
			var p01 := Vector3(cos(a0) * cos(b1), sin(a0), cos(a0) * sin(b1))
			var p10 := Vector3(cos(a1) * cos(b0), sin(a1), cos(a1) * sin(b0))
			var p11 := Vector3(cos(a1) * cos(b1), sin(a1), cos(a1) * sin(b1))
			mb.quad_facing(c + p00 * sc, c + p01 * sc, c + p11 * sc, c + p10 * sc, ((p00 + p11) * 0.5).normalized(),
					Color(col.r, col.g, col.b, 1.0), p00, p01, p11, p10)
	Ornaments._layer(mb, start, M_PAINT)


## A pumpkin: a squashed, ribbed ball with a stalk.
static func _gourd(mb: MeshBuilder, c: Vector3, r: float, col: Color) -> void:
	for k in 6:
		var a := TAU * k / 6.0
		_ball(mb, c + Vector3(cos(a) * r * 0.35, r * 0.75, sin(a) * r * 0.35), r * 0.7, col.darkened(0.06 * (k % 2)), 0.95)
	_cyl(mb, c + Vector3.UP * r * 1.4, c + Vector3(0.03, r * 1.75, 0), r * 0.12, Color(0.4, 0.45, 0.2), M_WOOD)


## A tapered cylinder from a to b (radius r at a, r_top at b; -1 = same).
static func _cyl(mb: MeshBuilder, a: Vector3, b: Vector3, r: float, col: Color, layer: int, r_top := -1.0) -> void:
	var start := mb.verts.size()
	if r_top < 0.0:
		r_top = r
	var axis := (b - a).normalized()
	var u := axis.cross(Vector3.FORWARD if absf(axis.z) < 0.9 else Vector3.RIGHT).normalized()
	var v := axis.cross(u)
	var segs := 8
	var c := Color(col.r, col.g, col.b, 1.0)
	for k in segs:
		var t0 := TAU * k / segs
		var t1 := TAU * (k + 1) / segs
		var d0 := u * cos(t0) + v * sin(t0)
		var d1 := u * cos(t1) + v * sin(t1)
		mb.quad_facing(a + d0 * r, a + d1 * r, b + d1 * r_top, b + d0 * r_top, (d0 + d1).normalized(), c, d0, d1, d1, d0)
		mb.tri_facing(b, b + d0 * r_top, b + d1 * r_top, axis, c)
		mb.tri_facing(a, a + d1 * r, a + d0 * r, -axis, c)
	Ornaments._layer(mb, start, layer)


static func _crate(mb: MeshBuilder, at: Vector3, size: Vector3) -> void:
	_box(mb, at + Vector3.UP * size.y * 0.5, size, WOOD, M_WOOD)
	for y in [0.06, size.y - 0.06]:
		_box(mb, at + Vector3(0, y, size.z * 0.5 + 0.01), Vector3(size.x, 0.06, 0.02), DARK_WOOD, M_WOOD)
		_box(mb, at + Vector3(0, y, -size.z * 0.5 - 0.01), Vector3(size.x, 0.06, 0.02), DARK_WOOD, M_WOOD)
