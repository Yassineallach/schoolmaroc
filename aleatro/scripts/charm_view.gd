class_name CharmView
extends Control

## Draws a charm (or a rune when `rune_hand` is set) as a small tile.

signal tapped(view)

const W := 120.0
const H := 150.0

var charm_id := ""
var rune_hand := ""


func _init(id: String = "", rune: String = "") -> void:
	charm_id = id
	rune_hand = rune
	size = Vector2(W, H)
	custom_minimum_size = size
	pivot_offset = size / 2
	mouse_filter = Control.MOUSE_FILTER_STOP


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		tapped.emit(self)
		accept_event()


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
	var sb := PixelBox.new(col, 4.0, 0.0, true)
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
	draw_multiline_string(font, Vector2(6, 112), name, HORIZONTAL_ALIGNMENT_CENTER, size.x - 12, 19, 2, Color.WHITE)
