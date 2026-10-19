class_name Poker
extends RefCounted

## Evaluates up to five played cards. Returns
## { name, scoring: Array (in played order), contains: Array of hand names }.
static func evaluate(cards: Array) -> Dictionary:
	if cards.is_empty():
		return {}
	var by_rank := {}
	for c in cards:
		if not by_rank.has(c.rank):
			by_rank[c.rank] = []
		by_rank[c.rank].append(c)
	var groups: Array = by_rank.values()
	groups.sort_custom(func(a, b):
		if a.size() != b.size():
			return a.size() > b.size()
		return a[0].rank > b[0].rank)

	var flush := false
	var straight := false
	if cards.size() == 5:
		flush = cards.all(func(c): return c.suit == cards[0].suit)
		if by_rank.size() == 5:
			var ranks: Array = by_rank.keys()
			ranks.sort()
			straight = ranks[4] - ranks[0] == 4 or ranks == [2, 3, 4, 5, 14]

	var top: int = groups[0].size()
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
	var scoring: Array = [groups[0][0]]
	if straight and flush:
		name = "Straight Flush"
		scoring = cards.duplicate()
	elif top >= 4:
		name = "Four of a Kind"
		scoring = groups[0]
	elif top == 3 and second >= 2:
		name = "Full House"
		scoring = cards.duplicate()
	elif flush:
		name = "Flush"
		scoring = cards.duplicate()
	elif straight:
		name = "Straight"
		scoring = cards.duplicate()
	elif top == 3:
		name = "Three of a Kind"
		scoring = groups[0]
	elif top == 2 and second == 2:
		name = "Two Pair"
		scoring = groups[0] + groups[1]
	elif top == 2:
		name = "Pair"
		scoring = groups[0]

	var ordered := cards.filter(func(c): return scoring.has(c))
	return {"name": name, "scoring": ordered, "contains": contains}
