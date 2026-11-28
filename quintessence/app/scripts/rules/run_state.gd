class_name RunState
extends RefCounted
## Whole-run simulation for the Cycle 1 slice. No rendering here.
## Phases: patron -> intro -> play -> (won -> market -> intro ...) | defeat | victory

const HAND_SIZE := 8
const READINGS := 4
const RESHUFFLES := 3
const START_COINS := 4
const MINOR_PRICE := 3
const SIGIL_PRICE := 3
const REROLL_PRICE := 2
const SAVE_VERSION := 1

const NIGHTS := [
	{"id": "curious", "name": "The Curious", "target": 600, "reward": 3, "shadow": 0, "rule": "",
		"line": "A young clerk asks if the letter will come."},
	{"id": "troubled", "name": "The Troubled", "target": 900, "reward": 4, "shadow": 1, "rule": "",
		"line": "A widower asks what the house remembers."},
	{"id": "twin", "name": "The Twin", "target": 1200, "reward": 5, "shadow": 2, "rule": "twin",
		"line": "Two sisters, one question. A suit already read this Night gives half Light."},
]

var seed_value := 0
var rng := RandomNumberGenerator.new()
var phase := "patron"
var night := 0
var coins := START_COINS
var deck: Array = []          # every card owned
var draw: Array = []
var hand: Array = []
var discard: Array = []
var spread: Array = [null, null, null]
var readings_left := READINGS
var reshuffles_left := RESHUFFLES
var insight := 0
var arcana: Array = []        # Major ids in slot order
var levels := {}              # reading id -> level
var twin_used := {}
var intents: Array = []       # {apply_at:int, pos:int}
var death_bonus := 0
var death_used := false
var tower_armed := false
var tower_used := false
var market: Array = []
var patron_offers: Array = []
var next_card_id := 56
var last_reward := {}
var stats := {"best_reading": 0, "best_reading_name": "", "total_insight": 0, "readings": 0}


func new_run(p_seed: int) -> void:
	seed_value = p_seed
	rng.seed = p_seed
	phase = "patron"
	night = 0
	coins = START_COINS
	deck = Cards.standard_deck()
	draw = []
	hand = []
	discard = []
	spread = [null, null, null]
	arcana = []
	levels = {}
	death_bonus = 0
	market = []
	next_card_id = 56
	last_reward = {}
	stats = {"best_reading": 0, "best_reading_name": "", "total_insight": 0, "readings": 0}
	var pool: Array = ArcanaDB.POOL.duplicate()
	_shuffle(pool)
	patron_offers = pool.slice(0, 3)


func night_info() -> Dictionary:
	return NIGHTS[night]


func target() -> int:
	return int(night_info()["target"])


func choose_patron(i: int) -> bool:
	if phase != "patron" or i < 0 or i >= patron_offers.size():
		return false
	arcana.append(patron_offers[i])
	patron_offers = []
	phase = "intro"
	return true


func start_night() -> bool:
	if phase != "intro":
		return false
	draw = deck.duplicate()
	_shuffle(draw)
	hand = []
	discard = []
	spread = [null, null, null]
	readings_left = READINGS
	reshuffles_left = RESHUFFLES
	insight = 0
	twin_used = {}
	intents = []
	death_used = false
	tower_armed = false
	tower_used = false
	_draw_to_full()
	phase = "play"
	return true


## 1-based number of the Reading about to be made.
func reading_number() -> int:
	return READINGS - readings_left + 1


func blocked_positions() -> Array:
	var out: Array = []
	for it in intents:
		if int(it["apply_at"]) == reading_number():
			out.append(int(it["pos"]))
	return out


func upcoming_intents() -> Array:
	var out: Array = []
	for it in intents:
		if int(it["apply_at"]) > reading_number():
			out.append(it)
	return out


func hand_index(card_id: int) -> int:
	for i in hand.size():
		if int(hand[i]["id"]) == card_id:
			return i
	return -1


func place(card_id: int, pos: int) -> bool:
	if phase != "play" or pos < 0 or pos > 2 or spread[pos] != null:
		return false
	if blocked_positions().has(pos):
		return false
	var i := hand_index(card_id)
	if i < 0:
		return false
	spread[pos] = hand[i]
	hand.remove_at(i)
	return true


func first_open_position() -> int:
	var blocked := blocked_positions()
	for p in 3:
		if spread[p] == null and not blocked.has(p):
			return p
	return -1


func unplace(pos: int) -> bool:
	if phase != "play" or pos < 0 or pos > 2 or spread[pos] == null:
		return false
	hand.append(spread[pos])
	spread[pos] = null
	return true


func clear_spread() -> void:
	for p in 3:
		if spread[p] != null:
			unplace(p)


func laid_count() -> int:
	var n := 0
	for c in spread:
		if c != null:
			n += 1
	return n


func score_context() -> Dictionary:
	return {"levels": levels, "arcana": arcana, "twin_used": twin_used,
		"twin": night_info()["rule"] == "twin", "owned": deck.size(),
		"tower_armed": tower_armed, "death_bonus": death_bonus}


func preview() -> Dictionary:
	return Scoring.evaluate(spread, score_context())


func can_arm_tower() -> bool:
	return phase == "play" and arcana.has("tower") and not tower_used


func toggle_tower() -> bool:
	if not can_arm_tower():
		return false
	tower_armed = not tower_armed
	return true


## Scores the spread. Returns {} when the Reading is not allowed.
func read() -> Dictionary:
	if phase != "play" or readings_left <= 0 or laid_count() == 0:
		return {}
	var result := preview()
	var events := {"destroyed": [], "returned": -1, "new_intent": null, "death_gain": 0,
		"to_discard": [], "drawn": []}
	insight += int(result["insight"])
	readings_left -= 1
	stats["readings"] = int(stats["readings"]) + 1
	stats["total_insight"] = int(stats["total_insight"]) + int(result["insight"])
	if int(result["insight"]) > int(stats["best_reading"]):
		stats["best_reading"] = int(result["insight"])
		stats["best_reading_name"] = Readings.DEFS[result["reading"]]["name"]

	var laid: Array = []
	for c in spread:
		if c != null:
			laid.append(c)
			twin_used[int(c["suit"])] = true

	var destroyed := {}
	if tower_armed:
		tower_used = true
		tower_armed = false
		for c in laid:
			destroyed[int(c["id"])] = true
	if arcana.has("death") and not death_used:
		death_used = true
		var low: Dictionary = laid[0]
		for c in laid:
			if int(c["rank"]) < int(low["rank"]):
				low = c
		destroyed[int(low["id"])] = true
		death_bonus += int(low["rank"])
		events["death_gain"] = int(low["rank"])

	for p in 3:
		var c = spread[p]
		if c == null:
			continue
		var cid := int(c["id"])
		if destroyed.has(cid):
			_remove_from_deck(cid)
			events["destroyed"].append(cid)
		elif p == Scoring.FUTURE:
			hand.append(c)
			events["returned"] = cid
		else:
			discard.append(c)
			events["to_discard"].append(cid)
		spread[p] = null

	if insight >= target():
		_win()
	elif readings_left == 0:
		phase = "defeat"
	else:
		var before := {}
		for c in hand:
			before[int(c["id"])] = true
		_draw_to_full()
		for c in hand:
			if not before.has(int(c["id"])):
				events["drawn"].append(int(c["id"]))
		events["new_intent"] = _plan_shadow()
	result["events"] = events
	return result


func reshuffle(card_ids: Array) -> bool:
	if phase != "play" or reshuffles_left <= 0 or card_ids.is_empty():
		return false
	var seen := {}
	for cid in card_ids:
		if seen.has(cid) or hand_index(int(cid)) < 0:
			return false
		seen[cid] = true
	for cid in card_ids:
		var i := hand_index(int(cid))
		discard.append(hand[i])
		hand.remove_at(i)
	reshuffles_left -= 1
	_draw_to_full()
	return true


func _plan_shadow() -> Variant:
	var level := int(night_info()["shadow"])
	var done := READINGS - readings_left
	var plan := false
	if level >= 1 and done == 1:
		plan = true
	if level >= 2 and done == 2:
		plan = true
	if not plan:
		return null
	var it := {"apply_at": done + 2, "pos": rng.randi_range(0, 2)}
	intents.append(it)
	return it


func _win() -> void:
	var info := night_info()
	var interest := mini(floori(coins / 5.0), 5)
	last_reward = {"base": int(info["reward"]), "unused": readings_left, "interest": interest}
	last_reward["total"] = int(info["reward"]) + readings_left + interest
	coins += int(last_reward["total"])
	# Cards still in play return to the deck pool; the deck list is unchanged.
	phase = "won"


func continue_after_win() -> bool:
	if phase != "won":
		return false
	if night >= NIGHTS.size() - 1:
		phase = "victory"
	else:
		phase = "market"
		_roll_market()
	return true


func _roll_market() -> void:
	market = []
	var majors: Array = []
	for id in ArcanaDB.POOL:
		if not arcana.has(id):
			majors.append(id)
	_shuffle(majors)
	for i in mini(2, majors.size()):
		market.append({"kind": "major", "id": majors[i], "price": ArcanaDB.PRICE, "sold": false})
	for i in 2:
		var suit := rng.randi_range(0, 3)
		var rank := rng.randi_range(1, 14)
		market.append({"kind": "minor", "card": Cards.make(-1, suit, rank), "price": MINOR_PRICE, "sold": false})
	var rid: String = Readings.ORDER[rng.randi_range(1, Readings.ORDER.size() - 1)]
	market.append({"kind": "sigil", "id": rid, "price": SIGIL_PRICE, "sold": false})


func buy(i: int) -> bool:
	if phase != "market" or i < 0 or i >= market.size():
		return false
	var it: Dictionary = market[i]
	if it["sold"] or coins < int(it["price"]):
		return false
	match it["kind"]:
		"major":
			if arcana.size() >= ArcanaDB.MAX_SLOTS or arcana.has(it["id"]):
				return false
			arcana.append(it["id"])
		"minor":
			var c: Dictionary = it["card"]
			deck.append(Cards.make(next_card_id, int(c["suit"]), int(c["rank"])))
			next_card_id += 1
		"sigil":
			levels[it["id"]] = int(levels.get(it["id"], 1)) + 1
	coins -= int(it["price"])
	it["sold"] = true
	return true


func sell_arcana(slot: int) -> bool:
	if phase != "market" or slot < 0 or slot >= arcana.size():
		return false
	arcana.remove_at(slot)
	coins += ArcanaDB.SELL
	return true


func reroll() -> bool:
	if phase != "market" or coins < REROLL_PRICE:
		return false
	coins -= REROLL_PRICE
	_roll_market()
	return true


func leave_market() -> bool:
	if phase != "market":
		return false
	night += 1
	phase = "intro"
	return true


func card_count_total() -> int:
	return draw.size() + hand.size() + discard.size() + laid_count()


func _remove_from_deck(cid: int) -> void:
	for i in deck.size():
		if int(deck[i]["id"]) == cid:
			deck.remove_at(i)
			return


func _draw_to_full() -> void:
	while hand.size() < HAND_SIZE:
		if draw.is_empty():
			if discard.is_empty():
				return
			draw = discard
			discard = []
			_shuffle(draw)
		hand.append(draw.pop_back())


func _shuffle(arr: Array) -> void:
	for i in range(arr.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = arr[i]
		arr[i] = arr[j]
		arr[j] = t


func to_dict() -> Dictionary:
	return {"v": SAVE_VERSION, "seed": seed_value, "rng_state": str(rng.state), "phase": phase,
		"night": night, "coins": coins, "deck": deck, "draw": draw, "hand": hand,
		"discard": discard, "spread": spread, "readings_left": readings_left,
		"reshuffles_left": reshuffles_left, "insight": insight, "arcana": arcana,
		"levels": levels, "twin_used": twin_used.keys(), "intents": intents,
		"death_bonus": death_bonus, "death_used": death_used, "tower_armed": tower_armed,
		"tower_used": tower_used, "market": market, "patron_offers": patron_offers,
		"next_card_id": next_card_id, "last_reward": last_reward, "stats": stats}


## Restores from a saved dictionary. Returns false (state untouched) when the data is invalid.
func from_dict(d: Dictionary) -> bool:
	if int(d.get("v", 0)) != SAVE_VERSION:
		return false
	var required := ["seed", "rng_state", "phase", "night", "coins", "deck", "draw", "hand",
		"discard", "spread", "arcana"]
	for k in required:
		if not d.has(k):
			return false
	if not (d["phase"] in ["patron", "intro", "play", "won", "market", "defeat", "victory"]):
		return false
	if int(d["night"]) < 0 or int(d["night"]) >= NIGHTS.size():
		return false
	seed_value = int(d["seed"])
	rng.seed = seed_value
	rng.state = int(str(d["rng_state"]))
	phase = d["phase"]
	night = int(d["night"])
	coins = int(d["coins"])
	deck = _cards(d["deck"])
	draw = _cards(d["draw"])
	hand = _cards(d["hand"])
	discard = _cards(d["discard"])
	spread = []
	for c in d["spread"]:
		spread.append(null if c == null else _card(c))
	readings_left = int(d.get("readings_left", READINGS))
	reshuffles_left = int(d.get("reshuffles_left", RESHUFFLES))
	insight = int(d.get("insight", 0))
	arcana = []
	for a in d["arcana"]:
		arcana.append(str(a))
	levels = {}
	var lv: Dictionary = d.get("levels", {})
	for k in lv:
		levels[str(k)] = int(lv[k])
	twin_used = {}
	for s in d.get("twin_used", []):
		twin_used[int(s)] = true
	intents = []
	for it in d.get("intents", []):
		intents.append({"apply_at": int(it["apply_at"]), "pos": int(it["pos"])})
	death_bonus = int(d.get("death_bonus", 0))
	death_used = bool(d.get("death_used", false))
	tower_armed = bool(d.get("tower_armed", false))
	tower_used = bool(d.get("tower_used", false))
	market = []
	for it in d.get("market", []):
		var m: Dictionary = (it as Dictionary).duplicate(true)
		m["price"] = int(m["price"])
		if m.has("card"):
			m["card"] = _card(m["card"])
		market.append(m)
	patron_offers = []
	for p in d.get("patron_offers", []):
		patron_offers.append(str(p))
	next_card_id = int(d.get("next_card_id", 56))
	last_reward = {}
	var lr: Dictionary = d.get("last_reward", {})
	for k in lr:
		last_reward[str(k)] = int(lr[k])
	var st: Dictionary = d.get("stats", {})
	stats = {"best_reading": int(st.get("best_reading", 0)),
		"best_reading_name": str(st.get("best_reading_name", "")),
		"total_insight": int(st.get("total_insight", 0)), "readings": int(st.get("readings", 0))}
	return true


func _card(c: Dictionary) -> Dictionary:
	return Cards.make(int(c["id"]), int(c["suit"]), int(c["rank"]))


func _cards(arr: Array) -> Array:
	var out: Array = []
	for c in arr:
		out.append(_card(c))
	return out
