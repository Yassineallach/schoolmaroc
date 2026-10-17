class_name FenceView
extends Node3D
## Rustic wooden fence: posts follow the drawn line, rails stretch between
## them and a little gate appears wherever a path crosses. The "planks"
## style closes the gaps with upright boards (Tiny Glade's wooden fence).

const POST_SPACING := 1.5

var data: Dictionary
var body: StaticBody3D
var perches: Array[Vector3] = []


func build(d: Dictionary, terrain: Terrain, gates: Array = [], preview := false) -> void:
	data = d
	for c in get_children():
		c.free()
	perches.clear()
	var pts: PackedVector2Array = d.pts
	var total := Geo.length(pts)
	if pts.size() < 2 or total < 0.4:
		return
	# post positions along the line
	var posts: Array[float] = []
	var n := maxi(1, int(round(total / POST_SPACING)))
	for i in n + 1:
		posts.append(total * i / n)
	var gate_spans: Array = []
	for g in gates:
		var hw: float = clampf(g.w * 0.5, 0.6, 1.3)
		var a: float = maxf(0.0, g.s - hw)
		var b: float = minf(total, g.s + hw)
		gate_spans.append(Vector2(a, b))
		var kept: Array[float] = []
		for s in posts:
			if s < a - 0.35 or s > b + 0.35:
				kept.append(s)
		kept.append(a)
		kept.append(b)
		kept.sort()
		posts = kept
	var ornate: bool = d.get("style", "wood") == "ornate"
	var post_kind := "fence_pillar" if ornate else "fence_post"
	var rail_kind := "fence_ornate" if ornate else "fence_rail"
	var gate_kind := "gate_ornate" if ornate else "gate"
	var deco := DecoMerge.new()
	var planks: bool = d.get("style", "wood") == "planks"
	var boards := MeshBuilder.new()
	var post_pos: Array[Vector3] = []
	for s in posts:
		var p := Geo.point_at(pts, s)
		var y := terrain.height_at_v(p) - 0.05
		var pos := Vector3(p.x, y, p.y)
		post_pos.append(pos)
		var rot := Basis(Vector3.UP, 0.0 if ornate else hash(Vector2(p.x, p.y)) % 100 * 0.01)
		deco.add(post_kind, Transform3D(rot, pos))
		perches.append(pos + Vector3.UP * (1.5 if ornate else 1.05))
	for i in posts.size() - 1:
		var a3 := post_pos[i]
		var b3 := post_pos[i + 1]
		var mid_s := (posts[i] + posts[i + 1]) * 0.5
		var is_gate := false
		for span in gate_spans:
			if mid_s > span.x and mid_s < span.y:
				is_gate = true
		var dir := b3 - a3
		var flat := Vector3(dir.x, 0, dir.z)
		var seg_len := flat.length()
		if seg_len < 0.05:
			continue
		var basis := DecoMerge.along(flat)
		if is_gate:
			var center := (a3 + b3) * 0.5
			deco.add(gate_kind, Transform3D(basis * Basis.from_scale(Vector3(seg_len, 1, 1)), center + Vector3.UP * 0.02))
			continue
		# rail: 1 m along +X starting at origin; tilt to follow slope
		var slope := atan2(dir.y, seg_len)
		var rb := basis * Basis(Vector3.BACK, slope)
		deco.add(rail_kind, Transform3D(rb * Basis.from_scale(Vector3(dir.length(), 1, 1)), a3))
		if planks:
			_boards(boards, a3, b3, terrain, posts[i])
	if not boards.is_empty():
		deco.add_mesh(boards.commit(), Transform3D.IDENTITY)
	deco.apply_to(self)
	if preview:
		return
	var mi := get_node_or_null("Deco") as MeshInstance3D
	if mi and mi.mesh:
		body = StaticBody3D.new()
		body.collision_layer = 4
		body.set_meta("kind", "fence")
		body.set_meta("id", d.id)
		var cs := CollisionShape3D.new()
		cs.shape = mi.mesh.create_trimesh_shape()
		body.add_child(cs)
		add_child(body)


## Upright boards with soft, rounded tops between two posts, standing on the
## ground (Tiny Glade's plank fence: honey wood, every board its own tone).
func _boards(mb: MeshBuilder, a: Vector3, b: Vector3, terrain: Terrain, s0: float) -> void:
	var flat := Vector3(b.x - a.x, 0, b.z - a.z)
	var l := flat.length()
	var dir := flat / l
	var side := dir.cross(Vector3.UP).normalized()
	var count := maxi(1, int(l / 0.19))
	var w := l / count
	const SEGS := 6
	const DOME := 0.06
	const T := 0.035
	for k in count:
		var c := a + dir * (w * (k + 0.5))
		var g := terrain.height_at(c.x, c.z) - 0.05
		var hh := 1.0 + 0.05 * sin((s0 + k * w) * 5.3)
		var rnd := fposmod(sin((s0 + k * w) * 12.9898) * 43.7, 1.0)
		var col := Color(0.72, 0.54, 0.31).lerp(Color(0.82, 0.64, 0.38), rnd * 0.8) if k % 2 == 0 else Color(0.70, 0.52, 0.30).darkened(rnd * 0.1)
		var start := mb.verts.size()
		var half := (w - 0.025) * 0.5
		mb.box(Transform3D(DecoMerge.along(dir), Vector3(c.x, g + hh * 0.5, c.z) + side * 0.06), Vector3(half * 2.0, hh, T), col)
		# a gentle dome across the top of the board
		var base := Vector3(c.x, g + hh, c.z) + side * 0.06
		var rim: Array[Vector3] = []
		for i in SEGS + 1:
			var t := float(i) / SEGS
			var x := lerpf(-half, half, t)
			rim.append(base + dir * x + Vector3.UP * DOME * sin(PI * t))
		for i in SEGS:
			for sgn in [1.0, -1.0]:
				var off: Vector3 = side * (T * 0.5 * sgn)
				mb.tri_facing(base + off, rim[i] + off, rim[i + 1] + off, side * sgn, col)
			var up := (rim[i + 1] - rim[i]).cross(side).normalized()
			if up.y < 0.0:
				up = -up
			mb.quad_facing(rim[i] + side * T * 0.5, rim[i + 1] + side * T * 0.5, rim[i + 1] - side * T * 0.5, rim[i] - side * T * 0.5, up, col)
		Ornaments._layer(mb, start, Ornaments.M_WOOD)


func play_build_anim() -> void:
	scale = Vector3(1, 0.01, 1)
	var tw := create_tween()
	tw.tween_property(self, "scale", Vector3.ONE, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
