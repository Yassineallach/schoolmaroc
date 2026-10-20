extends Control

const MAX_SELECT := 5
const SIDE_W := 340.0  # left sidebar width
const CHARM_H := 160.0
const TOP_H := 180.0
const SPELL_AREA := 230.0  # spell slots, right of the charm row  # charm row; table overlays start below it

var gs: GameState
var sfx: Sfx
var bg_mat: ShaderMaterial

var lbl_blind: Label
var lbl_target: Label
var lbl_reward: Label
var blind_box: Panel
var blind_chip: BlindChip
var side_panel: Panel
var side_box: PixelBox
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
var table_catcher: Control
var charm_bg: Panel
var spell_bg: Panel
var spell_row: Control
var spell_views: Array = []
var lbl_spell_count: Label
var deck_pile: PileView
var discard_pile: PileView
var hand_panel: Panel
var lbl_hand_count: Label
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
const STAT_DEFAULTS := {
	"runs": 0, "wins": 0, "best_ante": 0, "best_hand": 0, "hands_played": 0,
	"cards_played": 0, "money_earned": 0, "charms_bought": 0, "cards_shattered": 0, "spells_cast": 0,
}
var stats := STAT_DEFAULTS.duplicate()
var saves: SaveManager
var profile_data := {}
var settings := {"master": 80.0, "music": 70.0, "sfx": 85.0, "vibration": true, "speed": 1.0, "reduced_motion": false}
var on_title := false
var sidebar_buttons: Array = []
var pad: PadInput
var mascot: Mascot = null
var mascot_layer: Control
var music: Music
var score_ratio := 0.0  # round score / target, drives the sidebar bar
var score_box: Panel
var boss_motes: Motes = null
var debug_boxes: DebugBoxes  # embers drifting up the blind panel during a boss


func _ready() -> void:
	theme = _make_theme()
	sfx = Sfx.new()
	add_child(sfx)
	music = Music.new()
	add_child(music)
	saves = SaveManager.new()
	add_child(saves)
	_load_stats()
	_apply_settings()
	UIBuild.feedback = _ui_feedback
	_build_ui()
	pad = PadInput.new(self)
	add_child(pad)
	debug_boxes = DebugBoxes.new(self)
	add_child(debug_boxes)
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
	return UIBuild.make_button({"button": text, "color": col, "on": cb, "min": min_size, "size": fsize})


## Sound, haptics and juice for every UIBuild button.
func _ui_feedback(event: String, b: Button) -> void:
	match event:
		"press":
			sfx.play("click")
			haptic(12, 0.3)
			juice(b)
			jiggle += 0.5
		"hold_start":
			sfx.play("hold_tick")
		"hold_done":
			haptic(30, 0.6)
			sfx.play("hold_done")


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg_mat = ShaderMaterial.new()
	bg_mat.shader = load("res://shaders/background.gdshader")
	bg.material = bg_mat
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	# Left sidebar: blind, round score, current hand, counters, money
	side_panel = _panel(Vector2(0, 0), Vector2(SIDE_W, 720), Color(0, 0, 0, 0.3))
	side_box = _box(Color(0, 0, 0, 0.3), 0.0)
	side_panel.add_theme_stylebox_override("panel", side_box)
	blind_box = _panel(Vector2(10, 10), Vector2(320, 140), Color("3a7bd5"))
	lbl_blind = _place(_label("", 30), blind_box, Vector2(0, 4), Vector2(320, 38))
	_place(_label("Score at least", 20, Color(1, 1, 1, 0.8)), blind_box, Vector2(0, 40), Vector2(320, 24))
	lbl_target = _place(_label("", 38, Color("ffdf6b")), blind_box, Vector2(0, 62), Vector2(320, 44))
	lbl_reward = _place(_label("", 22, Data.MONEY_COLOR), blind_box, Vector2(0, 104), Vector2(320, 30))
	blind_chip = BlindChip.new(Color.WHITE, 58.0)
	blind_chip.position = Vector2(10, 46)
	blind_chip.pivot_offset = blind_chip.size / 2
	blind_box.add_child(blind_chip)
	# Tap the blind for its details.
	blind_box.mouse_filter = Control.MOUSE_FILTER_STOP
	blind_box.gui_input.connect(func(e):
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT and gs != null:
			juice(blind_chip, 0.25)
			sfx.play("chips", 0.6)
			show_blind_info())

	score_box = _panel(Vector2(10, 160), Vector2(320, 70), Color(0, 0, 0, 0.35))
	_place(_label("Round score", 22, Color(1, 1, 1, 0.8), HORIZONTAL_ALIGNMENT_LEFT), score_box, Vector2(14, 0), Vector2(140, 70))
	lbl_round_score = _place(_label("0", 36, Color.WHITE, HORIZONTAL_ALIGNMENT_RIGHT), score_box, Vector2(140, 0), Vector2(166, 62))
	_place(UIBuild.build({"bar": [self, "score_ratio"], "fill": Data.CHIP_COLOR, "min": Vector2(292, 8)}), score_box, Vector2(14, 56), Vector2(292, 8))

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
	var btn_hands := _place(_button("Hands", Color("5a5f73"), show_hand_info, Vector2(155, 56), 24), self, Vector2(10, 582), Vector2(155, 56))
	var btn_menu := _place(_button("Menu", Color("5a5f73"), show_menu, Vector2(155, 56), 24), self, Vector2(175, 582), Vector2(155, 56))
	btn_deck = _place(_button("Deck", Color("4a4f63"), show_deck, Vector2(320, 48), 22), self, Vector2(10, 650), Vector2(320, 48))
	sidebar_buttons = [btn_hands, btn_menu, btn_deck]

	# Charm row along the top of the table
	charm_bg = _panel(Vector2(SIDE_W + 10, 10), Vector2(900, CHARM_H), Color(0, 0, 0, 0.25))
	charm_row = Control.new()
	charm_row.position = Vector2(SIDE_W + 10, 10)
	add_child(charm_row)
	lbl_charm_count = _place(_label("0/5", 18, Color(1, 1, 1, 0.7), HORIZONTAL_ALIGNMENT_RIGHT), charm_bg, Vector2(0, CHARM_H - 26), Vector2(0, 24))
	spell_bg = _panel(Vector2(0, 10), Vector2(SPELL_AREA, CHARM_H), Color(0.05, 0.25, 0.2, 0.35))
	spell_row = Control.new()
	add_child(spell_row)
	lbl_spell_count = _place(_label("0/2", 18, Color(1, 1, 1, 0.7), HORIZONTAL_ALIGNMENT_RIGHT), spell_bg, Vector2(SPELL_AREA - 120, CHARM_H - 26), Vector2(110, 24))

	hand_panel = _panel(Vector2.ZERO, Vector2.ONE, Color(0, 0, 0, 0.14))
	lbl_hand_count = _place(_label("", 18, Color(1, 1, 1, 0.6), HORIZONTAL_ALIGNMENT_LEFT), hand_panel, Vector2(12, 0), Vector2(160, 24))
	deck_pile = PileView.new(false)
	deck_pile.tapped.connect(show_deck)
	add_child(deck_pile)
	discard_pile = PileView.new(true)
	add_child(discard_pile)

	# Tapping empty table space clears the selection.
	table_catcher = Control.new()
	table_catcher.mouse_filter = Control.MOUSE_FILTER_STOP
	table_catcher.gui_input.connect(func(e):
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			deselect_all())
	add_child(table_catcher)

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
	mascot_layer = Control.new()
	mascot_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(mascot_layer)
	modal = Control.new()
	modal.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(modal)
	# Cards use z_index for fanning and dragging; keep popups above them.
	fx_layer.z_index = 300
	overlay.z_index = 350
	mascot_layer.z_index = 380
	modal.z_index = 400


func _on_resize() -> void:
	var s := get_viewport_rect().size
	vw = s.x
	vh = s.y
	bg_mat.set_shader_parameter("aspect", vw / vh)
	var mw := main_w()
	charm_bg.size = Vector2(mw - 30 - SPELL_AREA, CHARM_H)
	charm_row.size = charm_bg.size
	spell_bg.position = Vector2(vw - 10 - SPELL_AREA, 10)
	spell_row.position = spell_bg.position
	spell_row.size = spell_bg.size
	hand_panel.position = Vector2(SIDE_W + 10, hand_y() - 46)
	hand_panel.size = Vector2(mw - 20, CardView.H + 58)
	lbl_hand_count.position = Vector2(12, hand_panel.size.y - 26)
	deck_pile.position = Vector2(vw - PileView.W - 18, play_y())
	discard_pile.position = Vector2(SIDE_W + 18, play_y())
	if gs != null:
		rebuild_spells()
	lbl_charm_count.position = Vector2(charm_bg.size.x - 120, CHARM_H - 26)
	lbl_charm_count.size = Vector2(110, 24)
	# between the two piles, so taps on them still reach them
	table_catcher.position = Vector2(SIDE_W + PileView.W + 30, TOP_H)
	table_catcher.size = Vector2(mw - 2 * (PileView.W + 30), vh - TOP_H - 104)
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
	if Anim.calm:
		return
	node.pivot_offset = node.size / 2
	var tw := create_tween().set_parallel()
	node.scale = Vector2.ONE * (1.0 + amount)
	tw.tween_property(node, "scale", Vector2.ONE, 0.35).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	var g := Glide.on(node)
	if g != null:
		g.kick(amount)
		return
	node.rotation_degrees = randf_range(-3.0, 3.0)
	tw.tween_property(node, "rotation_degrees", 0.0, 0.3).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)


## Small screen shake that decays every frame.
func _process(delta: float) -> void:
	if jiggle > 0.0 and Anim.calm:
		jiggle = 0.0
	if jiggle > 0.0:
		jiggle = maxf(0.0, jiggle - delta * 4.0)
		position = Vector2(randf_range(-1, 1), randf_range(-1, 1)) * jiggle * 4.0
	elif position != Vector2.ZERO:
		position = Vector2.ZERO


# ---------------------------------------------------------------- HUD

func update_hud() -> void:
	# Ambience: a quiet table bed, with a low drone under boss rounds.
	var boss_bed := gs != null and in_round and gs.hex() != ""
	sfx.set_ambient("ambient_table", 0.25 if boss_bed else 0.55)
	sfx.set_ambient("ambient_boss", 0.6 if boss_bed else 0.0)
	_set_boss_motes(boss_bed)
	if gs == null:
		return
	lbl_ante.text = "Ante %d/%d" % [gs.ante, Data.FINAL_ANTE]
	lbl_money.text = "$%d" % gs.money
	lbl_hands.text = str(gs.hands_left)
	lbl_discards.text = str(gs.discards_left)
	lbl_round_score.text = Data.fmt(gs.round_score)
	score_ratio = float(gs.round_score) / float(maxi(gs.target, 1)) if in_round else 0.0
	btn_deck.text = "Deck %d/%d" % [gs.draw_pile.size() if in_round else gs.deck.size(), gs.deck.size()]
	lbl_charm_count.text = "%d/%d" % [gs.charms.size(), gs.charm_slots]
	lbl_spell_count.text = "%d/%d" % [gs.spells.size(), gs.spell_slots]
	lbl_hand_count.text = "Hand %d/%d" % [hand_views.size(), gs.current_hand_size()] if in_round else ""
	deck_pile.visible = true
	discard_pile.visible = true
	deck_pile.set_count(gs.draw_pile.size() if in_round else gs.deck.size(), gs.deck.size())
	var shown_idx := gs.blind_idx
	lbl_blind.text = gs.blind_name(shown_idx)
	lbl_target.text = Data.fmt(gs.blind_target(shown_idx) if not in_round else gs.target)
	lbl_reward.text = "Reward: " + "$".repeat(gs.blind_reward(shown_idx))
	blind_box.add_theme_stylebox_override("panel", _box(gs.blind_color(shown_idx), 3.0, true))
	blind_chip.color = gs.blind_color(shown_idx).lightened(0.3)
	var boss := gs.blind_idx == 2
	# The sidebar takes on the colour of the blind being faced.
	var tint := Color(gs.blind_color(shown_idx).darkened(0.72), 0.55)
	if not side_box.color.is_equal_approx(tint) and not side_panel.has_meta("tinting"):
		side_panel.set_meta("tinting", true)
		var tw := create_tween()
		tw.tween_method(func(c):
			side_box.color = c
			side_panel.queue_redraw(), side_box.color, tint, 0.5)
		tw.tween_callback(func(): side_panel.remove_meta("tinting"))
	bg_mat.set_shader_parameter("base_a", gs.boss_hex.color.darkened(0.45) if boss else Color(0.09, 0.30, 0.22))
	bg_mat.set_shader_parameter("base_b", gs.boss_hex.color.darkened(0.8) if boss else Color(0.04, 0.15, 0.12))
	btn_play.disabled = busy or not in_round or selected_views().is_empty()
	btn_discard.disabled = busy or not in_round or selected_views().is_empty() or gs.discards_left <= 0
	update_preview()


## Embers rise through the blind panel while a boss is in play.
func _set_boss_motes(on: bool) -> void:
	if on and boss_motes == null:
		boss_motes = Motes.new()
		boss_motes.position = blind_box.size / 2
		boss_motes.area = blind_box.size - Vector2(16, 16)
		var col: Color = gs.boss_hex.color
		boss_motes.colors = [col.lightened(0.35), col.lightened(0.6), Color(1, 1, 1, 0.7)]
		boss_motes.rate = 0.09
		boss_motes.speed = 26.0
		boss_motes.spread = 0.9
		boss_motes.drag = 0.4
		boss_motes.size = 5.0
		boss_motes.life = 1.6
		boss_motes.spin = 1.5
		blind_box.add_child(boss_motes)
		blind_box.move_child(boss_motes, 0)  # behind the labels, above the panel
		boss_motes.prewarm(1.6)
	elif not on and boss_motes != null:
		boss_motes.fade_out(0.5)
		boss_motes = null


func update_preview() -> void:
	if busy or not in_round:
		return
	var sel := selected_views()
	if sel.is_empty():
		lbl_hand_name.text = ""
		lbl_chips.text = "0"
		lbl_mult.text = "0"
		return
	var cards := sel.map(func(v): return v.card)
	var ev := Poker.evaluate(cards)
	var lvl: int = gs.hand_levels[ev.name]
	lbl_hand_name.text = "%s  lvl %d" % [ev.name, lvl]
	if gs.hand_blocked(ev, cards) != "":
		lbl_hand_name.text = "%s  (not allowed)" % ev.name
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
		v.locked = gs.charms[i].get("locked", false)
		v.tapped.connect(_on_charm_tapped)
		v.held.connect(_on_charm_tapped)
		v.drag_started.connect(_on_drag_start)
		v.dragged.connect(_on_drag_move)
		v.drag_ended.connect(_on_drag_end)
		UIBuild.attach_tooltip(v, func(): return _charm_tip(v), false)
		charm_row.add_child(v)
		charm_views.append(v)
	layout_charms(false)
	refresh_charm_states()
	update_hud()


## Hover text for a charm in the row; nothing while the boss hides it.
func _charm_tip(v: CharmView) -> Dictionary:
	if not v.face_up or drag_view != null:
		return {}
	var inst := _charm_inst(v)
	var d := Data.charm_def(inst.id)
	var lines: Array = [d.desc]
	if inst.get("ed", "") != "":
		lines.append("%s: %s" % [Data.EDITIONS[inst.ed].name, Data.EDITIONS[inst.ed].desc])
	if v.smothered:
		lines.append("Disabled by the boss")
	return {"title": d.name, "lines": lines}


## Show which charms the boss has disabled or hidden.
func refresh_charm_states() -> void:
	for i in charm_views.size():
		var v: CharmView = charm_views[i]
		v.smothered = gs != null and in_round and gs.charm_disabled(i)
		var hidden := gs != null and in_round and gs.hex() == "eclipse"
		if hidden:
			v.face_up = false
		elif not v.face_up:
			v.flip_up(0.05 * i)
		v.queue_redraw()


func rebuild_spells() -> void:
	for v in spell_views:
		v.queue_free()
	spell_views = []
	if gs == null:
		return
	for i in gs.spells.size():
		var v := SpellView.new(gs.spells[i])
		v.position = Vector2(12 + i * (SpellView.W + 14), (CHARM_H - SpellView.H) / 2.0 - 6)
		v.tapped.connect(show_spell)
		spell_row.add_child(v)
		spell_views.append(v)
	update_hud()


func show_spell(v: SpellView) -> void:
	var d := Data.spell_def(v.spell_id)
	var targets: Array = selected_views().map(func(h): return h.card)
	var why := gs.spell_blocked(v.spell_id, targets, in_round)
	var vb := open_modal()
	vb.add_child(_label(d.name, 40, Color("9fe3cf")))
	vb.add_child(_label("Spell", 20, Color(1, 1, 1, 0.6)))
	var desc := _label(d.desc, 26)
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desc.custom_minimum_size = Vector2(520, 0)
	vb.add_child(desc)
	if why != "":
		vb.add_child(_label(why, 20, Color("ffb37a")))
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 14)
	var use := _button("Cast", Data.SPELL_COLOR, func():
		close_modal()
		cast_spell(v), Vector2(170, 70), 26)
	use.disabled = why != "" or (busy and in_round)
	row.add_child(use)
	row.add_child(_button("Sell $1", Color("3f9a5a"), func():
		gs.money += 1
		gs.spells.erase(v.spell_id)
		sfx.play("charm_sell")
		close_modal()
		rebuild_spells()
		if _shop_open:
			show_shop(), Vector2(150, 70), 24))
	row.add_child(_button("Close", Color("5a5f73"), close_modal, Vector2(150, 70), 24))
	vb.add_child(row)
	vb.add_child(_label("Select cards in your hand first, then cast.", 18, Color(1, 1, 1, 0.5)))


## Cast a spell on the selected cards with a flourish.
func cast_spell(v: SpellView) -> void:
	var sel := selected_views()
	var targets: Array = sel.map(func(h): return h.card)
	if gs.spell_blocked(v.spell_id, targets, in_round) != "":
		return
	busy = true
	var id := v.spell_id
	stats.spells_cast += 1
	spell_views.erase(v)
	var tw := create_tween().set_parallel()
	tw.tween_property(v, "global_position", Vector2(main_cx(), play_y()) - v.size / 2, 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(v, "scale", Vector2(1.4, 1.4), 0.3)
	sfx.play("spell_cast")
	await tw.finished
	await wait(0.15)
	var before_money := gs.money
	var removed := gs.cast_spell(id, targets)
	var vt := create_tween()
	vt.tween_property(v, "modulate:a", 0.0, 0.25)
	vt.tween_callback(v.queue_free)
	for h in sel:
		if removed.has(h.card):
			hand_views.erase(h)
			h.dissolve()
		else:
			h.selected = false
			h.flip_up(0.0)
			juice(h, 0.2)
	if gs.money != before_money:
		popup_text(Vector2(main_cx(), play_y()), "+$%d" % (gs.money - before_money), Data.MONEY_COLOR, 40)
		sfx.play("coin_cascade")
	haptic(30, 0.5)
	jiggle += 0.8
	await wait(0.4)
	gs.hand = hand_views.map(func(h): return h.card)
	rebuild_spells()
	layout_hand(true)
	if in_round:
		busy = false
		update_hud()
		save_run("round")
	elif _shop_open:
		show_shop()


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
			Glide.of(v).to(target, 0.0)
		else:
			Glide.of(v).snap(target, 0.0)


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
	# grab offset in the parent's unrotated space, so a tilted card doesn't jump
	_drag_grab = pos - (v.get_parent() as Control).get_global_transform() * v.position
	v.z_index = 200
	juice(v, 0.08)


func _on_drag_move(v: Control, pos: Vector2) -> void:
	if v != drag_view:
		return
	var parent := v.get_parent() as Control
	Glide.of(v).to(parent.get_global_transform().affine_inverse() * (pos - _drag_grab), 0.0, 0.0, Glide.SNAPPY)
	var list := _drag_list(v)
	var cx := pos.x - _drag_grab.x + v.size.x / 2  # where the card is headed
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
		save_run("round")
	else:
		gs.charms = charm_views.map(func(c): return _charm_inst(c))
		layout_charms(true)
	sfx.play("card_place", 1.2, 0.7)


func _charm_inst(v: CharmView) -> Dictionary:
	return v.get_meta("inst")


## A burst of motes at `pos` (fx layer space).
func motes(pos: Vector2, palette: Array, n: int, cfg := {}) -> Motes:
	return Motes.pop(fx_layer, pos, palette, n, cfg)


## The centre of `c` in fx layer space.
func fx_center(c: Control) -> Vector2:
	return fx_layer.get_global_transform().affine_inverse() * c.get_global_rect().get_center()


## Small, quick sparks for each scoring step.
func score_motes(pos: Vector2, col: Color, n := 6) -> void:
	motes(pos, [col, col.lightened(0.4)], n, {"speed": 110.0, "size": 7.0, "life": 0.5, "drag": 3.0})


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
	tw.tween_property(node, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	var g := Glide.on(node)
	if g != null:
		g.kick((amount - 1.0) * 0.6)
	elif not Anim.calm:
		tw.parallel().tween_property(node, "rotation_degrees", randf_range(-4.0, 4.0), 0.07)
		tw.tween_property(node, "rotation_degrees", 0.0, 0.25).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)


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
	dismiss_ace()
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
	on_title = true
	sfx.set_ambient("ambient_table", 0.55)
	sfx.set_ambient("ambient_boss", 0.0)
	music.set_track("table")
	music.pitch_target = 1.0
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
	var main_row := HBoxContainer.new()
	main_row.alignment = BoxContainer.ALIGNMENT_CENTER
	main_row.add_theme_constant_override("separation", 18)
	if saves.has_run():
		var run := saves.load_run()
		main_row.add_child(_button("Continue\nAnte %d  $%d" % [run.get("ante", 1), run.get("money", 0)], Color("3f9a5a"), resume_run, Vector2(300, 96), 28))
		main_row.add_child(_hold_button("Hold: New Run", Data.CHIP_COLOR, new_run, 0.6, Vector2(300, 96)))
	else:
		main_row.add_child(_button("Play", Data.CHIP_COLOR, new_run, Vector2(320, 96), 40))
	vb.add_child(main_row)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 14)
	row.add_child(_button("How to play", Color("5a5f73"), show_help, Vector2(200, 64), 24))
	row.add_child(_button("Collection", Color("5a5f73"), show_collection, Vector2(200, 64), 24))
	row.add_child(_button("Challenges", Color("b3364e"), show_challenges, Vector2(200, 64), 24))
	row.add_child(_button("Profile %d" % saves.profile, Color("7b4fa0"), func():
		saves.profile = saves.profile % SaveManager.PROFILES + 1
		saves.save_settings(settings)
		_load_profile()
		show_title(), Vector2(200, 64), 24))
	vb.add_child(row)
	var idle := summon_ace(Vector2(vw - Mascot.W - 60, vh - Mascot.H - 50))
	idle.poked.connect(func():
		if not idle.talking:
			idle.say(TIPS.pick_random(), [["Thanks!", func(): idle.say_hide()]]))
	if stats.runs > 0:
		vb.add_child(_label("Best ante: %d   Best hand: %s   Wins: %d" % [stats.best_ante, Data.fmt(stats.best_hand), stats.wins], 20, Color(1, 1, 1, 0.7)))


func show_help() -> void:
	var vb := open_modal()
	vb.add_child(_label("How to play", 40, Color("ffdf6b")))
	var t := Label.new()
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	t.custom_minimum_size = Vector2(820, 0)
	t.add_theme_font_size_override("font_size", 23)
	t.text = "Select up to 5 cards and play a poker hand. Each hand type has base Chips and Mult; scored cards add their rank in Chips (faces 10, Aces 11).\n\nScore = Chips x Mult. Reach the blind's target before you run out of hands. Discards let you swap cards.\n\nEach ante has a Small Blind, a Big Blind and a Boss Blind with a nasty twist. Beat ante %d to win.\n\nSpend money in the shop on Charms (passive bonuses, up to 5) and Runes (level up a hand type). You earn $1 interest per $5 held, up to $5.\n\nDrag cards or charms to reorder them; hold a card to see its details. Gamepad: d-pad moves, A selects (hold A + left/right to move a card), X plays, Y discards, LB/RB sort, Start opens the menu. Keyboard: arrows, Enter, P, D, Q/E, Esc; hold R to restart." % Data.FINAL_ANTE
	vb.add_child(t)
	vb.add_child(_center(_button("Close", Color("5a5f73"), close_modal, Vector2(220, 70))))


func _center(c: Control) -> Control:
	c.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	return c


func new_run(challenge_id: String = "") -> void:
	on_title = false
	music.pitch_target = 1.0
	gs = GameState.new()
	if challenge_id != "":
		gs.apply_challenge(challenge_id)
		toast("Challenge: " + Data.challenge_def(challenge_id).name)
	stats.runs += 1
	_save_stats()
	saves.delete_run()
	clear_hand_views()
	rebuild_charms()
	rebuild_spells()
	discard_pile.clear()
	lbl_hand_name.text = ""
	lbl_chips.text = "0"
	lbl_mult.text = "0"
	show_blind_select()


func show_blind_select() -> void:
	music.set_track("boss" if gs.blind_idx == 2 else "table")
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
		if i == 2 and gs.is_showdown(2):
			inner.add_child(_label("SHOWDOWN", 18, Color("ffdf6b")))
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
	discover("hex", gs.boss_hex.id)
	save_run("blind")
	if gs.blind_idx == 2:
		tutorial("boss", "That's a boss blind! Bosses bend the rules. Tap the blind panel at the top left any time to read what this one does.")
	else:
		tutorial("welcome", "Hi, I'm Ace! Each ante has three blinds. Score at least the target before your hands run out to beat one and earn money.")


# ---------------------------------------------------------------- round flow

func start_blind() -> void:
	dismiss_ace()
	clear_overlay()
	_shop_open = false
	gs.start_round()
	in_round = true
	busy = true
	lbl_hand_name.text = gs.blind_name()
	lbl_chips.text = "0"
	lbl_mult.text = "0"
	update_hud()
	rebuild_charms()
	if gs.blind_idx != 2:
		popup_text(Vector2(main_cx(), play_y() + 60), gs.blind_name(), Color.WHITE, 44)
	discard_pile.clear()
	deck_pile.shuffle()
	for i in 3:
		if i == 0: sfx.play("shuffle")
	await wait(0.5)
	await deal()
	if gs.hex() != "":
		await announce_boss()
	busy = false
	update_hud()
	save_run("round")
	tutorial("hand", "Tap up to 5 cards to make a poker hand, then press Play Hand. Your score is Chips x Mult, so stronger hands score more.")


## Fly a card onto the discard heap, then drop its view.
func send_to_discard(v: CardView, delay := 0.0) -> void:
	v.z_index = 60
	Glide.of(v).to(discard_pile.card_target() + Vector2(randf_range(-6, 6), randf_range(-6, 6)), randf_range(-25, 25), delay)
	var tw := create_tween()
	tw.tween_interval(delay)
	tw.tween_property(v, "scale", Vector2(PileView.W / CardView.W, PileView.W / CardView.W), 0.28)
	tw.tween_callback(func():
		discard_pile.add(v.card)
		v.queue_free())


func clear_hand_views() -> void:
	for v in hand_views:
		v.queue_free()
	hand_views = []
	drag_view = null
	manual_order = false


func _make_hand_view(c: Dictionary) -> CardView:
	var v := CardView.new(c)
	v.set_debuffed(gs.is_debuffed(c))
	v.position = deck_pile.card_target()
	v.rotation_degrees = -8
	v.face_up = false
	v.tapped.connect(_on_card_tapped)
	v.held.connect(show_card_info)
	v.drag_started.connect(_on_drag_start)
	v.dragged.connect(_on_drag_move)
	v.drag_ended.connect(_on_drag_end)
	hand_layer.add_child(v)
	hand_views.append(v)
	return v


func deal() -> void:
	var drawn := gs.draw_cards()
	for c in drawn:
		_make_hand_view(c)
	if not manual_order:
		sort_hand()
	gs.hand = hand_views.map(func(h): return h.card)
	for i in drawn.size():
		sfx.play("card_slide", 0.95 + 0.04 * i, 0.8)
	layout_hand(true)
	update_hud()
	for c in drawn:
		if gs.draws_face_down(c):
			gs.boss_state.down.append(c.id)
	var k := 0
	for v in hand_views:
		if not v.face_up and not gs.boss_state.get("down", []).has(v.card.id):
			v.flip_up(0.15 + 0.05 * k)
			k += 1
	if k > 0:
		get_tree().create_timer(0.2).timeout.connect(func(): sfx.play("card_flip", 1.0, 0.7))
	await wait(0.35 + 0.05 * k)
	ensure_forced()
	if in_round and hand_views.any(func(v): return v.card.enh != "" or v.card.ed != "" or v.card.seal != ""):
		tutorial("upgrade", "Ooh, an upgraded card! Press and hold any card to see what it does.")


## The Lantern keeps one card selected at all times.
func ensure_forced() -> void:
	if gs.hex() != "lantern" or hand_views.is_empty():
		return
	var forced: int = gs.boss_state.get("forced", -1)
	if hand_views.any(func(v): return v.card.id == forced):
		return
	var v: CardView = hand_views[gs.rng.randi_range(0, hand_views.size() - 1)]
	gs.boss_state.forced = v.card.id
	if not v.selected:
		var sel := selected_views()
		if sel.size() >= MAX_SELECT:
			sel[0].selected = false
			sel[0].queue_redraw()
		v.selected = true
		v.queue_redraw()
	juice(v, 0.15)
	layout_hand(true)
	update_hud()


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
			Glide.of(v).to(target, rot)
		else:
			Glide.of(v).snap(target, rot)


func selected_views() -> Array:
	return hand_views.filter(func(v): return v.selected)


func _on_card_tapped(v: CardView) -> void:
	if busy or not in_round or not hand_views.has(v):
		return
	if v.selected and v.card.id == gs.boss_state.get("forced", -1) and gs.hex() == "lantern":
		juice(blind_chip, 0.2)
		popup_text(v.position + Vector2(CardView.W / 2, -24), "Held by the Lantern", Color("9fdcff"), 22)
		return
	if not v.selected and selected_views().size() >= MAX_SELECT:
		return
	v.selected = not v.selected
	v.queue_redraw()
	sfx.play("card_select" if v.selected else "card_deselect")
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
	stats.hands_played += 1
	stats.cards_played += sel.size()
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
		Glide.of(v).to(Vector2(x0 + i * gap, play_y()), 0.0, 0.03 * i)
	sfx.play("card_place")
	layout_hand(true)
	await wait(0.3)

	# Face-down cards turn over once played.
	var revealed := false
	for v in sel:
		if gs.boss_state.get("down", []).has(v.card.id):
			gs.boss_state.down.erase(v.card.id)
			v.flip_up(0.0)
			revealed = true
	if revealed:
		await wait(0.25)

	var played: Array = sel.map(func(v): return v.card)
	var ev := Poker.evaluate(played)
	gs.hands_played_count[ev.name] += 1
	for c in gs.charms:
		if c.id == "snowball":
			c.data.m = c.data.get("m", 0) + 1
	var blocked := gs.hand_blocked(ev, played)
	if gs.rules.get("played_debuffed", false):
		for c in played:
			if not gs.played_this_ante.has(c.id):
				gs.played_this_ante.append(c.id)
	var result := {"events": [], "shatter": []}
	if blocked != "":
		juice(blind_chip, 0.3)
		sfx.play("not_allowed")
		haptic(40, 0.5)
		await banner("Not allowed!", blocked, gs.boss_hex.color)
	else:
		for note in gs.on_hand_played(ev, played):
			juice(blind_chip, 0.2)
			popup_text(Vector2(main_cx(), play_y() - 30), note, gs.boss_hex.color.lightened(0.45), 28)
			sfx.play("boss_ping", 1.0, 0.8)
			await wait(0.5)
		refresh_charm_states()
		update_hud()
		result = Scoring.compute(gs, played, ev, hand_views.map(func(v): return v.card))
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
	music.pitch_target = 1.03
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
			sfx.play("again")
		var line := 0
		if e.has("chips"):
			chips += e.chips
			lbl_chips.text = Data.fmt(chips)
			bump(lbl_chips.get_parent(), 1.08)
			popup_text(anchor, "+%d" % e.chips, Data.CHIP_COLOR.lightened(0.2))
			score_motes(anchor, Data.CHIP_COLOR)
			sfx.play("chips", pitch)
			line += 1
		if e.has("mult"):
			mult += e.mult
			lbl_mult.text = _fmt_mult(mult)
			bump(lbl_mult.get_parent(), 1.08)
			popup_text(anchor + Vector2(0, 36 * line), "+%d Mult" % e.mult, Data.MULT_COLOR)
			score_motes(anchor + Vector2(0, 36 * line), Data.MULT_COLOR)
			sfx.play("mult", pitch)
			line += 1
		if e.has("xmult"):
			mult *= e.xmult
			lbl_mult.text = _fmt_mult(mult)
			bump(lbl_mult.get_parent(), 1.08)
			popup_text(anchor + Vector2(0, 36 * line), "x%s Mult" % str(e.xmult).trim_suffix(".0"), Data.XMULT_COLOR)
			score_motes(anchor + Vector2(0, 36 * line), Data.XMULT_COLOR, 12)
			sfx.play("xmult", pitch)
			line += 1
		if e.has("money"):
			gs.money += e.money
			stats.money_earned += e.money
			update_hud()
			bump(lbl_money, 1.2)
			popup_text(anchor + Vector2(0, 36 * line), "$%d" % e.money, Data.MONEY_COLOR)
			score_motes(anchor + Vector2(0, 36 * line), Data.MONEY_COLOR, 8)
			sfx.play("coin", pitch)
		pitch += 0.04
		await wait(step_t)

	music.pitch_target = 1.0
	var total := int(floor(chips * mult))
	gs.best_hand = maxi(gs.best_hand, total)
	if total > stats.best_hand:
		stats.best_hand = total
		_save_stats()
	lbl_hand_name.text = Data.fmt(total)
	bump(lbl_hand_name, 1.3)
	sfx.play("score_total")
	await wait(0.45)
	var from := gs.round_score
	gs.round_score += total
	var tw := create_tween()
	tw.tween_method(func(x):
		if lbl_round_score.text != Data.fmt(x) and randf() < 0.25:
			sfx.play("tally", 1.0, 0.5)
		score_ratio = float(x) / float(maxi(gs.target, 1))
		lbl_round_score.text = Data.fmt(x), from, gs.round_score, 0.4)
	await wait(0.5)

	# Glass cards that broke leave the deck for good.
	for c in result.shatter:
		stats.cards_shattered += 1
		var v: CardView = view_of[c.id]
		sel.erase(v)
		gs.remove_from_deck(c)
		shatter(v)
	if not result.shatter.is_empty():
		await wait(0.4)
	# Clear played cards.
	for i in sel.size():
		send_to_discard(sel[i], i * 0.05)
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
			send_to_discard(v)
		popup_text(Vector2(main_cx(), play_y() + 60), "The Grip!", gs.boss_hex.color.lightened(0.3), 36)
		gs.hand = hand_views.map(func(v): return v.card)
		await wait(0.3)
	lbl_hand_name.text = ""
	await deal()
	busy = false
	update_hud()
	save_run("round")
	tutorial("discard", "Not every hand is a winner. Discard swaps cards for new ones. Keep an eye on your Hands and Discards on the left.")


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
	var cost: int = gs.rules.get("discard_cost", 0)
	if gs.money < cost:
		popup_text(Vector2(main_cx(), play_y() + 60), "Discarding costs $%d" % cost, Color.WHITE, 28)
		return
	busy = true
	gs.discards_left -= 1
	if cost > 0:
		gs.money -= cost
		popup_text(Vector2(main_cx(), play_y() + 60), "-$%d" % cost, Data.MONEY_COLOR, 32)
	sfx.play("discard")
	for i in sel.size():
		var v: CardView = sel[i]
		hand_views.erase(v)
		send_to_discard(v, i * 0.04)
	gs.hand = hand_views.map(func(v): return v.card)
	update_hud()
	await wait(0.25)
	await deal()
	busy = false
	update_hud()
	save_run("round")


func win_round() -> void:
	in_round = false
	sfx.play("round_win")
	haptic(40, 0.5)
	motes(fx_center(score_box), [Data.MONEY_COLOR, Color("fff1b8"), Data.CHIP_COLOR.lightened(0.3)], 34,
		{"area": score_box.size * Vector2(0.8, 0.4), "speed": 260.0, "spread": 1.6, "gravity": Vector2(0, 380), "life": 1.1, "drag": 0.8})
	refresh_charm_states()
	await defeat_blind()
	var gilded := 0
	for v in hand_views:
		if v.card.get("enh", "") == "gilded" and not gs.is_debuffed(v.card):
			gilded += 3
	for i in hand_views.size():
		send_to_discard(hand_views[i], i * 0.03)
	hand_views = []
	clear_hand_views()
	lbl_hand_name.text = ""
	var reward := gs.blind_reward()
	var per_hand := 0 if gs.rules.get("no_hand_money", false) else gs.hands_left
	var interest := gs.interest()
	var charm_cash := 0
	for c in gs.charms:
		if c.id == "gold":
			charm_cash += 4
	var rows := [["Blind reward", reward]]
	if per_hand > 0:
		rows.append(["Remaining hands (%d)" % per_hand, per_hand])
	if interest > 0:
		rows.append(["Interest ($1 per $5)", interest])
	if charm_cash > 0:
		rows.append(["Gold Tooth", charm_cash])
	if gilded > 0:
		rows.append(["Gilded cards held", gilded])
	var info := {"title": gs.blind_name() + " defeated!", "rows": rows, "total": reward + per_hand + interest + charm_cash + gilded}
	save_run("cashout", {"cashout": info})
	show_cashout(info)


func show_cashout(info: Dictionary) -> void:
	in_round = false
	busy = true
	music.set_track("boss" if gs.blind_idx == 2 else "table")
	var vb := open_overlay()
	vb.add_child(_label(info.title, 38, Color("ffdf6b")))
	for r in info.rows:
		_row_label(vb, r[0], "$%d" % r[1])
	var total: int = info.total
	vb.add_child(_center(_button("Cash Out: $%d" % total, Color("e0a526"), func():
		gs.money += total
		stats.money_earned += total
		sfx.play("cash_register")
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
	sfx.play("game_over")
	haptic(150, 0.8)
	music.set_track("table")
	music.pitch_target = 0.85
	saves.delete_run()
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
	ace_quip(["So close! Every run teaches something.", "Ouch. Want to deal again?", "The cards weren't with us this time.", "Shake it off, the next deck is lucky!"])
	vb.add_child(UIBuild.build({"col": [
		{"button": "New Run", "color": Data.CHIP_COLOR, "on": new_run, "min": Vector2(320, 90), "size": 34, "delay": 1.0, "once": true},
		{"button": "Main Menu", "color": Color("5a5f73"), "on": show_title, "min": Vector2(320, 70), "size": 26, "delay": 1.0, "once": true},
	]}))


func show_victory() -> void:
	busy = true
	sfx.play("victory")
	if gs.challenge != "":
		if not profile_data.has("challenges_won"):
			profile_data.challenges_won = []
		if not profile_data.challenges_won.has(gs.challenge):
			profile_data.challenges_won.append(gs.challenge)
			_save_stats()
		toast("Challenge complete: " + Data.challenge_def(gs.challenge).name)
	saves.delete_run()
	music.set_track("shop")
	var vb := open_overlay(true)
	vb.add_child(_label("You Win!", 72, Color("ffdf6b")))
	vb.add_child(_label("You beat ante %d." % Data.FINAL_ANTE, 28))
	_row_label(vb, "Best hand", Data.fmt(gs.best_hand), Data.CHIP_COLOR.lightened(0.3))
	ace_quip(["We did it! I knew you had it in you!", "Champion! Fancy seeing how far Endless goes?"])
	_confetti()
	vb.add_child(_center(_button("Endless Mode", Color("7b4fa0"), func():
		gs.endless = true
		open_shop(), Vector2(340, 84), 30)))
	vb.add_child(_center(_button("New Run", Data.CHIP_COLOR, new_run, Vector2(340, 84), 30)))


## Waves of confetti falling across the screen.
func _confetti() -> void:
	var palette := [Data.CHIP_COLOR, Data.MULT_COLOR, Data.MONEY_COLOR, Color("3f9a5a"), Color("b07cff"), Color.WHITE]
	for wave in 3:
		motes(Vector2(vw / 2, -20), palette, 50, {"area": Vector2(vw, 10), "heading": PI / 2, "spread": 0.8, "speed": 140.0,
			"gravity": Vector2(0, 120), "drag": 0.6, "life": 3.2, "size": 11.0, "spin": 6.0, "cap": 60})
		await wait(0.6)


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
	music.set_track("shop")
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
		grid.add_child(_shop_item(CharmView.new(d.id, "", d.get("ed", "")), gs.price(d.cost), desc, Data.RARITY_NAMES[d.rarity], func(): buy_charm(i)))
	for i in gs.shop_runes.size():
		var h: String = gs.shop_runes[i]
		var b: Array = Data.HAND_BASE[h]
		grid.add_child(_shop_item(CharmView.new("", h), gs.price(Data.RUNE_COST), "Level up %s\n+%d Chips +%d Mult" % [h, b[2], b[3]], "Rune", func(): buy_rune(i)))
	for i in gs.shop_spells.size():
		var sd := Data.spell_def(gs.shop_spells[i])
		grid.add_child(_shop_item(SpellView.new(sd.id), gs.price(Data.SPELL_COST), sd.desc, "Spell", func(): buy_spell(i)))
	if not gs.shop_card.is_empty():
		var c: Dictionary = gs.shop_card.card
		var cv := CardView.new(c)
		cv.float_amount = 1.0
		grid.add_child(_shop_item(cv, gs.price(gs.shop_card.cost), "\n".join(Data.card_mods(c)), Data.card_name(c), buy_card))
	if grid.get_child_count() == 0:
		grid.add_child(_label("Sold out!", 28))
	body.add_child(grid)
	var side := VBoxContainer.new()
	side.alignment = BoxContainer.ALIGNMENT_CENTER
	side.add_theme_constant_override("separation", 20)
	side.add_child(_button("Next Round", Data.MULT_COLOR, show_blind_select, Vector2(210, 110), 28))
	side.add_child(UIBuild.build({"button": "Reroll $%d" % gs.price(gs.reroll_cost), "color": Color("3f9a5a"), "on": reroll_shop,
		"min": Vector2(210, 90), "enabled": func(): return gs.money >= gs.price(gs.reroll_cost)}))
	body.add_child(side)
	for d in gs.shop_charms:
		discover("charm", d.id)
	save_run("shop")
	tutorial("shop", "Welcome to the shop! Charms give a bonus every hand and Runes level up a hand type. Drag your charms to change the order they trigger in.")


func _shop_item(view: Control, cost: int, desc: String, tag: String, cb: Callable) -> Control:
	view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var col := UIBuild.build({"col": [
		{"node": _center(view)},
		{"text": tag, "size": 16, "color": Color(1, 1, 1, 0.6), "fit": 138},
		{"text": desc, "size": 16, "wrap": 138, "lines": 4, "id": "desc", "tooltip": {"title": tag, "lines": desc.split("\n")}},
		{"button": "$%d" % cost, "color": Color("e0a526"), "on": cb, "min": Vector2(130, 60), "enabled": func(): return gs.money >= cost},
	], "sep": 6})
	UIBuild.find(col, "desc").custom_minimum_size.y = 92
	return col


func buy_charm(i: int) -> void:
	if i < 0 or i >= gs.shop_charms.size():
		return
	var d: Dictionary = gs.shop_charms[i]
	var cost := gs.price(d.cost)
	if gs.money < cost:
		return
	if gs.charms.size() >= gs.charm_slots:
		popup_text(Vector2(main_cx(), TOP_H + 40), "No room for more charms", Color.WHITE, 28)
		return
	gs.money -= cost
	_inflate()
	gs.charms.append({"id": d.id, "data": {}, "ed": d.get("ed", "")})
	stats.charms_bought += 1
	gs.shop_charms.remove_at(i)
	sfx.play("charm_buy")
	rebuild_charms()
	show_shop()


## Inflation challenge: each purchase raises every shop price by $1.
func _inflate() -> void:
	if gs.rules.get("inflation", false):
		gs.inflation += 1
		toast("Prices rose to +$%d" % gs.inflation)


func buy_card() -> void:
	var cost := gs.price(gs.shop_card.cost)
	if gs.money < cost:
		return
	gs.money -= cost
	_inflate()
	gs.deck.append(gs.shop_card.card)
	gs.shop_card = {}
	sfx.play("card_place")
	show_shop()
	popup_text(Vector2(main_cx(), TOP_H + 40), "Added to deck (%d cards)" % gs.deck.size(), Color.WHITE, 30)


func buy_spell(i: int) -> void:
	if i < 0 or i >= gs.shop_spells.size():
		return
	if gs.money < gs.price(Data.SPELL_COST):
		return
	if gs.spells.size() >= gs.spell_slots:
		popup_text(Vector2(main_cx(), TOP_H + 40), "No room for more spells", Color.WHITE, 28)
		return
	gs.money -= gs.price(Data.SPELL_COST)
	_inflate()
	gs.spells.append(gs.shop_spells[i])
	gs.shop_spells.remove_at(i)
	sfx.play("charm_buy", 1.15)
	rebuild_spells()
	show_shop()
	tutorial("spell", "Spells wait in the slots at the top right. Select cards in your hand during a round, then tap a spell to cast it on them.")


func buy_rune(i: int) -> void:
	if i < 0 or i >= gs.shop_runes.size():
		return
	if gs.money < gs.price(Data.RUNE_COST):
		return
	var h: String = gs.shop_runes[i]
	gs.money -= gs.price(Data.RUNE_COST)
	_inflate()
	gs.hand_levels[h] += 1
	gs.shop_runes.remove_at(i)
	sfx.play("rune")
	show_shop()
	popup_text(Vector2(main_cx(), TOP_H + 40), "%s  lvl %d" % [h, gs.hand_levels[h]], Color("c9b3ff"), 32)


func reroll_shop() -> void:
	if gs.money < gs.price(gs.reroll_cost):
		return
	gs.money -= gs.price(gs.reroll_cost)
	gs.reroll_cost += 1
	sfx.play("reroll")
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
	music.set_muffled(false)
	for c in modal.get_children():
		c.queue_free()
	modal.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _on_charm_tapped(v: CharmView) -> void:
	var idx := charm_views.find(v)
	if idx < 0:
		return
	var inst: Dictionary = gs.charms[idx]
	var d := Data.charm_def(inst.id)
	if not v.face_up:
		var hv := open_modal()
		hv.add_child(_label("Face down", 36, Color("f2d675")))
		hv.add_child(_label("%s hides your charms until it is defeated." % gs.boss_hex.name, 22))
		hv.add_child(_center(_button("Close", Color("5a5f73"), close_modal, Vector2(200, 60), 24)))
		return
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
		var was_ember := gs.charm_disabled(gs.charms.find(inst))
		gs.charms.erase(inst)
		if in_round and gs.blind_idx == 2:
			gs.boss_state.sold = true
			if was_ember:
				gs.boss_state.ember = -1
			if inst.id == "warden":
				disable_boss()
			elif gs.boss_hex.id == "jade" and gs.hex() == "jade":
				for hv in hand_views:
					hv.set_debuffed(gs.is_debuffed(hv.card))
				toast("Jade Wreath lifted: cards work again")
		charm_views.erase(v)
		motes(fx_center(v), [Data.MONEY_COLOR, Color("fff1b8")], 14, {"speed": 160.0, "gravity": Vector2(0, 260), "life": 0.8})
		v.dissolve()
		sfx.play("dissolve")
		sfx.play("charm_sell")
		layout_charms(true)
		update_hud()
		close_modal()
		if _shop_open:
			show_shop(), Vector2(170, 70), 24)
	sell.disabled = (busy and in_round) or inst.get("locked", false)
	if inst.get("locked", false):
		sell.text = "Locked"
	row.add_child(sell)
	row.add_child(_button("Close", Color("5a5f73"), close_modal, Vector2(150, 70), 24))
	vb.add_child(row)
	vb.add_child(_label("Charms trigger left to right. Drag to reorder.", 18, Color(1, 1, 1, 0.5)))


## Break a card into tumbling shards.
func shatter(v: CardView) -> void:
	sfx.play("glass_shatter")
	haptic(60, 0.7)
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
	motes(origin + Vector2(CardView.W, CardView.H) / 2, [Color("bff3ff"), Color.WHITE, face], 18,
		{"area": Vector2(CardView.W, CardView.H) * 0.6, "speed": 200.0, "size": 6.0, "gravity": Vector2(0, 300), "life": 0.8})
	popup_text(origin + Vector2(CardView.W / 2, -24), "Shattered!", Color("bff3ff"), 30)
	v.queue_free()


const TIPS := [
	"Interest pays $1 for every $5 you hold, up to $5. Saving up pays off!",
	"Charms trigger left to right, so put x Mult charms last.",
	"Runes level up a hand type permanently for the run.",
	"Glass cards hit hard but can shatter. Enjoy them while they last.",
	"Iron cards help most when you keep them in your hand.",
	"Sell a Warden during a boss blind to switch the boss off.",
	"Hold a card to read its upgrades.",
	"Tap the blind panel to see what the boss is up to.",
]


## Bring Ace onto the screen (or reuse him) at `pos`.
func summon_ace(pos: Vector2) -> Mascot:
	if mascot == null or not is_instance_valid(mascot) or mascot.is_queued_for_deletion():
		mascot = Mascot.new(sfx)
		mascot_layer.add_child(mascot)
		mascot.position = pos
		mascot.appear()
	else:
		create_tween().tween_property(mascot, "position", pos, 0.25)
	return mascot


func dismiss_ace() -> void:
	if mascot != null and is_instance_valid(mascot):
		mascot.leave()
	mascot = null


## A one-time tip from Ace, shown only once per profile.
func tutorial(step: String, text: String) -> void:
	if profile_data.get("tips_off", false):
		return
	if not profile_data.has("tutorial"):
		profile_data.tutorial = []
	if profile_data.tutorial.has(step):
		return
	profile_data.tutorial.append(step)
	_save_stats()
	var a := summon_ace(Vector2(vw - Mascot.W - 24, TOP_H + 24))
	a.say(text, [["Got it", dismiss_ace], ["No more tips", func():
		profile_data.tips_off = true
		_save_stats()
		dismiss_ace()]])


## Ace reacts to how the run ended.
func ace_quip(lines: Array) -> void:
	var a := summon_ace(Vector2(36, 36))
	a.say(lines.pick_random(), [["Thanks, Ace", dismiss_ace]], false)


## Large message across the table; play waits until it has been read.
func banner(title: String, text: String, col: Color, hold: float = 1.4) -> void:
	var p := PanelContainer.new()
	var sb := _box(col.darkened(0.35), 4.0, true)
	sb.outline = 4.0
	sb.outline_color = col.lightened(0.4)
	sb.set_content_margin_all(22)
	p.add_theme_stylebox_override("panel", sb)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var vb := VBoxContainer.new()
	vb.add_child(_label(title, 40, Color("ffdf6b")))
	var l := _label(text, 26)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(520, 0)
	vb.add_child(l)
	p.add_child(vb)
	fx_layer.add_child(p)
	await get_tree().process_frame
	p.pivot_offset = p.size / 2
	p.position = Vector2(main_cx(), (TOP_H + hand_y()) / 2.0) - p.size / 2
	p.scale = Vector2(0.3, 0.3)
	var tw := create_tween()
	tw.tween_property(p, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_interval(hold + text.length() * 0.02)
	tw.tween_property(p, "modulate:a", 0.0, 0.25)
	tw.tween_callback(p.queue_free)
	await tw.finished


## Boss warning: a run of descending pings, then its rule across the table.
func announce_boss() -> void:
	for i in 4:
		sfx.play("boss_intro") if i == 0 else sfx.play("boss_ping", 1.0, 0.7)
		if i == 0:
			juice(blind_chip, 0.35)
			jiggle += 1.5
		await wait(0.1)
	var title: String = ("Showdown: " if gs.is_showdown() else "") + gs.boss_hex.name
	await banner(title, gs.boss_hex.desc, gs.boss_hex.color)


## The blind token burns away with a ping for each dollar of reward.
func defeat_blind() -> void:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/card_fx.gdshader")
	m.set_shader_parameter("size", blind_chip.size)
	m.set_shader_parameter("burn", gs.blind_color().lightened(0.4))
	blind_chip.material = m
	juice(blind_chip, 0.3)
	var pings := mini(gs.blind_reward() + 2, 7)
	for i in pings:
		sfx.play("blind_defeat") if i == 0 else sfx.play("tally", 1.3 - 0.05 * i)
		m.set_shader_parameter("dissolve", float(i + 1) / pings)
		motes(fx_center(blind_chip), [gs.blind_color().lightened(0.4), gs.blind_color().lightened(0.7), Color.WHITE], 6,
			{"speed": 90.0, "size": 6.0, "life": 0.7, "gravity": Vector2(0, -60)})
		await wait(0.12)
	var tw := create_tween()
	tw.tween_property(lbl_blind, "modulate:a", 0.0, 0.2)
	await tw.finished
	blind_chip.material = null
	lbl_blind.modulate.a = 1.0


## The Warden's effect: undo whatever the boss changed this round.
func disable_boss() -> void:
	var was := gs.hex()
	if was == "":
		return
	gs.boss_state.disabled = true
	match was:
		"bulwark":
			gs.target = gs.target / 2
		"abyss":
			gs.target = gs.target / 3
		"needle":
			gs.hands_left += gs.max_hands - 1
		"drought":
			gs.discards_left = gs.max_discards
	gs.boss_state.down = []
	gs.boss_state.forced = -1
	gs.boss_state.ember = -1
	for v in hand_views:
		v.set_debuffed(gs.is_debuffed(v.card))
		if not v.face_up:
			v.flip_up()
	refresh_charm_states()
	juice(blind_chip, 0.4)
	sfx.play("spell_cast", 0.7)
	toast("Warden disabled %s" % gs.boss_hex.name)
	update_hud()
	if was == "shackle":
		busy = true
		await deal()
		busy = false
		update_hud()
	if gs.round_score >= gs.target:
		await win_round()


func show_blind_info() -> void:
	var idx := gs.blind_idx
	var vb := open_modal()
	vb.add_child(_label(gs.blind_name(idx), 38, gs.blind_color(idx).lightened(0.4)))
	vb.add_child(_label("Score at least %s   Reward %s" % [Data.fmt(gs.target if in_round else gs.blind_target(idx)), "$".repeat(gs.blind_reward(idx))], 22))
	if idx == 2:
		if gs.is_showdown():
			vb.add_child(_label("Showdown boss", 20, Color("ffdf6b")))
		var desc := _label(gs.boss_hex.desc, 26)
		desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		desc.custom_minimum_size = Vector2(520, 0)
		vb.add_child(desc)
		if in_round and gs.boss_state.get("disabled", false):
			vb.add_child(_label("Disabled by the Warden", 22, Color("8fe3a0")))
		elif in_round:
			match gs.hex():
				"echo":
					var used: Array = gs.boss_state.used_hands
					vb.add_child(_label("Already played: " + (", ".join(used) if not used.is_empty() else "none"), 20, Color(1, 1, 1, 0.75)))
				"monotone":
					var only: String = gs.boss_state.only_hand
					vb.add_child(_label("Allowed hand: " + (only if only != "" else "whatever you play first"), 20, Color(1, 1, 1, 0.75)))
	else:
		vb.add_child(_label("No special rules", 22, Color(1, 1, 1, 0.7)))
	vb.add_child(_center(_button("Close", Color("5a5f73"), close_modal, Vector2(200, 60), 24)))


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
	settings = saves.load_settings(settings)
	_load_profile()


func _load_profile() -> void:
	profile_data = saves.load_profile()
	stats = STAT_DEFAULTS.duplicate()
	stats.merge(profile_data.stats, true)


func _save_stats() -> void:
	saves.save_settings(settings)
	profile_data.stats = stats
	saves.save_profile(profile_data)


## Snapshot the run at a safe point so it can be resumed after the app closes.
func save_run(screen: String, extra := {}) -> void:
	if gs == null:
		return
	var snap := gs.to_dict()
	snap.screen = screen
	snap.sort_mode = sort_mode
	snap.manual_order = manual_order
	snap.merge(extra)
	saves.save_run(snap)
	# Lifetime stats change during play; keep them in step with the run.
	profile_data.stats = stats
	saves.save_profile(profile_data)


func resume_run() -> void:
	var d := saves.load_run()
	if d.is_empty():
		new_run()
		return
	on_title = false
	music.pitch_target = 1.0
	gs = GameState.from_dict(d)
	sort_mode = d.get("sort_mode", "rank")
	_place_marker()
	clear_hand_views()
	manual_order = d.get("manual_order", false)
	rebuild_charms()
	rebuild_spells()
	lbl_hand_name.text = ""
	match d.get("screen", "blind"):
		"shop":
			show_shop()
		"cashout":
			show_cashout(d.cashout)
		"round":
			resume_round()
		_:
			show_blind_select()


func resume_round() -> void:
	clear_overlay()
	_shop_open = false
	in_round = true
	busy = true
	music.set_track("boss" if gs.blind_idx == 2 else "table")
	var k := 0
	for c in gs.hand:
		var v := _make_hand_view(c)
		if not gs.boss_state.get("down", []).has(c.id):
			v.flip_up(0.1 + 0.05 * k)
			k += 1
	refresh_charm_states()
	layout_hand(true)
	update_hud()
	await wait(0.4 + 0.05 * k)
	ensure_forced()
	busy = false
	update_hud()


## Record a charm or boss the player has now seen; announce new ones.
func discover(kind: String, id: String) -> void:
	var key := "seen_charms" if kind == "charm" else "seen_hexes"
	if profile_data[key].has(id):
		return
	profile_data[key].append(id)
	_save_stats()
	if kind == "charm":
		toast("New charm discovered: " + Data.charm_def(id).name)
	else:
		for h in Data.HEXES:
			if h.id == id:
				toast("New boss discovered: " + h.name)


## A small notice that slides in at the top right.
func toast(text: String) -> void:
	sfx.play("discover" if text.begins_with("New ") or text.begins_with("Challenge complete") else "toast", 1.0, 0.7)
	var p := PanelContainer.new()
	var sb := _box(Color("22313b"), 3.0, true)
	sb.outline = 2.0
	sb.outline_color = Color("ffdf6b")
	sb.set_content_margin_all(12)
	p.add_theme_stylebox_override("panel", sb)
	p.add_child(_label(text, 20, Color.WHITE))
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fx_layer.add_child(p)
	var slot := fx_layer.get_children().filter(func(c): return c is PanelContainer).size() - 1
	p.position = Vector2(vw + 10, 12 + slot * 58)
	await get_tree().process_frame
	var tw := create_tween()
	tw.tween_property(p, "position:x", vw - p.size.x - 12, 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_interval(2.4)
	tw.tween_property(p, "position:x", vw + 10, 0.25)
	tw.tween_callback(p.queue_free)


func _apply_settings() -> void:
	Music.apply_volumes(settings.master, settings.music, settings.sfx)
	Engine.time_scale = settings.speed
	Glide.calm = settings.reduced_motion
	Anim.calm = settings.reduced_motion
	Motes.calm = settings.reduced_motion


# ---------------------------------------------------------------- input helpers

## Short buzz on phones (and rumble on a gamepad in use).
func haptic(ms: int, strength: float) -> void:
	if not settings.vibration:
		return
	if OS.has_feature("mobile"):
		Input.vibrate_handheld(ms, strength)
	if pad != null and pad.pad_mode and pad.last_joy >= 0:
		Input.start_joy_vibration(pad.last_joy, strength * 0.6, strength, ms / 1000.0)


func deselect_all() -> void:
	if busy or not in_round:
		return
	var any := false
	for v in hand_views:
		if v.selected and not (gs.hex() == "lantern" and v.card.id == gs.boss_state.get("forced", -1)):
			v.selected = false
			v.queue_redraw()
			any = true
	if any:
		sfx.play("card_deselect")
		layout_hand(true)
		update_hud()


## Back button / Escape / B: close a popup, then clear the selection, then
## open the menu. On the title screen it leaves the app.
func go_back() -> void:
	if mascot != null and is_instance_valid(mascot) and not mascot.buttons().is_empty():
		mascot.buttons()[0].pressed.emit()
		return
	if not modal.get_children().filter(func(c): return not c.is_queued_for_deletion()).is_empty():
		close_modal()
		return
	if in_round and not busy and not selected_views().is_empty():
		deselect_all()
		return
	if on_title:
		get_tree().quit()
		return
	show_menu()


func _exit_tree() -> void:
	UIBuild.feedback = Callable()


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_GO_BACK_REQUEST:
		go_back()


## A button that only fires after being held down, filling up as it goes.
func _hold_button(text: String, col: Color, cb: Callable, hold := 0.8, min_size := Vector2(300, 64)) -> Button:
	return UIBuild.make_button({"button": text, "color": col, "on": cb, "hold": hold, "min": min_size, "size": 24})


## Label, slider and value for one 0-100 volume setting; applies live.
func _volume_row(title: String, key: String) -> Control:
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 14)
	var l := _label(title, 24, Color.WHITE, HORIZONTAL_ALIGNMENT_LEFT)
	l.custom_minimum_size = Vector2(110, 0)
	hb.add_child(l)
	var slider := HSlider.new()
	slider.min_value = 0
	slider.max_value = 100
	slider.step = 5
	slider.value = settings[key]
	slider.custom_minimum_size = Vector2(420, 40)
	slider.focus_mode = Control.FOCUS_NONE
	slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var track := PixelBox.new(Color(0, 0, 0, 0.45), 2.0)
	track.set_content_margin_all(6)
	slider.add_theme_stylebox_override("slider", track)
	var fill := PixelBox.new(Data.CHIP_COLOR, 2.0)
	fill.set_content_margin_all(6)
	slider.add_theme_stylebox_override("grabber_area", fill)
	slider.add_theme_stylebox_override("grabber_area_highlight", fill)
	hb.add_child(slider)
	var val := _label("%d" % settings[key], 24, Color("ffdf6b"), HORIZONTAL_ALIGNMENT_RIGHT)
	val.custom_minimum_size = Vector2(56, 0)
	hb.add_child(val)
	slider.value_changed.connect(func(v):
		settings[key] = v
		val.text = "%d" % v
		_apply_settings()
		_save_stats()
		if key == "sfx":
			sfx.play("slider"))
	return hb


func show_challenges() -> void:
	var won: Array = profile_data.get("challenges_won", [])
	var cells: Array = []
	for ch in Data.CHALLENGES:
		var done := won.has(ch.id)
		cells.append({"button": ch.name + ("  [done]" if done else ""), "color": Color("3f9a5a") if done else Color("4a4f63"),
			"on": func(): show_challenge(ch.id), "min": Vector2(260, 58), "size": 22, "fit": 236,
			"tooltip": {"title": ch.name, "lines": [ch.desc]}})
	open_modal().add_child(UIBuild.build({"col": [
		{"text": "Challenges", "size": 38, "color": Color("ffdf6b")},
		{"text": "%d / %d complete  -  beat ante %d to complete one" % [won.size(), Data.CHALLENGES.size(), Data.FINAL_ANTE], "size": 20, "color": Color(1, 1, 1, 0.7)},
		{"grid": cells, "columns": 3},
		{"button": "Close", "color": Color("5a5f73"), "on": close_modal, "min": Vector2(200, 58), "size": 24},
	]}))


func show_challenge(id: String) -> void:
	var ch := Data.challenge_def(id)
	var rows: Array = [
		{"text": ch.name, "size": 40, "color": Color("ffdf6b")},
		{"text": ch.desc, "size": 24, "wrap": 620},
	]
	for line in Data.challenge_lines(ch):
		rows.append({"text": "-  " + line, "size": 20, "color": Color(1, 1, 1, 0.85), "wrap": 620, "align": "left"})
	var start := func():
		close_modal()
		new_run(id)
	var go: Dictionary = {"button": "Start", "color": Color("b3364e"), "on": start, "min": Vector2(220, 70)}
	if saves.has_run():
		go = {"button": "Hold: Start (ends current run)", "color": Color("b3364e"), "on": start, "hold": 0.6, "min": Vector2(380, 70), "size": 24}
	rows.append({"row": [go, {"button": "Back", "color": Color("5a5f73"), "on": show_challenges, "min": Vector2(160, 70), "size": 24}], "sep": 14})
	open_modal().add_child(UIBuild.build({"col": rows}))


func show_collection(tab: String = "charms") -> void:
	var vb := open_modal()
	vb.add_child(_label("Collection  (Profile %d)" % saves.profile, 34, Color("ffdf6b")))
	var tabs: Array = []
	for t in [["charms", "Charms"], ["bosses", "Bosses"], ["stats", "Stats"], ["credits", "Credits"]]:
		tabs.append({"button": t[1], "color": Data.CHIP_COLOR if t[0] == tab else Color("4a4f63"), "on": func(): show_collection(t[0]),
			"min": Vector2(170, 54), "size": 22, "choice": "collection", "chosen": t[0] == tab})
	vb.add_child(UIBuild.build({"row": tabs, "sep": 12}))
	match tab:
		"charms":
			var seen: Array = profile_data.seen_charms
			vb.add_child(_label("%d / %d discovered" % [seen.size(), Data.CHARMS.size()], 20, Color(1, 1, 1, 0.7)))
			var grid := GridContainer.new()
			grid.columns = 7
			grid.add_theme_constant_override("h_separation", 10)
			grid.add_theme_constant_override("v_separation", 8)
			for c in Data.CHARMS:
				var cell := Control.new()
				cell.custom_minimum_size = Vector2(CharmView.W, CharmView.H) * 0.62
				cell.mouse_filter = Control.MOUSE_FILTER_IGNORE
				if seen.has(c.id):
					cell.mouse_filter = Control.MOUSE_FILTER_STOP
					UIBuild.attach_tooltip(cell, {"title": c.name, "lines": [c.desc, Data.RARITY_NAMES[c.rarity]]})
					var cv := CharmView.new(c.id)
					cv.float_amount = 0.6
					cv.scale = Vector2(0.62, 0.62)
					cv.pivot_offset = Vector2.ZERO
					cv.mouse_filter = Control.MOUSE_FILTER_IGNORE
					cell.add_child(cv)
				else:
					var lock := Panel.new()
					lock.size = cell.custom_minimum_size
					lock.add_theme_stylebox_override("panel", _box(Color(0, 0, 0, 0.4), 3.0))
					_place(_label("?", 40, Color(1, 1, 1, 0.35)), lock, Vector2.ZERO, lock.size)
					cell.add_child(lock)
				grid.add_child(cell)
			vb.add_child(_center(grid))
		"bosses":
			var seen: Array = profile_data.seen_hexes
			vb.add_child(_label("%d / %d discovered" % [seen.size(), Data.HEXES.size()], 20, Color(1, 1, 1, 0.7)))
			var grid := GridContainer.new()
			grid.columns = 2
			grid.add_theme_constant_override("h_separation", 24)
			grid.add_theme_constant_override("v_separation", 6)
			for h in Data.HEXES:
				var row := HBoxContainer.new()
				row.add_theme_constant_override("separation", 10)
				var known := seen.has(h.id)
				row.add_child(BlindChip.new(h.color.lightened(0.3) if known else Color(0.4, 0.4, 0.4), 40.0))
				var txt := _label("%s: %s" % [h.name, h.desc] if known else "???", 19, Color.WHITE if known else Color(1, 1, 1, 0.4), HORIZONTAL_ALIGNMENT_LEFT)
				txt.custom_minimum_size = Vector2(380, 0)
				txt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				row.add_child(txt)
				grid.add_child(row)
			vb.add_child(_center(grid))
		"stats":
			var labels := [["Runs", "runs"], ["Wins", "wins"], ["Best ante", "best_ante"], ["Best hand", "best_hand"],
				["Hands played", "hands_played"], ["Cards played", "cards_played"], ["Money earned", "money_earned"],
				["Charms bought", "charms_bought"], ["Spells cast", "spells_cast"], ["Challenges won", "challenges_won"], ["Glass cards shattered", "cards_shattered"]]
			var box := VBoxContainer.new()
			box.custom_minimum_size = Vector2(520, 0)
			for l in labels:
				var val = profile_data.get("challenges_won", []).size() if l[1] == "challenges_won" else stats[l[1]]
				_row_label(box, l[0], ("$" if l[1] == "money_earned" else "") + Data.fmt(val), Color("ffdf6b"))
			vb.add_child(_center(box))
		"credits":
			var v := Engine.get_version_info()
			vb.add_child(_label("Aleatro", 36, Color.WHITE))
			var made := _label("Made with Godot Engine %d.%d" % [v.major, v.minor], 22)
			# five quick taps here toggle the developer hit-box overlay
			made.mouse_filter = Control.MOUSE_FILTER_STOP
			var taps := {"n": 0, "at": 0.0}
			made.gui_input.connect(func(e):
				if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
					taps.n = taps.n + 1 if Anim.now() - taps.at < 0.6 else 1
					taps.at = Anim.now()
					if taps.n == 5:
						taps.n = 0
						debug_boxes.toggle()
						toast("Debug boxes " + ("on" if debug_boxes.visible else "off")))
			vb.add_child(made)
			vb.add_child(_label("Music, sound and art are generated by the game's own code.", 20, Color(1, 1, 1, 0.7)))
	vb.add_child(_center(_button("Close", Color("5a5f73"), close_modal, Vector2(200, 58), 24)))


func show_menu() -> void:
	if on_title:
		return
	var vb := open_modal()
	music.set_muffled(true)
	sfx.play("pause_open")
	var title: String = "Paused" + ("  -  " + Data.challenge_def(gs.challenge).name if gs != null and gs.challenge != "" else "")
	var opt := {"color": Color("5a5f73"), "min": Vector2(300, 64), "size": 24}
	var b := func(text: String, cb: Callable, extra := {}) -> Dictionary:
		var d := opt.duplicate()
		d.merge({"button": text, "on": cb})
		d.merge(extra, true)
		return d
	vb.add_child(UIBuild.build({"col": [
		{"text": title, "size": 40, "color": Color("ffdf6b"), "fit": 720},
		{"node": _volume_row("Master", "master")},
		{"node": _volume_row("Music", "music")},
		{"node": _volume_row("Sounds", "sfx")},
		{"grid": [
			b.call("Vibration: %s" % ("On" if settings.vibration else "Off"), func():
				settings.vibration = not settings.vibration
				_save_stats()
				haptic(40, 0.6)
				show_menu(), {"color": Color("4a6fa5")}),
			b.call("Speed: %sx" % str(settings.speed).trim_suffix(".0"), func():
				var speeds := [1.0, 1.5, 2.0, 3.0]
				settings.speed = speeds[(speeds.find(settings.speed) + 1) % speeds.size()]
				_apply_settings()
				_save_stats()
				show_menu(), {"color": Color("4a6fa5"), "tooltip": "Speeds up scoring and dealing animations"}),
			b.call("Motion: %s" % ("Reduced" if settings.reduced_motion else "Full"), func():
				settings.reduced_motion = not settings.reduced_motion
				_apply_settings()
				_save_stats()
				show_menu(), {"color": Color("4a6fa5"), "tooltip": "Reduced turns off screen shake, wobble, lean and idle sway"}),
			b.call("How to play", show_help),
			b.call("Collection", show_collection),
			b.call("Replay tips", func():
				profile_data.tutorial = []
				profile_data.tips_off = false
				_save_stats()
				close_modal()
				toast("Ace will show the tips again"), {"once": true}),
			b.call("Hold: New Run", func():
				close_modal()
				new_run(), {"color": Data.MULT_COLOR, "hold": 0.8}),
			b.call("Hold: Main Menu", func():
				close_modal()
				clear_hand_views()
				show_title(), {"color": Color("7b4fa0"), "hold": 0.8}),
		], "columns": 2, "sep": 14},
		{"button": "Resume", "color": Data.CHIP_COLOR, "on": close_modal, "min": Vector2(320, 76), "size": 30},
	]}))
