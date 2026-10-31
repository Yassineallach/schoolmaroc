extends SceneTree

## Renders the Play feature graphic (1024x500) from the game's own pieces:
## the title's red and blue swirl (splash.gdshader), the ALEATRO logo, a fan
## of playing cards and a row of charms.
##   xvfb-run godot --rendering-driver opengl3 --resolution 1024x500 \
##       -s tools/play_games/feature_graphic.gd
## Writes tools/play_games/properties/feature_1024x500.png.

const OUT := "res://tools/play_games/properties/feature_1024x500.png"


func _initialize() -> void:
	# draw at the window's own 1024x500, not the project's stretched 1560x720
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	var root_c := Control.new()
	root_c.size = Vector2(1024, 500)
	root.add_child(root_c)
	var bg := ColorRect.new()
	bg.size = Vector2(1024, 500)
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/splash.gdshader")
	m.set_shader_parameter("time", 15.0)
	m.set_shader_parameter("vort_speed", 0.4)
	m.set_shader_parameter("colour_1", Palette.ROSE)
	m.set_shader_parameter("colour_2", Palette.TEAL)
	bg.material = m
	root_c.add_child(bg)
	var shade := ColorRect.new()
	shade.size = Vector2(1024, 500)
	shade.color = Color(0, 0, 0, 0.25)
	root_c.add_child(shade)
	# the fan of cards, low and centred
	var hand := [[14, 1], [13, 1], [12, 1], [11, 1], [10, 1]]
	for i in hand.size():
		var cv := CardView.new({"rank": hand[i][0], "suit": hand[i][1], "id": -1})
		cv.float_amount = 0.0
		cv.scale = Vector2.ONE * 1.3
		cv.rotation_degrees = (i - 2) * 9
		cv.position = Vector2(512 - CardView.W / 2 + (i - 2) * 78, 268 + abs(i - 2) * 12)
		root_c.add_child(cv)
	# charms either side
	var charms := ["jester", "foolking", "hologram", "bonecrown"]
	for i in charms.size():
		var ch := CharmView.new(charms[i], "", ["", "holo", "", "chroma"][i])
		ch.float_amount = 0.0
		ch.scale = Vector2.ONE * 1.1
		var left := i < 2
		var k := i if left else i - 2
		ch.position = Vector2((40 + k * 135) if left else (1024 - 40 - CharmView.W - k * 135), 262 - k * 26)
		ch.rotation_degrees = (-6 if left else 6) * (k + 1)
		root_c.add_child(ch)
	var logo: Label = load("res://scripts/main.gd").logo_label(162)
	logo.size = Vector2(1024, 170)
	logo.position = Vector2(0, 40)
	root_c.add_child(logo)
	_shoot.call_deferred()


func _shoot() -> void:
	for i in 10:
		await process_frame
	var img := root.get_texture().get_image()
	img.convert(Image.FORMAT_RGB8)  # Play wants no alpha
	img.save_png(ProjectSettings.globalize_path(OUT))
	print("saved ", OUT, " ", img.get_size())
	quit()
