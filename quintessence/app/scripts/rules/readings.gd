class_name Readings
extends RefCounted
## Reading (hand) detection for the Three-Card Spread. 1 to 3 cards.

const DEFS := {
	"glimpse": {"name": "Glimpse", "light": 5, "gravity": 1, "lv_light": 5, "lv_gravity": 1,
		"rule": "Any cards, no pattern"},
	"echo": {"name": "Echo", "light": 10, "gravity": 2, "lv_light": 10, "lv_gravity": 1,
		"rule": "Two cards of the same rank"},
	"path": {"name": "Path", "light": 25, "gravity": 3, "lv_light": 15, "lv_gravity": 1,
		"rule": "Three ranks in a row"},
	"triad": {"name": "Triad", "light": 30, "gravity": 3, "lv_light": 20, "lv_gravity": 2,
		"rule": "Three cards of the same rank"},
	"harmony": {"name": "Harmony", "light": 40, "gravity": 4, "lv_light": 15, "lv_gravity": 2,
		"rule": "Three cards of one suit"},
	"court": {"name": "Court Assembly", "light": 55, "gravity": 5, "lv_light": 20, "lv_gravity": 2,
		"rule": "Three Court cards"},
	"river": {"name": "River", "light": 80, "gravity": 8, "lv_light": 30, "lv_gravity": 3,
		"rule": "Three ranks in a row, one suit"},
}
const ORDER: Array[String] = ["glimpse", "echo", "path", "triad", "harmony", "court", "river"]


static func detect(cards: Array) -> String:
	var n := cards.size()
	if n == 0:
		return ""
	var ranks: Array[int] = []
	var suits := {}
	var counts := {}
	for c in cards:
		var r := int(c["rank"])
		ranks.append(r)
		suits[int(c["suit"])] = true
		counts[r] = int(counts.get(r, 0)) + 1
	ranks.sort()
	var max_same := 0
	for k in counts:
		max_same = maxi(max_same, int(counts[k]))
	var one_suit := suits.size() == 1
	var consecutive := n == 3 and ranks[1] == ranks[0] + 1 and ranks[2] == ranks[1] + 1
	if consecutive and one_suit:
		return "river"
	if n == 3 and ranks[0] >= 11:
		return "court"
	if n == 3 and one_suit:
		return "harmony"
	if max_same == 3:
		return "triad"
	if consecutive:
		return "path"
	if max_same >= 2:
		return "echo"
	return "glimpse"


static func base_values(id: String, level: int) -> Vector2i:
	var d: Dictionary = DEFS[id]
	return Vector2i(int(d["light"]) + int(d["lv_light"]) * (level - 1),
		int(d["gravity"]) + int(d["lv_gravity"]) * (level - 1))
