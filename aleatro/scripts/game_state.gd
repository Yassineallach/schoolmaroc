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
	if blind_idx != 2 or boss_state.get("disabled", false):
		return ""
	return boss_hex.id


func is_showdown(idx: int = blind_idx) -> bool:
	return idx == 2 and boss_hex.get("showdown", false)


func current_hand_size() -> int:
	return hand_size - (1 if hex() == "shackle" else 0)


func start_round() -> void:
	target = blind_target()
	round_score = 0
	hands_left = max_hands
	discards_left = max_discards
	match hex():
		"needle":
			hands_left = 1
		"drought":
			discards_left = 0
	draw_pile = deck.duplicate()
	shuffle(draw_pile)
	hand = []
	boss_state = {"used_hands": [], "only_hand": "", "disabled": false, "forced": -1,
		"ember": -1, "sold": false, "hands_played": 0, "down": []}
	if hex() == "eclipse":
		shuffle(charms)


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
			return card.rank >= 11 and card.rank <= 13
		"jade":
			return not boss_state.get("sold", false)
	if boss_hex.has("suit"):
		return card.suit == boss_hex.suit
	return false


## Whether a newly drawn card should arrive face down.
func draws_face_down(card: Dictionary) -> bool:
	if rules.has("flipped") and rng.randi_range(1, rules.flipped) == 1:
		return true
	match hex():
		"mask":
			return card.rank >= 11 and card.rank <= 13
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


func has_charm(id: String) -> bool:
	return charms.any(func(c): return c.id == id)


func roll_shop() -> void:
	shop_charms = []
	var owned := charms.map(func(c): return c.id)
	for i in 2:
		var roll := rng.randf()
		var rarity := 2 if roll > 0.95 else (1 if roll > 0.7 else 0)
		if rules.get("no_shop_charms", false):
			break
		var pool := Data.CHARMS.filter(func(c): return c.rarity == rarity and not owned.has(c.id) and not banned_charms.has(c.id))
		if pool.is_empty():
			pool = Data.CHARMS.filter(func(c): return not owned.has(c.id) and not banned_charms.has(c.id))
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
	if rng.randf() < 0.5:
		shop_runes = [hands[0]]
	else:
		shop_spells = [Data.SPELLS[rng.randi_range(0, Data.SPELLS.size() - 1)].id]
	roll_shop_card()


func sell_value(inst: Dictionary) -> int:
	var cost: int = Data.charm_def(inst.id).cost
	if inst.get("ed", "") != "":
		cost += Data.EDITIONS[inst.ed].cost
	return maxi(1, cost / 2)


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
					remove_from_deck(c)
					hand.erase(c)
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
	spells.erase(id)
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
	charms = []
	for c in ch.get("charms", []):
		charms.append({"id": c.id, "data": {}, "ed": c.get("ed", ""), "locked": c.get("locked", false)})
	spells = ch.get("spells", []).duplicate()
	if banned_hexes.has(boss_hex.id):
		pick_boss()
