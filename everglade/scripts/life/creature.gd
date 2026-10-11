class_name Creature
extends Node3D
## Base for the glade's animals: wandering, simple procedural animation and
## petting (tap them for a heart and a happy sound).

var glade: Glade
var model: Node3D
var rng := RandomNumberGenerator.new()
var target := Vector2.ZERO
var speed := 0.6
var state := "idle"
var state_time := 0.0
var walk_phase := 0.0
var pet_radius := 0.6
var happy := 0.0
var sound := ""
var _legs: Array[Node3D] = []
var _head: Node3D
var _heading := 0.0


func setup(g: Glade, kind: String, seed_value: int) -> void:
	glade = g
	rng.seed = seed_value
	model = ModelLib.instance(kind)
	add_child(model)
	for leg_name in ["LegFL", "LegFR", "LegBL", "LegBR"]:
		var leg := model.find_child(leg_name, true, false) as Node3D
		if leg:
			_legs.append(leg)
	_head = model.find_child("Head", true, false) as Node3D
	_heading = rng.randf() * TAU


func ground_pos() -> Vector2:
	return Vector2(global_position.x, global_position.z)


func face_towards(dir: Vector2, delta: float, turn_speed := 4.0) -> void:
	if dir.length_squared() < 1e-6:
		return
	# model front is +Z
	var want := atan2(dir.x, dir.y)
	_heading = lerp_angle(_heading, want, minf(1.0, delta * turn_speed))
	rotation.y = _heading


func move_towards(dest: Vector2, delta: float) -> bool:
	var pos := ground_pos()
	var to := dest - pos
	var d := to.length()
	if d < 0.15:
		return true
	var step := minf(d, speed * delta)
	var nxt := pos + to / d * step
	face_towards(to, delta)
	global_position = Vector3(nxt.x, ground_y(nxt), nxt.y)
	walk_phase += delta * speed * 9.0
	return false


func ground_y(p: Vector2) -> float:
	return glade.terrain.height_at_v(p)


func animate_legs(moving: bool, delta: float) -> void:
	for i in _legs.size():
		var leg := _legs[i]
		var target_angle := sin(walk_phase + (PI if i % 3 == 0 else 0.0)) * 0.5 if moving else 0.0
		leg.rotation.x = lerpf(leg.rotation.x, target_angle, minf(1.0, delta * 12.0))


## Picks a reachable meadow point not blocked by water, walls or buildings.
func pick_land_target(radius: float) -> bool:
	var pos := ground_pos()
	for i in 12:
		var a := rng.randf() * TAU
		var p := pos + Vector2(cos(a), sin(a)) * rng.randf_range(1.0, radius)
		if glade.is_blocked(p):
			continue
		if glade.crosses_obstacle(pos, p):
			continue
		target = p
		return true
	return false


func pet() -> void:
	happy = 1.0
	_spawn_heart()
	if sound != "":
		Sfx.play_at(sound, global_position + Vector3.UP, 0.0, 2)
	Sfx.play("heart", -6.0)
	Settings.vibrate(20)
	var tw := create_tween()
	tw.tween_property(model, "position:y", 0.35, 0.15).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(model, "position:y", 0.0, 0.2).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)


static var _heart_mesh: ArrayMesh


static func heart_mesh() -> ArrayMesh:
	if _heart_mesh:
		return _heart_mesh
	var poly := PackedVector2Array()
	for i in 40:
		var t := TAU * i / 40.0
		var x := 16.0 * pow(sin(t), 3)
		var y := 13.0 * cos(t) - 5.0 * cos(2.0 * t) - 2.0 * cos(3.0 * t) - cos(4.0 * t)
		poly.append(Vector2(x, y) / 34.0)
	var tris := Geometry2D.triangulate_polygon(poly)
	var mb := MeshBuilder.new()
	var col := Color(1.0, 0.45, 0.55)
	for i in range(0, tris.size(), 3):
		var a := Vector3(poly[tris[i]].x, poly[tris[i]].y, 0)
		var b := Vector3(poly[tris[i + 1]].x, poly[tris[i + 1]].y, 0)
		var c := Vector3(poly[tris[i + 2]].x, poly[tris[i + 2]].y, 0)
		mb.tri(a, b, c, col)
		mb.tri(a, c, b, col)
	_heart_mesh = mb.commit()
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	mat.no_depth_test = true
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_heart_mesh.surface_set_material(0, mat)
	return _heart_mesh


func _spawn_heart() -> void:
	var heart := MeshInstance3D.new()
	heart.mesh = heart_mesh()
	heart.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(heart)
	heart.position = Vector3(0, 1.3, 0)
	heart.scale = Vector3.ONE * 0.2
	var tw := heart.create_tween()
	tw.set_parallel(true)
	tw.tween_property(heart, "position:y", 2.3, 1.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tw.tween_property(heart, "scale", Vector3.ONE * 0.75, 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(heart, "scale", Vector3.ONE * 0.01, 0.4).set_delay(0.7)
	tw.chain().tween_callback(heart.queue_free)
