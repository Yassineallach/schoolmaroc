class_name Ornaments
extends RefCounted
## Small procedural decorations drawn with the shared prop material: arched,
## round and arrow-slit windows, flags on poles, hanging banners, bunting
## and laundry lines. Shapes are cached; pieces that span two points (lines,
## bunting) are built on demand.
## Vertex colour alpha is the prop channel (1 solid) and UV.x picks the
## surface material layer, as in blender/build_assets.py.

const M_PAINT := 0
const M_STONE := 1
const M_WOOD := 3
const M_CLOTH := 7
const M_METAL := 8

const STONE := Color(0.80, 0.76, 0.68)
const WOOD := Color(0.60, 0.45, 0.28)
const IRON := Color(0.20, 0.21, 0.24)
const GOLD := Color(0.86, 0.68, 0.30)
const GLASS := Color(1.0, 0.86, 0.6, 0.5)   # alpha 0.5: window glass in glow.gdshader

## Flag and banner colour pairs (field, charge) and the designs they're drawn in.
const PAIRS := [
	[Color(0.62, 0.16, 0.16), Color(0.95, 0.82, 0.42)], [Color(0.16, 0.30, 0.58), Color(0.95, 0.93, 0.86)],
	[Color(0.20, 0.42, 0.26), Color(0.95, 0.82, 0.42)], [Color(0.92, 0.88, 0.80), Color(0.66, 0.18, 0.18)],
	[Color(0.40, 0.22, 0.48), Color(0.95, 0.82, 0.42)], [Color(0.86, 0.62, 0.20), Color(0.24, 0.20, 0.30)],
]
const DESIGNS := 6
const PATTERNS := 36   # PAIRS x DESIGNS

static var _cache: Dictionary = {}


## {solid: ArrayMesh, glow: ArrayMesh} for a window type, centred like the
## kit window frame (origin at the opening's middle, +Z out of the wall).
static func window(kind: String) -> Dictionary:
	if _cache.has(kind):
		return _cache[kind]
	var mb := MeshBuilder.new()
	var gl := MeshBuilder.new()
	match kind:
		"arched":
			_arched(mb, gl)
		"round":
			_round(mb, gl)
		"slit":
			_slit(mb, gl)
	var out := {"solid": mb.commit(), "glow": gl.commit()}
	_cache[kind] = out
	return out


## A flag flying from a pole whose foot is at the origin.
static func flag(pattern: int) -> ArrayMesh:
	var key := "flag%d" % pattern
	if _cache.has(key):
		return _cache[key]
	var mb := MeshBuilder.new()
	var h := 2.1
	_box(mb, Transform3D(Basis(), Vector3(0, h * 0.5, 0)), Vector3(0.07, h, 0.07), WOOD, M_WOOD)
	_box(mb, Transform3D(Basis(), Vector3(0, h + 0.06, 0)), Vector3(0.13, 0.13, 0.13), GOLD, M_METAL)
	_cloth(mb, Vector3(0.04, h - 0.05, 0), Vector3(1.0, 0, 0), Vector3(0, -0.62, 0), pattern, 0.07, false)
	var m := mb.commit()
	_cache[key] = m
	return m


## A banner hanging from an iron rod that sticks out of a wall (+Z out).
static func banner(pattern: int) -> ArrayMesh:
	var key := "banner%d" % pattern
	if _cache.has(key):
		return _cache[key]
	var mb := MeshBuilder.new()
	_box(mb, Transform3D(Basis(), Vector3(0, 0, 0.32)), Vector3(0.04, 0.04, 0.64), IRON, M_METAL)
	_box(mb, Transform3D(Basis(), Vector3(0, -0.02, 0.6)), Vector3(0.74, 0.05, 0.05), WOOD, M_WOOD)
	_cloth(mb, Vector3(-0.32, -0.04, 0.6), Vector3(0.64, 0, 0), Vector3(0, -1.35, 0), pattern, 0.0, true)
	var m := mb.commit()
	_cache[key] = m
	return m


## Sagging rope from a to b with a row of washing hung on it.
static func laundry(a: Vector3, b: Vector3, seed_value: int) -> ArrayMesh:
	var mb := MeshBuilder.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var span := a.distance_to(b)
	var sag := 0.08 + span * 0.05
	_rope(mb, a, b, sag)
	var cols := [Color(0.95, 0.94, 0.9), Color(0.72, 0.82, 0.9), Color(0.9, 0.74, 0.72), Color(0.86, 0.84, 0.62),
			Color(0.7, 0.8, 0.66), Color(0.82, 0.74, 0.86)]
	var n := maxi(2, int(span / 0.75))
	var dir := (b - a).normalized()
	var side := dir.cross(Vector3.UP).normalized()
	for i in n:
		var t := (i + 0.5 + rng.randf_range(-0.2, 0.2)) / n
		if rng.randf() < 0.15:
			continue
		var p := a.lerp(b, t) + Vector3.DOWN * (sag * 4.0 * t * (1.0 - t))
		var w := rng.randf_range(0.28, 0.5)
		var h := rng.randf_range(0.3, 0.62)
		var col: Color = cols[rng.randi() % cols.size()]
		var c0 := p - dir * w * 0.5
		var c1 := p + dir * w * 0.5
		var lean := side * rng.randf_range(-0.04, 0.04)
		_two_sided(mb, c0, c1, c1 + Vector3.DOWN * h + lean, c0 + Vector3.DOWN * h * rng.randf_range(0.85, 1.0) + lean, col, M_CLOTH)
	return mb.commit()


## Rope with little triangular pennants between two flags or banners.
static func bunting(a: Vector3, b: Vector3, seed_value: int) -> ArrayMesh:
	var mb := MeshBuilder.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var span := a.distance_to(b)
	var sag := 0.1 + span * 0.06
	_rope(mb, a, b, sag)
	var dir := (b - a).normalized()
	var pair: Array = PAIRS[rng.randi() % PAIRS.size()]
	var n := maxi(2, int(span / 0.42))
	for i in n:
		var t0 := (i + 0.1) / n
		var t1 := (i + 0.9) / n
		var p0 := a.lerp(b, t0) + Vector3.DOWN * (sag * 4.0 * t0 * (1.0 - t0))
		var p1 := a.lerp(b, t1) + Vector3.DOWN * (sag * 4.0 * t1 * (1.0 - t1))
		var tip := (p0 + p1) * 0.5 + Vector3.DOWN * 0.3
		var col: Color = pair[i % 2]
		var nrm := dir.cross(Vector3.UP).normalized()
		mb.tri_facing(p0, p1, tip, nrm, col)
		mb.tri_facing(p0, p1, tip, -nrm, col)
		_layer(mb, mb.verts.size() - 6, M_CLOTH)
	return mb.commit()


## A stone archway (origin at the middle of its foot, +Z out of the wall):
## voussoirs round a dark passage, doubled with a centre pier when wide.
## `grate` fills the opening with iron bars (a water gate).
static func portal(w: float, h: float, grate := false) -> ArrayMesh:
	var key := "portal%.2f_%.2f_%s" % [w, h, grate]
	if _cache.has(key):
		return _cache[key]
	var mb := MeshBuilder.new()
	var spans: Array = [[0.0, w]]
	if w > 2.8:
		var half := (w - 0.5) * 0.5
		spans = [[-(half + 0.5) * 0.5, half], [(half + 0.5) * 0.5, half]]
		_box(mb, Transform3D(Basis.IDENTITY, Vector3(0, (h - half * 0.5) * 0.5, 0.08)), Vector3(0.5, h - half * 0.5, 0.3), STONE, M_STONE)
	for sp in spans:
		var cx: float = sp[0]
		var sw: float = sp[1]
		var r := sw * 0.5
		var spring := maxf(0.6, h - r)
		var t := 0.22
		var dark := Color(0.06, 0.055, 0.05)
		# the dark passage: a rectangle and a fan up into the arch
		var n := Vector3(0, 0, 1)
		var z := 0.02
		var start := mb.verts.size()
		mb.quad_facing(Vector3(cx - r, 0, z), Vector3(cx + r, 0, z), Vector3(cx + r, spring, z), Vector3(cx - r, spring, z), n, dark)
		for i in 12:
			var a0 := PI * i / 12.0
			var a1 := PI * (i + 1) / 12.0
			mb.tri_facing(Vector3(cx, spring, z), Vector3(cx + cos(a0) * r, spring + sin(a0) * r, z), Vector3(cx + cos(a1) * r, spring + sin(a1) * r, z), n, dark)
		_layer(mb, start, M_PAINT)
		# jamb blocks, alternating long and short
		var y := 0.0
		var k := 0
		while y < spring - 0.05:
			var bh := minf(0.42, spring - y)
			var bw := 0.32 if k % 2 == 0 else 0.22
			for sgn in [-1.0, 1.0]:
				_box(mb, Transform3D(Basis.IDENTITY, Vector3(cx + sgn * (r + bw * 0.5), y + bh * 0.5, 0.06)), Vector3(bw, bh - 0.02, 0.2), STONE.darkened(0.03 * (k % 3)), M_STONE)
			y += bh
			k += 1
		# voussoirs and keystone
		var segs := maxi(7, int(r * 7.0)) | 1
		for i in segs:
			var a0 := PI * float(i) / segs
			var a1 := PI * float(i + 1) / segs
			var am := (a0 + a1) * 0.5
			var rr := r + t * 0.5
			var key_stone := i == segs / 2
			var size := Vector3(rr * (a1 - a0) * 1.04, t * (1.35 if key_stone else 1.0), 0.22 if not key_stone else 0.28)
			_box(mb, Transform3D(Basis(Vector3(0, 0, 1), am - PI * 0.5), Vector3(cx + cos(am) * rr, spring + sin(am) * rr, 0.07)), size, STONE.lightened(0.04 if key_stone else 0.0), M_STONE)
		if grate:
			var bars := maxi(3, int(sw / 0.2))
			for b in bars:
				var bx := cx - r + sw * (b + 0.5) / bars
				var top := spring + sqrt(maxf(0.0, r * r - (bx - cx) * (bx - cx)))
				_box(mb, Transform3D(Basis.IDENTITY, Vector3(bx, top * 0.5, 0.1)), Vector3(0.04, top, 0.04), IRON, M_METAL)
			for yy in [spring * 0.35, spring * 0.75]:
				_box(mb, Transform3D(Basis.IDENTITY, Vector3(cx, yy, 0.1)), Vector3(sw, 0.05, 0.05), IRON, M_METAL)
	var m := mb.commit()
	_cache[key] = m
	return m


## A twiggy bird nest with three pale blue eggs (origin at its base).
static func nest() -> ArrayMesh:
	if _cache.has("nest"):
		return _cache["nest"]
	var mb := MeshBuilder.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = 41
	for i in 18:
		var a := TAU * i / 18.0
		var r := 0.16 + rng.randf_range(-0.02, 0.02)
		var p := Vector3(cos(a) * r, 0.05 + rng.randf_range(-0.02, 0.03), sin(a) * r)
		var basis := Basis(Vector3.UP, -a + rng.randf_range(-0.4, 0.4)) * Basis(Vector3.RIGHT, rng.randf_range(-0.3, 0.3))
		var c := Color(0.45, 0.34, 0.22).lerp(Color(0.62, 0.52, 0.34), rng.randf())
		_box(mb, Transform3D(basis, p), Vector3(0.03, 0.04, 0.16), c, M_WOOD)
	_box(mb, Transform3D(Basis.IDENTITY, Vector3(0, 0.02, 0)), Vector3(0.28, 0.04, 0.28), Color(0.4, 0.3, 0.2), M_WOOD)
	for e in 3:
		var a2 := TAU * e / 3.0
		var start := mb.verts.size()
		mb.box(Transform3D(Basis(Vector3.UP, a2), Vector3(cos(a2) * 0.05, 0.07, sin(a2) * 0.05)), Vector3(0.05, 0.06, 0.04), Color(0.72, 0.84, 0.86))
		_layer(mb, start, M_PAINT)
	var m := mb.commit()
	_cache["nest"] = m
	return m


## Colour of a flag's cloth at (u along the fly, v down the hoist), 0..1.
static func pattern_color(pattern: int, u: float, v: float) -> Color:
	var pair: Array = PAIRS[posmod(pattern, PAIRS.size())]
	var field: Color = pair[0]
	var charge: Color = pair[1]
	match int(posmod(pattern, PATTERNS) / PAIRS.size()):
		0:   # plain with a border
			return charge if u < 0.08 or u > 0.92 or v < 0.1 or v > 0.9 else field
		1:   # horizontal stripes
			return charge if int(v * 5.0) % 2 == 1 else field
		2:   # Nordic cross
			return charge if absf(u - 0.38) < 0.09 or absf(v - 0.5) < 0.1 else field
		3:   # per pale
			return charge if u > 0.5 else field
		4:   # roundel
			return charge if Vector2((u - 0.5) * 1.5, v - 0.5).length() < 0.27 else field
		_:   # chevron
			var k := absf(v - 0.5) - u * 0.6
			return charge if k < 0.0 and k > -0.2 else field


# ---------------------------------------------------------------------------
static func _arched(mb: MeshBuilder, gl: MeshBuilder) -> void:
	var hw := 0.42      # half width of the opening
	var y0 := -0.6
	var spring := 0.42   # where the arch starts
	var t := 0.13        # stone surround
	var d := 0.16
	# jambs and sill
	_box(mb, Transform3D(Basis(), Vector3(-hw - t * 0.5, (y0 + spring) * 0.5, d * 0.5)), Vector3(t, spring - y0, d), STONE, M_STONE)
	_box(mb, Transform3D(Basis(), Vector3(hw + t * 0.5, (y0 + spring) * 0.5, d * 0.5)), Vector3(t, spring - y0, d), STONE, M_STONE)
	_box(mb, Transform3D(Basis(), Vector3(0, y0 - 0.05, d * 0.6)), Vector3(hw * 2 + t * 2 + 0.1, 0.1, d * 1.2), STONE, M_STONE)
	# voussoirs round the head
	var segs := 7
	for i in segs:
		var a0 := PI * float(i) / segs
		var a1 := PI * float(i + 1) / segs
		var am := (a0 + a1) * 0.5
		var r := hw + t * 0.5
		var p := Vector3(cos(am) * r, spring + sin(am) * r, d * 0.5)
		var basis := Basis(Vector3(0, 0, 1), am - PI * 0.5)
		_box(mb, Transform3D(basis, p), Vector3(r * (a1 - a0) * 1.08, t, d), STONE, M_STONE)
	# glazing bars
	_box(mb, Transform3D(Basis(), Vector3(0, (y0 + spring + hw) * 0.5, 0.05)), Vector3(0.035, spring + hw - y0, 0.03), WOOD, M_WOOD)
	_box(mb, Transform3D(Basis(), Vector3(0, spring - 0.05, 0.05)), Vector3(hw * 2, 0.035, 0.03), WOOD, M_WOOD)
	# glass: rectangle plus a fan up into the arch
	var n := Vector3(0, 0, 1)
	gl.quad_facing(Vector3(-hw, y0, 0.03), Vector3(hw, y0, 0.03), Vector3(hw, spring, 0.03), Vector3(-hw, spring, 0.03), n, GLASS)
	for i in 10:
		var a0 := PI * float(i) / 10.0
		var a1 := PI * float(i + 1) / 10.0
		gl.tri_facing(Vector3(0, spring, 0.03), Vector3(cos(a0) * hw, spring + sin(a0) * hw, 0.03),
				Vector3(cos(a1) * hw, spring + sin(a1) * hw, 0.03), n, GLASS)


static func _round(mb: MeshBuilder, gl: MeshBuilder) -> void:
	var r := 0.4
	var t := 0.12
	var d := 0.16
	var cy := 0.25
	var segs := 12
	for i in segs:
		var a0 := TAU * float(i) / segs
		var a1 := TAU * float(i + 1) / segs
		var am := (a0 + a1) * 0.5
		var rr := r + t * 0.5
		_box(mb, Transform3D(Basis(Vector3(0, 0, 1), am - PI * 0.5), Vector3(cos(am) * rr, cy + sin(am) * rr, d * 0.5)),
				Vector3(rr * (a1 - a0) * 1.1, t, d), STONE, M_STONE)
	_box(mb, Transform3D(Basis(), Vector3(0, cy, 0.05)), Vector3(r * 2, 0.035, 0.03), WOOD, M_WOOD)
	_box(mb, Transform3D(Basis(), Vector3(0, cy, 0.05)), Vector3(0.035, r * 2, 0.03), WOOD, M_WOOD)
	var n := Vector3(0, 0, 1)
	for i in 14:
		var a0 := TAU * float(i) / 14.0
		var a1 := TAU * float(i + 1) / 14.0
		gl.tri_facing(Vector3(0, cy, 0.03), Vector3(cos(a0) * r, cy + sin(a0) * r, 0.03), Vector3(cos(a1) * r, cy + sin(a1) * r, 0.03), n, GLASS)


static func _slit(mb: MeshBuilder, gl: MeshBuilder) -> void:
	var d := 0.14
	# a tall stone surround with a narrow slot and a short cross arm
	_box(mb, Transform3D(Basis(), Vector3(-0.13, 0.15, d * 0.5)), Vector3(0.16, 1.3, d), STONE, M_STONE)
	_box(mb, Transform3D(Basis(), Vector3(0.13, 0.15, d * 0.5)), Vector3(0.16, 1.3, d), STONE, M_STONE)
	_box(mb, Transform3D(Basis(), Vector3(0, 0.84, d * 0.5)), Vector3(0.42, 0.12, d), STONE, M_STONE)
	_box(mb, Transform3D(Basis(), Vector3(0, -0.54, d * 0.5)), Vector3(0.42, 0.12, d), STONE, M_STONE)
	var n := Vector3(0, 0, 1)
	gl.quad_facing(Vector3(-0.05, -0.48, 0.02), Vector3(0.05, -0.48, 0.02), Vector3(0.05, 0.78, 0.02), Vector3(-0.05, 0.78, 0.02), n, GLASS)
	gl.quad_facing(Vector3(-0.2, 0.22, 0.015), Vector3(0.2, 0.22, 0.015), Vector3(0.2, 0.3, 0.015), Vector3(-0.2, 0.3, 0.015), n, GLASS)


## A patterned cloth from `origin` spanning `fly` (across) and `drop` (down),
## gently rippled; a banner ends in a swallow-tail point.
static func _cloth(mb: MeshBuilder, origin: Vector3, fly: Vector3, drop: Vector3, pattern: int, ripple: float, pointed: bool) -> void:
	var nu := 8
	var nv := 6
	var nrm := fly.cross(drop).normalized()
	for i in nu:
		for j in nv:
			var u0 := float(i) / nu
			var u1 := float(i + 1) / nu
			var v0 := float(j) / nv
			var v1 := float(j + 1) / nv
			if pointed and j == nv - 1:
				# swallow-tail: the last row narrows to two points
				var cut := absf((u0 + u1) * 0.5 - 0.5) < 0.25
				if cut:
					continue
			var col := pattern_color(pattern, (u0 + u1) * 0.5, (v0 + v1) * 0.5)
			var a := _cloth_pt(origin, fly, drop, u0, v0, ripple, nrm)
			var b := _cloth_pt(origin, fly, drop, u1, v0, ripple, nrm)
			var c := _cloth_pt(origin, fly, drop, u1, v1, ripple, nrm)
			var d := _cloth_pt(origin, fly, drop, u0, v1, ripple, nrm)
			_two_sided(mb, a, b, c, d, col, M_CLOTH)


static func _cloth_pt(origin: Vector3, fly: Vector3, drop: Vector3, u: float, v: float, ripple: float, nrm: Vector3) -> Vector3:
	return origin + fly * u + drop * v + nrm * sin(u * PI * 2.2 + v * 0.8) * ripple * u


static func _rope(mb: MeshBuilder, a: Vector3, b: Vector3, sag: float) -> void:
	var n := 8
	var prev := a
	for i in range(1, n + 1):
		var t := float(i) / n
		var p := a.lerp(b, t) + Vector3.DOWN * (sag * 4.0 * t * (1.0 - t))
		var mid := (prev + p) * 0.5
		var dir := p - prev
		if dir.length() > 0.001:
			var basis := Basis.looking_at(dir.normalized(), Vector3.UP if absf(dir.normalized().y) < 0.95 else Vector3.RIGHT)
			_box(mb, Transform3D(basis, mid), Vector3(0.025, 0.025, dir.length()), Color(0.78, 0.72, 0.6), M_CLOTH)
		prev = p


static func _two_sided(mb: MeshBuilder, a: Vector3, b: Vector3, c: Vector3, d: Vector3, col: Color, layer: int) -> void:
	var n := (b - a).cross(d - a).normalized()
	var start := mb.verts.size()
	mb.quad_facing(a, b, c, d, n, col)
	mb.quad_facing(a, b, c, d, -n, col)
	_layer(mb, start, layer)


static func _box(mb: MeshBuilder, xf: Transform3D, size: Vector3, col: Color, layer: int) -> void:
	var start := mb.verts.size()
	mb.box(xf, size, col)
	_layer(mb, start, layer)


## Points the vertices added since `start` at a surface material layer.
static func _layer(mb: MeshBuilder, start: int, layer: int) -> void:
	var uv := Vector2((layer + 0.5) / 16.0, 0.5)
	for i in range(start, mb.verts.size()):
		mb.uvs[i] = uv
