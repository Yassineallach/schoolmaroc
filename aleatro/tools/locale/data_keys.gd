extends SceneTree
var keys := []
var seen := {}
func add(s: String, group: String) -> void:
	for l in s.split("\n"):
		if l.strip_edges() != "" and not seen.has(l):
			seen[l] = true
			keys.append([group, l])
func _init() -> void:
	for c in Data.CHARMS:
		add(c.name, "charm"); add(c.desc, "charm")
	for g in ["ENHANCEMENTS", "EDITIONS", "SEALS"]:
		var dct: Dictionary = {"ENHANCEMENTS": Data.ENHANCEMENTS, "EDITIONS": Data.EDITIONS, "SEALS": Data.SEALS}[g]
		for k in dct:
			add(dct[k].name, g.to_lower()); add(dct[k].desc, g.to_lower())
	for k in Data.PACK_KINDS:
		add(Data.PACK_KINDS[k].name, "pack")
	for p in Data.PACKS:
		add(Data.pack_name(p), "pack"); add(Data.pack_desc(p), "pack")
	var arrs := {"spell": Data.SPELLS, "deck": Data.DECKS, "stake": Data.STAKES, "tag": Data.TAGS, "voucher": Data.VOUCHERS, "challenge": Data.CHALLENGES, "boss": Data.HEXES}
	for g in arrs:
		for d in arrs[g]:
			add(d.name, g); add(d.get("desc", ""), g)
	for h in Data.HAND_ORDER:
		add(h, "hand")
	for s in Data.SUIT_NAMES + Data.RARITY_NAMES + Data.BLIND_NAMES + ["Boss Blind", "Jack", "Queen", "King", "Ace"]:
		add(s, "misc")
	for id in Unlocks.GOALS:
		add(Unlocks.goal_text(id), "unlock")
	var f := FileAccess.open(OS.get_environment("OUT"), FileAccess.WRITE)
	f.store_string(JSON.stringify(keys, " "))
	quit()
