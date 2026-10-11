class_name Cat
extends Creature
## Village cat: strolls between cottages, sits to wash, naps in the sun.

var home := Vector2.ZERO
var _tail: Node3D


func _ready() -> void:
	speed = rng.randf_range(0.7, 0.95)
	sound = "meow"
	state = "sit"
	state_time = rng.randf_range(1.0, 4.0)
	pet_radius = 0.4
	_tail = model.find_child("Tail", true, false) as Node3D


func _process(delta: float) -> void:
	state_time -= delta
	var moving := false
	var t := Time.get_ticks_msec() * 0.001 + rng.seed
	match state:
		"sit", "nap":
			model.rotation.x = lerpf(model.rotation.x, -0.25 if state == "sit" else 0.0, minf(1.0, delta * 4.0))
			model.scale.y = lerpf(model.scale.y, 0.82 if state == "nap" else 1.0, minf(1.0, delta * 3.0))
			if _head:
				_head.rotation.y = sin(t * 0.7) * 0.4 if state == "sit" else 0.0
				_head.rotation.x = 0.0 if state == "sit" else 0.5
			if state_time <= 0.0:
				var a := rng.randf() * TAU
				var p := home + Vector2(cos(a), sin(a)) * rng.randf_range(1.5, 6.0)
				if not glade.is_blocked(p) and not glade.crosses_obstacle(ground_pos(), p):
					target = p
					state = "walk"
					state_time = 10.0
				else:
					state_time = 1.5
		"walk":
			moving = true
			model.rotation.x = lerpf(model.rotation.x, 0.0, minf(1.0, delta * 6.0))
			model.scale.y = 1.0
			if move_towards(target, delta) or state_time <= 0.0:
				state = "nap" if rng.randf() < 0.35 else "sit"
				state_time = rng.randf_range(4.0, 12.0)
	if _tail:
		_tail.rotation.z = sin(t * (6.0 if moving else 2.0)) * 0.5
	animate_legs(moving, delta)


func pet() -> void:
	super.pet()
	state = "sit"
	state_time = 3.0
