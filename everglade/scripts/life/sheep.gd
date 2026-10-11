class_name Sheep
extends Creature
## Wanders the meadow, grazes, follows the flock and loves a pat.

var flock: Array = []


func _ready() -> void:
	speed = rng.randf_range(0.45, 0.65)
	sound = "baa"
	state = "graze"
	state_time = rng.randf_range(1.0, 5.0)


func _process(delta: float) -> void:
	state_time -= delta
	happy = maxf(0.0, happy - delta * 0.5)
	var moving := false
	match state:
		"graze":
			if _head:
				_head.rotation.x = lerpf(_head.rotation.x, 0.75 + sin(Time.get_ticks_msec() * 0.006) * 0.08, minf(1.0, delta * 3.0))
			if state_time <= 0.0:
				if _choose_target():
					state = "walk"
					state_time = 12.0
				else:
					state_time = rng.randf_range(1.0, 3.0)
		"walk":
			if _head:
				_head.rotation.x = lerpf(_head.rotation.x, 0.0, minf(1.0, delta * 3.0))
			moving = true
			if move_towards(target, delta) or state_time <= 0.0:
				state = "graze" if rng.randf() < 0.75 else "look"
				state_time = rng.randf_range(3.0, 9.0)
		"look":
			if _head:
				_head.rotation.y = sin(Time.get_ticks_msec() * 0.0015 + rng.seed) * 0.6
				_head.rotation.x = lerpf(_head.rotation.x, -0.15, minf(1.0, delta * 3.0))
			if state_time <= 0.0:
				if _head:
					_head.rotation.y = 0.0
				state = "graze"
				state_time = rng.randf_range(2.0, 6.0)
				if rng.randf() < 0.15:
					Sfx.play_at("baa", global_position + Vector3.UP, -8.0, 2)
	animate_legs(moving, delta)
	# gentle breathing / body bob
	model.scale = Vector3.ONE * (1.0 + sin(Time.get_ticks_msec() * 0.003 + rng.seed) * 0.012)


func _choose_target() -> bool:
	# drift towards flock-mates so sheep stay loosely together
	if not flock.is_empty() and rng.randf() < 0.5:
		var center := Vector2.ZERO
		for s in flock:
			var gp := (s as Node3D).global_position
			center += Vector2(gp.x, gp.z)
		center /= flock.size()
		var p := center + Vector2(rng.randf_range(-2.5, 2.5), rng.randf_range(-2.5, 2.5))
		if not glade.is_blocked(p) and not glade.crosses_obstacle(ground_pos(), p):
			target = p
			return true
	return pick_land_target(5.0)
