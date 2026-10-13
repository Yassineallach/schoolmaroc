class_name Backdrop
extends Node3D
## Distant scenery beyond the play area, picked by the glade's template:
## jade-lake karst peaks around the lake village, grey cliffs and golden
## woods behind the town, rolling woods around open meadows. It sits in the
## depth fog so it reads as painted, hazy layers behind the diorama.


var terrain: Terrain


func build(template: String, t: Terrain) -> void:
	terrain = t
	for c in get_children():
		c.free()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(template) & 0xFFFF
	match template:
		"village":
			for i in 14:
				var a := TAU * i / 14.0 + rng.randf_range(-0.12, 0.12)
				var r := rng.randf_range(70.0, 140.0)
				var kind: String = ["karst_a", "karst_b", "karst_c"][rng.randi() % 3]
				var kp := Vector2(cos(a), sin(a)) * r
				_add(kind, Vector3(kp.x, Landscape.outer_height(kp.x, kp.y) - 3.0, kp.y), rng.randf() * TAU, rng.randf_range(1.4, 2.4))
		"town", "hamlet":
			for i in 6:
				var a2 := -2.4 + i * 0.32 + rng.randf_range(-0.05, 0.05)
				var r2 := rng.randf_range(75.0, 90.0)
				var cp := Vector2(cos(a2), sin(a2)) * r2
				_add("cliff", Vector3(cp.x, Landscape.outer_height(cp.x, cp.y) - 1.0, cp.y), -a2 + PI / 2, rng.randf_range(1.6, 2.2))
		_:
			pass


func _woods(rng: RandomNumberGenerator, count: int, kinds: Array) -> void:
	# big trees standing on the wild hills between the glade and the horizon
	var placed := 0
	var tries := 0
	while placed < count and tries < count * 6:
		tries += 1
		var p := Vector2(rng.randf_range(-Terrain.HALF + 1.5, Terrain.HALF - 1.5), rng.randf_range(-Terrain.HALF + 1.5, Terrain.HALF - 1.5))
		var edge := maxf(absf(p.x), absf(p.y))
		if edge < Terrain.PLAY_HALF + 3.5:
			continue
		var y := terrain.height_at(p.x, p.y) - 0.3
		_add(kinds[rng.randi() % kinds.size()], Vector3(p.x, y, p.y), rng.randf() * TAU, rng.randf_range(1.3, 2.1))
		placed += 1


func _add(kind: String, pos: Vector3, rot: float, s: float) -> void:
	if not ModelLib.has_model(kind):
		return
	var m := ModelLib.merged(kind)
	for part in ["solid", "leaves"]:
		if m[part] == null:
			continue
		var mi := MeshInstance3D.new()
		mi.mesh = m[part]
		mi.material_override = ModelLib.leaf_material if part == "leaves" else ModelLib.props_material
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.transform = Transform3D(Basis(Vector3.UP, rot).scaled(Vector3.ONE * s), pos)
		add_child(mi)
