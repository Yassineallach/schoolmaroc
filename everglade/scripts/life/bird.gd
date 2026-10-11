class_name Bird
extends Creature
## Small songbirds circling the glade that land on walls, posts and roofs.

var wings: Array[Node3D] = []
var flap := 0.0
var perch := Vector3.ZERO
var orbit_center := Vector3.ZERO
var orbit_angle := 0.0
var orbit_radius := 10.0
var altitude := 9.0


func _ready() -> void:
	for n in ["WingL", "WingR"]:
		var w := model.find_child(n, true, false) as Node3D
		if w:
			wings.append(w)
	scale = Vector3.ONE * 1.6
	state = "fly"
	state_time = rng.randf_range(5.0, 14.0)
	orbit_angle = rng.randf() * TAU
	orbit_radius = rng.randf_range(6.0, 14.0)
	altitude = rng.randf_range(7.0, 12.0)
	sound = "chirp"
	pet_radius = 0.5


func _process(delta: float) -> void:
	state_time -= delta
	match state:
		"fly":
			orbit_angle += delta * 3.2 / orbit_radius
			var goal := orbit_center + Vector3(cos(orbit_angle) * orbit_radius, altitude + sin(orbit_angle * 2.0), sin(orbit_angle) * orbit_radius)
			_fly_to(goal, delta, 3.2)
			_flap(delta, 18.0)
			if state_time <= 0.0:
				var options := glade.perches()
				if options.is_empty():
					state_time = 8.0
				else:
					perch = options[rng.randi() % options.size()]
					state = "land"
					state_time = 15.0
		"land":
			_flap(delta, 14.0)
			if _fly_to(perch, delta, 3.0) or state_time <= 0.0:
				global_position = perch
				state = "perched"
				state_time = rng.randf_range(6.0, 16.0)
		"perched":
			for w in wings:
				w.rotation.z = lerpf(w.rotation.z, 0.0, delta * 8.0)
			if _head:
				_head.rotation.y = sin(Time.get_ticks_msec() * 0.002 + rng.seed) * 0.5
			if rng.randf() < delta * 0.08:
				Sfx.play_at("chirp", global_position, -6.0, 2)
			if state_time <= 0.0:
				take_off()


func take_off() -> void:
	state = "fly"
	state_time = rng.randf_range(8.0, 20.0)
	orbit_angle = atan2(global_position.z - orbit_center.z, global_position.x - orbit_center.x)


func pet() -> void:
	Sfx.play_at("chirp", global_position, 0.0, 2)
	take_off()


func _fly_to(goal: Vector3, delta: float, spd: float) -> bool:
	var to := goal - global_position
	var d := to.length()
	if d < 0.1:
		return true
	var step := minf(d, spd * delta)
	global_position += to / d * step
	var flat := Vector2(to.x, to.z)
	if flat.length() > 0.01:
		face_towards(flat, delta, 6.0)
	return false


func _flap(delta: float, rate: float) -> void:
	flap += delta * rate
	for i in wings.size():
		var w := wings[i]
		w.rotation.z = sin(flap) * 0.9 * (1.0 if i == 0 else -1.0)
