class_name Art
extends RefCounted
## Procedural woodcut-style drawing on bone paper. All colors are the style contract roles.

const BONE := Color("#EDE3CF")
const BONE_SHADE := Color("#D9CCB0")
const INK := Color("#15110E")
const GOLD := Color("#C9A227")
const GOLD_HI := Color("#F1D77A")
const VERMILION := Color("#C8341E")
const PRUSSIAN := Color("#1F3A5F")
const CHALK := Color(0.93, 0.89, 0.8, 0.42)
const CLOTH := Color("#2A1C16")

static var font: Font
static var font_sc: Font
static var font_pica: Font
static var font_num: Font


static func text(ci: CanvasItem, f: Font, center: Vector2, s: String, size: int, col: Color) -> void:
	ci.draw_string(f, Vector2(center.x - 500.0, center.y), s, HORIZONTAL_ALIGNMENT_CENTER, 1000.0, size, col)


static func text_left(ci: CanvasItem, f: Font, pos: Vector2, s: String, size: int, col: Color, width := -1.0) -> void:
	ci.draw_string(f, pos, s, HORIZONTAL_ALIGNMENT_LEFT, width, size, col)


static func text_wrapped(ci: CanvasItem, f: Font, pos: Vector2, s: String, size: int, col: Color, width: float, align := HORIZONTAL_ALIGNMENT_CENTER) -> void:
	ci.draw_multiline_string(f, pos, s, align, width, size, -1, col)


static func ellipse(c: Vector2, rx: float, ry: float, rot := 0.0, n := 20) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in n:
		var a := TAU * i / n
		pts.append(c + Vector2(cos(a) * rx, sin(a) * ry).rotated(rot))
	return pts


static func paper(ci: CanvasItem, size: Vector2, seed: int, tint := BONE) -> void:
	var r := Rect2(-size / 2.0, size)
	ci.draw_rect(r, tint)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed * 7919 + 17
	for i in 38:
		var p := Vector2(rng.randf_range(-0.47, 0.47) * size.x, rng.randf_range(-0.47, 0.47) * size.y)
		ci.draw_circle(p, rng.randf_range(0.6, 1.6), Color(INK, 0.07))
	for i in 7:
		var p := Vector2(rng.randf_range(-0.45, 0.45) * size.x, rng.randf_range(-0.45, 0.45) * size.y)
		var d := Vector2.from_angle(rng.randf() * TAU) * rng.randf_range(4.0, 11.0)
		ci.draw_line(p, p + d, Color(INK, 0.08), 0.8)
	# Foxing toward the edges.
	ci.draw_rect(r.grow(-2.0), Color(0.55, 0.42, 0.25, 0.14), false, 4.0)


static func frame(ci: CanvasItem, size: Vector2, col := INK) -> void:
	var r := Rect2(-size / 2.0, size)
	ci.draw_rect(r.grow(-1.5), col, false, 3.0)
	var inner := r.grow(-size.x * 0.06)
	ci.draw_rect(inner, col, false, 1.2)
	for corner in [inner.position, Vector2(inner.end.x, inner.position.y), inner.end, Vector2(inner.position.x, inner.end.y)]:
		var k := 4.0
		ci.draw_colored_polygon(PackedVector2Array([corner + Vector2(0, -k), corner + Vector2(k, 0), corner + Vector2(0, k), corner + Vector2(-k, 0)]), col)


## Engraved arch window: horizontal hatch lines whose extent follows an arch outline.
static func arch(ci: CanvasItem, center: Vector2, w: float, h: float, col := INK) -> void:
	var r := w / 2.0
	var top := center.y - h / 2.0
	var circle_c := Vector2(center.x, top + r)
	var y := top + 2.0
	var i := 0
	while y < center.y + h / 2.0:
		var half := r
		if y < circle_c.y:
			var dy := circle_c.y - y
			half = sqrt(maxf(0.0, r * r - dy * dy))
		var thick := 0.7 + 0.5 * float(i % 3 == 0)
		ci.draw_line(Vector2(center.x - half, y), Vector2(center.x + half, y), Color(col, 0.28), thick)
		y += 3.4
		i += 1
	var outline := PackedVector2Array()
	outline.append(Vector2(center.x - r, center.y + h / 2.0))
	for k in 17:
		var a := PI + PI * k / 16.0
		outline.append(circle_c + Vector2(cos(a), sin(a)) * r)
	outline.append(Vector2(center.x + r, center.y + h / 2.0))
	ci.draw_polyline(outline, col, 1.6)
	ci.draw_line(Vector2(center.x - r - 4, center.y + h / 2.0), Vector2(center.x + r + 4, center.y + h / 2.0), col, 2.0)


# ---------- Suit emblems (bone halo behind ink, like a cut block) ----------

static func suit_emblem(ci: CanvasItem, c: Vector2, s: float, suit: int, col := INK) -> void:
	for pass_i in 2:
		var ink := BONE if pass_i == 0 else col
		var grow := 3.0 if pass_i == 0 else 0.0
		match suit:
			0: _wand(ci, c, s, ink, grow)
			1: _cup(ci, c, s, ink, grow)
			2: _sword(ci, c, s, ink, grow)
			3: _pentacle(ci, c, s, ink, grow)


static func _wand(ci: CanvasItem, c: Vector2, s: float, col: Color, g: float) -> void:
	var a := c + Vector2(-0.28, 0.46) * s
	var b := c + Vector2(0.28, -0.46) * s
	ci.draw_line(a, b, col, s * 0.11 + g * 2.0)
	ci.draw_circle(b, s * 0.07 + g, col)
	ci.draw_circle(a, s * 0.06 + g, col)
	var dir := (b - a).normalized()
	var nrm := Vector2(-dir.y, dir.x)
	for t in [0.3, 0.55, 0.78]:
		var p := a.lerp(b, t)
		var side := 1.0 if t != 0.55 else -1.0
		ci.draw_colored_polygon(ellipse(p + nrm * side * s * 0.13, s * 0.11 + g, s * 0.045 + g, nrm.angle() + 0.5 * side, 12), col)


static func _cup(ci: CanvasItem, c: Vector2, s: float, col: Color, g: float) -> void:
	var bowl := PackedVector2Array()
	var top := c.y - s * 0.32
	var rw := s * 0.34 + g
	bowl.append(Vector2(c.x - rw, top - g))
	for k in 13:
		var a := PI * k / 12.0
		bowl.append(Vector2(c.x - cos(a) * rw, top + sin(a) * s * 0.36 + g))
	bowl.append(Vector2(c.x + rw, top - g))
	ci.draw_colored_polygon(bowl, col)
	ci.draw_rect(Rect2(c.x - s * 0.05 - g, c.y + s * 0.02, s * 0.1 + g * 2, s * 0.3), col)
	ci.draw_colored_polygon(PackedVector2Array([
		Vector2(c.x - s * 0.24 - g, c.y + s * 0.45 + g), Vector2(c.x + s * 0.24 + g, c.y + s * 0.45 + g),
		Vector2(c.x + s * 0.08 + g, c.y + s * 0.3 - g), Vector2(c.x - s * 0.08 - g, c.y + s * 0.3 - g)]), col)
	if g == 0.0:
		ci.draw_line(Vector2(c.x - rw * 0.8, top + s * 0.06), Vector2(c.x + rw * 0.8, top + s * 0.06), BONE, 1.4)


static func _sword(ci: CanvasItem, c: Vector2, s: float, col: Color, g: float) -> void:
	ci.draw_colored_polygon(PackedVector2Array([
		Vector2(c.x, c.y - s * 0.5 - g), Vector2(c.x + s * 0.07 + g, c.y - s * 0.38),
		Vector2(c.x + s * 0.07 + g, c.y + s * 0.18), Vector2(c.x - s * 0.07 - g, c.y + s * 0.18),
		Vector2(c.x - s * 0.07 - g, c.y - s * 0.38)]), col)
	ci.draw_rect(Rect2(c.x - s * 0.26 - g, c.y + s * 0.16 - g, s * 0.52 + 2 * g, s * 0.07 + 2 * g), col)
	ci.draw_rect(Rect2(c.x - s * 0.04 - g, c.y + s * 0.22, s * 0.08 + 2 * g, s * 0.18), col)
	ci.draw_circle(Vector2(c.x, c.y + s * 0.44), s * 0.06 + g, col)
	if g == 0.0:
		ci.draw_line(Vector2(c.x, c.y - s * 0.4), Vector2(c.x, c.y + s * 0.12), BONE, 1.2)


static func _pentacle(ci: CanvasItem, c: Vector2, s: float, col: Color, g: float) -> void:
	var r := s * 0.42
	ci.draw_arc(c, r, 0, TAU, 40, col, s * 0.07 + g * 2.0)
	var star := PackedVector2Array()
	for k in 6:
		var a := -PI / 2.0 + TAU * ((k * 2) % 5) / 5.0
		star.append(c + Vector2(cos(a), sin(a)) * r * 0.82)
	ci.draw_polyline(star, col, s * 0.045 + g * 2.0)


# ---------- Major Arcana emblems ----------

static func major_emblem(ci: CanvasItem, c: Vector2, s: float, id: String, col := INK, accent := GOLD) -> void:
	match id:
		"magician":
			var pts := PackedVector2Array()
			for k in 49:
				var t := TAU * k / 48.0
				var d := 1.0 + sin(t) * sin(t)
				pts.append(c + Vector2(cos(t) / d, sin(t) * cos(t) / d) * s * 0.42)
			ci.draw_polyline(pts, col, s * 0.07)
			ci.draw_line(c + Vector2(0, s * 0.15), c + Vector2(0, s * 0.48), col, s * 0.06)
			ci.draw_circle(c + Vector2(0, s * 0.12), s * 0.05, accent)
		"empress":
			ci.draw_arc(c + Vector2(0, -s * 0.12), s * 0.24, 0, TAU, 32, col, s * 0.07)
			ci.draw_line(c + Vector2(0, s * 0.12), c + Vector2(0, s * 0.5), col, s * 0.07)
			ci.draw_line(c + Vector2(-s * 0.16, s * 0.32), c + Vector2(s * 0.16, s * 0.32), col, s * 0.07)
			_crown(ci, c + Vector2(0, -s * 0.44), s * 0.36, accent)
		"lovers":
			ci.draw_arc(c + Vector2(-s * 0.14, 0), s * 0.26, 0, TAU, 32, col, s * 0.06)
			ci.draw_arc(c + Vector2(s * 0.14, 0), s * 0.26, 0, TAU, 32, col, s * 0.06)
			ci.draw_circle(c, s * 0.07, accent)
		"hermit":
			ci.draw_line(c + Vector2(-s * 0.3, -s * 0.5), c + Vector2(-s * 0.3, s * 0.5), col, s * 0.05)
			var lan := PackedVector2Array([c + Vector2(-s * 0.12, -s * 0.16), c + Vector2(s * 0.24, -s * 0.16),
				c + Vector2(s * 0.3, s * 0.06), c + Vector2(s * 0.24, s * 0.28), c + Vector2(-s * 0.12, s * 0.28), c + Vector2(-s * 0.18, s * 0.06)])
			ci.draw_colored_polygon(lan, col)
			_star(ci, c + Vector2(s * 0.06, s * 0.06), s * 0.12, 6, accent)
			ci.draw_arc(c + Vector2(s * 0.06, -s * 0.24), s * 0.08, 0, TAU, 16, col, s * 0.04)
		"death":
			ci.draw_line(c + Vector2(-s * 0.1, s * 0.5), c + Vector2(s * 0.12, -s * 0.48), col, s * 0.06)
			var blade := PackedVector2Array()
			for k in 13:
				var a := PI * 1.05 + PI * 0.75 * k / 12.0
				blade.append(c + Vector2(s * 0.12, -s * 0.48) + Vector2(cos(a) * s * 0.5, sin(a) * s * 0.22 + s * 0.2))
			ci.draw_polyline(blade, col, s * 0.07)
			ci.draw_circle(c + Vector2(s * 0.24, s * 0.2), s * 0.12, col)
			ci.draw_circle(c + Vector2(s * 0.2, s * 0.18), s * 0.03, BONE)
			ci.draw_circle(c + Vector2(s * 0.28, s * 0.18), s * 0.03, BONE)
		"tower":
			ci.draw_rect(Rect2(c.x - s * 0.18, c.y - s * 0.3, s * 0.36, s * 0.8), col)
			for k in 3:
				ci.draw_rect(Rect2(c.x - s * 0.18 + k * s * 0.13, c.y - s * 0.4, s * 0.1, s * 0.12), col)
			ci.draw_rect(Rect2(c.x - s * 0.05, c.y + s * 0.3, s * 0.1, s * 0.2), BONE)
			ci.draw_polyline(PackedVector2Array([c + Vector2(s * 0.42, -s * 0.52), c + Vector2(s * 0.2, -s * 0.2),
				c + Vector2(s * 0.32, -s * 0.18), c + Vector2(s * 0.1, s * 0.12)]), accent, s * 0.05)
		"star":
			_star(ci, c, s * 0.42, 8, accent)
			_star_outline(ci, c, s * 0.42, 8, col, s * 0.025)
			_star(ci, c + Vector2(-s * 0.4, -s * 0.38), s * 0.08, 8, col)
			_star(ci, c + Vector2(s * 0.38, s * 0.36), s * 0.08, 8, col)
		"sun":
			for k in 12:
				var a := TAU * k / 12.0
				var dir := Vector2(cos(a), sin(a))
				var nrm := Vector2(-dir.y, dir.x)
				ci.draw_colored_polygon(PackedVector2Array([c + dir * s * 0.3 + nrm * s * 0.06,
					c + dir * s * 0.5, c + dir * s * 0.3 - nrm * s * 0.06]), col)
			ci.draw_circle(c, s * 0.26, accent)
			ci.draw_arc(c, s * 0.26, 0, TAU, 32, col, s * 0.04)
		_:
			ci.draw_arc(c, s * 0.3, 0, TAU, 24, col, s * 0.05)


static func _crown(ci: CanvasItem, c: Vector2, w: float, col: Color) -> void:
	var h := w * 0.5
	ci.draw_colored_polygon(PackedVector2Array([c + Vector2(-w / 2, h / 2), c + Vector2(w / 2, h / 2),
		c + Vector2(w / 2, -h / 2), c + Vector2(w / 4, 0), c + Vector2(0, -h / 2), c + Vector2(-w / 4, 0),
		c + Vector2(-w / 2, -h / 2)]), col)


static func _star_pts(c: Vector2, r: float, points: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for k in points * 2:
		var a := -PI / 2.0 + PI * k / points
		var rr := r if k % 2 == 0 else r * 0.42
		pts.append(c + Vector2(cos(a), sin(a)) * rr)
	return pts


static func _star(ci: CanvasItem, c: Vector2, r: float, points: int, col: Color) -> void:
	ci.draw_colored_polygon(_star_pts(c, r, points), col)


static func _star_outline(ci: CanvasItem, c: Vector2, r: float, points: int, col: Color, w: float) -> void:
	var pts := _star_pts(c, r, points)
	pts.append(pts[0])
	ci.draw_polyline(pts, col, w)


# ---------- Whole cards ----------

static func minor_card(ci: CanvasItem, size: Vector2, card: Dictionary, xf := Transform2D.IDENTITY) -> void:
	var suit := int(card["suit"])
	var rank := int(card["rank"])
	paper(ci, size, int(card["id"]) + suit * 31 + rank)
	frame(ci, size)
	var w := size.x
	var h := size.y
	arch(ci, Vector2(0, h * 0.02), w * 0.66, h * 0.58)
	var es := w * 0.5
	if rank >= 11:
		suit_emblem(ci, Vector2(0, h * 0.06), es * 0.86, suit)
		_court_mark(ci, Vector2(0, -h * 0.2), w * 0.22, rank)
	else:
		suit_emblem(ci, Vector2(0, h * 0.04), es, suit)
	var label := Cards.corner_label(rank)
	var fs := int(w * 0.17)
	text_left(ci, font, Vector2(-w / 2 + w * 0.1, -h / 2 + h * 0.13), label, fs, INK)
	ci.draw_set_transform_matrix(xf * Transform2D(PI, Vector2.ZERO))
	text_left(ci, font, Vector2(-w / 2 + w * 0.1, -h / 2 + h * 0.13), label, fs, INK)
	ci.draw_set_transform_matrix(xf)
	# Light value as a small gold-leaf seal in the top-right.
	var lp := Vector2(w / 2 - w * 0.17, -h / 2 + h * 0.1)
	ci.draw_circle(lp, w * 0.085, GOLD)
	ci.draw_arc(lp, w * 0.085, 0, TAU, 20, Color(INK, 0.6), 1.0)
	text(ci, font_num, lp + Vector2(0, w * 0.037), str(rank), int(w * 0.095), INK)
	text(ci, font_sc, Vector2(0, h / 2 - h * 0.12), "of " + Cards.SUIT_NAMES[suit].to_lower(), int(w * 0.1), INK)


static func _court_mark(ci: CanvasItem, c: Vector2, w: float, rank: int) -> void:
	for pass_i in 2:
		var col := BONE if pass_i == 0 else INK
		var g := 2.5 if pass_i == 0 else 0.0
		match rank:
			11:
				ci.draw_colored_polygon(ellipse(c, w * 0.12 + g, w * 0.36 + g, 0.6, 14), col)
			12:
				ci.draw_arc(c + Vector2(0, w * 0.1), w * 0.3 + g, PI, TAU, 16, col, w * 0.14 + g)
				ci.draw_line(c + Vector2(-w * 0.2, w * 0.1), c + Vector2(w * 0.2, w * 0.1), col, 3.0 + g)
			_:
				var cw := w * (0.8 if rank == 14 else 0.62)
				var h := cw * 0.5
				ci.draw_colored_polygon(PackedVector2Array([c + Vector2(-cw / 2 - g, h / 2 + g), c + Vector2(cw / 2 + g, h / 2 + g),
					c + Vector2(cw / 2 + g, -h / 2 - g), c + Vector2(cw / 4, 0), c + Vector2(0, -h / 2 - g), c + Vector2(-cw / 4, 0),
					c + Vector2(-cw / 2 - g, -h / 2 - g)]), col)


static func major_card(ci: CanvasItem, size: Vector2, id: String, lit := false) -> void:
	var n := ArcanaDB.num_of(id)
	paper(ci, size, 500 + n)
	frame(ci, size, GOLD if lit else INK)
	var w := size.x
	var h := size.y
	arch(ci, Vector2(0, h * 0.03), w * 0.66, h * 0.56)
	major_emblem(ci, Vector2(0, h * 0.06), w * 0.56, id)
	text(ci, font, Vector2(0, -h / 2 + h * 0.15), Cards.ROMAN[n], int(w * 0.16), INK)
	var name := ArcanaDB.name_of(id).replace("The ", "")
	text(ci, font_sc, Vector2(0, h / 2 - h * 0.09), name, int(w * (0.15 if name.length() < 8 else 0.12)), INK)


static func card_back(ci: CanvasItem, size: Vector2) -> void:
	ci.draw_rect(Rect2(-size / 2.0, size), Color("#3A1E18"))
	frame(ci, size, GOLD)
	_star(ci, Vector2.ZERO, size.x * 0.22, 8, GOLD)
	ci.draw_arc(Vector2.ZERO, size.x * 0.32, 0, TAU, 32, Color(GOLD, 0.6), 1.5)


## Irregular wax seal with a number pressed into it.
static func wax_seal(ci: CanvasItem, c: Vector2, r: float, value: String, seed: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var pts := PackedVector2Array()
	for k in 28:
		var a := TAU * k / 28.0
		pts.append(c + Vector2(cos(a), sin(a)) * r * rng.randf_range(0.92, 1.08))
	ci.draw_colored_polygon(pts, VERMILION)
	ci.draw_arc(c, r * 0.78, 0, TAU, 32, Color(0.55, 0.1, 0.05, 0.9), 2.0)
	ci.draw_circle(c + Vector2(-r * 0.3, -r * 0.35), r * 0.16, Color(1, 0.7, 0.6, 0.25))
	var fs := int(r * (0.62 if value.length() <= 3 else 0.48))
	var f := font if value.is_valid_int() == false else font_num
	text(ci, f, c + Vector2(0, fs * 0.36), value, fs, Color("#F6E3C8"))


static func ink_blob(ci: CanvasItem, c: Vector2, r: float, seed: int, col: Color, t := 0.0) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var pts := PackedVector2Array()
	var phases: Array[float] = []
	for k in 5:
		phases.append(rng.randf() * TAU)
	for k in 36:
		var a := TAU * k / 36.0
		var wob := 0.0
		for j in 5:
			wob += sin(a * (j + 2) + phases[j] + t * (0.5 + j * 0.2)) * 0.06
		pts.append(c + Vector2(cos(a) * 0.7, sin(a)) * r * (1.0 + wob))
	ci.draw_colored_polygon(pts, col)


## Paper tag button.
static func tag(ci: CanvasItem, rect: Rect2, label: String, enabled := true, accent := false, size := 26) -> void:
	var paper_col := BONE if enabled else Color(BONE_SHADE, 0.45)
	ci.draw_rect(Rect2(rect.position + Vector2(3, 4), rect.size), Color(0, 0, 0, 0.45))
	ci.draw_rect(rect, paper_col)
	ci.draw_rect(rect.grow(-1.5), VERMILION if accent and enabled else INK, false, 2.5 if accent else 1.8)
	ci.draw_rect(rect.grow(-6), Color(INK, 0.35), false, 1.0)
	var ink := INK if enabled else Color(INK, 0.45)
	text(ci, font_sc, Vector2(rect.get_center().x, rect.get_center().y + size * 0.33), label, size, ink)


static func parchment(ci: CanvasItem, rect: Rect2, seed: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var pts := PackedVector2Array()
	var steps := 12
	for k in steps:
		pts.append(Vector2(rect.position.x + rect.size.x * k / steps, rect.position.y + rng.randf_range(-3, 3)))
	for k in steps:
		pts.append(Vector2(rect.end.x + rng.randf_range(-3, 3), rect.position.y + rect.size.y * k / steps))
	for k in steps:
		pts.append(Vector2(rect.end.x - rect.size.x * k / steps, rect.end.y + rng.randf_range(-3, 3)))
	for k in steps:
		pts.append(Vector2(rect.position.x + rng.randf_range(-3, 3), rect.end.y - rect.size.y * k / steps))
	var shadow := PackedVector2Array()
	for p in pts:
		shadow.append(p + Vector2(6, 8))
	ci.draw_colored_polygon(shadow, Color(0, 0, 0, 0.45))
	ci.draw_colored_polygon(pts, BONE)
	for i in 60:
		var p := Vector2(rng.randf_range(rect.position.x, rect.end.x), rng.randf_range(rect.position.y, rect.end.y))
		ci.draw_circle(p, rng.randf_range(0.6, 1.8), Color(INK, 0.05))
	ci.draw_rect(rect.grow(-10), Color(0.55, 0.42, 0.25, 0.12), false, 14.0)
	ci.draw_rect(rect.grow(-14), INK, false, 1.5)
