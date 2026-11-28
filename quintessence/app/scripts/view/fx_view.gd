class_name FxView
extends Node2D
## Physical score effects: gold leaf (Light), ink drops (Gravity), rubber stamp (Reading),
## wax seal (Insight), gold storm (big scores). Short-lived items are reused from arrays.

var flakes: Array = []   # {a, b, ctrl, t, dur, rot, spin, size}
var drops: Array = []    # {a, b, t, dur, r}
var splats: Array = []   # {p, t}
var storm: Array = []    # {p, v, rot, spin, size, life}
var stamp := {}          # {text, t, hold, pos}
var seal := {}           # {value, pos, t, r}
var speed := 1.0


func busy() -> bool:
	return not (flakes.is_empty() and drops.is_empty())


func clear_all() -> void:
	flakes.clear()
	drops.clear()
	splats.clear()
	storm.clear()
	stamp = {}
	seal = {}
	queue_redraw()


func gold_flakes(from: Vector2, to: Vector2, count: int, dur: float) -> void:
	for i in count:
		var spread := Vector2(randf_range(-40, 40), randf_range(-30, 20))
		var lift := Vector2(randf_range(-60, 60), -randf_range(80, 160))
		flakes.append({"a": from + spread * 0.4, "b": to + Vector2(randf_range(-14, 14), randf_range(-8, 8)),
			"ctrl": from.lerp(to, 0.35) + lift, "t": -i * 0.04, "dur": dur,
			"rot": randf() * TAU, "spin": randf_range(-9, 9), "size": randf_range(5, 10)})


func ink_drops(from: Vector2, to: Vector2, count: int, dur: float) -> void:
	for i in count:
		drops.append({"a": from + Vector2(randf_range(-20, 20), randf_range(-10, 10)), "b": to + Vector2(randf_range(-18, 18), randf_range(-6, 6)),
			"t": -i * 0.07, "dur": dur, "r": randf_range(4, 7)})


func gold_storm(count: int) -> void:
	for i in count:
		storm.append({"p": Vector2(randf_range(0, 720), randf_range(1150, 1320)), "v": Vector2(randf_range(-40, 40), -randf_range(260, 520)),
			"rot": randf() * TAU, "spin": randf_range(-8, 8), "size": randf_range(6, 13), "life": randf_range(1.6, 2.6)})


func show_stamp(text: String, pos: Vector2) -> void:
	stamp = {"text": text, "t": 0.0, "pos": pos}


func show_seal(value: int, pos: Vector2) -> void:
	seal = {"value": value, "pos": pos, "t": 0.0, "r": 56.0}


func _process(delta: float) -> void:
	var d := delta * maxf(speed, 1.0)
	var i := flakes.size() - 1
	while i >= 0:
		var f: Dictionary = flakes[i]
		f["t"] += d / f["dur"]
		f["rot"] += f["spin"] * d
		if f["t"] >= 1.0:
			flakes.remove_at(i)
		i -= 1
	i = drops.size() - 1
	while i >= 0:
		var dr: Dictionary = drops[i]
		dr["t"] += d / dr["dur"]
		if dr["t"] >= 1.0:
			splats.append({"p": dr["b"], "t": 0.0})
			drops.remove_at(i)
		i -= 1
	i = splats.size() - 1
	while i >= 0:
		splats[i]["t"] += d * 2.0
		if splats[i]["t"] >= 1.0:
			splats.remove_at(i)
		i -= 1
	i = storm.size() - 1
	while i >= 0:
		var s: Dictionary = storm[i]
		s["v"].y += 140.0 * delta
		s["v"].x += sin(s["rot"]) * 30.0 * delta
		s["p"] += s["v"] * delta
		s["rot"] += s["spin"] * delta
		s["life"] -= delta
		if s["life"] <= 0.0:
			storm.remove_at(i)
		i -= 1
	if not stamp.is_empty():
		stamp["t"] += d
	if not seal.is_empty():
		seal["t"] += d
	queue_redraw()


func _flake(p: Vector2, rot: float, size: float, alpha := 1.0) -> void:
	var w := size
	var h := size * (0.35 + 0.65 * absf(sin(rot)))
	var pts := PackedVector2Array([Vector2(-w, -h * 0.4), Vector2(w * 0.7, -h), Vector2(w, h * 0.5), Vector2(-w * 0.5, h)])
	draw_set_transform(p, rot, Vector2.ONE)
	draw_colored_polygon(pts, Color(Art.GOLD, alpha))
	draw_line(pts[0], pts[2], Color(Art.GOLD_HI, alpha * (0.5 + 0.5 * sin(rot * 2.0))), 1.5)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw() -> void:
	for f in flakes:
		var t: float = f["t"]
		if t < 0.0:
			continue
		var e := t * t * (3.0 - 2.0 * t)
		var p: Vector2 = (f["a"] as Vector2).lerp(f["ctrl"], e).lerp((f["ctrl"] as Vector2).lerp(f["b"], e), e)
		_flake(p, f["rot"], f["size"])
	for dr in drops:
		var t: float = dr["t"]
		if t < 0.0:
			continue
		var p: Vector2 = (dr["a"] as Vector2).lerp(dr["b"], t * t)
		p.y -= sin(t * PI) * 40.0
		var r: float = dr["r"]
		draw_circle(p, r, Art.INK)
		draw_colored_polygon(PackedVector2Array([p + Vector2(-r * 0.8, -r * 0.4), p + Vector2(0, -r * 2.4), p + Vector2(r * 0.8, -r * 0.4)]), Art.INK)
		draw_circle(p + Vector2(-r * 0.35, -r * 0.3), r * 0.25, Color(Art.BONE, 0.6))
	for sp in splats:
		var t: float = sp["t"]
		draw_arc(sp["p"], 6.0 + 18.0 * t, 0, TAU, 18, Color(Art.INK, 1.0 - t), 2.0)
	for s in storm:
		_flake(s["p"], s["rot"], s["size"], clampf(s["life"], 0.0, 1.0))
	if not stamp.is_empty():
		var t: float = stamp["t"]
		var k := 1.0 + maxf(0.0, 0.5 - t * 3.0)
		var a := clampf(t * 8.0, 0.0, 1.0) * clampf(1.6 - t * 0.9, 0.0, 1.0)
		if a > 0.0:
			draw_set_transform(stamp["pos"], -0.09, Vector2(k, k))
			var txt: String = stamp["text"]
			var w := txt.length() * 21.0 + 50.0
			draw_rect(Rect2(-w / 2, -38, w, 64), Color(Art.VERMILION, 0.9 * a), false, 4.0)
			draw_rect(Rect2(-w / 2 + 6, -32, w - 12, 52), Color(Art.VERMILION, 0.5 * a), false, 1.5)
			Art.text(self, Art.font_sc, Vector2(0, 8), txt.to_upper(), 36, Color(Art.VERMILION, a))
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	if not seal.is_empty():
		var t: float = seal["t"]
		var k := 1.0 + maxf(0.0, 0.6 - t * 4.0)
		var a := clampf(1.8 - t * 1.2, 0.0, 1.0)
		if a > 0.0:
			draw_set_transform(seal["pos"], 0.12, Vector2(k, k))
			draw_circle(Vector2(4, 6), seal["r"], Color(0, 0, 0, 0.4 * a))
			Art.wax_seal(self, Vector2.ZERO, seal["r"], str(seal["value"]), int(seal["value"]))
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
