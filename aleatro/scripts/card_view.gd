class_name CardView
extends Control

signal tapped(view)
signal held(view)
signal drag_started(view, pos)
signal dragged(view, pos)
signal drag_ended(view)

const W := 100.0
const H := 140.0
## The card back colour: the run's starting deck sets it.
static var back_color := Color("b3364e")
static var back_art: Texture2D = null
static var _enh_faces := {}
static var _seal_art := {}  # seal id -> Texture2D or null  # enhancement id -> Texture2D or null  # the current deck's card back, if it has art

var card: Dictionary
var selected := false
var debuffed := false
var face_up := true
var float_amount := 0.5
var _phase := randf() * TAU
var _touch := TouchTracker.new()
var _tilt := Tilt.new()

static var _face_box: PixelBox
static var _select_box: PixelBox
static var _fx_shader: Shader


func _init(c: Dictionary = {}) -> void:
	card = c
	size = Vector2(W, H)
	custom_minimum_size = size
	pivot_offset = size / 2
	mouse_filter = Control.MOUSE_FILTER_STOP
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR  # face art is pre-scaled 2x, so this stays crisp
	_tilt.attach(self)
	if _face_box == null:
		_face_box = PixelBox.new(Color("f7f3ea"), 4.0, 0.0, true)
		_face_box.rounded = true
		_face_box.outline = 2.0
		_face_box.outline_color = Color("c9c2b0")
		_select_box = PixelBox.new(Color(0, 0, 0, 0), 4.0)
		_select_box.rounded = true
		_select_box.outline = 4.0
		_select_box.outline_color = Color("ffcc33")
		_fx_shader = load("res://shaders/card_fx.gdshader")
	if card.get("ed", "") != "":
		_ensure_material().set_shader_parameter("edition", Data.EDITIONS[card.ed].shader)


func _ensure_material() -> ShaderMaterial:
	if material == null:
		var m := ShaderMaterial.new()
		m.shader = _fx_shader
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
	if float_amount > 0.0 and is_visible_in_tree():
		queue_redraw()


func set_debuffed(v: bool) -> void:
	debuffed = v
	if v or material != null:
		_ensure_material().set_shader_parameter("debuff", v)
	queue_redraw()


## Turn over to reveal the face (squash to an edge, swap, unsquash).
func flip_up(delay: float = 0.0) -> void:
	face_up = false
	queue_redraw()
	var tw := create_tween()
	tw.tween_interval(delay)
	tw.tween_property(self, "scale:x", 0.0, 0.09)
	tw.tween_callback(func():
		face_up = true
		queue_redraw())
	tw.tween_property(self, "scale:x", 1.0, 0.09)


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


func _draw() -> void:
	var t := Prof.begin()
	_paint()
	Prof.end("card draw", t)


func _paint() -> void:
	var amount := float_amount * (2.0 if selected else 1.0)
	var base := Anim.float_xform(size, _phase, amount)
	draw_set_transform_matrix(base)
	var lift := Anim.lift(_phase, amount)
	# lifted cards cast a longer shadow
	_face_box.shadow_offset = (Vector2(6, 12) if selected else Vector2(3, 6)) + Vector2(1, 3) * lift + Anim.parallax(self)
	if not face_up:
		_draw_back()
		return
	var enh: String = card.get("enh", "")
	var face_art := enh_face(enh)
	if face_art != null:
		# the enhancement's own card face, over the box's shadow
		_face_box.color = Color(0, 0, 0, 0)
		_face_box.outline = 0.0
		draw_style_box(_face_box, Rect2(Vector2.ZERO, size))
		_face_box.outline = 2.0
		draw_texture_rect(face_art, Rect2(Vector2.ZERO, size), false)
	else:
		_face_box.color = Data.ENHANCEMENTS[enh].face if enh != "" else Color("f7f3ea")
		draw_style_box(_face_box, Rect2(Vector2.ZERO, size))
		_draw_enhancement(enh)
	if selected:
		draw_style_box(_select_box, Rect2(Vector2.ZERO, size))
	# indices, pips and court figures: one cached pixel image (Stone has none)
	if enh != "stone":
		draw_texture_rect(DeckArt.face(card.rank, card.suit), Rect2(Vector2.ZERO, size), false)
	if enh != "":
		_draw_badge(Data.ENHANCEMENTS[enh].name, Data.ENHANCEMENTS[enh].badge)
	if card.get("seal", "") != "":
		var sc: Color = Data.SEALS[card.seal].color
		var at := Vector2(size.x - 15, size.y / 2)
		var stamp := seal_art(card.seal)
		if stamp != null:
			# the wax seal art, with a soft shadow
			draw_texture_rect(stamp, Rect2(at - Vector2(13, 11), Vector2(28, 28)), false, Color(0, 0, 0, 0.35))
			draw_texture_rect(stamp, Rect2(at - Vector2(14, 14), Vector2(28, 28)), false)
		else:
			draw_circle(at + Vector2(1, 2), 10, Color(0, 0, 0, 0.3))
			draw_circle(at, 10, sc.darkened(0.3))
			draw_circle(at, 7, sc)
			draw_circle(at + Vector2(-2, -2), 2.5, sc.lightened(0.5))


func _draw_back() -> void:
	if back_art != null:
		_face_box.color = Color(0, 0, 0, 0)
		_face_box.outline = 0.0
		draw_style_box(_face_box, Rect2(Vector2.ZERO, size))  # just its shadow
		_face_box.outline = 2.0
		draw_texture_rect(back_art, Rect2(Vector2.ZERO, size), false)
		return
	_face_box.color = back_color
	draw_style_box(_face_box, Rect2(Vector2.ZERO, size))
	var inner := PixelBox.new(back_color.darkened(0.25), 3.0)
	inner.rounded = true
	inner.outline = 2.0
	inner.outline_color = Color(1, 1, 1, 0.5)
	draw_style_box(inner, Rect2(8, 8, size.x - 16, size.y - 16))
	for y in range(18, int(size.y) - 12, 18):
		for x in range(20, int(size.x) - 12, 20):
			var c := Vector2(x + (9 if (y / 18) % 2 == 0 else 0), y)
			if c.x < size.x - 12:
				draw_colored_polygon(PackedVector2Array([c + Vector2(0, -5), c + Vector2(4, 0), c + Vector2(0, 5), c + Vector2(-4, 0)]), Color(1, 1, 1, 0.25))


## The wax seal art for `seal` (assets/seals/<seal>.png), or null.
static func seal_art(seal: String) -> Texture2D:
	if not _seal_art.has(seal):
		var path := "res://assets/seals/%s.png" % seal
		_seal_art[seal] = load(path) if ResourceLoader.exists(path) else null
	return _seal_art[seal]


## The card face art for enhancement `enh` (assets/enhancements/<enh>.png),
## or null for a plain card or an enhancement without art.
static func enh_face(enh: String) -> Texture2D:
	if enh == "":
		return null
	if not _enh_faces.has(enh):
		var path := "res://assets/enhancements/%s.png" % enh
		_enh_faces[enh] = load(path) if ResourceLoader.exists(path) else null
	return _enh_faces[enh]


## The card back art for deck `id` (assets/decks/<id>.png), or null.
static func deck_back(id: String) -> Texture2D:
	var path := "res://assets/decks/%s.png" % id
	return load(path) if ResourceLoader.exists(path) else null


func _draw_enhancement(enh: String) -> void:
	match enh:
		"glass":
			for i in 3:
				var x := 22.0 + i * 26.0
				draw_line(Vector2(x, 10), Vector2(x - 18, 40), Color(1, 1, 1, 0.7), 4.0 - i)
		"iron":
			for p in [Vector2(9, 9), Vector2(size.x - 9, 9), Vector2(9, size.y - 9), Vector2(size.x - 9, size.y - 9)]:
				draw_circle(p, 3, Color("8a929e"))
		"stone":
			# speckled rock with a few cracks
			for i in 26:
				var p := Vector2(fmod(i * 37.0, size.x - 16) + 8, fmod(i * 53.0, size.y - 24) + 8)
				draw_rect(Rect2(p, Vector2(4, 4)), Color("6f6a64") if i % 3 else Color("bdb7af"))
			draw_polyline(PackedVector2Array([Vector2(16, 30), Vector2(34, 44), Vector2(30, 62), Vector2(48, 78)]), Color("5d5852"), 3.0)
			draw_polyline(PackedVector2Array([Vector2(size.x - 14, 90), Vector2(size.x - 34, 104), Vector2(size.x - 28, 122)]), Color("5d5852"), 3.0)
		"wild":
			var rainbow := [Color("e63946"), Color("f08a24"), Color("f5d742"), Color("3fb97a"), Color("42aaf0"), Color("9b5de5")]
			for i in rainbow.size():
				draw_rect(Rect2(8 + i * 6, size.y - 30, 6, 6), Color(rainbow[i], 0.8))
		"lucky":
			for p in [Vector2(80, 14), Vector2(20, 126)]:
				for k in 4:
					var a := PI / 2 * k + PI / 4
					draw_circle(p + Vector2(cos(a), sin(a)) * 4, 3.2, Color("3b9a4a", 0.6))


func _draw_badge(text: String, col: Color) -> void:
	var font := ThemeDB.fallback_font
	# bottom middle, below the lowest pips and clear of the corner index
	var r := Rect2(22, size.y - 17, 56, 13)
	var b := PixelBox.new(col, 2.0)
	b.rounded = true
	draw_style_box(b, r)
	var label := tr(text).to_upper()
	var fs := 9
	while fs > 6 and font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > r.size.x - 2:
		fs -= 1
	draw_string(font, Vector2(r.position.x, r.position.y + 10.5), label, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, fs, Color.WHITE)


static func draw_suit(ci: CanvasItem, suit: int, c: Vector2, s: float, col: Color) -> void:
	match suit:
		1:  # heart
			ci.draw_circle(c + Vector2(-0.25, -0.12) * s, 0.28 * s, col)
			ci.draw_circle(c + Vector2(0.25, -0.12) * s, 0.28 * s, col)
			ci.draw_colored_polygon(PackedVector2Array([
				c + Vector2(-0.52, -0.02) * s, c + Vector2(0.52, -0.02) * s, c + Vector2(0, 0.55) * s]), col)
		3:  # diamond
			ci.draw_colored_polygon(PackedVector2Array([
				c + Vector2(0, -0.55) * s, c + Vector2(0.4, 0) * s,
				c + Vector2(0, 0.55) * s, c + Vector2(-0.4, 0) * s]), col)
		0:  # spade
			ci.draw_circle(c + Vector2(-0.25, 0.1) * s, 0.27 * s, col)
			ci.draw_circle(c + Vector2(0.25, 0.1) * s, 0.27 * s, col)
			ci.draw_colored_polygon(PackedVector2Array([
				c + Vector2(-0.51, 0.04) * s, c + Vector2(0, -0.55) * s, c + Vector2(0.51, 0.04) * s]), col)
			ci.draw_colored_polygon(PackedVector2Array([
				c + Vector2(0, 0.1) * s, c + Vector2(0.18, 0.55) * s, c + Vector2(-0.18, 0.55) * s]), col)
		2:  # club
			ci.draw_circle(c + Vector2(0, -0.26) * s, 0.23 * s, col)
			ci.draw_circle(c + Vector2(-0.26, 0.08) * s, 0.23 * s, col)
			ci.draw_circle(c + Vector2(0.26, 0.08) * s, 0.23 * s, col)
			ci.draw_colored_polygon(PackedVector2Array([
				c + Vector2(0, -0.05) * s, c + Vector2(0.18, 0.55) * s, c + Vector2(-0.18, 0.55) * s]), col)
