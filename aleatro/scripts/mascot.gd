class_name Mascot
extends Control

## Ace, a living playing card who explains things. Materializes in a burst of
## sparks, talks through a speech bubble with a blip per syllable, and can
## offer buttons under the bubble.

signal dismissed
signal poked

const W := 110.0
const H := 150.0
const BUBBLE_W := 400.0
const CHAR_TIME := 0.016

var talking := false
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
	ramp.set_color(0, Color("ff4d4d"))
	ramp.set_color(1, Color(0.18, 0.56, 0.91, 0))
	ramp.add_point(0.5, Color("ff9f1c"))
	_sparks.color_ramp = ramp
	_sparks.show_behind_parent = true
	add_child(_sparks)

	var sb := PixelBox.new(Color("f7f3ea"), 4.0, 0.0, true)
	sb.outline = 3.0
	sb.outline_color = Color("2b2d42")
	sb.set_content_margin_all(16)
	_bubble.add_theme_stylebox_override("panel", sb)
	_bubble.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bubble.visible = false
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 12)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.custom_minimum_size = Vector2(BUBBLE_W - 32, 0)
	_text.add_theme_font_size_override("font_size", 22)
	_text.add_theme_color_override("font_color", Color("2b2d42"))
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
	var normal := PixelBox.new(Color("2f8fe8"), 3.0, 5.0, true)
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
	var card := PixelBox.new(Color("f7f3ea"), 4.0, 0.0, true)
	card.outline = 3.0
	card.outline_color = Color("b3364e")
	card.shadow_offset = Vector2(4, 8 - bob * 0.5)
	_body.draw_style_box(card, Rect2(Vector2.ZERO, _body.size))
	var font := ThemeDB.fallback_font
	var red := Color("e63946")
	# corner marks: he is the Ace of Hearts
	_body.draw_string(font, Vector2(8, 26), "A", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, red)
	CardView.draw_suit(_body, 1, Vector2(15, 38), 13.0, red)
	# face
	var eye_y := 66.0
	var open := 1.0 if _blink <= 0.0 else 0.15
	for ex in [36.0, 74.0]:
		_body.draw_rect(Rect2(ex - 7, eye_y - 9 * open, 14, 18 * open), Color("2b2d42"))
		if open > 0.5:
			_body.draw_rect(Rect2(ex - 3, eye_y - 6, 5, 5), Color.WHITE)
	_body.draw_circle(Vector2(26, 86), 7, Color(red, 0.25))
	_body.draw_circle(Vector2(84, 86), 7, Color(red, 0.25))
	var mouth_h := 4.0 + 12.0 * _mouth_open
	var mouth := PixelBox.new(Color("7a1f2b"), 2.0)
	_body.draw_style_box(mouth, Rect2(c.x - 14, 92, 28, mouth_h))
	# big heart on the chest
	CardView.draw_suit(_body, 1, Vector2(c.x, 124), 26.0, red)
