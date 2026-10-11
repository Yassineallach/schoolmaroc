class_name PathView
extends Node3D
## Path decorations: edge cobbles, stepping stones, little arched bridges
## where the path crosses water and stone steps on steep slopes. The path
## surface itself is painted into the terrain mask by the Glade.

var data: Dictionary


func build(d: Dictionary, terrain: Terrain) -> void:
	data = d
	for c in get_children():
		c.free()
	var pts: PackedVector2Array = d.pts
	var total := Geo.length(pts)
	if pts.size() < 2 or total < 0.3:
		return
	var style: String = d.get("style", "dirt")
	var width: float = d.get("w", 1.4)
	var rng := RandomNumberGenerator.new()
	rng.seed = int(d.id) * 977 + 3
	var deco := DecoMerge.new()

	# --- classify samples: land / water
	var step := 0.35
	var n := maxi(2, int(total / step))
	var wet: Array[bool] = []
	for i in n + 1:
		var p := Geo.point_at(pts, total * i / n)
		wet.append(terrain.height_at_v(p) < Terrain.WATER_LEVEL - 0.05)

	# --- bridges over water runs (dirt & cobble paths)
	if style != "stones":
		var i := 0
		while i <= n:
			if not wet[i]:
				i += 1
				continue
			var j := i
			while j <= n and wet[j]:
				j += 1
			var s0 := maxf(0.0, total * i / n - 0.9)
			var s1 := minf(total, total * (j - 1) / n + 0.9)
			_bridge(deco, pts, terrain, s0, s1, width)
			i = j

	# --- surface details
	var s := 0.0
	match style:
		"stones":
			while s < total:
				var p2 := Geo.point_at(pts, s)
				var t := Geo.tangent_at(pts, s)
				var side := Vector2(-t.y, t.x) * rng.randf_range(-0.18, 0.18) * width
				var q := p2 + side
				var gy := terrain.height_at_v(q)
				var y := maxf(gy + 0.04, Terrain.WATER_LEVEL + 0.08)
				var sc := width / 1.2 * rng.randf_range(0.8, 1.1)
				deco.add("stepping_stone", Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(sc, 1, sc)), Vector3(q.x, y, q.y)))
				s += rng.randf_range(0.75, 0.95) * clampf(width, 0.9, 1.5)
		"cobble":
			# a border of chunky stones along both edges
			while s < total:
				var p3 := Geo.point_at(pts, s)
				if terrain.height_at_v(p3) > Terrain.WATER_LEVEL:
					var t3 := Geo.tangent_at(pts, s)
					var nn := Vector2(-t3.y, t3.x)
					for side_sign in [-1.0, 1.0]:
						var q3: Vector2 = p3 + nn * (width * 0.5 + 0.05) * side_sign
						var y3 := terrain.height_at_v(q3)
						deco.add("cobble_a" if rng.randf() < 0.5 else "cobble_b",
								Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(0.8, 1.2)), Vector3(q3.x, y3 + 0.02, q3.y)))
				s += 0.33
		_:
			# a few pebbles scattered along dirt paths
			while s < total:
				var p4 := Geo.point_at(pts, s)
				var t4 := Geo.tangent_at(pts, s)
				var q4 := p4 + Vector2(-t4.y, t4.x) * rng.randf_range(-0.6, 0.6) * width
				if terrain.height_at_v(q4) > Terrain.WATER_LEVEL:
					deco.add("cobble_b", Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(0.35, 0.6)), Vector3(q4.x, terrain.height_at_v(q4), q4.y)))
				s += rng.randf_range(1.2, 2.6)

	# --- stairs on steep slopes
	if style != "stones":
		var k := 0.0
		var last_y := -INF
		while k < total - 0.2:
			var a := Geo.point_at(pts, k)
			var b := Geo.point_at(pts, k + 0.4)
			var ha := terrain.height_at_v(a)
			var hb := terrain.height_at_v(b)
			var slope := absf(hb - ha) / 0.4
			if slope > 0.55 and ha > Terrain.WATER_LEVEL:
				var y := snappedf(ha, 0.2)
				if absf(y - last_y) > 0.1:
					var t5 := Geo.tangent_at(pts, k)
					var basis := DecoMerge.facing(Vector3(t5.x, 0, t5.y)) * Basis.from_scale(Vector3(width * 0.9, 1, 1))
					deco.add("stair_step", Transform3D(basis, Vector3(a.x, y - 0.12, a.y)))
					last_y = y
			k += 0.3

	deco.apply_to(self)


func _bridge(deco: DecoMerge, pts: PackedVector2Array, terrain: Terrain, s0: float, s1: float, width: float) -> void:
	var span := s1 - s0
	if span < 0.5:
		return
	var segs := maxi(1, int(ceil(span)))
	var seg_len := span / segs
	var y0 := maxf(terrain.height_at_v(Geo.point_at(pts, s0)), Terrain.WATER_LEVEL + 0.1)
	var y1 := maxf(terrain.height_at_v(Geo.point_at(pts, s1)), Terrain.WATER_LEVEL + 0.1)
	var arch := clampf(span * 0.12, 0.2, 0.9)
	for i in segs:
		var sa := s0 + i * seg_len
		var sb := sa + seg_len
		var pa := Geo.point_at(pts, sa)
		var pb := Geo.point_at(pts, sb)
		var ta := float(i) / segs
		var tb := float(i + 1) / segs
		var ya := lerpf(y0, y1, ta) + sin(ta * PI) * arch + 0.1
		var yb := lerpf(y0, y1, tb) + sin(tb * PI) * arch + 0.1
		var a3 := Vector3(pa.x, ya, pa.y)
		var b3 := Vector3(pb.x, yb, pb.y)
		var dir := b3 - a3
		var flat := Vector3(dir.x, 0, dir.z)
		var basis := DecoMerge.along(flat) * Basis(Vector3.BACK, atan2(dir.y, flat.length()))
		var w := clampf(width / 1.5, 0.8, 1.8)
		deco.add("bridge_plank", Transform3D(basis * Basis.from_scale(Vector3(dir.length(), 1, w)), a3))
	# ornate lamps guard both ends of the bridge
	for se in [s0, s1]:
		var pe := Geo.point_at(pts, se)
		var te := Geo.tangent_at(pts, se)
		var side := Vector2(-te.y, te.x) * (width * 0.5 + 0.55)
		for sgn in [-1.0, 1.0]:
			var q: Vector2 = pe + side * sgn
			deco.add("lantern", Transform3D(Basis.IDENTITY.scaled(Vector3.ONE * 0.75), Vector3(q.x, terrain.height_at_v(q) - 0.05, q.y)))
