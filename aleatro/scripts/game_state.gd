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
var _last_hex := ""


func _init() -> void:
	rng.randomize()
	for n in Data.HAND_ORDER:
		hand_levels[n] = 1
		hands_played_count[n] = 0
	var id := 0
	for s in 4:
		for r in range(2, 15):
			deck.append({"rank": r, "suit": s, "id": id})
			id += 1
	pick_boss()


func pick_boss() -> void:
	var pool := Data.HEXES.filter(func(h): return h.min_ante <= ante and h.id != _last_hex)
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
	return [3, 4, 5][idx]


func hex() -> String:
	return boss_hex.id if blind_idx == 2 else ""


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


func shuffle(arr: Array) -> void:
	for i in range(arr.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = arr[i]
		arr[i] = arr[j]
		arr[j] = t


func is_debuffed(card: Dictionary) -> bool:
	if blind_idx != 2:
		return false
	if boss_hex.has("suit"):
		return card.suit == boss_hex.suit
	if boss_hex.id == "mute":
		return card.rank >= 11 and card.rank <= 13
	return false


func draw_cards() -> Array:
	var drawn := []
	while hand.size() < hand_size and not draw_pile.is_empty():
		var c = draw_pile.pop_back()
		hand.append(c)
		drawn.append(c)
	return drawn


func interest() -> int:
	return clampi(money / 5, 0, 5)


func advance_blind() -> void:
	blind_idx += 1
	if blind_idx > 2:
		blind_idx = 0
		ante += 1
		pick_boss()


func has_charm(id: String) -> bool:
	return charms.any(func(c): return c.id == id)


func roll_shop() -> void:
	shop_charms = []
	var owned := charms.map(func(c): return c.id)
	for i in 2:
		var roll := rng.randf()
		var rarity := 2 if roll > 0.95 else (1 if roll > 0.7 else 0)
		var pool := Data.CHARMS.filter(func(c): return c.rarity == rarity and not owned.has(c.id))
		if pool.is_empty():
			pool = Data.CHARMS.filter(func(c): return not owned.has(c.id))
		if pool.is_empty():
			break
		var pick: Dictionary = pool[rng.randi_range(0, pool.size() - 1)]
		shop_charms.append(pick)
		owned.append(pick.id)
	shop_runes = []
	var hands := Data.HAND_ORDER.duplicate()
	shuffle(hands)
	shop_runes = [hands[0], hands[1]]


func sell_value(charm_id: String) -> int:
	return maxi(1, Data.charm_def(charm_id).cost / 2)
