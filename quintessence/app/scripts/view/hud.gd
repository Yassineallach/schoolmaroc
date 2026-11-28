class_name Hud
extends Node2D
## Interface drawn above the candlelight: score row, top bar, buttons, panels.
## Main fills these fields from RunState and calls queue_redraw(). Buttons are hit-tested by Main.

const LIGHT_POS := Vector2(282, 500)
const GRAVITY_POS := Vector2(470, 492)
const INSIGHT_POS := Vector2(626, 500)

var buttons: Array = []         # {id, rect, label, enabled, accent, size}
var panel := ""                 # "", title, patron, intro, won, market, defeat, victory
var data := {}                  # panel-specific data
var top_left := ""
var coins := 0
var speed_label := "x1"
var show_score := false
var light := 0
var gravity := 0
var insight := 0
var target := 0
var reading_name := ""
var preview_line := ""
var hint := ""
var querent_name := ""
var querent_line := ""
var deck_count := 0
var gravity_bump := 0.0
var light_bump := 0.0
var time := 0.0


func _process(delta: float) -> void:
	time += delta
	gravity_bump = maxf(0.0, gravity_bump - delta * 4.0)
	light_bump = maxf(0.0, light_bump - delta * 4.0)
	queue_redraw()


func add_button(id: String, rect: Rect2, label: String, enabled := true, accent := false, size := 26) -> void:
	buttons.append({"id": id, "rect": rect, "label": label, "enabled": enabled, "accent": accent, "size": size})


func hit(p: Vector2) -> String:
	for b in buttons:
		if b["enabled"] and (b["rect"] as Rect2).grow(6).has_point(p):
			return b["id"]
	return ""


func _outline(pos: Vector2, s: String, size: int, col: Color, f: Font = null) -> void:
	var fo: Font = f if f != null else Art.font
	draw_string_outline(fo, Vector2(pos.x - 300, pos.y), s, HORIZONTAL_ALIGNMENT_CENTER, 600, size, 6, Color(0, 0, 0, 0.75))
	draw_string(fo, Vector2(pos.x - 300, pos.y), s, HORIZONTAL_ALIGNMENT_CENTER, 600, size, col)


func _draw() -> void:
	# Top bar.
	draw_rect(Rect2(0, 0, 720, 54), Color(0, 0, 0, 0.55))
	draw_line(Vector2(0, 54), Vector2(720, 54), Color(Art.GOLD, 0.35), 1.0)
	Art.text_left(self, Art.font_sc, Vector2(22, 36), top_left, 22, Color(Art.BONE, 0.85))
	if panel != "title":
		draw_circle(Vector2(520, 27), 13, Art.GOLD)
		draw_arc(Vector2(520, 27), 9, 0, TAU, 16, Color(Art.INK, 0.5), 1.5)
		Art.text_left(self, Art.font_num, Vector2(542, 37), str(coins), 26, Art.GOLD_HI)

	if querent_name != "" and panel == "":
		_outline(Vector2(150, 104), querent_name, 34, Art.BONE)
		draw_multiline_string(Art.font, Vector2(24, 132), querent_line, HORIZONTAL_ALIGNMENT_LEFT, 230, 18, -1, Color(Art.BONE, 0.62))

	if show_score:
		_outline(LIGHT_POS + Vector2(0, -50), "LIGHT", 18, Color(Art.GOLD, 0.85), Art.font_sc)
		var lk := 1.0 + light_bump * 0.18
		draw_set_transform(LIGHT_POS, 0.0, Vector2(lk, lk))
		_outline(Vector2(0, 18), str(light), 50, Art.GOLD_HI, Art.font_num)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		_outline(Vector2(376, 512), "x", 38, Color(Art.BONE, 0.7))
		# Gravity is ink on a paper slip.
		var gk := 1.0 + gravity_bump * 0.12
		draw_set_transform(GRAVITY_POS, -0.04, Vector2(gk, gk))
		var slip := Rect2(-54, -44, 108, 88)
		draw_rect(Rect2(slip.position + Vector2(4, 5), slip.size), Color(0, 0, 0, 0.5))
		Art.paper(self, slip.size, 3)
		draw_rect(slip.grow(-4), Color(Art.INK, 0.6), false, 1.2)
		Art.text(self, Art.font_sc, Vector2(0, -22), "GRAVITY", 15, Color(Art.INK, 0.75))
		Art.text(self, Art.font_num, Vector2(0, 28), str(gravity), 42, Art.INK)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		_outline(INSIGHT_POS + Vector2(0, -50), "INSIGHT", 18, Color(Art.BONE, 0.75), Art.font_sc)
		_outline(INSIGHT_POS + Vector2(0, 16), str(insight), 40, Art.BONE, Art.font_num)
		_outline(INSIGHT_POS + Vector2(0, 46), "of %d" % target, 20, Color(Art.BONE, 0.6))
		if reading_name != "":
			_outline(Vector2(360, 418) + Vector2(0, 0), reading_name, 24, Color(Art.GOLD_HI, 0.9), Art.font_sc)
		if preview_line != "":
			_outline(Vector2(360, 924), preview_line, 24, Color(Art.BONE, 0.92))
		elif hint != "":
			_outline(Vector2(360, 924), hint, 21, Color(Art.BONE, 0.62))
		_outline(Vector2(660, 1036), "deck %d" % deck_count, 16, Color(Art.BONE, 0.45))

	match panel:
		"title": _title()
		"patron": _patron()
		"intro": _intro()
		"won": _won()
		"market": _market()
		"defeat", "victory": _ending()

	for b in buttons:
		Art.tag(self, b["rect"], b["label"], b["enabled"], b["accent"], b["size"])


func _title() -> void:
	var y := 380.0 + sin(time * 0.8) * 3.0
	_outline(Vector2(360, y), "Quintessence", 92, Art.BONE)
	draw_line(Vector2(170, y + 26), Vector2(550, y + 26), Color(Art.GOLD, 0.8), 2.0)
	_outline(Vector2(360, y + 70), "a tarot reading, by candlelight", 28, Color(Art.BONE, 0.7))
	_outline(Vector2(360, 1236), "Cycle I slice · v0.1", 18, Color(Art.BONE, 0.4))


func _panel_bg() -> Rect2:
	var r := Rect2(36, 92, 648, 1120)
	Art.parchment(self, r, 77)
	return r


func _patron() -> void:
	var r := _panel_bg()
	Art.text(self, Art.font, Vector2(360, r.position.y + 78), "Choose your Patron Arcana", 40, Art.INK)
	Art.text(self, Art.font, Vector2(360, r.position.y + 116), "It sits in your first Arcana slot.", 22, Color(Art.INK, 0.7))
	var offers: Array = data.get("offers", [])
	for i in offers.size():
		var y := 340.0 + i * 300.0
		var id: String = offers[i]
		draw_set_transform(Vector2(170, y), 0.0, Vector2(0.86, 0.86))
		Art.major_card(self, CardView.SIZE, id, i == int(data.get("pick", -1)))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		Art.text_left(self, Art.font, Vector2(270, y - 60), ArcanaDB.name_of(id), 34, Art.INK)
		draw_multiline_string(Art.font, Vector2(270, y - 22), ArcanaDB.text_of(id), HORIZONTAL_ALIGNMENT_LEFT, 380, 22, -1, Color(Art.INK, 0.85))


func _intro() -> void:
	var r := _panel_bg()
	var cx := 360.0
	Art.text(self, Art.font_sc, Vector2(cx, r.position.y + 90), data.get("label", ""), 24, Color(Art.INK, 0.6))
	Art.text(self, Art.font, Vector2(cx, r.position.y + 160), data.get("name", ""), 60, Art.INK)
	draw_line(Vector2(200, r.position.y + 186), Vector2(520, r.position.y + 186), Art.VERMILION, 2.0)
	draw_multiline_string(Art.font, Vector2(96, r.position.y + 240), data.get("line", ""), HORIZONTAL_ALIGNMENT_CENTER, 528, 28, -1, Color(Art.INK, 0.85))
	Art.text(self, Art.font_sc, Vector2(cx, r.position.y + 430), "INSIGHT NEEDED", 22, Color(Art.INK, 0.6))
	Art.wax_seal(self, Vector2(cx, r.position.y + 520), 70, str(data.get("target", 0)), 5)
	var y := r.position.y + 650
	for line in data.get("notes", []):
		draw_multiline_string(Art.font, Vector2(96, y), line, HORIZONTAL_ALIGNMENT_CENTER, 528, 23, -1, Color(Art.INK, 0.8))
		y += 74


func _won() -> void:
	var r := _panel_bg()
	Art.text(self, Art.font, Vector2(360, r.position.y + 120), data.get("title", "The Querent is satisfied"), 42, Art.INK)
	Art.wax_seal(self, Vector2(360, r.position.y + 270), 74, str(data.get("insight", 0)), 9)
	var y := r.position.y + 420
	for row in data.get("rows", []):
		Art.text_left(self, Art.font, Vector2(140, y), row[0], 28, Art.INK)
		draw_string(Art.font, Vector2(380, y), row[1], HORIZONTAL_ALIGNMENT_RIGHT, 200, 28, Art.INK)
		y += 46
	draw_line(Vector2(140, y - 26), Vector2(580, y - 26), Color(Art.INK, 0.5), 1.0)
	Art.text_left(self, Art.font, Vector2(140, y + 14), "Coins", 32, Art.INK)
	draw_string(Art.font, Vector2(380, y + 14), "+%d" % int(data.get("total", 0)), HORIZONTAL_ALIGNMENT_RIGHT, 200, 32, Color("#8A6A10"))


func _market() -> void:
	var r := _panel_bg()
	Art.text(self, Art.font, Vector2(360, r.position.y + 70), "The Market", 46, Art.INK)
	Art.text(self, Art.font, Vector2(360, r.position.y + 104), "Tap an item to buy it.", 20, Color(Art.INK, 0.65))
	var items: Array = data.get("items", [])
	for it in items:
		var pos: Vector2 = it["pos"]
		var sc: float = it["scale"]
		var sold: bool = it["sold"]
		draw_set_transform(pos, 0.0, Vector2(sc, sc))
		match it["kind"]:
			"major":
				Art.major_card(self, CardView.SIZE, it["id"])
			"minor":
				Art.minor_card(self, CardView.SIZE, it["card"], Transform2D(0.0, Vector2(sc, sc), 0.0, pos))
			"sigil":
				Art.paper(self, Vector2(170, 210), 12)
				draw_rect(Rect2(-85, -105, 170, 210).grow(-6), Art.INK, false, 1.5)
				Art.text(self, Art.font_sc, Vector2(0, -62), "SIGIL", 26, Art.VERMILION)
				Art.text(self, Art.font, Vector2(0, -16), Readings.DEFS[it["id"]]["name"], 30, Art.INK)
				Art.text(self, Art.font, Vector2(0, 24), "level %d" % (int(it["level"]) + 1), 24, Color(Art.INK, 0.75))
				var nv := Readings.base_values(it["id"], int(it["level"]) + 1)
				Art.text(self, Art.font, Vector2(0, 62), "%d Light · %d Gravity" % [nv.x, nv.y], 19, Color(Art.INK, 0.75))
		if sold:
			draw_rect(Rect2(-CardView.SIZE / 2.0, CardView.SIZE).grow(6), Color(Art.BONE, 0.78))
			Art.text(self, Art.font_sc, Vector2(0, 10), "SOLD", 40, Art.VERMILION)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		if it.has("caption"):
			draw_multiline_string(Art.font, pos + Vector2(-148, it["caption_y"]), it["caption"], HORIZONTAL_ALIGNMENT_CENTER, 296, 18, -1, Color(Art.INK, 0.85))
	Art.text_left(self, Art.font_sc, Vector2(76, 874), "YOUR ARCANA", 20, Color(Art.INK, 0.6))
	var owned: Array = data.get("owned", [])
	for i in owned.size():
		draw_set_transform(Vector2(116 + i * 120, 940), 0.0, Vector2(0.42, 0.42))
		Art.major_card(self, CardView.SIZE, owned[i])
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _ending() -> void:
	var r := _panel_bg()
	var won := panel == "victory"
	Art.text(self, Art.font, Vector2(360, r.position.y + 130), "Cycle I complete" if won else "The candle gutters out", 48, Art.INK)
	draw_multiline_string(Art.font, Vector2(96, r.position.y + 190), data.get("line", ""), HORIZONTAL_ALIGNMENT_CENTER, 528, 26, -1, Color(Art.INK, 0.8))
	var y := r.position.y + 380
	for row in data.get("rows", []):
		Art.text_left(self, Art.font, Vector2(120, y), row[0], 28, Art.INK)
		draw_string(Art.font, Vector2(330, y), row[1], HORIZONTAL_ALIGNMENT_RIGHT, 270, 28, Art.INK)
		y += 50
	if won:
		Art.wax_seal(self, Vector2(360, r.position.y + 800), 80, "I", 3)
