class_name CardView
extends Control

signal tapped(view)

const W := 100.0
const H := 140.0

var card: Dictionary
var selected := false
var debuffed := false

static var _face_box: PixelBox
static var _select_box: PixelBox


func _init(c: Dictionary = {}) -> void:
	card = c
	size = Vector2(W, H)
	custom_minimum_size = size
	pivot_offset = size / 2
	mouse_filter = Control.MOUSE_FILTER_STOP
	if _face_box == null:
		_face_box = PixelBox.new(Color("f7f3ea"), 4.0, 0.0, true)
		_face_box.outline = 2.0
		_face_box.outline_color = Color("c9c2b0")
		_select_box = PixelBox.new(Color(0, 0, 0, 0), 4.0)
		_select_box.outline = 4.0
		_select_box.outline_color = Color("ffcc33")


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		tapped.emit(self)
		accept_event()


func set_debuffed(v: bool) -> void:
	debuffed = v
	queue_redraw()


func _draw() -> void:
	var font := ThemeDB.fallback_font
	# lifted cards cast a longer shadow
	_face_box.shadow_offset = Vector2(6, 12) if selected else Vector2(3, 6)
	draw_style_box(_face_box, Rect2(Vector2.ZERO, size))
	if selected:
		draw_style_box(_select_box, Rect2(Vector2.ZERO, size))
	var col: Color = Data.SUIT_COLORS[card.suit]
	var label: String = Data.RANK_LABELS[card.rank]
	draw_string(font, Vector2(8, 32), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 28, col)
	draw_suit(self, card.suit, Vector2(20, 48), 18.0, col)
	# bottom-right mirror
	draw_set_transform(size, PI, Vector2.ONE)
	draw_string(font, Vector2(8, 32), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 28, col)
	draw_suit(self, card.suit, Vector2(20, 48), 18.0, col)
	draw_set_transform(Vector2.ZERO, 0, Vector2.ONE)
	if card.rank >= 11 and card.rank <= 13:
		var inner := PixelBox.new(col.lightened(0.75), 2.0)
		inner.outline = 2.0
		inner.outline_color = col
		draw_style_box(inner, Rect2(30, 34, 40, 72))
		draw_string(font, Vector2(30, 82), label, HORIZONTAL_ALIGNMENT_CENTER, 40, 34, col)
	else:
		draw_suit(self, card.suit, size / 2 + Vector2(0, 2), 46.0, col)
	if debuffed:
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.1, 0.1, 0.1, 0.55))
		draw_line(Vector2(18, 18), size - Vector2(18, 18), Color("ff4d4d"), 6)
		draw_line(Vector2(size.x - 18, 18), Vector2(18, size.y - 18), Color("ff4d4d"), 6)


static func draw_suit(ci: CanvasItem, suit: int, c: Vector2, s: float, col: Color) -> void:
	match suit:
		1:  # heart
			ci.draw_circle(c + Vector2(-0.25, -0.12) * s, 0.28 * s, col)
			ci.draw_circle(c + Vector2(0.25, -0.12) * s, 0.28 * s, col)
			ci.draw_colored_polygon(PackedVector2Array([
				c + Vector2(-0.52, -0.02) * s, c + Vector2(0.52, -0.02) * s, c + Vector2(0, 0.55) * s]), col)
		3:  # diamond
			ci.draw_colored_polygon(PackedVector2Array([
				c + Vector2(0, -0.55) * s, c + Vector2(0.4, 0) * s,
				c + Vector2(0, 0.55) * s, c + Vector2(-0.4, 0) * s]), col)
		0:  # spade
			ci.draw_circle(c + Vector2(-0.25, 0.1) * s, 0.27 * s, col)
			ci.draw_circle(c + Vector2(0.25, 0.1) * s, 0.27 * s, col)
			ci.draw_colored_polygon(PackedVector2Array([
				c + Vector2(-0.51, 0.04) * s, c + Vector2(0, -0.55) * s, c + Vector2(0.51, 0.04) * s]), col)
			ci.draw_colored_polygon(PackedVector2Array([
				c + Vector2(0, 0.1) * s, c + Vector2(0.18, 0.55) * s, c + Vector2(-0.18, 0.55) * s]), col)
		2:  # club
			ci.draw_circle(c + Vector2(0, -0.26) * s, 0.23 * s, col)
			ci.draw_circle(c + Vector2(-0.26, 0.08) * s, 0.23 * s, col)
			ci.draw_circle(c + Vector2(0.26, 0.08) * s, 0.23 * s, col)
			ci.draw_colored_polygon(PackedVector2Array([
				c + Vector2(0, -0.05) * s, c + Vector2(0.18, 0.55) * s, c + Vector2(-0.18, 0.55) * s]), col)
