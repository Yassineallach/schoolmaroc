class_name SpellView
extends Control

## A spell tile: a small rune-inscribed card held in the spell slots.

signal tapped(view)

const W := 96.0
const H := 128.0

var spell_id := ""
var float_amount := 1.0
var _phase := randf() * TAU
var _touch := TouchTracker.new()


func _init(id: String = "") -> void:
	spell_id = id
	size = Vector2(W, H)
	custom_minimum_size = size
	pivot_offset = size / 2
	mouse_filter = Control.MOUSE_FILTER_STOP


func _gui_input(event: InputEvent) -> void:
	if _touch.handle(event) == "tap":
		tapped.emit(self)
	if event is InputEventMouseButton:
		accept_event()


func _process(delta: float) -> void:
	if _touch.tick(delta):
		tapped.emit(self)
	if is_visible_in_tree():
		queue_redraw()


func _draw() -> void:
	var d := Data.spell_def(spell_id)
	var col := Data.SPELL_COLOR
	var font := ThemeDB.fallback_font
	draw_set_transform_matrix(Anim.float_xform(size, _phase, float_amount))
	var sb := PixelBox.new(col, 4.0, 0.0, true)
	sb.shadow_offset = Vector2(3, 5) + Vector2(1, 3) * Anim.lift(_phase, float_amount)
	sb.outline = 4.0
	sb.outline_color = Color("9fe3cf")
	draw_style_box(sb, Rect2(Vector2.ZERO, size))
	# a rotating rune circle
	var c := Vector2(size.x / 2, 46)
	var spin := Anim.now() * 0.8 + _phase
	draw_arc(c, 28, 0, TAU, 28, Color(1, 1, 1, 0.75), 3.0)
	var pts := PackedVector2Array()
	for i in 4:
		var a := spin + TAU * i / 4.0
		pts.append(c + Vector2(cos(a), sin(a)) * 24)
	pts.append(pts[0])
	draw_polyline(pts, Color("d7fff3"), 2.5)
	if d.has("suit"):
		CardView.draw_suit(self, d.suit, c, 26.0, Data.SUIT_COLORS[d.suit].lightened(0.3))
	else:
		draw_string(font, c + Vector2(-20, 11), d.name.substr(0, 1), HORIZONTAL_ALIGNMENT_CENTER, 40, 30, Color.WHITE)
	draw_multiline_string(font, Vector2(4, 98), d.name, HORIZONTAL_ALIGNMENT_CENTER, size.x - 8, 18, 2, Color.WHITE)
