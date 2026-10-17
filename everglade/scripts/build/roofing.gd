class_name Roofing
extends RefCounted
## Individually laid roof tiles, as Tiny Glade lays them: chunky, rounded
## little slabs in staggered courses from the eave up to the ridge, each
## overlapping the one below with its lower edge kicked up off the roof (so
## every course casts a soft shadow line), every tile a touch wonky and its
## own shade. Ridges and hips are capped with round ridge tiles.

const COURSE := 0.235    # exposed length of each course along the slope
const TILE_LEN := 0.33
const TILE_W := 0.3
const LIFT := 0.05
const THICK := 0.05


static func tile_color(base: Color, rng: RandomNumberGenerator) -> Color:
	var k := rng.randf_range(0.82, 1.12)
	var c := Color(base.r * k, base.g * k, base.b * k, 1.0)
	# a patchwork of shades: some tiles warmer, some cooler
	var r := rng.randf()
	if r < 0.22:
		c = c.lerp(Color(c.r * 1.1, c.g * 0.97, c.b * 0.88), 0.7)
	elif r < 0.4:
		c = c.lerp(Color(c.r * 0.9, c.g * 1.0, c.b * 1.1), 0.7)
	elif r < 0.46:
		c = c.darkened(0.2)
	elif r < 0.49:
		c = c.lerp(Color(0.42, 0.48, 0.30), 0.35)
	return Color(minf(c.r, 1.0), minf(c.g, 1.0), minf(c.b, 1.0), 1.0)


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


## One chunky tile: a soft-edged slab from its kicked-up lower edge at o
## (width w along `along`) up the slope by up_dir.
static func _tile(mb: MeshBuilder, o: Vector3, along: Vector3, up_dir: Vector3, n: Vector3, w: float, lift: float, col: Color) -> void:
	var low := o + along * (w * 0.5) + n * (lift + THICK * 0.5)
	var high := o + along * (w * 0.5) + up_dir + n * (THICK * 0.5 + 0.004)
	var y := high - low
	var len := y.length()
	if len < 0.02:
		return
	y /= len
	var x := (along - y * along.dot(y)).normalized()
	var z := x.cross(y)
	if z.dot(n) < 0.0:
		z = -z
		x = -x
	mb.bevel_box(Transform3D(Basis(x, y, z), (low + high) * 0.5), Vector3(w, len, THICK), 0.02, col)


## Round ridge tiles capping a ridge or hip from a to b.
static func ridge(mb: MeshBuilder, a: Vector3, b: Vector3, base: Color, rng: RandomNumberGenerator, r := 0.12) -> void:
	var d := b - a
	var L := d.length()
	if L < 0.05:
		return
	var ax := d / L
	var side := ax.cross(Vector3.UP)
	if side.length_squared() < 1e-6:
		side = Vector3.RIGHT
	side = side.normalized()
	var up := side.cross(ax).normalized()
	if up.y < 0.0:
		up = -up
	var count := maxi(1, int(round(L / 0.34)))
	const SEG := 8
	for k in count:
		var c0 := a + d * (float(k) / count) + ax * 0.012
		var c1 := a + d * (float(k + 1) / count) - ax * 0.012
		var col := tile_color(base, rng).darkened(0.06)
		var rr := r * rng.randf_range(0.95, 1.05)
		var prev0 := Vector3.ZERO
		var prev1 := Vector3.ZERO
		var prev_n := Vector3.ZERO
		for i in SEG + 1:
			var t := PI * i / SEG
			var nn := side * cos(t) + up * sin(t)
			var p0 := c0 + nn * rr
			var p1 := c1 + nn * rr
			if i > 0:
				mb.quad_facing(prev0, prev1, p1, p0, (prev_n + nn).normalized(), col, prev_n, prev_n, nn, nn)
				# end caps
				mb.tri_facing(c0, prev0, p0, -ax, col.darkened(0.1))
				mb.tri_facing(c1, prev1, p1, ax, col.darkened(0.1))
			prev0 = p0
			prev1 = p1
			prev_n = nn


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
			var o := ring_c + d0 * r_low + Vector3.UP * (y_low - ring_y)
			var o_up := ring_c + mid * r_up * cos(PI * 0.46 / count) + Vector3.UP * (y_up - ring_y)
			var w := (d1 - d0).length() * r_low
			var along := (d1 - d0).normalized()
			_tile(mb, o, along, o_up - (o + along * w * 0.5), n, w, lift, col)
