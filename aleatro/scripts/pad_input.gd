class_name PadInput
extends Node

## Gamepad and keyboard control. Keeps one focused control per screen layer
## (game, overlay, modal), moves it with the d-pad/stick/arrows and activates
## it with A/Enter. Touch or mouse input hides the focus again.

const DIRS := {"ui_left": Vector2.LEFT, "ui_right": Vector2.RIGHT, "ui_up": Vector2.UP, "ui_down": Vector2.DOWN}
const SHORTCUTS := {
	"aleatro_play": [JOY_BUTTON_X, KEY_P],
	"aleatro_discard": [JOY_BUTTON_Y, KEY_D],
	"aleatro_sort_rank": [JOY_BUTTON_LEFT_SHOULDER, KEY_Q],
	"aleatro_sort_suit": [JOY_BUTTON_RIGHT_SHOULDER, KEY_E],
	"aleatro_menu": [JOY_BUTTON_START, KEY_M],
	"aleatro_deck": [JOY_BUTTON_BACK, KEY_TAB],
}
const RESTART_HOLD := 0.8

var main: Control
var focused: Control = null
var pad_mode := false
var last_joy := -1
var ring := FocusRing.new()

var _layer := ""
var _remember := {}
var _held_dir := ""
var _dir_timer := 0.0
var _repeat_delay := 0.3
var _accept_down := false
var _moved_card := false
var _restart_timer := 0.0


func _init(m: Control) -> void:
	main = m


func _ready() -> void:
	for action in SHORTCUTS:
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action)
		var jb := InputEventJoypadButton.new()
		jb.button_index = SHORTCUTS[action][0]
		InputMap.action_add_event(action, jb)
		var k := InputEventKey.new()
		k.physical_keycode = SHORTCUTS[action][1]
		InputMap.action_add_event(action, k)
	ring.z_index = 450
	main.add_child(ring)


func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton or event is InputEventScreenTouch \
			or (event is InputEventMouseMotion and event.relative.length() > 3.0):
		if pad_mode:
			pad_mode = false
			ring.visible = false
		return
	var pressed := event.is_pressed()
	if event is InputEventJoypadMotion:
		pressed = absf(event.axis_value) > 0.5
	if not pressed:
		return
	if event is InputEventJoypadButton or event is InputEventJoypadMotion:
		last_joy = event.device
	if (event is InputEventKey or event is InputEventJoypadButton or event is InputEventJoypadMotion) and not pad_mode:
		pad_mode = true
		_sync_layer(true)


func _process(delta: float) -> void:
	_sync_layer(false)
	ring.visible = pad_mode and focused != null
	ring.target = focused

	for action in DIRS:
		if Input.is_action_just_pressed(action):
			_held_dir = action
			_dir_timer = 0.0
			_repeat_delay = 0.3
			navigate(DIRS[action])
		elif _held_dir == action and Input.is_action_pressed(action):
			_dir_timer += delta
			if _dir_timer > _repeat_delay:
				_dir_timer = 0.0
				_repeat_delay = 0.1
				navigate(DIRS[action])
	if Input.is_action_just_pressed("ui_accept"):
		_accept_pressed()
	if Input.is_action_just_released("ui_accept"):
		_accept_released()
	if Input.is_action_just_pressed("ui_cancel"):
		main.go_back()
	if Input.is_action_just_pressed("aleatro_menu"):
		main.show_menu()
	if Input.is_action_just_pressed("aleatro_deck"):
		main.show_deck()
	if _layer == "game" and main.in_round:
		if Input.is_action_just_pressed("aleatro_play"):
			main.play_selected()
		if Input.is_action_just_pressed("aleatro_discard"):
			main.discard_selected()
		if Input.is_action_just_pressed("aleatro_sort_rank"):
			main.set_sort("rank")
		if Input.is_action_just_pressed("aleatro_sort_suit"):
			main.set_sort("suit")
	# Hold R to restart the run.
	if Input.is_physical_key_pressed(KEY_R) and main.gs != null and not main.on_title:
		_restart_timer += delta
		if _restart_timer >= RESTART_HOLD:
			_restart_timer = -INF
			main.close_modal()
			main.new_run()
	else:
		_restart_timer = 0.0


# ---------------------------------------------------------------- layers

func current_layer() -> String:
	if _live(main.modal).size() > 0:
		return "modal"
	if main.overlay.mouse_filter == Control.MOUSE_FILTER_STOP and _live(main.overlay).size() > 0:
		return "overlay"
	return "game"


func focusables() -> Array:
	match _layer:
		"modal":
			return _buttons(main.modal)
		"overlay":
			var list := _buttons(main.overlay)
			if not main._overlay_full:
				list += main.charm_views
			return list
	var list := []
	if main.in_round:
		list += main.hand_views
	list += _buttons(main.controls)
	list += main.sidebar_buttons
	list += main.charm_views
	return list.filter(func(c): return is_instance_valid(c) and c.is_visible_in_tree() and not (c is BaseButton and c.disabled))


## Track layer changes; remember focus per layer and restore it on return.
func _sync_layer(force: bool) -> void:
	var layer := current_layer()
	var list := focusables()
	if layer != _layer:
		if _layer != "" and focused != null and is_instance_valid(focused):
			_remember[_layer] = focused
		_layer = layer
		var back = _remember.get(layer)
		focused = back if back != null and is_instance_valid(back) and list.has(back) else _default(list)
	elif force or focused == null or not is_instance_valid(focused) or not list.has(focused):
		focused = _default(list)


func _default(list: Array) -> Control:
	if list.is_empty():
		return null
	if _layer == "game" and main.in_round and not main.hand_views.is_empty():
		return main.hand_views[0]
	# The biggest button on a screen is its main action.
	var best: Control = null
	for c in list:
		if c is BaseButton and (best == null or c.size.x * c.size.y > best.size.x * best.size.y):
			best = c
	return best if best != null else list[0]


func _live(node: Node) -> Array:
	return node.get_children().filter(func(c): return not c.is_queued_for_deletion())


func _buttons(node: Node) -> Array:
	var out := []
	for c in _live(node):
		if c is BaseButton or c is Slider:
			if c.is_visible_in_tree() and not (c is BaseButton and c.disabled):
				out.append(c)
		elif c is Control or c is CanvasLayer:
			out += _buttons(c)
	return out


# ---------------------------------------------------------------- actions

func navigate(dir: Vector2) -> void:
	if not pad_mode:
		return
	var list := focusables()
	if focused == null:
		focused = _default(list)
		return
	# Left/right on a slider changes its value instead of moving focus.
	if focused is Slider and dir.y == 0:
		focused.value += focused.step * dir.x
		main.haptic(6, 0.15)
		return
	var hand: Array = main.hand_views
	if focused is CardView and hand.has(focused) and dir.y == 0:
		var i := hand.find(focused)
		var j := i + int(dir.x)
		if j >= 0 and j < hand.size():
			if _accept_down and not main.busy:
				# Holding A while pressing left/right carries the card along.
				hand.remove_at(i)
				hand.insert(j, focused)
				main.manual_order = true
				main.gs.hand = hand.map(func(v): return v.card)
				main.layout_hand(true)
				_moved_card = true
			else:
				focused = hand[j]
			main.haptic(8, 0.2)
			return
	var from := focused.get_global_rect().get_center()
	var best: Control = null
	var best_d := INF
	for c in list:
		if c == focused:
			continue
		var v: Vector2 = c.get_global_rect().get_center() - from
		var along := v.dot(dir)
		if along <= 4.0:
			continue
		var across := absf(v.dot(Vector2(dir.y, dir.x)))
		var d := along + across * 2.0
		if d < best_d:
			best_d = d
			best = c
	if best != null:
		focused = best
		main.haptic(8, 0.2)


func _accept_pressed() -> void:
	if not pad_mode or focused == null or not is_instance_valid(focused):
		return
	_accept_down = true
	_moved_card = false
	if focused is BaseButton:
		if focused.has_meta("hold"):
			focused.button_down.emit()
		else:
			focused.pressed.emit()
	elif focused is CharmView:
		main._on_charm_tapped(focused)


func _accept_released() -> void:
	if not _accept_down:
		return
	_accept_down = false
	if focused == null or not is_instance_valid(focused):
		return
	if focused is CardView and not _moved_card:
		main._on_card_tapped(focused)
	elif focused is BaseButton and focused.has_meta("hold"):
		focused.button_up.emit()
