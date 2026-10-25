class_name Loc
extends RefCounted

## Localisation. Every language lives in res://locale/<code>.json as
## {"messages": {english: translation}}. Keys holding %d or %s are templates:
## "Ante %d/%d" -> "第{0}/{1}底注" matches "Ante 3/8"; a %s part is translated
## in turn ("Skip: %s" -> "跳过：{0}" with the tag's own name translated).
## Text with several lines is translated a line at a time, so a charm's
## description and its "(Currently +8 Mult)" line are separate keys.
##
## Labels and buttons translate themselves (Godot's auto-translate); text a
## view draws itself goes through tr().

const LANGS := ["en", "zh_CN", "ja", "ko", "de", "fr", "es", "pt_BR", "it", "ar"]
const NATIVE := {
	"en": "English", "zh_CN": "简体中文", "ja": "日本語", "ko": "한국어", "de": "Deutsch",
	"fr": "Français", "es": "Español", "pt_BR": "Português (Brasil)", "it": "Italiano", "ar": "العربية",
}
## Fonts for the scripts the game's own font lacks, per language, first
## choice first (Japanese borrows the rarer kanji from the Chinese font).
const FONTS := {"zh_CN": ["sc"], "ja": ["jp", "sc"], "ko": ["kr"], "ar": ["arabic"]}

static var lang := "en"
static var _tr: Translator = null
static var _base_font: Font = null
static var _all_font: FontVariation = null


## The supported language closest to the device's, else English.
static func detect() -> String:
	var os := OS.get_locale()  # "pt_BR", "zh_Hans_CN", "ar", ...
	var code := os.get_slice("_", 0).to_lower()
	match code:
		"zh":
			return "zh_CN"
		"pt":
			return "pt_BR"
	return code if code in LANGS else "en"


## Switch to `choice` ("auto" follows the device).
static func apply(choice: String) -> void:
	lang = detect() if choice == "auto" or not choice in LANGS else choice
	if _tr != null:
		TranslationServer.remove_translation(_tr)
		_tr = null
	var dump := OS.get_environment("ALEATRO_LOC_DUMP")
	# English is the source text: no translator, unless collecting strings
	if lang != "en" or dump != "":
		_tr = Translator.new()
		_tr.locale = lang
		if lang != "en":
			_tr.load_json("res://locale/%s.json" % lang)
		_tr.dump_path = dump
		TranslationServer.add_translation(_tr)
	TranslationServer.set_locale(lang)
	_set_fonts()


static func is_rtl() -> bool:
	return lang == "ar"


## Translate outside a node (static helpers).
static func t(s: String) -> String:
	return TranslationServer.translate(s)


static func _set_fonts() -> void:
	if _base_font == null:
		_base_font = ThemeDB.fallback_font
	# only the current language's: each fallback can make lines taller
	_base_font.fallbacks = _fonts(FONTS.get(lang, []))


## The game font able to show every language, for the language picker.
static func any_script_font() -> Font:
	if _all_font == null:
		_all_font = FontVariation.new()
		_all_font.base_font = ThemeDB.fallback_font if _base_font == null else _base_font
		_all_font.fallbacks = _fonts(["sc", "jp", "kr", "arabic"])
	return _all_font


static func _fonts(keys: Array) -> Array[Font]:
	var out: Array[Font] = []
	for k in keys:
		var path := "res://assets/fonts/noto_%s.ttf" % k
		if ResourceLoader.exists(path):
			out.append(load(path))
	return out


class Translator extends Translation:
	var exact := {}
	var templates: Array = []  # [RegEx, translation, kinds ("d"/"s" per part)]
	var cache := {}
	var dump_path := ""
	var _missed := {}
	var _letter := RegEx.create_from_string("[A-Za-z]")

	func load_json(path: String) -> void:
		var f := FileAccess.open(path, FileAccess.READ)
		if f == null:
			return
		var data = JSON.parse_string(f.get_as_text())
		if not data is Dictionary:
			return
		var msgs: Dictionary = data.get("messages", {})
		var tpl := []
		for k in msgs:
			if msgs[k] == "":
				continue
			if "%d" in k or "%s" in k:
				tpl.append(k)
			else:
				exact[k] = msgs[k]
		# the most specific (most literal text) first
		tpl.sort_custom(func(a, b): return _literal_len(a) > _literal_len(b))
		for k in tpl:
			var kinds := []
			var pat := "^"
			var i := 0
			while i < k.length():
				var two: String = k.substr(i, 2)
				if two == "%d":
					pat += "([-+]?[0-9][0-9,.]*)"
					kinds.append("d")
					i += 2
				elif two == "%s":
					pat += "(.+?)"
					kinds.append("s")
					i += 2
				else:
					pat += _escape(k[i])
					i += 1
			templates.append([RegEx.create_from_string(pat + "$"), msgs[k], kinds])

	static func _literal_len(k: String) -> int:
		return k.replace("%d", "").replace("%s", "").length()

	static func _escape(c: String) -> String:
		return "\\" + c if c in ".^$*+?()[]{}|\\/-" else c

	func _get_message(src_message: StringName, _context: StringName) -> StringName:
		var s := String(src_message)
		if cache.has(s):
			return cache[s]
		var out := lookup(s)
		if cache.size() > 6000:
			cache.clear()
		cache[s] = out
		return out

	func lookup(s: String) -> String:
		var misses := []
		var out := _lookup(s, misses)
		for m in misses:
			_miss(m)
		return out

	## Translate `s`, adding the pieces nothing matched to `misses`. Several
	## templates can match one text ("%s (%s)" fits almost anything with a
	## bracket), so the first whose parts all translate wins.
	func _lookup(s: String, misses: Array) -> String:
		if _letter.search(s) == null:
			return s
		if exact.has(s):
			return exact[s]
		if "\n" in s:
			var lines := s.split("\n")
			for i in lines.size():
				lines[i] = _lookup(lines[i], misses)
			return "\n".join(lines)
		var core := s.strip_edges()
		if core != s:
			if core == "":
				return s
			var at := s.find(core)
			return s.substr(0, at) + _lookup(core, misses) + s.substr(at + core.length())
		var fallback := []  # [text, misses] of the first partial match
		for t in templates:
			var m: RegExMatch = t[0].search(s)
			if m == null:
				continue
			var res: String = t[1]
			var mine := []
			for g in t[2].size():
				var part := m.get_string(g + 1)
				if t[2][g] == "s":
					part = _lookup(part, mine)
				res = res.replace("{%d}" % g, part)
			if mine.is_empty():
				return res
			if fallback.is_empty():
				fallback = [res, mine]
		# a list ("Jester, Glitch, Flag"): each item on its own
		for sep in ["; ", ", ", " / "]:
			if sep in s:
				var mine := []
				var parts := s.split(sep)
				for i in parts.size():
					parts[i] = _lookup(parts[i], mine)
				var res: String = exact.get(sep, sep).join(parts)
				if mine.is_empty():
					return res
				if fallback.is_empty():
					fallback = [res, mine]
				break
		if not fallback.is_empty():
			misses.append_array(fallback[1])
			return fallback[0]
		misses.append(s)
		return s

	func _miss(s: String) -> void:
		if dump_path == "" or _missed.has(s):
			return
		_missed[s] = true
		var f := FileAccess.open(dump_path, FileAccess.READ_WRITE)
		if f == null:
			f = FileAccess.open(dump_path, FileAccess.WRITE)
		if f != null:
			f.seek_end()
			f.store_line(s.c_escape())
