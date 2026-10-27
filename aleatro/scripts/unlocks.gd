class_name Unlocks
extends RefCounted

## Charms and vouchers that start locked, each with Balatro's unlock goal
## (the Joker or Voucher it stands for is noted). Until its goal is met a
## locked item never shows up in shops, packs or as the ante's voucher.
##
## Each goal: {text, type, ...}. `met()` checks one against a context built
## by main.gd: {stats, profile, gs, event, ...event data}.

const GOALS := {
	# ---------------------------------------------------------------- charms
	"ticket": {"text": "Play a 5 card hand made only of Gilded cards", "type": "hand_all_enh", "enh": "gilded"},  # Golden Ticket
	"lastlaugh": {"text": "Lose 5 runs", "type": "stat", "stat": "losses", "n": 5},  # Mr. Bones
	"tightrope": {"text": "Play 200 hands", "type": "stat", "stat": "hands_played", "n": 200},  # Acrobat
	"masquerade": {"text": "Play 300 face cards", "type": "stat", "stat": "faces_played", "n": 300},  # Sock and Buskin
	"corsair": {"text": "Sell 20 charms", "type": "stat", "stat": "charms_sold", "n": 20},  # Swashbuckler
	"minstrel": {"text": "Win 5 rounds in a row using only 1 hand each", "type": "stat", "stat": "one_hand_streak", "n": 5},  # Troubadour
	"notary": {"text": "Have a Gilded card with a Golden Seal", "type": "deck_enh_seal", "enh": "gilded", "seal": "golden"},  # Certificate
	"blot": {"text": "Have 3 Wild cards in your deck", "type": "deck_enh", "enh": "wild", "n": 3},  # Smeared Joker
	"rewind": {"text": "Continue a saved run", "type": "event", "event": "continue"},  # Throwback
	"punchcard": {"text": "Beat a boss blind with a High Card", "type": "boss_hand", "hand": "High Card"},  # Hanging Chad
	"rawgem": {"text": "Have 30 Diamonds in your deck", "type": "deck_suit", "suit": 3, "n": 30},  # Rough Gem
	"heartstone": {"text": "Have 30 Hearts in your deck", "type": "deck_suit", "suit": 1, "n": 30},  # Bloodstone
	"spearhead": {"text": "Have 30 Spades in your deck", "type": "deck_suit", "suit": 0, "n": 30},  # Arrowhead
	"clover": {"text": "Have 30 Clubs in your deck", "type": "deck_suit", "suit": 2, "n": 30},  # Onyx Agate
	"glazier": {"text": "Have 5 Glass cards in your deck", "type": "deck_enh", "enh": "glass", "n": 5},  # Glass Joker
	"ringmaster": {"text": "Reach ante 4", "type": "ante", "n": 4},  # Showman
	"prism": {"text": "Reach ante 8", "type": "ante", "n": 8},  # Flower Pot
	"tracing": {"text": "Win a run", "type": "stat", "stat": "wins", "n": 1},  # Blueprint
	"tiny": {"text": "Win a run in 18 rounds or fewer", "type": "win_rounds", "n": 18},  # Wee Joker
	"merry": {"text": "Win a run in 12 rounds or fewer", "type": "win_rounds", "n": 12},  # Merry Andy
	"loaded": {"text": "Score 10,000 in one hand", "type": "stat", "stat": "best_hand", "n": 10000},  # Oops! All 6s
	"idol": {"text": "Score 1,000,000 in one hand", "type": "stat", "stat": "best_hand", "n": 1000000},  # The Idol
	"daredevil": {"text": "Score 100,000,000 in one hand", "type": "stat", "stat": "best_hand", "n": 100000000},  # Stuntman
	"doublevision": {"text": "Play a hand with four 7 of Clubs", "type": "hand_cards", "rank": 7, "suit": 2, "n": 4},  # Seeing Double
	"toreador": {"text": "Beat a boss blind in one hand without discarding", "type": "boss_one_hand"},  # Matador
	"roadtrip": {"text": "Discard 5 Jacks at once", "type": "discard_rank", "rank": 11, "n": 5},  # Hit the Road
	"duet": {"text": "Win a run without playing a Pair", "type": "win_no_hand", "hand": "Pair"},  # The Duo
	"tripsx": {"text": "Win a run without playing Three of a Kind", "type": "win_no_hand", "hand": "Three of a Kind"},  # The Trio
	"quadsx": {"text": "Win a run without playing Four of a Kind", "type": "win_no_hand", "hand": "Four of a Kind"},  # The Family
	"straightx": {"text": "Win a run without playing a Straight", "type": "win_no_hand", "hand": "Straight"},  # The Order
	"flushx": {"text": "Win a run without playing a Flush", "type": "win_no_hand", "hand": "Flush"},  # The Tribe
	"phantom": {"text": "Win a run without ever having more than 4 charms", "type": "win_few_charms", "n": 4},  # Invisible Joker
	"brainwave": {"text": "Discard a Royal Flush", "type": "discard_royal"},  # Brainstorm
	"satellite": {"text": "Have $400", "type": "money", "n": 400},  # Satellite
	"moonrise": {"text": "Play every Heart in your deck in one round", "type": "all_hearts"},  # Shoot the Moon
	"license": {"text": "Have 16 enhanced cards in your deck", "type": "deck_enhanced", "n": 16},  # Driver's License
	"diviner": {"text": "Discover every Spell", "type": "seen_spells"},  # Cartomancer
	"stargazer": {"text": "Discover every Rune", "type": "seen_runes"},  # Astronomer
	"kindling": {"text": "Sell 50 charms or spells", "type": "stat", "stat": "items_sold", "n": 50},  # Burnt Joker
	"bootstraps": {"text": "Have 2 Chroma charms at once", "type": "charm_edition", "eds": ["chroma"], "n": 2},  # Bootstraps
	# ---------------------------------------------------------------- vouchers
	"shelves": {"text": "Spend $2,500 in shops", "type": "stat", "stat": "shop_spent", "n": 2500},  # Overstock Plus
	"firesale": {"text": "Redeem 10 vouchers in one run", "type": "run_vouchers", "n": 10},  # Liquidation
	"shine": {"text": "Have 5 Foil, Holo or Chroma charms at once", "type": "charm_edition", "eds": ["foil", "holo", "chroma"], "n": 5},  # Glow Up
	"shaker": {"text": "Reroll the shop 100 times", "type": "stat", "stat": "rerolls", "n": 100},  # Reroll Glut
	"lamp": {"text": "Use 25 Spells from Spell Packs", "type": "stat", "stat": "pack_spells_used", "n": 25},  # Omen Globe
	"planetarium": {"text": "Use 25 Runes from Rune Packs", "type": "stat", "stat": "pack_runes_used", "n": 25},  # Observatory
	"tongs": {"text": "Play 2,500 cards", "type": "stat", "stat": "cards_played", "n": 2500},  # Nacho Tong
	"recycler": {"text": "Discard 2,500 cards", "type": "stat", "stat": "cards_discarded", "n": 2500},  # Recyclomancy
	"spellbaron": {"text": "Buy 50 Spells from the shop", "type": "stat", "stat": "spells_bought", "n": 50},  # Tarot Tycoon
	"runebaron": {"text": "Buy 50 Runes from the shop", "type": "stat", "stat": "runes_bought", "n": 50},  # Planet Tycoon
	"goldtree": {"text": "Earn the most interest 10 rounds in a row", "type": "stat", "stat": "interest_streak", "n": 10},  # Money Tree
	"antimatter": {"text": "Redeem Blank 10 times", "type": "stat", "stat": "blanks_redeemed", "n": 10},  # Antimatter
	"showcase": {"text": "Buy 20 playing cards from the shop", "type": "stat", "stat": "cards_bought", "n": 20},  # Illusion
	"stoneglyph": {"text": "Reach ante 12", "type": "ante", "n": 12},  # Petroglyph
	"rewrite": {"text": "Discover 25 blinds", "type": "blinds_seen", "n": 25},  # Retcon
	"palette": {"text": "Get down to a hand size of 5", "type": "hand_size", "n": 5},  # Palette
}


static func is_voucher(id: String) -> bool:
	return not Data.voucher_def(id).is_empty()


## The ids still locked for a profile that has unlocked `unlocked`.
static func locked(unlocked: Array) -> Array:
	return GOALS.keys().filter(func(id): return not unlocked.has(id))


static func goal_text(id: String) -> String:
	return GOALS[id].text if GOALS.has(id) else ""


## Whether goal `id` is met in context `c`.
static func met(id: String, c: Dictionary) -> bool:
	return met_goal(GOALS[id], c)


## Whether goal `g` (any {type, ...} above; achievements use them too) is met.
static func met_goal(g: Dictionary, c: Dictionary) -> bool:
	var stats: Dictionary = c.stats
	var gs: GameState = c.get("gs")
	var ev: String = c.get("event", "")
	match g.type:
		"stat":
			return int(stats.get(g.stat, 0)) >= g.n
		"ante":
			return int(stats.get("best_ante", 0)) >= g.n or (gs != null and gs.ante >= g.n)
		"event":
			return ev == g.event
		"seen_spells":
			var seen: Array = c.profile.get("seen_spells", [])
			return Data.SPELLS.all(func(sp): return sp.get("omen", false) or seen.has(sp.id))
		"seen_runes":
			var seen: Array = c.profile.get("seen_spells", [])
			return Data.HAND_ORDER.all(func(h): return seen.has("rune:" + h))
		"blinds_seen":
			return c.profile.get("seen_hexes", []).size() + 2 >= g.n
	if gs == null:
		return false
	match g.type:
		"money":
			return gs.money >= g.n
		"deck_enh":
			return gs.deck.filter(func(k): return k.get("enh", "") == g.enh).size() >= g.n
		"deck_enhanced":
			return gs.deck.filter(func(k): return k.get("enh", "") != "").size() >= g.n
		"deck_enh_seal":
			return gs.deck.any(func(k): return k.get("enh", "") == g.enh and k.get("seal", "") == g.seal)
		"deck_suit":
			return gs.deck.filter(func(k): return k.get("enh", "") != "stone" and k.suit == g.suit).size() >= g.n
		"charm_edition":
			return gs.charms.filter(func(k): return g.eds.has(k.get("ed", ""))).size() >= g.n
		"run_vouchers":
			return gs.vouchers.size() >= g.n
		"hand_size":
			return c.get("in_round", false) and gs.current_hand_size() <= g.n
		"hand_all_enh":
			var cards: Array = c.get("cards", [])
			return ev == "hand" and cards.size() == 5 and cards.all(func(k): return k.get("enh", "") == g.enh)
		"hand_cards":
			var cards: Array = c.get("cards", [])
			return ev == "hand" and cards.filter(func(k): return k.get("enh", "") != "stone" and k.rank == g.rank and k.suit == g.suit).size() >= g.n
		"all_hearts":
			if ev != "hand":
				return false
			var hearts := gs.deck.filter(func(k): return k.get("enh", "") != "stone" and k.suit == 1)
			var played: Dictionary = c.get("hearts_played", {})
			return not hearts.is_empty() and hearts.all(func(k): return played.has(k.id))
		"discard_rank":
			var cards: Array = c.get("cards", [])
			return ev == "discard" and cards.filter(func(k): return k.get("enh", "") != "stone" and k.rank == g.rank).size() >= g.n
		"discard_royal":
			var cards: Array = c.get("cards", [])
			if ev != "discard" or cards.size() != 5:
				return false
			var r := Poker.evaluate(cards)
			var ranks := cards.map(func(k): return k.get("rank", 0))
			ranks.sort()
			return r.get("name", "") == "Straight Flush" and ranks == [10, 11, 12, 13, 14]
		"boss_hand":
			return ev == "round_won" and c.get("boss", false) and c.get("last_hand", "") == g.hand
		"boss_one_hand":
			return ev == "round_won" and c.get("boss", false) and c.get("plays", 0) == 1 and c.get("discards", 0) == 0
		"win_rounds":
			return ev == "won_run" and gs.rounds <= g.n
		"win_no_hand":
			return ev == "won_run" and int(gs.hands_played_count.get(g.hand, 0)) == 0
		"win_few_charms":
			return ev == "won_run" and int(gs.run_flags.get("max_charms", 0)) <= g.n
	return false
