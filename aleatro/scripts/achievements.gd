class_name Achievements
extends RefCounted

## Aleatro's Google Play Games achievements and leaderboards, after Balatro's
## achievement list. Each achievement is checked with the same goals as the
## unlocks (Unlocks.met_goal) plus a few of its own; `steps` makes it
## incremental in Play Games (progress shown), filled from a career stat.
##
## Play Console gives each one an ID; the game finds it in
## res://pgs/games-ids.xml (Play Console > Achievements > Get resources) under
## "achievement_" + the key, or the snake_case English name. Points add up to
## Play Games' limit of 1000. See tools/play_games/README.md.

const LIST := [
	{"key": "climbing", "name": "Climbing", "desc": "Reach ante 4", "points": 10, "goal": {"type": "ante", "n": 4}},
	{"key": "summit", "name": "Summit", "desc": "Reach ante 8", "points": 20, "goal": {"type": "ante", "n": 8}},
	{"key": "victory_lap", "name": "Victory Lap", "desc": "Win a run", "points": 30, "goal": {"type": "stat", "stat": "wins", "n": 1}},
	{"key": "red_chip", "name": "Red Chip", "desc": "Win a run on Red Chip stake or higher", "points": 30, "goal": {"type": "win_stake", "n": 2}},
	{"key": "black_chip", "name": "Black Chip", "desc": "Win a run on Black Chip stake or higher", "points": 50, "goal": {"type": "win_stake", "n": 4}},
	{"key": "gold_chip", "name": "Gold Chip", "desc": "Win a run on Gold Chip stake", "points": 100, "goal": {"type": "win_stake", "n": 8}},
	{"key": "card_sharp", "name": "Card Sharp", "desc": "Play 2,500 cards", "points": 20, "goal": {"type": "stat", "stat": "cards_played", "n": 2500}, "steps": true},
	{"key": "clean_sweep", "name": "Clean Sweep", "desc": "Discard 2,500 cards", "points": 20, "goal": {"type": "stat", "stat": "cards_discarded", "n": 2500}, "steps": true},
	{"key": "nest_egg", "name": "Nest Egg", "desc": "Have $400 at once", "points": 30, "goal": {"type": "money", "n": 400}},
	{"key": "speedrun", "name": "Speedrun", "desc": "Win a run in 12 rounds or fewer", "points": 50, "goal": {"type": "win_rounds", "n": 12}},
	{"key": "glass_cannon", "name": "Glass Cannon", "desc": "Shatter 2 Glass cards in one hand", "points": 20, "goal": {"type": "shatter_hand", "n": 2}},
	{"key": "royalty", "name": "Royalty", "desc": "Play a Royal Flush", "points": 20, "goal": {"type": "royal"}},
	{"key": "grandmaster", "name": "Grandmaster", "desc": "Level any poker hand up to level 10", "points": 30, "goal": {"type": "hand_level", "n": 10}},
	{"key": "collector", "name": "Collector", "desc": "Discover every charm", "points": 50, "goal": {"type": "seen_charms_all"}},
	{"key": "living_legend", "name": "Living Legend", "desc": "Discover a legendary charm", "points": 20, "goal": {"type": "seen_legendary"}},
	{"key": "stargazer", "name": "Stargazer", "desc": "Discover every Rune", "points": 20, "goal": {"type": "seen_runes"}},
	{"key": "fortune_teller", "name": "Fortune Teller", "desc": "Discover every Spell", "points": 20, "goal": {"type": "seen_spells"}},
	{"key": "seer", "name": "Seer", "desc": "Discover every Omen", "points": 20, "goal": {"type": "seen_omens"}},
	{"key": "hex_hunter", "name": "Hex Hunter", "desc": "Face every boss blind", "points": 30, "goal": {"type": "seen_hexes_all"}},
	{"key": "slim_pickings", "name": "Slim Pickings", "desc": "Have 20 or fewer cards in your deck", "points": 20, "goal": {"type": "deck_max", "n": 20}},
	{"key": "overstuffed", "name": "Overstuffed", "desc": "Have 80 or more cards in your deck", "points": 20, "goal": {"type": "deck_min", "n": 80}},
	{"key": "no_takebacks", "name": "No Takebacks", "desc": "Win a run without rerolling the shop", "points": 30, "goal": {"type": "win_no_reroll"}},
	{"key": "rule_bender", "name": "Rule Bender", "desc": "Win a challenge", "points": 30, "goal": {"type": "challenges", "n": 1}},
	{"key": "rule_breaker", "name": "Rule Breaker", "desc": "Win every challenge", "points": 80, "goal": {"type": "challenges", "n": -1}},
	{"key": "five_figures", "name": "Five Figures", "desc": "Score 10,000 in one hand", "points": 10, "goal": {"type": "stat", "stat": "best_hand", "n": 10000}},
	{"key": "millionaire", "name": "Millionaire", "desc": "Score 1,000,000 in one hand", "points": 30, "goal": {"type": "stat", "stat": "best_hand", "n": 1000000}},
	{"key": "astronomical", "name": "Astronomical", "desc": "Score 100,000,000 in one hand", "points": 50, "goal": {"type": "stat", "stat": "best_hand", "n": 100000000}},
	{"key": "deck_master", "name": "Deck Master", "desc": "Win a run with every deck", "points": 100, "goal": {"type": "decks_won"}},
	{"key": "five_alive", "name": "Five Alive", "desc": "Play a Flush Five", "points": 20, "goal": {"type": "play_hand", "hand": "Flush Five"}},
	{"key": "big_spender", "name": "Big Spender", "desc": "Spend $2,500 in shops", "points": 20, "goal": {"type": "stat", "stat": "shop_spent", "n": 2500}, "steps": true},
]

## `stat` is the career stat sent as the score; `low` when fewer is better.
const LEADERBOARDS := [
	{"key": "best_hand", "name": "Best Hand", "desc": "Highest score in a single hand", "stat": "best_hand"},
	{"key": "highest_ante", "name": "Highest Ante", "desc": "Highest ante reached in a run", "stat": "best_ante"},
	{"key": "fastest_win", "name": "Fastest Win", "desc": "Fewest rounds to win a run", "stat": "fastest_win", "low": true},
	{"key": "career_wins", "name": "Career Wins", "desc": "Runs won", "stat": "wins"},
]


static func by_key(key: String) -> Dictionary:
	for a in LIST:
		if a.key == key:
			return a
	return {}


## Whether achievement `a` is earned, given check_unlocks' context `c`.
static func met(a: Dictionary, c: Dictionary) -> bool:
	var g: Dictionary = a.goal
	var gs: GameState = c.get("gs")
	var ev: String = c.get("event", "")
	var profile: Dictionary = c.get("profile", {})
	match g.type:
		"seen_charms_all":
			var seen: Array = profile.get("seen_charms", [])
			return Data.CHARMS.all(func(ch): return seen.has(ch.id))
		"seen_legendary":
			var seen: Array = profile.get("seen_charms", [])
			return Data.CHARMS.any(func(ch): return ch.rarity == 3 and seen.has(ch.id))
		"seen_omens":
			var seen: Array = profile.get("seen_spells", [])
			return Data.SPELLS.all(func(sp): return not sp.get("omen", false) or seen.has(sp.id))
		"seen_hexes_all":
			var seen: Array = profile.get("seen_hexes", [])
			return Data.HEXES.all(func(h): return seen.has(h.id))
		"challenges":
			var won: Array = profile.get("challenges_won", [])
			return won.size() >= (Data.CHALLENGES.size() if g.n < 0 else g.n)
		"decks_won":
			var wins = profile.get("deck_stakes", {})
			return wins is Dictionary and Data.DECKS.all(func(d): return int(wins.get(d.id, 0)) >= 1)
	if gs == null:
		return Unlocks.met_goal(g, c)
	match g.type:
		"win_stake":
			return ev == "won_run" and gs.stake >= g.n
		"win_no_reroll":
			return ev == "won_run" and not gs.run_flags.get("rerolled", false)
		"hand_level":
			return gs.hand_levels.values().any(func(l): return int(l) >= g.n)
		"play_hand":
			return ev == "hand" and c.get("hand_name", "") == g.hand
		"royal":
			var cards: Array = c.get("cards", [])
			if ev != "hand" or c.get("hand_name", "") != "Straight Flush" or cards.size() != 5:
				return false
			var ranks := cards.map(func(k): return k.get("rank", 0))
			ranks.sort()
			return ranks == [10, 11, 12, 13, 14]
		"shatter_hand":
			return ev == "shatter" and int(c.get("count", 0)) >= g.n
		"deck_max":
			return c.get("in_round", false) and gs.deck.size() <= g.n
		"deck_min":
			return gs.deck.size() >= g.n
	return Unlocks.met_goal(g, c)


## Progress toward an incremental achievement, 0..its target.
static func progress(a: Dictionary, stats: Dictionary) -> int:
	return mini(int(stats.get(a.goal.stat, 0)), int(a.goal.n))
