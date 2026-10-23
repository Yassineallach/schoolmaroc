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

	var ctx := {"gs": gs, "played": played, "held": held, "contains": ev.contains, "name": hand_name, "scoring": ev.scoring,
		"final": gs.hands_left == 0, "first_face": -1, "first": -1}
	for card in ev.scoring:
		if not gs.is_debuffed(card):
			if ctx.first == -1:
				ctx.first = card.id
			if ctx.first_face == -1 and gs.is_face(card):
				ctx.first_face = card.id

	for card in ev.scoring:
		if gs.is_debuffed(card):
			events.append({"kind": "card", "card": card, "debuff": true})
			continue
		# Each entry is one more pass over the card: -1 for its seal, else the charm.
		var again := []
		if card.get("seal", "") == "crimson":
			again.append(-1)
		for i in gs.charms.size():
			if not gs.charm_disabled(i):
				for k in _retriggers(gs.effective(i), card, ctx):
					again.append(i)
		for rep in again.size() + 1:
			if rep > 0:
				var a := {"kind": "card", "card": card, "again": true}
				if again[rep - 1] >= 0:
					a.charm_index = again[rep - 1]
				events.append(a)
			var stone: bool = card.get("enh", "") == "stone"
			events.append({"kind": "card", "card": card, "chips": 50 if stone else Data.card_chips(card.rank) + card.get("bonus", 0)})
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
				var fx := _on_card(gs.effective(i), card, ctx)
				if not fx.is_empty():
					fx.kind = "charm"
					fx.charm_index = i
					fx.card = card
					events.append(fx)
			# charms that grow from this card being scored
			for c in gs.charms:
				match c.id:
					"rambler":
						card.bonus = card.get("bonus", 0) + 5
					"tiny":
						if card.rank == 2 and not stone:
							c.data.c = c.data.get("c", 0) + 8
		if card.get("enh", "") == "glass" and gs.roll(4):
			shatter.append(card)

	var lowest = null
	for card in held:
		if lowest == null or card.rank <= lowest.rank:
			lowest = card
	ctx.lowest = lowest.id if lowest != null else -1
	var mimics := 0
	for i in gs.charms.size():
		if not gs.charm_disabled(i) and gs.effective(i).get("id", "") == "mimic":
			mimics += 1
	for card in held:
		if gs.is_debuffed(card):
			continue
		var reps := 1 + mimics + (1 if card.get("seal", "") == "crimson" else 0)
		for rep in reps:
			var before := events.size()
			if card.get("enh", "") == "iron":
				events.append({"kind": "held", "card": card, "xmult": 1.5})
			for i in gs.charms.size():
				if gs.charm_disabled(i):
					continue
				var fx := _on_held(gs.effective(i), card, ctx)
				if not fx.is_empty():
					fx.kind = "held"
					fx.charm_index = i
					fx.card = card
					events.append(fx)
			if rep > 0 and events.size() > before:
				events.insert(before, {"kind": "held", "card": card, "again": true})
			elif events.size() == before:
				break

	var pennants := 0
	for i in gs.charms.size():
		if not gs.charm_disabled(i) and gs.effective(i).get("id", "") == "pennant":
			pennants += 1
	for i in gs.charms.size():
		if gs.charm_disabled(i):
			continue
		var inst: Dictionary = gs.charms[i]
		var fx := _on_hand(gs.effective(i), ctx)
		if not fx.is_empty():
			fx.kind = "charm"
			fx.charm_index = i
			events.append(fx)
		if Data.charm_def(inst.id).rarity == 1:
			for k in pennants:
				events.append({"kind": "charm", "charm_index": i, "xmult": 1.5})
		var ed := edition_fx(inst.get("ed", ""))
		if not ed.is_empty():
			ed.kind = "charm"
			ed.charm_index = i
			events.append(ed)
	# Planetarium: Runes kept for this hand give x1.5 each
	if gs.has_voucher("planetarium"):
		for k in gs.spells.size():
			if gs.spells[k] == "rune:" + hand_name:
				events.append({"kind": "spell", "spell_index": k, "xmult": 1.5})
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
			var fx := {}
			if gs.roll(5):
				fx.mult = 20
			if gs.roll(15):
				fx.money = 20
			if not fx.is_empty():
				for c in gs.charms:
					if c.id == "maneki":
						c.data.x = c.data.get("x", 1.0) + 0.25
			return fx
	return {}


## How many extra times `inst` makes a scored card count.
static func _retriggers(inst: Dictionary, card: Dictionary, ctx: Dictionary) -> int:
	var gs: GameState = ctx.gs
	match inst.get("id", ""):
		"encore":
			if card.rank >= 2 and card.rank <= 5 and card.get("enh", "") != "stone": return 1
		"masquerade":
			if gs.is_face(card): return 1
		"punchcard":
			if card.id == ctx.first: return 2
		"twilight":
			if ctx.final: return 1
		"fizz":
			return 1
	return 0


static func _on_card(inst: Dictionary, card: Dictionary, ctx: Dictionary) -> Dictionary:
	var gs: GameState = ctx.gs
	if card.get("enh", "") == "stone":
		return {}  # no rank or suit for charms to read
	var r: int = card.rank
	var face := gs.is_face(card)
	match inst.get("id", ""):
		"grin":
			if face: return {"mult": 5}
		"radio":
			if r == 10 or r == 4: return {"chips": 10, "mult": 4}
		"spearhead":
			if gs.suit_is(card, 0): return {"chips": 50}
		"clover":
			if gs.suit_is(card, 2): return {"mult": 7}
		"rawgem":
			if gs.suit_is(card, 3): return {"money": 1}
		"heartstone":
			if gs.suit_is(card, 1) and gs.roll(2): return {"xmult": 1.5}
		"portrait":
			if card.id == ctx.first_face: return {"xmult": 2.0}
		"callingcard":
			if face and gs.roll(2): return {"money": 2}
		"ticket":
			if card.get("enh", "") == "gilded": return {"money": 4}
		"foolking":
			if r == 12 or r == 13: return {"xmult": 2.0}
		"relic":
			if gs.suit_is(card, inst.data.get("suit", 0)): return {"xmult": 1.5}
		"idol":
			if r == inst.data.get("rank", 0) and gs.suit_is(card, inst.data.get("suit", 0)): return {"xmult": 2.0}
		"crystal":
			if r == 8 and gs.roll(4) and gs.give_spell() != "": return {"text": "+1 Spell"}
		"ruby":
			if gs.suit_is(card, 1): return {"mult": 3}
		"topaz":
			if gs.suit_is(card, 3): return {"mult": 3}
		"onyx":
			if gs.suit_is(card, 0): return {"mult": 3}
		"jade":
			if gs.suit_is(card, 2): return {"mult": 3}
		"spiral":
			if r in [14, 2, 3, 5, 8]: return {"mult": 8}
		"even":
			if r <= 10 and r % 2 == 0: return {"mult": 4}
		"odd":
			if r == 14 or (r <= 10 and r % 2 == 1): return {"chips": 31}
		"scribe":
			if r == 14: return {"chips": 20, "mult": 4}
		"court":
			if face: return {"chips": 30}
	return {}


## Effects of `inst` on a card held in hand (not played).
static func _on_held(inst: Dictionary, card: Dictionary, ctx: Dictionary) -> Dictionary:
	var gs: GameState = ctx.gs
	if card.get("enh", "") == "stone":
		return {}
	match inst.get("id", ""):
		"valet":
			if gs.is_face(card) and gs.roll(2): return {"money": 1}
		"regent":
			if card.rank == 13: return {"xmult": 1.5}
		"moonrise":
			if card.rank == 12: return {"mult": 13}
		"fist":
			if card.id == ctx.lowest: return {"mult": 2 * Data.card_chips(card.rank)}
	return {}


static func _on_hand(inst: Dictionary, ctx: Dictionary) -> Dictionary:
	var gs: GameState = ctx.gs
	var contains: Array = ctx.contains
	var played: Array = ctx.played
	var data: Dictionary = inst.get("data", {})
	match inst.get("id", ""):
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
				for k in 4:
					if gs.suit_is(c, k):
						suits[k] = true
			if suits.size() == 4: return {"xmult": 3.0}
		"duet":
			if contains.has("Pair"): return {"xmult": 2.0}
		"pairchips":
			if contains.has("Pair"): return {"chips": 50}
		"twopairchips":
			if contains.has("Two Pair"): return {"chips": 80}
		"tripschips":
			if contains.has("Three of a Kind"): return {"chips": 100}
		"straightchips":
			if contains.has("Straight"): return {"chips": 100}
		"flushchips":
			if contains.has("Flush"): return {"chips": 80}
		"tripsx":
			if contains.has("Three of a Kind"): return {"xmult": 3.0}
		"quadsx":
			if contains.has("Four of a Kind"): return {"xmult": 4.0}
		"straightx":
			if contains.has("Straight"): return {"xmult": 3.0}
		"flushx":
			if contains.has("Flush"): return {"xmult": 2.0}
		"tightrope":
			if ctx.final: return {"xmult": 3.0}
		"corsair":
			var worth := 0
			for c in gs.charms:
				if c != inst:
					worth += gs.sell_value(c)
			if worth > 0: return {"mult": worth}
		"fame":
			var n: int = gs.hands_played_count.get(ctx.name, 0)
			if n > 0: return {"mult": n}
		"commuter":
			var m: int = inst.data.get("m", 0)
			if m > 0: return {"mult": m}
		"sprinter", "foursquare":
			var c: int = inst.data.get("c", 0)
			if c > 0: return {"chips": c}
		"sorbet":
			return {"chips": inst.data.get("c", 100)}
		"kettle":
			return {"mult": inst.data.get("m", 20)}
		"plantain":
			return {"mult": 15}
		"ripe":
			return {"xmult": 3.0}
		"cardshark":
			if gs.boss_state.get("round_hands", {}).get(ctx.name, 0) > 1: return {"xmult": 3.0}
		"loyal":
			var n: int = inst.data.get("n", 0)
			if n > 0 and n % 6 == 0: return {"xmult": 4.0}
		"slate":
			if ctx.held.all(func(c): return gs.suit_is(c, 0) or gs.suit_is(c, 2)): return {"xmult": 3.0}
		"seer":
			var n: int = gs.run_flags.get("spells_cast", 0)
			if n > 0: return {"mult": n}
		"daredevil":
			return {"chips": 250}
		"rewind":
			if gs.skips > 0: return {"xmult": 1.0 + 0.25 * gs.skips}
		"scrapbook":
			var m: int = data.get("m", 0)
			if m > 0: return {"mult": m}
		"bootstraps":
			if gs.money >= 5: return {"mult": 2 * (gs.money / 5)}
		"noodles":
			return {"xmult": data.get("x", 2.0)}
		"ironwill":
			var n := gs.deck.filter(func(c): return c.get("enh", "") == "iron").size()
			if n > 0: return {"xmult": 1.0 + 0.2 * n}
		"quarry":
			var n := gs.deck.filter(func(c): return c.get("enh", "") == "stone").size()
			if n > 0: return {"chips": 25 * n}
		"license":
			if gs.deck.filter(func(c): return c.get("enh", "") != "").size() >= 16: return {"xmult": 3.0}
		"monolith", "frenzy", "hologram", "starmap", "bonfire", "maneki", "glazier", "roadtrip", "skull", "bonecrown":
			var x: float = data.get("x", 1.0)
			if x > 1.0: return {"xmult": x}
		"dagger", "trousers", "flashcard":
			var m: int = data.get("m", 0)
			if m > 0: return {"mult": m}
		"tiny", "keep":
			var c: int = data.get("c", 0)
			if c > 0: return {"chips": c}
		"doublevision":
			var scoring: Array = ctx.scoring
			for k in scoring.size():
				if gs.suit_is(scoring[k], 2):
					for j in scoring.size():
						if j != k and [0, 1, 3].any(func(s): return gs.suit_is(scoring[j], s)):
							return {"xmult": 2.0}
		"wear":
			var short := gs.start_deck_size - gs.deck.size()
			if short > 0: return {"mult": 4 * short}
	return {}


static func describe(inst: Dictionary) -> String:
	var d: Dictionary = Data.charm_def(inst.id)
	var text: String = d.desc
	var data: Dictionary = inst.get("data", {})
	match inst.id:
		"snowball", "commuter":
			text += "\n(Currently +%d Mult)" % data.get("m", 0)
		"kettle":
			text += "\n(Currently +%d Mult)" % data.get("m", 20)
		"sprinter", "foursquare":
			text += "\n(Currently +%d Chips)" % data.get("c", 0)
		"sorbet":
			text += "\n(Currently +%d Chips)" % data.get("c", 100)
		"fizz":
			text += "\n(%d hands left)" % data.get("n", 10)
		"loyal":
			text += "\n(%d hands to go)" % (6 - data.get("n", 0) % 6)
		"monolith", "frenzy", "hologram", "starmap", "bonfire", "maneki", "glazier", "roadtrip", "skull", "bonecrown":
			text += "\n(Currently x%s Mult)" % str(snappedf(data.get("x", 1.0), 0.01))
		"noodles":
			text += "\n(Currently x%s Mult)" % str(snappedf(data.get("x", 2.0), 0.01))
		"dagger", "trousers", "flashcard", "scrapbook":
			text += "\n(Currently +%d Mult)" % data.get("m", 0)
		"tiny", "keep":
			text += "\n(Currently +%d Chips)" % data.get("c", 0)
		"sprout":
			text += "\n(Currently +%d hand size)" % data.get("h", 5)
		"skyrocket":
			text += "\n(Currently $%d)" % data.get("p", 1)
		"phantom":
			text += "\n(%s)" % ("Ready to sell" if data.get("r", 0) >= 2 else "%d of 2 rounds" % data.get("r", 0))
	if data.has("suit") and inst.id in ["relic", "keep", "idol"]:
		var what: String = Data.SUIT_NAMES[data.suit]
		if inst.id == "idol":
			what = Data.card_name({"rank": data.rank, "suit": data.suit})
		text += "\n(This round: %s)" % what
	if inst.id == "rebate" and data.has("rank"):
		text += "\n(This round: %ss)" % Data.RANK_LABELS[data.rank]
	if inst.id == "errand" and data.has("hand"):
		text += "\n(This round: %s)" % data.hand
	if inst.get("ed", "") != "":
		var e: Dictionary = Data.EDITIONS[inst.ed]
		text += "\n%s: %s" % [e.name, e.desc]
	return text
