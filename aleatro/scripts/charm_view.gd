class_name CharmView
extends Control

## Draws a charm (or a rune when `rune_hand` is set) as a small tile.

signal tapped(view)
signal held(view)
signal drag_started(view, pos)
signal dragged(view, pos)
signal drag_ended(view)

const W := 120.0
const H := 150.0

var charm_id := ""
var rune_hand := ""
var edition := ""
var float_amount := 1.0
var _phase := randf() * TAU
var _touch := TouchTracker.new()


func _init(id: String = "", rune: String = "", ed: String = "") -> void:
	charm_id = id
	rune_hand = rune
	edition = ed
	size = Vector2(W, H)
	custom_minimum_size = size
	pivot_offset = size / 2
	mouse_filter = Control.MOUSE_FILTER_STOP
	if edition != "":
		_ensure_material().set_shader_parameter("edition", Data.EDITIONS[edition].shader)


func _ensure_material() -> ShaderMaterial:
	if material == null:
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/card_fx.gdshader")
		m.set_shader_parameter("size", size)
		m.set_shader_parameter("phase", _phase)
		material = m
	return material


func _gui_input(event: InputEvent) -> void:
	match _touch.handle(event):
		"tap":
			tapped.emit(self)
		"drag_start":
			drag_started.emit(self, event.global_position)
		"drag":
			dragged.emit(self, event.global_position)
		"drag_end":
			drag_ended.emit(self)
	if event is InputEventMouseButton or _touch.dragging:
		accept_event()


func _process(delta: float) -> void:
	if _touch.tick(delta):
		held.emit(self)
	if float_amount > 0.0 and is_visible_in_tree():
		queue_redraw()


## Burn away, then free.
func dissolve(time: float = 0.6) -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var m := _ensure_material()
	var tw := create_tween()
	tw.tween_method(func(v): m.set_shader_parameter("dissolve", v), 0.0, 1.0, time)
	tw.tween_callback(queue_free)


func title() -> String:
	return "Rune: " + rune_hand if rune_hand != "" else Data.charm_def(charm_id).name


func _draw() -> void:
	var font := ThemeDB.fallback_font
	var col: Color
	var name: String
	if rune_hand != "":
		col = Data.RUNE_COLOR
		name = rune_hand
	else:
		var d := Data.charm_def(charm_id)
		col = Data.RARITY_COLORS[d.rarity]
		name = d.name
	draw_set_transform_matrix(Anim.float_xform(size, _phase, float_amount))
	var sb := PixelBox.new(col, 4.0, 0.0, true)
	sb.shadow_offset = Vector2(3, 5) + Vector2(1, 3) * Anim.lift(_phase, float_amount)
	sb.outline = 4.0
	sb.outline_color = col.lightened(0.35)
	draw_style_box(sb, Rect2(Vector2.ZERO, size))
	# emblem
	var center := Vector2(size.x / 2, 52)
	if rune_hand != "":
		var pts := PackedVector2Array()
		for i in 6:
			var a := TAU * i / 6.0 - PI / 2
			pts.append(center + Vector2(cos(a), sin(a)) * 34)
		draw_colored_polygon(pts, col.darkened(0.35))
		draw_polyline(pts + PackedVector2Array([pts[0]]), Color(1, 1, 1, 0.8), 3)
		draw_string(font, center + Vector2(-34, 11), "+1", HORIZONTAL_ALIGNMENT_CENTER, 68, 30, Color.WHITE)
	else:
		draw_circle(center, 34, col.darkened(0.35))
		draw_arc(center, 34, 0, TAU, 32, Color(1, 1, 1, 0.8), 3)
		draw_string(font, center + Vector2(-34, 13), name.substr(0, 1), HORIZONTAL_ALIGNMENT_CENTER, 68, 38, Color.WHITE)
	if edition != "":
		var tag: String = Data.EDITIONS[edition].name.to_upper()
		var b := PixelBox.new(Color(0, 0, 0, 0.45), 2.0)
		draw_style_box(b, Rect2(30, 6, 60, 16))
		draw_string(font, Vector2(30, 18.5), tag, HORIZONTAL_ALIGNMENT_CENTER, 60, 11, Color.WHITE)
	draw_multiline_string(font, Vector2(6, 112), name, HORIZONTAL_ALIGNMENT_CENTER, size.x - 12, 19, 2, Color.WHITE)
