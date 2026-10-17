class_name HUD
extends CanvasLayer
## In-game interface: tool belt, per-tool option strip, inspector for the
## selected piece, undo/redo, time-of-day dial, seasons and photo mode.

signal tool_selected(id: String)
signal option_changed(key: String, value: Variant)
signal inspector_action(action: String, value: Variant)
signal undo_pressed
signal redo_pressed
signal home_pressed
signal photo_pressed
signal settings_pressed
signal time_changed(value: float)
signal season_pressed

const TOOLS := [
	{"id": "hand", "label": "Explore", "icon": "hand"},
	{"id": "wall", "label": "Walls", "icon": "wall"},
	{"id": "building", "label": "Houses", "icon": "building"},
	{"id": "roof", "label": "Roofs", "icon": "roof"},
	{"id": "details", "label": "Windows", "icon": "details"},
	{"id": "fence", "label": "Fences", "icon": "fence"},
	{"id": "path", "label": "Paths", "icon": "path"},
	{"id": "stairs", "label": "Stairs", "icon": "stairs"},
	{"id": "nature", "label": "Nature", "icon": "nature"},
	{"id": "decor", "label": "Decor", "icon": "decor"},
	{"id": "water", "label": "Ponds", "icon": "water"},
	{"id": "terrain", "label": "Land", "icon": "terrain"},
	{"id": "eraser", "label": "Eraser", "icon": "eraser"},
]

var root: Control
var thumbs: Thumbs
var _tool_buttons: Dictionary = {}
var _options_panel: PanelContainer
var _options_box: HBoxContainer
var _inspector: PanelContainer
var _inspector_box: VBoxContainer
var _hint_panel: PanelContainer
var _hint_label: Label
var _toast: Label
var _undo_btn: Button
var _redo_btn: Button
var _time_slider: HSlider
var _time_icon: UIIcon
var _season_btn: Button
var _tool_bar: PanelContainer
var _hint_tween: Tween
var _thumb_targets: Dictionary = {}


func _ready() -> void:
	layer = 10
	thumbs = Thumbs.new()
	add_child(thumbs)
	thumbs.ready_thumb.connect(_on_thumb)
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.theme = UITheme.get_theme()
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(margin)
	_apply_safe_area(margin)
	get_viewport().size_changed.connect(func(): _apply_safe_area(margin))
	var layer_box := Control.new()
	layer_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(layer_box)
	_build_top(layer_box)
	_build_bottom(layer_box)
	_build_inspector(layer_box)
	_build_hint(layer_box)


func _apply_safe_area(margin: MarginContainer) -> void:
	var safe := DisplayServer.get_display_safe_area()
	var win := DisplayServer.window_get_size()
	var vp := get_viewport().get_visible_rect().size
	var sx := vp.x / maxf(1.0, win.x)
	var sy := vp.y / maxf(1.0, win.y)
	var l := 14.0
	var t := 12.0
	var r := 14.0
	var b := 10.0
	if OS.has_feature("mobile") and safe.size.x > 0:
		l = maxf(l, safe.position.x * sx)
		t = maxf(t, safe.position.y * sy)
		r = maxf(r, (win.x - safe.end.x) * sx)
		b = maxf(b, (win.y - safe.end.y) * sy)
	margin.add_theme_constant_override("margin_left", int(l))
	margin.add_theme_constant_override("margin_top", int(t))
	margin.add_theme_constant_override("margin_right", int(r))
	margin.add_theme_constant_override("margin_bottom", int(b))


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------
static func icon_button(icon_name: String, label_text := "", px := 60.0) -> Button:
	var b := Button.new()
	b.custom_minimum_size = Vector2(px, px + (20.0 if label_text != "" else 0.0))
	b.focus_mode = Control.FOCUS_NONE
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_theme_constant_override("separation", 0)
	b.add_child(v)
	var ic := UIIcon.new()
	ic.name = "Icon"
	ic.icon = icon_name
	ic.custom_minimum_size = Vector2(px * 0.62, px * 0.62)
	ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(ic)
	if label_text != "":
		var l := Label.new()
		l.text = label_text
		l.add_theme_font_size_override("font_size", 15)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(l)
	b.button_down.connect(func(): Sfx.play("click", -10.0, 0.1))
	return b


static func _style_selected(b: Button, on: bool) -> void:
	if on:
		b.add_theme_stylebox_override("normal", UITheme.button_box(UITheme.ACCENT_SOFT))
		b.add_theme_stylebox_override("hover", UITheme.button_box(UITheme.ACCENT_SOFT))
	else:
		b.remove_theme_stylebox_override("normal")
		b.remove_theme_stylebox_override("hover")


func _build_top(parent: Control) -> void:
	var left := HBoxContainer.new()
	left.add_theme_constant_override("separation", 8)
	left.set_anchors_preset(Control.PRESET_TOP_LEFT)
	parent.add_child(left)
	var home := icon_button("home", "", 56)
	home.pressed.connect(func(): home_pressed.emit())
	left.add_child(home)
	_undo_btn = icon_button("undo", "", 56)
	_undo_btn.pressed.connect(func(): undo_pressed.emit())
	left.add_child(_undo_btn)
	_redo_btn = icon_button("redo", "", 56)
	_redo_btn.pressed.connect(func(): redo_pressed.emit())
	left.add_child(_redo_btn)

	var right := HBoxContainer.new()
	right.add_theme_constant_override("separation", 8)
	right.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	right.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	parent.add_child(right)
	var time_panel := PanelContainer.new()
	time_panel.add_theme_stylebox_override("panel", UITheme.panel_box(UITheme.CREAM, 28))
	var th := HBoxContainer.new()
	th.add_theme_constant_override("separation", 8)
	time_panel.add_child(th)
	_time_icon = UIIcon.new()
	_time_icon.icon = "sun"
	_time_icon.custom_minimum_size = Vector2(34, 34)
	th.add_child(_time_icon)
	_time_slider = HSlider.new()
	_time_slider.min_value = 0.0
	_time_slider.max_value = 1.0
	_time_slider.step = 0.001
	_time_slider.custom_minimum_size = Vector2(200, 34)
	_time_slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_time_slider.value_changed.connect(func(v): time_changed.emit(v))
	th.add_child(_time_slider)
	right.add_child(time_panel)
	_season_btn = icon_button("season", "Summer", 56)
	_season_btn.custom_minimum_size.x = 84
	_season_btn.pressed.connect(func(): season_pressed.emit())
	right.add_child(_season_btn)
	var photo := icon_button("camera", "", 56)
	photo.pressed.connect(func(): photo_pressed.emit())
	right.add_child(photo)
	var settings := icon_button("settings", "", 56)
	settings.pressed.connect(func(): settings_pressed.emit())
	right.add_child(settings)


func _build_bottom(parent: Control) -> void:
	var col := VBoxContainer.new()
	col.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	col.grow_horizontal = Control.GROW_DIRECTION_BOTH
	col.grow_vertical = Control.GROW_DIRECTION_BEGIN
	col.alignment = BoxContainer.ALIGNMENT_END
	col.add_theme_constant_override("separation", 8)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(col)
	_options_panel = PanelContainer.new()
	_options_panel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	var scroll := ScrollContainer.new()
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	scroll.custom_minimum_size = Vector2(0, 74)
	_options_panel.add_child(scroll)
	_options_box = HBoxContainer.new()
	_options_box.add_theme_constant_override("separation", 10)
	scroll.add_child(_options_box)
	col.add_child(_options_panel)
	_tool_bar = PanelContainer.new()
	_tool_bar.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_tool_bar.add_theme_stylebox_override("panel", UITheme.panel_box(UITheme.CREAM, 26))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	_tool_bar.add_child(row)
	for t in TOOLS:
		var b := icon_button(t.icon, t.label, 58)
		b.custom_minimum_size.x = 74
		var id: String = t.id
		b.pressed.connect(func(): tool_selected.emit(id))
		row.add_child(b)
		_tool_buttons[id] = b
	col.add_child(_tool_bar)
	# keep the scroll width sensible on narrow screens
	_options_panel.resized.connect(func():
		var maxw := get_viewport().get_visible_rect().size.x - 60.0
		scroll.custom_minimum_size.x = minf(_options_box.get_combined_minimum_size().x, maxw))


func _build_inspector(parent: Control) -> void:
	_inspector = PanelContainer.new()
	_inspector.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
	_inspector.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_inspector.grow_vertical = Control.GROW_DIRECTION_BOTH
	_inspector.custom_minimum_size = Vector2(300, 0)
	_inspector.visible = false
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.custom_minimum_size = Vector2(290, 0)
	_inspector.add_child(scroll)
	_inspector_box = VBoxContainer.new()
	_inspector_box.add_theme_constant_override("separation", 10)
	_inspector_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_inspector_box)
	parent.add_child(_inspector)
	get_viewport().size_changed.connect(_fit_inspector)
	_fit_inspector()


func _fit_inspector() -> void:
	var h := get_viewport().get_visible_rect().size.y
	(_inspector.get_child(0) as ScrollContainer).custom_minimum_size.y = minf(h - 260.0, 460.0)


func _build_hint(parent: Control) -> void:
	_hint_panel = PanelContainer.new()
	_hint_panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_hint_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_hint_panel.position.y = 76
	_hint_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hint_panel.modulate.a = 0.0
	_hint_label = Label.new()
	_hint_label.add_theme_font_size_override("font_size", 19)
	_hint_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_hint_label.custom_minimum_size = Vector2(420, 0)
	_hint_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hint_panel.add_child(_hint_label)
	parent.add_child(_hint_panel)
	_toast = Label.new()
	_toast.set_anchors_preset(Control.PRESET_CENTER)
	_toast.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_toast.add_theme_font_size_override("font_size", 30)
	_toast.add_theme_color_override("font_color", Color.WHITE)
	_toast.add_theme_color_override("font_outline_color", Color(0.3, 0.22, 0.16, 0.8))
	_toast.add_theme_constant_override("outline_size", 10)
	_toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_toast.modulate.a = 0.0
	_toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(_toast)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
func set_tool(id: String, tool_node: BaseTool) -> void:
	for key in _tool_buttons:
		_style_selected(_tool_buttons[key], key == id)
	_build_options(tool_node)
	if tool_node:
		show_hint(tool_node.hint())


func _build_options(tool_node: BaseTool) -> void:
	for c in _options_box.get_children():
		c.queue_free()
	_thumb_targets.clear()
	var defs: Array = tool_node.option_defs() if tool_node else []
	_options_panel.visible = not defs.is_empty()
	for d in defs:
		_options_box.add_child(_make_option(d, tool_node.options, func(k, v): option_changed.emit(k, v)))
	await get_tree().process_frame
	if is_instance_valid(_options_panel):
		_options_panel.resized.emit()


func _make_option(d: Dictionary, values: Dictionary, on_change: Callable) -> Control:
	var key: String = d.get("key", "")
	match d.type:
		"choice":
			var row := HBoxContainer.new()
			row.add_theme_constant_override("separation", 6)
			var buttons: Array[Button] = []
			for item in d.items:
				var b := icon_button(item.get("icon", item.id), item.label, 46)
				b.custom_minimum_size.x = 74
				var id = item.id
				buttons.append(b)
				_style_selected(b, values.get(key) == id)
				b.pressed.connect(func():
					for other in buttons:
						_style_selected(other, other == b)
					on_change.call(key, id))
				row.add_child(b)
				var kind := String(item.get("icon", ""))
				if Catalog.DECOR.has(kind) or Catalog.NATURE.has(kind):
					var model_kind: String = kind if Catalog.DECOR.has(kind) else String(Catalog.NATURE[kind].kinds[0])
					var ic := b.find_child("Icon", true, false) as UIIcon
					var tex := thumbs.get_thumb(model_kind)
					if tex:
						ic.texture = tex
					else:
						if not _thumb_targets.has(model_kind):
							_thumb_targets[model_kind] = []
						_thumb_targets[model_kind].append(ic)
			return row
		"slider":
			var box := HBoxContainer.new()
			box.add_theme_constant_override("separation", 6)
			var l := Label.new()
			l.text = d.label
			l.add_theme_font_size_override("font_size", 17)
			box.add_child(l)
			var s := HSlider.new()
			s.min_value = d.min
			s.max_value = d.max
			s.step = d.step
			s.value = values.get(key, d.min)
			s.custom_minimum_size = Vector2(170, 44)
			s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			var vl := Label.new()
			vl.text = _fmt(s.value)
			vl.custom_minimum_size.x = 40
			vl.add_theme_font_size_override("font_size", 17)
			s.value_changed.connect(func(v):
				vl.text = _fmt(v)
				on_change.call(key, v))
			box.add_child(s)
			box.add_child(vl)
			return box
		"colors":
			var row2 := HBoxContainer.new()
			row2.add_theme_constant_override("separation", 4)
			var swatches: Array[Button] = []
			var colors: Array = d.colors
			for i in colors.size():
				var b2 := Button.new()
				b2.focus_mode = Control.FOCUS_NONE
				b2.custom_minimum_size = Vector2(40, 40)
				swatches.append(b2)
				_style_swatch(b2, colors[i], values.get(key, 0) == i)
				var idx := i
				b2.pressed.connect(func():
					for j in swatches.size():
						_style_swatch(swatches[j], colors[j], j == idx)
					Sfx.play("click", -10.0)
					on_change.call(key, idx))
				row2.add_child(b2)
			return row2
		"toggle":
			var t := icon_button(d.get("icon", "check"), d.label, 46)
			t.custom_minimum_size.x = 80
			t.toggle_mode = true
			t.button_pressed = values.get(key, false)
			_style_selected(t, t.button_pressed)
			t.toggled.connect(func(on):
				_style_selected(t, on)
				on_change.call(key, on))
			return t
		"stepper":
			var box2 := HBoxContainer.new()
			var l2 := Label.new()
			l2.text = d.label
			l2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			l2.add_theme_font_size_override("font_size", 18)
			box2.add_child(l2)
			var minus := icon_button("minus", "", 40)
			minus.pressed.connect(func(): on_change.call(key, -1))
			box2.add_child(minus)
			var val := Label.new()
			val.text = str(d.get("value", ""))
			val.custom_minimum_size.x = 34
			val.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			box2.add_child(val)
			var plus := icon_button("plus", "", 40)
			plus.pressed.connect(func(): on_change.call(key, 1))
			box2.add_child(plus)
			return box2
		"actions":
			var flow := HFlowContainer.new()
			flow.add_theme_constant_override("h_separation", 6)
			flow.add_theme_constant_override("v_separation", 6)
			for item in d.items:
				var b3 := icon_button(item.icon, item.label, 44)
				b3.custom_minimum_size.x = 84
				var act: String = item.id
				b3.pressed.connect(func(): on_change.call(act, true))
				flow.add_child(b3)
			return flow
		"title":
			var tl := Label.new()
			tl.text = d.text
			tl.add_theme_font_override("font", UITheme.title_font())
			tl.add_theme_font_size_override("font_size", 26)
			return tl
		"label":
			var ll := Label.new()
			ll.text = d.text
			ll.add_theme_font_size_override("font_size", 16)
			ll.add_theme_color_override("font_color", UITheme.INK_SOFT)
			ll.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			return ll
	return Control.new()


func _style_swatch(b: Button, col: Color, selected: bool) -> void:
	for st in ["normal", "hover", "pressed"]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = col
		sb.set_corner_radius_all(20)
		sb.border_color = UITheme.INK if selected else Color(1, 1, 1, 0.9)
		sb.set_border_width_all(4 if selected else 3)
		b.add_theme_stylebox_override(st, sb)


func _fmt(v: float) -> String:
	return str(int(v)) if is_equal_approx(v, round(v)) else "%.1f" % v


func _on_thumb(kind: String, tex: Texture2D) -> void:
	for ic in _thumb_targets.get(kind, []):
		if is_instance_valid(ic):
			ic.texture = tex


## Inspector content uses the same descriptors as tool options.
func show_inspector(defs: Array, values: Dictionary = {}) -> void:
	for c in _inspector_box.get_children():
		c.queue_free()
	for d in defs:
		_inspector_box.add_child(_make_option(d, values, func(k, v): inspector_action.emit(k, v)))
	if not _inspector.visible:
		_inspector.visible = true
		_inspector.modulate.a = 0.0
		_inspector.pivot_offset = Vector2(150, 0)
		create_tween().tween_property(_inspector, "modulate:a", 1.0, 0.15)


func hide_inspector() -> void:
	_inspector.visible = false


func show_hint(text: String, key := "") -> void:
	if text == "":
		return
	if key != "" and Settings.tip_seen(key):
		return
	if key != "":
		Settings.mark_tip(key)
	_hint_label.text = text
	if _hint_tween:
		_hint_tween.kill()
	_hint_tween = create_tween()
	_hint_tween.tween_property(_hint_panel, "modulate:a", 1.0, 0.25)
	_hint_tween.tween_interval(4.5)
	_hint_tween.tween_property(_hint_panel, "modulate:a", 0.0, 0.6)


func toast(text: String) -> void:
	_toast.text = text
	var tw := create_tween()
	_toast.modulate.a = 0.0
	tw.tween_property(_toast, "modulate:a", 1.0, 0.2)
	tw.tween_interval(1.4)
	tw.tween_property(_toast, "modulate:a", 0.0, 0.5)


func update_undo(can_undo: bool, can_redo: bool) -> void:
	_undo_btn.disabled = not can_undo
	_redo_btn.disabled = not can_redo
	_undo_btn.modulate.a = 1.0 if can_undo else 0.5
	_redo_btn.modulate.a = 1.0 if can_redo else 0.5


func set_time(t: float, night: bool) -> void:
	_time_slider.set_value_no_signal(t)
	_time_icon.icon = "moon" if night else "sun"


func set_season(name_text: String) -> void:
	for c in _season_btn.get_child(0).get_children():
		if c is Label:
			(c as Label).text = name_text


## True when the screen position is over interactive HUD widgets.
func is_over_ui(pos: Vector2) -> bool:
	for c in [_tool_bar, _options_panel, _inspector]:
		var ctl := c as Control
		if ctl.is_visible_in_tree() and ctl.get_global_rect().has_point(pos):
			return true
	var top_h := 90.0
	if pos.y < top_h and (pos.x < 220.0 or pos.x > get_viewport().get_visible_rect().size.x - 560.0):
		return true
	return false
