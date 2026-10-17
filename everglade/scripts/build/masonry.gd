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

## Facing pattern used by lay(): "classic" (current coursed stones),
## "glade" (pillowy, irregular hand-laid stones, big at the foot),
## "ashlar" (large dressed blocks, fine joints), "brick" (Flemish bond),
## "rubble" (uncoursed polygonal fieldstone), "broken" (Tiny Glade's
## broken-course stonework: flat-faced blocks of mixed sizes, courses that
## never run straight for long, grey stone washed with lichen), "peel"
## (small cream bricks showing where plaster has worn away).
const PATTERNS := ["classic", "glade", "kit", "rubble", "brick", "ashlar", "broken", "peel"]
static var pattern := "classic"
## "kit" pattern: Quaternius rounded stones (Medieval Village MegaKit, CC0)
## gathered while laying, tinted per stone, and drawn with their painted
## texture as a separate mesh (see WallView).
static var kit_st: SurfaceTool = null
static var _kit_meshes: Array = []   # [arrays, aabb]


static func _kit_stone(o: Vector3, u: Vector3, v: Vector3, n: Vector3, w: float, h: float, depth: float,
		col: Color, rng: RandomNumberGenerator) -> void:
	if _kit_meshes.is_empty():
		for i in 4:
			var root := (load("res://assets/models/q_stone_%d.glb" % (i + 1)) as PackedScene).instantiate()
			var mi: MeshInstance3D = root if root is MeshInstance3D else null
			for c in root.get_children():
				if c is MeshInstance3D:
					mi = c
			_kit_meshes.append([mi.mesh.surface_get_arrays(0), mi.mesh.get_aabb()])
			root.free()
	var pick: Array = _kit_meshes[rng.randi() % _kit_meshes.size()]
	var arrays: Array = pick[0]
	var bb: AABB = pick[1]
	# slightly oversized so neighbouring stones nearly touch
	var basis := Basis(u * (w * 1.05 / bb.size.x), v * (h * 1.08 / bb.size.y), n * (depth * 2.0 / bb.size.z))
	var origin := o - u * (w * 0.025) - v * (h * 0.04) - n * depth - basis * bb.position
	var nb := basis.inverse().transposed()
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var norms: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
	var uvs: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV]
	var idx: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	# the painted texture is already stone-coloured: tint towards the wall colour
	var l := col.get_luminance()
	var tint := Color(lerpf(l, col.r, 0.6), lerpf(l, col.g, 0.6), lerpf(l, col.b, 0.6)) * 1.28
	tint.a = 1.0
	for k in idx.size():
		var vi := idx[k]
		kit_st.set_color(tint)
		kit_st.set_normal((nb * norms[vi]).normalized())
		kit_st.set_uv(uvs[vi])
		kit_st.add_vertex(basis * verts[vi] + origin)


## Slight per-stone colour shift around the wall's base colour (brightness,
## warm/cool hue and the odd darker weathered stone).
static func stone_color(base: Color, rng: RandomNumberGenerator) -> Color:
	var k := rng.randf_range(0.86, 1.08)
	if rng.randf() < 0.1:
		k *= 0.84
	var t := rng.randf_range(-1.0, 1.0)
	return Color(clampf(base.r * k * (1.0 + t * 0.035), 0, 1), clampf(base.g * k, 0, 1), clampf(base.b * k * (1.0 - t * 0.045), 0, 1), 1.0)


## Warm lime render laid over the stonework of "rendered" walls.
static func plaster_color(base: Color) -> Color:
	var p := base.lerp(Color(0.99, 0.89, 0.66), 0.85)
	return Color(p.r, p.g, p.b, 0.0)


static func mortar_color(base: Color) -> Color:
	var m := base * 0.72
	var l := m.get_luminance()
	return Color(lerpf(m.r, l, 0.2), lerpf(m.g, l, 0.2), lerpf(m.b, l, 0.2), 0.0)


## One bevelled stone. `o` is its bottom-left corner on the mortar plane, `u`
## runs along the wall, `v` up and `n` out of the wall.
static func stone(mb: MeshBuilder, o: Vector3, u: Vector3, v: Vector3, n: Vector3, w: float, h: float,
		depth: float, col: Color, rng: RandomNumberGenerator, uv0 := Vector2.ZERO, pillow := 0.0, bevel_max := 0.032) -> void:
	var b := minf(bevel_max, minf(w, h) * 0.24)
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
	if pillow > 0.0:
		# rounded, cushion-like face: a raised centre fanned to the edges
		var c: Vector3 = (front[0] + front[1] + front[2] + front[3]) * 0.25 + n * pillow
		var uc: Vector2 = uv0 + Vector2(w, h) * 0.5
		for k in 4:
			var k2 := (k + 1) % 4
			_tri_n(mb, front[k], front[k2], c, fn[k], fn[k2], n, col, uvs[k], uvs[k2], uc, n)
	else:
		mb.quad_facing(front[0], front[1], front[2], front[3], n, col, fn[0], fn[1], fn[2], fn[3], uvs[0], uvs[1], uvs[2], uvs[3])
	# chamfered sides: bottom, right, top, left
	var outs := [-v, u, v, -u]
	for k in 4:
		var k2 := (k + 1) % 4
		var out: Vector3 = outs[k]
		var nf := (n * 0.55 + out).normalized()
		var nback := (n * 0.15 + out).normalized()
		mb.quad_facing(back[k], back[k2], front[k2], front[k], nf, col, nback, nback, fn[k2], fn[k], uvs[k], uvs[k2], uvs[k2], uvs[k])


## Smooth-shaded triangle wound to face `facing`.
static func _tri_n(mb: MeshBuilder, a: Vector3, b: Vector3, c: Vector3, na: Vector3, nb: Vector3, nc: Vector3,
		col: Color, ua: Vector2, ub: Vector2, uc: Vector2, facing: Vector3) -> void:
	var i0 := mb._v(a, na, col, ua)
	var i1 := mb._v(b, nb, col, ub)
	var i2 := mb._v(c, nc, col, uc)
	if (b - a).cross(c - a).dot(facing) < 0.0:
		mb.indices.append_array([i0, i1, i2])
	else:
		mb.indices.append_array([i0, i2, i1])


## Lays courses over a surface described by `surf(s) -> {p, n, g, low, top}`:
## p = point on the mortar plane at y = 0, n = outward normal, g = course
## baseline height, low/top = absolute limits of the wall at s.
## `skip(s0, s1, y0, y1)` vetoes stones (openings, voussoir bands).
static func lay(mb: MeshBuilder, surf: Callable, s_from: float, s_to: float, y_from: float, y_to: float,
		base: Color, rng: RandomNumberGenerator, skip := Callable(), veto := Callable()) -> void:
	match pattern:
		"brick", "peel":
			lay_brick(mb, surf, s_from, s_to, y_from, y_to, base, rng, skip, veto)
			return
		"broken":
			lay_broken(mb, surf, s_from, s_to, y_from, y_to, base, rng, skip, veto)
			return
		"rubble":
			lay_rubble(mb, surf, s_from, s_to, y_from, y_to, base, rng, skip, veto)
			return
	var kit := pattern == "kit" and kit_st != null
	var glade := pattern == "glade" or kit
	var ashlar := pattern == "ashlar"
	var row_h := Vector2(0.36, 0.46) if ashlar else ROW_H
	var len_r := Vector2(0.7, 1.15) if ashlar else LEN
	var joint := 0.014 if ashlar else (0.01 if kit else (0.022 if glade else JOINT))
	var y := y_from
	var row := 0
	while y < y_to - 0.04:
		var rh := rng.randf_range(row_h.x, row_h.y)
		if glade:
			# big footing stones, getting smaller towards the top
			var t := clampf((y - y_from) / maxf(y_to - y_from, 0.5), 0.0, 1.0)
			rh *= lerpf(1.45, 0.8, t)
		var s := s_from - rng.randf_range(0.0, len_r.y)
		while s < s_to:
			var sw := rng.randf_range(len_r.x, len_r.y) * (0.75 + rh * 1.1)
			if glade:
				sw *= rng.randf_range(0.8, 1.3)
			var s0 := maxf(s, s_from)
			var s1 := minf(s + sw, s_to)
			s += sw
			if s1 - s0 < 0.12:
				continue
			# cheap whole-stone rejection (e.g. outside a worn patch of render)
			if veto.is_valid():
				var gg := gmid_offset(surf, s0, s1)
				if veto.call(s0, s1, gg + y, gg + y + rh):
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
			var y0 := maxf(gy, lo) + joint * 0.5
			var y1 := minf(gy + rh, hi) - joint * 0.5
			if glade and not kit:
				# hand-laid: stones don't fill their course exactly
				y1 -= rng.randf_range(0.0, rh * 0.05)
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
			var w := chord.length() - joint
			if w < 0.08:
				continue
			var u := chord.normalized()
			var n: Vector3 = c.n
			# hand-laid: a whisker of tilt and set-back variation
			var tilt := 0.0 if ashlar else rng.randf_range(-0.012, 0.012) * (2.5 if glade else 1.0)
			var v := (Vector3.UP + u * tilt).normalized()
			var o := p0 + u * (joint * 0.5) + Vector3.UP * y0
			var col := stone_color(base, rng)
			if glade:
				col = _glade_color(col, base, y0 - c.g, rng)
			elif ashlar:
				col = base.lerp(col, 0.45)
			var depth := DEPTH * (rng.randf_range(0.95, 1.05) if ashlar else rng.randf_range(0.75, 1.2))
			if glade:
				depth *= 1.25
			if kit:
				_kit_stone(o, u, v, n, w, y1 - y0, depth * 1.4, col, rng)
				continue
			stone(mb, o, u, v, n, w, y1 - y0, depth, col, rng, Vector2(s0, y0),
					minf(w, y1 - y0) * 0.22 if glade else 0.0, 0.06 if glade else (0.014 if ashlar else 0.032))
		y += rh
		row += 1


static func gmid_offset(surf: Callable, s0: float, s1: float) -> float:
	return surf.call((s0 + s1) * 0.5).g


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


## Tiny Glade-like colouring: stronger stone-to-stone variation, warm and cool
## stones mixed, and a mossy green cast creeping up from the ground.
static func _glade_color(col: Color, base: Color, height: float, rng: RandomNumberGenerator) -> Color:
	var c := col
	var r := rng.randf()
	if r < 0.12:
		c = c.lerp(Color(base.r * 1.05, base.g * 0.92, base.b * 0.8), 0.6)   # warm ochre stone
	elif r < 0.22:
		c = c.lerp(Color(base.r * 0.85, base.g * 0.9, base.b * 1.0), 0.6)   # cool blue-grey stone
	var moss := clampf(1.0 - height / 0.9, 0.0, 1.0) * rng.randf_range(0.0, 0.55)
	c = c.lerp(Color(0.46, 0.54, 0.3), moss)
	c.a = 1.0
	return c


## Flemish bond brickwork: headers and stretchers alternate in every course,
## courses offset by a quarter brick; headers fired a little darker.
static func lay_brick(mb: MeshBuilder, surf: Callable, s_from: float, s_to: float, y_from: float, y_to: float,
		base: Color, rng: RandomNumberGenerator, skip := Callable(), veto := Callable()) -> void:
	const CH := 0.15          # course height incl. joint
	const STRETCH := 0.4
	const HEADER := 0.19
	const BJ := 0.016
	var peel := pattern == "peel"
	var brick := base if peel else Color(0.66, 0.36, 0.26).lerp(base, 0.25)
	var y := y_from
	var row := 0
	while y < y_to - 0.05:
		var s := s_from - (0.0 if row % 2 == 0 else (STRETCH + HEADER) * 0.5)
		var k := 0
		while s < s_to:
			var header := k % 2 == 1
			var bw := HEADER if header else STRETCH
			var s0 := maxf(s, s_from)
			var s1 := minf(s + bw, s_to)
			s += bw + BJ
			k += 1
			if s1 - s0 < 0.08:
				continue
			var c: Dictionary = surf.call((s0 + s1) * 0.5)
			var gy: float = c.g + y
			var y0 := maxf(gy, c.low) + BJ * 0.5
			var y1 := minf(gy + CH, c.top) - BJ * 0.5
			if y1 - y0 < 0.05 or _blocked(surf.call(s0), (y0 + y1) * 0.5) or _blocked(surf.call(s1), (y0 + y1) * 0.5):
				continue
			if skip.is_valid() and skip.call(s0, s1, y0, y1):
				continue
			if veto.is_valid() and veto.call(s0, s1, y0, y1):
				continue
			var p0: Vector3 = surf.call(s0).p
			var p1: Vector3 = surf.call(s1).p
			var u := (p1 - p0).normalized()
			var k2 := rng.randf_range(0.85, 1.1)
			var col := Color(brick.r * k2, brick.g * k2, brick.b * k2, 1.0)
			if header:
				col = col.darkened(rng.randf_range(0.04, 0.1) if peel else rng.randf_range(0.12, 0.3))
			stone(mb, p0 + Vector3.UP * y0, u, Vector3.UP, c.n, p0.distance_to(p1), y1 - y0, 0.035 * rng.randf_range(0.8, 1.15),
					col, rng, Vector2(s0, y0), 0.0, 0.014)
		y += CH
		row += 1


## Tiny Glade's broken-course stonework (its stone towers), packed the way
## the stones go up: always into the lowest gap, each block as wide as fits
## (0.28-0.7 m) and one of a few heights, now and then one and a half or two
## courses tall, often matching a neighbour's top so courses still read.
## Blocks are flat-faced with only eased edges, set a little proud or back
## and out of square; near an opening smaller stones are tried so the
## coursing runs right up to the frame. Joints are thin.
static func lay_broken(mb: MeshBuilder, surf: Callable, s_from: float, s_to: float, y_from: float, y_to: float,
		base: Color, rng: RandomNumberGenerator, skip := Callable(), veto := Callable()) -> void:
	const CELL := 0.05
	const BJ := 0.02
	var n := maxi(1, int(ceil((s_to - s_from) / CELL)))
	var sky := PackedFloat32Array()
	sky.resize(n)
	sky.fill(y_from)
	var heights := [0.2, 0.24, 0.28, 0.24, 0.32, 0.46]
	var guard := 0
	while guard < 40000:
		guard += 1
		var lo := INF
		var i0 := 0
		for k in n:
			if sky[k] < lo - 1e-5:
				lo = sky[k]
				i0 = k
		if lo >= y_to - 0.03:
			break
		var i1 := i0
		while i1 < n and absf(sky[i1] - lo) < 1e-5:
			i1 += 1
		if i1 - i0 < 3:
			# too narrow for a stone: mortar takes it up to its lower neighbour
			var top := INF
			if i0 > 0:
				top = sky[i0 - 1]
			if i1 < n:
				top = minf(top, sky[i1])
			if top == INF:
				top = lo + 0.1
			for k in range(i0, i1):
				sky[k] = maxf(lo + 0.02, top)
			continue
		var wc := clampi(int(round(rng.randf_range(0.28, 0.7) / CELL)), 1, i1 - i0)
		if (i1 - i0) - wc > 0 and (i1 - i0) - wc < 4:
			wc = i1 - i0
		var h: float = heights[rng.randi() % heights.size()]
		for t in [sky[i0 - 1] if i0 > 0 else -1.0, sky[i1] if i1 < n else -1.0]:
			if t > 0.0 and t - lo > 0.12 and t - lo < 0.5 and rng.randf() < 0.55:
				h = t - lo
		h = minf(h, y_to - lo)
		if y_to - (lo + h) < 0.12:
			h = y_to - lo
		# near an opening (or outside a worn patch) try smaller stones
		var fit := Vector2(-1, -1)
		for opt: Vector2 in [Vector2(wc, h), Vector2(maxi(4, wc * 2 / 3), h), Vector2(maxi(4, wc / 2), h),
				Vector2(maxi(4, wc / 2), minf(h, 0.18)), Vector2(4, minf(h, 0.15))]:
			var oc := mini(int(opt.x), i1 - i0)
			var a0 := s_from + i0 * CELL
			var a1 := a0 + oc * CELL
			var g := gmid_offset(surf, a0, a1)
			var y0 := g + lo
			var y1: float = g + lo + opt.y
			if skip.is_valid() and skip.call(a0, a1, y0, y1):
				continue
			if veto.is_valid() and veto.call(a0, a1, y0, y1):
				continue
			fit = Vector2(oc, opt.y)
			break
		if fit.x < 0.0:
			sky[i0] = lo + CELL
			continue
		wc = int(fit.x)
		h = fit.y
		for k in range(i0, i0 + wc):
			sky[k] = lo + h
		var s0 := s_from + i0 * CELL
		var s1 := s0 + wc * CELL
		var a: Dictionary = surf.call(s0)
		var c: Dictionary = surf.call((s0 + s1) * 0.5)
		var e: Dictionary = surf.call(s1)
		var gy: float = c.g + lo
		var yb := maxf(gy, maxf(a.low, e.low)) + BJ * 0.5
		var yt := minf(gy + h, minf(a.top, e.top)) - BJ * 0.5
		if yt - yb < 0.07 or _blocked(a, (yb + yt) * 0.5) or _blocked(e, (yb + yt) * 0.5):
			continue
		var p0: Vector3 = a.p
		var p1: Vector3 = e.p
		var chord := p1 - p0
		var w := chord.length() - BJ
		if w < 0.1:
			continue
		var u := chord.normalized()
		var v := (Vector3.UP + u * rng.randf_range(-0.02, 0.02)).normalized()
		var o := p0 + u * (BJ * 0.5) + Vector3.UP * yb
		var depth := DEPTH * rng.randf_range(0.8, 1.45)
		stone(mb, o, u, v, c.n, w, yt - yb, depth, broken_color(base, rng), rng, Vector2(s0, yb), 0.0, 0.026)


## Grey stone, many blocks washed ochre or olive by lichen and sun.
static func broken_color(base: Color, rng: RandomNumberGenerator) -> Color:
	var k := rng.randf_range(0.88, 1.08)
	var c := Color(base.r * k, base.g * k, base.b * k, 1.0)
	var lichen := [Color(0.74, 0.73, 0.52), Color(0.79, 0.75, 0.53), Color(0.68, 0.69, 0.50), Color(0.76, 0.70, 0.48)]
	var amt := pow(rng.randf(), 1.6) * 0.8
	var t: Color = lichen[rng.randi() % lichen.size()]
	c = c.lerp(Color(t.r * k, t.g * k, t.b * k, 1.0), amt)
	if rng.randf() < 0.08:
		c = c.darkened(0.12)
	return Color(clampf(c.r, 0, 1), clampf(c.g, 0, 1), clampf(c.b, 0, 1), 1.0)


## Uncoursed polygonal rubble: a jittered grid of seeds cut into Voronoi
## cells, each cell inset by a mortar joint and raised as a cushioned stone.
static func lay_rubble(mb: MeshBuilder, surf: Callable, s_from: float, s_to: float, y_from: float, y_to: float,
		base: Color, rng: RandomNumberGenerator, skip := Callable(), veto := Callable()) -> void:
	const SP := 0.46
	var nx := int(ceil((s_to - s_from) / SP)) + 2
	var ny := int(ceil((y_to - y_from) / (SP * 0.8))) + 2
	var seeds: Array[Vector2] = []
	for j in ny:
		for i in nx:
			var sx := s_from + (i - 0.5 + (0.5 if j % 2 == 1 else 0.0)) * SP + rng.randf_range(-0.3, 0.3) * SP
			var sy := y_from + (j - 0.5) * SP * 0.8 * lerpf(1.0, 0.85, float(j) / ny) + rng.randf_range(-0.25, 0.25) * SP
			seeds.append(Vector2(sx, sy))
	for idx in seeds.size():
		var p := seeds[idx]
		var cell := PackedVector2Array([p + Vector2(-SP, -SP), p + Vector2(SP, -SP), p + Vector2(SP, SP), p + Vector2(-SP, SP)])
		for q in seeds:
			if q == p or q.distance_squared_to(p) > SP * SP * 4.0:
				continue
			# keep the half-plane closer to p than to q
			var mid := (p + q) * 0.5
			var d := (q - p).normalized()
			var t := Vector2(-d.y, d.x)
			var half := PackedVector2Array([mid + t * 4.0, mid + t * 4.0 - d * 4.0, mid - t * 4.0 - d * 4.0, mid - t * 4.0])
			var clipped := Geometry2D.intersect_polygons(cell, half)
			if clipped.is_empty():
				cell = PackedVector2Array()
				break
			cell = clipped[0]
		if cell.size() < 3:
			continue
		var inset := Geometry2D.offset_polygon(cell, -0.012)
		if inset.is_empty():
			continue
		cell = inset[0]
		# clip to the wall face outline around this stone
		var bb := Rect2(cell[0], Vector2.ZERO)
		for v in cell:
			bb = bb.expand(v)
		var k0: Dictionary = surf.call(clampf(bb.position.x, s_from, s_to))
		var k1: Dictionary = surf.call(clampf(bb.end.x, s_from, s_to))
		var km: Dictionary = surf.call(clampf(bb.get_center().x, s_from, s_to))
		var g: float = km.g
		var lo := maxf(maxf(k0.low, k1.low), km.low) - g
		var hi := minf(minf(k0.top, k1.top), km.top) - g
		var rect := PackedVector2Array([Vector2(s_from, lo), Vector2(s_to, lo), Vector2(s_to, hi), Vector2(s_from, hi)])
		var cl := Geometry2D.intersect_polygons(cell, rect)
		if cl.is_empty():
			continue
		cell = cl[0]
		if cell.size() < 3 or absf(_area(cell)) < 0.012:
			continue
		bb = Rect2(cell[0], Vector2.ZERO)
		for v in cell:
			bb = bb.expand(v)
		if skip.is_valid() and skip.call(bb.position.x, bb.end.x, bb.position.y + g, bb.end.y + g):
			continue
		if veto.is_valid() and veto.call(bb.position.x, bb.end.x, bb.position.y + g, bb.end.y + g):
			continue
		var n: Vector3 = km.n
		var depth := DEPTH * rng.randf_range(0.9, 1.4)
		var col := _glade_color(stone_color(base, rng), base, bb.get_center().y, rng)
		var centre2 := Vector2.ZERO
		for v in cell:
			centre2 += v
		centre2 /= cell.size()
		var back: Array[Vector3] = []
		var front: Array[Vector3] = []
		for v in cell:
			var k: Dictionary = surf.call(clampf(v.x, s_from, s_to))
			var bp: Vector3 = k.p + Vector3.UP * (v.y + g)
			back.append(bp)
			var inward := (centre2 - v).normalized() * minf(0.035, (centre2 - v).length() * 0.3)
			var kf: Dictionary = surf.call(clampf(v.x + inward.x, s_from, s_to))
			front.append(kf.p + Vector3.UP * (v.y + inward.y + g) + n * depth)
		var kc: Dictionary = surf.call(clampf(centre2.x, s_from, s_to))
		var top: Vector3 = kc.p + Vector3.UP * (centre2.y + g) + n * (depth + minf(bb.size.x, bb.size.y) * 0.18)
		var uc := Vector2(centre2.x, centre2.y + g)
		for i in cell.size():
			var j := (i + 1) % cell.size()
			var ui := Vector2(cell[i].x, cell[i].y + g)
			var uj := Vector2(cell[j].x, cell[j].y + g)
			var out_i := (front[i] - top).normalized()
			var out_j := (front[j] - top).normalized()
			var ni := (n + out_i * 0.5).normalized()
			var nj := (n + out_j * 0.5).normalized()
			_tri_n(mb, front[i], front[j], top, ni, nj, n, col, ui, uj, uc, n)
			var side := ((front[i] + front[j]) * 0.5 - top).normalized()
			var sn := (side + n * 0.3).normalized()
			_tri_n(mb, back[i], back[j], front[j], sn, sn, nj, col, ui, uj, uj, side)
			_tri_n(mb, back[i], front[j], front[i], sn, nj, ni, col, ui, uj, ui, side)


static func _area(poly: PackedVector2Array) -> float:
	var a := 0.0
	for i in poly.size():
		var j := (i + 1) % poly.size()
		a += poly[i].x * poly[j].y - poly[j].x * poly[i].y
	return a * 0.5
