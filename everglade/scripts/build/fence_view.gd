class_name FenceView
extends Node3D
## Rustic wooden fence: posts follow the drawn line, rails stretch between
## them and a little gate appears wherever a path crosses.

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
	var deco := DecoMerge.new()
	var post_pos: Array[Vector3] = []
	for s in posts:
		var p := Geo.point_at(pts, s)
		var y := terrain.height_at_v(p) - 0.05
		var pos := Vector3(p.x, y, p.y)
		post_pos.append(pos)
		var rot := Basis(Vector3.UP, hash(Vector2(p.x, p.y)) % 100 * 0.01)
		deco.add("fence_post", Transform3D(rot, pos))
		perches.append(pos + Vector3.UP * 1.05)
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
			deco.add("gate", Transform3D(basis * Basis.from_scale(Vector3(seg_len, 1, 1)), center + Vector3.UP * 0.02))
			continue
		# rail: 1 m along +X starting at origin; tilt to follow slope
		var slope := atan2(dir.y, seg_len)
		var rb := basis * Basis(Vector3.BACK, slope)
		deco.add("fence_rail", Transform3D(rb * Basis.from_scale(Vector3(dir.length(), 1, 1)), a3))
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


func play_build_anim() -> void:
	scale = Vector3(1, 0.01, 1)
	var tw := create_tween()
	tw.tween_property(self, "scale", Vector3.ONE, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
