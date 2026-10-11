class_name WallView
extends Node3D
## Freehand stone wall. Follows the terrain, grows battlements when tall and
## opens into arches (or simple gaps when low) wherever a path crosses it.

const SPACING := 0.25

var data: Dictionary
var body: StaticBody3D
var mesh_instance: MeshInstance3D
var ivy: MultiMeshInstance3D
var material: ShaderMaterial
var perches: Array[Vector3] = []


func build(d: Dictionary, terrain: Terrain, openings: Array = [], preview := false) -> void:
	data = d
	for c in get_children():
		c.free()
	perches.clear()
	var pts: PackedVector2Array = d.pts
	if pts.size() < 2 or Geo.length(pts) < 0.3:
		return
	var h: float = d.get("h", 2.4)
	var col: Color = d.get("col", Catalog.STONE_COLORS[0])
	var thick := clampf(0.5 + h * 0.05, 0.55, 0.95)
	var total := Geo.length(pts)
	var stone := Color(col.r, col.g, col.b, 0.25)
	var cap := Color(col.r * 0.9, col.g * 0.9, col.b * 0.9, 0.25)

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
		samples.append({"s": s, "p": Vector3(p.x, 0, p.y), "n": nrm, "low": low, "top": top, "hole": hole, "arch": arch, "g": g})

	var mb := MeshBuilder.new()
	var ht := thick * 0.5
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
			_pillar(mb, S, thick, h, col)
		if prev_open:
			mb.quad(b_l, f_l, f_t, b_t, stone, Vector2(0, S.low), Vector2(thick, S.low), Vector2(thick, S.top), Vector2(0, S.top))
			_pillar(mb, S, thick, h, col)

	# battlements on tall walls
	if tall:
		var step := 1.05
		var k := 0.4
		while k < total - 0.3:
			var idx := _nearest(samples, k)
			var S: Dictionary = samples[idx]
			if not S.hole:
				var t2 := Geo.tangent_at(pts, k)
				var basis := DecoMerge.along(Vector3(t2.x, 0, t2.y))
				var top: float = S.top
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
	var min_g := INF
	var max_t := -INF
	for S in samples:
		min_g = minf(min_g, S.g)
		max_t = maxf(max_t, S.top)
	material.set_shader_parameter("base_height", min_g)
	material.set_shader_parameter("top_height", max_t + 0.6)

	# lanterns flanking archways, ivy, collision
	var deco := DecoMerge.new()
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
	ivy = Ivy.build(faces, int(d.id) * 31 + 7, 0.8)
	add_child(ivy)
	Ivy.set_growth(ivy, d.get("ivy", 0.0))

	body = StaticBody3D.new()
	body.collision_layer = 2
	body.set_meta("kind", "wall")
	body.set_meta("id", d.id)
	var cs := CollisionShape3D.new()
	cs.shape = mesh_instance.mesh.create_trimesh_shape()
	body.add_child(cs)
	add_child(body)


func _pillar(mb: MeshBuilder, S: Dictionary, thick: float, h: float, col: Color) -> void:
	if h < 1.0:
		return
	var c := Color(col.r * 0.95, col.g * 0.95, col.b * 0.95, 1.0)
	var basis := DecoMerge.facing(S.n)
	var top: float = S.top
	var low: float = S.low
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
