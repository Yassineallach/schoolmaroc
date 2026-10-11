class_name PhotoUI
extends CanvasLayer
## Minimal photo-mode overlay: shutter, time of day and exit.

signal shutter
signal exit_photo
signal time_changed(v: float)

var _root: Control
var _bar: PanelContainer
var _time: HSlider
var _flash: ColorRect


func _ready() -> void:
	layer = 15
	visible = false
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.theme = UITheme.get_theme()
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_root)
	_flash = ColorRect.new()
	_flash.color = Color(1, 1, 1, 0)
	_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_flash)
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
	_time.custom_minimum_size = Vector2(260, 44)
	_time.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_time.value_changed.connect(func(v): time_changed.emit(v))
	h.add_child(_time)
	var snap := HUD.icon_button("camera", "Snap", 54)
	snap.pressed.connect(func(): shutter.emit())
	h.add_child(snap)


func open(t: float) -> void:
	visible = true
	_time.set_value_no_signal(t)


func hide_bar(v: bool) -> void:
	_bar.visible = not v


func flash() -> void:
	_flash.color.a = 0.9
	create_tween().tween_property(_flash, "color:a", 0.0, 0.45)


func is_over_ui(pos: Vector2) -> bool:
	return visible and _bar.visible and _bar.get_global_rect().has_point(pos)
