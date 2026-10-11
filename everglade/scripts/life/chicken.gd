class_name Chicken
extends Creature
## Bustles about near cottages, pecking at the ground.

var home := Vector2.ZERO


func _ready() -> void:
	speed = rng.randf_range(0.8, 1.1)
	sound = "cluck"
	state = "peck"
	state_time = rng.randf_range(0.5, 2.0)
	pet_radius = 0.4


func _process(delta: float) -> void:
	state_time -= delta
	var moving := false
	match state:
		"peck":
			if _head:
				_head.rotation.x = 0.9 if fmod(Time.get_ticks_msec() * 0.004 + rng.seed, 1.0) < 0.3 else 0.1
			if state_time <= 0.0:
				var a := rng.randf() * TAU
				var p := home + Vector2(cos(a), sin(a)) * rng.randf_range(1.5, 4.5)
				if not glade.is_blocked(p) and not glade.crosses_obstacle(ground_pos(), p):
					target = p
					state = "walk"
					state_time = 6.0
				else:
					state_time = 1.0
		"walk":
			moving = true
			if _head:
				_head.rotation.x = 0.0
			if move_towards(target, delta) or state_time <= 0.0:
				state = "peck"
				state_time = rng.randf_range(1.5, 4.0)
				if rng.randf() < 0.2:
					Sfx.play_at("cluck", global_position, -8.0, 2)
	animate_legs(moving, delta)
	if moving:
		model.position.y = absf(sin(walk_phase)) * 0.04
