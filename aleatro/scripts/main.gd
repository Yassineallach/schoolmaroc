extends Control

const MAX_SELECT := 5
const STATS_PATH := "user://stats.cfg"
const SIDE_W := 340.0  # left sidebar width
const CHARM_H := 160.0
const TOP_H := 180.0  # charm row; table overlays start below it

var gs: GameState
var sfx: Sfx
var bg_mat: ShaderMaterial

var lbl_blind: Label
var lbl_target: Label
var lbl_reward: Label
var blind_box: Panel
var blind_chip: BlindChip
var lbl_round_score: Label
var lbl_ante: Label
var lbl_money: Label
var lbl_hands: Label
var lbl_discards: Label
var lbl_hand_name: Label
var lbl_chips: Label
var lbl_mult: Label
var btn_deck: Button
var lbl_charm_count: Label

var charm_row: Control
var charm_bg: Panel
var hand_layer: Control
var fx_layer: Control
var overlay: Control
var modal: Control
var controls: HBoxContainer
var btn_play: Button
var btn_discard: Button
var btn_rank: Button
var btn_suit: Button
var chosen_marker: Polygon2D
var jiggle := 0.0

var hand_views: Array = []
var drag_view: Control = null
var _drag_grab := Vector2.ZERO
var manual_order := false
var charm_views: Array = []
var busy := true
var _shop_open := false
var _overlay_full := false
var in_round := false
var sort_mode := "rank"
var vw := 1280.0
var vh := 720.0
var stats := {"best_ante": 0, "best_hand": 0, "runs": 0, "wins": 0}


func _ready() -> void:
	theme = _make_theme()
	sfx = Sfx.new()
	add_child(sfx)
	_load_stats()
	_build_ui()
	get_viewport().size_changed.connect(_on_resize)
	_on_resize()
	show_title()


# ---------------------------------------------------------------- UI building

func _make_theme() -> Theme:
	var t := Theme.new()
	t.default_font_size = 26
	t.set_color("font_color", "Label", Color.WHITE)
	t.set_color("font_shadow_color", "Label", Color(0, 0, 0, 0.4))
	t.set_constant("shadow_offset_x", "Label", 2)
	t.set_constant("shadow_offset_y", "Label", 3)
	return t


func _box(col: Color, step: float = 3.0, shadow := false) -> PixelBox:
	return PixelBox.new(col, step, 0.0, shadow)


func _panel(pos: Vector2, sz: Vector2, col: Color, parent: Node = self) -> Panel:
	var p := Panel.new()
	p.position = pos
	p.size = sz
	p.add_theme_stylebox_override("panel", _box(col, 3.0, col.a > 0.5))
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(p)
	return p


func _label(text: String, fsize: int = 26, col: Color = Color.WHITE, align := HORIZONTAL_ALIGNMENT_CENTER) -> Label:
	var l := Label.new()
	l.text = text
	l.horizontal_alignment = align
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", fsize)
	l.add_theme_color_override("font_color", col)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _place(l: Control, parent: Node, pos: Vector2, sz: Vector2) -> Control:
	parent.add_child(l)
	l.position = pos
	l.size = sz
	return l


func _button(text: String, col: Color, cb: Callable, min_size := Vector2(160, 76), fsize := 28) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = min_size
	b.focus_mode = Control.FOCUS_NONE
	var normal := PixelBox.new(col, 3.0, 6.0, true)
	var pressed := PixelBox.new(col.lightened(0.08), 3.0, 6.0, true)
	pressed.pressed = true
	var disabled := PixelBox.new(col.darkened(0.55).lerp(Color(0.3, 0.3, 0.3), 0.5), 3.0, 6.0, false)
	for sb in [normal, pressed, disabled]:
		sb.content_margin_bottom = 18
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", normal)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_stylebox_override("disabled", disabled)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	b.add_theme_font_size_override("font_size", fsize)
	b.add_theme_color_override("font_color", Color.WHITE)
	b.add_theme_color_override("font_hover_color", Color.WHITE)
	b.add_theme_color_override("font_pressed_color", Color.WHITE)
	b.add_theme_color_override("font_disabled_color", Color(1, 1, 1, 0.4))
	b.resized.connect(func(): b.pivot_offset = b.size / 2)
	b.pressed.connect(func():
		sfx.play("click")
		juice(b)
		jiggle += 0.5
		cb.call())
	return b


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg_mat = ShaderMaterial.new()
	bg_mat.shader = load("res://shaders/background.gdshader")
	bg.material = bg_mat
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	# Left sidebar: blind, round score, current hand, counters, money
	var side := _panel(Vector2(0, 0), Vector2(SIDE_W, 720), Color(0, 0, 0, 0.3))
	side.add_theme_stylebox_override("panel", _box(Color(0, 0, 0, 0.3), 0.0))
	blind_box = _panel(Vector2(10, 10), Vector2(320, 140), Color("3a7bd5"))
	lbl_blind = _place(_label("", 30), blind_box, Vector2(0, 4), Vector2(320, 38))
	_place(_label("Score at least", 20, Color(1, 1, 1, 0.8)), blind_box, Vector2(0, 40), Vector2(320, 24))
	lbl_target = _place(_label("", 38, Color("ffdf6b")), blind_box, Vector2(0, 62), Vector2(320, 44))
	lbl_reward = _place(_label("", 22, Data.MONEY_COLOR), blind_box, Vector2(0, 104), Vector2(320, 30))
	blind_chip = BlindChip.new(Color.WHITE, 58.0)
	blind_chip.position = Vector2(10, 46)
	blind_box.add_child(blind_chip)

	var score_box := _panel(Vector2(10, 160), Vector2(320, 70), Color(0, 0, 0, 0.35))
	_place(_label("Round score", 22, Color(1, 1, 1, 0.8), HORIZONTAL_ALIGNMENT_LEFT), score_box, Vector2(14, 0), Vector2(140, 70))
	lbl_round_score = _place(_label("0", 36, Color.WHITE, HORIZONTAL_ALIGNMENT_RIGHT), score_box, Vector2(140, 0), Vector2(166, 70))

	var sbox := _panel(Vector2(10, 240), Vector2(320, 120), Color(0, 0, 0, 0.35))
	lbl_hand_name = _place(_label("", 26), sbox, Vector2(0, 4), Vector2(320, 38))
	var cbox := _panel(Vector2(10, 46), Vector2(138, 62), Data.CHIP_COLOR, sbox)
	lbl_chips = _place(_label("0", 34), cbox, Vector2(0, 0), Vector2(138, 62))
	_place(_label("x", 34, Color("ff6b6b")), sbox, Vector2(148, 46), Vector2(24, 62))
	var mbox := _panel(Vector2(172, 46), Vector2(138, 62), Data.MULT_COLOR, sbox)
	lbl_mult = _place(_label("0", 34), mbox, Vector2(0, 0), Vector2(138, 62))

	var hb := _panel(Vector2(10, 370), Vector2(155, 100), Data.CHIP_COLOR.darkened(0.35))
	_place(_label("Hands", 20), hb, Vector2(0, 6), Vector2(155, 26))
	lbl_hands = _place(_label("4", 44), hb, Vector2(0, 32), Vector2(155, 60))
	var db := _panel(Vector2(175, 370), Vector2(155, 100), Data.MULT_COLOR.darkened(0.35))
	_place(_label("Discards", 20), db, Vector2(0, 6), Vector2(155, 26))
	lbl_discards = _place(_label("3", 44), db, Vector2(0, 32), Vector2(155, 60))

	var info_box := _panel(Vector2(10, 480), Vector2(320, 90), Color(0, 0, 0, 0.35))
	lbl_ante = _place(_label("", 28), info_box, Vector2(0, 0), Vector2(150, 90))
	lbl_money = _place(_label("", 46, Data.MONEY_COLOR), info_box, Vector2(150, 0), Vector2(170, 90))
	_place(_button("Poker Hands", Color("5a5f73"), show_hand_info, Vector2(320, 56), 24), self, Vector2(10, 582), Vector2(320, 56))
	btn_deck = _place(_button("Deck", Color("4a4f63"), show_deck, Vector2(320, 48), 22), self, Vector2(10, 650), Vector2(320, 48))

	# Charm row along the top of the table
	charm_bg = _panel(Vector2(SIDE_W + 10, 10), Vector2(900, CHARM_H), Color(0, 0, 0, 0.25))
	charm_row = Control.new()
	charm_row.position = Vector2(SIDE_W + 10, 10)
	add_child(charm_row)
	lbl_charm_count = _place(_label("0/5", 18, Color(1, 1, 1, 0.7), HORIZONTAL_ALIGNMENT_RIGHT), charm_bg, Vector2(0, CHARM_H - 26), Vector2(0, 24))

	hand_layer = Control.new()
	hand_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	hand_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(hand_layer)

	controls = HBoxContainer.new()
	controls.add_theme_constant_override("separation", 14)
	controls.alignment = BoxContainer.ALIGNMENT_CENTER
	btn_play = _button("Play Hand", Data.CHIP_COLOR, play_selected, Vector2(220, 80))
	btn_discard = _button("Discard", Data.MULT_COLOR, discard_selected, Vector2(220, 80))
	controls.add_child(btn_play)
	btn_rank = _button("Rank", Color("c47b1a"), func(): set_sort("rank"), Vector2(120, 80), 24)
	btn_suit = _button("Suit", Color("c47b1a"), func(): set_sort("suit"), Vector2(120, 80), 24)
	controls.add_child(btn_rank)
	controls.add_child(btn_suit)
	chosen_marker = Polygon2D.new()
	chosen_marker.polygon = PackedVector2Array([Vector2(-11, 0), Vector2(11, 0), Vector2(0, 13)])
	chosen_marker.color = Data.MULT_COLOR
	btn_rank.add_child(chosen_marker)
	_place_marker()
	var bob := create_tween().set_loops()
	bob.tween_property(chosen_marker, "offset:y", -5.0, 0.5).set_trans(Tween.TRANS_SINE)
	bob.tween_property(chosen_marker, "offset:y", 0.0, 0.5).set_trans(Tween.TRANS_SINE)
	controls.add_child(btn_discard)
	add_child(controls)

	fx_layer = Control.new()
	fx_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	fx_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(fx_layer)

	overlay = Control.new()
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(overlay)
	modal = Control.new()
	modal.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(modal)
	# Cards use z_index for fanning and dragging; keep popups above them.
	fx_layer.z_index = 300
	overlay.z_index = 350
	modal.z_index = 400


func _on_resize() -> void:
	var s := get_viewport_rect().size
	vw = s.x
	vh = s.y
	bg_mat.set_shader_parameter("aspect", vw / vh)
	var mw := main_w()
	charm_bg.size = Vector2(mw - 20, CHARM_H)
	charm_row.size = charm_bg.size
	lbl_charm_count.position = Vector2(mw - 140, CHARM_H - 26)
	lbl_charm_count.size = Vector2(110, 24)
	controls.position = Vector2(SIDE_W, vh - 94)
	controls.size = Vector2(mw, 80)
	_fit_overlay()
	modal.size = s
	if gs:
		rebuild_charms()
	layout_hand(false)


## Width of the table area right of the sidebar.
func main_w() -> float:
	return vw - SIDE_W


func main_cx() -> float:
	return SIDE_W + main_w() / 2.0


func hand_y() -> float:
	return vh - 104.0 - CardView.H - 14.0


func play_y() -> float:
	return (TOP_H + hand_y()) / 2.0 - CardView.H / 2.0 - 16.0


func _place_marker() -> void:
	var b := btn_rank if sort_mode == "rank" else btn_suit
	if chosen_marker.get_parent() != b:
		chosen_marker.reparent(b, false)
	chosen_marker.position = Vector2(60, -18)


## Quick squash-and-wobble used on taps and score changes.
func juice(node: Control, amount: float = 0.12) -> void:
	node.pivot_offset = node.size / 2
	var tw := create_tween().set_parallel()
	node.scale = Vector2.ONE * (1.0 + amount)
	node.rotation_degrees = randf_range(-3.0, 3.0)
	tw.tween_property(node, "scale", Vector2.ONE, 0.35).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	tw.tween_property(node, "rotation_degrees", 0.0, 0.3).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)


## Small screen shake that decays every frame.
func _process(delta: float) -> void:
	if jiggle > 0.0:
		jiggle = maxf(0.0, jiggle - delta * 4.0)
		position = Vector2(randf_range(-1, 1), randf_range(-1, 1)) * jiggle * 4.0
	elif position != Vector2.ZERO:
		position = Vector2.ZERO


# ---------------------------------------------------------------- HUD

func update_hud() -> void:
	if gs == null:
		return
	lbl_ante.text = "Ante %d/%d" % [gs.ante, Data.FINAL_ANTE]
	lbl_money.text = "$%d" % gs.money
	lbl_hands.text = str(gs.hands_left)
	lbl_discards.text = str(gs.discards_left)
	lbl_round_score.text = Data.fmt(gs.round_score)
	btn_deck.text = "Deck %d/%d" % [gs.draw_pile.size() if in_round else gs.deck.size(), gs.deck.size()]
	lbl_charm_count.text = "%d/%d" % [gs.charms.size(), gs.charm_slots]
	var shown_idx := gs.blind_idx
	lbl_blind.text = gs.blind_name(shown_idx)
	lbl_target.text = Data.fmt(gs.blind_target(shown_idx) if not in_round else gs.target)
	lbl_reward.text = "Reward: " + "$".repeat(gs.blind_reward(shown_idx))
	blind_box.add_theme_stylebox_override("panel", _box(gs.blind_color(shown_idx), 3.0, true))
	blind_chip.color = gs.blind_color(shown_idx).lightened(0.3)
	var boss := gs.blind_idx == 2
	bg_mat.set_shader_parameter("base_a", gs.boss_hex.color.darkened(0.45) if boss else Color(0.09, 0.30, 0.22))
	bg_mat.set_shader_parameter("base_b", gs.boss_hex.color.darkened(0.8) if boss else Color(0.04, 0.15, 0.12))
	btn_play.disabled = busy or not in_round or selected_views().is_empty()
	btn_discard.disabled = busy or not in_round or selected_views().is_empty() or gs.discards_left <= 0
	update_preview()


func update_preview() -> void:
	if busy or not in_round:
		return
	var sel := selected_views()
	if sel.is_empty():
		lbl_hand_name.text = ""
		lbl_chips.text = "0"
		lbl_mult.text = "0"
		return
	var ev := Poker.evaluate(sel.map(func(v): return v.card))
	var lvl: int = gs.hand_levels[ev.name]
	lbl_hand_name.text = "%s  lvl %d" % [ev.name, lvl]
	lbl_chips.text = Data.fmt(Data.hand_chips(ev.name, lvl))
	lbl_mult.text = Data.fmt(Data.hand_mult(ev.name, lvl))


func rebuild_charms() -> void:
	for v in charm_views:
		v.queue_free()
	charm_views = []
	var n := gs.charms.size() if gs else 0
	for i in n:
		var v := CharmView.new(gs.charms[i].id, "", gs.charms[i].get("ed", ""))
		v.set_meta("inst", gs.charms[i])
		v.tapped.connect(_on_charm_tapped)
		v.held.connect(_on_charm_tapped)
		v.drag_started.connect(_on_drag_start)
		v.dragged.connect(_on_drag_move)
		v.drag_ended.connect(_on_drag_end)
		charm_row.add_child(v)
		charm_views.append(v)
	layout_charms(false)
	update_hud()


func layout_charms(animate: bool) -> void:
	var n := charm_views.size()
	var step := 136.0
	var x0 := (charm_row.size.x - (CharmView.W + step * maxi(n - 1, 0))) / 2.0
	for i in n:
		var v: CharmView = charm_views[i]
		if v == drag_view:
			continue
		var target := Vector2(x0 + i * step, 4)
		if animate:
			create_tween().tween_property(v, "position", target, 0.18).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		else:
			v.position = target


# ---------------------------------------------------------------- dragging

## Cards in hand and owned charms can be dragged sideways to reorder them.
func _drag_list(v: Control) -> Array:
	return hand_views if v is CardView else charm_views


func _on_drag_start(v: Control, pos: Vector2) -> void:
	if v is CardView and (busy or not in_round or not hand_views.has(v)):
		return
	if v is CharmView and busy and in_round:
		return
	drag_view = v
	_drag_grab = pos - v.global_position
	v.z_index = 200
	juice(v, 0.08)


func _on_drag_move(v: Control, pos: Vector2) -> void:
	if v != drag_view:
		return
	v.global_position = pos - _drag_grab
	var list := _drag_list(v)
	var cx := v.global_position.x + v.size.x / 2
	var idx := 0
	for o in list:
		if o != v and o.global_position.x + o.size.x / 2 < cx:
			idx += 1
	var cur := list.find(v)
	if idx != cur:
		list.remove_at(cur)
		list.insert(idx, v)
		if v is CardView:
			manual_order = true
			layout_hand(true)
		else:
			layout_charms(true)


func _on_drag_end(v: Control) -> void:
	if v != drag_view:
		return
	drag_view = null
	if v is CardView:
		gs.hand = hand_views.map(func(h): return h.card)
		layout_hand(true)
	else:
		gs.charms = charm_views.map(func(c): return _charm_inst(c))
		layout_charms(true)
	sfx.play("select")


func _charm_inst(v: CharmView) -> Dictionary:
	return v.get_meta("inst")


func popup_text(pos: Vector2, text: String, col: Color, fsize: int = 34) -> void:
	var l := _label(text, fsize, col)
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 10)
	l.size = Vector2(220, 50)
	l.position = pos - l.size / 2
	fx_layer.add_child(l)
	l.scale = Vector2(0.4, 0.4)
	l.pivot_offset = l.size / 2
	var tw := create_tween()
	tw.tween_property(l, "scale", Vector2.ONE, 0.12).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(l, "position:y", l.position.y - 50, 0.5)
	tw.parallel().tween_property(l, "modulate:a", 0.0, 0.3).set_delay(0.2)
	tw.tween_callback(l.queue_free)


func bump(node: Control, amount: float = 1.18) -> void:
	node.pivot_offset = node.size / 2
	var tw := create_tween()
	tw.tween_property(node, "scale", Vector2(amount, amount), 0.07)
	tw.parallel().tween_property(node, "rotation_degrees", randf_range(-4.0, 4.0), 0.07)
	tw.tween_property(node, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	tw.parallel().tween_property(node, "rotation_degrees", 0.0, 0.25).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)


func wait(t: float) -> void:
	await get_tree().create_timer(t).timeout


# ---------------------------------------------------------------- overlays

func clear_overlay() -> void:
	for c in overlay.get_children():
		c.queue_free()
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _fit_overlay() -> void:
	overlay.position = Vector2.ZERO if _overlay_full else Vector2(SIDE_W, TOP_H)
	overlay.size = Vector2(vw, vh) if _overlay_full else Vector2(main_w(), vh - TOP_H)


## Builds a centered panel in the overlay area and returns its VBox.
func open_overlay(full_screen := false) -> VBoxContainer:
	clear_overlay()
	_shop_open = false
	overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	_overlay_full = full_screen
	_fit_overlay()
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.55 if full_screen else 0.35)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.add_child(center)
	var panel := PanelContainer.new()
	var sb := _box(Color("1d2a33").lerp(Color.BLACK, 0.1), 5.0, true)
	sb.set_content_margin_all(26)
	sb.outline = 3.0
	sb.outline_color = Color(1, 1, 1, 0.2)
	panel.add_theme_stylebox_override("panel", sb)
	panel.custom_minimum_size = Vector2(660, 0)
	center.add_child(panel)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 16)
	vb.alignment = BoxContainer.ALIGNMENT_CENTER
	panel.add_child(vb)
	panel.scale = Vector2(0.92, 0.92)
	panel.modulate.a = 0
	panel.resized.connect(func(): panel.pivot_offset = panel.size / 2)
	var tw := create_tween()
	tw.tween_property(panel, "scale", Vector2.ONE, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.parallel().tween_property(panel, "modulate:a", 1.0, 0.12)
	return vb


func _row_label(vb: Container, left: String, right: String, right_col := Data.MONEY_COLOR) -> void:
	var hb := HBoxContainer.new()
	var l := _label(left, 26, Color.WHITE, HORIZONTAL_ALIGNMENT_LEFT)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hb.add_child(l)
	hb.add_child(_label(right, 28, right_col, HORIZONTAL_ALIGNMENT_RIGHT))
	vb.add_child(hb)


func show_title() -> void:
	in_round = false
	busy = true
	var vb := open_overlay(true)
	var title := _label("ALEATRO", 92, Color("ffdf6b"))
	title.add_theme_color_override("font_outline_color", Color("b3364e"))
	title.add_theme_constant_override("outline_size", 18)
	vb.add_child(title)
	vb.add_child(_label("A poker roguelike", 26, Color(1, 1, 1, 0.8)))
	var cards := HBoxContainer.new()
	cards.alignment = BoxContainer.ALIGNMENT_CENTER
	cards.add_theme_constant_override("separation", -20)
	for i in 5:
		var cv := CardView.new({"rank": [14, 13, 12, 11, 10][i], "suit": [1, 0, 3, 2, 1][i], "id": -1})
		cv.mouse_filter = Control.MOUSE_FILTER_IGNORE
		cv.float_amount = 1.2
		cv.rotation_degrees = (i - 2) * 6
		cards.add_child(cv)
	vb.add_child(cards)
	vb.add_child(Control.new())
	var b := _button("Play", Data.CHIP_COLOR, new_run, Vector2(320, 96), 40)
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	vb.add_child(b)
	var h := _button("How to play", Color("5a5f73"), show_help, Vector2(320, 70), 26)
	h.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	vb.add_child(h)
	if stats.runs > 0:
		vb.add_child(_label("Best ante: %d   Best hand: %s   Wins: %d" % [stats.best_ante, Data.fmt(stats.best_hand), stats.wins], 20, Color(1, 1, 1, 0.7)))


func show_help() -> void:
	var vb := open_modal()
	vb.add_child(_label("How to play", 40, Color("ffdf6b")))
	var t := Label.new()
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	t.custom_minimum_size = Vector2(820, 0)
	t.add_theme_font_size_override("font_size", 23)
	t.text = "Select up to 5 cards and play a poker hand. Each hand type has base Chips and Mult; scored cards add their rank in Chips (faces 10, Aces 11).\n\nScore = Chips x Mult. Reach the blind's target before you run out of hands. Discards let you swap cards.\n\nEach ante has a Small Blind, a Big Blind and a Boss Blind with a nasty twist. Beat ante %d to win.\n\nSpend money in the shop on Charms (passive bonuses, up to 5) and Runes (level up a hand type). You earn $1 interest per $5 held, up to $5." % Data.FINAL_ANTE
	vb.add_child(t)
	vb.add_child(_center(_button("Close", Color("5a5f73"), close_modal, Vector2(220, 70))))


func _center(c: Control) -> Control:
	c.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	return c


func new_run() -> void:
	gs = GameState.new()
	stats.runs += 1
	_save_stats()
	clear_hand_views()
	rebuild_charms()
	lbl_hand_name.text = ""
	lbl_chips.text = "0"
	lbl_mult.text = "0"
	show_blind_select()


func show_blind_select() -> void:
	in_round = false
	busy = true
	update_hud()
	var vb := open_overlay()
	vb.add_child(_label("Ante %d" % gs.ante, 40, Color("ffdf6b")))
	var cols := HBoxContainer.new()
	cols.alignment = BoxContainer.ALIGNMENT_CENTER
	cols.add_theme_constant_override("separation", 16)
	for i in 3:
		var p := PanelContainer.new()
		p.custom_minimum_size = Vector2(250, 190)
		var current := i == gs.blind_idx
		var col := gs.blind_color(i)
		var sb := _box(col if current else col.darkened(0.6), 3.0, current)
		if current:
			sb.outline = 4.0
			sb.outline_color = Color.WHITE
		p.add_theme_stylebox_override("panel", sb)
		var inner := VBoxContainer.new()
		inner.add_theme_constant_override("separation", 4)
		var state := "Upcoming"
		if i < gs.blind_idx:
			state = "Defeated"
		elif current:
			state = "Up next"
		inner.add_child(_label(state, 18, Color(1, 1, 1, 0.75)))
		inner.add_child(_center(BlindChip.new(col.lightened(0.3), 60.0)))
		inner.add_child(_label(gs.blind_name(i), 30))
		inner.add_child(_label("Score at least", 18, Color(1, 1, 1, 0.8)))
		inner.add_child(_label(Data.fmt(gs.blind_target(i)), 30, Color("ffdf6b")))
		inner.add_child(_label("Reward " + "$".repeat(gs.blind_reward(i)), 20, Data.MONEY_COLOR))
		if i == 2:
			var desc := _label(gs.boss_hex.desc, 19, Color.WHITE)
			desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			desc.custom_minimum_size = Vector2(220, 0)
			inner.add_child(desc)
		p.add_child(inner)
		if i < gs.blind_idx:
			p.modulate.a = 0.5
		cols.add_child(p)
	vb.add_child(cols)
	vb.add_child(_center(_button("Play " + gs.blind_name(), gs.blind_color(), start_blind, Vector2(360, 86), 30)))


# ---------------------------------------------------------------- round flow

func start_blind() -> void:
	clear_overlay()
	_shop_open = false
	gs.start_round()
	in_round = true
	busy = true
	lbl_hand_name.text = gs.blind_name()
	lbl_chips.text = "0"
	lbl_mult.text = "0"
	update_hud()
	popup_text(Vector2(main_cx(), play_y() + 60), gs.blind_name(), Color.WHITE, 44)
	if gs.blind_idx == 2:
		popup_text(Vector2(main_cx(), play_y() + 110), gs.boss_hex.desc, Color("ffdf6b"), 26)
	await deal()
	busy = false
	update_hud()


func clear_hand_views() -> void:
	for v in hand_views:
		v.queue_free()
	hand_views = []
	drag_view = null
	manual_order = false


func deal() -> void:
	var drawn := gs.draw_cards()
	for c in drawn:
		var v := CardView.new(c)
		v.set_debuffed(gs.is_debuffed(c))
		v.position = Vector2(vw - 60, vh - 120)
		v.rotation_degrees = 30
		v.face_up = false
		v.tapped.connect(_on_card_tapped)
		v.held.connect(show_card_info)
		v.drag_started.connect(_on_drag_start)
		v.dragged.connect(_on_drag_move)
		v.drag_ended.connect(_on_drag_end)
		hand_layer.add_child(v)
		hand_views.append(v)
	if not manual_order:
		sort_hand()
	gs.hand = hand_views.map(func(h): return h.card)
	for i in drawn.size():
		sfx.play("deal", 0.9 + 0.05 * i)
	layout_hand(true)
	update_hud()
	var k := 0
	for v in hand_views:
		if not v.face_up:
			v.flip_up(0.15 + 0.05 * k)
			k += 1
	await wait(0.35 + 0.05 * k)


func sort_hand() -> void:
	if sort_mode == "rank":
		hand_views.sort_custom(func(a, b):
			if a.card.rank != b.card.rank:
				return a.card.rank > b.card.rank
			return a.card.suit < b.card.suit)
	else:
		hand_views.sort_custom(func(a, b):
			if a.card.suit != b.card.suit:
				return a.card.suit < b.card.suit
			return a.card.rank > b.card.rank)
	gs.hand = hand_views.map(func(v): return v.card)


func set_sort(mode: String) -> void:
	sort_mode = mode
	manual_order = false
	_place_marker()
	if gs == null or not in_round or busy:
		return
	sort_hand()
	layout_hand(true)


func layout_hand(animate: bool) -> void:
	var n := hand_views.size()
	if n == 0:
		return
	var avail := main_w() - 40.0
	var step := minf(CardView.W + 6, (avail - CardView.W) / maxf(n - 1, 1))
	var total := CardView.W + step * (n - 1)
	var x0 := main_cx() - total / 2.0
	for i in n:
		var v: CardView = hand_views[i]
		if v == drag_view:
			continue
		var off := i - (n - 1) / 2.0
		var target := Vector2(x0 + i * step, hand_y() + absf(off) * absf(off) * 2.0 - (34.0 if v.selected else 0.0))
		var rot := off * 2.5
		v.z_index = i
		if animate:
			var tw := create_tween().set_parallel()
			tw.tween_property(v, "position", target, 0.18).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
			tw.tween_property(v, "rotation_degrees", rot, 0.18)
		else:
			v.position = target
			v.rotation_degrees = rot


func selected_views() -> Array:
	return hand_views.filter(func(v): return v.selected)


func _on_card_tapped(v: CardView) -> void:
	if busy or not in_round or not hand_views.has(v):
		return
	if not v.selected and selected_views().size() >= MAX_SELECT:
		return
	v.selected = not v.selected
	v.queue_redraw()
	sfx.play("select", 1.1 if v.selected else 0.9)
	layout_hand(true)
	update_hud()


func play_selected() -> void:
	if busy or not in_round:
		return
	var sel := selected_views()
	if sel.is_empty():
		return
	busy = true
	gs.hands_left -= 1
	update_hud()
	btn_play.disabled = true
	btn_discard.disabled = true

	# Move the played cards to the play row.
	for v in sel:
		hand_views.erase(v)
	var n := sel.size()
	var gap := 108.0
	var x0 := main_cx() - (CardView.W + gap * (n - 1)) / 2.0
	for i in n:
		var v: CardView = sel[i]
		v.selected = false
		v.queue_redraw()
		v.z_index = 50 + i
		var tw := create_tween().set_parallel()
		tw.tween_property(v, "position", Vector2(x0 + i * gap, play_y()), 0.22).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_property(v, "rotation_degrees", 0.0, 0.22)
	layout_hand(true)
	await wait(0.3)

	var played: Array = sel.map(func(v): return v.card)
	var ev := Poker.evaluate(played)
	gs.hands_played_count[ev.name] += 1
	for c in gs.charms:
		if c.id == "snowball":
			c.data.m = c.data.get("m", 0) + 1
	var result := Scoring.compute(gs, played, ev, hand_views.map(func(v): return v.card))
	var view_of := {}
	for v in sel + hand_views:
		view_of[v.card.id] = v
	var scoring_ids: Array = ev.scoring.map(func(c): return c.id)
	for v in sel:
		if not scoring_ids.has(v.card.id):
			var tw := create_tween()
			tw.tween_property(v, "modulate", Color(0.6, 0.6, 0.6), 0.15)

	var chips := 0.0
	var mult := 0.0
	var step_t := 0.3
	var pitch := 1.0
	lbl_hand_name.text = "%s  lvl %d" % [ev.name, gs.hand_levels[ev.name]]
	for e in result.events:
		if e.kind == "base":
			chips = e.chips
			mult = e.mult
			lbl_chips.text = Data.fmt(chips)
			lbl_mult.text = Data.fmt(mult)
			bump(lbl_chips.get_parent())
			bump(lbl_mult.get_parent())
			await wait(step_t)
			continue
		# Popups go above a played card, below a charm, or above a held card.
		var anchor := Vector2.ZERO
		if e.has("charm_index"):
			var cv: CharmView = charm_views[e.charm_index]
			bump(cv, 1.15)
			anchor = cv.global_position + Vector2(CharmView.W / 2, CharmView.H + 18)
		if e.has("card"):
			var v: CardView = view_of[e.card.id]
			bump(v, 1.2 if e.kind != "charm" else 1.1)
			if e.kind == "held" or not e.has("charm_index"):
				anchor = v.position + Vector2(CardView.W / 2, -24)
			else:
				anchor = v.position + Vector2(CardView.W / 2, CardView.H + 22)
		if e.get("debuff", false):
			popup_text(anchor, "Debuffed", Color("aaaaaa"), 26)
		if e.get("again", false):
			popup_text(anchor, "Again!", Color("ffdf6b"), 30)
			sfx.play("select", 1.3)
		var line := 0
		if e.has("chips"):
			chips += e.chips
			lbl_chips.text = Data.fmt(chips)
			bump(lbl_chips.get_parent(), 1.08)
			popup_text(anchor, "+%d" % e.chips, Data.CHIP_COLOR.lightened(0.2))
			sfx.play("chips", pitch)
			line += 1
		if e.has("mult"):
			mult += e.mult
			lbl_mult.text = _fmt_mult(mult)
			bump(lbl_mult.get_parent(), 1.08)
			popup_text(anchor + Vector2(0, 36 * line), "+%d Mult" % e.mult, Data.MULT_COLOR)
			sfx.play("mult", pitch)
			line += 1
		if e.has("xmult"):
			mult *= e.xmult
			lbl_mult.text = _fmt_mult(mult)
			bump(lbl_mult.get_parent(), 1.08)
			popup_text(anchor + Vector2(0, 36 * line), "x%s Mult" % str(e.xmult).trim_suffix(".0"), Data.XMULT_COLOR)
			sfx.play("xmult", pitch)
			line += 1
		if e.has("money"):
			gs.money += e.money
			update_hud()
			bump(lbl_money, 1.2)
			popup_text(anchor + Vector2(0, 36 * line), "$%d" % e.money, Data.MONEY_COLOR)
			sfx.play("coin", pitch)
		pitch += 0.04
		await wait(step_t)

	var total := int(floor(chips * mult))
	gs.best_hand = maxi(gs.best_hand, total)
	if total > stats.best_hand:
		stats.best_hand = total
		_save_stats()
	lbl_hand_name.text = Data.fmt(total)
	bump(lbl_hand_name, 1.3)
	sfx.play("coin")
	await wait(0.45)
	var from := gs.round_score
	gs.round_score += total
	var tw := create_tween()
	tw.tween_method(func(x): lbl_round_score.text = Data.fmt(x), from, gs.round_score, 0.4)
	await wait(0.5)

	# Glass cards that broke leave the deck for good.
	for c in result.shatter:
		var v: CardView = view_of[c.id]
		sel.erase(v)
		gs.remove_from_deck(c)
		shatter(v)
	if not result.shatter.is_empty():
		await wait(0.4)
	# Clear played cards.
	for i in sel.size():
		var v: CardView = sel[i]
		var t2 := create_tween().set_parallel()
		t2.tween_property(v, "position", Vector2(vw + 40, play_y() - 80), 0.25).set_delay(i * 0.04)
		t2.tween_property(v, "rotation_degrees", 40.0, 0.25).set_delay(i * 0.04)
		t2.chain().tween_callback(v.queue_free)
	gs.hand = hand_views.map(func(v): return v.card)
	lbl_chips.text = "0"
	lbl_mult.text = "0"
	await wait(0.3)

	if gs.round_score >= gs.target:
		await win_round()
		return
	if gs.hands_left <= 0:
		game_over()
		return
	if gs.hex() == "grip" and not hand_views.is_empty():
		for k in 2:
			if hand_views.is_empty():
				break
			var v: CardView = hand_views[gs.rng.randi_range(0, hand_views.size() - 1)]
			hand_views.erase(v)
			var t3 := create_tween()
			t3.tween_property(v, "position", Vector2(vw + 40, v.position.y), 0.25)
			t3.tween_callback(v.queue_free)
		popup_text(Vector2(main_cx(), play_y() + 60), "The Grip!", gs.boss_hex.color.lightened(0.3), 36)
		gs.hand = hand_views.map(func(v): return v.card)
		await wait(0.3)
	lbl_hand_name.text = ""
	await deal()
	busy = false
	update_hud()


func _fmt_mult(m: float) -> String:
	if is_equal_approx(m, round(m)) or m >= 100:
		return Data.fmt(int(m))
	return "%.1f" % m


func discard_selected() -> void:
	if busy or not in_round or gs.discards_left <= 0:
		return
	var sel := selected_views()
	if sel.is_empty():
		return
	busy = true
	gs.discards_left -= 1
	for i in sel.size():
		var v: CardView = sel[i]
		hand_views.erase(v)
		var tw := create_tween().set_parallel()
		tw.tween_property(v, "position", Vector2(vw + 40, v.position.y - 60), 0.22).set_delay(i * 0.04)
		tw.tween_property(v, "rotation_degrees", 30.0, 0.22).set_delay(i * 0.04)
		tw.chain().tween_callback(v.queue_free)
	gs.hand = hand_views.map(func(v): return v.card)
	update_hud()
	await wait(0.25)
	await deal()
	busy = false
	update_hud()


func win_round() -> void:
	in_round = false
	sfx.play("win")
	await wait(0.3)
	var gilded := 0
	for v in hand_views:
		if v.card.get("enh", "") == "gilded" and not gs.is_debuffed(v.card):
			gilded += 3
	clear_hand_views()
	lbl_hand_name.text = ""
	var reward := gs.blind_reward()
	var per_hand := gs.hands_left
	var interest := gs.interest()
	var charm_cash := 0
	for c in gs.charms:
		if c.id == "gold":
			charm_cash += 4
	var total := reward + per_hand + interest + charm_cash + gilded
	var vb := open_overlay()
	vb.add_child(_label(gs.blind_name() + " defeated!", 38, Color("ffdf6b")))
	_row_label(vb, "Blind reward", "$%d" % reward)
	if per_hand > 0:
		_row_label(vb, "Remaining hands (%d)" % per_hand, "$%d" % per_hand)
	if interest > 0:
		_row_label(vb, "Interest ($1 per $5)", "$%d" % interest)
	if charm_cash > 0:
		_row_label(vb, "Gold Tooth", "$%d" % charm_cash)
	if gilded > 0:
		_row_label(vb, "Gilded cards held", "$%d" % gilded)
	vb.add_child(_center(_button("Cash Out: $%d" % total, Color("e0a526"), func():
		gs.money += total
		sfx.play("coin")
		cash_out(), Vector2(380, 90), 32)))


func cash_out() -> void:
	var won_run := gs.blind_idx == 2 and gs.ante == Data.FINAL_ANTE and not gs.endless
	stats.best_ante = maxi(stats.best_ante, gs.ante)
	gs.advance_blind()
	_save_stats()
	if won_run:
		stats.wins += 1
		_save_stats()
		show_victory()
		return
	open_shop()


func game_over() -> void:
	in_round = false
	busy = true
	sfx.play("lose")
	stats.best_ante = maxi(stats.best_ante, gs.ante)
	_save_stats()
	clear_hand_views()
	lbl_hand_name.text = ""
	var vb := open_overlay(true)
	vb.add_child(_label("Game Over", 64, Data.MULT_COLOR))
	_row_label(vb, "Reached", "Ante %d" % gs.ante, Color.WHITE)
	_row_label(vb, "Best hand", Data.fmt(gs.best_hand), Data.CHIP_COLOR.lightened(0.3))
	var most := "High Card"
	for n in Data.HAND_ORDER:
		if gs.hands_played_count[n] > gs.hands_played_count[most]:
			most = n
	_row_label(vb, "Most played", most, Color.WHITE)
	vb.add_child(_center(_button("New Run", Data.CHIP_COLOR, new_run, Vector2(320, 90), 34)))
	vb.add_child(_center(_button("Main Menu", Color("5a5f73"), show_title, Vector2(320, 70), 26)))


func show_victory() -> void:
	busy = true
	var vb := open_overlay(true)
	vb.add_child(_label("You Win!", 72, Color("ffdf6b")))
	vb.add_child(_label("You beat ante %d." % Data.FINAL_ANTE, 28))
	_row_label(vb, "Best hand", Data.fmt(gs.best_hand), Data.CHIP_COLOR.lightened(0.3))
	vb.add_child(_center(_button("Endless Mode", Color("7b4fa0"), func():
		gs.endless = true
		open_shop(), Vector2(340, 84), 30)))
	vb.add_child(_center(_button("New Run", Data.CHIP_COLOR, new_run, Vector2(340, 84), 30)))


# ---------------------------------------------------------------- shop

func open_shop() -> void:
	gs.reroll_cost = 5
	gs.roll_shop()
	show_shop()


func show_shop() -> void:
	in_round = false
	busy = true
	update_hud()
	var vb := open_overlay()
	_shop_open = true
	vb.add_child(_label("Shop", 40, Color("ffdf6b")))
	vb.add_child(_label("Tap a charm above to sell it. Bought cards join your deck.", 18, Color(1, 1, 1, 0.6)))
	var body := HBoxContainer.new()
	body.alignment = BoxContainer.ALIGNMENT_CENTER
	body.add_theme_constant_override("separation", 24)
	vb.add_child(body)
	var grid := HBoxContainer.new()
	grid.alignment = BoxContainer.ALIGNMENT_CENTER
	grid.add_theme_constant_override("separation", 16)
	for i in gs.shop_charms.size():
		var d: Dictionary = gs.shop_charms[i]
		var desc: String = d.desc
		if d.get("ed", "") != "":
			desc = "%s\n%s: %s" % [d.desc, Data.EDITIONS[d.ed].name, Data.EDITIONS[d.ed].desc]
		grid.add_child(_shop_item(CharmView.new(d.id, "", d.get("ed", "")), d.cost, desc, Data.RARITY_NAMES[d.rarity], func(): buy_charm(i)))
	for i in gs.shop_runes.size():
		var h: String = gs.shop_runes[i]
		var b: Array = Data.HAND_BASE[h]
		grid.add_child(_shop_item(CharmView.new("", h), Data.RUNE_COST, "Level up %s\n+%d Chips +%d Mult" % [h, b[2], b[3]], "Rune", func(): buy_rune(i)))
	if not gs.shop_card.is_empty():
		var c: Dictionary = gs.shop_card.card
		var cv := CardView.new(c)
		cv.float_amount = 1.0
		grid.add_child(_shop_item(cv, gs.shop_card.cost, "\n".join(Data.card_mods(c)), Data.card_name(c), buy_card))
	if grid.get_child_count() == 0:
		grid.add_child(_label("Sold out!", 28))
	body.add_child(grid)
	var side := VBoxContainer.new()
	side.alignment = BoxContainer.ALIGNMENT_CENTER
	side.add_theme_constant_override("separation", 20)
	side.add_child(_button("Next Round", Data.MULT_COLOR, show_blind_select, Vector2(210, 110), 28))
	var reroll := _button("Reroll $%d" % gs.reroll_cost, Color("3f9a5a"), reroll_shop, Vector2(210, 90), 28)
	reroll.disabled = gs.money < gs.reroll_cost
	side.add_child(reroll)
	body.add_child(side)


func _shop_item(view: Control, cost: int, desc: String, tag: String, cb: Callable) -> Control:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 6)
	col.custom_minimum_size = Vector2(138, 0)
	view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(_center(view))
	col.add_child(_label(tag, 16, Color(1, 1, 1, 0.6)))
	var d := Label.new()
	d.text = desc
	d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	d.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	d.custom_minimum_size = Vector2(138, 92)
	d.add_theme_font_size_override("font_size", 16)
	col.add_child(d)
	var b := _button("$%d" % cost, Color("e0a526"), cb, Vector2(130, 60), 28)
	b.disabled = gs.money < cost
	col.add_child(_center(b))
	return col


func buy_charm(i: int) -> void:
	var d: Dictionary = gs.shop_charms[i]
	if gs.money < d.cost:
		return
	if gs.charms.size() >= gs.charm_slots:
		popup_text(Vector2(main_cx(), TOP_H + 40), "No room for more charms", Color.WHITE, 28)
		return
	gs.money -= d.cost
	gs.charms.append({"id": d.id, "data": {}, "ed": d.get("ed", "")})
	gs.shop_charms.remove_at(i)
	sfx.play("coin")
	rebuild_charms()
	show_shop()


func buy_card() -> void:
	var cost: int = gs.shop_card.cost
	if gs.money < cost:
		return
	gs.money -= cost
	gs.deck.append(gs.shop_card.card)
	gs.shop_card = {}
	sfx.play("coin")
	show_shop()
	popup_text(Vector2(main_cx(), TOP_H + 40), "Added to deck (%d cards)" % gs.deck.size(), Color.WHITE, 30)


func buy_rune(i: int) -> void:
	if gs.money < Data.RUNE_COST:
		return
	var h: String = gs.shop_runes[i]
	gs.money -= Data.RUNE_COST
	gs.hand_levels[h] += 1
	gs.shop_runes.remove_at(i)
	sfx.play("xmult")
	show_shop()
	popup_text(Vector2(main_cx(), TOP_H + 40), "%s  lvl %d" % [h, gs.hand_levels[h]], Color("c9b3ff"), 32)


func reroll_shop() -> void:
	if gs.money < gs.reroll_cost:
		return
	gs.money -= gs.reroll_cost
	gs.reroll_cost += 1
	gs.roll_shop()
	show_shop()


# ---------------------------------------------------------------- modal popups

func open_modal() -> VBoxContainer:
	close_modal()
	modal.mouse_filter = Control.MOUSE_FILTER_STOP
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.6)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.gui_input.connect(func(e):
		if e is InputEventMouseButton and e.pressed:
			close_modal())
	modal.add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	modal.add_child(center)
	var panel := PanelContainer.new()
	var sb := _box(Color("22313b"), 5.0, true)
	sb.set_content_margin_all(26)
	sb.outline = 3.0
	sb.outline_color = Color(1, 1, 1, 0.25)
	panel.add_theme_stylebox_override("panel", sb)
	panel.custom_minimum_size = Vector2(600, 0)
	center.add_child(panel)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 14)
	panel.add_child(vb)
	return vb


func close_modal() -> void:
	for c in modal.get_children():
		c.queue_free()
	modal.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _on_charm_tapped(v: CharmView) -> void:
	var idx := charm_views.find(v)
	if idx < 0:
		return
	var inst: Dictionary = gs.charms[idx]
	var d := Data.charm_def(inst.id)
	if v == drag_view:
		return
	var vb := open_modal()
	vb.add_child(_label(d.name, 40, Data.RARITY_COLORS[d.rarity].lightened(0.4)))
	vb.add_child(_label(Data.RARITY_NAMES[d.rarity], 20, Color(1, 1, 1, 0.6)))
	var desc := _label(Scoring.describe(inst), 26)
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desc.custom_minimum_size = Vector2(540, 0)
	vb.add_child(desc)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 14)
	var sell := _button("Sell $%d" % gs.sell_value(inst), Color("3f9a5a"), func():
		gs.money += gs.sell_value(inst)
		gs.charms.erase(inst)
		charm_views.erase(v)
		v.dissolve()
		sfx.play("coin")
		layout_charms(true)
		update_hud()
		close_modal()
		if _shop_open:
			show_shop(), Vector2(170, 70), 24)
	sell.disabled = busy and in_round
	row.add_child(sell)
	row.add_child(_button("Close", Color("5a5f73"), close_modal, Vector2(150, 70), 24))
	vb.add_child(row)
	vb.add_child(_label("Charms trigger left to right. Drag to reorder.", 18, Color(1, 1, 1, 0.5)))


## Break a card into tumbling shards.
func shatter(v: CardView) -> void:
	sfx.play("lose", 2.2)
	jiggle += 1.0
	var origin := v.position
	var face: Color = Data.ENHANCEMENTS["glass"].face
	for i in 10:
		var shard := Polygon2D.new()
		var c := Vector2(randf() * CardView.W, randf() * CardView.H)
		var pts := PackedVector2Array()
		for k in 3:
			var a := TAU * k / 3.0 + randf()
			pts.append(Vector2(cos(a), sin(a)) * randf_range(10, 22))
		shard.polygon = pts
		shard.color = face if i % 3 else Color(1, 1, 1, 0.9)
		shard.position = origin + c
		shard.z_index = 120
		fx_layer.add_child(shard)
		var dir := (c - Vector2(CardView.W, CardView.H) / 2).normalized()
		var tw := create_tween().set_parallel()
		tw.tween_property(shard, "position", shard.position + dir * randf_range(60, 140) + Vector2(0, 90), 0.6).set_ease(Tween.EASE_IN)
		tw.tween_property(shard, "rotation", randf_range(-4, 4), 0.6)
		tw.tween_property(shard, "modulate:a", 0.0, 0.6).set_delay(0.2)
		tw.chain().tween_callback(shard.queue_free)
	popup_text(origin + Vector2(CardView.W / 2, -24), "Shattered!", Color("bff3ff"), 30)
	v.queue_free()


func show_card_info(v: CardView) -> void:
	if v == drag_view:
		return
	var c := v.card
	var vb := open_modal()
	vb.add_child(_label(Data.card_name(c), 36, Color("ffdf6b")))
	vb.add_child(_label("+%d Chips when scored" % Data.card_chips(c.rank), 24, Data.CHIP_COLOR.lightened(0.3)))
	for line in Data.card_mods(c):
		var l := _label(line, 24)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size = Vector2(540, 0)
		vb.add_child(l)
	if gs.is_debuffed(c):
		vb.add_child(_label("Debuffed by " + gs.boss_hex.name, 22, Color("ff8080")))
	vb.add_child(_center(_button("Close", Color("5a5f73"), close_modal, Vector2(200, 64), 24)))


func show_deck() -> void:
	if gs == null:
		return
	var vb := open_modal()
	var remaining := {}
	for c in gs.draw_pile:
		remaining[c.id] = true
	vb.add_child(_label("Deck: %d cards" % gs.deck.size(), 34, Color("ffdf6b")))
	if in_round:
		vb.add_child(_label("Faded cards have already been drawn this round", 18, Color(1, 1, 1, 0.6)))
	var cards := gs.deck.duplicate()
	cards.sort_custom(func(a, b):
		if a.suit != b.suit:
			return a.suit < b.suit
		return a.rank > b.rank)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(760, mini(ceili(cards.size() / 13.0), 6) * 78)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	var grid := GridContainer.new()
	grid.columns = 13
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 6)
	for c in cards:
		var cell := Control.new()
		cell.custom_minimum_size = Vector2(52, 72)
		cell.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var cv := CardView.new(c)
		cv.float_amount = 0.0
		cv.scale = Vector2(0.5, 0.5)
		cv.pivot_offset = Vector2.ZERO
		cv.mouse_filter = Control.MOUSE_FILTER_IGNORE
		if in_round and not remaining.has(c.id):
			cv.modulate = Color(1, 1, 1, 0.3)
		cell.add_child(cv)
		grid.add_child(cell)
	scroll.add_child(grid)
	vb.add_child(_center(scroll))
	var upgraded := cards.filter(func(c): return c.enh != "" or c.ed != "" or c.seal != "").size()
	vb.add_child(_label("%d upgraded cards. Hold a card in hand to see its details." % upgraded, 18, Color(1, 1, 1, 0.6)))
	vb.add_child(_center(_button("Close", Color("5a5f73"), close_modal, Vector2(200, 60), 24)))


func show_hand_info() -> void:
	if gs == null:
		return
	var vb := open_modal()
	vb.add_child(_label("Poker Hands", 38, Color("ffdf6b")))
	for n in Data.HAND_ORDER:
		var lvl: int = gs.hand_levels[n]
		var hb := HBoxContainer.new()
		hb.add_theme_constant_override("separation", 10)
		var l := _label("lvl %d" % lvl, 22, Color("c9b3ff"), HORIZONTAL_ALIGNMENT_LEFT)
		l.custom_minimum_size = Vector2(70, 0)
		hb.add_child(l)
		var nm := _label(n, 24, Color.WHITE, HORIZONTAL_ALIGNMENT_LEFT)
		nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		hb.add_child(nm)
		var c := _label(str(Data.hand_chips(n, lvl)), 24, Data.CHIP_COLOR.lightened(0.3), HORIZONTAL_ALIGNMENT_RIGHT)
		c.custom_minimum_size = Vector2(70, 0)
		hb.add_child(c)
		hb.add_child(_label("x", 22, Color(1, 1, 1, 0.6)))
		var m := _label(str(Data.hand_mult(n, lvl)), 24, Data.MULT_COLOR.lightened(0.2), HORIZONTAL_ALIGNMENT_LEFT)
		m.custom_minimum_size = Vector2(50, 0)
		hb.add_child(m)
		var p := _label("#%d" % gs.hands_played_count[n], 20, Color(1, 1, 1, 0.5), HORIZONTAL_ALIGNMENT_RIGHT)
		p.custom_minimum_size = Vector2(50, 0)
		hb.add_child(p)
		vb.add_child(hb)
	vb.add_child(_center(_button("Close", Color("5a5f73"), close_modal, Vector2(200, 66), 24)))


# ---------------------------------------------------------------- persistence

func _load_stats() -> void:
	var cf := ConfigFile.new()
	if cf.load(STATS_PATH) != OK:
		return
	for k in stats.keys():
		stats[k] = cf.get_value("stats", k, stats[k])


func _save_stats() -> void:
	var cf := ConfigFile.new()
	for k in stats.keys():
		cf.set_value("stats", k, stats[k])
	cf.save(STATS_PATH)
