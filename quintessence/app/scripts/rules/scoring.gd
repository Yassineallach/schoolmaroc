class_name Scoring
extends RefCounted
## Pure scoring. Insight = Light x Gravity (x Tower). Fate is fixed at 1 in Cycle 1.
## spread: Array of 3 slots (card Dictionary or null): 0 Past, 1 Present, 2 Future.
## ctx keys: levels (Dictionary), arcana (Array[String] in slot order), twin_used
## (Dictionary suit->true or empty), twin (bool), owned (int), tower_armed (bool),
## death_bonus (int).
## Every step records running totals so the view can animate exactly what was scored.

const PAST := 0
const PRESENT := 1
const FUTURE := 2
const POS_NAMES: Array[String] = ["Past", "Present", "Future"]


static func evaluate(spread: Array, ctx: Dictionary) -> Dictionary:
	var laid: Array = []
	var positions: Array[int] = []
	for i in spread.size():
		if spread[i] != null:
			laid.append(spread[i])
			positions.append(i)
	var res := {"reading": "", "light": 0, "gravity": 0, "mult": 1, "insight": 0,
		"steps": [], "count": laid.size()}
	if laid.is_empty():
		return res
	var arc: Array = ctx.get("arcana", [])
	var steps: Array = []

	var rid := Readings.detect(laid)
	var lovers := false
	if rid == "echo" and arc.has("lovers"):
		rid = "triad"
		lovers = true
	var levels: Dictionary = ctx.get("levels", {})
	var lv := int(levels.get(rid, 1))
	var base := Readings.base_values(rid, lv)
	var light := base.x
	var gravity := base.y
	res["reading"] = rid
	steps.append({"kind": "reading", "id": rid, "level": lv, "light": light, "gravity": gravity,
		"light_total": light, "gravity_total": gravity})

	var twin_used: Dictionary = ctx.get("twin_used", {})
	var twin: bool = ctx.get("twin", false)
	var seed_mult := 1
	for k in laid.size():
		var c: Dictionary = laid[k]
		var pos := positions[k]
		var amt := int(c["rank"])
		var notes: Array[String] = []
		if seed_mult > 1:
			amt *= seed_mult
			notes.append("Seed x2")
			seed_mult = 1
		if twin and twin_used.has(int(c["suit"])):
			amt = floori(amt / 2.0)
			notes.append("The Twin 1/2")
		if pos == PRESENT and arc.has("sun"):
			amt *= 2
			notes.append("The Sun x2")
		if pos == PAST:
			amt *= 2
			notes.append("Past x2")
		elif pos == FUTURE:
			amt = floori(amt / 2.0)
			notes.append("Future 1/2")
		if int(c["rank"]) == 1:
			seed_mult = 2
		light += amt
		steps.append({"kind": "card", "pos": pos, "card_id": int(c["id"]), "light": amt,
			"notes": notes, "light_total": light, "gravity_total": gravity})

	if spread[PRESENT] != null:
		var g := 3 if Cards.is_court(spread[PRESENT]) else 2
		gravity += g
		steps.append({"kind": "position", "pos": PRESENT, "gravity": g,
			"light_total": light, "gravity_total": gravity})

	var mult := 1
	for slot in arc.size():
		var id: String = arc[slot]
		var dl := 0
		var dg := 0
		var gm := 1
		var im := 1
		match id:
			"magician":
				var s := {}
				for c in laid:
					s[int(c["suit"])] = true
				if s.size() >= 3:
					dg = 3
			"empress":
				dl = floori(int(ctx.get("owned", 56)) / 4.0)
			"lovers":
				if not lovers:
					continue
			"hermit":
				if laid.size() == 1:
					gm = 3
			"death":
				dl = int(ctx.get("death_bonus", 0))
			"tower":
				if ctx.get("tower_armed", false):
					im = 5
			"star":
				for c in laid:
					if int(c["suit"]) == 1:
						dg += 1
			"sun":
				if spread[PRESENT] == null:
					continue
		if dl == 0 and dg == 0 and gm == 1 and im == 1 and id != "lovers" and id != "sun":
			continue
		light += dl
		gravity = (gravity + dg) * gm
		mult *= im
		steps.append({"kind": "arcana", "slot": slot, "id": id, "light": dl, "gravity": dg,
			"gravity_mult": gm, "insight_mult": im, "light_total": light, "gravity_total": gravity})

	res["light"] = light
	res["gravity"] = gravity
	res["mult"] = mult
	res["insight"] = light * gravity * mult
	res["steps"] = steps
	return res
