class_name PlayGames
extends Node

## Google Play Games Services through the AleatroPGS Android plugin
## (addons/aleatro_pgs). Off Android, or before Play Console's IDs are in
## res://pgs/games-ids.xml, every call quietly does nothing.
##
## Achievements are earned locally (main.gd keeps them in the profile) and
## sent whenever the player is signed in, so ones earned offline sync on the
## next sign-in. Leaderboards get the career bests the same way.

signal signed_in_changed(signed_in: bool)

const IDS_PATH := "res://pgs/games-ids.xml"
## Incremental achievements resend their progress at most every 5%.
const STEP_BUCKETS := 20

var plugin: Object = null
var signed_in := false
var player_name := ""
var ids := {}  # "achievement_x" / "leaderboard_x" -> Play Console ID
var _sent_steps := {}  # achievement key -> progress bucket last sent


func _ready() -> void:
	ids = load_ids(IDS_PATH)
	if Engine.has_singleton("AleatroPGS"):
		plugin = Engine.get_singleton("AleatroPGS")
		plugin.signed_in.connect(_on_signed_in)
		plugin.player.connect(func(_id: String, name: String): player_name = name)
		plugin.failed.connect(func(what: String, msg: String): push_warning("Play Games %s failed: %s" % [what, msg]))
		plugin.check_sign_in()


func available() -> bool:
	return plugin != null


func sign_in() -> void:
	if plugin != null:
		plugin.sign_in()


func _on_signed_in(ok: bool) -> void:
	signed_in = ok
	_sent_steps.clear()
	signed_in_changed.emit(ok)


## The IDs from Play Console's "Get resources" file (Android XML):
## <string name="achievement_climbing">CgkI...</string>.
static func load_ids(path: String) -> Dictionary:
	var out := {}
	var xml := XMLParser.new()
	if not FileAccess.file_exists(path) or xml.open(path) != OK:
		return out
	var name := ""
	while xml.read() == OK:
		match xml.get_node_type():
			XMLParser.NODE_ELEMENT:
				name = xml.get_named_attribute_value_safe("name") if xml.get_node_name() == "string" else ""
			XMLParser.NODE_TEXT:
				var text := xml.get_node_data().strip_edges()
				if name != "" and text != "":
					out[name] = text
			XMLParser.NODE_ELEMENT_END:
				name = ""
	return out


## Play Console names resources after the English name in snake_case.
static func res_name(prefix: String, entry: Dictionary) -> String:
	var n := ""
	for ch in String(entry.name).to_lower():
		n += ch if (ch >= "a" and ch <= "z") or (ch >= "0" and ch <= "9") else "_"
	while n.contains("__"):
		n = n.replace("__", "_")
	return prefix + n.strip_edges().trim_prefix("_").trim_suffix("_")


func id_for(prefix: String, entry: Dictionary) -> String:
	return ids.get(prefix + entry.key, ids.get(res_name(prefix, entry), ""))


func unlock(a: Dictionary) -> void:
	var id := id_for("achievement_", a)
	if plugin != null and signed_in and id != "":
		plugin.unlock_achievement(id)


## Progress on an incremental achievement (sent in 5% steps).
func set_steps(a: Dictionary, steps: int) -> void:
	var id := id_for("achievement_", a)
	if plugin == null or not signed_in or id == "" or steps <= 0:
		return
	var bucket := steps * STEP_BUCKETS / maxi(1, int(a.goal.n))
	if _sent_steps.get(a.key, -1) == bucket:
		return
	_sent_steps[a.key] = bucket
	plugin.set_achievement_steps(id, steps)


func submit(board_key: String, score: int) -> void:
	for lb in Achievements.LEADERBOARDS:
		if lb.key == board_key:
			var id := id_for("leaderboard_", lb)
			if plugin != null and signed_in and id != "" and score > 0:
				plugin.submit_score(id, score)


func show_achievements() -> void:
	if plugin != null:
		plugin.show_achievements()


func show_leaderboards() -> void:
	if plugin != null:
		plugin.show_all_leaderboards()
