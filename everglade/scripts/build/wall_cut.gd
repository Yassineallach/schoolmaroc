class_name WallCut
extends RefCounted
## Openings cut right through a wall, as in Tiny Glade: the wall face is laid
## around each hole, the hole is lined with deep reveals and closed at the
## back, and the door or window (the tg_* models) sits inside it rather than
## on the face.
##
## A hole is {"s": centre along the face, "y": sill / threshold height,
## "w": width, "h": height of the straight jambs, "arch": FLAT, ROUND or
## POINTED (the head rises above y + h)}; "nosill" leaves the bottom
## unlined (doors, whose threshold is the floor).

const FLAT := 0
const ROUND := 1
const POINTED := 2
## How deep the reveals run into the wall.
const DEPTH := 0.34
const ARC_STEPS := 12
## Pointed arches: arcs of radius K_R * half-width centred K_C * half-width
## off the middle (the lancet the tg_* gothic models are built on).
const K_R := 1.7
const K_C := 0.7
const BACK := Color(0.10, 0.08, 0.065, 1.0)

## Openings of the tg_* door and window models (origin = bottom centre of
## the opening on the wall face). Frames overlap these by a centimetre or
## two, so no gap shows round them.
const MODELS := {
	"tg_door": {"w": 1.40, "h": 2.36, "arch": FLAT},
	"tg_door_arch": {"w": 1.40, "h": 1.64, "arch": ROUND},
	"tg_door_gothic": {"w": 1.12, "h": 1.548, "arch": POINTED},
	"tg_door_double": {"w": 2.20, "h": 2.50, "arch": FLAT},
	"tg_window": {"w": 0.96, "h": 1.08, "arch": FLAT},
	"tg_window_arch": {"w": 0.96, "h": 1.04, "arch": ROUND},
	"tg_window_gothic": {"w": 0.80, "h": 0.58, "arch": POINTED},
	"tg_window_lattice": {"w": 0.90, "h": 1.14, "arch": FLAT},
}


## The hole a tg_* model needs, centred at s with its sill at y, `sx` times
## as wide (merged windows, double doors).
static func hole_for(model: String, s: float, y: float, sx := 1.0) -> Dictionary:
	var m: Dictionary = MODELS[model]
	return {"s": s, "y": y, "w": float(m.w) * sx, "h": float(m.h), "arch": int(m.arch), "model": model}


## How far the head rises above the jambs.
static func rise(hl: Dictionary) -> float:
	match int(hl.arch):
		ROUND:
			return hl.w * 0.5
		POINTED:
			var half: float = hl.w * 0.5
			return sqrt(K_R * K_R - K_C * K_C) * half
	return 0.0


## Height of a model's opening above its origin.
static func model_height(model: String) -> float:
	var m: Dictionary = MODELS[model]
	return float(m.h) + rise({"w": m.w, "arch": m.arch})


static func top(hl: Dictionary) -> float:
	return hl.y + hl.h + rise(hl)


## Head height at offset x from the hole's centre (|x| <= w / 2).
static func head(hl: Dictionary, x: float) -> float:
	var half: float = hl.w * 0.5
	var base: float = hl.y + hl.h
	match int(hl.arch):
		ROUND:
			return base + sqrt(maxf(0.0, half * half - x * x))
		POINTED:
			var r := half * K_R
			var dx := absf(x) + half * K_C
			return base + sqrt(maxf(0.0, r * r - dx * dx))
	return base


## Bounding rectangle (s, y) of a hole grown by `margin`, for stone and
## board layouts that keep clear of it.
static func rect(hl: Dictionary, margin := 0.0) -> Rect2:
	return Rect2(hl.s - hl.w * 0.5 - margin, hl.y - margin, hl.w + margin * 2.0, top(hl) - hl.y + margin * 2.0)


static func rects(holes: Array, margin := 0.0) -> Array:
	var out: Array = []
	for hl in holes:
		out.append(rect(hl, margin))
	return out


## Where the outline of a hole bends: its jambs and the arch samples.
static func _xs(hl: Dictionary) -> Array:
	var half: float = hl.w * 0.5
	var out: Array = [hl.s - half, hl.s + half]
	if int(hl.arch) != FLAT:
		for k in range(1, ARC_STEPS):
			out.append(hl.s - half + hl.w * k / ARC_STEPS)
		if int(hl.arch) == POINTED:
			out.append(hl.s)
	return out


## Lays a wall face over s0..s1 x y0..y1 with the holes left open, then lines
## the part of each hole inside y0..y1 with reveals DEPTH deep and a dark
## back. `at.call(s, y)` gives the point on the face, `nrm.call(s)` the
## outward normal; strips are cut at least every `step` metres (curved
## walls). UVs run in metres from u0 along the face.
static func face(mb: MeshBuilder, at: Callable, nrm: Callable, s0: float, s1: float, y0: float, y1: float,
		holes: Array, col: Color, reveal_col: Color, u0 := 0.0, step := 0.0) -> void:
	if y1 - y0 < 0.001 or s1 - s0 < 0.001:
		return
	var mine: Array = []
	for hl in holes:
		var r := rect(hl)
		if r.position.y < y1 and r.end.y > y0 and r.position.x < s1 and r.end.x > s0:
			mine.append(hl)
	var xs: Array = [s0, s1]
	for hl in mine:
		for x in _xs(hl):
			if x > s0 and x < s1:
				xs.append(x)
	if step > 0.0:
		var n := int(ceil((s1 - s0) / step))
		for k in range(1, n):
			xs.append(s0 + (s1 - s0) * k / n)
	xs.sort()
	for i in xs.size() - 1:
		var xa: float = xs[i]
		var xb: float = xs[i + 1]
		if xb - xa < 0.0005:
			continue
		var xm := (xa + xb) * 0.5
		var over: Array = []
		for hl in mine:
			if absf(xm - hl.s) < hl.w * 0.5:
				over.append(hl)
		over.sort_custom(func(p, q): return p.y < q.y)
		var ca := y0
		var cb := y0
		for hl in over:
			var bot := clampf(hl.y, y0, y1)
			_strip(mb, at, nrm, xa, xb, ca, cb, bot, bot, col, u0)
			ca = maxf(ca, clampf(head(hl, xa - hl.s), y0, y1))
			cb = maxf(cb, clampf(head(hl, xb - hl.s), y0, y1))
		_strip(mb, at, nrm, xa, xb, ca, cb, y1, y1, col, u0)
	for hl in mine:
		_reveal(mb, at, nrm, hl, y0, y1, reveal_col)


## One piece of face between xa and xb, from (ya0, yb0) up to (ya1, yb1).
static func _strip(mb: MeshBuilder, at: Callable, nrm: Callable, xa: float, xb: float, ya0: float, yb0: float,
		ya1: float, yb1: float, col: Color, u0: float) -> void:
	if ya1 - ya0 < 0.0005 and yb1 - yb0 < 0.0005:
		return
	var na: Vector3 = nrm.call(xa)
	var nb: Vector3 = nrm.call(xb)
	mb.quad_facing(at.call(xa, ya0), at.call(xb, yb0), at.call(xb, yb1), at.call(xa, ya1), (na + nb).normalized(), col,
			na, nb, nb, na, Vector2(u0 + xa, ya0), Vector2(u0 + xb, yb0), Vector2(u0 + xb, yb1), Vector2(u0 + xa, ya1))


## The hole's outline in (s, y), counter-clockwise from the bottom left.
static func outline(hl: Dictionary) -> PackedVector2Array:
	var half: float = hl.w * 0.5
	var pts := PackedVector2Array([Vector2(hl.s - half, hl.y), Vector2(hl.s + half, hl.y)])
	var xs := _xs(hl)
	xs.sort()
	xs.reverse()
	for x in xs:
		pts.append(Vector2(x, head(hl, x - hl.s)))
	return pts


static func _reveal(mb: MeshBuilder, at: Callable, nrm: Callable, hl: Dictionary, y0: float, y1: float, col: Color) -> void:
	var poly := outline(hl)
	var centre := Vector2(hl.s, (hl.y + top(hl)) * 0.5)
	for i in poly.size():
		var p: Vector2 = poly[i]
		var q: Vector2 = poly[(i + 1) % poly.size()]
		# clip the edge to the y0..y1 slab
		var t0 := 0.0
		var t1 := 1.0
		var dy := q.y - p.y
		if absf(dy) < 1e-6:
			# a sill belongs to the slab above it, a flat head to the one below
			if i == 0:
				if hl.get("nosill", false) or p.y < y0 - 1e-4 or p.y >= y1 - 1e-4:
					continue
			elif p.y <= y0 + 1e-4 or p.y > y1 + 1e-4:
				continue
		else:
			var ta := (y0 - p.y) / dy
			var tb := (y1 - p.y) / dy
			t0 = maxf(t0, minf(ta, tb))
			t1 = minf(t1, maxf(ta, tb))
			if t1 - t0 < 1e-5:
				continue
		var a := p.lerp(q, t0)
		var b := p.lerp(q, t1)
		var na: Vector3 = nrm.call(a.x)
		var nb: Vector3 = nrm.call(b.x)
		var fa: Vector3 = at.call(a.x, a.y)
		var fb: Vector3 = at.call(b.x, b.y)
		# facing into the opening, across the edge
		var mid := (a + b) * 0.5
		var into: Vector3 = at.call(centre.x, centre.y) - at.call(mid.x, mid.y)
		var along := (fb - fa).normalized()
		var wn := (na + nb).normalized()
		into = (into - along * into.dot(along) - wn * into.dot(wn)).normalized()
		var ln := Vector2(b.x - a.x, b.y - a.y).length()
		mb.quad_facing(fa, fb, fb - nb * DEPTH, fa - na * DEPTH, into, col,
				Vector3.ZERO, Vector3.ZERO, Vector3.ZERO, Vector3.ZERO,
				Vector2(0, 0), Vector2(ln, 0), Vector2(ln, DEPTH), Vector2(0, DEPTH))
	# the dark back the door or window stands in front of
	var slab := PackedVector2Array([Vector2(hl.s - hl.w, y0), Vector2(hl.s + hl.w, y0), Vector2(hl.s + hl.w, y1), Vector2(hl.s - hl.w, y1)])
	for part in Geometry2D.intersect_polygons(poly, slab):
		var pts: PackedVector2Array = part
		var tris := Geometry2D.triangulate_polygon(pts)
		for k in range(0, tris.size(), 3):
			var p0: Vector2 = pts[tris[k]]
			var p1: Vector2 = pts[tris[k + 1]]
			var p2: Vector2 = pts[tris[k + 2]]
			var n0: Vector3 = nrm.call((p0.x + p1.x + p2.x) / 3.0)
			mb.tri_facing(at.call(p0.x, p0.y) - nrm.call(p0.x) * DEPTH, at.call(p1.x, p1.y) - nrm.call(p1.x) * DEPTH,
					at.call(p2.x, p2.y) - nrm.call(p2.x) * DEPTH, n0, BACK)


## Face mapping for a straight wall from a to b (s = distance from a).
static func flat_at(a: Vector3, b: Vector3) -> Callable:
	var dir := (b - a).normalized()
	return func(s: float, y: float) -> Vector3: return Vector3(a.x, 0.0, a.z) + dir * s + Vector3.UP * y


static func flat_nrm(n: Vector3) -> Callable:
	return func(_s: float) -> Vector3: return n


## Face mapping round a tower face of radius r, s being arc length at
## radius `ref` from angle 0 (so faces set proud share the openings).
static func round_at(r: float, ref: float) -> Callable:
	return func(s: float, y: float) -> Vector3: return Vector3(cos(s / ref), 0.0, sin(s / ref)) * r + Vector3.UP * y


static func round_nrm(ref: float) -> Callable:
	return func(s: float) -> Vector3: return Vector3(cos(s / ref), 0.0, sin(s / ref))
