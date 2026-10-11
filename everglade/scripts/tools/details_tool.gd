class_name DetailsTool
extends BaseTool
## Tap walls of houses to add windows (doors at ground level), tap roofs for
## dormers, or switch to chimney mode. Tap an existing window to remove it.


func _init() -> void:
	tool_id = "details"
	title = "Windows & Doors"
	options = {"mode": "window"}


func option_defs() -> Array:
	return [{"type": "choice", "key": "mode", "items": [
		{"id": "window", "label": "Window", "icon": "window"},
		{"id": "door", "label": "Door", "icon": "door"},
		{"id": "dormer", "label": "Dormer", "icon": "dormer"},
		{"id": "chimney", "label": "Chimney", "icon": "chimney"}]}]


func hint() -> String:
	return "Tap a cottage wall to add a window. Low taps make doors, roof taps add dormers."


func tap(screen: Vector2) -> void:
	var hit := pick(screen, 8)
	if hit.is_empty() or hit.kind != "building":
		Sfx.play("nope", -8.0)
		return
	var f := glade.find(hit.id)
	if f.is_empty():
		return
	var b: Dictionary = f.item
	var view: BuildingView = glade.views.get(b.id)
	if view == null:
		return
	var loc := view.locate(hit.point)
	var mode: String = options.mode
	glade.begin_change()
	if mode == "chimney":
		if b.shape == "round":
			glade.undo_stack.pop_back()
			return
		var u: float = loc.get("x", (loc.u - 0.5) * b.size.x) / b.size.x
		var cur: float = b.get("chimney", BuildingView.NO_CHIMNEY)
		b.chimney = BuildingView.NO_CHIMNEY if absf(cur - u) < 0.12 else clampf(u, -0.45, 0.45)
	elif loc.zone == "roof" or mode == "dormer":
		if b.shape == "round" or b.roof == "flat":
			glade.undo_stack.pop_back()
			Sfx.play("nope", -8.0)
			return
		var side: int = 0 if loc.side == 0 else 2
		if loc.zone != "roof":
			side = 0 if loc.side <= 1 else 2
		_toggle(b, {"side": side, "u": loc.u, "f": 0, "kind": "dormer"}, 1.0)
	else:
		var kind := "door" if mode == "door" or (loc.y < Catalog.PLINTH + 0.9 and loc.f == 0) else "window"
		var f_idx: int = 0 if kind == "door" else loc.f
		_toggle(b, {"side": loc.side, "u": loc.u, "f": f_idx, "kind": kind}, 0.9)
	glade.refresh(b.id)
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
