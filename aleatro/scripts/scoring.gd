class_name Scoring
extends RefCounted

## Builds the ordered scoring events for a played hand.
## Returns {events: Array, shatter: Array of glass cards that broke}.
## Every event but "base" may carry chips, mult, xmult and money, plus an
## anchor: "card" (played or held card) and/or "charm_index".
## Flags: "debuff" (card did nothing), "again" (retrigger).
static func compute(gs: GameState, played: Array, ev: Dictionary, held: Array) -> Dictionary:
	var events := []
	var shatter := []
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
		var reps := 2 if card.get("seal", "") == "crimson" else 1
		for rep in reps:
			if rep > 0:
				events.append({"kind": "card", "card": card, "again": true})
			events.append({"kind": "card", "card": card, "chips": Data.card_chips(card.rank)})
			var enh := _enhancement(gs, card)
			if not enh.is_empty():
				enh.kind = "card"
				enh.card = card
				events.append(enh)
			if card.get("seal", "") == "golden":
				events.append({"kind": "card", "card": card, "money": 3})
			var ed := edition_fx(card.get("ed", ""))
			if not ed.is_empty():
				ed.kind = "card"
				ed.card = card
				events.append(ed)
			for i in gs.charms.size():
				if gs.charm_disabled(i):
					continue
				var fx := _on_card(gs.charms[i], card)
				if not fx.is_empty():
					fx.kind = "charm"
					fx.charm_index = i
					fx.card = card
					events.append(fx)
		if card.get("enh", "") == "glass" and gs.rng.randi_range(1, 4) == 1:
			shatter.append(card)

	for card in held:
		if card.get("enh", "") == "iron" and not gs.is_debuffed(card):
			events.append({"kind": "held", "card": card, "xmult": 1.5})

	var ctx := {"gs": gs, "played": played, "contains": ev.contains}
	for i in gs.charms.size():
		if gs.charm_disabled(i):
			continue
		var inst: Dictionary = gs.charms[i]
		var fx := _on_hand(inst, ctx)
		if not fx.is_empty():
			fx.kind = "charm"
			fx.charm_index = i
			events.append(fx)
		var ed := edition_fx(inst.get("ed", ""))
		if not ed.is_empty():
			ed.kind = "charm"
			ed.charm_index = i
			events.append(ed)
	return {"events": events, "shatter": shatter}


static func edition_fx(ed: String) -> Dictionary:
	match ed:
		"foil":
			return {"chips": 50}
		"holo":
			return {"mult": 10}
		"chroma":
			return {"xmult": 1.5}
	return {}


static func _enhancement(gs: GameState, card: Dictionary) -> Dictionary:
	match card.get("enh", ""):
		"etched":
			return {"chips": 30}
		"charged":
			return {"mult": 4}
		"glass":
			return {"xmult": 2.0}
		"lucky":
			if gs.rng.randi_range(1, 5) == 1:
				return {"mult": 20}
	return {}


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
	var text: String = d.desc
	if inst.id == "snowball":
		text = "%s\n(Currently +%d Mult)" % [d.desc, inst.data.get("m", 0)]
	if inst.get("ed", "") != "":
		var e: Dictionary = Data.EDITIONS[inst.ed]
		text += "\n%s: %s" % [e.name, e.desc]
	return text
