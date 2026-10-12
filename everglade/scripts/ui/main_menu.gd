class_name MainMenu
extends CanvasLayer
## Title screen over a slowly orbiting showcase glade.

signal continue_pressed
signal new_glade(template: String)
signal open_glade(id: String)
signal settings_pressed

const TEMPLATES := [
	{"id": "meadow", "label": "Meadow", "desc": "Soft rolling grass, a blank canvas.", "icon": "nature"},
	{"id": "hills", "label": "Hills", "desc": "Hilly ground for terraces and stairs.", "icon": "terrain"},
	{"id": "lake", "label": "Lakeside", "desc": "A pond waiting for bridges and ducks.", "icon": "water"},
	{"id": "hamlet", "label": "Windrise Town", "desc": "A finished fantasy town with windmills to explore.", "icon": "house"},
	{"id": "town", "label": "Town Plaza", "desc": "Paved square, fountain, cafés and golden trees.", "icon": "windrise"},
	{"id": "ruins", "label": "Meadow Ruins", "desc": "Ancient arches and a glowing rotunda in tall grass.", "icon": "grand"},
	{"id": "village", "label": "Jade Lake Village", "desc": "White houses, a stone causeway, rafts and peaks.", "icon": "lakeside"},
]

var root: Control
var _side: VBoxContainer
var _panel: PanelContainer
var _panel_box: VBoxContainer
var _continue_btn: Button


func _ready() -> void:
	layer = 20
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.theme = UITheme.get_theme()
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	# soft vignette on the left so the title reads well
	var shade := ColorRect.new()
	shade.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	shade.custom_minimum_size.x = 520
	shade.color = Color(0.99, 0.96, 0.9, 0.0)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(shade)
	var grad_mat := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = "shader_type canvas_item; void fragment(){ COLOR = vec4(0.99,0.96,0.90, 0.55 * (1.0 - smoothstep(0.2, 1.0, UV.x))); }"
	grad_mat.shader = sh
	shade.material = grad_mat
	_side = VBoxContainer.new()
	_side.set_anchors_preset(Control.PRESET_CENTER_LEFT)
	_side.position = Vector2(70, -300)
	_side.add_theme_constant_override("separation", 10)
	root.add_child(_side)
	var title := Label.new()
	title.text = "Everglade"
	title.add_theme_font_override("font", UITheme.title_font())
	title.add_theme_font_size_override("font_size", 92)
	title.add_theme_color_override("font_color", Color(0.98, 0.97, 0.93))
	title.add_theme_color_override("font_outline_color", Color(0.38, 0.30, 0.24))
	title.add_theme_constant_override("outline_size", 18)
	title.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.25))
	title.add_theme_constant_override("shadow_offset_y", 6)
	_side.add_child(title)
	var sub := Label.new()
	sub.text = "a tiny, cosy place to build"
	sub.add_theme_font_size_override("font_size", 24)
	sub.add_theme_color_override("font_color", Color(0.98, 0.97, 0.93))
	sub.add_theme_color_override("font_outline_color", Color(0.38, 0.30, 0.24, 0.8))
	sub.add_theme_constant_override("outline_size", 8)
	_side.add_child(sub)
	var spacer := Control.new()
	spacer.custom_minimum_size.y = 18
	_side.add_child(spacer)
	_continue_btn = _menu_button("Continue", "play", func(): continue_pressed.emit())
	_menu_button("New glade", "plus", _show_templates)
	_menu_button("My glades", "home", _show_glades)
	_menu_button("Settings", "settings", func(): settings_pressed.emit())
	if not OS.has_feature("mobile") and not OS.has_feature("web"):
		_menu_button("Quit", "close", func(): get_tree().quit())
	_panel = PanelContainer.new()
	_panel.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
	_panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	_panel.position.x = -40
	_panel.visible = false
	root.add_child(_panel)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(520, 470)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_panel.add_child(scroll)
	_panel_box = VBoxContainer.new()
	_panel_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_panel_box.add_theme_constant_override("separation", 10)
	scroll.add_child(_panel_box)
	refresh()


func _menu_button(text: String, icon_name: String, cb: Callable) -> Button:
	var b := Button.new()
	b.custom_minimum_size = Vector2(300, 60)
	b.focus_mode = Control.FOCUS_NONE
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.text = "        " + text
	b.add_theme_font_size_override("font_size", 28)
	var ic := UIIcon.new()
	ic.icon = icon_name
	ic.position = Vector2(14, 11)
	ic.size = Vector2(44, 44)
	b.add_child(ic)
	b.pressed.connect(func():
		Sfx.play("click", -6.0)
		cb.call())
	_side.add_child(b)
	return b


func refresh() -> void:
	_continue_btn.visible = GladeStore.last_glade_id() != ""


func open() -> void:
	visible = true
	refresh()
	_panel.visible = false
	root.modulate.a = 0.0
	create_tween().tween_property(root, "modulate:a", 1.0, 0.4)


func close() -> void:
	var tw := create_tween()
	tw.tween_property(root, "modulate:a", 0.0, 0.3)
	tw.tween_callback(func(): visible = false)


func _clear_panel(title_text: String) -> void:
	for c in _panel_box.get_children():
		c.queue_free()
	var t := Label.new()
	t.text = title_text
	t.add_theme_font_override("font", UITheme.title_font())
	t.add_theme_font_size_override("font_size", 32)
	_panel_box.add_child(t)
	_panel.visible = true


func _show_templates() -> void:
	_clear_panel("Choose a glade")
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 10)
	grid.add_theme_constant_override("v_separation", 10)
	_panel_box.add_child(grid)
	for tpl in TEMPLATES:
		var b := Button.new()
		b.custom_minimum_size = Vector2(420, 94)
		b.focus_mode = Control.FOCUS_NONE
		var h := HBoxContainer.new()
		h.set_anchors_preset(Control.PRESET_FULL_RECT)
		h.mouse_filter = Control.MOUSE_FILTER_IGNORE
		h.add_theme_constant_override("separation", 14)
		b.add_child(h)
		var pad := Control.new()
		pad.custom_minimum_size.x = 4
		h.add_child(pad)
		var ic := UIIcon.new()
		ic.icon = tpl.icon
		ic.custom_minimum_size = Vector2(60, 60)
		ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(ic)
		var v := VBoxContainer.new()
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		h.add_child(v)
		var l := Label.new()
		l.text = tpl.label
		l.add_theme_font_size_override("font_size", 26)
		v.add_child(l)
		var d := Label.new()
		d.text = tpl.desc
		d.add_theme_font_size_override("font_size", 15)
		d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		d.custom_minimum_size.x = 320
		d.add_theme_color_override("font_color", UITheme.INK_SOFT)
		v.add_child(d)
		var id: String = tpl.id
		b.pressed.connect(func():
			Sfx.play("build", -4.0)
			new_glade.emit(id))
		grid.add_child(b)


func _show_glades() -> void:
	_clear_panel("My glades")
	var list := GladeStore.list_glades()
	if list.is_empty():
		var l := Label.new()
		l.text = "No glades yet. Start a new one!"
		_panel_box.add_child(l)
		return
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 10)
	grid.add_theme_constant_override("v_separation", 10)
	_panel_box.add_child(grid)
	for g in list:
		var card := VBoxContainer.new()
		card.add_theme_constant_override("separation", 4)
		var b := TextureButton.new()
		b.texture_normal = g.thumb
		b.ignore_texture_size = true
		b.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_COVERED
		b.custom_minimum_size = Vector2(240, 135)
		var id: String = g.id
		b.pressed.connect(func(): open_glade.emit(id))
		if g.thumb == null:
			var cr := ColorRect.new()
			cr.color = Color(0.6, 0.75, 0.5)
			cr.set_anchors_preset(Control.PRESET_FULL_RECT)
			cr.mouse_filter = Control.MOUSE_FILTER_IGNORE
			b.add_child(cr)
		card.add_child(b)
		var row := HBoxContainer.new()
		var name_label := Label.new()
		name_label.text = g.name
		name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		name_label.add_theme_font_size_override("font_size", 18)
		name_label.clip_text = true
		name_label.custom_minimum_size.x = 150
		row.add_child(name_label)
		var del := HUD.icon_button("trash", "", 36)
		del.pressed.connect(func():
			GladeStore.delete(id)
			Sfx.play("erase")
			_show_glades()
			refresh())
		row.add_child(del)
		card.add_child(row)
		grid.add_child(card)
