class_name PhotoUI
extends CanvasLayer
## Photo mode, as in Tiny Glade: tap the scene to set the focus point, then
## tune the depth of field (aperture and focus range), field of view,
## exposure, saturation, vignette and a colour filter (warm, cool, sepia,
## black & white, dreamy) or a painterly look. Shutter saves the picture;
## the folder button opens where pictures go.

signal shutter
signal exit_photo
signal time_changed(v: float)

var game   # Game
var _root: Control
var _bar: PanelContainer
var _panel: PanelContainer
var _time: HSlider
var _flash: ColorRect
var _fx: ColorRect
var _fx_mat: ShaderMaterial
var _focus_dot: Control
var values := {"aperture": 0.08, "range": 6.0, "fov": 42.0, "exposure": 1.0, "saturation": 1.0, "vignette": 0.35,
		"filter": 0, "paint": false}
var focus_d := 25.0


func _ready() -> void:
	layer = 15
	visible = false
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.theme = UITheme.get_theme()
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_root)
	_fx = ColorRect.new()
	_fx.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fx.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fx_mat = ShaderMaterial.new()
	_fx_mat.shader = load("res://shaders/photo_fx.gdshader")
	_fx.material = _fx_mat
	_root.add_child(_fx)
	_flash = ColorRect.new()
	_flash.color = Color(1, 1, 1, 0)
	_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_flash)
	_focus_dot = UIIcon.new()
	(_focus_dot as UIIcon).icon = "focus"
	_focus_dot.custom_minimum_size = Vector2(46, 46)
	_focus_dot.size = Vector2(46, 46)
	_focus_dot.visible = false
	_root.add_child(_focus_dot)
	_bar = PanelContainer.new()
	_bar.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_bar.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_bar.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_bar.position.y = -16
	_root.add_child(_bar)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 14)
	_bar.add_child(h)
	var back := HUD.icon_button("close", "Back", 54)
	back.pressed.connect(func(): exit_photo.emit())
	h.add_child(back)
	var ic := UIIcon.new()
	ic.icon = "sun"
	ic.custom_minimum_size = Vector2(36, 36)
	ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(ic)
	_time = HSlider.new()
	_time.min_value = 0
	_time.max_value = 1
	_time.step = 0.001
	_time.custom_minimum_size = Vector2(220, 44)
	_time.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_time.value_changed.connect(func(v): time_changed.emit(v))
	h.add_child(_time)
	var tune := HUD.icon_button("settings", "Lens", 54)
	tune.pressed.connect(func(): _panel.visible = not _panel.visible)
	h.add_child(tune)
	var folder := HUD.icon_button("folder", "Folder", 54)
	folder.pressed.connect(_open_folder)
	h.add_child(folder)
	var snap := HUD.icon_button("camera", "Snap", 54)
	snap.pressed.connect(func(): shutter.emit())
	h.add_child(snap)
	_build_panel()


func _build_panel() -> void:
	_panel = PanelContainer.new()
	_panel.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
	_panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	_panel.position.x = -16
	_panel.visible = false
	_root.add_child(_panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	_panel.add_child(v)
	var tip := Label.new()
	tip.text = "Tap the scene to focus"
	tip.add_theme_font_size_override("font_size", 15)
	v.add_child(tip)
	for s in [["aperture", "Blur", 0.0, 0.25, 0.005], ["range", "Focus depth", 1.0, 30.0, 0.5], ["fov", "Lens (FOV)", 15.0, 100.0, 1.0],
			["exposure", "Exposure", 0.5, 1.8, 0.02], ["saturation", "Colour", 0.0, 1.8, 0.02], ["vignette", "Vignette", 0.0, 1.0, 0.02]]:
		var row := HBoxContainer.new()
		var l := Label.new()
		l.text = s[1]
		l.custom_minimum_size.x = 104
		l.add_theme_font_size_override("font_size", 15)
		row.add_child(l)
		var sl := HSlider.new()
		sl.min_value = s[2]
		sl.max_value = s[3]
		sl.step = s[4]
		sl.value = values[s[0]]
		sl.custom_minimum_size = Vector2(170, 36)
		var key: String = s[0]
		sl.value_changed.connect(func(val):
			values[key] = val
			apply())
		row.add_child(sl)
		v.add_child(row)
	var filters := HBoxContainer.new()
	filters.add_theme_constant_override("separation", 4)
	var names := ["None", "Warm", "Cool", "Sepia", "Mono", "Dreamy"]
	var btns: Array[Button] = []
	for i in names.size():
		var b := Button.new()
		b.text = names[i]
		b.focus_mode = Control.FOCUS_NONE
		b.toggle_mode = true
		b.button_pressed = i == 0
		btns.append(b)
		var idx := i
		b.pressed.connect(func():
			for o in btns:
				o.button_pressed = o == b
			values.filter = idx
			apply())
		filters.add_child(b)
	v.add_child(filters)
	var paint := CheckButton.new()
	paint.text = "Painterly"
	paint.focus_mode = Control.FOCUS_NONE
	paint.toggled.connect(func(on):
		values.paint = on
		apply())
	v.add_child(paint)


func open(t: float) -> void:
	visible = true
	_time.set_value_no_signal(t)
	if game:
		focus_d = game.rig.distance
	apply()


## Pushes the lens settings to the camera and the finishing pass.
func apply() -> void:
	_fx_mat.set_shader_parameter("exposure", values.exposure)
	_fx_mat.set_shader_parameter("saturation", values.saturation)
	_fx_mat.set_shader_parameter("vignette", values.vignette)
	_fx_mat.set_shader_parameter("filter_mode", values.filter)
	_fx_mat.set_shader_parameter("paint", 1.0 if values.paint else 0.0)
	if game == null or not visible:
		return
	var cam: Camera3D = game.rig.camera
	cam.fov = values.fov
	var attrs := cam.attributes as CameraAttributesPractical
	if attrs:
		var r: float = values.range
		attrs.dof_blur_far_enabled = values.aperture > 0.001
		attrs.dof_blur_far_distance = focus_d + r * 0.5
		attrs.dof_blur_far_transition = r + 4.0
		attrs.dof_blur_near_enabled = values.aperture > 0.001 and focus_d - r * 0.5 > 0.3
		attrs.dof_blur_near_distance = maxf(0.3, focus_d - r * 0.5)
		attrs.dof_blur_near_transition = maxf(0.5, minf(r, focus_d * 0.6))
		attrs.dof_blur_amount = values.aperture


## Focus on whatever is under the tap.
func focus_at(screen: Vector2) -> void:
	if game == null:
		return
	var cam: Camera3D = game.rig.camera
	var from := cam.project_ray_origin(screen)
	var dir := cam.project_ray_normal(screen)
	var q := PhysicsRayQueryParameters3D.create(from, from + dir * 400.0)
	var hit: Dictionary = game.get_world_3d().direct_space_state.intersect_ray(q)
	if hit.is_empty():
		return
	focus_d = from.distance_to(hit.position)
	_focus_dot.position = screen - _focus_dot.size * 0.5
	_focus_dot.visible = true
	_focus_dot.modulate.a = 1.0
	create_tween().tween_property(_focus_dot, "modulate:a", 0.0, 1.2).set_delay(0.6)
	apply()


func _open_folder() -> void:
	var pictures := OS.get_system_dir(OS.SYSTEM_DIR_PICTURES)
	var dir := pictures.path_join("Everglade") if pictures != "" else ProjectSettings.globalize_path(GladeStore.PHOTO_DIR)
	DirAccess.make_dir_recursive_absolute(dir)
	if OS.shell_open(dir) != OK and game:
		game.hud.toast("Pictures are in " + dir)


func hide_bar(v: bool) -> void:
	_bar.visible = not v
	_panel.visible = _panel.visible and not v
	_focus_dot.visible = false


func flash() -> void:
	_flash.color.a = 0.9
	create_tween().tween_property(_flash, "color:a", 0.0, 0.45)


func is_over_ui(pos: Vector2) -> bool:
	if not visible:
		return false
	if _bar.visible and _bar.get_global_rect().has_point(pos):
		return true
	return _panel.visible and _panel.get_global_rect().has_point(pos)
