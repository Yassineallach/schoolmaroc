class_name Masonry
extends RefCounted
## Individually modelled stonework for walls, towers and stone storeys.
##
## A recessed mortar core is faced with courses of separate stones. Each
## stone is a bevelled, slightly pillowed block with controlled variation:
## course heights, stone lengths, protrusion, a gentle tilt and colour all
## vary inside believable limits, joints stay a few centimetres wide, and
## stones are clipped to the wall's real outline (terrain, tops, openings)
## so the facing follows the structure instead of being scattered on it.
## Arches get radial voussoirs with a keystone; tops get coping stones.

const JOINT := 0.026
const DEPTH := 0.06        # how far stones stand proud of the mortar
const ROW_H := Vector2(0.2, 0.3)
const LEN := Vector2(0.3, 0.68)


## Slight per-stone colour shift around the wall's base colour (brightness,
## warm/cool hue and the odd darker weathered stone).
static func stone_color(base: Color, rng: RandomNumberGenerator) -> Color:
	var k := rng.randf_range(0.86, 1.08)
	if rng.randf() < 0.1:
		k *= 0.84
	var t := rng.randf_range(-1.0, 1.0)
	return Color(clampf(base.r * k * (1.0 + t * 0.035), 0, 1), clampf(base.g * k, 0, 1), clampf(base.b * k * (1.0 - t * 0.045), 0, 1), 1.0)


static func mortar_color(base: Color) -> Color:
	var m := base * 0.72
	var l := m.get_luminance()
	return Color(lerpf(m.r, l, 0.2), lerpf(m.g, l, 0.2), lerpf(m.b, l, 0.2), 0.0)


## One bevelled stone. `o` is its bottom-left corner on the mortar plane, `u`
## runs along the wall, `v` up and `n` out of the wall.
static func stone(mb: MeshBuilder, o: Vector3, u: Vector3, v: Vector3, n: Vector3, w: float, h: float,
		depth: float, col: Color, rng: RandomNumberGenerator, uv0 := Vector2.ZERO) -> void:
	var b := minf(0.032, minf(w, h) * 0.24)
	var j := depth * 0.18
	var back := [o, o + u * w, o + u * w + v * h, o + v * h]
	var front := [
		o + u * b + v * b + n * (depth + rng.randf_range(-j, j)),
		o + u * (w - b) + v * b + n * (depth + rng.randf_range(-j, j)),
		o + u * (w - b) + v * (h - b) + n * (depth + rng.randf_range(-j, j)),
		o + u * b + v * (h - b) + n * (depth + rng.randf_range(-j, j)),
	]
	var corner := [-u - v, u - v, u + v, -u + v]
	var fn: Array[Vector3] = []
	for k in 4:
		fn.append((n + corner[k] * 0.22).normalized())
	var uvs := [uv0, uv0 + Vector2(w, 0), uv0 + Vector2(w, h), uv0 + Vector2(0, h)]
	mb.quad_facing(front[0], front[1], front[2], front[3], n, col, fn[0], fn[1], fn[2], fn[3], uvs[0], uvs[1], uvs[2], uvs[3])
	# chamfered sides: bottom, right, top, left
	var outs := [-v, u, v, -u]
	for k in 4:
		var k2 := (k + 1) % 4
		var out: Vector3 = outs[k]
		var nf := (n * 0.55 + out).normalized()
		var nback := (n * 0.15 + out).normalized()
		mb.quad_facing(back[k], back[k2], front[k2], front[k], nf, col, nback, nback, fn[k2], fn[k], uvs[k], uvs[k2], uvs[k2], uvs[k])


## Lays courses over a surface described by `surf(s) -> {p, n, g, low, top}`:
## p = point on the mortar plane at y = 0, n = outward normal, g = course
## baseline height, low/top = absolute limits of the wall at s.
## `skip(s0, s1, y0, y1)` vetoes stones (openings, voussoir bands).
static func lay(mb: MeshBuilder, surf: Callable, s_from: float, s_to: float, y_from: float, y_to: float,
		base: Color, rng: RandomNumberGenerator, skip := Callable()) -> void:
	var y := y_from
	var row := 0
	while y < y_to - 0.04:
		var rh := rng.randf_range(ROW_H.x, ROW_H.y)
		var s := s_from - rng.randf_range(0.0, LEN.y)
		while s < s_to:
			var sw := rng.randf_range(LEN.x, LEN.y) * (0.75 + rh * 1.1)
			var s0 := maxf(s, s_from)
			var s1 := minf(s + sw, s_to)
			s += sw
			if s1 - s0 < 0.12:
				continue
			# trim stones that run into an opening so jambs stay fully faced
			var gmid: float = surf.call((s0 + s1) * 0.5).g + y
			var probe := gmid + rh * 0.5
			while s1 - s0 > 0.12 and _blocked(surf.call(s1), probe):
				s1 -= 0.05
			while s1 - s0 > 0.12 and _blocked(surf.call(s0), probe):
				s0 += 0.05
			if s1 - s0 < 0.12:
				continue
			var sc := (s0 + s1) * 0.5
			var a: Dictionary = surf.call(s0)
			var c: Dictionary = surf.call(sc)
			var e: Dictionary = surf.call(s1)
			var gy: float = c.g + y
			var lo := maxf(maxf(a.low, c.low), e.low)
			var hi := minf(minf(a.top, c.top), e.top)
			var y0 := maxf(gy, lo) + JOINT * 0.5
			var y1 := minf(gy + rh, hi) - JOINT * 0.5
			if y1 - y0 < 0.07:
				continue
			if skip.is_valid() and skip.call(s0, s1, y0, y1):
				# cut the stone back to the opening's edge instead of leaving a gap
				var t1 := s1
				while t1 - s0 > 0.14 and skip.call(s0, t1, y0, y1):
					t1 -= 0.04
				if skip.call(s0, t1, y0, y1):
					var t0 := s0
					while s1 - t0 > 0.14 and skip.call(t0, s1, y0, y1):
						t0 += 0.04
					if skip.call(t0, s1, y0, y1):
						continue
					s0 = t0
				else:
					s1 = t1
				a = surf.call(s0)
				e = surf.call(s1)
			var p0: Vector3 = a.p
			var p1: Vector3 = e.p
			var chord := p1 - p0
			var w := chord.length() - JOINT
			if w < 0.08:
				continue
			var u := chord.normalized()
			var n: Vector3 = c.n
			# hand-laid: a whisker of tilt and set-back variation
			var tilt := rng.randf_range(-0.012, 0.012)
			var v := (Vector3.UP + u * tilt).normalized()
			var o := p0 + u * (JOINT * 0.5) + Vector3.UP * y0
			stone(mb, o, u, v, n, w, y1 - y0, DEPTH * rng.randf_range(0.75, 1.2), stone_color(base, rng), rng, Vector2(s0, y0))
		y += rh
		row += 1


static func _blocked(k: Dictionary, y: float) -> bool:
	return k.low > y or k.top < y


## Radial voussoirs around a semicircular arch (keystone on top), passing
## through the wall's thickness. `c` = arch centre at the springing line.
static func voussoirs(mb: MeshBuilder, c: Vector3, along: Vector3, n: Vector3, r: float, half_thick: float,
		base: Color, rng: RandomNumberGenerator) -> void:
	var count := maxi(5, int(round(PI * r / 0.26)))
	if count % 2 == 0:
		count += 1
	var gap := JOINT / maxf(r, 0.3) * 0.5
	var depth := half_thick + DEPTH
	for i in count:
		var a0 := PI * i / count + gap
		var a1 := PI * (i + 1) / count - gap
		var key := i == count / 2
		var ro := r + (0.4 if key else 0.3 + rng.randf_range(-0.02, 0.03))
		var col := stone_color(base, rng)
		var dirs := [along * cos(a0) + Vector3.UP * sin(a0), along * cos(a1) + Vector3.UP * sin(a1)]
		var ins := [c + dirs[0] * r, c + dirs[1] * r]
		var outs := [c + dirs[0] * ro, c + dirs[1] * ro]
		var fr := n * (depth + (0.015 if key else 0.0))
		# front & back faces
		for side in [1.0, -1.0]:
			var off: Vector3 = fr * side
			mb.quad_facing(ins[0] + off, ins[1] + off, outs[1] + off, outs[0] + off, n * side, col)
		# soffit (underside), extrados, and the two joint faces
		var mid: Vector3 = (dirs[0] + dirs[1]).normalized()
		mb.quad_facing(ins[0] + fr, ins[1] + fr, ins[1] - fr, ins[0] - fr, -mid, col)
		mb.quad_facing(outs[0] + fr, outs[1] + fr, outs[1] - fr, outs[0] - fr, mid, col)
		for k in 2:
			var dn: Vector3 = dirs[k]
			var side_n := dn.cross(n).normalized() * (1.0 if k == 1 else -1.0)
			mb.quad_facing(ins[k] + fr, outs[k] + fr, outs[k] - fr, ins[k] - fr, side_n, col)


## A run of coping stones along the top of a wall, between two points.
static func coping(mb: MeshBuilder, a: Vector3, b: Vector3, width: float, base: Color, rng: RandomNumberGenerator) -> void:
	var d := b - a
	var flat := Vector3(d.x, 0.0, d.z)
	if flat.length() < 0.05:
		return
	var basis := DecoMerge.along(flat) * Basis(Vector3.BACK, atan2(d.y, flat.length()))
	var mid := (a + b) * 0.5
	var size := Vector3(d.length() - JOINT, rng.randf_range(0.11, 0.15), width + rng.randf_range(0.06, 0.1))
	mb.bevel_box(Transform3D(basis, mid + Vector3.UP * size.y * 0.5), size, 0.035, stone_color(base, rng))


## Stack of alternating quoin blocks (wall ends, door jambs, pillar shafts).
static func quoins(mb: MeshBuilder, p: Vector3, n: Vector3, y0: float, y1: float, thick: float, base: Color, rng: RandomNumberGenerator) -> void:
	var basis := DecoMerge.facing(n)
	var y := y0
	var k := 0
	while y < y1 - 0.05:
		var h := minf(rng.randf_range(0.24, 0.32), y1 - y)
		var long := k % 2 == 0
		var size := Vector3(0.5 if long else 0.34, h - JOINT, thick + 0.1)
		var shift := 0.06 if long else -0.03
		mb.bevel_box(Transform3D(basis, p + basis.x * shift + Vector3.UP * (y + h * 0.5)), size, 0.03, stone_color(base, rng))
		y += h
		k += 1
