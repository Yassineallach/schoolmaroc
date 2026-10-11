class_name Slime
extends Creature
## Bouncy jelly slime: hops around the meadow with squash & stretch and does a
## happy double jump when tapped.

var _body: Node3D
var _hop := 0.0
var _hop_from := Vector2.ZERO
var _hop_to := Vector2.ZERO
var _hop_len := 0.6


func _ready() -> void:
	sound = "boing"
	pet_radius = 0.55
	state = "rest"
	state_time = rng.randf_range(0.5, 2.5)
	_body = model.find_child("Body", true, false) as Node3D


func _process(delta: float) -> void:
	var t := Time.get_ticks_msec() * 0.001 + rng.seed
	match state:
		"rest":
			# idle wobble
			var w := sin(t * 5.0) * 0.04
			_squash(1.0 - w, 1.0 + w * 0.5)
			model.position.y = 0.0
			state_time -= delta
			if state_time <= 0.0:
				var a := rng.randf() * TAU
				var p := ground_pos() + Vector2(cos(a), sin(a)) * rng.randf_range(0.6, 1.4)
				if not glade.is_blocked(p) and not glade.crosses_obstacle(ground_pos(), p):
					_hop_from = ground_pos()
					_hop_to = p
					_hop = 0.0
					_hop_len = rng.randf_range(0.45, 0.65)
					state = "hop"
				else:
					state_time = 0.6
		"hop":
			_hop += delta / _hop_len
			var k := clampf(_hop, 0.0, 1.0)
			var p2 := _hop_from.lerp(_hop_to, k)
			face_towards(_hop_to - _hop_from, delta, 10.0)
			global_position = Vector3(p2.x, ground_y(p2), p2.y)
			model.position.y = sin(k * PI) * 0.45
			var stretch := 1.0 + sin(k * PI) * 0.18
			_squash(1.0 / sqrt(stretch), stretch)
			if _hop >= 1.0:
				_squash(1.25, 0.7)
				state = "rest" if rng.randf() < 0.4 else "land"
				state_time = rng.randf_range(0.8, 2.6)
		"land":
			# quick recovery bounce, then hop again
			var s := move_toward(_body.scale.y if _body else 1.0, 1.0, delta * 3.0)
			_squash(1.0 / sqrt(maxf(s, 0.1)), s)
			state_time -= delta
			if state_time <= 0.0 or absf(s - 1.0) < 0.01:
				state = "rest"
				state_time = 0.05


func _squash(xz: float, y: float) -> void:
	if _body:
		_body.scale = Vector3(xz, y, xz)


func pet() -> void:
	super.pet()
	state = "rest"
	state_time = 1.2
