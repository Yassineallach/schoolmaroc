class_name Roofing
extends RefCounted
## Individually laid roof tiles. Courses run from the eave up to the ridge,
## each tile overlapping the one below with its lower lip lifted off the roof
## so every course casts a thin shadow line. Tiles are staggered by half a
## tile per course and vary slightly in width, lift and colour (the odd
## darker, weathered or mossy tile) for a handmade look.

const COURSE := 0.2      # exposed length of each course along the slope
const TILE_LEN := 0.27
const TILE_W := 0.25
const LIFT := 0.035


static func tile_color(base: Color, rng: RandomNumberGenerator) -> Color:
	var k := rng.randf_range(0.86, 1.08)
	var c := Color(base.r * k, base.g * k, base.b * k, 1.0)
	var r := rng.randf()
	if r < 0.06:
		c = c.darkened(0.18)
	elif r < 0.09:
		c = c.lerp(Color(0.42, 0.48, 0.30), 0.35)
	return c


## Tiles over a planar quad slope given by its ridge edge (rl, rr) and eave
## edge (el, er); rl == rr gives a hip triangle.
static func slope(mb: MeshBuilder, rl: Vector3, rr: Vector3, el: Vector3, er: Vector3, base: Color, rng: RandomNumberGenerator) -> void:
	var ridge_mid := (rl + rr) * 0.5
	var eave_mid := (el + er) * 0.5
	var down := eave_mid - ridge_mid
	var slant := down.length()
	if slant < 0.2:
		return
	var n := (er - el).cross(ridge_mid - eave_mid).normalized()
	if n.y < 0.0:
		n = -n
	var courses := maxi(1, int(ceil(slant / COURSE)))
	for c in courses:
		# course c counts up from the eave
		var f_low := 1.0 - float(c) / courses
		var f_up := maxf(0.0, f_low - TILE_LEN / slant)
		var left := rl.lerp(el, f_low)
		var right := rr.lerp(er, f_low)
		var width := left.distance_to(right)
		if width < 0.1:
			continue
		var along := (right - left).normalized()
		var up_dir := (rl.lerp(el, f_up) - left)
		var stagger := (0.5 if c % 2 == 1 else 0.0) * TILE_W
		var x := -stagger
		while x < width - 0.02:
			var w := TILE_W * rng.randf_range(0.88, 1.08)
			var x0 := maxf(x, 0.0)
			var x1 := minf(x + w, width)
			x += w
			if x1 - x0 < 0.06:
				continue
			_tile(mb, left + along * (x0 + 0.008), along, up_dir, n, x1 - x0 - 0.016, LIFT * rng.randf_range(0.7, 1.2), tile_color(base, rng))


static func _tile(mb: MeshBuilder, o: Vector3, along: Vector3, up_dir: Vector3, n: Vector3, w: float, lift: float, col: Color) -> void:
	var bl := o + n * lift
	var br := o + along * w + n * lift
	var tl := o + up_dir + n * 0.006
	var tr := o + along * w + up_dir + n * 0.006
	var top_n := up_dir.normalized().cross(along).normalized()
	if top_n.dot(n) < 0.0:
		top_n = -top_n
	mb.quad_facing(bl, br, tr, tl, top_n, col)
	# lifted lower lip and its two small cheeks
	var pl := o
	var pr := o + along * w
	var lip_n := (-up_dir.normalized() + n * 0.3).normalized()
	mb.quad_facing(pl, pr, br, bl, lip_n, col.darkened(0.08))
	mb.tri_facing(pl, bl, tl, -along, col.darkened(0.12))
	mb.tri_facing(pr, br, tr, along, col.darkened(0.12))


## Tiles over a cone from the apex down to the eave ring.
static func cone(mb: MeshBuilder, apex: Vector3, ring_y: float, radius: float, base: Color, rng: RandomNumberGenerator) -> void:
	var ring_c := Vector3(apex.x, ring_y, apex.z)
	var slant := Vector2(radius, apex.y - ring_y).length()
	var courses := maxi(1, int(ceil(slant / COURSE)))
	for c in courses:
		var f_low := 1.0 - float(c) / courses
		var f_up := maxf(0.0, f_low - TILE_LEN / slant)
		var r_low := radius * f_low
		if r_low < 0.15:
			continue
		var y_low := lerpf(apex.y, ring_y, f_low)
		var r_up := radius * f_up
		var y_up := lerpf(apex.y, ring_y, f_up)
		var count := maxi(6, int(TAU * r_low / TILE_W))
		var off := rng.randf() * TAU
		for k in count:
			var a0 := off + TAU * k / count
			var a1 := off + TAU * (k + 0.92) / count
			var d0 := Vector3(cos(a0), 0, sin(a0))
			var d1 := Vector3(cos(a1), 0, sin(a1))
			var mid := (d0 + d1).normalized()
			var n := (mid * (apex.y - ring_y) / slant + Vector3.UP * radius / slant).normalized()
			var lift := LIFT * rng.randf_range(0.7, 1.2)
			var col := tile_color(base, rng)
			var bl := ring_c + d0 * r_low + Vector3.UP * (y_low - ring_y) + n * lift
			var br := ring_c + d1 * r_low + Vector3.UP * (y_low - ring_y) + n * lift
			var tl := ring_c + d0 * r_up + Vector3.UP * (y_up - ring_y) + n * 0.006
			var tr := ring_c + d1 * r_up + Vector3.UP * (y_up - ring_y) + n * 0.006
			mb.quad_facing(bl, br, tr, tl, n, col)
			mb.quad_facing(bl - n * lift, br - n * lift, br, bl, (mid + n * 0.3).normalized(), col.darkened(0.08))
