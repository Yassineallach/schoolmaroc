class_name Wildlife
extends Creature
## Deer, a fox, a donkey and an alpaca from Quaternius' Ultimate Animated
## Animals (CC0): rigged models with their own walk / idle / eating clips.
## They wander like the sheep, graze for a while, then look about.

## kind -> [model scale, walk speed, pet radius, walk clip playback speed]
const SPECIES := {
	"q_deer": [0.25, 0.7, 0.55, 1.0],
	"q_fox": [0.15, 0.9, 0.3, 1.2],
	"q_donkey": [0.25, 0.45, 0.55, 0.9],
	"q_alpaca": [0.24, 0.5, 0.5, 0.9],
}

var roam_center := Vector2.ZERO
var roam_radius := 6.0
var _anim: AnimationPlayer
var _clips: Dictionary = {}
var _walk_speed_scale := 1.0
var _base_speed := 0.6


func setup(g: Glade, kind: String, seed_value: int) -> void:
	super.setup(g, kind, seed_value)
	var spec: Array = SPECIES.get(kind, [0.25, 0.6, 0.5, 1.0])
	model.scale = Vector3.ONE * spec[0]
	_base_speed = spec[1]
	speed = spec[1] * rng.randf_range(0.85, 1.15)
	pet_radius = spec[2]
	_walk_speed_scale = spec[3]
	_anim = model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	if _anim:
		for a in _anim.get_animation_list():
			var base := String(a).get_slice("|", String(a).get_slice_count("|") - 1)
			_clips[base] = a
			var anim := _anim.get_animation(a)
			if base != "Death":
				anim.loop_mode = Animation.LOOP_LINEAR


func _ready() -> void:
	state = "graze"
	state_time = rng.randf_range(2.0, 6.0)
	_play("Eating")


func _play(clip: String, speed_scale := 1.0) -> void:
	if _anim == null or not _clips.has(clip):
		return
	var name: StringName = _clips[clip]
	if _anim.current_animation != name:
		_anim.play(name, 0.3)
	_anim.speed_scale = speed_scale


func _process(delta: float) -> void:
	state_time -= delta
	match state:
		"graze", "idle":
			if state_time <= 0.0:
				if _choose_target():
					state = "walk"
					state_time = 14.0
					_play("Walk", _walk_speed_scale * speed / _base_speed)
				else:
					state_time = rng.randf_range(1.0, 3.0)
		"walk":
			if move_towards(target, delta) or state_time <= 0.0:
				if rng.randf() < 0.6:
					state = "graze"
					_play("Eating")
				else:
					state = "idle"
					_play("Idle" if rng.randf() < 0.6 else "Idle_2")
				state_time = rng.randf_range(4.0, 10.0)


func _choose_target() -> bool:
	for i in 12:
		var a := rng.randf() * TAU
		var p := roam_center + Vector2(cos(a), sin(a)) * rng.randf_range(0.0, roam_radius)
		if glade.is_blocked(p) or glade.crosses_obstacle(ground_pos(), p):
			continue
		target = p
		return true
	return pick_land_target(4.0)
