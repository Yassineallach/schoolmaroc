class_name DebugBoxes
extends Control

## Developer overlay: outlines every control that can take input, in its
## real (rotated, scaled) shape, coloured by state, plus a corner readout.
## F3 toggles it; on a phone, tap the credits line five times.
##
##   red    takes input          green  under the pointer
##   gold   gamepad focus        blue   gliding to a new spot
##   grey   inside a container that ignores input (dimmed)

const C_INPUT := Color(1, 0.25, 0.25, 0.55)
const C_HOVER := Color(0.3, 1, 0.4, 0.95)
const C_FOCUS := Color(1, 0.8, 0.2, 0.95)
const C_MOVING := Color(0.35, 0.6, 1, 0.95)

var main: Control
var _fps := 0.0
var _visited := 0


func _init(m: Control) -> void:
	main = m
	name = "DebugBoxes"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	top_level = true
	z_index = 4000
	z_as_relative = false
	visible = false


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F3:
		toggle()


func toggle() -> void:
	visible = not visible
	set_process(visible)


func _ready() -> void:
	set_process(visible)


func _process(delta: float) -> void:
	size = get_viewport_rect().size
	_fps = lerpf(_fps, 1.0 / maxf(delta, 0.0001), 0.1) if _fps > 0.0 else 1.0 / maxf(delta, 0.0001)
	queue_redraw()


func _draw() -> void:
	var hovered := get_viewport().gui_get_hovered_control()
	var focused: Control = main.pad.focused if main.pad != null else null
	var moving := 0
	var motes := 0
	_visited = 0
	var stack: Array = [main]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n == self:
			continue
		if n is CanvasItem and not n.visible:
			continue
		_visited += 1
		if n is Motes:
			motes += n.count()
		if n is Glide and n.is_moving():
			moving += 1
		if n is Control:
			var c: Control = n
			var col := Color.TRANSPARENT
			if c == focused:
				col = C_FOCUS
			elif c == hovered:
				col = C_HOVER
			elif Glide.on(c) != null and Glide.on(c).is_moving():
				col = C_MOVING
			elif c.mouse_filter == Control.MOUSE_FILTER_STOP and c.size.x > 0.0:
				col = C_INPUT
			if col.a > 0.0:
				_outline(c, col, 2.0 if col == C_INPUT else 3.0)
				if c == hovered:
					_tag(c)
		for ch in n.get_children():
			stack.push_back(ch)
	var lines := [
		"%d fps" % roundi(_fps),
		"%d nodes visible" % _visited,
		"%d gliding" % moving,
		"%d motes" % motes,
		"layer: %s" % (main.pad.current_layer() if main.pad != null else "?"),
	]
	var font := ThemeDB.fallback_font
	var at := Vector2(size.x - 250, 14)
	draw_rect(Rect2(at - Vector2(8, 4), Vector2(240, 22 * lines.size() + 8)), Color(0, 0, 0, 0.7))
	for i in lines.size():
		draw_string(font, at + Vector2(0, 18 + 22 * i), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)


## Draw `c`'s rectangle through its full transform, so rotation shows.
func _outline(c: Control, col: Color, width: float) -> void:
	var xf := get_global_transform().affine_inverse() * c.get_global_transform()
	var s := c.size
	var pts := PackedVector2Array([xf * Vector2.ZERO, xf * Vector2(s.x, 0), xf * s, xf * Vector2(0, s.y), xf * Vector2.ZERO])
	draw_polyline(pts, col, width)


## Name, type and size of the control under the pointer.
func _tag(c: Control) -> void:
	var font := ThemeDB.fallback_font
	var kind := c.get_class()
	if c.get_script() != null and String(c.get_script().get_global_name()) != "":
		kind = String(c.get_script().get_global_name())
	var text := "%s (%s) %dx%d" % [c.name, kind, c.size.x, c.size.y]
	var at := (get_global_transform().affine_inverse() * c.get_global_transform()) * Vector2(0, -6)
	at.x = clampf(at.x, 4, size.x - 300)
	at.y = maxf(at.y, 18)
	draw_rect(Rect2(at - Vector2(2, 16), Vector2(font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 15).x + 6, 20)), Color(0, 0, 0, 0.75))
	draw_string(font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, C_HOVER)
