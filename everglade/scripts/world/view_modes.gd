class_name ViewModes
extends Node
## Tiny Glade's other cameras, besides the diorama orbit:
##  * walk: first person at eye height, stepping up stairs and onto flat
##    roofs and wall tops (there is no collision, as in Tiny Glade: Ctrl
##    walks you straight through anything). Walk up to sheep to pet them.
##  * fly: a free floating camera (Q/E or the side buttons for up/down)
##  * map: straight down over the whole glade
##  * ride: standing by a cart (or wheelbarrow) on some stairs, press Enter
##    (or Ride) to ride it like a rollercoaster down the flights; W speeds
##    up, S brakes, A/D lean. Carts parked nearby join the train, and a
##    sheep hops into each.
## Keys: WASD/arrows move, mouse drag looks, Esc leaves. Touch: drag on the
## left half to move, on the right half to look.

signal exited

const EYE := 1.6
const WALK_SPEED := 3.2
const FLY_SPEED := 7.0

var game   # Game
var mode := ""   # "" (orbit), walk, fly, map, ride
var cam: Camera3D
var _yaw := 0.0
var _pitch := 0.0
var _pos := Vector3.ZERO
var _move_touch := -1
var _move_from := Vector2.ZERO
var _move_vec := Vector2.ZERO
var _look_touch := -1
var _look_drag := false
var _ui: CanvasLayer
var _ride_btn: Button
var _label: Label
var _ride: Dictionary = {}
var _train: Array[Node3D] = []


func setup(g) -> void:
	game = g
	cam = game.rig.camera
	_build_ui()


func active() -> bool:
	return mode != ""


func cycle() -> void:
	var order := ["", "walk", "fly", "map"]
	enter(order[(order.find(mode) + 1) % order.size()])


func enter(m: String) -> void:
	if m == mode:
		return
	_end_ride()
	var was := mode
	mode = m
	if m == "" or m == "map":
		cam.fov = 42.0
	if m == "":
		game.rig.set_process(true)
		game.rig.map_mode = false
		game.rig.snap()
		_ui.visible = false
		game.hud.visible = true
		exited.emit()
		return
	if m == "map":
		game.rig.set_process(true)
		game.rig.map_mode = true
		game.rig.focus_on(Vector3.ZERO, game.rig.MAX_DIST)
		game.hud.visible = true
		_ui.visible = true
		_label.text = "Map view. Drag to move around. Esc or Back returns."
		game.hud.toast("Map")
		return
	game.rig.map_mode = false
	game.rig.set_process(false)
	if was == "" or was == "map":
		# start where the diorama camera looks, facing the same way
		var t: Vector3 = game.rig.target
		_yaw = game.rig.yaw + PI
		_pitch = -0.05
		_pos = Vector3(t.x, _ground(Vector2(t.x, t.z), 50.0) + EYE, t.z) if m == "walk" else cam.global_position
		if m == "walk":
			# step back from the middle of things
			_pos -= Vector3(sin(_yaw), 0, cos(_yaw)) * 0.0
	cam.fov = 70.0
	_ui.visible = true
	game.hud.visible = false
	_label.text = ("Walking. WASD / left thumb to move, drag to look. Tap animals to pet them. Esc to leave." if m == "walk"
			else "Flying. WASD to move, Q/E down/up, drag to look. Esc to leave.")
	game.hud.toast("Walk" if m == "walk" else "Fly")
	_apply()


func leave() -> void:
	cam.fov = 42.0
	enter("")


func _build_ui() -> void:
	_ui = CanvasLayer.new()
	_ui.layer = 5
	_ui.visible = false
	add_child(_ui)
	var box := HBoxContainer.new()
	box.set_anchors_preset(Control.PRESET_TOP_LEFT)
	box.position = Vector2(16, 16)
	box.add_theme_constant_override("separation", 10)
	_ui.add_child(box)
	var back := HUD.icon_button("close", "Leave", 56)
	back.pressed.connect(leave)
	box.add_child(back)
	var cyc := HUD.icon_button("eye", "View", 56)
	cyc.pressed.connect(cycle)
	box.add_child(cyc)
	_ride_btn = HUD.icon_button("cart", "Ride", 56)
	_ride_btn.visible = false
	_ride_btn.pressed.connect(_try_ride)
	box.add_child(_ride_btn)
	for pair in [["up", 1.0], ["down", -1.0]]:
		var b := HUD.icon_button("plus" if pair[1] > 0 else "minus", "", 48)
		b.set_meta("dir", pair[1])
		b.button_down.connect(func(): set_meta("vert", pair[1]))
		b.button_up.connect(func(): set_meta("vert", 0.0))
		box.add_child(b)
	_label = Label.new()
	_label.add_theme_font_size_override("font_size", 16)
	_label.add_theme_color_override("font_color", Color.WHITE)
	_label.add_theme_color_override("font_outline_color", Color(0.2, 0.15, 0.1, 0.8))
	_label.add_theme_constant_override("outline_size", 8)
	_label.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_label.position = Vector2(18, -40)
	_label.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_ui.add_child(_label)


func over_ui(pos: Vector2) -> bool:
	return pos.y < 90.0 and pos.x < 420.0


# ---------------------------------------------------------------------------
func _process(delta: float) -> void:
	if mode == "" or mode == "map":
		return
	if mode == "ride":
		_ride_step(delta)
		return
	var v := Vector2.ZERO
	if get_viewport().gui_get_focus_owner() == null:
		if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
			v.y += 1
		if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
			v.y -= 1
		if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
			v.x -= 1
		if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
			v.x += 1
	if _move_touch >= 0:
		v += Vector2(_move_vec.x, -_move_vec.y)
	v = v.limit_length(1.0)
	var fwd := Vector3(-sin(_yaw), 0, -cos(_yaw))
	var right := Vector3(cos(_yaw), 0, -sin(_yaw))
	var speed := WALK_SPEED if mode == "walk" else FLY_SPEED
	if Input.is_key_pressed(KEY_SHIFT):
		speed *= 2.0
	if mode == "fly":
		fwd = -cam.global_transform.basis.z
		var vert := float(get_meta("vert", 0.0))
		if Input.is_key_pressed(KEY_E) or Input.is_key_pressed(KEY_SPACE):
			vert += 1.0
		if Input.is_key_pressed(KEY_Q):
			vert -= 1.0
		_pos += Vector3.UP * vert * speed * delta
	_pos += (fwd * v.y + right * v.x) * speed * delta
	var lim := Terrain.HALF + 40.0
	_pos.x = clampf(_pos.x, -lim, lim)
	_pos.z = clampf(_pos.z, -lim, lim)
	if mode == "walk":
		var floor_y := _ground(Vector2(_pos.x, _pos.z), _pos.y - EYE + 0.55)
		# step up gently, drop down a little faster
		var target := floor_y + EYE
		_pos.y = lerpf(_pos.y, target, minf(1.0, delta * (10.0 if target > _pos.y else 6.0)))
		_ride_btn.visible = not _cart_near().is_empty()
	else:
		var g: float = game.glade.terrain.height_at(_pos.x, _pos.z) if absf(_pos.x) < Terrain.HALF and absf(_pos.z) < Terrain.HALF else Landscape.outer_height(_pos.x, _pos.z)
		_pos.y = clampf(_pos.y, g + 0.5, 120.0)
	_apply()


func _apply() -> void:
	cam.global_position = _pos
	cam.global_basis = Basis.from_euler(Vector3(_pitch, _yaw, 0.0))


## Height of the surface under p no higher than `reach` (so you walk under
## bridges and into archways rather than popping onto their tops): stairs,
## roofs, wall tops and the ground, found by a ray straight down.
func _ground(p: Vector2, reach: float) -> float:
	var g: float = game.glade.terrain.height_at_v(p) if absf(p.x) < Terrain.HALF and absf(p.y) < Terrain.HALF else Landscape.outer_height(p.x, p.y)
	g = maxf(g, Terrain.WATER_LEVEL - 0.3)
	if Input.is_key_pressed(KEY_CTRL):
		return g
	var space: PhysicsDirectSpaceState3D = game.get_world_3d().direct_space_state
	var from := Vector3(p.x, reach + 0.01, p.y)
	var q := PhysicsRayQueryParameters3D.create(from, Vector3(p.x, g - 0.1, p.y), 2 | 8)
	var hit: Dictionary = space.intersect_ray(q)
	if not hit.is_empty():
		g = maxf(g, (hit.position as Vector3).y)
	return g


# ---------------------------------------------------------------------------
# Input (routed here by the Game while a mode is active)
# ---------------------------------------------------------------------------
func input(event: InputEvent) -> void:
	if mode == "map":
		return
	if event is InputEventScreenTouch:
		var t := event as InputEventScreenTouch
		var w := get_viewport().get_visible_rect().size.x
		if t.pressed:
			if t.position.x < w * 0.45 and _move_touch < 0 and mode != "ride":
				_move_touch = t.index
				_move_from = t.position
				_move_vec = Vector2.ZERO
			elif _look_touch < 0:
				_look_touch = t.index
				_look_drag = false
		else:
			if t.index == _move_touch:
				_move_touch = -1
				_move_vec = Vector2.ZERO
			elif t.index == _look_touch:
				_look_touch = -1
				if not _look_drag:
					game._handle_tap(t.position)
	elif event is InputEventScreenDrag:
		var dr := event as InputEventScreenDrag
		if dr.index == _move_touch:
			_move_vec = ((dr.position - _move_from) / 90.0).limit_length(1.0)
		elif dr.index == _look_touch:
			if dr.relative.length() > 1.5:
				_look_drag = true
			_look(dr.relative)
	elif event is InputEventMouseMotion:
		var mm := event as InputEventMouseMotion
		if Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT) or Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
			_look(mm.relative)
	elif event is InputEventKey and event.pressed and not event.echo:
		match (event as InputEventKey).keycode:
			KEY_ESCAPE:
				leave()
			KEY_ENTER, KEY_KP_ENTER:
				if mode == "ride":
					_end_ride()
				else:
					_try_ride()
			KEY_V:
				cycle()


func _look(rel: Vector2) -> void:
	_yaw -= rel.x * 0.005
	_pitch = clampf(_pitch - rel.y * 0.004, -1.45, 1.45)
	if mode != "ride":
		_apply()


# ---------------------------------------------------------------------------
# Riding carts down stairs
# ---------------------------------------------------------------------------
const RIDERS := ["cart", "wheelbarrow", "q_cart"]


## The cart prop within reach that stands on (or right by) some stairs.
func _cart_near() -> Dictionary:
	var me := Vector2(_pos.x, _pos.z)
	for p in game.glade.data.props:
		if not p.kind in RIDERS:
			continue
		var pp: Vector3 = p.p
		if Vector2(pp.x, pp.z).distance_to(me) > 2.6:
			continue
		var st := _stairs_near(Vector2(pp.x, pp.z), 1.6)
		if not st.is_empty():
			return {"prop": p, "stairs": st}
	return {}


func _stairs_near(q: Vector2, reach: float) -> Dictionary:
	var best := {}
	var bd := reach
	for st in game.glade.data.get("stairs", []):
		var c := Geo.closest(st.pts, q)
		if c.x < bd:
			bd = c.x
			best = st
	return best


func _try_ride() -> void:
	var near := _cart_near()
	if near.is_empty():
		game.hud.toast("Stand by a cart on some stairs to ride it")
		return
	var st: Dictionary = near.stairs
	var pp: Vector3 = near.prop.p
	var s := Geo.closest(st.pts, Vector2(pp.x, pp.z)).y
	var total := Geo.length(st.pts)
	# roll downhill from where the cart stands
	var dir := -1.0 if float(st.y1) > float(st.y0) else 1.0
	_ride = {"stairs": st, "s": s, "dir": dir, "v": 2.0, "lean": 0.0, "total": total, "visited": [st.id]}
	mode = "ride"
	_ride_btn.visible = false
	_label.text = "Riding! W faster, S slower, A/D lean. Enter to hop off."
	_make_train()
	Sfx.play("place_wood", -2.0)


func _make_train() -> void:
	for n in _train:
		n.queue_free()
	_train.clear()
	var carts := 1
	var me := Vector2(_pos.x, _pos.z)
	for p in game.glade.data.props:
		if p.kind in RIDERS and Vector2((p.p as Vector3).x, (p.p as Vector3).z).distance_to(me) < 8.0:
			carts += 1
	carts = clampi(carts - 1, 1, 5)
	for i in carts:
		var car := Node3D.new()
		var mi := MeshInstance3D.new()
		mi.mesh = ModelLib.combined("cart")
		mi.scale = Vector3.ONE * 0.75
		mi.rotation.y = PI * 0.5
		car.add_child(mi)
		if i > 0:
			var sheep := ModelLib.instance("sheep")
			sheep.position = Vector3(0, 0.45, 0)
			sheep.scale = Vector3.ONE * 0.8
			car.add_child(sheep)
		game.glade.add_child(car)
		_train.append(car)


func _ride_step(delta: float) -> void:
	var st: Dictionary = _ride.stairs
	var total: float = _ride.total
	var s: float = _ride.s
	var dir: float = _ride.dir
	# slope along the travel direction: downhill speeds up
	var y_here := StairView.height_at(st, s)
	var y_next := StairView.height_at(st, clampf(s + dir * 0.3, 0.0, total))
	var slope := (y_next - y_here) / 0.3
	var v: float = _ride.v
	v += -slope * 9.0 * delta
	if Input.is_key_pressed(KEY_W):
		v += 3.0 * delta
	if Input.is_key_pressed(KEY_S):
		v -= 4.0 * delta
	v = clampf(v, 1.2, 14.0)
	_ride.v = v
	var lean := 0.0
	if Input.is_key_pressed(KEY_A):
		lean -= 1.0
	if Input.is_key_pressed(KEY_D):
		lean += 1.0
	_ride.lean = lerpf(float(_ride.lean), lean * 0.25, delta * 5.0)
	s += dir * v * delta
	if s < 0.0 or s > total:
		# carry on down the next flight that starts where this one ends
		var end_p: Vector2 = (st.pts as PackedVector2Array)[0] if s < 0.0 else (st.pts as PackedVector2Array)[(st.pts as PackedVector2Array).size() - 1]
		var end_y := StairView.height_at(st, clampf(s, 0.0, total))
		var nxt := _next_flight(end_p, end_y, _ride.visited)
		if nxt.is_empty():
			_end_ride()
			return
		_ride.stairs = nxt.stairs
		_ride.total = Geo.length(nxt.stairs.pts)
		_ride.dir = nxt.dir
		(_ride.visited as Array).append(nxt.stairs.id)
		s = 0.0 if nxt.dir > 0.0 else _ride.total
		st = nxt.stairs
	_ride.s = s
	var p2 := Geo.point_at(st.pts, s)
	var t2 := Geo.tangent_at(st.pts, s) * dir
	var y := StairView.height_at(st, s)
	_pos = Vector3(p2.x, y + 1.25, p2.y)
	var heading := atan2(-t2.x, -t2.y)
	_yaw = lerp_angle(_yaw, heading, minf(1.0, delta * 6.0))
	cam.global_position = _pos
	cam.global_basis = Basis.from_euler(Vector3(_pitch + clampf(slope * 0.25, -0.4, 0.4), _yaw, float(_ride.lean)))
	# the train follows behind
	for i in _train.size():
		var si := clampf(s - dir * (0.2 + i * 1.3), 0.0, float(_ride.total))
		var pi := Geo.point_at(st.pts, si)
		var ti := Geo.tangent_at(st.pts, si) * dir
		_train[i].global_position = Vector3(pi.x, StairView.height_at(st, si) + 0.05, pi.y)
		_train[i].rotation = Vector3(0, atan2(ti.x, ti.y), 0)
	if i_frames(delta):
		Sfx.play("brush", -16.0, 0.3)


var _clack := 0.0


func i_frames(delta: float) -> bool:
	_clack -= delta * float(_ride.v)
	if _clack <= 0.0:
		_clack = 0.9
		return true
	return false


func _next_flight(p: Vector2, y: float, visited: Array) -> Dictionary:
	for st in game.glade.data.get("stairs", []):
		if visited.has(st.id):
			continue
		var pts: PackedVector2Array = st.pts
		if pts[0].distance_to(p) < 1.2 and absf(float(st.y0) - y) < 0.8:
			return {"stairs": st, "dir": 1.0}
		if pts[pts.size() - 1].distance_to(p) < 1.2 and absf(float(st.y1) - y) < 0.8:
			return {"stairs": st, "dir": -1.0}
	return {}


func _end_ride() -> void:
	for n in _train:
		n.queue_free()
	_train.clear()
	if mode == "ride":
		mode = "walk"
		_ride = {}
		_label.text = "Walking. WASD / left thumb to move, drag to look. Esc to leave."
		Sfx.play("place_wood", -6.0)
