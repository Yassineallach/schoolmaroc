extends SceneTree
## Headless rules tests: godot --headless --path app -s res://tests/run_tests.gd
## Unit tests below build fixtures directly; the bot section plays whole runs only through
## the public RunState API (place/read/reshuffle/buy).

var failures := 0
var passes := 0


func _init() -> void:
	test_detect()
	test_scoring_values()
	test_seed_and_future()
	test_read_rules()
	test_reshuffle_rules()
	test_shadow_block()
	test_twin()
	test_market()
	test_save_roundtrip()
	test_bad_save()
	bot_report()
	print("RESULT: %d passed, %d failed" % [passes, failures])
	quit(1 if failures > 0 else 0)


func check(cond: bool, msg: String) -> void:
	if cond:
		passes += 1
	else:
		failures += 1
		print("FAIL: ", msg)


func c(id: int, suit: int, rank: int) -> Dictionary:
	return Cards.make(id, suit, rank)


func test_detect() -> void:
	check(Readings.detect([c(0, 0, 7)]) == "glimpse", "single card is glimpse")
	check(Readings.detect([c(0, 0, 7), c(1, 1, 7)]) == "echo", "pair is echo")
	check(Readings.detect([c(0, 0, 7), c(1, 1, 7), c(2, 2, 7)]) == "triad", "triad")
	check(Readings.detect([c(0, 0, 4), c(1, 1, 5), c(2, 2, 6)]) == "path", "path")
	check(Readings.detect([c(0, 1, 2), c(1, 1, 9), c(2, 1, 13)]) == "harmony", "harmony")
	check(Readings.detect([c(0, 0, 11), c(1, 1, 13), c(2, 2, 14)]) == "court", "court")
	check(Readings.detect([c(0, 3, 11), c(1, 3, 12), c(2, 3, 13)]) == "river", "court run in one suit is river")
	check(Readings.detect([c(0, 0, 4), c(1, 0, 6), c(2, 0, 5)]) == "river", "unsorted river")
	check(Readings.detect([c(0, 0, 13), c(1, 1, 14), c(2, 2, 1)]) == "glimpse", "no wraparound path")
	check(Readings.detect([]) == "", "empty")


func test_scoring_values() -> void:
	# Past 7 Cups, Present 7 Wands: Echo 10/2. Light 10 + 14 + 7 = 31. Gravity 2 + 2 = 4.
	var r := Scoring.evaluate([c(0, 1, 7), c(1, 0, 7), null], {})
	check(r["reading"] == "echo", "echo detected in spread")
	check(r["light"] == 31 and r["gravity"] == 4 and r["insight"] == 124, "echo value 124, got %s" % r["insight"])
	# Court in Present gives +3 Gravity.
	r = Scoring.evaluate([null, c(0, 0, 13), null], {})
	check(r["gravity"] == 1 + 3 and r["light"] == 5 + 13, "court present gravity")
	# Hermit x3 on a single card.
	r = Scoring.evaluate([null, c(0, 0, 9), null], {"arcana": ["hermit"]})
	check(r["gravity"] == (1 + 2) * 3, "hermit x3")
	# Star counts Cups.
	r = Scoring.evaluate([c(0, 1, 2), c(1, 1, 9), c(2, 1, 13)], {"arcana": ["star"]})
	check(r["reading"] == "harmony" and r["gravity"] == 4 + 2 + 3, "star +1 per cup")
	# Lovers converts echo to triad values.
	r = Scoring.evaluate([c(0, 1, 7), c(1, 0, 7), null], {"arcana": ["lovers"]})
	check(r["reading"] == "triad" and r["light"] == 30 + 14 + 7, "lovers")
	# Tower x5.
	r = Scoring.evaluate([null, c(0, 0, 9), null], {"arcana": ["tower"], "tower_armed": true})
	check(r["insight"] == (5 + 9) * 3 * 5, "tower x5")
	# Sigil level 2 echo: 20/3.
	r = Scoring.evaluate([c(0, 1, 7), c(1, 0, 7), null], {"levels": {"echo": 2}})
	check(r["light"] == 20 + 14 + 7 and r["gravity"] == 3 + 2, "sigil level")
	# Last step totals equal the result (the view animates these).
	var last: Dictionary = r["steps"][-1]
	check(last["light_total"] == r["light"] and last["gravity_total"] == r["gravity"], "step totals")


func test_seed_and_future() -> void:
	# Ace in Past doubles next card (Present 6 -> 12). Future 9 halved -> 4.
	var r := Scoring.evaluate([c(0, 0, 1), c(1, 1, 6), c(2, 2, 9)], {})
	check(r["light"] == 5 + 2 + 12 + 4, "seed and future, got %d" % r["light"])
	var s := RunState.new()
	s.new_run(7)
	s.choose_patron(0)
	s.start_night()
	var fut: Dictionary = s.hand[0]
	check(s.place(int(fut["id"]), 2), "place in future")
	var before_total := s.card_count_total()
	var res := s.read()
	check(not res.is_empty(), "read ok")
	check(s.hand_index(int(fut["id"])) >= 0 or s.phase != "play", "future card returns to hand")
	check(s.card_count_total() == before_total, "conservation after read")


func test_read_rules() -> void:
	var s := RunState.new()
	s.new_run(11)
	s.choose_patron(0)
	check(s.read().is_empty(), "read rejected outside play")
	s.start_night()
	check(s.read().is_empty(), "read rejected with empty spread")
	check(s.readings_left == 4, "rejected read consumes nothing")
	var id0 := int(s.hand[0]["id"])
	check(s.place(id0, 1), "place present")
	check(not s.place(int(s.hand[0]["id"]), 1), "occupied position rejected")
	check(not s.place(9999, 0), "unknown card rejected")
	var p := s.preview()
	var r := s.read()
	check(r["insight"] == p["insight"], "preview equals scored")
	check(s.readings_left == 3, "one reading consumed")
	check(s.hand.size() == 8, "hand refilled")


func test_reshuffle_rules() -> void:
	var s := RunState.new()
	s.new_run(12)
	s.choose_patron(1)
	s.start_night()
	check(not s.reshuffle([]), "empty reshuffle rejected")
	var a := int(s.hand[0]["id"])
	check(not s.reshuffle([a, a]), "duplicate ids rejected")
	var total := s.card_count_total()
	check(s.reshuffle([a, int(s.hand[1]["id"])]), "reshuffle ok")
	check(s.reshuffles_left == 2 and s.hand.size() == 8, "reshuffle consumed once, hand full")
	check(s.card_count_total() == total, "reshuffle conserves cards")
	check(s.hand_index(a) < 0 or s.draw.size() == 0, "discarded card left hand")


func test_shadow_block() -> void:
	var s := RunState.new()
	s.new_run(5)
	s.choose_patron(0)
	s.night = 1
	s.start_night()
	s.place(int(s.hand[0]["id"]), 1)
	var r := s.read()
	check(r["events"]["new_intent"] != null, "troubled shadow plans after reading 1")
	var it: Dictionary = r["events"]["new_intent"]
	check(int(it["apply_at"]) == 3, "intent applies two readings later")
	check(s.blocked_positions().is_empty(), "not active yet")
	s.place(int(s.hand[0]["id"]), 1)
	s.read()
	if s.phase == "play":
		check(s.blocked_positions() == [int(it["pos"])], "active on reading 3")
		check(not s.place(int(s.hand[0]["id"]), int(it["pos"])), "blocked position rejects")


func test_twin() -> void:
	var ctx := {"twin": true, "twin_used": {1: true}}
	var r := Scoring.evaluate([null, c(0, 1, 10), null], ctx)
	check(r["light"] == 5 + 5, "twin halves used suit")


func test_market() -> void:
	var s := RunState.new()
	s.new_run(3)
	s.choose_patron(0)
	s.phase = "market"
	s.coins = 5
	s._roll_market()
	var major_i := -1
	for i in s.market.size():
		if s.market[i]["kind"] == "major":
			major_i = i
	check(not s.buy(major_i), "unaffordable major rejected")
	check(s.coins == 5, "coins unchanged on rejection")
	s.coins = 100
	check(s.buy(major_i), "major bought")
	check(not s.buy(major_i), "sold item rejected")
	var ids := {}
	for a in s.arcana:
		check(not ids.has(a), "arcana unique")
		ids[a] = true
	while s.arcana.size() < ArcanaDB.MAX_SLOTS:
		s.arcana.append("x%d" % s.arcana.size())
	s._roll_market()
	for i in s.market.size():
		if s.market[i]["kind"] == "major":
			check(not s.buy(i), "full slots reject major")
	var n := s.deck.size()
	for i in s.market.size():
		if s.market[i]["kind"] == "minor":
			s.buy(i)
	check(s.deck.size() == n + 2, "minors join deck")
	var c0 := s.coins
	check(s.sell_arcana(0) and s.coins == c0 + 3, "sell gives 3")
	s.coins = 1
	check(not s.reroll(), "reroll needs 2 coins")


func test_save_roundtrip() -> void:
	var s := RunState.new()
	s.new_run(99)
	s.choose_patron(2)
	s.start_night()
	s.place(int(s.hand[0]["id"]), 0)
	var json := JSON.stringify(s.to_dict())
	var t := RunState.new()
	check(t.from_dict(JSON.parse_string(json)), "load ok")
	check(JSON.stringify(t.to_dict()) == json, "roundtrip identical")
	var r1 := s.read()
	var r2 := t.read()
	check(r1["insight"] == r2["insight"], "same result after load")
	check(JSON.stringify(s.to_dict()) == JSON.stringify(t.to_dict()), "same draws after load")


func test_bad_save() -> void:
	var t := RunState.new()
	t.new_run(1)
	check(not t.from_dict({"v": 1, "phase": "play"}), "missing keys rejected")
	check(not t.from_dict({}), "empty rejected")
	check(t.phase == "patron", "state untouched after bad load")


# ---- Bot: plays complete runs through the public API to check reachability and tuning ----

func best_play(s: RunState) -> Array:
	var best := []
	var best_v := -1
	var n := s.hand.size()
	var blocked := s.blocked_positions()
	var open: Array = []
	for p in 3:
		if not blocked.has(p):
			open.append(p)
	var perms := _assignments(open)
	for i in n:
		for j in range(i, n):
			for k in range(j, n):
				var idx := {}
				idx[i] = true
				idx[j] = true
				idx[k] = true
				var cards: Array = []
				for key in idx.keys():
					cards.append(s.hand[key])
				for perm in perms:
					if perm.size() < cards.size():
						continue
					var sp: Array = [null, null, null]
					for q in cards.size():
						sp[perm[q]] = cards[q]
					var v := int(Scoring.evaluate(sp, s.score_context())["insight"])
					if v > best_v:
						best_v = v
						best = [cards, perm]
	return best


func _assignments(open: Array) -> Array:
	var out: Array = []
	for a in open:
		out.append([a])
		for b in open:
			if b == a:
				continue
			out.append([a, b])
			for cpos in open:
				if cpos != a and cpos != b:
					out.append([a, b, cpos])
	return out


func play_run(seed: int) -> Dictionary:
	var s := RunState.new()
	s.new_run(seed)
	s.choose_patron(0)
	var guard := 0
	while guard < 200:
		guard += 1
		match s.phase:
			"intro":
				s.start_night()
			"play":
				var total_before := s.card_count_total() + 0
				var pick := best_play(s)
				var cards: Array = pick[0]
				var perm: Array = pick[1]
				for q in cards.size():
					s.place(int(cards[q]["id"]), perm[q])
				var res := s.read()
				if res.is_empty():
					return {"won": false, "night": s.night, "error": "read failed"}
				var destroyed: int = res["events"]["destroyed"].size()
				if s.phase == "play" and s.card_count_total() + destroyed != total_before:
					return {"won": false, "night": s.night, "error": "conservation"}
			"won":
				s.continue_after_win()
			"market":
				for i in s.market.size():
					if s.market[i]["kind"] == "major":
						s.buy(i)
				for i in s.market.size():
					if s.market[i]["kind"] == "sigil":
						s.buy(i)
				s.leave_market()
			"victory":
				return {"won": true, "night": 3}
			"defeat":
				return {"won": false, "night": s.night}
	return {"won": false, "night": s.night, "error": "stuck"}


func bot_report() -> void:
	var wins := 0
	var reached := [0, 0, 0, 0]
	var errors := 0
	var runs := 150
	for seed in runs:
		var r := play_run(1000 + seed)
		if r.has("error"):
			errors += 1
			print("bot error seed %d: %s" % [1000 + seed, r["error"]])
		if r["won"]:
			wins += 1
		reached[int(r["night"])] += 1
	check(errors == 0, "bot runs complete without rule errors")
	check(wins > 0, "Cycle 1 is winnable through the public API")
	print("BOT (greedy, no reshuffles): %d/%d runs cleared Cycle 1; lost at night: curious %d, troubled %d, twin %d" % [wins, runs, reached[0], reached[1], reached[2]])
