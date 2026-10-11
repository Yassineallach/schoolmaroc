class_name UITheme
extends RefCounted
## Soft, paper-like storybook UI theme built in code.

const CREAM := Color(0.985, 0.965, 0.92, 0.96)
const CREAM_DARK := Color(0.93, 0.89, 0.80, 1.0)
const INK := Color(0.30, 0.25, 0.22)
const INK_SOFT := Color(0.45, 0.39, 0.34)
const ACCENT := Color(0.86, 0.55, 0.36)
const ACCENT_SOFT := Color(0.98, 0.86, 0.72)
const SHADOW := Color(0.2, 0.15, 0.1, 0.18)

static var _theme: Theme


static func get_theme() -> Theme:
	if _theme:
		return _theme
	var t := Theme.new()
	t.default_font_size = 22
	t.default_font = body_font()
	t.set_color("font_color", "Label", INK)
	t.set_color("font_color", "Button", INK)
	t.set_color("font_hover_color", "Button", INK)
	t.set_color("font_pressed_color", "Button", INK)
	t.set_color("font_focus_color", "Button", INK)
	t.set_color("font_disabled_color", "Button", Color(INK, 0.4))
	t.set_stylebox("panel", "PanelContainer", panel_box())
	t.set_stylebox("panel", "Panel", panel_box())
	t.set_stylebox("normal", "Button", button_box(CREAM))
	t.set_stylebox("hover", "Button", button_box(Color(1, 0.98, 0.94)))
	t.set_stylebox("pressed", "Button", button_box(ACCENT_SOFT))
	t.set_stylebox("disabled", "Button", button_box(Color(CREAM, 0.6)))
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	# sliders
	var track := StyleBoxFlat.new()
	track.bg_color = CREAM_DARK
	track.set_corner_radius_all(8)
	track.content_margin_top = 6
	track.content_margin_bottom = 6
	t.set_stylebox("slider", "HSlider", track)
	var fill := StyleBoxFlat.new()
	fill.bg_color = ACCENT
	fill.set_corner_radius_all(8)
	fill.content_margin_top = 6
	fill.content_margin_bottom = 6
	t.set_stylebox("grabber_area", "HSlider", fill)
	t.set_stylebox("grabber_area_highlight", "HSlider", fill)
	var grab := _circle_texture(30, Color.WHITE, ACCENT)
	t.set_icon("grabber", "HSlider", grab)
	t.set_icon("grabber_highlight", "HSlider", grab)
	t.set_stylebox("panel", "PopupPanel", panel_box())
	t.set_stylebox("scroll", "VScrollBar", StyleBoxEmpty.new())
	_theme = t
	return t


static func body_font() -> Font:
	var f = load("res://assets/fonts/Nunito-Bold.woff2")
	if f is Font:
		return f
	var sf := SystemFont.new()
	sf.font_names = PackedStringArray(["Nunito", "Roboto", "sans-serif"])
	return sf


static func title_font() -> Font:
	var f = load("res://assets/fonts/Nunito-ExtraBold.woff2")
	return f if f is Font else body_font()


static func panel_box(col := CREAM, radius := 22) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = col
	sb.set_corner_radius_all(radius)
	sb.shadow_color = SHADOW
	sb.shadow_size = 8
	sb.shadow_offset = Vector2(0, 3)
	sb.content_margin_left = 16
	sb.content_margin_right = 16
	sb.content_margin_top = 12
	sb.content_margin_bottom = 12
	sb.anti_aliasing = true
	return sb


static func button_box(col: Color, radius := 18) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = col
	sb.set_corner_radius_all(radius)
	sb.border_color = Color(0.85, 0.78, 0.66, 0.9)
	sb.set_border_width_all(2)
	sb.content_margin_left = 14
	sb.content_margin_right = 14
	sb.content_margin_top = 8
	sb.content_margin_bottom = 8
	sb.shadow_color = SHADOW
	sb.shadow_size = 3
	sb.shadow_offset = Vector2(0, 2)
	return sb


static func _circle_texture(size: int, fill: Color, ring: Color) -> ImageTexture:
	var img := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var c := Vector2(size, size) * 0.5
	for y in size:
		for x in size:
			var d := Vector2(x + 0.5, y + 0.5).distance_to(c)
			var r := size * 0.5 - 1.0
			var a := clampf(r - d + 0.5, 0.0, 1.0)
			var col := fill if d < r - 4.0 else ring
			img.set_pixel(x, y, Color(col, a))
	return ImageTexture.create_from_image(img)
