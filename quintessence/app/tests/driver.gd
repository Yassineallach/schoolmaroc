extends Node
## Gameplay driver: loads the real main scene and plays it ONLY through pointer events
## (Input.parse_input_event) at on-screen positions. It reads Main's state to decide what
## to tap (read-only), captures screenshots, and writes an input trace.
## Run: xvfb-run godot --path app --resolution 720x1280 res://tests/driver.tscn -- --out=DIR

var main: Node
var out_dir := "user://shots"
var trace: Array = []
var shot_i := 0
var t0 := 0
var short := false


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		if a == "--short":
			short = true
	DirAccess.make_dir_recursive_absolute(out_dir)
	if FileAccess.file_exists("user://run.json"):
		DirAccess.remove_absolute(ProjectSettings.globalize_path("user://run.json"))
	t0 = Time.get_ticks_msec()
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	_run.call_deferred()


func frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func secs(t: float) -> void:
	await get_tree().create_timer(t).timeout


func shot(name: String) -> void:
	await frames(2)
	var img := get_viewport().get_texture().get_image()
	shot_i += 1
	img.save_png("%s/%02d-%s.png" % [out_dir, shot_i, name])


func tap(p: Vector2, label := "") -> void:
	trace.append({"ms": Time.get_ticks_msec() - t0, "type": "tap", "x": p.x, "y": p.y, "label": label})
	var m := InputEventMouseMotion.new()
	m.position = p
	Input.parse_input_event(m)
	var d := InputEventMouseButton.new()
	d.button_index = MOUSE_BUTTON_LEFT
	d.pressed = true
	d.position = p
	Input.parse_input_event(d)
	await frames(2)
	var u := InputEventMouseButton.new()
	u.button_index = MOUSE_BUTTON_LEFT
	u.pressed = false
	u.position = p
	Input.parse_input_event(u)
	await frames(3)


func drag(a: Vector2, b: Vector2, label := "") -> void:
	trace.append({"ms": Time.get_ticks_msec() - t0, "type": "drag", "x": a.x, "y": a.y, "x2": b.x, "y2": b.y, "label": label})
	var d := InputEventMouseButton.new()
	d.button_index = MOUSE_BUTTON_LEFT
	d.pressed = true
	d.position = a
	Input.parse_input_event(d)
	await frames(2)
	for k in 10:
		var m := InputEventMouseMotion.new()
		m.position = a.lerp(b, (k + 1) / 10.0)
		Input.parse_input_event(m)
		await frames(1)
	var u := InputEventMouseButton.new()
	u.button_index = MOUSE_BUTTON_LEFT
	u.pressed = false
	u.position = b
	Input.parse_input_event(u)
	await frames(3)


func button(id: String) -> void:
	for b in main.hud.buttons:
		if b["id"] == id:
			await tap((b["rect"] as Rect2).get_center(), id)
			return
	push_error("button not found: " + id)
	trace.append({"type": "missing", "label": id})


func wait_idle() -> void:
	var guard := 0
	while main.busy and guard < 2000:
		await frames(1)
		guard += 1
	await frames(4)


func card_pos(id: int) -> Vector2:
	return (main.views[id] as CardView).global_position


func best_play() -> Array:
	var s: RunState = main.state
	var best := []
	var best_v := -1
	var blocked := s.blocked_positions()
	var open: Array = []
	for p in 3:
		if not blocked.has(p) and s.spread[p] == null:
			open.append(p)
	var n := s.hand.size()
	for i in n:
		for j in range(i, n):
			for k in range(j, n):
				var idx := {i: true, j: true, k: true}
				var cards: Array = []
				for key in idx.keys():
					cards.append(s.hand[key])
				for a in open:
					for b in open:
						for c in open:
							var perm := [a, b, c].slice(0, cards.size())
							var u := {}
							for x in perm:
								u[x] = true
							if u.size() != perm.size():
								continue
							var sp: Array = [null, null, null]
							for q in cards.size():
								sp[perm[q]] = cards[q]
							var v := int(Scoring.evaluate(sp, s.score_context())["insight"])
							if v > best_v:
								best_v = v
								best = [cards, perm]
	return best


func play_reading(capture := false) -> void:
	var pick := best_play()
	var cards: Array = pick[0]
	var perm: Array = pick[1]
	for q in cards.size():
		var id := int(cards[q]["id"])
		await drag(card_pos(id), main.SPREAD_CENTERS[perm[q]], "lay %s -> %s" % [Cards.title(cards[q]), Scoring.POS_NAMES[perm[q]]])
		await secs(0.35)
	if capture:
		await shot("preview")
	var before: int = main.state.readings_left
	await button("read")
	if capture:
		await secs(0.7)
		await shot("scoring-stamp")
		await secs(0.9)
		await shot("scoring-flakes")
	await wait_idle()
	assert(main.state.readings_left == before - 1 or main.state.phase != "play")


func _run() -> void:
	await secs(1.0)
	await shot("title")
	await button("new")
	await secs(0.4)
	await shot("patron")
	# Take a Patron that gives visible effects.
	var pick := 0
	for i in main.state.patron_offers.size():
		if main.state.patron_offers[i] in ["star", "sun", "hermit", "magician"]:
			pick = i
	await button("patron:%d" % pick)
	await secs(0.3)
	await shot("intro-curious")
	await button("begin")
	await secs(1.0)
	await shot("play-dealt")
	# Tap-to-lay on the first card, then tap it in the spread to return it.
	var first := int(main.display_hand()[0]["id"])
	await tap(card_pos(first), "tap lay")
	await secs(0.4)
	var laid: bool = main.state.laid_count() == 1
	await tap(card_pos(first), "tap return")
	await secs(0.4)
	trace.append({"type": "check", "label": "tap lay + return", "ok": laid and main.state.laid_count() == 0})
	# Reshuffle two cards through the UI.
	await button("reshuffle")
	var h: Array = main.display_hand()
	await tap(card_pos(int(h[0]["id"])), "mark")
	await tap(card_pos(int(h[1]["id"])), "mark")
	await secs(0.3)
	await shot("reshuffle-marked")
	await button("discard")
	await wait_idle()
	trace.append({"type": "check", "label": "reshuffle consumed", "ok": main.state.reshuffles_left == 2 and main.state.hand.size() == 8})
	await play_reading(true)
	await shot("after-first-reading")
	var guard := 0
	while guard < 60:
		guard += 1
		var ph: String = main.state.phase
		if ph == "play":
			if main.state.night == 1 and main.state.reading_number() == 2:
				await shot("troubled-shadow-preview")
			if main.state.night == 2 and main.state.reading_number() == 1 and main.speed_i == 0:
				await shot("twin-start")
				await button("speed")
				await button("speed")
			await play_reading(main.state.night == 1 and main.state.reading_number() == 3)
		elif ph == "won":
			await secs(0.5)
			await shot("won-night-%d" % (main.state.night + 1))
			if short:
				await secs(1.0)
				break
			await button("onward")
			await secs(0.3)
		elif ph == "market":
			await shot("market")
			for i in main.state.market.size():
				var it: Dictionary = main.state.market[i]
				if it["kind"] == "major" and not it["sold"] and main.state.coins >= int(it["price"]) and main.state.arcana.size() < 5:
					await button("buy:%d" % i)
			for i in main.state.market.size():
				var it: Dictionary = main.state.market[i]
				if it["kind"] == "sigil" and not it["sold"] and main.state.coins >= int(it["price"]):
					await button("buy:%d" % i)
			await shot("market-bought")
			# Save/restore check through the real UI: go to title, then Continue.
			var before := JSON.stringify(main.state.to_dict())
			main._notification(NOTIFICATION_WM_GO_BACK_REQUEST)
			await secs(0.3)
			await button("continue")
			await secs(0.3)
			trace.append({"type": "check", "label": "back + continue restores run", "ok": JSON.stringify(main.state.to_dict()) == before})
			await button("leave")
			await secs(0.3)
			await shot("intro-%s" % main.state.night_info()["id"])
			await button("begin")
			await secs(0.9)
		elif ph == "intro":
			await button("begin")
		elif ph in ["victory", "defeat"]:
			await secs(0.6)
			await shot(ph)
			break
	trace.append({"type": "result", "phase": main.state.phase, "night": main.state.night,
		"insight": main.state.insight, "stats": main.state.stats, "arcana": main.state.arcana})
	# Restart from the end screen through the button.
	await button("new")
	await secs(0.3)
	trace.append({"type": "check", "label": "restart resets", "ok": main.state.phase == "patron" and main.views.is_empty() and main.state.coins == RunState.START_COINS})
	var f := FileAccess.open(out_dir + "/trace.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(trace, "  "))
	f.close()
	print("DRIVER DONE phase=%s" % main.state.phase)
	get_tree().quit()
