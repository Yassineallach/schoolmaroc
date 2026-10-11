class_name Koi
extends Creature
## Koi gliding under the pond surface, tails swishing.

var _tail: Node3D
var t := 0.0


func _ready() -> void:
	speed = rng.randf_range(0.35, 0.6)
	sound = ""
	pet_radius = 0.35
	scale = Vector3.ONE * rng.randf_range(1.6, 2.2)
	_tail = model.find_child("Tail", true, false) as Node3D
	t = rng.randf() * 10.0


func ground_y(_p: Vector2) -> float:
	return Terrain.WATER_LEVEL - 0.14


func _process(delta: float) -> void:
	t += delta
	if _tail:
		_tail.rotation.y = sin(t * 7.0) * 0.5
	model.rotation.y = sin(t * 3.5) * 0.08
	state_time -= delta
	if state_time <= 0.0 or move_towards(target, delta):
		state_time = rng.randf_range(4.0, 9.0)
		for i in 8:
			var a := rng.randf() * TAU
			var p := ground_pos() + Vector2(cos(a), sin(a)) * rng.randf_range(1.0, 3.5)
			if glade.terrain.height_at_v(p) < Terrain.WATER_LEVEL - 0.3:
				target = p
				break


func pet() -> void:
	Sfx.play_at("splash", global_position, -10.0)
	speed = 1.4
	state_time = 1.2
	var a := rng.randf() * TAU
	target = ground_pos() + Vector2(cos(a), sin(a)) * 2.0
	if glade.terrain.height_at_v(target) > Terrain.WATER_LEVEL - 0.3:
		target = ground_pos()
	get_tree().create_timer(1.5).timeout.connect(func(): speed = 0.45)
