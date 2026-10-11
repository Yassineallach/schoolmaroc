class_name Geo
extends RefCounted
## 2D polyline helpers on the ground plane (Vector2 = world x,z).


static func length(pts: PackedVector2Array) -> float:
	var l := 0.0
	for i in range(1, pts.size()):
		l += pts[i - 1].distance_to(pts[i])
	return l


## Ramer-Douglas-Peucker simplification.
static func simplify(pts: PackedVector2Array, eps: float) -> PackedVector2Array:
	if pts.size() < 3:
		return pts
	var dmax := 0.0
	var index := 0
	var a := pts[0]
	var b := pts[pts.size() - 1]
	for i in range(1, pts.size() - 1):
		var d := dist_to_segment(pts[i], a, b)
		if d > dmax:
			dmax = d
			index = i
	if dmax > eps:
		var left := simplify(pts.slice(0, index + 1), eps)
		var right := simplify(pts.slice(index), eps)
		left.resize(left.size() - 1)
		left.append_array(right)
		return left
	return PackedVector2Array([a, b])


## Chaikin corner cutting, keeps end points.
static func smooth(pts: PackedVector2Array, iterations := 2) -> PackedVector2Array:
	var cur := pts
	for it in iterations:
		if cur.size() < 3:
			return cur
		var out := PackedVector2Array()
		out.append(cur[0])
		for i in range(cur.size() - 1):
			var p := cur[i]
			var q := cur[i + 1]
			out.append(p.lerp(q, 0.25))
			out.append(p.lerp(q, 0.75))
		out.append(cur[cur.size() - 1])
		cur = out
	return cur


## Resamples a polyline at (roughly) fixed spacing.
static func resample(pts: PackedVector2Array, spacing: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	if pts.size() < 2:
		return pts
	var total := length(pts)
	var n := maxi(1, int(ceil(total / spacing)))
	for i in n + 1:
		out.append(point_at(pts, total * float(i) / n))
	return out


static func point_at(pts: PackedVector2Array, s: float) -> Vector2:
	if pts.is_empty():
		return Vector2.ZERO
	var acc := 0.0
	for i in range(1, pts.size()):
		var seg := pts[i - 1].distance_to(pts[i])
		if acc + seg >= s and seg > 0.0:
			return pts[i - 1].lerp(pts[i], (s - acc) / seg)
		acc += seg
	return pts[pts.size() - 1]


static func tangent_at(pts: PackedVector2Array, s: float) -> Vector2:
	var a := point_at(pts, maxf(0.0, s - 0.15))
	var b := point_at(pts, s + 0.15)
	var t := b - a
	if t.length_squared() < 1e-8 and pts.size() > 1:
		t = pts[pts.size() - 1] - pts[0]
	return t.normalized() if t.length_squared() > 1e-10 else Vector2.RIGHT


static func dist_to_segment(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var l2 := ab.length_squared()
	if l2 < 1e-10:
		return p.distance_to(a)
	var t := clampf((p - a).dot(ab) / l2, 0.0, 1.0)
	return p.distance_to(a + ab * t)


## Returns [distance, arclength-at-closest] to the polyline.
static func closest(pts: PackedVector2Array, p: Vector2) -> Vector2:
	var best := INF
	var best_s := 0.0
	var acc := 0.0
	for i in range(1, pts.size()):
		var a := pts[i - 1]
		var b := pts[i]
		var ab := b - a
		var l2 := ab.length_squared()
		var t := 0.0 if l2 < 1e-10 else clampf((p - a).dot(ab) / l2, 0.0, 1.0)
		var d := p.distance_to(a + ab * t)
		if d < best:
			best = d
			best_s = acc + sqrt(l2) * t
		acc += sqrt(l2)
	if pts.size() == 1:
		best = p.distance_to(pts[0])
	return Vector2(best, best_s)


## All crossings of polyline A with polyline B.
## Returns Array of {sa, sb, point, angle} (arclengths along each polyline).
static func intersections(a: PackedVector2Array, b: PackedVector2Array) -> Array:
	var out: Array = []
	var acc_a := 0.0
	for i in range(1, a.size()):
		var p1 := a[i - 1]
		var p2 := a[i]
		var la := p1.distance_to(p2)
		var acc_b := 0.0
		for j in range(1, b.size()):
			var q1 := b[j - 1]
			var q2 := b[j]
			var lb := q1.distance_to(q2)
			var hit = Geometry2D.segment_intersects_segment(p1, p2, q1, q2)
			if hit != null:
				var h: Vector2 = hit
				var da := (p2 - p1).normalized()
				var db := (q2 - q1).normalized()
				out.append({
					"sa": acc_a + p1.distance_to(h),
					"sb": acc_b + q1.distance_to(h),
					"point": h,
					"sin": absf(da.cross(db)),
				})
			acc_b += lb
		acc_a += la
	return out


## Splits a polyline removing every part within `radius` of `center`.
static func erase_circle(pts: PackedVector2Array, center: Vector2, radius: float) -> Array:
	var dense := resample(pts, 0.25)
	var pieces: Array = []
	var cur := PackedVector2Array()
	for p in dense:
		if p.distance_to(center) < radius:
			if cur.size() >= 2:
				pieces.append(cur)
			cur = PackedVector2Array()
		else:
			cur.append(p)
	if cur.size() >= 2:
		pieces.append(cur)
	var out: Array = []
	for piece in pieces:
		if length(piece) > 0.6:
			out.append(simplify(piece, 0.05))
	return out


static func polygon_rect(center: Vector2, size: Vector2, rot: float) -> PackedVector2Array:
	var hx := Vector2(cos(rot), sin(rot)) * size.x * 0.5
	var hz := Vector2(-sin(rot), cos(rot)) * size.y * 0.5
	return PackedVector2Array([center - hx - hz, center + hx - hz, center + hx + hz, center - hx + hz])


static func v3(p: Vector2, y := 0.0) -> Vector3:
	return Vector3(p.x, y, p.y)


static func v2(p: Vector3) -> Vector2:
	return Vector2(p.x, p.z)
