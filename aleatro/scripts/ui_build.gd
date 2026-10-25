class_name UIBuild
extends RefCounted

## Declarative UI. Describe a screen as nested dictionaries and get real
## Godot containers back; anything live (bound text, bars, delays, enable
## checks) is driven by one small ticker node attached to the result.
##
##   {"row": [...]} / {"col": [...]}    HBox / VBox. sep, align ("start"/"center"/"end")
##   {"grid": [...], "columns": 3}      GridContainer. sep
##   {"text": "Hi"}                     Label. size, color, shadow, wrap (width), lines (max
##                                      shown), fit (max width: shrink the font until it
##                                      fits), align ("left"/"right")
##   {"bind": [obj, key], "fmt": "%s"}  live Label showing obj[key] (fmt String or Callable)
##   {"button": "Play", "on": Callable} styled Button. color, min, size, fit, tooltip,
##                                      delay (s, fills then enables), hold (s, press and
##                                      hold to fire), once, enabled (Callable -> bool,
##                                      checked every frame), choice (group) + chosen
##   {"bar": [obj, key], "max": 1.0}    live progress bar. fill, back, min
##   {"space": Vector2}                 fixed spacer
##   {"node": control}                  embed an existing Control
## Any entry may also carry: panel (Color, wraps it in a pixel panel; pad, outline),
## id, group, expand (fill horizontally; otherwise children keep their own width), tooltip.

## Called on button feedback events: "press", "hold_start", "hold_done".
static var feedback: Callable

const CHOSEN_COLOR := Color("ff4d4d")


static func build(def: Dictionary) -> Control:
	var jobs: Array = []
	var root := _make(def, jobs)
	if not jobs.is_empty():
		var t := Ticker.new()
		t.jobs = jobs
		root.add_child(t)
	return root


# ---------------------------------------------------------------- queries

static func find(root: Node, id: String) -> Control:
	if root is Control and root.get_meta("ui_id", "") == id:
		return root
	for c in root.get_children():
		var r := find(c, id)
		if r != null:
			return r
	return null


static func group(root: Node, name: String, into: Array = []) -> Array:
	if root is Control and root.get_meta("ui_group", "") == name:
		into.append(root)
	for c in root.get_children():
		group(c, name, into)
	return into


static func remove_group(root: Node, name: String) -> void:
	for c in group(root, name):
		c.queue_free()


# ---------------------------------------------------------------- building

static func _make(def: Dictionary, jobs: Array) -> Control:
	var c: Control
	if def.has("row") or def.has("col"):
		var box: BoxContainer = HBoxContainer.new() if def.has("row") else VBoxContainer.new()
		box.add_theme_constant_override("separation", int(def.get("sep", 12)))
		box.alignment = _box_align(def.get("align", "center"))
		for child in def.get("row", def.get("col", [])):
			box.add_child(_child(child, jobs))
		c = box
	elif def.has("grid"):
		var g := GridContainer.new()
		g.columns = int(def.get("columns", 2))
		g.add_theme_constant_override("h_separation", int(def.get("sep", 12)))
		g.add_theme_constant_override("v_separation", int(def.get("sep", 12)))
		for child in def.grid:
			g.add_child(_child(child, jobs))
		c = g
	elif def.has("text") or def.has("bind"):
		c = _text(def, jobs)
	elif def.has("button"):
		c = make_button(def, jobs)
	elif def.has("bar"):
		c = _bar(def, jobs)
	elif def.has("space"):
		c = Control.new()
		c.custom_minimum_size = def.space
		c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	elif def.has("node"):
		c = def.node
	else:
		c = Control.new()

	if def.has("tooltip") and not def.has("button"):
		if c.mouse_filter == Control.MOUSE_FILTER_IGNORE:
			c.mouse_filter = Control.MOUSE_FILTER_PASS
		attach_tooltip(c, def.tooltip)
	if def.has("panel"):
		c = _panel(c, def)
	if def.has("id"):
		c.set_meta("ui_id", String(def.id))
	if def.has("group"):
		c.set_meta("ui_group", String(def.group))
	return c


static func _child(def, jobs: Array) -> Control:
	var c := _make(def, jobs) if def is Dictionary else (def as Control)
	# Children keep their own width unless asked to stretch.
	if def is Dictionary and def.get("expand", false):
		c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	else:
		c.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	return c


static func _box_align(a: String) -> BoxContainer.AlignmentMode:
	match a:
		"start":
			return BoxContainer.ALIGNMENT_BEGIN
		"end":
			return BoxContainer.ALIGNMENT_END
	return BoxContainer.ALIGNMENT_CENTER


static func _panel(inner: Control, def: Dictionary) -> PanelContainer:
	var p := PanelContainer.new()
	var sb := PixelBox.new(def.panel, 4.0, 0.0, true)
	sb.set_content_margin_all(float(def.get("pad", 16)))
	if def.has("outline"):
		sb.outline = 3.0
		sb.outline_color = def.outline
	p.add_theme_stylebox_override("panel", sb)
	p.add_child(inner)
	return p


static func _text(def: Dictionary, jobs: Array) -> Label:
	var l := Label.new()
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.horizontal_alignment = {"left": HORIZONTAL_ALIGNMENT_LEFT, "right": HORIZONTAL_ALIGNMENT_RIGHT}.get(def.get("align", ""), HORIZONTAL_ALIGNMENT_CENTER)
	var size := int(def.get("size", 26))
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", def.get("color", Color.WHITE))
	if def.has("shadow"):
		l.add_theme_color_override("font_shadow_color", def.shadow)
	if def.has("lines"):
		l.max_lines_visible = int(def.lines)
		l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	if def.has("wrap"):
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size.x = float(def.wrap)
	var set_text := func(t: String):
		l.text = t
		if def.has("fit"):
			_fit_label(l, size, float(def.fit))
	if def.has("bind"):
		var src = def.bind[0]
		var key = def.bind[1]
		var fmt = def.get("fmt", "%s")
		var state := {"last": null, "first": true}
		var update := func():
			var v = _read(src, key)
			if state.first or typeof(v) != typeof(state.last) or v != state.last:
				state.first = false
				state.last = v
				set_text.call(fmt.call(v) if fmt is Callable else String(fmt) % [v])
		update.call()
		jobs.append(func(): if is_instance_valid(l): update.call())
	else:
		set_text.call(String(def.text))
	return l


## Shrink a label's font until its text fits in `max_w` pixels.
static func _fit_label(l: Label, size: int, max_w: float) -> void:
	l.add_theme_font_size_override("font_size", fit_size(l.get_theme_font("font"), l.text, size, max_w))


## The largest font size up to `size` at which every line of `text`, as
## translated, fits in `max_w` pixels.
static func fit_size(font: Font, text: String, size: int, max_w: float) -> int:
	var lines := TranslationServer.translate(text).split("\n")
	var s := size
	while s > 10 and Array(lines).any(func(t): return font.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, s).x > max_w):
		s -= 1
	return s


static func _read(src, key):
	if src is Dictionary:
		return src.get(key)
	if is_instance_valid(src):
		return src.get(key)
	return null


# ---------------------------------------------------------------- buttons

## A pixel-style button with a raised lip. Usable directly or via build().
static func make_button(def: Dictionary, jobs: Array = []) -> Button:
	var b := Button.new()
	var col: Color = def.get("color", Color("2f8fe8"))
	var size := int(def.get("size", 28))
	b.text = String(def.button)
	b.custom_minimum_size = def.get("min", Vector2(160, 76))
	b.focus_mode = Control.FOCUS_NONE
	var normal := PixelBox.new(col, 3.0, 6.0, true)
	var pressed := PixelBox.new(col.lightened(0.08), 3.0, 6.0, true)
	pressed.pressed = true
	var disabled := PixelBox.new(col.darkened(0.55).lerp(Color(0.3, 0.3, 0.3), 0.5), 3.0, 6.0, false)
	for sb in [normal, pressed, disabled]:
		sb.content_margin_bottom = 18
		sb.content_margin_left = 10
		sb.content_margin_right = 10
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", normal)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_stylebox_override("disabled", disabled)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	b.add_theme_font_size_override("font_size", size)
	for k in ["font_color", "font_hover_color", "font_pressed_color"]:
		b.add_theme_color_override(k, Color.WHITE)
	b.add_theme_color_override("font_disabled_color", Color(1, 1, 1, 0.4))
	# translated text can run longer than the English: shrink it to the
	# button's width (or the given fit) rather than stretch the layout
	var fit_w: float = float(def.fit) if def.has("fit") else (b.custom_minimum_size.x - 24.0 if Loc.lang != "en" else 0.0)
	if fit_w > 0:
		b.add_theme_font_size_override("font_size", fit_size(b.get_theme_font("font"), b.text, size, fit_w))
	b.resized.connect(func(): b.pivot_offset = b.size / 2)
	var on: Callable = def.get("on", Callable())

	if def.has("choice"):
		b.set_meta("ui_choice", String(def.choice))
		_set_chosen(b, def.get("chosen", false))

	# Lock-outs that the per-frame job combines: a delay, a one-press, a check.
	var gate := {"ready_at": 0.0, "spent": false}
	if def.has("delay"):
		gate.ready_at = Anim.now() + float(def.delay)
		var fill := ColorRect.new()
		fill.color = Color(1, 1, 1, 0.25)
		fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
		fill.position = Vector2(4, 4)
		b.add_child(fill)
		var total := float(def.delay)
		jobs.append(func():
			if not is_instance_valid(fill):
				return
			var left: float = float(gate.ready_at) - Anim.now()
			fill.visible = left > 0.0
			fill.size = Vector2((b.size.x - 8) * clampf(1.0 - left / total, 0.0, 1.0), b.size.y - 18))
	var enabled = def.get("enabled")
	if def.has("delay") or def.has("once") or enabled is Callable:
		var check := func():
			if not is_instance_valid(b):
				return
			var ok: bool = Anim.now() >= float(gate.ready_at) and not gate.spent
			if ok and enabled is Callable:
				ok = bool(enabled.call())
			b.disabled = not ok
		check.call()
		jobs.append(check)

	if def.has("hold"):
		_make_hold(b, float(def.hold), on)
	else:
		b.pressed.connect(func():
			if def.get("once", false):
				gate.spent = true
				b.disabled = true
			if b.has_meta("ui_choice"):
				_choose(b)
			if feedback.is_valid():
				feedback.call("press", b)
			if on.is_valid():
				on.call())
	if def.has("tooltip"):
		attach_tooltip(b, def.tooltip)
	return b


## Press and hold to fire; a fill bar shows progress.
static func _make_hold(b: Button, hold: float, on: Callable) -> void:
	b.set_meta("hold", true)
	var fill := ColorRect.new()
	fill.color = Color(1, 1, 1, 0.3)
	fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fill.position = Vector2(4, 4)
	fill.size = Vector2(0, maxf(b.custom_minimum_size.y - 14, 0))
	b.add_child(fill)
	var state := {"tw": null}
	b.button_down.connect(func():
		if feedback.is_valid():
			feedback.call("hold_start", b)
		var tw := b.create_tween()
		state.tw = tw
		tw.tween_property(fill, "size:x", b.size.x - 8, hold)
		tw.tween_callback(func():
			if feedback.is_valid():
				feedback.call("hold_done", b)
			if on.is_valid():
				on.call()))
	b.button_up.connect(func():
		if state.tw != null and state.tw.is_valid():
			state.tw.kill()
		fill.size.x = 0)


static func _set_chosen(b: Button, on: bool) -> void:
	b.set_meta("ui_chosen", on)
	var marker: Polygon2D = b.get_node_or_null("ChosenMarker")
	if on and marker == null:
		marker = Polygon2D.new()
		marker.name = "ChosenMarker"
		marker.polygon = PackedVector2Array([Vector2(-10, 0), Vector2(10, 0), Vector2(0, 12)])
		marker.color = CHOSEN_COLOR
		b.add_child(marker)
		var place := func(): marker.position = Vector2(b.size.x / 2, -16)
		place.call()
		b.resized.connect(place)
	if marker != null:
		marker.visible = on


## Select `b` and clear every other button in its choice group on the same screen.
static func _choose(b: Button) -> void:
	var name: String = b.get_meta("ui_choice")
	var top: Node = b
	while top.get_parent() != null and not (top.get_parent() is Window):
		top = top.get_parent()
	for other in _choice_members(top, name):
		_set_chosen(other, other == b)


static func _choice_members(n: Node, name: String, into: Array = []) -> Array:
	if n is Button and n.get_meta("ui_choice", "") == name:
		into.append(n)
	for c in n.get_children():
		_choice_members(c, name, into)
	return into


# ---------------------------------------------------------------- bars

static func _bar(def: Dictionary, jobs: Array) -> Control:
	var bar := Bar.new()
	bar.custom_minimum_size = def.get("min", Vector2(300, 18))
	bar.fill = def.get("fill", Color("2f8fe8"))
	bar.back = def.get("back", Color(0, 0, 0, 0.35))
	var src = def.bar[0]
	var key = def.bar[1]
	var mx := float(def.get("max", 1.0))
	var update := func():
		if is_instance_valid(bar):
			var v = _read(src, key)
			bar.set_ratio(clampf(float(v if v != null else 0.0) / maxf(mx, 0.0001), 0.0, 1.0))
	update.call()
	jobs.append(update)
	return bar


class Bar extends Control:
	var fill := Color.WHITE
	var back := Color.BLACK
	var ratio := 0.0

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func set_ratio(r: float) -> void:
		if not is_equal_approx(r, ratio):
			ratio = r
			queue_redraw()

	func _draw() -> void:
		draw_style_box(PixelBox.new(back, 2.0), Rect2(Vector2.ZERO, size))
		if ratio > 0.0:
			var w := maxf(size.x * ratio, minf(size.x, 12.0))
			draw_style_box(PixelBox.new(fill, 2.0), Rect2(Vector2.ZERO, Vector2(w, size.y)))


# ---------------------------------------------------------------- tooltips

## Show `tip` (String, Array of lines, or {"title", "lines"}) on mouse hover,
## and on press-and-hold for touch. `tip` may also be a Callable returning one
## of those, read each time the popup opens; an empty result shows nothing.
static func attach_tooltip(c: Control, tip, touch := true) -> void:
	var state := {"popup": null, "pressing": false}
	var show := func():
		if state.popup != null and is_instance_valid(state.popup):
			return
		var t = tip.call() if tip is Callable else tip
		if t == null or (t is String or t is Array or t is Dictionary) and t.is_empty():
			return
		state.popup = _tooltip_popup(c, t)
	var hide := func():
		if state.popup != null and is_instance_valid(state.popup):
			state.popup.queue_free()
		state.popup = null
	c.mouse_entered.connect(func():
		if not DisplayServer.is_touchscreen_available():
			show.call())
	c.mouse_exited.connect(hide)
	c.tree_exiting.connect(hide)
	c.gui_input.connect(func(e):
		if not (e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT):
			return
		state.pressing = e.pressed
		if not touch:
			hide.call()
		elif e.pressed:
			c.get_tree().create_timer(0.45).timeout.connect(func():
				if state.pressing and is_instance_valid(c):
					show.call())
		else:
			hide.call())


static func _tooltip_popup(c: Control, tip) -> Control:
	var title := ""
	var lines: Array = []
	if tip is String:
		lines = [tip]
	elif tip is Array or tip is PackedStringArray:
		lines = Array(tip)
	elif tip is Dictionary:
		title = str(tip.get("title", ""))
		var t = tip.get("lines", tip.get("text", []))
		lines = Array(t) if t is Array or t is PackedStringArray else [t]
	var rows: Array = []
	if title != "":
		rows.append({"text": title, "size": 22, "color": Color("2b2d42"), "shadow": Color.TRANSPARENT})
	for line in lines:
		rows.append({"text": str(line), "size": 18, "color": Color("4f6367"), "wrap": 320, "shadow": Color.TRANSPARENT})
	var p := build({"col": rows, "sep": 4, "panel": Color("f7f3ea"), "pad": 12, "outline": Color("2b2d42")})
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.top_level = true
	p.z_index = 950
	c.add_child(p)
	# place above the control (below it when it sits in the top half)
	var place := func():
		var r := c.get_global_rect()
		var vp := c.get_viewport_rect().size
		var above := r.get_center().y > vp.y * 0.5
		var pos := Vector2(r.get_center().x - p.size.x / 2, r.position.y - p.size.y - 10 if above else r.end.y + 10)
		pos.x = clampf(pos.x, 8, vp.x - p.size.x - 8)
		pos.y = clampf(pos.y, 8, vp.y - p.size.y - 8)
		p.global_position = pos
	p.resized.connect(place)
	place.call_deferred()
	return p


class Ticker extends Node:
	var jobs: Array = []

	func _process(_delta: float) -> void:
		for j in jobs:
			j.call()
