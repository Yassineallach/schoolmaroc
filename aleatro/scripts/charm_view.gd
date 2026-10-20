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
var face_up := true
var smothered := false
var locked := false
var float_amount := 1.0
var _phase := randf() * TAU
var _touch := TouchTracker.new()
var _tilt := Tilt.new()


func _init(id: String = "", rune: String = "", ed: String = "") -> void:
	charm_id = id
	rune_hand = rune
	edition = ed
	size = Vector2(W, H)
	custom_minimum_size = size
	pivot_offset = size / 2
	mouse_filter = Control.MOUSE_FILTER_STOP
	_tilt.attach(self)
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
	_tilt.update(self, delta, _touch.pressing or _touch.dragging, _ensure_material)
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
	var t := Prof.begin()
	_paint()
	Prof.end("charm draw", t)


func _paint() -> void:
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
	if not face_up:
		_draw_back()
		return
	var sb := PixelBox.new(col, 4.0, 0.0, true)
	sb.shadow_offset = Vector2(3, 5) + Vector2(1, 3) * Anim.lift(_phase, float_amount) + Anim.parallax(self)
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
	if locked:
		# a small padlock: this charm cannot be sold
		var at := Vector2(size.x - 22, 10)
		draw_arc(at + Vector2(7, 7), 5, PI, TAU, 10, Color("f2d675"), 2.5)
		draw_rect(Rect2(at + Vector2(0, 7), Vector2(14, 10)), Color("f2d675"))
	if smothered:
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.1, 0.05, 0.05, 0.6))
		draw_string(font, Vector2(0, size.y / 2 + 8), "DISABLED", HORIZONTAL_ALIGNMENT_CENTER, size.x, 18, Color("ff8a5c"))


func _draw_back() -> void:
	var back := PixelBox.new(Color("3b2f4f"), 4.0, 0.0, true)
	back.outline = 4.0
	back.outline_color = Color("c9a227")
	draw_style_box(back, Rect2(Vector2.ZERO, size))
	var c := size / 2
	for r in [34.0, 22.0, 10.0]:
		draw_arc(c, r, 0, TAU, 24, Color("c9a227", 0.6), 3.0)
	draw_string(ThemeDB.fallback_font, c + Vector2(-20, 12), "?", HORIZONTAL_ALIGNMENT_CENTER, 40, 34, Color("f2d675"))


## Turn over to reveal the face.
func flip_up(delay: float = 0.0) -> void:
	if face_up:
		return
	var tw := create_tween()
	tw.tween_interval(delay)
	tw.tween_property(self, "scale:x", 0.0, 0.09)
	tw.tween_callback(func():
		face_up = true
		queue_redraw())
	tw.tween_property(self, "scale:x", 1.0, 0.09)
