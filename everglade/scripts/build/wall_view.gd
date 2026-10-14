class_name WallView
extends Node3D
## Freehand stone wall. Follows the terrain, grows battlements when tall and
## opens into arches (or simple gaps when low) wherever a path crosses it.

const SPACING := 0.25

var data: Dictionary
var body: StaticBody3D
var mesh_instance: MeshInstance3D
var ivy: Node3D
var material: ShaderMaterial
var perches: Array[Vector3] = []
var lamps: Array[Vector3] = []   # world positions of wall lanterns (lit at night)


func build(d: Dictionary, terrain: Terrain, openings: Array = [], preview := false) -> void:
	data = d
	for c in get_children():
		c.free()
	perches.clear()
	lamps.clear()
	# doors (paths ending at the wall) are separate from pass-through openings
	var doors: Array = openings.filter(func(o): return o.has("door"))
	openings = openings.filter(func(o): return not o.has("door"))
	var pts: PackedVector2Array = d.pts
	if pts.size() < 2 or Geo.length(pts) < 0.3:
		return
	var h: float = d.get("h", 2.4)
	var col: Color = d.get("col", Catalog.STONE_COLORS[0])
	var thick := clampf(0.5 + h * 0.05, 0.55, 0.95)
	var total := Geo.length(pts)
	# finished walls: a recessed mortar core faced with individual stones;
	# previews (while drawing) stay a light flat stone volume
	var masonry := not preview
	# "rendered": warm lime plaster over the stonework, with quoins, a stone
	# course under the battlements and worn patches where stones show through
	var rendered: bool = d.get("style", "stone") == "rendered"
	var stone := Masonry.mortar_color(col) if masonry else Color(col.r, col.g, col.b, 0.25)
	if masonry and rendered:
		stone = Masonry.plaster_color(col)
	var cap := stone if masonry else Color(col.r * 0.9, col.g * 0.9, col.b * 0.9, 0.25)
	var rng := RandomNumberGenerator.new()
	rng.seed = int(d.get("id", 1)) * 7919 + 13

	# ---- sample positions (uniform + exact opening edges)
	var s_list: Array[float] = []
	var n := maxi(2, int(ceil(total / SPACING)))
	for i in n + 1:
		s_list.append(total * i / n)
	for o in openings:
		for e in [o.s - o.w * 0.5, o.s + o.w * 0.5]:
			if e > 0.05 and e < total - 0.05:
				s_list.append(e)
	s_list.sort()

	var tall := h >= 3.2
	var samples: Array = []
	var ground_raw: Array[float] = []
	for s in s_list:
		var p := Geo.point_at(pts, s)
		ground_raw.append(terrain.height_at_v(p))
	# smooth the top line so walls do not jitter over bumps
	var smooth_g: Array[float] = []
	for i in ground_raw.size():
		var acc := 0.0
		var cnt := 0
		for k in range(maxi(0, i - 3), mini(ground_raw.size(), i + 4)):
			acc += ground_raw[k]
			cnt += 1
		smooth_g.append(acc / cnt)
	for i in s_list.size():
		var s: float = s_list[i]
		var p := Geo.point_at(pts, s)
		var t := Geo.tangent_at(pts, s)
		var nrm := Vector3(-t.y, 0, t.x)
		var g := ground_raw[i]
		var top := smooth_g[i] + h
		var low := minf(g, smooth_g[i]) - 0.45
		var hole := false
		var arch := false
		for o in openings:
			var r: float = o.w * 0.5
			var dd := absf(s - o.s)
			if dd <= r + 0.001:
				var spring := minf(1.7, h - 0.45 - r)
				if spring < 0.9:
					hole = dd < r - 0.01
				else:
					low = smooth_g[i] + spring + sqrt(maxf(0.0, r * r - dd * dd))
					arch = true
		samples.append({"s": s, "p": Vector3(p.x, 0, p.y), "n": nrm, "low": low, "top": top, "hole": hole, "arch": arch, "g": g, "base": smooth_g[i]})

	var mb := MeshBuilder.new()
	# facing pattern (Masonry.PATTERNS); the Quaternius "kit" stones collect
	# into their own textured mesh
	Masonry.pattern = d.get("pattern", "classic")
	Masonry.kit_st = SurfaceTool.new() if Masonry.pattern == "kit" and masonry else null
	if Masonry.kit_st:
		Masonry.kit_st.begin(Mesh.PRIMITIVE_TRIANGLES)
	# the stones stand proud of the core by Masonry.DEPTH on each side
	var ht := thick * 0.5 - (Masonry.DEPTH if masonry and not rendered else 0.0)
	if masonry and rendered:
		ht = thick * 0.5 - 0.025
	for i in samples.size() - 1:
		var A: Dictionary = samples[i]
		var B: Dictionary = samples[i + 1]
		if A.hole or B.hole:
			continue
		var fa_l: Vector3 = A.p + A.n * ht + Vector3.UP * A.low
		var fb_l: Vector3 = B.p + B.n * ht + Vector3.UP * B.low
		var fa_t: Vector3 = A.p + A.n * ht + Vector3.UP * A.top
		var fb_t: Vector3 = B.p + B.n * ht + Vector3.UP * B.top
		var ba_l: Vector3 = A.p - A.n * ht + Vector3.UP * A.low
		var bb_l: Vector3 = B.p - B.n * ht + Vector3.UP * B.low
		var ba_t: Vector3 = A.p - A.n * ht + Vector3.UP * A.top
		var bb_t: Vector3 = B.p - B.n * ht + Vector3.UP * B.top
		var sa: float = A.s
		var sb: float = B.s
		var An: Vector3 = A.n
		var Bn: Vector3 = B.n
		mb.quad_n(fa_l, fb_l, fb_t, fa_t, An, Bn, Bn, An, stone,
				Vector2(sa, A.low), Vector2(sb, B.low), Vector2(sb, B.top), Vector2(sa, A.top))
		mb.quad_n(bb_l, ba_l, ba_t, bb_t, -Bn, -An, -An, -Bn, stone,
				Vector2(-sb, B.low), Vector2(-sa, A.low), Vector2(-sa, A.top), Vector2(-sb, B.top))
		mb.quad(fa_t, fb_t, bb_t, ba_t, cap, Vector2(sa, 0), Vector2(sb, 0), Vector2(sb, thick), Vector2(sa, thick))
		if A.arch or B.arch:
			mb.quad(ba_l, bb_l, fb_l, fa_l, stone, Vector2(sa, 0), Vector2(sb, 0), Vector2(sb, thick), Vector2(sa, thick))
	# end caps (wall ends and gap edges)
	for i in samples.size():
		var S: Dictionary = samples[i]
		if S.hole:
			continue
		var prev_open: bool = i == 0 or samples[i - 1].hole
		var next_open: bool = i == samples.size() - 1 or samples[i + 1].hole
		var f_l: Vector3 = S.p + S.n * ht + Vector3.UP * S.low
		var f_t: Vector3 = S.p + S.n * ht + Vector3.UP * S.top
		var b_l: Vector3 = S.p - S.n * ht + Vector3.UP * S.low
		var b_t: Vector3 = S.p - S.n * ht + Vector3.UP * S.top
		if next_open:
			mb.quad(f_l, b_l, b_t, f_t, stone, Vector2(0, S.low), Vector2(thick, S.low), Vector2(thick, S.top), Vector2(0, S.top))
			_pillar(mb, S, thick, h, col, masonry, rng)
		if prev_open:
			mb.quad(b_l, f_l, f_t, b_t, stone, Vector2(0, S.low), Vector2(thick, S.low), Vector2(thick, S.top), Vector2(0, S.top))
			_pillar(mb, S, thick, h, col, masonry, rng)

	if masonry:
		_lay_stones(mb, samples, openings, doors, total, h, thick, ht, col, rng, rendered)

	# battlements on tall walls
	if tall:
		var step := 1.3 if masonry else 1.05
		var k := 0.45
		while k < total - 0.3:
			var idx := _nearest(samples, k)
			var S: Dictionary = samples[idx]
			if not S.hole:
				var t2 := Geo.tangent_at(pts, k)
				var basis := DecoMerge.along(Vector3(t2.x, 0, t2.y))
				var top: float = S.top
				if masonry:
					# chunky, soft-edged merlon blocks on the coping, each a
					# little different in size and set
					var y0 := top + 0.13
					var mh := rng.randf_range(0.5, 0.62)
					var mw := rng.randf_range(0.66, 0.78)
					var tw := Basis(Vector3.UP, rng.randf_range(-0.04, 0.04))
					mb.bevel_box(Transform3D(basis * tw, S.p + Vector3.UP * (y0 + mh * 0.5)), Vector3(mw, mh, thick + 0.08), 0.075, Masonry.stone_color(col, rng))
				else:
					mb.box(Transform3D(basis, S.p + Vector3.UP * (top + 0.25)), Vector3(0.55, 0.5, thick + 0.06), stone)
				perches.append(S.p + Vector3.UP * (top + 0.5))
			k += step
	else:
		var k2 := 0.6
		while k2 < total:
			var S2: Dictionary = samples[_nearest(samples, k2)]
			if not S2.hole:
				perches.append(S2.p + Vector3.UP * S2.top)
			k2 += 2.5

	material = ModelLib.new_arch_material()
	mesh_instance = MeshInstance3D.new()
	mesh_instance.name = "Mesh"
	mesh_instance.mesh = mb.commit()
	mesh_instance.material_override = material
	add_child(mesh_instance)
	if Masonry.kit_st != null:
		var km := MeshInstance3D.new()
		km.name = "KitStones"
		km.mesh = Masonry.kit_st.commit()
		km.material_override = ModelLib.kit_material_for("Tex__T_RockTrim_BaseColor.png")
		add_child(km)
	Masonry.kit_st = null
	Masonry.pattern = "classic"
	var min_g := INF
	var max_t := -INF
	for S in samples:
		min_g = minf(min_g, S.g)
		max_t = maxf(max_t, S.top)
	material.set_shader_parameter("base_height", min_g)
	material.set_shader_parameter("top_height", max_t + 0.6)

	# lanterns flanking archways, doors where paths end, ivy, collision
	var deco := DecoMerge.new()
	for o in doors:
		var side: float = o.door
		var ds := _sample_at(samples, o.s)
		var dn: Vector3 = ds.n * side
		var face: Vector3 = ds.p + dn * (thick * 0.5 - 0.02)
		deco.add("door", Transform3D(DecoMerge.facing(dn), face + Vector3.UP * (terrain.height_at(face.x, face.z) - 0.04)))
		var t4 := Geo.tangent_at(pts, o.s)
		var lp: Vector3 = face + Vector3(t4.x, 0, t4.y) * 0.95 + dn * 0.05
		deco.add("wall_lantern", Transform3D(Basis.looking_at(dn, Vector3.UP), lp + Vector3.UP * (terrain.height_at(lp.x, lp.z) + 2.0)))
		lamps.append(lp + Vector3.UP * (terrain.height_at(lp.x, lp.z) + 1.9) + dn * 0.25)
	for o in openings:
		var r: float = o.w * 0.5
		var spring2 := minf(1.7, h - 0.45 - r)
		if spring2 < 0.9 or o.s - r - 0.4 < 0.0:
			continue
		var p := Geo.point_at(pts, o.s - r - 0.35)
		var t3 := Geo.tangent_at(pts, o.s)
		var nrm3 := Vector3(-t3.y, 0, t3.x)
		var y := terrain.height_at_v(p) + 1.9
		deco.add("wall_lantern", Transform3D(Basis.looking_at(nrm3, Vector3.UP), Vector3(p.x, y, p.y) + nrm3 * ht))
		lamps.append(Vector3(p.x, y - 0.1, p.y) + nrm3 * (ht + 0.25))
	deco.apply_to(self)

	if preview:
		return
	var faces: Array = []
	var seg := 0
	while seg < samples.size() - 1:
		var j := mini(seg + 8, samples.size() - 1)
		var A2: Dictionary = samples[seg]
		var B2: Dictionary = samples[j]
		if not (A2.hole or B2.hole or A2.arch or B2.arch):
			faces.append({"a": A2.p + A2.n * ht + Vector3.UP * A2.g, "b": B2.p + B2.n * ht + Vector3.UP * B2.g, "n": A2.n, "h": h})
			faces.append({"a": B2.p - B2.n * ht + Vector3.UP * B2.g, "b": A2.p - A2.n * ht + Vector3.UP * A2.g, "n": -A2.n, "h": h})
		seg = j
	ivy = Ivy.build(faces, int(d.id) * 31 + 7, 1.7)
	add_child(ivy)
	Ivy.set_growth(ivy, d.get("ivy", 0.0))

	body = StaticBody3D.new()
	body.collision_layer = 2
	body.set_meta("kind", "wall")
	body.set_meta("id", d.id)
	var cs := CollisionShape3D.new()
	cs.shape = _collision_shell(samples, thick * 0.5 + 0.04)
	body.add_child(cs)
	add_child(body)


func _pillar(mb: MeshBuilder, S: Dictionary, thick: float, h: float, col: Color, masonry := false, rng: RandomNumberGenerator = null) -> void:
	if h < 1.0:
		return
	var c := Color(col.r * 0.95, col.g * 0.95, col.b * 0.95, 1.0)
	var basis := DecoMerge.facing(S.n)
	var top: float = S.top
	var low: float = S.low
	if masonry:
		Masonry.quoins(mb, S.p, S.n, low, top, thick, col, rng)
		mb.bevel_box(Transform3D(basis, S.p + Vector3.UP * (top + 0.08)), Vector3(thick + 0.22, 0.16, thick + 0.22), 0.04, Masonry.stone_color(col, rng))
		if h < 2.0:
			mb.bevel_box(Transform3D(basis, S.p + Vector3.UP * (top + 0.29)), Vector3(0.32, 0.26, 0.32), 0.05, Masonry.stone_color(col, rng))
		return
	mb.box(Transform3D(basis, S.p + Vector3.UP * (top + 0.08)), Vector3(thick + 0.2, 0.16, thick + 0.2), c)
	if h < 2.0:
		mb.box(Transform3D(basis, S.p + Vector3.UP * (top + 0.28)), Vector3(0.32, 0.26, 0.32), c)
	mb.box(Transform3D(basis, S.p + Vector3.UP * ((low + top) * 0.5)), Vector3(thick + 0.12, top - low, thick + 0.12), Color(col.r, col.g, col.b, 0.25))


func _nearest(samples: Array, s: float) -> int:
	var best := 0
	var bd := INF
	for i in samples.size():
		var d: float = absf(samples[i].s - s)
		if d < bd:
			bd = d
			best = i
	return best


func set_ivy(growth: float) -> void:
	Ivy.set_growth(ivy, growth)


func play_build_anim() -> void:
	if material == null:
		return
	material.set_shader_parameter("build_progress", 0.0)
	var tw := create_tween()
	tw.tween_method(func(v): material.set_shader_parameter("build_progress", v), 0.0, 1.0, 0.6).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


## Interpolates the wall's sample line at arclength `s`.
func _sample_at(samples: Array, s: float) -> Dictionary:
	var lo := 0
	var hi := samples.size() - 1
	if s <= samples[0].s:
		hi = 1
	elif s >= samples[hi].s:
		lo = hi - 1
	else:
		while hi - lo > 1:
			var mid := (lo + hi) / 2
			if samples[mid].s <= s:
				lo = mid
			else:
				hi = mid
	var A: Dictionary = samples[lo]
	var B: Dictionary = samples[hi]
	var span: float = B.s - A.s
	var t := clampf((s - A.s) / span, 0.0, 1.0) if span > 1e-5 else 0.0
	var hole: bool = A.hole or B.hole
	return {
		"p": A.p.lerp(B.p, t),
		"n": A.n.lerp(B.n, t).normalized(),
		"base": lerpf(A.base, B.base, t),
		"low": 1e6 if hole else maxf(A.low, B.low),
		"top": minf(A.top, B.top),
	}


## Faces both sides of the wall with stone courses, arches with voussoirs
## and the top with coping stones.
func _lay_stones(mb: MeshBuilder, samples: Array, openings: Array, doors: Array, total: float, h: float, thick: float, ht: float, col: Color, rng: RandomNumberGenerator, rendered := false) -> void:
	var arches: Array = []
	for o in openings:
		var r: float = o.w * 0.5
		var spring := minf(1.7, h - 0.45 - r)
		if spring < 0.9:
			continue
		var c := _sample_at(samples, o.s)
		arches.append({"s": o.s, "r": r, "y": c.base + spring, "c": c})
	var front := func(s: float) -> Dictionary:
		var k := _sample_at(samples, s)
		return {"p": k.p + k.n * ht, "n": k.n, "g": k.base, "low": k.low, "top": k.top}
	var back := func(s: float) -> Dictionary:
		var k := _sample_at(samples, total - s)
		return {"p": k.p - k.n * ht, "n": -k.n, "g": k.base, "low": k.low, "top": k.top}
	# worn patches in the render, where the stonework shows through
	var patches: Array = [[], []]
	if rendered:
		for face in 2:
			var count := int(total * h / 7.0 + rng.randf() * 2.0)
			for i in count:
				patches[face].append(Vector4(rng.randf_range(0.6, total - 0.6), rng.randf_range(0.3, h - 0.6), rng.randf_range(0.35, 0.85), rng.randf_range(0.25, 0.55)))
	var band := func(s0: float, s1: float, y0: float, y1: float, mirrored: bool) -> bool:
		var fs0: float = total - s1 if mirrored else s0
		var fs1: float = total - s0 if mirrored else s1
		# keep doorways clear on the face they open from
		for o in doors:
			if (o.door < 0.0) == mirrored and fs1 > o.s - 0.72 and fs0 < o.s + 0.72:
				var dk := _sample_at(samples, o.s)
				if y0 < dk.base + 2.45:
					return true
		for a in arches:
			var a0: float = (total - s1 if mirrored else s0) - a.s
			var a1: float = (total - s0 if mirrored else s1) - a.s
			var b0: float = y0 - a.y
			var b1: float = y1 - a.y
			if b1 < -0.05:
				continue
			var dx := maxf(maxf(a0, 0.0), -a1)
			var dy := maxf(maxf(b0, 0.0), -b1)
			var dmin := sqrt(dx * dx + dy * dy)
			var fx := maxf(absf(a0), absf(a1))
			var fy := maxf(absf(b0), absf(b1))
			var dmax := sqrt(fx * fx + fy * fy)
			if dmax > a.r - 0.06 and dmin < a.r + 0.36:
				return true
		return false
	# rendered walls only show stones in the top course and worn patches
	var veto := Callable()
	if rendered:
		veto = func(s0: float, s1: float, y0: float, y1: float, mirrored: bool) -> bool:
			var sm: float = total - (s0 + s1) * 0.5 if mirrored else (s0 + s1) * 0.5
			var k := _sample_at(samples, sm)
			if k.top - y1 < 0.34:
				return false
			var rel: float = (y0 + y1) * 0.5 - k.base
			for p in patches[1 if mirrored else 0]:
				var dx: float = (sm - p.x) / p.z
				var dy: float = (rel - p.y) / p.w
				if dx * dx + dy * dy < 1.0:
					return false
			return true
	var veto_f := func(s0, s1, y0, y1): return veto.call(s0, s1, y0, y1, false) if veto.is_valid() else false
	var veto_b := func(s0, s1, y0, y1): return veto.call(s0, s1, y0, y1, true) if veto.is_valid() else false
	Masonry.lay(mb, front, 0.0, total, -0.35, h + 0.1, col, rng, func(s0, s1, y0, y1): return band.call(s0, s1, y0, y1, false), veto_f if rendered else Callable())
	Masonry.lay(mb, back, 0.0, total, -0.35, h + 0.1, col, rng, func(s0, s1, y0, y1): return band.call(s0, s1, y0, y1, true), veto_b if rendered else Callable())
	for a in arches:
		var t := Geo.tangent_at(data.pts, a.s)
		Masonry.voussoirs(mb, a.c.p + Vector3.UP * a.y, Vector3(t.x, 0, t.y), a.c.n, a.r, ht, col, rng)
		# dressed jamb stones up both sides of the opening
		for side in [-1.0, 1.0]:
			var j := _sample_at(samples, a.s + side * (a.r + 0.17))
			Masonry.quoins(mb, j.p, j.n, j.base - 0.3, a.y, thick - 0.1, col, rng)
	# coping stones along the top
	var s := 0.0
	while s < total - 0.05:
		var seg := rng.randf_range(0.42, 0.66)
		var e := minf(s + seg, total)
		var ka := _sample_at(samples, s)
		var kb := _sample_at(samples, e)
		if ka.low < 1e5 and kb.low < 1e5:
			Masonry.coping(mb, ka.p + Vector3.UP * ka.top, kb.p + Vector3.UP * kb.top, thick, col, rng)
		s = e


## A light collision shell (both faces and the top of the wall, following
## its outline) instead of a trimesh of every individual stone.
func _collision_shell(samples: Array, half: float) -> ConcavePolygonShape3D:
	var faces := PackedVector3Array()
	var step := maxi(1, int(0.6 / SPACING))
	var i := 0
	while i < samples.size() - 1:
		var j := mini(i + step, samples.size() - 1)
		var A: Dictionary = samples[i]
		var B: Dictionary = samples[j]
		i = j
		if A.hole or B.hole:
			continue
		var top_a := maxf(A.top + 0.7, A.low)
		var top_b := maxf(B.top + 0.7, B.low)
		var quads := [
			[A.p + A.n * half, B.p + B.n * half],
			[A.p - A.n * half, B.p - B.n * half],
		]
		for q in quads:
			var a0: Vector3 = q[0] + Vector3.UP * A.low
			var b0: Vector3 = q[1] + Vector3.UP * B.low
			var a1: Vector3 = q[0] + Vector3.UP * top_a
			var b1: Vector3 = q[1] + Vector3.UP * top_b
			faces.append_array([a0, b0, b1, a0, b1, a1])
		var fa: Vector3 = A.p + A.n * half + Vector3.UP * top_a
		var fb: Vector3 = B.p + B.n * half + Vector3.UP * top_b
		var ba: Vector3 = A.p - A.n * half + Vector3.UP * top_a
		var bb: Vector3 = B.p - B.n * half + Vector3.UP * top_b
		faces.append_array([fa, fb, bb, fa, bb, ba])
	var shape := ConcavePolygonShape3D.new()
	shape.backface_collision = true
	shape.set_faces(faces)
	return shape
