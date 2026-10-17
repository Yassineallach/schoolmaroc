class_name Duck
extends Creature
## Paddles around ponds; ducklings follow their parent in a little line.

var leader: Node3D
var bob := 0.0
var _alarm_t := 1.0
var _flying := false


func _ready() -> void:
	speed = rng.randf_range(0.35, 0.5)
	sound = "quack"
	state = "idle"
	state_time = rng.randf_range(0.5, 3.0)
	pet_radius = 0.45


func ground_y(_p: Vector2) -> float:
	return Terrain.WATER_LEVEL - 0.04


func _process(delta: float) -> void:
	bob += delta
	if _flying:
		return
	model.position.y = sin(bob * 2.2 + rng.seed) * 0.02
	# a path laid right by them, or their water filled in: fly off
	_alarm_t -= delta
	if _alarm_t <= 0.0 and leader == null:
		_alarm_t = 1.0
		var gp := ground_pos()
		if glade._on_path(gp, 0.6) or glade.terrain.height_at_v(gp) > Terrain.WATER_LEVEL - 0.05:
			_fly_away()
			return
	model.rotation.z = sin(bob * 1.7) * 0.05
	if leader and is_instance_valid(leader):
		var lp := Vector2(leader.global_position.x, leader.global_position.z)
		var my := ground_pos()
		if my.distance_to(lp) > 0.55:
			var behind := lp + (my - lp).normalized() * 0.5
			speed = 0.7
			move_towards(behind, delta)
		return
	state_time -= delta
	match state:
		"idle":
			if _head:
				_head.rotation.x = lerpf(_head.rotation.x, 0.0, delta * 3.0)
			if state_time <= 0.0:
				var p = glade.random_water_point(rng)
				if p != null and _water_route(ground_pos(), p):
					target = p
					state = "swim"
					state_time = 20.0
				else:
					state_time = 2.0
		"swim":
			if move_towards(target, delta) or state_time <= 0.0:
				state = "dip" if rng.randf() < 0.4 else "idle"
				state_time = rng.randf_range(1.5, 4.0)
				if rng.randf() < 0.3:
					Sfx.play_at("quack", global_position, -6.0, 2)
		"dip":
			if _head:
				_head.rotation.x = lerpf(_head.rotation.x, 1.6, delta * 4.0)
			if state_time <= 0.0:
				state = "idle"
				state_time = rng.randf_range(2.0, 5.0)


func _fly_away() -> void:
	var dest = null
	for i in 12:
		var p = glade.random_water_point(rng)
		if p != null and not glade._on_path(p, 2.0) and (p as Vector2).distance_to(ground_pos()) > 3.0:
			dest = p
			break
	if dest == null:
		return
	_flying = true
	Sfx.play_at("quack", global_position, -2.0, 2)
	var d: Vector2 = dest
	face_towards(d - ground_pos(), 1.0, 100.0)
	var tw := create_tween()
	tw.tween_property(self, "global_position:y", global_position.y + 2.5, 0.6).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.parallel().tween_property(model, "rotation:x", -0.4, 0.3)
	tw.tween_property(self, "global_position", Vector3(d.x, Terrain.WATER_LEVEL + 2.0, d.y), d.distance_to(ground_pos()) / 4.0 + 0.5)
	tw.tween_property(self, "global_position:y", Terrain.WATER_LEVEL - 0.04, 0.7).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.parallel().tween_property(model, "rotation:x", 0.0, 0.5)
	tw.tween_callback(func():
		_flying = false
		state = "idle"
		state_time = 2.0
		Sfx.play_at("splash", global_position, -8.0))
	# ducklings scurry after their parent
	for d2 in get_parent().get_children():
		if d2 is Duck and d2.leader == self:
			var tw2 := (d2 as Duck).create_tween()
			tw2.tween_property(d2, "global_position", Vector3(d.x - 0.5, Terrain.WATER_LEVEL - 0.04, d.y), 2.5)


func _water_route(a: Vector2, b: Vector2) -> bool:
	for i in 9:
		var p := a.lerp(b, i / 8.0)
		if glade.terrain.height_at_v(p) > Terrain.WATER_LEVEL - 0.15:
			return false
	return true
