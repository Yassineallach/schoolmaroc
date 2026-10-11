class_name Butterfly
extends Creature
## Flutters between flowers on warm days.

var wings: Array[Node3D] = []
var t := 0.0
var home := Vector3.ZERO


func _ready() -> void:
	for n in ["WingL", "WingR"]:
		var w := model.find_child(n, true, false) as Node3D
		if w:
			wings.append(w)
	scale = Vector3.ONE * 1.8
	t = rng.randf() * 10.0
	pet_radius = 0.3


func _process(delta: float) -> void:
	t += delta
	for i in wings.size():
		wings[i].rotation.z = sin(t * 22.0) * 1.1 * (1.0 if i == 0 else -1.0)
	state_time -= delta
	if state_time <= 0.0:
		state_time = rng.randf_range(2.0, 5.0)
		target = Vector2(home.x, home.z) + Vector2(rng.randf_range(-3, 3), rng.randf_range(-3, 3))
	var pos := ground_pos()
	var to := target - pos
	if to.length() > 0.1:
		var nxt := pos + to.normalized() * minf(to.length(), delta * 0.9)
		face_towards(to, delta, 5.0)
		var y := glade.terrain.height_at_v(nxt) + 0.6 + sin(t * 3.0) * 0.25
		global_position = Vector3(nxt.x, maxf(y, Terrain.WATER_LEVEL + 0.6), nxt.y)


func pet() -> void:
	state_time = 0.0
