class_name Tilt
extends RefCounted

## Pointer tilt for a card-like Control drawn with card_fx.gdshader: while
## the pointer hovers it (mouse) or presses it (touch), the face leans away
## from the pointer. Eases in and out; off under reduced motion.

const EASE := 12.0

var dir := Vector2.ZERO
var amt := 0.0
var hovered := false


## Hook hover tracking up to `c`.
func attach(c: Control) -> void:
	c.mouse_entered.connect(func(): hovered = true)
	c.mouse_exited.connect(func(): hovered = false)


## Advance one frame. `pressed` is whether a touch or click holds `c`.
## Returns true while the shader needs new values.
func update(c: Control, delta: float, pressed: bool, mat_for: Callable) -> bool:
	var active := not Anim.calm and c.is_visible_in_tree() and c.mouse_filter != Control.MOUSE_FILTER_IGNORE \
		and (pressed or (hovered and not DisplayServer.is_touchscreen_available()))
	if not active and amt == 0.0:
		return false
	var goal := 1.0 if active else 0.0
	var k := 1.0 - exp(-EASE * delta)
	if active:
		var half := c.size / 2.0
		var p := (c.get_local_mouse_position() - half) / half
		dir = dir.lerp(p.clamp(Vector2(-1, -1), Vector2(1, 1)), k)
	amt = lerpf(amt, goal, k)
	if not active and amt < 0.01:
		amt = 0.0
	var m: ShaderMaterial = mat_for.call()
	m.set_shader_parameter("tilt", dir)
	m.set_shader_parameter("tilt_amt", amt)
	return true
