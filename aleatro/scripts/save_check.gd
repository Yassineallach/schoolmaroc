class_name SaveCheck
extends RefCounted

## Checks what a save file holds before the game trusts it. Saves are plain
## data (bytes_to_var never builds objects), but a file that is damaged,
## left over from an odd build, or edited by hand can still decode to values
## the game would crash on later: a charm id that no longer exists, a card
## without a suit, blind 7 of 3. A run that fails is set aside rather than
## resumed; a profile is repaired field by field so lifetime stats survive.

const MAX_INT := 1_000_000_000
## Saved alongside SAVE_FIELDS by GameState.to_dict and main.save_run.
const EXTRA_TYPES := {"hand": TYPE_ARRAY, "draw_pile": TYPE_ARRAY, "boss": TYPE_STRING, "rng_seed": TYPE_INT,
	"rng_state": TYPE_INT, "screen": TYPE_STRING, "sort_mode": TYPE_STRING, "manual_order": TYPE_BOOL}


## "" when `d` is a run the game can resume, else what is wrong with it.
static func run(d: Dictionary) -> String:
	_rename_charms(d)
	var fresh := GameState.new()
	for f in GameState.SAVE_FIELDS:
		if d.has(f) and not _same_type(d[f], fresh.get(f)):
			return "%s has the wrong type" % f
	for f in EXTRA_TYPES:
		if d.has(f) and typeof(d[f]) != EXTRA_TYPES[f]:
			return "%s has the wrong type" % f
	var why := _ranges(d)
	if why == "":
		why = _cards(d)
	if why == "":
		why = _items(d)
	if why == "":
		why = _screen(d)
	return why


## Carry charms that were renamed between versions over to their new ids.
static func _rename_charms(d: Dictionary) -> void:
	for key in ["charms", "shop_items"]:
		for c in d.get(key, []):
			if c is Dictionary and Data.RENAMED_CHARMS.has(c.get("id")):
				c.id = Data.RENAMED_CHARMS[c.id]
				c.data = {}


static func _same_type(v, like) -> bool:
	if typeof(like) == TYPE_FLOAT:
		return v is float or v is int
	return typeof(v) == typeof(like)


static func _int_in(d: Dictionary, key: String, lo: int, hi: int) -> bool:
	return not d.has(key) or (d[key] is int and d[key] >= lo and d[key] <= hi)


static func _ranges(d: Dictionary) -> String:
	for spec in [["ante", 1, 100000], ["blind_idx", 0, 2], ["money", -MAX_INT, MAX_INT],
			["hand_size", 1, 30], ["max_hands", 1, 50], ["max_discards", 0, 50],
			["hands_left", 0, 50], ["discards_left", 0, 50], ["charm_slots", 0, 30],
			["spell_slots", 0, 30], ["round_score", 0, MAX_INT * 1000], ["target", 0, MAX_INT * 1000],
			["reroll_cost", 0, MAX_INT], ["inflation", 0, MAX_INT], ["_next_id", 0, MAX_INT]]:
		if not _int_in(d, spec[0], spec[1], spec[2]):
			return "%s out of range" % spec[0]
	for key in ["hand_levels", "hands_played_count"]:
		var t: Dictionary = d.get(key, {})
		for h in t:
			if not Data.HAND_ORDER.has(h) or not (t[h] is int) or t[h] < 0:
				return "%s has a bad entry" % key
	return ""


static func _card_ok(c) -> bool:
	return c is Dictionary and c.get("id") is int and c.get("rank") is int and c.get("suit") is int \
		and c.rank >= 2 and c.rank <= 14 and c.suit >= 0 and c.suit <= 3 \
		and _key_ok(c.get("enh", ""), Data.ENHANCEMENTS) and _key_ok(c.get("ed", ""), Data.EDITIONS) \
		and _key_ok(c.get("seal", ""), Data.SEALS)


static func _key_ok(v, table: Dictionary) -> bool:
	return v is String and (v == "" or table.has(v))


static func _cards(d: Dictionary) -> String:
	var deck: Array = d.get("deck", [])
	if d.has("deck") and deck.is_empty():
		return "deck is empty"
	var ids := {}
	for c in deck:
		if not _card_ok(c):
			return "deck has a broken card"
		if ids.has(c.id):
			return "deck has a duplicate card"
		ids[c.id] = true
	for key in ["hand", "draw_pile", "played_this_ante"]:
		for i in d.get(key, []):
			if not (i is int):
				return "%s has a bad card id" % key
	for it in d.get("shop_items", []):
		if it is Dictionary and it.get("type") == "card" and not _card_ok(it.get("card")):
			return "shop card is broken"
	return ""


static func _charm_ok(c) -> bool:
	return c is Dictionary and c.get("id") is String and not Data.charm_def(c.id).is_empty() \
		and _key_ok(c.get("ed", ""), Data.EDITIONS) and c.get("data", {}) is Dictionary


static func _items(d: Dictionary) -> String:
	for c in d.get("charms", []):
		if not _charm_ok(c):
			return "unknown charm"
	for it in d.get("shop_items", []):
		if not (it is Dictionary and it.get("base") is int and it.get("type") in ["charm", "spell", "card"]):
			return "broken shop item"
		if it.type == "charm" and (not (it.get("id") is String) or Data.charm_def(it.id).is_empty()):
			return "unknown charm in shop"
		if it.type == "spell" and (not (it.get("id") is String) or Data.spell_def(it.id).is_empty()):
			return "unknown spell in shop"
	for s in d.get("spells", []):
		if not (s is String) or Data.spell_def(s).is_empty():
			return "unknown spell"
	for key in ["vouchers", "shop_vouchers"]:
		for v in d.get(key, []):
			if not (v is String) or Data.voucher_def(v).is_empty():
				return "unknown voucher"
	var av = d.get("ante_voucher", "")
	if not (av is String) or (av != "" and Data.voucher_def(av).is_empty()):
		return "unknown voucher"
	for key in ["tags", "blind_tags"]:
		for t in d.get(key, []):
			if not (t is String) or Data.tag_def(t).is_empty():
				return "unknown tag"
	for k in d.get("pending_packs", []):
		if not Data.PACKS.has(k):
			return "unknown pack"
	for pk in d.get("shop_packs", []):
		if not (pk is Dictionary and Data.PACKS.has(pk.get("id"))):
			return "unknown pack"
	var ch = d.get("challenge", "")
	if ch != "" and Data.challenge_def(ch).is_empty():
		return "unknown challenge"
	var boss: String = d.get("boss", "")
	if boss != "" and not Data.HEXES.any(func(h): return h.id == boss):
		return "unknown boss"
	var bs = d.get("boss_state", {})
	for spec in [["used_hands", TYPE_ARRAY], ["only_hand", TYPE_STRING], ["disabled", TYPE_BOOL],
			["forced", TYPE_INT], ["ember", TYPE_INT], ["sold", TYPE_BOOL], ["hands_played", TYPE_INT], ["down", TYPE_ARRAY]]:
		if bs.has(spec[0]) and typeof(bs[spec[0]]) != spec[1]:
			return "boss state is broken"
	return ""


static func _screen(d: Dictionary) -> String:
	var screen: String = d.get("screen", "blind")
	if not (screen in ["blind", "round", "shop", "cashout"]):
		return "unknown screen"
	if screen == "cashout":
		var info = d.get("cashout")
		if not (info is Dictionary and info.get("title") is String and info.get("rows") is Array and info.get("total") is int):
			return "cash-out summary is broken"
		for r in info.rows:
			if not (r is Array and r.size() == 2 and r[0] is String and r[1] is int):
				return "cash-out summary is broken"
	if screen == "round" and d.get("hand", []).is_empty() and d.get("draw_pile", []).is_empty():
		return "round has no cards"
	return ""


## A profile with anything unusable dropped back to its default.
static func profile(d: Dictionary, stat_defaults: Dictionary) -> Dictionary:
	var out := {"stats": {}, "seen_charms": [], "seen_hexes": []}
	var stats = d.get("stats", {})
	if stats is Dictionary:
		for k in stat_defaults:
			if stats.get(k) is int and stats[k] >= 0:
				out.stats[k] = stats[k]
	if d.get("seen_charms") is Array:
		d.seen_charms = d.seen_charms.map(func(id): return Data.RENAMED_CHARMS.get(id, id))
	out.seen_charms = _strings(d.get("seen_charms"), func(id): return not Data.charm_def(id).is_empty())
	out.seen_hexes = _strings(d.get("seen_hexes"), func(id): return Data.HEXES.any(func(h): return h.id == id))
	out.challenges_won = _strings(d.get("challenges_won"), func(id): return not Data.challenge_def(id).is_empty())
	out.tutorial = _strings(d.get("tutorial"), func(_s): return true)
	out.tips_off = d.get("tips_off") is bool and d.tips_off
	out.deck_stakes = {}
	var ds = d.get("deck_stakes", {})
	if ds is Dictionary:
		for k in ds:
			if k is String and not Data.deck_def(k).is_empty() and ds[k] is int:
				out.deck_stakes[k] = clampi(ds[k], 0, Data.STAKES.size())
	# anything else the game stored keeps its value if it is plain data
	for k in d:
		if not out.has(k) and typeof(d[k]) in [TYPE_BOOL, TYPE_INT, TYPE_FLOAT, TYPE_STRING]:
			out[k] = d[k]
	return out


static func _strings(v, keep: Callable) -> Array:
	var out: Array = []
	if v is Array:
		for s in v:
			if s is String and keep.call(s) and not out.has(s):
				out.append(s)
	return out
