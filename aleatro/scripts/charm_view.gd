class_name CharmView
extends Control

## Draws a charm as its pixel-art card (assets/charms_pixel/<id>.png, made
## from the painted cards by tools/pixelize_charms.py) when it has one, else
## as its SVG card (see CharmSVG), or a rune as a tile when `rune_hand` is set.

signal tapped(view)
signal held(view)
signal drag_started(view, pos)
signal dragged(view, pos)
signal drag_ended(view)

const W := 120.0
const H := 150.0

var charm_id := ""
var rune_hand := ""
var edition := ""
## Stake sticker text shown on the card ("ETERNAL", "PERISH 3", "RENTAL").
var sticker := ""
var face_up := true
var smothered := false
var locked := false
var _lock_badge := TextureRect.new()
var float_amount := 1.0
var _phase := randf() * TAU
var _touch := TouchTracker.new()
static var _painted := {}  # charm id -> Texture2D, or null when it has no painted card
var _tilt := Tilt.new()

func _init(id: String = "", rune: String = "", ed: String = "") -> void:
	charm_id = id
	rune_hand = rune
	edition = ed
	size = Vector2(W, H)
	custom_minimum_size = size
	pivot_offset = size / 2
	mouse_filter = Control.MOUSE_FILTER_STOP
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_tilt.attach(self)
	_lock_badge.texture = load("res://assets/ui/lock_badge.png")
	_lock_badge.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_lock_badge.position = Vector2(W - 30, 2)
	_lock_badge.size = Vector2(28, 28)
	_lock_badge.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_lock_badge.visible = false
	add_child(_lock_badge)
	if edition != "":
		_ensure_material().set_shader_parameter("edition", Data.EDITIONS[edition].shader)


func _ensure_material() -> ShaderMaterial:
	if material == null:
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/card_fx.gdshader")
		m.set_shader_parameter("size", size)
		m.set_shader_parameter("phase", _phase)
		material = m
	return material


func _gui_input(event: InputEvent) -> void:
	match _touch.handle(event):
		"tap":
			tapped.emit(self)
		"drag_start":
			drag_started.emit(self, event.global_position)
		"drag":
			dragged.emit(self, event.global_position)
		"drag_end":
			drag_ended.emit(self)
	if event is InputEventMouseButton or _touch.dragging:
		accept_event()


func _process(delta: float) -> void:
	if _touch.tick(delta):
		held.emit(self)
	_tilt.update(self, delta, _touch.pressing or _touch.dragging, _ensure_material)
	if material != null and edition == "foil":
		material.set_shader_parameter("rot", rotation)
	if float_amount > 0.0 and is_visible_in_tree():
		queue_redraw()


## Burn away, then free (Balatro's Card:start_dissolve: 0.7 s, rimmed in
## black then orange unless `colours` says otherwise).
func dissolve(time: float = 0.7, colours: Array = []) -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var m := _ensure_material()
	m.set_shader_parameter("dissolve_seed", randf() * 3000.0)
	if colours.is_empty():
		colours = [Color("374244"), Color("fda200")]  # G.C.BLACK, G.C.ORANGE
	m.set_shader_parameter("burn_colour_1", colours[0])
	m.set_shader_parameter("burn_colour_2", colours[1] if colours.size() > 1 else Color(0, 0, 0, 0))
	var tw := create_tween()
	tw.tween_method(func(v): m.set_shader_parameter("dissolve", v), 0.0, 1.0, time)
	tw.tween_interval(0.05 * time)
	tw.tween_callback(queue_free)


func title() -> String:
	return "Rune: " + rune_hand if rune_hand != "" else Data.charm_def(charm_id).name


func _draw() -> void:
	var t := Prof.begin()
	_paint()
	Prof.end("charm draw", t)


func _paint() -> void:
	var font := ThemeDB.fallback_font
	var col: Color
	var name: String
	if rune_hand != "":
		col = Data.RUNE_COLOR
		name = tr(rune_hand)
	else:
		var d := Data.charm_def(charm_id)
		col = Data.RARITY_COLORS[d.rarity]
		name = tr(d.name)
	draw_set_transform_matrix(Anim.float_xform(size, _phase, float_amount))
	if not face_up:
		_draw_back()
		return
	var sb := PixelBox.new(col, 4.0, 0.0, true)
	sb.rounded = true
	sb.shadow_offset = Vector2(3, 5) + Vector2(1, 3) * Anim.lift(_phase, float_amount) + Anim.parallax(self)
	var painted := painted_art(charm_id) if rune_hand == "" else null
	if painted != null:
		draw_texture_rect(painted, Rect2(sb.shadow_offset, size), false, Color(0, 0, 0, 0.35))
		draw_texture_rect(painted, Rect2(Vector2.ZERO, size), false)
		_draw_overlays(font)
		return
	if rune_hand == "" and CharmSVG.has_art(charm_id):
		# the card art at screen resolution (snapped so tweens reuse textures),
		# over a soft drop shadow of its own silhouette
		var zoom := get_global_transform_with_canvas().get_scale().x
		var px := int(snappedf(clampf(zoom * size.x * 2.0, 192.0, 1024.0), 64.0))
		var tex := CharmSVG.texture(charm_id, px)
		draw_texture_rect(tex, Rect2(sb.shadow_offset, size), false, Color(0, 0, 0, 0.35))
		draw_texture_rect(tex, Rect2(Vector2.ZERO, size), false)
		_draw_overlays(font)
		return
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
	if edition != "":
		var tag: String = tr(Data.EDITIONS[edition].name).to_upper()
		var b := PixelBox.new(Color(0, 0, 0, 0.45), 2.0)
		draw_style_box(b, Rect2(30, 6, 60, 16))
		draw_string(font, Vector2(30, 18.5), tag, HORIZONTAL_ALIGNMENT_CENTER, 60, 11, Color.WHITE)
	draw_multiline_string(font, Vector2(6, 112), name, HORIZONTAL_ALIGNMENT_CENTER, size.x - 12, 19, 2, Color.WHITE)
	_draw_overlays(font)


## The charm's pixel-art card, or null if it has none yet.
static func painted_art(id: String) -> Texture2D:
	if not _painted.has(id):
		var path := "res://assets/charms_pixel/%s.png" % id
		_painted[id] = load(path) if ResourceLoader.exists(path) else null
	return _painted[id]


## Edition tag, padlock and the boss's "disabled" veil, over any face.
func _draw_overlays(font: Font) -> void:
	if edition != "" and rune_hand == "" and (painted_art(charm_id) != null or CharmSVG.has_art(charm_id)):
		var tag: String = tr(Data.EDITIONS[edition].name).to_upper()
		var b := PixelBox.new(Color(0, 0, 0, 0.55), 2.0)
		draw_style_box(b, Rect2(30, size.y - 22, 60, 16))
		draw_string(font, Vector2(30, size.y - 9.5), tag, HORIZONTAL_ALIGNMENT_CENTER, 60, _fit(font, tag, 11, 58), Color.WHITE)
	if sticker != "":
		var sb := PixelBox.new(Color(0.1, 0.08, 0.15, 0.8), 2.0)
		draw_style_box(sb, Rect2(24, 2, size.x - 48, 15))
		draw_string(font, Vector2(24, 13.5), tr(sticker), HORIZONTAL_ALIGNMENT_CENTER, size.x - 48, _fit(font, tr(sticker), 10, size.x - 50), Color("f2d675"))
	# the padlock badge (this charm cannot be sold) is a child, so the card's
	# shader, which maps UV to the whole face, leaves it alone
	_lock_badge.visible = locked
	if locked:
		# ride along with the card's hover and sway
		var xf := Anim.float_xform(size, _phase, float_amount)
		_lock_badge.position = xf * Vector2(W - 30, 2)
		_lock_badge.rotation = xf.get_rotation()
	# a disabled charm wears Balatro's debuff look (card_fx's debuff)
	if smothered or material != null:
		_ensure_material().set_shader_parameter("debuff", smothered)


## The font size, at most `fs`, at which `text` fits in `w` pixels.
static func _fit(font: Font, text: String, fs: int, w: float) -> int:
	while fs > 6 and font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > w:
		fs -= 1
	return fs


func _draw_back() -> void:
	var back := PixelBox.new(Color("3b2f4f"), 4.0, 0.0, true)
	back.rounded = true
	back.outline = 4.0
	back.outline_color = Color("c9a227")
	draw_style_box(back, Rect2(Vector2.ZERO, size))
	var c := size / 2
	for r in [34.0, 22.0, 10.0]:
		draw_arc(c, r, 0, TAU, 24, Color("c9a227", 0.6), 3.0)
	draw_string(ThemeDB.fallback_font, c + Vector2(-20, 12), "?", HORIZONTAL_ALIGNMENT_CENTER, 40, 34, Color("f2d675"))


## Turn over to reveal the face.
func flip_up(delay: float = 0.0) -> void:
	if face_up:
		return
	var tw := create_tween()
	tw.tween_interval(delay)
	tw.tween_property(self, "scale:x", 0.0, 0.09)
	tw.tween_callback(func():
		face_up = true
		queue_redraw())
	tw.tween_property(self, "scale:x", 1.0, 0.09)
