class_name Poker
extends RefCounted

## Evaluates up to five played cards. Returns
## { name, scoring: Array (in played order), contains: Array of hand names }.
## `opts` comes from GameState.poker_opts():
##   four    Flushes and Straights need only 4 cards
##   skip    Straights may skip one rank between cards
##   blot    Hearts/Diamonds and Spades/Clubs count as one suit each
##   all     every played card scores
## Wild cards count as every suit; Stone cards have no rank or suit and
## always score.
static func evaluate(cards: Array, opts: Dictionary = {}) -> Dictionary:
	if cards.is_empty():
		return {}
	var stones := cards.filter(func(c): return c.get("enh", "") == "stone")
	var ranked := cards.filter(func(c): return c.get("enh", "") != "stone")
	var by_rank := {}
	for c in ranked:
		if not by_rank.has(c.rank):
			by_rank[c.rank] = []
		by_rank[c.rank].append(c)
	var groups: Array = by_rank.values()
	groups.sort_custom(func(a, b):
		if a.size() != b.size():
			return a.size() > b.size()
		return a[0].rank > b[0].rank)

	var need := 4 if opts.get("four", false) else 5
	var flush_cards := _flush(ranked, need, opts.get("blot", false))
	var straight_cards := _straight(ranked, by_rank, need, opts.get("skip", false))
	var flush := not flush_cards.is_empty()
	var straight := not straight_cards.is_empty()

	var top: int = groups[0].size() if groups.size() > 0 else 0
	var second: int = groups[1].size() if groups.size() > 1 else 0

	var contains := ["High Card"]
	if top >= 2:
		contains.append("Pair")
	if top >= 2 and second >= 2:
		contains.append("Two Pair")
	if top >= 3:
		contains.append("Three of a Kind")
	if straight:
		contains.append("Straight")
	if flush:
		contains.append("Flush")
	if top >= 3 and second >= 2:
		contains.append("Full House")
	if top >= 4:
		contains.append("Four of a Kind")
	if straight and flush:
		contains.append("Straight Flush")

	var name := "High Card"
	var scoring: Array = [groups[0][0]] if top > 0 else []
	if straight and flush:
		name = "Straight Flush"
		scoring = straight_cards + flush_cards
	elif top >= 4:
		name = "Four of a Kind"
		scoring = groups[0]
	elif top == 3 and second >= 2:
		name = "Full House"
		scoring = groups[0] + groups[1]
	elif flush:
		name = "Flush"
		scoring = flush_cards
	elif straight:
		name = "Straight"
		scoring = straight_cards
	elif top == 3:
		name = "Three of a Kind"
		scoring = groups[0]
	elif top == 2 and second == 2:
		name = "Two Pair"
		scoring = groups[0] + groups[1]
	elif top == 2:
		name = "Pair"
		scoring = groups[0]

	var keep_all: bool = opts.get("all", false)
	var ordered := cards.filter(func(c): return keep_all or scoring.has(c) or stones.has(c))
	return {"name": name, "scoring": ordered, "contains": contains}


## Whether `card` counts as suit `s` (Wild counts as every suit).
static func suit_is(card: Dictionary, s: int, blot := false) -> bool:
	match card.get("enh", ""):
		"stone":
			return false
		"wild":
			return true
	if blot:
		return card.suit % 2 == s % 2  # 0/2 spades+clubs, 1/3 hearts+diamonds
	return card.suit == s


## The cards making a flush of at least `need`, or [].
static func _flush(cards: Array, need: int, blot: bool) -> Array:
	if cards.size() < need:
		return []
	for s in 4:
		var members := cards.filter(func(c): return suit_is(c, s, blot))
		if members.size() >= need:
			return members
	return []


## The cards making a straight of at least `need` distinct ranks, or [].
static func _straight(cards: Array, by_rank: Dictionary, need: int, skip: bool) -> Array:
	if by_rank.size() < need:
		return []
	var have := {}
	for r in by_rank:
		have[r] = true
		if r == 14:
			have[1] = true  # the ace also plays low
	var best: Array = []
	for start in range(1, 15):
		if not have.has(start):
			continue
		var run := [start]
		var cur := start
		while true:
			if have.has(cur + 1):
				cur += 1
			elif skip and have.has(cur + 2):
				cur += 2
			else:
				break
			run.append(cur)
		if run.size() > best.size():
			best = run
	if best.size() < need:
		return []
	var ranks := best.map(func(r): return 14 if r == 1 else r)
	return cards.filter(func(c): return ranks.has(c.rank))
