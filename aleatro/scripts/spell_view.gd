class_name SpellView
extends Control

## A spell card held in the spell slots. Spells with SVG art (SpellSVG)
## show their illustrated card with the numeral and name set in the game's
## font; Omens and Runes use the plain rune tile.

signal tapped(view)

const W := 96.0
const H := 144.0

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
	if SpellSVG.has_art(spell_id):
		_draw_card()
		return
	var d := Data.spell_def(spell_id)
	var col := Data.SPELL_COLOR
	if d.get("omen", false):
		col = Data.OMEN_COLOR
	elif d.has("rune"):
		col = Data.RUNE_COLOR
	var font := ThemeDB.fallback_font
	draw_set_transform_matrix(Anim.float_xform(size, _phase, float_amount))
	var sb := PixelBox.new(col, 4.0, 0.0, true)
	sb.shadow_offset = Vector2(3, 5) + Vector2(1, 3) * Anim.lift(_phase, float_amount) + Anim.parallax(self)
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


## The illustrated card: SVG frame and emblem, then numeral and name.
func _draw_card() -> void:
	draw_set_transform_matrix(Anim.float_xform(size, _phase, float_amount))
	# rasterise at the size actually on screen (at least 2x for crisp lines)
	var zoom := get_global_transform_with_canvas().get_scale().x
	var tex := SpellSVG.texture(spell_id, int(clampf(zoom * size.x * 2.0, 192.0, 1024.0)))
	var lift := Vector2(3, 5) + Vector2(1, 3) * Anim.lift(_phase, float_amount) + Anim.parallax(self)
	draw_texture_rect(tex, Rect2(lift, size), false, Color(0, 0, 0, 0.35))
	draw_texture_rect(tex, Rect2(Vector2.ZERO, size), false)
	# text is set at screen resolution so it stays sharp when the card is zoomed
	var base := Anim.float_xform(size, _phase, float_amount)
	draw_set_transform_matrix(base * Transform2D(0.0, Vector2(1.0 / zoom, 1.0 / zoom), 0.0, Vector2.ZERO))
	var font := ThemeDB.fallback_font
	var k := size.x / SpellSVG.VIEW_W * zoom
	var w := size.x * zoom
	draw_string(font, Vector2(0, (SpellSVG.NUMERAL_Y + 5) * k), SpellSVG.roman(spell_id), HORIZONTAL_ALIGNMENT_CENTER, w,
		maxi(6, int(17 * k)), Color(SpellSVG.GOLD))
	var name: String = Data.spell_def(spell_id).name.to_upper()
	var fs := int(24 * k)
	while fs > 7 and font.get_string_size(name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > 118 * k:
		fs -= 1
	draw_string(font, Vector2(0, (SpellSVG.NAME_Y + 8) * k), name, HORIZONTAL_ALIGNMENT_CENTER, w, fs, Color(SpellSVG.IVORY))
