class_name Mascot
extends Control

## Ace, a living playing card who explains things: a sly card shark rather
## than a cute buddy (angled brows, narrow eyes, a lopsided smirk). He is a
## different Ace each time he shows up, Spades, Hearts, Clubs, Diamonds in
## turn, in the deck's own suit colours. Materializes in a burst of
## sparks, talks through a speech bubble with a blip per syllable, and can
## offer buttons under the bubble.

signal dismissed
signal poked

const W := 110.0
const H := 150.0
const BUBBLE_W := 400.0
const CHAR_TIME := 0.016

var talking := false
## which Ace he is this time (Data suit order); moves on every appearance
var suit := 0
static var _next_suit := 1  # the first one is Hearts, as he always was
var sfx: Sfx

var _body := Control.new()
var _bubble := PanelContainer.new()
var _text := Label.new()
var _buttons := HBoxContainer.new()
var _sparks := CPUParticles2D.new()
var _mouth_open := 0.0
var _blink := 0.0
var _next_blink := 2.0
var _phase := randf() * TAU
var _bubble_left := true
var _say_id := 0
var _skip := false


func _init(effects: Sfx) -> void:
	sfx = effects
	suit = _next_suit
	_next_suit = (_next_suit + 1) % 4
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	size = Vector2(W, H)

	_body.size = size
	_body.pivot_offset = size / 2
	_body.mouse_filter = Control.MOUSE_FILTER_STOP
	_body.draw.connect(_draw_body)
	_body.gui_input.connect(func(e):
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			poke())
	add_child(_body)

	_sparks.amount = 24
	_sparks.lifetime = 1.6
	_sparks.position = size / 2
	_sparks.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	_sparks.emission_rect_extents = size / 2
	_sparks.direction = Vector2.UP
	_sparks.spread = 60
	_sparks.gravity = Vector2(0, -20)
	_sparks.initial_velocity_min = 10
	_sparks.initial_velocity_max = 35
	_sparks.scale_amount_min = 3
	_sparks.scale_amount_max = 6
	var ramp := Gradient.new()
	ramp.set_color(0, Palette.MULT)
	ramp.set_color(1, Color(0.18, 0.56, 0.91, 0))
	ramp.add_point(0.5, Palette.XMULT)
	_sparks.color_ramp = ramp
	_sparks.show_behind_parent = true
	add_child(_sparks)

	var sb := PixelBox.new(Palette.PAPER, 4.0, 0.0, true)
	sb.outline = 3.0
	sb.outline_color = Palette.INK
	sb.set_content_margin_all(16)
	_bubble.add_theme_stylebox_override("panel", sb)
	_bubble.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bubble.visible = false
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 12)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	_text.custom_minimum_size = Vector2(BUBBLE_W - 32, 0)
	_text.add_theme_font_size_override("font_size", 22)
	_text.add_theme_color_override("font_color", Palette.INK)
	_text.add_theme_constant_override("shadow_offset_x", 0)
	_text.add_theme_constant_override("shadow_offset_y", 0)
	_text.visible_ratio = 0.0
	vb.add_child(_text)
	_buttons.alignment = BoxContainer.ALIGNMENT_END
	_buttons.add_theme_constant_override("separation", 10)
	vb.add_child(_buttons)
	_bubble.add_child(vb)
	add_child(_bubble)


func _process(delta: float) -> void:
	_mouth_open = maxf(0.0, _mouth_open - delta * 6.0)
	_next_blink -= delta
	if _next_blink <= 0.0:
		_blink = 0.12
		_next_blink = randf_range(2.0, 4.5)
	_blink = maxf(0.0, _blink - delta)
	_place_bubble()
	_body.queue_redraw()


## Fade in out of sparks, the way a card materializes.
func appear() -> void:
	modulate.a = 0.0
	_body.scale = Vector2(0.4, 0.4)
	_sparks.emitting = true
	_sparks.restart()
	var tw := create_tween().set_parallel()
	tw.tween_property(self, "modulate:a", 1.0, 0.35)
	tw.tween_property(_body, "scale", Vector2.ONE, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	if sfx:
		sfx.play("ace_appear")


## Type a line into the bubble with voice blips; buttons appear when done.
## `options` is an Array of [label, Callable]; an empty list adds "OK".
func say(text: String, options: Array = [], bubble_left := true) -> void:
	_say_id += 1
	var my_id := _say_id
	_bubble_left = bubble_left
	for b in _buttons.get_children():
		b.queue_free()
	_buttons.visible = false
	# typed out letter by letter, so translate it here rather than in the label
	text = tr(text)
	_text.text = text
	_text.visible_ratio = 0.0
	_bubble.visible = true
	_bubble.scale = Vector2(0.6, 0.6)
	await get_tree().process_frame
	_place_bubble()
	create_tween().tween_property(_bubble, "scale", Vector2.ONE, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	talking = true
	_skip = false
	var n := text.length()
	var shown := 0
	var start := Anim.now()
	# Reveal by elapsed time so typing speed does not depend on frame rate.
	while shown < n and my_id == _say_id and not _skip:
		await get_tree().process_frame
		var target := mini(n, int((Anim.now() - start) / CHAR_TIME))
		var vowel := false
		while shown < target:
			shown += 1
			vowel = vowel or "aeiouyAEIOUY".contains(text[shown - 1])
		_text.visible_characters = shown
		# at most one blip per frame, on a vowel
		if vowel and randf() < 0.6 and _mouth_open < 0.4:
			_mouth_open = 1.0
			if sfx:
				sfx.play("voice", randf_range(0.9, 1.25))
			_body.pivot_offset = _body.size / 2
			_body.scale = Vector2(1.04, 0.97)
			create_tween().tween_property(_body, "scale", Vector2.ONE, 0.12)
	if my_id != _say_id:
		return
	talking = false
	_text.visible_ratio = 1.0
	if options.is_empty():
		options = [["OK", func(): pass]]
	for opt in options:
		_buttons.add_child(_make_button(opt[0], opt[1]))
	_buttons.visible = true


## Hide the bubble but stay on screen.
func say_hide() -> void:
	_say_id += 1
	talking = false
	_bubble.visible = false


func buttons() -> Array:
	return _buttons.get_children().filter(func(c): return c is Button and not c.is_queued_for_deletion())


## Dissolve away and free.
func leave() -> void:
	_say_id += 1
	_bubble.visible = false
	_sparks.emitting = false
	var tw := create_tween().set_parallel()
	tw.tween_property(self, "modulate:a", 0.0, 0.3)
	tw.tween_property(_body, "scale", Vector2(0.3, 1.3), 0.3)
	tw.chain().tween_callback(queue_free)
	dismissed.emit()


func poke() -> void:
	if talking:
		_skip = true  # tapping Ace mid-sentence finishes the line
		return
	_body.pivot_offset = _body.size / 2
	_body.rotation_degrees = randf_range(-12, 12)
	create_tween().tween_property(_body, "rotation_degrees", 0.0, 0.4).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	if sfx:
		sfx.play("voice", 1.4)
	poked.emit()


func _make_button(text: String, cb: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(110, 46)
	var normal := PixelBox.new(Palette.CHIPS, 3.0, 5.0, true)
	normal.content_margin_bottom = 12
	normal.content_margin_left = 14
	normal.content_margin_right = 14
	var pressed: PixelBox = normal.duplicate()
	pressed.pressed = true
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", normal)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	b.add_theme_font_size_override("font_size", 20)
	b.add_theme_color_override("font_color", Color.WHITE)
	b.add_theme_color_override("font_hover_color", Color.WHITE)
	b.add_theme_color_override("font_pressed_color", Color.WHITE)
	b.pressed.connect(func():
		if sfx:
			sfx.play("click")
		cb.call())
	return b


func _place_bubble() -> void:
	if not _bubble.visible:
		return
	var bs := _bubble.size
	var x := -bs.x - 18.0 if _bubble_left else W + 18.0
	_bubble.position = Vector2(x, minf(0.0, H - bs.y) * 0.5 - 10.0)
	_bubble.pivot_offset = Vector2(bs.x if _bubble_left else 0.0, bs.y / 2)


func _draw_body() -> void:
	var t := Anim.now()
	var bob := sin(t * 2.0 + _phase) * 4.0
	var tilt := sin(t * 1.3 + _phase) * 0.04
	var c := _body.size / 2
	_body.draw_set_transform_matrix(Transform2D(tilt, c + Vector2(0, bob)) * Transform2D(0.0, -c))
	var ink := Palette.INK
	var col: Color = Data.SUIT_COLORS[suit]
	var card := PixelBox.new(Palette.PAPER, 4.0, 0.0, true)
	card.outline = 3.0
	card.outline_color = col.darkened(0.25)
	card.shadow_offset = Vector2(4, 8 - bob * 0.5)
	_body.draw_style_box(card, Rect2(Vector2.ZERO, _body.size))
	var font := ThemeDB.fallback_font
	# corner marks: which Ace he is this time, top left and upside down bottom right
	_body.draw_string(font, Vector2(8, 26), "A", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, col)
	CardView.draw_suit(_body, suit, Vector2(15, 38), 13.0, col)
	CardView.draw_suit(_body, suit, Vector2(W - 15, H - 14), 13.0, col)
	# brows: heavy and angled down to the middle, a scheming look
	_body.draw_colored_polygon(PackedVector2Array([Vector2(24, 50), Vector2(46, 57), Vector2(45, 62), Vector2(24, 55)]), ink)
	_body.draw_colored_polygon(PackedVector2Array([Vector2(86, 50), Vector2(64, 57), Vector2(65, 62), Vector2(86, 55)]), ink)
	# eyes: narrow slits with the pupils glancing aside
	var open := 1.0 if _blink <= 0.0 else 0.2
	for ex in [35.0, 75.0]:
		var h := 9.0 * open
		_body.draw_rect(Rect2(ex - 9, 70 - h / 2, 18, h), Color.WHITE)
		_body.draw_rect(Rect2(ex - 9, 70 - h / 2, 18, h), ink, false, 2.0)
		if open > 0.5:
			_body.draw_rect(Rect2(ex + 1, 70 - h / 2, 6, h), ink)
	# a lopsided smirk, up on his right; it opens on teeth as he talks
	var o := 10.0 * _mouth_open
	var smirk := PackedVector2Array([Vector2(38, 95), Vector2(60, 93), Vector2(76, 86), Vector2(77, 90 + o * 0.4), Vector2(61, 98 + o), Vector2(39, 99 + o * 0.6)])
	_body.draw_colored_polygon(smirk, Color("5b1a20"))
	if _mouth_open > 0.2:
		_body.draw_colored_polygon(PackedVector2Array([Vector2(41, 96.5), Vector2(60, 95), Vector2(74, 89.5), Vector2(74, 91.5), Vector2(60, 98), Vector2(41, 99)]), Color.WHITE)
	_body.draw_polyline(PackedVector2Array([Vector2(36, 94), Vector2(38, 95)]), ink, 2.0)
	# his suit, big, on the chest
	CardView.draw_suit(_body, suit, Vector2(c.x, 126), 24.0, col)
