class_name Scoring
extends RefCounted

## Builds the ordered list of scoring events for a played hand.
## Event kinds: "base" {chips, mult}, "card" {card, chips} / {card, debuff},
## "charm" {charm_index, card?, chips?, mult?, xmult?}.
static func compute(gs: GameState, played: Array, ev: Dictionary) -> Array:
	var events := []
	var hand_name: String = ev.name
	var lvl: int = gs.hand_levels[hand_name]
	var chips := Data.hand_chips(hand_name, lvl)
	var mult := Data.hand_mult(hand_name, lvl)
	if gs.hex() == "halving":
		chips = ceili(chips / 2.0)
		mult = maxi(1, ceili(mult / 2.0))
	events.append({"kind": "base", "chips": chips, "mult": mult})

	for card in ev.scoring:
		if gs.is_debuffed(card):
			events.append({"kind": "card", "card": card, "debuff": true})
			continue
		events.append({"kind": "card", "card": card, "chips": Data.card_chips(card.rank)})
		for i in gs.charms.size():
			var fx := _on_card(gs.charms[i], card)
			if not fx.is_empty():
				fx.kind = "charm"
				fx.charm_index = i
				fx.card = card
				events.append(fx)

	var ctx := {"gs": gs, "played": played, "contains": ev.contains}
	for i in gs.charms.size():
		var fx := _on_hand(gs.charms[i], ctx)
		if not fx.is_empty():
			fx.kind = "charm"
			fx.charm_index = i
			events.append(fx)
	return events


static func _on_card(inst: Dictionary, card: Dictionary) -> Dictionary:
	var r: int = card.rank
	match inst.id:
		"ruby":
			if card.suit == 1: return {"mult": 3}
		"topaz":
			if card.suit == 3: return {"mult": 3}
		"onyx":
			if card.suit == 0: return {"mult": 3}
		"jade":
			if card.suit == 2: return {"mult": 3}
		"spiral":
			if r in [14, 2, 3, 5, 8]: return {"mult": 8}
		"even":
			if r <= 10 and r % 2 == 0: return {"mult": 4}
		"odd":
			if r == 14 or (r <= 10 and r % 2 == 1): return {"chips": 31}
		"scribe":
			if r == 14: return {"chips": 20, "mult": 4}
		"court":
			if r >= 11 and r <= 13: return {"chips": 30}
		"crown":
			if r == 13: return {"xmult": 1.5}
	return {}


static func _on_hand(inst: Dictionary, ctx: Dictionary) -> Dictionary:
	var gs: GameState = ctx.gs
	var contains: Array = ctx.contains
	var played: Array = ctx.played
	match inst.id:
		"jester":
			return {"mult": 4}
		"twin":
			if contains.has("Pair"): return {"mult": 8}
		"triad":
			if contains.has("Three of a Kind"): return {"mult": 12}
		"duo":
			if contains.has("Two Pair"): return {"mult": 10}
		"ladder":
			if contains.has("Straight"): return {"mult": 12}
		"tide":
			if contains.has("Flush"): return {"mult": 10}
		"mint":
			if played.size() <= 3: return {"mult": 20}
		"flag":
			if gs.discards_left > 0: return {"chips": 30 * gs.discards_left}
		"glitch":
			return {"mult": gs.rng.randi_range(0, 23)}
		"well":
			if gs.draw_pile.size() > 0: return {"chips": 2 * gs.draw_pile.size()}
		"crowd":
			return {"mult": 3 * gs.charms.size()}
		"laststand":
			if gs.discards_left == 0: return {"mult": 15}
		"snowball":
			var m: int = inst.data.get("m", 0)
			if m > 0: return {"mult": m}
		"treasury":
			if gs.money > 0: return {"chips": 2 * gs.money}
		"hollow":
			var x := gs.charm_slots - gs.charms.size() + 1
			if x > 1: return {"xmult": float(x)}
		"prism":
			var suits := {}
			for c in played:
				suits[c.suit] = true
			if suits.size() == 4: return {"xmult": 3.0}
		"duet":
			if contains.has("Pair"): return {"xmult": 2.0}
	return {}


static func describe(inst: Dictionary) -> String:
	var d: Dictionary = Data.charm_def(inst.id)
	if inst.id == "snowball":
		return "%s\n(Currently +%d Mult)" % [d.desc, inst.data.get("m", 0)]
	return d.desc
