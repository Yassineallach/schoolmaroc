extends Node2D
## Scene controller: builds the table, routes touch input to RunState, animates results.
## RunState owns all game rules; this file only reads it and calls its public methods.

const SAVE_PATH := "user://run.json"
const SPREAD_CENTERS: Array[Vector2] = [Vector2(174, 722), Vector2(360, 722), Vector2(546, 722)]
const HAND_Y := 1150.0
const HAND_SCALE := 0.77
const ARCANA_Y := 362.0
const ARCANA_SCALE := 0.42
const CANDLE_BASE := Vector2(110, 566)
const LIGHT_ORIGIN := Vector2(110, 452)
const DECK_POS := Vector2(-110, 1150)
const DISCARD_POS := Vector2(840, 760)

var state := RunState.new()
var screen := "title"
var world: Node2D
var room: ColorRect
var dark: ColorRect
var dark_mat: ShaderMaterial
var querent: QuerentView
var table: TableView
var arcana_layer: Node2D
var cards_layer: Node2D
var candle: CandleView
var fx: FxView
var hud: Hud
var views := {}            # card id -> CardView
var arcana_views: Array = []
var zones: Array = []      # non-button tap areas {id, rect}
var busy := false
var speeds: Array[float] = [1.0, 2.0, 4.0, 0.0]
var speed_labels: Array[String] = ["x1", "x2", "x4", "skip"]
var speed_i := 0
var reshuffle_mode := false
var marked := {}
var press_view: CardView = null
var press_pos := Vector2.ZERO
var dragging := false
var shown_insight := 0.0
var flame_h := 0.5
var flame_override := -1.0
var gutter := 0.0
var flare := 0.0
var tooltip := ""
var tooltip_t := 0.0
var shadow_note := ""


func _ready() -> void:
	Art.font = load("res://assets/fonts/fell.woff2")
	Art.font_sc = load("res://assets/fonts/fell_sc.woff2")
	Art.font_pica = load("res://assets/fonts/pica.woff2")
	var num := FontVariation.new()
	num.base_font = load("res://assets/fonts/numbers.woff2")
	var ts := TextServerManager.get_primary_interface()
	num.opentype_features = {ts.name_to_tag("lnum"): 1}
	Art.font_num = num
	CardView.light_origin = LIGHT_ORIGIN
	get_tree().set_auto_accept_quit(false)
	_build()
	go_title()


func _build() -> void:
	world = Node2D.new()
	add_child(world)
	room = ColorRect.new()
	room.size = Vector2(720, 1280)
	room.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var rm := ShaderMaterial.new()
	rm.shader = load("res://shaders/room.gdshader")
	room.material = rm
	world.add_child(room)
	querent = QuerentView.new()
	world.add_child(querent)
	table = TableView.new()
	table.centers = SPREAD_CENTERS
	for i in ArcanaDB.MAX_SLOTS:
		table.arcana_centers.append(_arcana_pos(i))
	world.add_child(table)
	arcana_layer = Node2D.new()
	world.add_child(arcana_layer)
	cards_layer = Node2D.new()
	world.add_child(cards_layer)
	dark = ColorRect.new()
	dark.size = Vector2(720, 1280)
	dark.mouse_filter = Control.MOUSE_FILTER_IGNORE
	dark_mat = ShaderMaterial.new()
	dark_mat.shader = load("res://shaders/darkness.gdshader")
	dark_mat.set_shader_parameter("candle", LIGHT_ORIGIN)
	dark.material = dark_mat
	dark.z_index = 1000
	world.add_child(dark)
	var glow := CanvasLayer.new()
	glow.layer = 1
	add_child(glow)
	candle = CandleView.new()
	candle.position = CANDLE_BASE
	glow.add_child(candle)
	fx = FxView.new()
	glow.add_child(fx)
	var hud_layer := CanvasLayer.new()
	hud_layer.layer = 2
	add_child(hud_layer)
	hud = Hud.new()
	hud_layer.add_child(hud)


func _process(delta: float) -> void:
	var goal := 0.55
	if screen == "game" and state.phase in ["play", "won", "defeat"]:
		goal = clampf(shown_insight / maxf(1.0, float(state.target())), 0.0, 1.15)
	if flame_override >= 0.0:
		goal = flame_override
	flame_h = lerpf(flame_h, goal, 1.0 - exp(-delta * 3.0))
	candle.set_flame(flame_h, gutter, flare)
	dark_mat.set_shader_parameter("brightness", clampf(flame_h, 0.0, 1.1))
	dark_mat.set_shader_parameter("gutter", gutter)
	dark_mat.set_shader_parameter("flare", flare)
	hud.insight = int(round(shown_insight))
	if tooltip_t > 0.0:
		tooltip_t -= delta
		if tooltip_t <= 0.0:
			tooltip = ""
			_refresh_hint()


# ------------------------------------------------------------------ flow

func go_title() -> void:
	screen = "title"
	_cancel_press()
	refresh()


func start_new_run() -> void:
	_clear_views()
	fx.clear_all()
	state = RunState.new()
	state.new_run(int(Time.get_unix_time_from_system()) ^ Time.get_ticks_usec())
	screen = "game"
	reshuffle_mode = false
	marked = {}
	shown_insight = 0.0
	flame_override = -1.0
	querent.stand = 0.0
	save()
	refresh()


func continue_run() -> void:
	if not load_save():
		return
	_clear_views()
	fx.clear_all()
	screen = "game"
	reshuffle_mode = false
	marked = {}
	shown_insight = float(state.insight)
	flame_override = -1.0
	querent.stand = 0.0
	refresh()


func begin_night() -> void:
	if not state.start_night():
		return
	shown_insight = 0.0
	flame_override = -1.0
	querent.kind = state.night_info()["id"]
	querent.lean = 0.0
	querent.stand = 0.0
	shadow_note = ""
	save()
	refresh()


# ------------------------------------------------------------------ input

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_on_press(event.position)
		else:
			_on_release(event.position)
	elif event is InputEventMouseMotion and press_view != null:
		_on_move(event.position)


func _on_press(p: Vector2) -> void:
	var b := hud.hit(p)
	if busy:
		if b == "speed":
			_handle_button(b)
		return
	if b != "":
		_handle_button(b)
		return
	if screen != "game" or state.phase != "play":
		return
	for i in arcana_views.size():
		if (arcana_views[i] as CardView).contains(p):
			_on_arcana(i)
			return
	for pos in 3:
		var c = state.spread[pos]
		if c != null and views.has(int(c["id"])) and (views[int(c["id"])] as CardView).contains(p):
			if not reshuffle_mode:
				state.unplace(pos)
				save()
				refresh()
			return
	var hit_view: CardView = null
	for v in _hand_views_top_first():
		if v.contains(p):
			hit_view = v
			break
	if hit_view == null:
		return
	if reshuffle_mode:
		var id := hit_view.card_id()
		if marked.has(id):
			marked.erase(id)
		else:
			marked[id] = true
		refresh()
		return
	press_view = hit_view
	press_pos = p
	dragging = false


func _on_move(p: Vector2) -> void:
	if not dragging and p.distance_to(press_pos) > 14.0:
		dragging = true
		press_view.z_index = 200
		press_view.lift = 1.0
		var tw := create_tween()
		tw.tween_property(press_view, "scale", Vector2(0.9, 0.9), 0.08)
		press_view.rotation = 0.0
	if dragging:
		press_view.position = p
		table.hover = _slot_at(p)
		table.queue_redraw()


func _on_release(p: Vector2) -> void:
	if press_view == null:
		return
	var id := press_view.card_id()
	var placed := false
	if dragging:
		var slot := _slot_at(p)
		if slot >= 0:
			placed = state.place(id, slot)
	else:
		var slot := state.first_open_position()
		if slot >= 0:
			placed = state.place(id, slot)
	press_view.lift = 0.0
	_cancel_press()
	if placed:
		save()
	refresh()


func _cancel_press() -> void:
	press_view = null
	dragging = false
	if table:
		table.hover = -1
		table.queue_redraw()


func _slot_at(p: Vector2) -> int:
	var blocked := state.blocked_positions()
	for i in 3:
		if table.slot_rect(i).grow(30).has_point(p) and state.spread[i] == null and not blocked.has(i):
			return i
	return -1


func _on_arcana(i: int) -> void:
	var id: String = state.arcana[i]
	if id == "tower" and state.can_arm_tower():
		state.toggle_tower()
		_show_tooltip("The Tower is armed: the next Reading scores x5, then its cards burn." if state.tower_armed else "The Tower is at rest.")
		save()
		refresh()
		return
	_show_tooltip("%s: %s" % [ArcanaDB.name_of(id), ArcanaDB.text_of(id)])


func _show_tooltip(s: String) -> void:
	tooltip = s
	tooltip_t = 4.0
	_refresh_hint()


func _handle_button(id: String) -> void:
	var parts := id.split(":")
	match parts[0]:
		"new":
			start_new_run()
		"continue":
			continue_run()
		"title":
			go_title()
		"speed":
			speed_i = (speed_i + 1) % speeds.size()
			fx.speed = maxf(speeds[speed_i], 4.0) if speeds[speed_i] == 0.0 else speeds[speed_i]
			refresh_buttons_only()
		"patron":
			if state.choose_patron(int(parts[1])):
				save()
				refresh()
		"begin":
			begin_night()
		"read":
			do_read()
		"reshuffle":
			state.clear_spread()
			reshuffle_mode = true
			marked = {}
			refresh()
		"cancel":
			reshuffle_mode = false
			marked = {}
			refresh()
		"discard":
			do_reshuffle()
		"onward":
			if state.continue_after_win():
				if state.phase == "victory":
					_end_run()
				save()
				refresh()
		"buy":
			if state.buy(int(parts[1])):
				save()
				refresh()
		"sell":
			if state.sell_arcana(int(parts[1])):
				save()
				refresh()
		"reroll":
			if state.reroll():
				save()
				refresh()
		"leave":
			if state.leave_market():
				save()
				refresh()


func _notification(what: int) -> void:
	match what:
		NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_APPLICATION_FOCUS_OUT, NOTIFICATION_WM_WINDOW_FOCUS_OUT:
			if press_view != null:
				press_view.lift = 0.0
				_cancel_press()
				refresh()
			save()
		NOTIFICATION_WM_CLOSE_REQUEST:
			save()
			get_tree().quit()
		NOTIFICATION_WM_GO_BACK_REQUEST:
			if screen == "game" and not busy:
				save()
				go_title()
			elif screen == "title":
				get_tree().quit()


# ------------------------------------------------------------------ actions

func do_read() -> void:
	if busy or state.laid_count() == 0:
		return
	var spread_views: Array = [null, null, null]
	for p in 3:
		if state.spread[p] != null:
			spread_views[p] = views[int(state.spread[p]["id"])]
	var old_insight := float(state.insight)
	var res := state.read()
	if res.is_empty():
		return
	busy = true
	save()
	refresh_buttons_only()
	await _play_reading(res, spread_views, old_insight)
	busy = false
	if state.phase in ["defeat", "victory"]:
		_end_run()
	refresh()


func do_reshuffle() -> void:
	var ids: Array = marked.keys()
	if busy or not state.reshuffle(ids):
		return
	busy = true
	reshuffle_mode = false
	marked = {}
	save()
	for id in ids:
		if views.has(id):
			var v: CardView = views[id]
			v.marked = false
			var tw := create_tween().set_parallel()
			tw.tween_property(v, "position", DISCARD_POS, _d(0.3))
			tw.tween_property(v, "rotation", 0.6, _d(0.3))
	await wait(0.3)
	for id in ids:
		_free_view(id)
	busy = false
	refresh()


func _play_reading(res: Dictionary, sv: Array, old_insight: float) -> void:
	hud.preview_line = ""
	hud.hint = ""
	var steps: Array = res["steps"]
	var first: Dictionary = steps[0]
	var rname: String = Readings.DEFS[first["id"]]["name"]
	if int(first["level"]) > 1:
		rname += " " + Cards.ROMAN[int(first["level"])]
	hud.reading_name = ""
	hud.light = int(first["light_total"])
	hud.gravity = int(first["gravity_total"])
	hud.light_bump = 1.0
	hud.gravity_bump = 1.0
	fx.show_stamp(rname, Vector2(360, 588))
	await wait(0.6)
	for k in range(1, steps.size()):
		var st: Dictionary = steps[k]
		match st["kind"]:
			"card":
				var v: CardView = sv[int(st["pos"])]
				if v != null:
					var pulse := create_tween()
					pulse.tween_property(v, "scale", Vector2(1.07, 1.07), _d(0.1))
					pulse.tween_property(v, "scale", Vector2.ONE, _d(0.18))
					fx.gold_flakes(v.global_position, Hud.LIGHT_POS, 5 + mini(int(st["light"]), 14) / 2, _d(0.5))
				if int(st["pos"]) != 1:
					_underline(int(st["pos"]))
				var notes: Array = st["notes"]
				hud.preview_line = "+%d Light" % int(st["light"]) + ("   (%s)" % ", ".join(notes) if not notes.is_empty() else "")
				await wait(0.5)
				hud.light = int(st["light_total"])
				hud.light_bump = 1.0
				await wait(0.1)
			"position":
				_underline(1)
				fx.ink_drops(SPREAD_CENTERS[1] + Vector2(0, -60), Hud.GRAVITY_POS, 4, _d(0.55))
				hud.preview_line = "+%d Gravity   (Present)" % int(st["gravity"])
				await wait(0.6)
				hud.gravity = int(st["gravity_total"])
				hud.gravity_bump = 1.0
				await wait(0.1)
			"arcana":
				var slot := int(st["slot"])
				var av: CardView = arcana_views[slot] if slot < arcana_views.size() else null
				var id: String = st["id"]
				querent.puppet = id
				var pt := create_tween()
				pt.tween_property(querent, "puppet_alpha", 1.0, _d(0.25))
				pt.tween_interval(_d(0.5))
				pt.tween_property(querent, "puppet_alpha", 0.0, _d(0.4))
				if av != null:
					av.lit = true
					var tilt := create_tween()
					tilt.tween_property(av, "rotation", -0.22, _d(0.12))
					tilt.tween_property(av, "rotation", 0.0, _d(0.3))
					if int(st["light"]) > 0:
						fx.gold_flakes(av.global_position, Hud.LIGHT_POS, 6, _d(0.45))
					if int(st["gravity"]) > 0 or int(st["gravity_mult"]) > 1:
						fx.ink_drops(av.global_position, Hud.GRAVITY_POS, 3, _d(0.5))
				var bits: Array[String] = []
				if int(st["light"]) > 0:
					bits.append("+%d Light" % int(st["light"]))
				if int(st["gravity"]) > 0:
					bits.append("+%d Gravity" % int(st["gravity"]))
				if int(st["gravity_mult"]) > 1:
					bits.append("x%d Gravity" % int(st["gravity_mult"]))
				if int(st["insight_mult"]) > 1:
					bits.append("x%d Insight" % int(st["insight_mult"]))
				if id == "lovers":
					bits.append("Echo read as Triad")
				if id == "sun":
					bits.append("Present Light doubled")
				hud.preview_line = "%s: %s" % [ArcanaDB.name_of(id), ", ".join(bits)]
				await wait(0.6)
				hud.light = int(st["light_total"])
				hud.gravity = int(st["gravity_total"])
				hud.light_bump = 1.0
				hud.gravity_bump = 1.0
				if av != null:
					av.lit = id == "tower" and state.tower_armed
				await wait(0.1)
	var total := int(res["insight"])
	var mult := int(res["mult"])
	hud.preview_line = "%d x %d%s = %d Insight" % [int(res["light"]), int(res["gravity"]), " x%d" % mult if mult > 1 else "", total]
	fx.show_seal(total, Hud.INSIGHT_POS + Vector2(-6, -8))
	await wait(0.55)
	var tw := create_tween()
	tw.tween_property(self, "shown_insight", float(state.insight), _d(0.7)).from(old_insight)
	var lean := clampf(float(state.insight) / float(state.target()), 0.0, 1.0)
	create_tween().tween_property(querent, "lean", lean, _d(0.6))
	if total >= state.target():
		_flare(1.0, 1.6)
		fx.gold_storm(90)
		if total >= state.target() * 2:
			querent.puppet = "sun"
			querent.puppet_dance = 1.0
			var pt2 := create_tween()
			pt2.tween_property(querent, "puppet_alpha", 1.0, _d(0.3))
			pt2.tween_interval(_d(1.2))
			pt2.tween_property(querent, "puppet_alpha", 0.0, _d(0.5))
			pt2.tween_callback(func(): querent.puppet_dance = 0.0)
	await wait(0.8)

	# Cards leave the table.
	var ev: Dictionary = res["events"]
	for id in ev["destroyed"]:
		if views.has(id):
			create_tween().tween_property(views[id], "ash", 1.0, _d(0.6))
	for id in ev["to_discard"]:
		if views.has(id):
			var t2 := create_tween().set_parallel()
			t2.tween_property(views[id], "position", DISCARD_POS, _d(0.35))
			t2.tween_property(views[id], "rotation", 0.5, _d(0.35))
	await wait(0.6 if not (ev["destroyed"] as Array).is_empty() else 0.38)
	for id in ev["destroyed"]:
		_free_view(id)
	for id in ev["to_discard"]:
		_free_view(id)
	hud.preview_line = ""
	if int(ev["death_gain"]) > 0:
		_show_tooltip("Death takes your lowest card. +%d permanent Light." % int(ev["death_gain"]))

	if state.phase == "won":
		_flare(0.8, 1.2)
		await wait(1.0)
		return
	if state.phase == "defeat":
		flame_override = 0.0
		querent.stand = 0.0
		create_tween().tween_property(querent, "stand", 1.0, _d(1.2))
		var g := create_tween()
		g.tween_property(self, "gutter", 1.0, _d(0.4))
		g.tween_property(self, "gutter", 0.0, _d(1.2))
		await wait(1.6)
		return
	sync_cards(0.35)
	if ev["new_intent"] != null:
		var it: Dictionary = ev["new_intent"]
		shadow_note = "The Shadow stirs. On Reading %d it eclipses %s." % [int(it["apply_at"]), Scoring.POS_NAMES[int(it["pos"])]]
		var g := create_tween()
		g.tween_property(self, "gutter", 1.0, _d(0.25))
		g.tween_property(self, "gutter", 0.0, _d(1.0))
		var r := create_tween()
		r.tween_property(querent, "recoil", 1.0, _d(0.15))
		r.tween_property(querent, "recoil", 0.0, _d(0.6))
		await wait(0.4)
	var blocked := state.blocked_positions()
	for p in blocked:
		table.stain_grow[p] = 0.01
		_grow_stain(p)
	await wait(0.3)


func _grow_stain(p: int) -> void:
	var tw := create_tween()
	tw.tween_method(func(v: float): table.stain_grow[p] = v; table.queue_redraw(), 0.05, 1.0, _d(0.7))


func _underline(p: int) -> void:
	var tw := create_tween()
	tw.tween_method(func(v: float): table.underline[p] = v; table.queue_redraw(), 0.0, 1.0, _d(0.3))
	tw.tween_interval(_d(0.6))
	tw.tween_method(func(v: float): table.underline[p] = v; table.queue_redraw(), 1.0, 0.0, _d(0.2))


func _flare(amount: float, dur: float) -> void:
	var tw := create_tween()
	tw.tween_property(self, "flare", amount, _d(dur * 0.2))
	tw.tween_property(self, "flare", 0.0, _d(dur * 0.8))


func _end_run() -> void:
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_PATH))


func wait(t: float) -> void:
	var sp := speeds[speed_i]
	if sp <= 0.0:
		return
	await get_tree().create_timer(t / sp).timeout


func _d(t: float) -> float:
	var sp := speeds[speed_i]
	return 0.01 if sp <= 0.0 else t / sp


# ------------------------------------------------------------------ persistence

func save() -> void:
	if screen != "game" or state.phase in ["defeat", "victory"]:
		return
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f == null:
		return
	f.store_string(JSON.stringify(state.to_dict()))
	f.close()


func has_save() -> bool:
	if not FileAccess.file_exists(SAVE_PATH):
		return false
	var d = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
	if typeof(d) != TYPE_DICTIONARY:
		return false
	var s := RunState.new()
	return s.from_dict(d) and not (s.phase in ["defeat", "victory"])


func load_save() -> bool:
	if not has_save():
		return false
	var d = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
	var s := RunState.new()
	if not s.from_dict(d):
		return false
	state = s
	querent.kind = state.night_info()["id"]
	return true


# ------------------------------------------------------------------ view sync

func _arcana_pos(i: int) -> Vector2:
	return Vector2(360 + (i - 2) * 84, ARCANA_Y)


func display_hand() -> Array:
	var h: Array = state.hand.duplicate()
	h.sort_custom(func(a, b):
		if int(a["suit"]) != int(b["suit"]):
			return int(a["suit"]) < int(b["suit"])
		return int(a["rank"]) < int(b["rank"]))
	return h


func _hand_transform(i: int, n: int) -> Array:
	var spacing := minf(78.0, 600.0 / maxf(1.0, n - 1))
	var off := i - (n - 1) / 2.0
	return [Vector2(360 + off * spacing, HAND_Y + off * off * 2.4), off * 0.035]


func _hand_views_top_first() -> Array:
	var out: Array = []
	var hand := display_hand()
	for i in range(hand.size() - 1, -1, -1):
		var id := int(hand[i]["id"])
		if views.has(id):
			out.append(views[id])
	return out


func _ensure_view(card: Dictionary) -> CardView:
	var id := int(card["id"])
	if views.has(id):
		return views[id]
	var v := CardView.new()
	v.card = card
	v.position = DECK_POS
	v.rotation = -0.4
	v.scale = Vector2(HAND_SCALE, HAND_SCALE)
	cards_layer.add_child(v)
	views[id] = v
	return v


func _free_view(id: int) -> void:
	if views.has(id):
		(views[id] as CardView).queue_free()
		views.erase(id)


func _clear_views() -> void:
	for id in views.keys():
		_free_view(id)
	for v in arcana_views:
		v.queue_free()
	arcana_views = []


func sync_cards(dur: float) -> void:
	var keep := {}
	var show := screen == "game" and state.phase == "play"
	cards_layer.visible = show
	if not show:
		return
	for p in 3:
		var c = state.spread[p]
		if c == null:
			continue
		var v := _ensure_view(c)
		keep[int(c["id"])] = true
		v.z_index = 50 + p
		v.marked = false
		_move(v, SPREAD_CENTERS[p], 0.0, 1.0, dur)
	var hand := display_hand()
	var n := hand.size()
	for i in n:
		var v := _ensure_view(hand[i])
		var id := int(hand[i]["id"])
		keep[id] = true
		v.z_index = i
		v.marked = marked.has(id)
		var t := _hand_transform(i, n)
		var pos: Vector2 = t[0]
		if v.marked:
			pos.y -= 30
		_move(v, pos, t[1], HAND_SCALE, dur + i * 0.02)
	for id in views.keys():
		if not keep.has(id):
			_free_view(id)


func _move(v: CardView, pos: Vector2, rot: float, sc: float, dur: float) -> void:
	if v == press_view and dragging:
		return
	var d := _d(dur)
	if d <= 0.011:
		v.position = pos
		v.rotation = rot
		v.scale = Vector2(sc, sc)
		return
	var tw := create_tween().set_parallel().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tw.tween_property(v, "position", pos, d)
	tw.tween_property(v, "rotation", rot, d)
	tw.tween_property(v, "scale", Vector2(sc, sc), d)


func sync_arcana() -> void:
	for v in arcana_views:
		v.queue_free()
	arcana_views = []
	var show := screen == "game" and state.phase == "play"
	arcana_layer.visible = show
	table.arcana_visible = show
	if not show:
		return
	for i in state.arcana.size():
		var v := CardView.new()
		v.major = state.arcana[i]
		v.position = _arcana_pos(i)
		v.scale = Vector2(ARCANA_SCALE, ARCANA_SCALE)
		v.lit = v.major == "tower" and state.tower_armed
		arcana_layer.add_child(v)
		arcana_views.append(v)


# ------------------------------------------------------------------ HUD

func refresh() -> void:
	var ph := state.phase if screen == "game" else "title"
	table.show_slots = ph == "play"
	table.blocked = state.blocked_positions() if ph == "play" else []
	table.upcoming = state.upcoming_intents() if ph == "play" else []
	for p in 3:
		if not table.blocked.has(p):
			table.stain_grow[p] = 0.0
	table.queue_redraw()
	querent.visible = ph == "play"
	querent.kind = state.night_info()["id"] if screen == "game" else "curious"
	hud.show_score = ph == "play"
	hud.coins = state.coins if screen == "game" else 0
	hud.target = state.target() if screen == "game" else 0
	hud.deck_count = state.draw.size()
	var info := state.night_info()
	hud.top_left = "" if screen == "title" else "CYCLE I  ·  NIGHT %d OF 3" % (state.night + 1)
	hud.querent_name = info["name"] if ph == "play" else ""
	hud.querent_line = info["line"] if ph == "play" else ""
	hud.panel = "" if ph == "play" else ph
	if ph == "play" and not busy:
		shown_insight = float(state.insight)
	_refresh_preview()
	refresh_buttons_only()
	sync_cards(0.3)
	sync_arcana()


func _refresh_preview() -> void:
	hud.reading_name = ""
	hud.preview_line = ""
	if screen != "game" or state.phase != "play" or busy:
		return
	var p := state.preview()
	if int(p["count"]) > 0:
		var lv := int(state.levels.get(p["reading"], 1))
		hud.reading_name = Readings.DEFS[p["reading"]]["name"] + ("" if lv == 1 else " " + Cards.ROMAN[lv])
		hud.light = int(p["light"])
		hud.gravity = int(p["gravity"])
		var mult := int(p["mult"])
		hud.preview_line = "%d x %d%s = %d Insight" % [int(p["light"]), int(p["gravity"]), " x%d" % mult if mult > 1 else "", int(p["insight"])]
	else:
		hud.light = 0
		hud.gravity = 0
	_refresh_hint()


func _refresh_hint() -> void:
	if tooltip != "":
		hud.hint = tooltip
		if not busy:
			hud.preview_line = ""
		return
	if reshuffle_mode:
		hud.hint = "Mark cards to give back to the deck  (%d marked)" % marked.size()
	elif shadow_note != "":
		hud.hint = shadow_note
	else:
		hud.hint = "Tap a card to lay it, or drag it to a position"
	if busy or screen != "game" or state.phase != "play" or state.laid_count() == 0:
		return
	var p := state.preview()
	var mult := int(p["mult"])
	hud.preview_line = "%d x %d%s = %d Insight" % [int(p["light"]), int(p["gravity"]), " x%d" % mult if mult > 1 else "", int(p["insight"])]


func refresh_buttons_only() -> void:
	hud.buttons = []
	zones = []
	hud.speed_label = speed_labels[speed_i]
	if screen == "game":
		hud.add_button("speed", Rect2(610, 9, 96, 36), "speed " + speed_labels[speed_i], true, false, 18)
	var ph := state.phase if screen == "game" else "title"
	if busy and screen == "game":
		ph = "play"
	match ph:
		"title":
			hud.add_button("new", Rect2(200, 700, 320, 78), "New Reading", true, true, 32)
			if has_save():
				hud.add_button("continue", Rect2(200, 806, 320, 70), "Continue", true, false, 28)
		"patron":
			hud.data = {"offers": state.patron_offers}
			for i in state.patron_offers.size():
				hud.add_button("patron:%d" % i, Rect2(474, 340.0 + i * 300.0 + 40, 170, 54), "Take", true, true, 26)
		"intro":
			var info := state.night_info()
			var notes: Array = []
			match state.night:
				0:
					notes = ["Lay up to three cards in Past, Present and Future, then Read. Patterns score more.",
						"Past counts its Light twice. Present adds Gravity. Future gives half, then returns to your hand."]
				1:
					notes = ["The Shadow stirs. After your first Reading it shows where it will reach. Two Readings later, that position is eclipsed.",
						"You have %d Readings and %d Reshuffles." % [RunState.READINGS, RunState.RESHUFFLES]]
				2:
					notes = ["Boss: The Twin. A suit you have already read this Night gives half Light.",
						"The Shadow reaches twice tonight."]
			hud.data = {"label": "CYCLE I  ·  NIGHT %d OF 3" % (state.night + 1), "name": info["name"],
				"line": info["line"], "target": info["target"], "notes": notes}
			hud.add_button("begin", Rect2(190, 1090, 340, 80), "Begin the Reading", true, true, 30)
		"won":
			var r := state.last_reward
			hud.data = {"insight": state.insight, "title": "%s is satisfied" % state.night_info()["name"],
				"rows": [["Querent's fee", "+%d" % int(r.get("base", 0))], ["Readings to spare", "+%d" % int(r.get("unused", 0))],
					["Interest", "+%d" % int(r.get("interest", 0))]], "total": int(r.get("total", 0))}
			var last := state.night >= RunState.NIGHTS.size() - 1
			hud.add_button("onward", Rect2(190, 1090, 340, 80), "Finish the Cycle" if last else "To the Market", true, true, 30)
		"market":
			var items: Array = []
			var mpos: Array[Vector2] = [Vector2(200, 330), Vector2(520, 330), Vector2(140, 682), Vector2(320, 682), Vector2(535, 682)]
			for i in state.market.size():
				var it: Dictionary = state.market[i].duplicate()
				var pos: Vector2 = mpos[mini(i, mpos.size() - 1)]
				it["pos"] = pos
				it["scale"] = 0.78 if it["kind"] == "major" else (0.66 if it["kind"] == "minor" else 0.86)
				if it["kind"] == "major":
					it["caption"] = ArcanaDB.text_of(it["id"])
					it["caption_y"] = 120
				if it["kind"] == "sigil":
					it["level"] = int(state.levels.get(it["id"], 1))
				items.append(it)
				var can: bool = not it["sold"] and state.coins >= int(it["price"])
				if it["kind"] == "major" and state.arcana.size() >= ArcanaDB.MAX_SLOTS:
					can = false
				var ty := 522.0 if it["kind"] == "major" else 784.0
				hud.add_button("buy:%d" % i, Rect2(pos.x - 58, ty, 116, 44), "sold" if it["sold"] else "%d coins" % int(it["price"]), can, false, 20)
			hud.data = {"items": items, "owned": state.arcana}
			for i in state.arcana.size():
				hud.add_button("sell:%d" % i, Rect2(116 + i * 120 - 48, 1002, 96, 36), "sell 3", true, false, 17)
			hud.add_button("reroll", Rect2(76, 1100, 250, 70), "Reroll · 2", state.coins >= RunState.REROLL_PRICE, false, 26)
			hud.add_button("leave", Rect2(394, 1100, 250, 70), "Leave", true, true, 28)
		"defeat", "victory":
			var won := ph == "victory"
			var info := state.night_info()
			var line := "Three Querents left satisfied. The next Cycle is not in this build yet." if won else "%s needed %d Insight. You found %d." % [info["name"], int(info["target"]), state.insight]
			hud.data = {"line": line, "rows": [["Querents satisfied", str(state.night + (1 if won else 0))],
				["Best Reading", "%d %s" % [int(state.stats["best_reading"]), state.stats["best_reading_name"]]],
				["Total Insight", str(int(state.stats["total_insight"]))], ["Readings given", str(int(state.stats["readings"]))]]}
			hud.add_button("new", Rect2(190, 1060, 340, 80), "New Reading", true, true, 30)
			hud.add_button("title", Rect2(260, 1156, 200, 50), "Title", true, false, 22)
		"play":
			if reshuffle_mode:
				hud.add_button("cancel", Rect2(60, 948, 230, 60), "Cancel", not busy, false, 26)
				hud.add_button("discard", Rect2(430, 948, 230, 60), "Give back %d" % marked.size(), not busy and marked.size() > 0, true, 26)
			else:
				hud.add_button("reshuffle", Rect2(60, 948, 230, 60), "Reshuffle · %d" % state.reshuffles_left, not busy and state.reshuffles_left > 0, false, 26)
				hud.add_button("read", Rect2(430, 948, 230, 60), "Read · %d left" % state.readings_left, not busy and state.laid_count() > 0, true, 26)
	hud.queue_redraw()
