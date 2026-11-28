class_name Cards
extends RefCounted
## Minor Arcana data helpers. A card is a Dictionary {id:int, suit:int, rank:int}.
## Suits: 0 Wands (Fire), 1 Cups (Water), 2 Swords (Air), 3 Pentacles (Earth).
## Ranks: 1 Ace .. 10, 11 Page, 12 Knight, 13 Queen, 14 King.

const SUIT_NAMES: Array[String] = ["Wands", "Cups", "Swords", "Pentacles"]
const ELEMENTS: Array[String] = ["Fire", "Water", "Air", "Earth"]
const COURT_NAMES := {11: "Page", 12: "Knight", 13: "Queen", 14: "King"}
const ROMAN: Array[String] = ["0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
	"XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI"]


static func make(id: int, suit: int, rank: int) -> Dictionary:
	return {"id": id, "suit": suit, "rank": rank}


static func standard_deck() -> Array:
	var deck: Array = []
	var id := 0
	for s in 4:
		for r in range(1, 15):
			deck.append(make(id, s, r))
			id += 1
	return deck


static func is_court(c: Dictionary) -> bool:
	return int(c["rank"]) >= 11


static func rank_label(rank: int) -> String:
	if rank >= 11:
		return COURT_NAMES[rank]
	if rank == 1:
		return "Ace"
	return ROMAN[rank]


static func corner_label(rank: int) -> String:
	match rank:
		1: return "A"
		11: return "P"
		12: return "Kn"
		13: return "Q"
		14: return "K"
	return ROMAN[rank]


static func title(c: Dictionary) -> String:
	return "%s of %s" % [rank_label(int(c["rank"])), SUIT_NAMES[int(c["suit"])]]
