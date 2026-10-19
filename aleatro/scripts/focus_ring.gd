class_name FocusRing
extends Control

## Pulsing pixel outline drawn around whatever the gamepad/keyboard focus is on.

var target: Control = null
var _box := PixelBox.new(Color(0, 0, 0, 0), 4.0)


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_box.outline = 4.0
	visible = false


func _process(_delta: float) -> void:
	if not visible or target == null or not is_instance_valid(target):
		return
	var r := target.get_global_rect().grow(7)
	global_position = r.position
	size = r.size
	queue_redraw()


func _draw() -> void:
	var pulse := 0.6 + 0.4 * sin(Anim.now() * 6.0)
	_box.outline_color = Color(1, 1, 1, pulse)
	draw_style_box(_box, Rect2(Vector2.ZERO, size))
	# small pointer above the target, like a cursor
	var c := Vector2(size.x / 2, -6 - 3 * pulse)
	draw_colored_polygon(PackedVector2Array([c + Vector2(-9, -10), c + Vector2(9, -10), c]), Color(1, 1, 1, 0.9))
