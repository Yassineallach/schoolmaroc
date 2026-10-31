extends SceneTree
## Store screenshots: each raw shot from capture.gd under a one-line caption
## in its language, at the window size, saved as 24-bit PNG (no alpha).
## Usage (from the project folder):
##   STORE_RAW=/abs/raw STORE_OUT=/abs/out STORE_SET=phone FONT_DIR=/abs/fonts \
##   xvfb-run -a -s "-screen 0 2600x1500x24" godot --rendering-driver opengl3 \
##     --resolution 1920x1080 -s tools/store/compose.gd
## FONT_DIR holds the full Noto Sans SC/JP/KR/Arabic fonts (the game's copies
## are cut down to its own text).

const RAW_NAME := {"score": "score1"}
const SCRIPT_FONTS := {"zh_CN": ["NotoSansSC"], "ja": ["NotoSansJP", "NotoSansSC"], "ko": ["NotoSansKR"], "ar": ["NotoSansArabic"]}

var raw_dir: String
var out_dir: String
var set_name: String
var font_dir: String


func _initialize() -> void:
	raw_dir = OS.get_environment("STORE_RAW")
	out_dir = OS.get_environment("STORE_OUT")
	set_name = OS.get_environment("STORE_SET")
	font_dir = OS.get_environment("FONT_DIR")
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	run()


func _font(lang: String) -> Font:
	var f := FontVariation.new()
	f.base_font = load("res://assets/fonts/m6x11plus.ttf")
	var fb: Array[Font] = []
	for name in SCRIPT_FONTS.get(lang, []):
		for file in DirAccess.get_files_at(font_dir):
			if file.begins_with(name):
				var ff := FontFile.new()
				ff.load_dynamic_font(font_dir.path_join(file))
				var v := FontVariation.new()
				v.base_font = ff
				v.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 700}
				fb.append(v)
	f.fallbacks = fb
	return f


func run() -> void:
	await process_frame
	var size := Vector2(root.size)
	var s := size.y / 1080.0
	var cap: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tools/store/captions.json"))
	for lang in cap.keys():
		if lang == "order":
			continue
		var dir := out_dir.path_join(lang).path_join(set_name)
		DirAccess.make_dir_recursive_absolute(dir)
		var font := _font(lang)
		var i := 0
		for key in cap.order:
			i += 1
			var ui := _page(size, s, font, cap[lang][key], raw_dir.path_join("%s_%s.png" % [lang, RAW_NAME.get(key, key)]), lang)
			root.add_child(ui)
			for _f in 4:
				await process_frame
			var img := root.get_texture().get_image()
			img.convert(Image.FORMAT_RGB8)
			img.save_png(dir.path_join("%02d_%s.png" % [i, key]))
			ui.queue_free()
			await process_frame
	quit()


func _page(size: Vector2, s: float, font: Font, text: String, shot_path: String, lang: String) -> Control:
	var page := Control.new()
	page.size = size
	# backdrop: the icon's rose to teal over plum
	var g := Gradient.new()
	g.set_color(0, Palette.WINE.darkened(0.25))
	g.set_color(1, Palette.TEAL.darkened(0.55))
	g.add_point(0.5, Palette.TABLE_DARK)
	var gt := GradientTexture2D.new()
	gt.gradient = g
	gt.fill_from = Vector2(0, 0)
	gt.fill_to = Vector2(1, 1)
	gt.width = 256
	gt.height = 256
	var bg := TextureRect.new()
	bg.texture = gt
	bg.stretch_mode = TextureRect.STRETCH_SCALE
	bg.size = size
	page.add_child(bg)
	# caption band: under 15% of the height
	var band_h := 150.0 * s
	var lab := Label.new()
	lab.text = text
	lab.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lab.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lab.position = Vector2(40 * s, 0)
	lab.size = Vector2(size.x - 80 * s, band_h)
	lab.add_theme_font_override("font", font)
	var fs := 100.0 if not lang in ["zh_CN", "ja", "ko", "ar"] else 78.0
	lab.add_theme_font_size_override("font_size", int(fs * s))
	lab.add_theme_color_override("font_color", Color.WHITE)
	lab.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.55))
	lab.add_theme_constant_override("shadow_offset_x", int(4 * s))
	lab.add_theme_constant_override("shadow_offset_y", int(5 * s))
	lab.add_theme_color_override("font_outline_color", Palette.PANEL_DEEPER)
	lab.add_theme_constant_override("outline_size", int(10 * s))
	# shrink long captions to fit one line
	while font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, int(fs * s)).x > lab.size.x and fs > 30:
		fs -= 2
		lab.add_theme_font_size_override("font_size", int(fs * s))
	page.add_child(lab)
	# the game, framed
	var tex := ImageTexture.create_from_image(Image.load_from_file(shot_path))
	var avail_h := size.y - band_h - 34 * s
	var shot_sz := Vector2(avail_h * 16.0 / 9.0, avail_h)
	var frame := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Palette.PAPER
	sb.set_corner_radius_all(int(22 * s))
	sb.shadow_color = Color(0, 0, 0, 0.45)
	sb.shadow_size = int(18 * s)
	sb.shadow_offset = Vector2(0, 8 * s)
	frame.add_theme_stylebox_override("panel", sb)
	var b := 8.0 * s
	frame.size = shot_sz + Vector2(b, b) * 2
	frame.position = Vector2((size.x - frame.size.x) / 2.0, band_h)
	page.add_child(frame)
	var clip := Panel.new()
	var sb2 := StyleBoxFlat.new()
	sb2.bg_color = Color.WHITE
	sb2.set_corner_radius_all(int(16 * s))
	clip.add_theme_stylebox_override("panel", sb2)
	clip.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	clip.position = Vector2(b, b)
	clip.size = shot_sz
	frame.add_child(clip)
	var tr := TextureRect.new()
	tr.texture = tex
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_SCALE
	tr.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	tr.size = shot_sz
	clip.add_child(tr)
	return page
