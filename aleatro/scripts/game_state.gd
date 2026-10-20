class_name GameState
extends RefCounted

var rng := RandomNumberGenerator.new()
var ante := 1
var blind_idx := 0  # 0 small, 1 big, 2 boss
var money := 4
var hand_size := 8
var max_hands := 4
var max_discards := 3
var hands_left := 4
var discards_left := 3
var charm_slots := 5
var charms: Array = []  # [{id, data}]
var spells: Array = []  # spell ids
var challenge := ""
var rules := {}
var banned_charms: Array = []
var banned_hexes: Array = []
var inflation := 0
var played_this_ante: Array = []  # card ids, for the Burnout rule
var spell_slots := 2
var hand_levels := {}
var hands_played_count := {}
var deck: Array = []
var draw_pile: Array = []
var hand: Array = []
var boss_hex: Dictionary = {}
var round_score := 0
var target := 0
var endless := false
var reroll_cost := 5
var best_hand := 0
var shop_charms: Array = []
var shop_runes: Array = []
var shop_spells: Array = []
var _last_hex := ""
var _next_id := 0
var shop_card: Dictionary = {}
## Per-round boss bookkeeping; saved with the run.
var boss_state := {}
## Things that happened this run that charms care about (e.g. "plantain_spoiled").
var run_flags := {}
## Extra spell slots from Negative spells (made by the Hoarder).
var neg_spells := 0
## Deck size at the start of the run, for Wear and Tear.
var start_deck_size := 52
## Shop rerolls that cost nothing (Chaos), reset each shop.
var free_rerolls := 0
## Played cards destroyed by charms this hand, and new cards bound for the
## hand; main takes these after each step.
var pending_destroy: Array = []
var pending_hand: Array = []
## Tags waiting to take effect, the tag on offer for skipping the Small and
## Big Blind this ante, and how many blinds were skipped this run.
var tags: Array = []
var blind_tags: Array = []
var skips := 0
## Booster packs in the shop (kinds), packs to open right away (from tags),
## and whether the Coupon Tag made this shop's first stock free.
var shop_packs: Array = []
var pending_packs: Array = []
var shop_coupon := false


func _init() -> void:
	rng.randomize()
	for n in Data.HAND_ORDER:
		hand_levels[n] = 1
		hands_played_count[n] = 0
	var id := 0
	for s in 4:
		for r in range(2, 15):
			deck.append(make_card(r, s, id))
			id += 1
	_next_id = id
	pick_boss()
	roll_blind_tags()


static func make_card(rank: int, suit: int, id: int) -> Dictionary:
	return {"rank": rank, "suit": suit, "id": id, "enh": "", "ed": "", "seal": ""}


func new_card_id() -> int:
	_next_id += 1
	return _next_id - 1


func random_edition(chance: float) -> String:
	if rng.randf() >= chance:
		return ""
	var r := rng.randf()
	return "chroma" if r > 0.85 else ("holo" if r > 0.5 else "foil")


## A random upgraded playing card for the shop, with its price.
func roll_shop_card() -> void:
	var c := make_card(rng.randi_range(2, 14), rng.randi_range(0, 3), new_card_id())
	var enh := Data.ENHANCEMENTS.keys()
	c.enh = enh[rng.randi_range(0, enh.size() - 1)]
	c.ed = random_edition(0.25)
	if rng.randf() < 0.25:
		c.seal = "crimson" if rng.randf() < 0.5 else "golden"
	var cost := 3
	if c.ed != "":
		cost += Data.EDITIONS[c.ed].cost
	if c.seal != "":
		cost += 2
	shop_card = {"card": c, "cost": cost}


func pick_boss() -> void:
	var showdown := ante % Data.FINAL_ANTE == 0
	var pool := Data.HEXES.filter(func(h): return h.get("showdown", false) == showdown \
			and h.min_ante <= maxi(ante, 1) and h.id != _last_hex and not banned_hexes.has(h.id))
	boss_hex = pool[rng.randi_range(0, pool.size() - 1)]
	_last_hex = boss_hex.id


func blind_name(idx: int = blind_idx) -> String:
	return boss_hex.name if idx == 2 else Data.BLIND_NAMES[idx]


func blind_color(idx: int = blind_idx) -> Color:
	return boss_hex.color if idx == 2 else Data.BLIND_COLORS[idx]


func blind_target(idx: int = blind_idx) -> int:
	var m: float = [1.0, 1.5, boss_hex.mult][idx]
	return int(Data.ante_target(ante) * m)


func blind_reward(idx: int = blind_idx) -> int:
	if rules.get("no_reward", []).has(idx):
		return 0
	return [3, 4, 5][idx]


## A shop price after challenge inflation.
func price(base: int) -> int:
	return base + inflation


## The active boss effect, or "" outside boss blinds or once disabled.
func hex() -> String:
	if blind_idx != 2 or boss_state.get("disabled", false) or has_charm("veto"):
		return ""
	return boss_hex.id


func is_showdown(idx: int = blind_idx) -> bool:
	return idx == 2 and boss_hex.get("showdown", false)


func current_hand_size() -> int:
	var n: int = hand_size - (1 if hex() == "shackle" else 0) + boss_state.get("juggle", 0)
	for c in charms:
		match c.id:
			"juggler":
				n += 1
			"minstrel":
				n += 2
			"merry":
				n -= 1
			"daredevil":
				n -= 2
			"sprout":
				n += c.data.get("h", 5)
	return maxi(n, 1)


func charm_count(id: String) -> int:
	return charms.filter(func(c): return c.id == id).size()


## A listed chance of 1 in `n`, doubled by each Loaded Dice.
func roll(n: int) -> bool:
	return rng.randi_range(1, n) <= (1 << charm_count("loaded"))


func is_face(card: Dictionary) -> bool:
	if card.get("enh", "") == "stone":
		return false
	return has_charm("mirage") or (card.rank >= 11 and card.rank <= 13)


func suit_is(card: Dictionary, s: int) -> bool:
	return Poker.suit_is(card, s, has_charm("blot"))


func poker_opts() -> Dictionary:
	return {"four": has_charm("spread"), "skip": has_charm("hopscotch"), "blot": has_charm("blot"),
		"all": has_charm("puddle")}


## Whether buying something for `cost` is allowed (an IOU allows $20 of debt).
func can_afford(cost: int) -> bool:
	return money - cost >= (-20 if has_charm("iou") else 0)


func spell_capacity() -> int:
	return spell_slots + neg_spells


## The charm whose ability charm `i` uses: itself, or what a copier points at.
## {} when a copier has nothing to copy.
func effective(i: int, depth := 0) -> Dictionary:
	if i < 0 or i >= charms.size() or depth > charms.size():
		return {}
	var inst: Dictionary = charms[i]
	match inst.id:
		"tracing":
			return effective(i + 1, depth + 1)
		"brainwave":
			return {} if i == 0 else effective(0, depth + 1)
	return inst


## Add a random spell (or Omen) if there is room. Returns its id or "".
func give_spell(omen := false) -> String:
	if spells.size() >= spell_capacity():
		return ""
	var pool := Data.SPELLS.filter(func(sp): return sp.get("omen", false) == omen)
	var id: String = pool[rng.randi_range(0, pool.size() - 1)].id
	spells.append(id)
	return id


## Add a random charm of `rarity` if there is room. Returns its name or "".
func give_charm(rarity: int) -> String:
	if charms.size() >= charm_slots:
		return ""
	var owned := charms.map(func(c): return c.id)
	var pool := Data.CHARMS.filter(func(c): return c.rarity == rarity and _offerable(c.id, owned))
	if pool.is_empty():
		return ""
	var d: Dictionary = pool[rng.randi_range(0, pool.size() - 1)]
	charms.append({"id": d.id, "data": {}, "ed": ""})
	return d.name


## A new card joins the deck (and the hand, if `to_hand`).
func add_card(card: Dictionary, to_hand := false) -> void:
	deck.append(card)
	if to_hand:
		pending_hand.append(card)
	for c in charms:
		if c.id == "hologram":
			c.data.x = c.data.get("x", 1.0) + 0.25


## A card leaves the deck for good.
func destroy_card(card: Dictionary, shattered := false) -> void:
	remove_from_deck(card)
	hand.erase(card)
	for c in charms:
		match c.id:
			"bonecrown":
				if is_face(card):
					c.data.x = c.data.get("x", 1.0) + 1.0
			"glazier":
				if shattered:
					c.data.x = c.data.get("x", 1.0) + 0.75


func random_card() -> Dictionary:
	return make_card(rng.randi_range(2, 14), rng.randi_range(0, 3), new_card_id())


## Pick the suit, rank, card or hand a "changes every round" charm wants.
func _reroll_target(c: Dictionary) -> void:
	match c.id:
		"relic", "keep":
			c.data.suit = rng.randi_range(0, 3)
		"rebate":
			c.data.rank = rng.randi_range(2, 14)
		"idol":
			var real := deck.filter(func(k): return k.get("enh", "") != "stone")
			var pick: Dictionary = real[rng.randi_range(0, real.size() - 1)] if not real.is_empty() else random_card()
			c.data.rank = pick.rank
			c.data.suit = pick.suit
		"errand":
			var hands := Data.HAND_ORDER.filter(func(h): return h != c.data.get("hand", ""))
			c.data.hand = hands[rng.randi_range(0, hands.size() - 1)]


## Start a blind. Returns notes [{text, charm}] for what charms did.
func start_round() -> Array:
	var notes := []
	target = blind_target()
	round_score = 0
	hands_left = max_hands
	discards_left = max_discards
	pending_destroy = []
	pending_hand = []
	match hex():
		"needle":
			hands_left = 1
		"drought":
			discards_left = 0
	boss_state = {"used_hands": [], "only_hand": "", "disabled": false, "forced": -1,
		"ember": -1, "sold": false, "hands_played": 0, "down": [], "round_hands": {}, "discarded": 0}
	if tags.has("juggle"):
		tags.erase("juggle")
		boss_state.juggle = 3
		notes.append({"text": "Juggle Tag: +3 hand size"})
	for c in charms:
		if c.id in ["relic", "keep", "rebate", "idol", "errand"] and not c.data.has("suit") \
				and not c.data.has("rank") and not c.data.has("hand"):
			_reroll_target(c)
	var i := 0
	while i < charms.size():
		var c: Dictionary = charms[i]
		var name: String = Data.charm_def(c.id).name
		match c.id:
			"tipsy":
				discards_left += 1
			"merry":
				discards_left += 3
			"minstrel":
				hands_left = maxi(1, hands_left - 1)
			"roadtrip":
				c.data.x = 1.0
			"mason":
				var stone := random_card()
				stone.enh = "stone"
				add_card(stone)
				notes.append({"text": "+1 Stone card", "charm": i})
			"frenzy":
				if blind_idx < 2:
					c.data.x = c.data.get("x", 1.0) + 0.5
					var others := []
					for j in charms.size():
						if j != i and not charms[j].get("locked", false):
							others.append(j)
					var text := "x%s Mult" % str(c.data.x)
					if not others.is_empty():
						var j: int = others[rng.randi_range(0, others.size() - 1)]
						text += ", ate " + _drop_charm(j)
						if j < i:
							i -= 1
					notes.append({"text": text, "charm": i})
			"dagger":
				if i + 1 < charms.size() and not charms[i + 1].get("locked", false):
					c.data.m = c.data.get("m", 0) + 2 * sell_value(charms[i + 1])
					var gone := _drop_charm(i + 1)
					notes.append({"text": "Cut %s: +%d Mult" % [gone, c.data.m], "charm": i})
			"diviner":
				if give_spell() != "":
					notes.append({"text": "+1 Spell", "charm": i})
			"rabble":
				for k in 2:
					var got := give_charm(0)
					if got != "":
						notes.append({"text": "+" + got, "charm": i})
			"burglar":
				hands_left += 3
				notes.append({"text": "+3 Hands", "charm": i})
		i += 1
	if has_charm("burglar"):
		discards_left = 0
	draw_pile = deck.duplicate()
	shuffle(draw_pile)
	hand = []
	for c in charms:
		if c.id == "notary":
			var card := random_card()
			card.seal = Data.SEALS.keys()[rng.randi_range(0, Data.SEALS.size() - 1)]
			deck.append(card)
			draw_pile.append(card)  # drawn first
			notes.append({"text": "+" + Data.card_name(card), "charm": charms.find(c)})
	if hex() == "eclipse":
		shuffle(charms)
	return notes


func shuffle(arr: Array) -> void:
	for i in range(arr.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = arr[i]
		arr[i] = arr[j]
		arr[j] = t


func is_debuffed(card: Dictionary) -> bool:
	if rules.get("played_debuffed", false) and played_this_ante.has(card.id):
		return true
	match hex():
		"":
			return false
		"mute":
			return is_face(card)
		"jade":
			return not boss_state.get("sold", false)
	if boss_hex.has("suit"):
		return suit_is(card, boss_hex.suit)
	return false


## Whether a newly drawn card should arrive face down.
func draws_face_down(card: Dictionary) -> bool:
	if rules.has("flipped") and rng.randi_range(1, rules.flipped) == 1:
		return true
	match hex():
		"mask":
			return is_face(card)
		"shroud":
			return boss_state.get("hands_played", 0) == 0
	return false


func charm_disabled(i: int) -> bool:
	return hex() == "ember" and boss_state.get("ember", -1) == i


## Why the boss refuses this hand, or "" if it may be played.
func hand_blocked(ev: Dictionary, played: Array) -> String:
	match hex():
		"echo":
			if boss_state.used_hands.has(ev.name):
				return "%s was already played" % ev.name
		"monotone":
			if boss_state.only_hand != "" and boss_state.only_hand != ev.name:
				return "Only %s is allowed" % boss_state.only_hand
		"tithe":
			if played.size() < 5:
				return "Hands must use 5 cards"
	return ""


## Boss bookkeeping when a hand is played; returns lines to announce.
func on_hand_played(ev: Dictionary, played: Array) -> Array:
	var notes := []
	boss_state.hands_played = boss_state.get("hands_played", 0) + 1
	match hex():
		"echo":
			boss_state.used_hands.append(ev.name)
		"monotone":
			if boss_state.only_hand == "":
				boss_state.only_hand = ev.name
		"erosion":
			if hand_levels[ev.name] > 1:
				hand_levels[ev.name] -= 1
				notes.append("%s eroded to lvl %d" % [ev.name, hand_levels[ev.name]])
		"toll":
			var cost := mini(played.size(), money)
			money -= cost
			if cost > 0:
				notes.append("Toll: -$%d" % cost)
		"ember":
			if not charms.is_empty():
				boss_state.ember = rng.randi_range(0, charms.size() - 1)
				notes.append("%s is smothered" % Data.charm_def(charms[boss_state.ember].id).name)
	return notes


func draw_cards() -> Array:
	var drawn := []
	while hand.size() < current_hand_size() and not draw_pile.is_empty():
		var c = draw_pile.pop_back()
		hand.append(c)
		drawn.append(c)
	return drawn


func interest() -> int:
	if rules.get("no_interest", false):
		return 0
	return clampi(money / 5, 0, 5)


func advance_blind() -> void:
	blind_idx += 1
	if blind_idx > 2:
		blind_idx = 0
		ante += 1
		played_this_ante = []
		pick_boss()
		roll_blind_tags()


func has_charm(id: String) -> bool:
	return charms.any(func(c): return c.id == id)


func roll_shop() -> void:
	shop_charms = []
	var owned := [] if has_charm("ringmaster") else charms.map(func(c): return c.id)
	for i in 2:
		var roll := rng.randf()
		var rarity := 2 if roll > 0.95 else (1 if roll > 0.7 else 0)
		if rules.get("no_shop_charms", false):
			break
		var pool := Data.CHARMS.filter(func(c): return c.rarity == rarity and _offerable(c.id, owned))
		if pool.is_empty():
			pool = Data.CHARMS.filter(func(c): return c.rarity < 3 and _offerable(c.id, owned))
		if pool.is_empty():
			break
		var pick: Dictionary = pool[rng.randi_range(0, pool.size() - 1)].duplicate()
		pick.ed = random_edition(0.12)
		if pick.ed != "":
			pick.cost += Data.EDITIONS[pick.ed].cost
		shop_charms.append(pick)
		owned.append(pick.id)
	shop_runes = []
	var hands := Data.HAND_ORDER.duplicate()
	shuffle(hands)
	# The magic slot holds either a rune or a spell.
	shop_runes = []
	shop_spells = []
	shop_packs = []
	shop_coupon = false
	for k in 2:
		var kinds := Data.PACKS.keys()
		shop_packs.append(kinds[rng.randi_range(0, kinds.size() - 1)])
	if rng.randf() < 0.5:
		shop_runes = [hands[0]]
	else:
		var pool := Data.SPELLS.filter(func(sp): return not sp.get("omen", false) \
			and (has_charm("ringmaster") or not spells.has(sp.id)))
		shop_spells = [pool[rng.randi_range(0, pool.size() - 1)].id]
	roll_shop_card()


func _offerable(id: String, owned: Array) -> bool:
	if owned.has(id) or banned_charms.has(id):
		return false
	return not Data.CHARM_UNLOCKS.has(id) or run_flags.get(Data.CHARM_UNLOCKS[id], false)


# ---------------------------------------------------------------- charm upkeep

## Charms that grow, count or act as a hand is played, just before it
## scores. Returns notes [{text, charm}]; money they mention is already paid.
func pre_score(ev: Dictionary, played: Array) -> Array:
	var notes := []
	var rh: Dictionary = boss_state.get("round_hands", {})
	rh[ev.name] = rh.get(ev.name, 0) + 1
	boss_state.round_hands = rh
	var first: bool = boss_state.get("hands_played", 0) <= 1
	var live: Array = ev.scoring.filter(func(c): return not is_debuffed(c))
	var face: bool = live.any(func(c): return is_face(c))
	var most := true
	for h in hands_played_count:
		if h != ev.name and hands_played_count[h] > hands_played_count[ev.name]:
			most = false
	for i in charms.size():
		var c: Dictionary = charms[i]
		match c.id:
			"snowball":
				c.data.m = c.data.get("m", 0) + 1
			"commuter":
				c.data.m = 0 if face else c.data.get("m", 0) + 1
			"sprinter":
				if ev.contains.has("Straight"):
					c.data.c = c.data.get("c", 0) + 15
			"foursquare":
				if played.size() == 4:
					c.data.c = c.data.get("c", 0) + 4
			"loyal":
				c.data.n = c.data.get("n", 0) + 1
			"trousers":
				if ev.contains.has("Two Pair"):
					c.data.m = c.data.get("m", 0) + 2
			"monolith":
				c.data.x = 1.0 if most else c.data.get("x", 1.0) + 0.2
			"midas":
				for k in live:
					if is_face(k) and k.get("enh", "") != "gilded":
						k.enh = "gilded"
			"leech":
				for k in live:
					if k.get("enh", "") != "":
						k.enh = ""
						c.data.x = c.data.get("x", 1.0) + 0.1
			"orbit":
				if roll(4):
					hand_levels[ev.name] += 1
					notes.append({"text": "%s lvl %d" % [ev.name, hand_levels[ev.name]], "charm": i})
			"wanderer":
				if money <= 4 and give_spell() != "":
					notes.append({"text": "+1 Spell", "charm": i})
			"ouija":
				if ev.name == "Straight Flush" and give_spell(true) != "":
					notes.append({"text": "+1 Omen", "charm": i})
			"quantum":
				if ev.contains.has("Straight") and played.any(func(k): return k.rank == 14 and k.get("enh", "") != "stone") \
						and give_spell() != "":
					notes.append({"text": "+1 Spell", "charm": i})
			"secondsight":
				if first and played.size() == 1 and played[0].rank == 6 and played[0].get("enh", "") != "stone":
					pending_destroy.append(played[0])
					give_spell(true)
					notes.append({"text": "+1 Omen", "charm": i})
			"clone":
				if first and played.size() == 1:
					var copy: Dictionary = played[0].duplicate()
					copy.id = new_card_id()
					add_card(copy, true)
					notes.append({"text": "Copied!", "charm": i})
			"errand":
				if ev.name == c.data.get("hand", ""):
					money += 4
					notes.append({"text": "$4", "charm": i, "money": 4})
	return notes


## Whether the boss blind's effect touched this hand (for the Toreador).
func boss_hit(played: Array, blocked: String) -> bool:
	if hex() == "":
		return false
	return blocked != "" or played.any(func(k): return is_debuffed(k)) \
		or hex() in ["toll", "erosion", "ember", "halving", "grip"]


# ---------------------------------------------------------------- skips, tags, packs

func roll_blind_tags() -> void:
	blind_tags = []
	for i in 2:
		blind_tags.append(Data.TAGS[rng.randi_range(0, Data.TAGS.size() - 1)].id)


## Skip the current Small or Big Blind for its tag. Returns notes (strings).
func skip_blind() -> Array:
	var tag: String = blind_tags[blind_idx]
	skips += 1
	blind_idx += 1
	return add_tag(tag)


## Gain a tag: some act at once, the rest wait in `tags`. Returns notes.
func add_tag(id: String) -> Array:
	var times := 1
	while id != "twin" and tags.has("twin"):
		tags.erase("twin")
		times += 1
	var notes := []
	for k in times:
		var name: String = Data.tag_def(id).name
		match id:
			"riches":
				var gain := clampi(money, 0, 40)
				money += gain
				notes.append("%s: +$%d" % [name, gain])
			"haste":
				money += 5 * skips
				notes.append("%s: +$%d" % [name, 5 * skips])
			"star":
				var h: String = Data.HAND_ORDER[rng.randi_range(0, Data.HAND_ORDER.size() - 1)]
				hand_levels[h] += 3
				notes.append("%s: %s lvl %d" % [name, h, hand_levels[h]])
			"bundle":
				pending_packs.append("charm")
				notes.append(name)
			"tome":
				pending_packs.append("spell")
				notes.append(name)
			_:
				tags.append(id)
				notes.append(name)
	return notes


## Apply waiting shop tags when a shop opens. Returns notes.
func apply_shop_tags() -> Array:
	var notes := []
	shop_coupon = false
	for t in ["rare", "uncommon"]:
		while tags.has(t):
			tags.erase(t)
			var rarity := 2 if t == "rare" else 1
			var owned := charms.map(func(c): return c.id) + shop_charms.map(func(c): return c.id)
			var pool := Data.CHARMS.filter(func(c): return c.rarity == rarity and _offerable(c.id, owned))
			if not pool.is_empty():
				var pick: Dictionary = pool[rng.randi_range(0, pool.size() - 1)].duplicate()
				pick.ed = ""
				pick.cost = 0
				shop_charms.push_front(pick)
				notes.append("%s: free %s" % [Data.tag_def(t).name, pick.name])
	if tags.has("coupon"):
		tags.erase("coupon")
		shop_coupon = true
		for c in shop_charms:
			c.cost = 0
		if not shop_card.is_empty():
			shop_card.cost = 0
		notes.append(Data.tag_def("coupon").name + ": everything is free")
	if tags.has("dice"):
		tags.erase("dice")
		reroll_cost = 0
		notes.append(Data.tag_def("dice").name + ": rerolls start at $0")
	return notes


func pack_price(kind: String) -> int:
	return 0 if shop_coupon else price(Data.PACKS[kind].cost)


## The choices inside a freshly opened pack of `kind`.
func open_pack(kind: String) -> Array:
	var out := []
	var n: int = Data.PACKS[kind].show
	match kind:
		"charm":
			var owned := [] if has_charm("ringmaster") else charms.map(func(c): return c.id)
			for i in n:
				var roll := rng.randf()
				var rarity := 2 if roll > 0.95 else (1 if roll > 0.7 else 0)
				var pool := Data.CHARMS.filter(func(c): return c.rarity == rarity and _offerable(c.id, owned))
				if pool.is_empty():
					continue
				var pick: Dictionary = pool[rng.randi_range(0, pool.size() - 1)]
				out.append({"id": pick.id, "data": {}, "ed": random_edition(0.12)})
				owned.append(pick.id)
		"spell":
			var pool := Data.SPELLS.filter(func(sp): return not sp.get("omen", false))
			shuffle(pool)
			for i in n:
				out.append(pool[i].id)
		"rune":
			var hands := Data.HAND_ORDER.duplicate()
			shuffle(hands)
			out = hands.slice(0, n)
		"card":
			for i in n:
				var c := random_card()
				if rng.randf() < 0.4:
					var enh := Data.ENHANCEMENTS.keys()
					c.enh = enh[rng.randi_range(0, enh.size() - 1)]
				c.ed = random_edition(0.1)
				if rng.randf() < 0.15:
					c.seal = Data.SEALS.keys()[rng.randi_range(0, Data.SEALS.size() - 1)]
				out.append(c)
	return out


## Charms that react to opening a pack. Returns notes.
func on_pack_opened() -> Array:
	var notes := []
	for c in charms:
		if c.id == "daydream" and roll(2) and give_spell() != "":
			notes.append("Daydream: +1 Spell")
	return notes


## Take `choice` from an opened pack of `kind`. Returns "" or why it can't be taken.
func take_from_pack(kind: String, choice) -> String:
	match kind:
		"charm":
			if charms.size() >= charm_slots:
				return "No room for more charms"
			charms.append(choice)
		"spell":
			if spells.size() >= spell_capacity():
				return "No room for more spells"
			spells.append(choice)
		"rune":
			hand_levels[choice] += 1
			on_rune(choice)
		"card":
			add_card(choice)
	return ""


func skip_pack() -> void:
	for c in charms:
		if c.id == "scrapbook":
			c.data.m = c.data.get("m", 0) + 3


## Charms that react to a discard. Money is paid here; returns notes.
func on_discard(cards: Array) -> Array:
	var notes := []
	var first: bool = boss_state.get("discarded", 0) == 0
	boss_state.discarded = boss_state.get("discarded", 0) + 1
	var faces := cards.filter(func(k): return is_face(k)).size()
	var i := 0
	while i < charms.size():
		var c: Dictionary = charms[i]
		match c.id:
			"snowball":
				c.data.m = maxi(0, c.data.get("m", 0) - 1)
			"keep":
				var n := cards.filter(func(k): return suit_is(k, c.data.get("suit", 0))).size()
				if n > 0:
					c.data.c = c.data.get("c", 0) + 3 * n
					notes.append({"text": "+%d Chips" % (3 * n), "charm": i})
			"rebate":
				var n := cards.filter(func(k): return k.rank == c.data.get("rank", 0) and k.get("enh", "") != "stone").size()
				if n > 0:
					money += 5 * n
					notes.append({"text": "$%d" % (5 * n), "charm": i, "money": 5 * n})
			"trader":
				if first and cards.size() == 1:
					pending_destroy.append(cards[0])
					money += 3
					notes.append({"text": "$3", "charm": i, "money": 3})
			"kindling":
				if first:
					var h: String = Poker.evaluate(cards, poker_opts()).name
					hand_levels[h] += 1
					notes.append({"text": "%s lvl %d" % [h, hand_levels[h]], "charm": i})
			"blankmask":
				if faces >= 3:
					money += 5
					notes.append({"text": "$5", "charm": i, "money": 5})
			"roadtrip":
				var jacks := cards.filter(func(k): return k.rank == 11 and k.get("enh", "") != "stone").size()
				if jacks > 0:
					c.data.x = c.data.get("x", 1.0) + 0.5 * jacks
					notes.append({"text": "x%s Mult" % str(c.data.x), "charm": i})
			"skull":
				c.data.n = c.data.get("n", 0) + cards.size()
				while c.data.n >= 23:
					c.data.n -= 23
					c.data.x = c.data.get("x", 1.0) + 1.0
					notes.append({"text": "x%s Mult" % str(c.data.x), "charm": i})
			"noodles":
				c.data.x = snappedf(c.data.get("x", 2.0) - 0.01 * cards.size(), 0.01)
				if c.data.x <= 1.0:
					notes.append({"text": _drop_charm(i) + " is gone!"})
					continue
		i += 1
	return notes


func on_rune(h: String) -> void:
	var used: Array = run_flags.get("runes_used", [])
	if not used.has(h):
		used.append(h)
	run_flags["runes_used"] = used
	for c in charms:
		if c.id == "starmap":
			c.data.x = c.data.get("x", 1.0) + 0.1


func on_reroll() -> void:
	for c in charms:
		if c.id == "flashcard":
			c.data.m = c.data.get("m", 0) + 2


## After `inst` has been sold (and removed). Returns notes.
func on_sell(inst: Dictionary) -> Array:
	var notes := []
	for c in charms:
		if c.id == "bonfire":
			c.data.x = c.data.get("x", 1.0) + 0.25
	if inst.id == "float":
		notes.append_array(add_tag("twin"))
	if inst.id == "phantom" and inst.data.get("r", 0) >= 2:
		var others := charms.filter(func(c): return c.id != "phantom")
		if not others.is_empty() and charms.size() < charm_slots:
			var pick: Dictionary = others[rng.randi_range(0, others.size() - 1)].duplicate(true)
			pick.erase("locked")
			charms.append(pick)
			notes.append("Duplicated " + Data.charm_def(pick.id).name)
	return notes


## On leaving the shop. Returns notes.
func on_leave_shop() -> Array:
	var notes := []
	for c in charms:
		if c.id == "hoarder" and not spells.is_empty():
			spells.append(spells[rng.randi_range(0, spells.size() - 1)])
			neg_spells += 1
			notes.append("Negative copy of " + Data.spell_def(spells[-1]).name)
	return notes


## Charms that wear down after a hand has scored. Returns the names of any
## that ran out and were removed.
func after_hand() -> Array:
	var gone := []
	for i in range(charms.size() - 1, -1, -1):
		var c: Dictionary = charms[i]
		match c.id:
			"sorbet":
				c.data.c = c.data.get("c", 100) - 5
				if c.data.c <= 0:
					gone.append(_drop_charm(i))
			"fizz":
				c.data.n = c.data.get("n", 10) - 1
				if c.data.n <= 0:
					gone.append(_drop_charm(i))
	return gone


## End-of-round charm payouts and decay. Returns {rows: [[label, $]], gone: [names]}.
func end_of_round() -> Dictionary:
	var rows := []
	var gone := []
	for i in range(charms.size() - 1, -1, -1):
		var c: Dictionary = charms[i]
		var name: String = Data.charm_def(c.id).name
		match c.id:
			"gold":
				rows.push_front([name, 4])
			"patience":
				if boss_state.get("discarded", 0) == 0 and discards_left > 0:
					rows.push_front([name, 2 * discards_left])
			"kettle":
				c.data.m = c.data.get("m", 20) - 4
				if c.data.m <= 0:
					gone.append(_drop_charm(i))
			"plantain":
				if roll(6):
					run_flags["plantain_spoiled"] = true
					gone.append(_drop_charm(i))
			"ripe":
				if roll(1000):
					gone.append(_drop_charm(i))
			"skyrocket":
				rows.push_front([name, c.data.get("p", 1)])
				if blind_idx == 2:
					c.data.p = c.data.get("p", 1) + 2
			"ninelives":
				var nines := deck.filter(func(k): return k.rank == 9 and k.get("enh", "") != "stone").size()
				if nines > 0:
					rows.push_front([name, nines])
			"satellite":
				var n: int = run_flags.get("runes_used", []).size()
				if n > 0:
					rows.push_front([name, n])
			"nestegg":
				c.data.v = c.data.get("v", 0) + 3
			"giftwrap":
				for k in charms:
					k.data.v = k.data.get("v", 0) + 1
			"sprout":
				c.data.h = c.data.get("h", 5) - 1
				if c.data.h <= 0:
					gone.append(_drop_charm(i))
			"phantom":
				c.data.r = c.data.get("r", 0) + 1
			"bonfire":
				if blind_idx == 2:
					c.data.x = 1.0
			"relic", "keep", "rebate", "idol", "errand":
				_reroll_target(c)
	if blind_idx == 2 and tags.has("invest"):
		var n := tags.count("invest")
		while tags.has("invest"):
			tags.erase("invest")
		rows.append([Data.tag_def("invest").name, 15 * n])
	return {"rows": rows, "gone": gone}


## Remove charm `i`, keeping the smothered-charm index pointing at the same charm.
func _drop_charm(i: int) -> String:
	var name: String = Data.charm_def(charms[i].id).name
	charms.remove_at(i)
	var ember: int = boss_state.get("ember", -1)
	if ember == i:
		boss_state.ember = -1
	elif ember > i:
		boss_state.ember = ember - 1
	return name


func sell_value(inst: Dictionary) -> int:
	var cost: int = Data.charm_def(inst.id).cost
	if inst.get("ed", "") != "":
		cost += Data.EDITIONS[inst.ed].cost
	return maxi(1, cost / 2) + inst.get("data", {}).get("v", 0)


## Why a spell can't be cast on these cards right now, or "".
func spell_blocked(id: String, selected: Array, in_round: bool) -> String:
	var d := Data.spell_def(id)
	if d.max == 0:
		return ""
	if not in_round:
		return "Cast it during a round, on cards in your hand"
	if selected.is_empty():
		return "Select up to %d card%s first" % [d.max, "" if d.max == 1 else "s"]
	if selected.size() > d.max:
		return "Select at most %d card%s" % [d.max, "" if d.max == 1 else "s"]
	if selected.size() < d.get("min", 1):
		return "Select exactly %d cards" % d.min
	return ""


## Apply a spell to the selected cards (in hand order). Returns cards removed.
func cast_spell(id: String, selected: Array) -> Array:
	var d := Data.spell_def(id)
	var removed := []
	if d.has("enh"):
		for c in selected:
			c.enh = d.enh
	elif d.has("suit"):
		for c in selected:
			c.suit = d.suit
	else:
		match id:
			"ascend":
				for c in selected:
					c.rank = 2 if c.rank == 14 else c.rank + 1
			"purge":
				for c in selected:
					destroy_card(c)
					removed.append(c)
			"mirror":
				var left: Dictionary = selected[0]
				var right: Dictionary = selected[1]
				for k in ["rank", "suit", "enh", "ed", "seal"]:
					left[k] = right[k]
			"sigil":
				for c in selected:
					c.seal = "crimson"
			"windfall":
				money += mini(money, 20)
			"aura":
				for c in selected:
					c.ed = random_edition(1.0)
			"talisman":
				for c in selected:
					c.seal = "golden"
			"duplicate":
				for k in 2:
					var copy: Dictionary = selected[0].duplicate()
					copy.id = new_card_id()
					add_card(copy)
			"wraith":
				give_charm(2)
				money = mini(money, 0)
			"soul":
				give_charm(3)
	spells.erase(id)
	# casting a spell beyond the normal slots uses up a Negative slot
	neg_spells = clampi(neg_spells, 0, maxi(0, spells.size() - spell_slots))
	return removed


func remove_from_deck(card: Dictionary) -> void:
	for i in deck.size():
		if deck[i].id == card.id:
			deck.remove_at(i)
			return


# ---------------------------------------------------------------- save / load

const SAVE_FIELDS := [
	"ante", "blind_idx", "money", "hand_size", "max_hands", "max_discards", "hands_left",
	"discards_left", "charm_slots", "charms", "hand_levels", "hands_played_count", "deck",
	"round_score", "target", "endless", "reroll_cost", "best_hand", "shop_charms",
	"shop_runes", "shop_card", "_last_hex", "_next_id", "boss_state", "spells", "shop_spells",
	"challenge", "rules", "banned_charms", "banned_hexes", "inflation", "played_this_ante",
	"run_flags", "neg_spells", "start_deck_size", "tags", "blind_tags", "skips", "shop_packs",
	"pending_packs", "shop_coupon",
]


func to_dict() -> Dictionary:
	var d := {}
	for f in SAVE_FIELDS:
		d[f] = get(f)
	# Hand and draw pile hold the same card objects as the deck; store ids.
	d.hand = hand.map(func(c): return c.id)
	d.draw_pile = draw_pile.map(func(c): return c.id)
	d.boss = boss_hex.id
	d.rng_seed = rng.seed
	d.rng_state = rng.state
	return d


static func from_dict(d: Dictionary) -> GameState:
	var gs := GameState.new()
	for f in SAVE_FIELDS:
		if d.has(f):
			gs.set(f, d[f])
	var by_id := {}
	for c in gs.deck:
		by_id[c.id] = c
	gs.hand = d.get("hand", []).filter(func(i): return by_id.has(i)).map(func(i): return by_id[i])
	gs.draw_pile = d.get("draw_pile", []).filter(func(i): return by_id.has(i)).map(func(i): return by_id[i])
	for h in Data.HEXES:
		if h.id == d.get("boss", ""):
			gs.boss_hex = h
	gs.rng.seed = d.get("rng_seed", gs.rng.seed)
	gs.rng.state = d.get("rng_state", gs.rng.state)
	return gs


## Set this run up as a challenge: deck, slots, money, starting items, rules.
func apply_challenge(id: String) -> void:
	var ch := Data.challenge_def(id)
	if ch.is_empty():
		return
	challenge = id
	rules = ch.get("rules", {}).duplicate(true)
	banned_charms = ch.get("banned_charms", []).duplicate()
	banned_hexes = ch.get("banned_hexes", []).duplicate()
	var mods: Dictionary = ch.get("mods", {})
	money = mods.get("money", money)
	max_hands = mods.get("hands", max_hands)
	max_discards = mods.get("discards", max_discards)
	hand_size = mods.get("hand_size", hand_size)
	charm_slots = mods.get("charm_slots", charm_slots)
	spell_slots = mods.get("spell_slots", spell_slots)
	var spec: Dictionary = ch.get("deck", {})
	if not spec.is_empty():
		deck = []
		_next_id = 0
		for copy in spec.get("copies", 1):
			for s in spec.get("suits", [0, 1, 2, 3]):
				for r in spec.get("ranks", range(2, 15)):
					var c := make_card(r, s, new_card_id())
					c.enh = spec.get("enh", "")
					c.ed = spec.get("ed", "")
					c.seal = spec.get("seal", "")
					deck.append(c)
	start_deck_size = deck.size()
	charms = []
	for c in ch.get("charms", []):
		charms.append({"id": c.id, "data": {}, "ed": c.get("ed", ""), "locked": c.get("locked", false)})
	spells = ch.get("spells", []).duplicate()
	if banned_hexes.has(boss_hex.id):
		pick_boss()
