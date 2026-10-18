class_name SettingsPanel
extends CanvasLayer
## Audio, graphics and comfort options.

signal closed

var _root: Control


func _ready() -> void:
	layer = 40
	visible = false
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.theme = UITheme.get_theme()
	add_child(_root)
	var dim := ColorRect.new()
	dim.color = Color(0.1, 0.08, 0.05, 0.35)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.gui_input.connect(func(e):
		if e is InputEventMouseButton and e.pressed:
			close())
	_root.add_child(dim)
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	_root.add_child(panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	v.custom_minimum_size = Vector2(520, 0)
	panel.add_child(v)
	var head := HBoxContainer.new()
	var title := Label.new()
	title.text = "Settings"
	title.add_theme_font_override("font", UITheme.title_font())
	title.add_theme_font_size_override("font_size", 34)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(title)
	var x := HUD.icon_button("close", "", 48)
	x.pressed.connect(close)
	head.add_child(x)
	v.add_child(head)
	v.add_child(_slider("Music", Settings.music_volume, func(val): Settings.music_volume = val))
	v.add_child(_slider("Sound effects", Settings.sfx_volume, func(val): Settings.sfx_volume = val))
	v.add_child(_slider("Ambience", Settings.ambience_volume, func(val): Settings.ambience_volume = val))
	var q := HBoxContainer.new()
	var ql := Label.new()
	ql.text = "Graphics"
	ql.custom_minimum_size.x = 170
	q.add_child(ql)
	var qbuttons: Array[Button] = []
	for i in 3:
		var b := Button.new()
		b.text = ["Battery", "Balanced", "Beautiful"][i]
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(110, 48)
		qbuttons.append(b)
		var idx := i
		b.pressed.connect(func():
			Settings.quality = idx
			Settings.apply()
			Settings.save_settings()
			for j in qbuttons.size():
				HUD._style_selected(qbuttons[j], j == idx))
		HUD._style_selected(b, Settings.quality == i)
		q.add_child(b)
	v.add_child(q)
	v.add_child(_slider("Fog", Settings.fog, func(val): Settings.fog = val))
	v.add_child(_slider("Fog height", Settings.fog_height, func(val): Settings.fog_height = val))
	v.add_child(_slider("Snow (winter)", Settings.snow, func(val): Settings.snow = val))
	v.add_child(_toggle("Vibration", Settings.haptics, func(on): Settings.haptics = on))
	v.add_child(_toggle("Zoom towards the pointer", Settings.zoom_to_cursor, func(on): Settings.zoom_to_cursor = on))
	v.add_child(_toggle("Key hints", Settings.key_hints, func(on): Settings.key_hints = on))
	v.add_child(_toggle("Performance readout", Settings.perf_overlay, func(on): Settings.perf_overlay = on))
	v.add_child(_toggle("Show tips", Settings.show_tips, func(on):
		Settings.show_tips = on
		if on:
			Settings.tips_seen.clear()))
	var credits := Label.new()
	credits.text = "Everglade · made with Godot Engine & Blender\nFont: Nunito (SIL Open Font License)"
	credits.add_theme_font_size_override("font_size", 15)
	credits.add_theme_color_override("font_color", UITheme.INK_SOFT)
	credits.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(credits)


func _slider(text: String, value: float, cb: Callable) -> Control:
	var h := HBoxContainer.new()
	var l := Label.new()
	l.text = text
	l.custom_minimum_size.x = 170
	h.add_child(l)
	var s := HSlider.new()
	s.min_value = 0.0
	s.max_value = 1.0
	s.step = 0.01
	s.value = value
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.custom_minimum_size.y = 44
	s.value_changed.connect(func(val):
		cb.call(val)
		Settings.apply())
	h.add_child(s)
	return h


func _toggle(text: String, value: bool, cb: Callable) -> Control:
	var c := CheckButton.new()
	c.text = text
	c.button_pressed = value
	c.focus_mode = Control.FOCUS_NONE
	c.toggled.connect(func(on): cb.call(on))
	return c


func open() -> void:
	visible = true
	_root.modulate.a = 0.0
	create_tween().tween_property(_root, "modulate:a", 1.0, 0.2)


func close() -> void:
	Settings.save_settings()
	visible = false
	closed.emit()
