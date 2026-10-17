class_name DetailsTool
extends BaseTool
## Everything that dresses a house or a wall, as in Tiny Glade's decoration
## tool:
##  * windows in four shapes (plain, arched, round, arrow slit). Tapping a
##    plain window again cycles its trim: flower box, washing-line bracket
##    (facing brackets string a line of laundry between them, even across a
##    lane), shutters, then removes it. Tapping with another shape selected
##    swaps the shape. Windows can be dragged along the wall, to another
##    storey or down to the ground where they turn into a door.
##  * on a flat roof a window becomes a trapdoor
##  * doors, dormers and chimneys
##  * lanterns: a bracket lantern on a wall, a lamp post on the ground
##  * flags: on a roof or tower top a flag on a pole, on a wall a hanging
##    banner, on the ground a banner on a post. Tap one again for the next
##    pattern; flags and banners near each other are strung with bunting
##  * remove: tap any of these details to take it away

var _grab: Dictionary = {}   # {b, w} while dragging a window
var _moved := false

const TRIM_NAMES := ["Plain", "Flower box", "Washing line", "Shutters"]


func _init() -> void:
	tool_id = "details"
	title = "Windows & Doors"
	options = {"mode": "window", "wt": "plain"}


func option_defs() -> Array:
	var defs: Array = [{"type": "choice", "key": "mode", "items": [
		{"id": "window", "label": "Window", "icon": "window"},
		{"id": "door", "label": "Door", "icon": "door"},
		{"id": "dormer", "label": "Dormer", "icon": "dormer"},
		{"id": "chimney", "label": "Chimney", "icon": "chimney"},
		{"id": "lantern", "label": "Lantern", "icon": "wall_lantern"},
		{"id": "flag", "label": "Flag", "icon": "flag"},
		{"id": "remove", "label": "Remove", "icon": "hammer"}]}]
	if options.mode == "window":
		defs.append({"type": "choice", "key": "wt", "items": [
			{"id": "plain", "label": "Square", "icon": "win_plain"},
			{"id": "arched", "label": "Arched", "icon": "win_arched"},
			{"id": "round", "label": "Round", "icon": "win_round"},
			{"id": "slit", "label": "Arrow slit", "icon": "win_slit"}]})
	return defs


func set_option(key: String, value: Variant) -> void:
	super.set_option(key, value)
	if key == "mode" and game:
		game.hud.set_tool(tool_id, self)


func hint() -> String:
	match options.mode:
		"lantern":
			return "Tap a wall to hang a lantern, or the ground for a lamp post."
		"flag":
			return "Tap a roof or tower top for a flag, a wall for a banner, the ground for a standard. Tap one again to change its pattern."
		"remove":
			return "Tap a window, door, lantern, flag or chimney to take it away."
	return "Tap a wall for a window; tap it again for a flower box, washing line or shutters. Drag one to the ground for a door. On a flat roof it's a trapdoor."


func press(screen: Vector2) -> bool:
	if options.mode != "window" and options.mode != "door":
		return false
	var hit := pick(screen, 8)
	if hit.is_empty() or hit.kind != "building":
		return false
	var f := glade.find(hit.id)
	var view: BuildingView = glade.views.get(hit.id)
	if f.is_empty() or view == null:
		return false
	var b: Dictionary = f.item
	var loc := view.locate(hit.point)
	if loc.zone == "roof":
		return false
	var hit_w := _window_at(b, loc, 0.6)
	if hit_w.is_empty():
		return false
	glade.begin_change()
	_grab = {"b": b, "w": hit_w}
	_moved = false
	return true


func drag(screen: Vector2) -> void:
	if _grab.is_empty():
		return
	var hit := pick(screen, 8)
	var b: Dictionary = _grab.b
	if hit.is_empty() or hit.kind != "building" or hit.id != b.id:
		return
	var view: BuildingView = glade.views.get(b.id)
	if view == null:
		return
	var loc := view.locate(hit.point)
	if loc.zone == "roof":
		return
	var w: Dictionary = _grab.w
	var door: bool = loc.y < Catalog.PLINTH + 0.9 and loc.f == 0
	var kind := "door" if door else "window"
	var nf: int = 0 if door else loc.f
	if w.side == loc.side and w.f == nf and w.kind == kind and absf(w.u - loc.u) < 0.02:
		return
	w.side = loc.side
	w.u = clampf(loc.u, 0.05, 0.95) if b.shape != "round" else loc.u
	w.f = nf
	if w.kind != kind:
		Sfx.play("place_wood", -10.0)
	w.kind = kind
	_moved = true
	glade.refresh(b.id)


func release(_screen: Vector2) -> void:
	if _grab.is_empty():
		return
	_grab = {}
	if not _moved:
		glade.undo_stack.pop_back()
		return
	Sfx.play("place_wood", -4.0)
	Settings.vibrate(10)


func cancel() -> void:
	release(Vector2.ZERO)


func tap(screen: Vector2) -> void:
	var hit := pick(screen)
	if hit.is_empty():
		Sfx.play("nope", -8.0)
		return
	var mode: String = options.mode
	match hit.kind:
		"building":
			_tap_building(hit, mode)
		"wall":
			_tap_wall(hit, mode)
		_:
			_tap_ground(hit, mode)


# ---------------------------------------------------------------------------
func _tap_building(hit: Dictionary, mode: String) -> void:
	var f := glade.find(hit.id)
	if f.is_empty():
		return
	var b: Dictionary = f.item
	var view: BuildingView = glade.views.get(b.id)
	if view == null:
		return
	var loc := view.locate(hit.point)
	var lp: Vector3 = view.transform.affine_inverse() * (hit.point as Vector3)
	glade.begin_change()
	var ok := true
	match mode:
		"chimney":
			if b.shape == "round":
				ok = false
			else:
				var u: float = loc.get("x", (loc.u - 0.5) * b.size.x) / b.size.x
				var cur: float = b.get("chimney", BuildingView.NO_CHIMNEY)
				b.chimney = BuildingView.NO_CHIMNEY if absf(cur - u) < 0.12 else clampf(u, -0.45, 0.45)
		"dormer":
			if b.shape == "round" or b.roof == "flat":
				ok = false
			else:
				var side: int = 0 if loc.side == 0 else 2
				if loc.zone != "roof":
					side = 0 if loc.side <= 1 else 2
				_toggle(b, {"side": side, "u": loc.u, "f": 0, "kind": "dormer"}, 1.0)
		"lantern":
			if loc.zone == "roof":
				ok = false
			else:
				_toggle_spot(b, "lanterns", {"side": loc.side, "u": loc.u, "y": clampf(lp.y, 1.4, view.eave - 0.3)}, 0.7)
		"flag":
			ok = _flag_on_building(b, view, loc, lp)
		"remove":
			ok = _remove_on_building(b, view, loc, lp)
		_:
			if loc.zone == "roof":
				if b.get("roof", "") == "flat":
					_toggle_trapdoor(b, lp)
				elif mode == "window" and b.shape != "round":
					# a window tapped on a pitched roof is a dormer
					_toggle(b, {"side": 0 if loc.side == 0 else 2, "u": loc.u, "f": 0, "kind": "dormer"}, 1.0)
				else:
					ok = false
			else:
				var kind := "door" if mode == "door" or (loc.y < Catalog.PLINTH + 0.9 and loc.f == 0) else "window"
				var f_idx: int = 0 if kind == "door" else loc.f
				var door := glade.door_near(b, loc.side, loc.u, 0.9) if kind == "door" else {}
				if not door.is_empty():
					# tapping a door again shuffles the clutter beside it
					glade.reroll_clutter(b, door)
					Sfx.play("plant", -4.0)
					return
				_tap_window(b, {"side": loc.side, "u": loc.u, "f": f_idx, "kind": kind, "wt": options.wt})
	if not ok:
		glade.undo_stack.pop_back()
		Sfx.play("nope", -8.0)
		return
	glade.refresh(b.id)
	Sfx.play("place_wood", -2.0)
	Settings.vibrate(10)


## Adds a window or door, or (tapping an existing one) cycles its trim,
## swaps its shape, or removes it.
func _tap_window(b: Dictionary, w: Dictionary) -> void:
	var existing := _window_at(b, {"side": w.side, "u": w.u, "f": w.f}, 0.9)
	if existing.is_empty():
		if w.kind == "door":
			w.erase("wt")
		b.windows.append(w)
		return
	if existing.kind == "door" or w.kind == "door":
		b.windows.erase(existing)
		return
	var wt: String = existing.get("wt", "plain")
	if wt != w.wt:
		existing.wt = w.wt
		existing.erase("deco")
		game.hud.toast(String(w.wt).capitalize() if w.wt != "slit" else "Arrow slit")
		return
	if wt != "plain":
		b.windows.erase(existing)
		return
	var trim := int(existing.get("deco", 0))
	if trim >= 3:
		b.windows.erase(existing)
		return
	existing.deco = trim + 1
	game.hud.toast(TRIM_NAMES[trim + 1])


## The window or door of `b` nearest (side, u, f), if closer than `gap` m.
func _window_at(b: Dictionary, loc: Dictionary, gap: float) -> Dictionary:
	var best := {}
	var bd := gap
	for w in b.windows:
		var kind: String = w.get("kind", "window")
		if kind == "dormer" or kind == "trapdoor" or w.side != loc.side or w.f != loc.f:
			continue
		var span: float = TAU * b.r if b.shape == "round" else (b.size.x if w.side % 2 == 0 else b.size.y)
		var du: float = absf(w.u - loc.u)
		if b.shape == "round":
			du = minf(du, 1.0 - du)
		if du * span < bd:
			bd = du * span
			best = w
	return best


func _toggle_trapdoor(b: Dictionary, lp: Vector3) -> void:
	for w in b.windows:
		if w.get("kind", "") == "trapdoor" and Vector2(w.x, w.z).distance_to(Vector2(lp.x, lp.z)) < 0.9:
			b.windows.erase(w)
			return
	b.windows.append({"kind": "trapdoor", "side": 0, "u": 0.5, "f": 0, "x": snappedf(lp.x, 0.01), "z": snappedf(lp.z, 0.01)})


## Toggles an entry {side, u, y} in b[list] (lanterns): removes one that's
## near enough, else adds it.
func _toggle_spot(b: Dictionary, list: String, e: Dictionary, gap: float) -> void:
	var arr: Array = b.get(list, [])
	var view: BuildingView = glade.views.get(b.id)
	var p: Vector3 = view._wall_spot(e.side, e.u, e.y)[0]
	for o in arr:
		var q: Vector3 = view._wall_spot(int(o.side), float(o.u), float(o.y))[0]
		if p.distance_to(q) < gap:
			arr.erase(o)
			b[list] = arr
			return
	arr.append(e)
	b[list] = arr


func _flag_on_building(b: Dictionary, view: BuildingView, loc: Dictionary, lp: Vector3) -> bool:
	var flags: Array = b.get("flags", [])
	b.flags = flags
	if loc.zone == "roof":
		for fl in flags:
			if fl.get("at", "") != "top":
				continue
			var near: bool = b.shape == "round" or absf((float(fl.get("u", 0.5)) - loc.u) * b.size.x) < 1.2
			if near:
				_next_pattern(fl)
				return true
		flags.append({"at": "top", "u": snappedf(loc.u, 0.001), "z": snappedf(lp.z, 0.01),
				"pat": randi() % Ornaments.PATTERNS, "r": snappedf(randf() * TAU, 0.01)})
		game.hud.toast("Tap it again for another pattern")
		return true
	var y := clampf(lp.y, 2.2, view.eave - 0.2)
	var p: Vector3 = view._wall_spot(loc.side, loc.u, y)[0]
	for fl in flags:
		if fl.get("at", "") != "wall":
			continue
		var q: Vector3 = view._wall_spot(int(fl.side), float(fl.u), float(fl.y))[0]
		if p.distance_to(q) < 0.8:
			_next_pattern(fl)
			return true
	flags.append({"at": "wall", "side": loc.side, "u": snappedf(loc.u, 0.001), "y": snappedf(y, 0.01), "pat": randi() % Ornaments.PATTERNS})
	return true


func _next_pattern(fl: Dictionary) -> void:
	fl.pat = (int(fl.get("pat", 0)) + 1) % Ornaments.PATTERNS


## Removes the window, door, dormer, trapdoor, lantern, flag or chimney
## nearest the tap.
func _remove_on_building(b: Dictionary, view: BuildingView, loc: Dictionary, lp: Vector3) -> bool:
	var best_d := 1.1
	var best_list := ""
	var best_item = null
	for fl in b.get("flags", []):
		if fl.get("at", "") == "top":
			if loc.zone != "roof":
				continue
			var tx: float = 0.0 if b.shape == "round" else (float(fl.get("u", 0.5)) - 0.5) * b.size.x
			var dd: float = absf(lp.x - tx) if b.shape != "round" else 0.0
			if dd < best_d:
				best_d = dd
				best_list = "flags"
				best_item = fl
			continue
		var q: Vector3 = view._wall_spot(int(fl.side), float(fl.u), float(fl.y))[0]
		if lp.distance_to(q) < best_d:
			best_d = lp.distance_to(q)
			best_list = "flags"
			best_item = fl
	for lt in b.get("lanterns", []):
		var q2: Vector3 = view._wall_spot(int(lt.side), float(lt.u), float(lt.y))[0]
		if lp.distance_to(q2) < best_d:
			best_d = lp.distance_to(q2)
			best_list = "lanterns"
			best_item = lt
	if best_item != null:
		(b[best_list] as Array).erase(best_item)
		return true
	if loc.zone == "roof":
		for w in b.windows:
			var kind: String = w.get("kind", "")
			if kind == "trapdoor" and Vector2(w.x, w.z).distance_to(Vector2(lp.x, lp.z)) < 1.0:
				b.windows.erase(w)
				return true
			if kind == "dormer" and w.side == (0 if loc.side == 0 else 2) and absf(w.u - loc.u) * b.size.x < 1.0:
				b.windows.erase(w)
				return true
		if b.get("chimney", BuildingView.NO_CHIMNEY) > BuildingView.NO_CHIMNEY + 1.0:
			b.chimney = BuildingView.NO_CHIMNEY
			return true
		return false
	var w2 := _window_at(b, loc, 0.9)
	if w2.is_empty():
		return false
	b.windows.erase(w2)
	return true


# ---------------------------------------------------------------------------
func _tap_wall(hit: Dictionary, mode: String) -> void:
	if mode != "lantern" and mode != "flag" and mode != "remove":
		Sfx.play("nope", -8.0)
		return
	var f := glade.find(hit.id)
	if f.is_empty():
		return
	var wall: Dictionary = f.item
	var hp: Vector3 = hit.point
	var p2 := Vector2(hp.x, hp.z)
	var c := Geo.closest(wall.pts, p2)
	var s: float = c.y
	var t := Geo.tangent_at(wall.pts, s)
	var wp := Geo.point_at(wall.pts, s)
	var side := 1.0 if (p2 - wp).dot(Vector2(-t.y, t.x)) >= 0.0 else -1.0
	var h: float = wall.get("h", 2.4)
	var y := clampf(hp.y - glade.terrain.height_at(hp.x, hp.z), 0.9, maxf(1.0, h - 0.25))
	var orn: Array = wall.get("orn", [])
	wall.orn = orn
	glade.begin_change()
	var near = null
	for o in orn:
		if absf(float(o.s) - s) < 0.7 and float(o.get("side", 1.0)) == side and absf(float(o.y) - y) < 1.0:
			near = o
	match mode:
		"remove":
			if near == null:
				glade.undo_stack.pop_back()
				Sfx.play("nope", -8.0)
				return
			orn.erase(near)
		"lantern":
			if near != null and near.kind == "lantern":
				orn.erase(near)
			else:
				orn.append({"kind": "lantern", "s": snappedf(s, 0.01), "side": side, "y": snappedf(minf(y, 2.2), 0.01)})
		"flag":
			if near != null and near.kind == "banner":
				_next_pattern(near)
			else:
				orn.append({"kind": "banner", "s": snappedf(s, 0.01), "side": side, "y": snappedf(maxf(y, minf(h - 0.2, 2.2)), 0.01),
						"pat": randi() % Ornaments.PATTERNS})
	glade.refresh(wall.id)
	Sfx.play("place_wood", -2.0)
	Settings.vibrate(10)


func _tap_ground(hit: Dictionary, mode: String) -> void:
	var kind := ""
	match mode:
		"lantern":
			kind = "lantern"
		"flag":
			kind = "banner"
	if kind == "" or hit.kind == "prop":
		Sfx.play("nope", -8.0)
		return
	var hp: Vector3 = hit.point
	var c := glade.terrain.clamp_to_play(Vector2(hp.x, hp.z))
	glade.begin_change()
	glade.add_prop(kind, Vector3(c.x, glade.terrain.height_at_v(c), c.y), randf() * TAU, 1.0)
	Sfx.play("place_wood", -2.0)
	Settings.vibrate(10)


func _toggle(b: Dictionary, w: Dictionary, min_gap: float) -> void:
	var span: float = TAU * b.r if b.shape == "round" else (b.size.x if w.side % 2 == 0 else b.size.y)
	var is_dormer: bool = w.kind == "dormer"
	for existing in b.windows:
		if existing.side != w.side:
			continue
		var e_dormer: bool = existing.get("kind", "window") == "dormer"
		if e_dormer != is_dormer:
			continue
		if not is_dormer and existing.f != w.f:
			continue
		var du: float = absf(existing.u - w.u)
		if b.shape == "round":
			du = minf(du, 1.0 - du)
		if du * span < min_gap:
			b.windows.erase(existing)
			return
	b.windows.append(w)
