class_name ArcanaDB
extends RefCounted
## Major Arcana available in the Cycle 1 slice. Only effects that do not depend on
## systems locked in Cycle 1 (orientation, Dignities, Thread, Quintessence) are included.

const DEFS := {
	"magician": {"num": 1, "name": "The Magician", "text": "+3 Gravity if the Reading uses three different suits."},
	"empress": {"num": 3, "name": "The Empress", "text": "+1 Light for every 4 cards you own."},
	"lovers": {"num": 6, "name": "The Lovers", "text": "Echo Readings score as a Triad."},
	"hermit": {"num": 9, "name": "The Hermit", "text": "x3 Gravity when you read exactly one card."},
	"death": {"num": 13, "name": "Death", "text": "First Reading each Night: your lowest card is destroyed for good. Its rank becomes permanent Light."},
	"tower": {"num": 16, "name": "The Tower", "text": "Tap to arm. Once per Night, the Reading scores x5, then its cards are destroyed."},
	"star": {"num": 17, "name": "The Star", "text": "+1 Gravity for each Cups card in the Reading."},
	"sun": {"num": 19, "name": "The Sun", "text": "The card in Present gives double Light."},
}
const POOL: Array[String] = ["magician", "empress", "lovers", "hermit", "death", "tower", "star", "sun"]
const MAX_SLOTS := 5
const PRICE := 6
const SELL := 3


static func name_of(id: String) -> String:
	return DEFS[id]["name"]


static func text_of(id: String) -> String:
	return DEFS[id]["text"]


static func num_of(id: String) -> int:
	return int(DEFS[id]["num"])
